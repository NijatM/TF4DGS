"""Source/depth-guided recovery after selective opacity attenuation.

Uses official Difix image targets but is an experimental project adapter,
not NVIDIA's complete progressive training pipeline. Originals are untouched.
"""
import argparse
import gc
from importlib.util import spec_from_file_location,module_from_spec
import json
import math
from pathlib import Path
import re
import time
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
import torch
import torch.nn.functional as F
from gsplat import rasterization

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)

def depth_tracks(manifest,entry,edge):
    dataset=Path(manifest['dataset']);points={}
    with (dataset/'sparse/points3D.bin').open('rb') as f:
        for _ in range(r.unpack(f,'Q')[0]):
            v=r.unpack(f,'QdddBBBdQ');f.seek(v[-1]*8,1)
            if v[-1]>=4 and v[-2]<1.5:points[v[0]]=v[1:4]
    views={v['name']:v for v in r.aligned_views(manifest['views'],entry)};tracks={}
    with (dataset/'sparse/images.bin').open('rb') as f:
        for _ in range(r.unpack(f,'Q')[0]):
            r.unpack(f,'idddddddi');name=bytearray()
            while (b:=f.read(1))!=b'\0':
                if not b:raise EOFError('image name')
                name+=b
            name=name.decode();n=r.unpack(f,'Q')[0]
            observations=np.frombuffer(f.read(n*24),dtype=[('x','<f8'),('y','<f8'),('id','<i8')])
            records=[(o['x'],o['y'],points[o['id']]) for o in observations if o['id'] in points]
            if not records:continue
            uv=np.array([(x,y) for x,y,_ in records]);xyz=np.array([p for _,_,p in records])
            align=entry.get('alignment')
            if align:xyz=align['scale']*xyz@np.array(align['rotation']).T+np.array(align['translation'])
            v=views[name];V=np.array(v['view']);z=(xyz@V[:3,:3].T+V[:3,3])[:,2]
            w,h,_=r.scaled(v,edge);uv*=np.array([w/v['width'],h/v['height']])
            keep=(z>.01)&(uv[:,0]>=0)&(uv[:,0]<w-1)&(uv[:,1]>=0)&(uv[:,1]<h-1)
            uv=uv[keep];z=z[keep]
            # Bounded deterministic subset of accurate triangulated observations.
            ids=np.linspace(0,len(z)-1,min(1024,len(z))).round().astype(int) if len(z) else []
            tracks[name]=(torch.tensor(uv[ids],device='cuda',dtype=torch.float32),torch.tensor(z[ids],device='cuda',dtype=torch.float32))
    return np.array(list(points.values())),tracks

def structural_loss(rgb,gt,mask):
    x=(rgb*mask).permute(2,0,1)[None];y=(gt*mask).permute(2,0,1)[None]
    mx=F.avg_pool2d(x,7,1,3);my=F.avg_pool2d(y,7,1,3)
    vx=(F.avg_pool2d(x*x,7,1,3)-mx*mx).clamp_min(0);vy=(F.avg_pool2d(y*y,7,1,3)-my*my).clamp_min(0)
    cov=F.avg_pool2d(x*y,7,1,3)-mx*my
    s=((2*mx*my+.01**2)*(2*cov+.03**2))/((mx*mx+my*my+.01**2)*(vx+vy+.03**2))
    support=mask.permute(2,0,1)[None]
    return ((1-s)*support).sum()/(3*support.sum().clamp_min(1))

def run(a):
    torch.set_num_threads(6)
    manifest=json.loads((r.WORK/'manifest.json').read_text());entry=dict(manifest['files'][a.index]);stem=Path(entry['name']).stem
    base=r.WORK/entry['folder']/(stem+'_wide_official')
    source=r.WORK/'tuning'/entry['folder']/(stem+'_wide_official_Difix3D.ply')
    directory=base.with_name(stem+'_'+a.recipe);directory.mkdir(parents=True,exist_ok=True)
    output=source.with_name(stem+'_'+a.recipe+'_Difix3D.ply')
    if output.exists():raise FileExistsError(output)
    targets=json.loads((base/'targets.json').read_text());audit=[x for x in targets['records'] if x['kind']=='audit']
    # Keep local interpolation and only the two visually inspected, wall-safe wide poses.
    novel=[x for x in targets['records'] if x['kind']=='novel' and (not x['view']['name'].startswith('wide_') or x['view']['name'] in ['wide_0_-35','wide_0_-20'])]
    wide=[x for x in novel if x['view']['name'].startswith('wide_')];near=[x for x in novel if not x['view']['name'].startswith('wide_')]
    views=r.aligned_views(manifest['views'],entry)
    anchors=[]
    for v in views:
        w,h,_=r.scaled(v,a.edge)
        anchors.append(dict(view=v,kind='anchor',target=v['image']))
    points,tracks=depth_tracks(manifest,entry,a.edge)
    m,layout=r.load_model(source,True);before,images_before=r.evaluate(m,audit,targets['edge'],directory,'before_recovery')
    centers=np.array([np.linalg.inv(v['view'])[:3,3] for v in manifest['views']]);extent=float(np.median(np.linalg.norm(centers-centers.mean(0),axis=1)))
    xyz=m['means'].detach().cpu().numpy().astype(float);alignment=entry.get('alignment')
    if alignment:xyz=(xyz-np.array(alignment['translation']))@np.array(alignment['rotation'])/alignment['scale']
    tree=cKDTree(points);spacing=tree.query(points,k=8,workers=6)[0][:,1:].mean(1);distance,nearest=tree.query(xyz,workers=6)
    scales=np.sort(m['scales'].detach().exp().cpu().numpy(),axis=1);opa=m['opacities'].detach().sigmoid().cpu().numpy()
    candidate=(distance>np.maximum(spacing[nearest]*4,scales[:,1]*3))&((opa<.2)|(scales[:,2]/np.maximum(scales[:,1],1e-8)>12)|(scales[:,2]>.03*extent))
    ids=torch.tensor(np.flatnonzero(candidate),device='cuda')
    with torch.no_grad():m['opacities'][ids]=torch.minimum(m['opacities'][ids],torch.tensor(math.log(.05/.95),device='cuda'))
    rates=dict(means=1.6e-5*extent,scales=.001,quats=.0002,opacities=.02,sh0=.00015,shN=.0000075)
    optim={k:torch.optim.Adam([v],lr=rates[k],foreach=False) for k,v in m.items()}
    checkpoint=directory/'refinement.pth';initial=0
    if checkpoint.exists():
        cp=torch.load(checkpoint,map_location='cuda',weights_only=False)
        for k in m:m[k].data.copy_(cp['model'][k]);optim[k].load_state_dict(cp['optimizers'][k])
        initial=cp['step'];del cp
    depth_weight=.03 if a.recipe=='geometry_recovery' else 0.
    ssim_weight=.2 if a.recipe=='geometry_recovery' else 0.
    r.stage('Opacity recovery test: '+entry['name'],f'{int(candidate.sum()):,} candidates attenuated, not deleted. All {len(anchors)} source photos plus {len(novel)} repair targets; colliding wide views excluded. Recipe {a.recipe}; depth weight {depth_weight}; SSIM weight {ssim_weight}.',status='experimental refinement started')
    cache={};start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
    for step in range(initial,a.steps):
        rng=np.random.default_rng(42+step)
        is_novel=step%10>=7
        group=(wide if step%2==0 else near) if is_novel else anchors
        t=group[int(rng.integers(len(group)))];v=t['view'];w,h,K=r.scaled(v,a.edge)
        key=t['target']
        if key not in cache:
            gt=np.asarray(Image.open(key).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)).copy()/255
            mask=np.asarray(Image.fromarray(np.load(t['alpha']).astype(np.float32)).resize((w,h),Image.Resampling.BILINEAR))>.02 if is_novel else np.ones((h,w),bool)
            # CPU cache prevents all 275 full-resolution references consuming GPU RAM.
            cache[key]=(torch.tensor(gt,dtype=torch.float32),torch.tensor(mask[...,None],dtype=torch.float32))
        gt,mask=[x.to('cuda') for x in cache[key]]
        rgb,alpha,_=rasterization(means=m['means'],quats=m['quats'],scales=m['scales'].exp(),opacities=m['opacities'].sigmoid(),colors=torch.cat((m['sh0'],m['shN']),dim=1),viewmats=torch.tensor(v['view'],device='cuda',dtype=torch.float32)[None],Ks=torch.tensor(K,device='cuda')[None],width=w,height=h,sh_degree=3,packed=True,near_plane=.01,far_plane=1e6,rasterize_mode='classic',render_mode='RGB+ED')
        rgb=rgb[0];color=rgb[...,:3].clamp(0,1)
        l1=((color-gt).abs()*mask).sum()/(3*mask.sum()).clamp_min(1)
        loss=(1-ssim_weight)*l1
        if ssim_weight:loss+=ssim_weight*structural_loss(color,gt,mask)
        if is_novel:loss*=.6
        elif depth_weight and v['name'] in tracks:
            uv,z=tracks[v['name']]
            if len(z):
                grid=uv.clone();grid[:,0]=grid[:,0]/(w-1)*2-1;grid[:,1]=grid[:,1]/(h-1)*2-1
                pred=F.grid_sample(rgb[...,3][None,None],grid[None,None],align_corners=True).flatten()
                visibility=F.grid_sample(alpha.permute(0,3,1,2),grid[None,None],align_corners=True).flatten().detach()>.5
                loss+=depth_weight*((1/pred.clamp_min(.01)-1/z).abs()*extent*visibility).sum()/visibility.sum().clamp_min(1)
        if not torch.isfinite(loss):raise FloatingPointError(f'Nonfinite loss at {step}')
        loss.backward()
        for o in optim.values():o.step();o.zero_grad(set_to_none=True)
        # Decay position LR after geometry settles, keeping texture optimization active.
        optim['means'].param_groups[0]['lr']=rates['means']*(.15**((step+1)/a.steps))
        if (step+1)%100==0:
            r.write_json(r.DOCS/'live_progress.json',dict(model=entry['name'],stage='opacity and SfM-depth recovery',step=step+1,total=a.steps,loss=float(loss),elapsed_s=time.perf_counter()-start))
            print(f'{entry["name"]} geometry recovery {step+1}/{a.steps} loss={float(loss):.5f}',flush=True)
        if (step+1)%500==0 or step+1==a.steps:
            torch.save(dict(step=step+1,model={k:v.detach() for k,v in m.items()},optimizers={k:o.state_dict() for k,o in optim.items()}),checkpoint.with_suffix('.tmp'));checkpoint.with_suffix('.tmp').replace(checkpoint)
    after,images_after=r.evaluate(m,audit,targets['edge'],directory,'after_recovery')
    with torch.no_grad():remaining=int((m['opacities'][ids].sigmoid()<.01).sum())
    r.export(output,m,layout)
    record=dict(input=entry['name'],output=output.name,source_sha256=entry['sha256'],starting_model_sha256=r.sha(source),output_sha256=r.sha(output),original_preserved=r.sha(Path(entry['path']))==entry['sha256'],recipe=a.recipe,steps=a.steps,training_edge=a.edge,target_edge=targets['edge'],source_photos=len(anchors),novel_targets=len(novel),opacity_attenuated=int(candidate.sum()),attenuated_still_below_1pct=remaining,sfm_depth_weight=depth_weight,ssim_weight=ssim_weight,learning_rates=rates,before=before,after=after,gaussians=entry['count'],camera_alignment=alignment,reopened_ply_verified=False,scope='Experimental opacity attenuation and optional sparse SfM-depth adaptation with official Difix image targets. Same Gaussian count; no invented claim of complete missing geometry recovery.',elapsed_s=time.perf_counter()-start)
    r.write_json(output.with_suffix('.difix3d.json'),record)
    evidence=entry['folder']+'_'+directory.name+'_comparison.jpg'
    r.montage(r.DOCS/evidence,[[audit[i]['target'],images_before[i],images_after[i]] for i in range(3)],['Photograph','Moderate Difix3D','Opacity/depth recovery'])
    r.stage('Geometry recovery exported: '+entry['name'],f'Camera audit {before["mean_psnr"]:.3f} → {after["mean_psnr"]:.3f} dB; visual review still required.',[evidence],status='prototype; not published beside original')
    del m,optim,cache,layout;gc.collect();torch.cuda.empty_cache()
    # Reuse independent reload verification and matched orbit evidence.
    r.write_json(directory/'targets.json',targets);entry.update(output=str(output),recipe=a.recipe)
    r.verify(entry,directory);r.stress(entry,manifest,directory)
    print(json.dumps(record),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,default=2);p.add_argument('--steps',type=int,default=6000);p.add_argument('--edge',type=int,default=1024);p.add_argument('--recipe',choices=['geometry_recovery','opacity_recovery'],default='geometry_recovery');a=p.parse_args()
    try:run(a)
    except Exception as e:r.stage('Geometry recovery failed',str(e),status='failed; retained for diagnosis');raise
