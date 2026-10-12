"""Source-guided Difix3D PLY refinement; originals are never overwritten.

The published diffusion model is unchanged. This adapter imports standard SH3
PLY into gsplat, caches repaired novel-view targets, then refines the same
primitives. It is not the paper's complete progressive reconstruction recipe.
"""
import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import time
import traceback
from datetime import datetime, timezone

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation, Slerp
import torch
from gsplat import rasterization

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/difix3d_necto_001'
WORK = ROOT / 'outputs/difix3d_necto_001'
SOURCE = ROOT / '.local/src/Difix3D'
MODEL_REVISION='d4830559772a5795c9d136302c5b197d6418d3fb'
os.environ.setdefault('HF_HOME',str(ROOT/'.local/cache/difix3d'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2), encoding='utf8')
    for attempt in range(30):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(.15)
    raise PermissionError(str(path))


def stage(title, detail, images=(), status='in progress'):
    DOCS.mkdir(parents=True, exist_ok=True)
    path = DOCS / 'journal.json'
    rows = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else []
    rows.append(dict(number=len(rows)+1, utc=datetime.now(timezone.utc).isoformat(),
                     title=title, detail=detail, status=status, images=list(images)))
    write_json(path, rows)
    write_json(DOCS / 'live_progress.json', dict(title=title, detail=detail, status=status,
               utc=datetime.now(timezone.utc).isoformat()))
    html = '<!doctype html><meta charset="utf-8"><title>TF4DGS Difix3D Necto repair</title>'
    html += '<style>body{background:#111820;color:#e2e9ef;font:16px Arial;margin:30px}img{max-width:100%}section{margin:25px 0;padding:20px;background:#1c2833}a{color:#80cff5}</style>'
    html += '<h1>TF4DGS · Difix3D Necto repair</h1><p>Actual Gaussian renderings and repair tests. Image enhancements and exported 3D results are labelled separately. Original PLYs remain untouched.</p><aside id="live">Loading live status…</aside>'
    for r in reversed(rows):
        html += f'<section><h2>{r["number"]:03d} · {r["title"]}</h2><p>{r["utc"]} · {r["status"]}</p><p>{r["detail"]}</p>'
        html += ''.join(f'<a href="{p}"><img src="{p}"></a>' for p in r['images'])+'</section>'
    html += '<script>window.tf4dgsReportReady=true;window.tf4dgsReportStage='+str(len(rows))+';setInterval(async()=>{if(window.tf4dgsFreezeReport)return;try{const p=await(await fetch("live_progress.json",{cache:"no-store"})).json();document.getElementById("live").textContent=p.model?`${p.model}: ${p.stage}, ${p.step}/${p.total}`:`${p.title}: ${p.status}`;const j=await(await fetch("journal.json",{cache:"no-store"})).json();if(j.length!==window.tf4dgsReportStage)location.reload();}catch(e){}},3000);</script>'
    (DOCS/'index.html').write_text(html, encoding='utf8')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while data := f.read(8*1024*1024):
            h.update(data)
    return h.hexdigest()


def read_ply(path):
    names=[]; count=None
    with path.open('rb') as f:
        lines=[]
        while True:
            line=f.readline(); lines.append(line)
            if len(lines)>150: raise ValueError('Unsupported PLY header')
            text=line.decode('ascii').strip()
            if text.startswith('element vertex '): count=int(text.split()[-1])
            if text.startswith('property '):
                _,kind,name=text.split()
                if kind not in ('float','float32'): raise ValueError('Only standard float Gaussian PLY supported')
                names.append(name)
            if text=='end_header': break
        offset=f.tell()
    if b'format binary_little_endian 1.0' not in b''.join(lines): raise ValueError('Unsupported PLY format')
    if path.stat().st_size!=offset+count*len(names)*4: raise ValueError('PLY size/header mismatch')
    data=np.memmap(path, mode='r', dtype=[(n,'<f4') for n in names], offset=offset, shape=count)
    return data,names,b''.join(lines)


def unpack(f, fmt):
    return struct.unpack('<'+fmt, f.read(struct.calcsize('<'+fmt)))


def cameras(dataset):
    params_count={0:3,1:4,2:4,3:5,4:8,5:8,6:12,7:5,8:4,9:5,10:12,11:16}
    cam={}
    with (dataset/'sparse/cameras.bin').open('rb') as f:
        for _ in range(unpack(f,'Q')[0]):
            cid,model,w,h=unpack(f,'iiQQ'); p=unpack(f,'d'*params_count[model])
            if model==1: fx,fy,cx,cy=p
            elif model==0: fx,cx,cy=p;fy=fx
            else: raise ValueError(f'Expected undistorted PINHOLE cameras, found model {model}')
            cam[cid]=dict(width=w,height=h,K=[[fx,0,cx],[0,fy,cy],[0,0,1]],model=model)
    views=[]
    with (dataset/'sparse/images.bin').open('rb') as f:
        for _ in range(unpack(f,'Q')[0]):
            values=unpack(f,'idddddddi'); iid=values[0];q=values[1:5];t=values[5:8];cid=values[8]
            chars=bytearray()
            while (b:=f.read(1))!=b'\0':
                if not b: raise EOFError('image name')
                chars+=b
            name=chars.decode('utf8'); n=unpack(f,'Q')[0];f.seek(n*24,1)
            path=dataset/'images'/name
            if not path.exists(): raise FileNotFoundError(path)
            v=np.eye(4);v[:3,:3]=Rotation.from_quat([q[1],q[2],q[3],q[0]]).as_matrix();v[:3,3]=t
            c=cam[cid];size=Image.open(path).size
            if size!=(c['width'],c['height']): raise ValueError(f'Camera/image size mismatch: {name}')
            views.append(dict(name=name,image=str(path),image_id=iid,camera_id=cid,view=v.tolist(),**c))
    return sorted(views,key=lambda v:v['name'])


def scaled(v,edge):
    s=min(1.,edge/max(v['width'],v['height']))
    # Multiples of eight for diffusion's encoder; full frame with exact K scale.
    w=max(8,int(round(v['width']*s/8))*8);h=max(8,int(round(v['height']*s/8))*8)
    K=np.array(v['K'],np.float32);K[0]*=w/v['width'];K[1]*=h/v['height']
    return w,h,K


def load_model(path,train=False):
    data,names,header=read_ply(path)
    def tensor(fields):
        a=np.stack([data[n] for n in fields],axis=1)
        if not np.isfinite(a).all(): raise ValueError(f'Nonfinite PLY: {fields}')
        return torch.tensor(a,device='cuda')
    rest=sorted([n for n in names if n.startswith('f_rest_')],key=lambda n:int(n[7:]))
    if len(rest)!=45: raise ValueError('Expected SH3 Gaussian PLY')
    m=dict(means=tensor(['x','y','z']),quats=tensor(['rot_'+str(i) for i in range(4)]),
           scales=tensor(['scale_'+str(i) for i in range(3)]),opacities=tensor(['opacity']).flatten(),
           sh0=tensor(['f_dc_'+str(i) for i in range(3)])[:,None,:],
           shN=tensor(rest).reshape(len(data),3,15).transpose(1,2).contiguous())
    if train:m={k:torch.nn.Parameter(v) for k,v in m.items()}
    return m,(data,names,header)


def render(m,v,edge):
    w,h,K=scaled(v,edge)
    rgb,alpha,info=rasterization(means=m['means'],quats=m['quats'],scales=m['scales'].exp(),
        opacities=m['opacities'].sigmoid(),colors=torch.cat((m['sh0'],m['shN']),dim=1),
        viewmats=torch.tensor(v['view'],device='cuda',dtype=torch.float32)[None],
        Ks=torch.tensor(K,device='cuda')[None],width=w,height=h,sh_degree=3,
        packed=True,near_plane=.01,far_plane=1e6,rasterize_mode='classic',render_mode='RGB')
    return rgb[0].clamp(0,1),alpha[0,...,0]


def rgb_image(t):
    return Image.fromarray((t.detach().cpu().numpy().clip(0,1)*255).round().astype('uint8'))


def montage(path, rows, labels):
    # Documentation layout only: photographs and actual renderings are labelled.
    cellw,cellh=480,350;canvas=Image.new('RGB',(cellw*len(labels),cellh*len(rows)),(16,24,32));draw=ImageDraw.Draw(canvas)
    for r,row in enumerate(rows):
        for c,item in enumerate(row):
            image=Image.open(item).convert('RGB') if isinstance(item,(str,Path)) else item.copy()
            image.thumbnail((cellw-8,cellh-35))
            canvas.paste(image,(c*cellw+(cellw-image.width)//2,r*cellh+30))
            draw.text((c*cellw+8,r*cellh+8),labels[c],fill='white')
    canvas.save(path,quality=92,subsampling=0)


def select_views(views,count):
    # Uniform ordered capture sampling, deterministic across all eight PLYs.
    return [views[i] for i in np.linspace(0,len(views)-1,min(count,len(views))).round().astype(int)]


def aligned_views(views,entry):
    alignment=entry.get('alignment')
    if not alignment:return views
    Q=np.array(alignment['rotation']);s=alignment['scale'];t=np.array(alignment['translation']);out=[]
    for original in views:
        v=dict(original);c=np.linalg.inv(v['view']);edited=np.eye(4)
        edited[:3,:3]=Q@c[:3,:3];edited[:3,3]=s*Q@c[:3,3]+t
        v['view']=np.linalg.inv(edited).tolist();out.append(v)
    return out


def novel_views(anchors):
    result=[]
    for index,a in enumerate(anchors[::2]):
        ca=np.linalg.inv(a['view']); candidates=[]
        for b in anchors:
            if b['name']==a['name']:continue
            cb=np.linalg.inv(b['view'])
            angle=Rotation.from_matrix(ca[:3,:3].T@cb[:3,:3]).magnitude()
            if .025<angle<.7 and (a['width']>a['height'])==(b['width']>b['height']):
                candidates.append((np.linalg.norm(ca[:3,3]-cb[:3,3]),b,cb))
        if not candidates:continue
        _,b,cb=min(candidates,key=lambda x:x[0]);out=ca.copy()
        out[:3,:3]=Slerp([0,1],Rotation.from_matrix(np.stack([ca[:3,:3],cb[:3,:3]])))([.35]).as_matrix()[0]
        out[:3,3]=ca[:3,3]*.65+cb[:3,3]*.35
        v=dict(a);v.update(name=f'novel_{index:03d}',view=np.linalg.inv(out).tolist(),reference=a['image'],reference_name=a['name'])
        result.append(v)
    return result


def inspect(dataset,folders):
    views=cameras(dataset);files=[]
    old_path=WORK/'manifest.json'
    previous=json.loads(old_path.read_text()).get('files',[]) if old_path.exists() else []
    for folder in folders:
        for path in sorted(folder.glob('*.ply')):
            if '_Difix3D' in path.stem:continue
            data,names,header=read_ply(path)
            entry=dict(path=str(path),name=path.name,folder=folder.name,count=len(data),bytes=path.stat().st_size,
                sha256=sha(path),output=str(path.with_name(path.stem+'_Difix3D.ply')))
            for old in previous:
                if old['path']==entry['path'] and old['sha256']==entry['sha256'] and 'alignment' in old:
                    entry['alignment']=old['alignment']
            files.append(entry)
    manifest=dict(schema_version=1,dataset=str(dataset),files=files,views=views,
                  source_commit='c76edc595586e16732c91ddee82f3a6d83a8a9cc',model_id='nvidia/difix_ref',
                  scope='Bounded source-guided 3D refinement adapter, not full paper reproduction; audit views were used in original training.')
    write_json(WORK/'manifest.json',manifest)
    write_json(DOCS/'input_inventory.json',dict(files=[{k:v for k,v in x.items() if k not in ('path','output')} for x in files],camera_count=len({v['camera_id'] for v in views}),registered_images=len(views)))
    stage('Inputs audited',f'{len(files)} SH3 PLYs, {len(views)} matching calibrated images. Original SHA256 hashes recorded; originals will remain untouched.')
    print(json.dumps(dict(files=len(files),cameras=len({v['camera_id'] for v in views}),images=len(views))),flush=True)


def wide_views(m,anchors):
    focus=np.median(m['means'].detach().cpu().numpy(),axis=0)
    broad=[v for v in anchors if v['name'].startswith('DJI')]
    broad=select_views(broad,4) if broad else select_views(anchors,4)
    result=[]
    for index,a in enumerate(broad):
        C=np.linalg.inv(a['view']);up=-C[:3,1];offset=C[:3,3]-focus
        for angle in [-35,-20,20,35]:
            pos=focus+Rotation.from_rotvec(up*np.deg2rad(angle)).apply(offset)
            f=focus-pos;f/=np.linalg.norm(f);right=np.cross(f,up);right/=np.linalg.norm(right);down=np.cross(f,right)
            c=np.eye(4);c[:3,:3]=np.column_stack([right,down,f]);c[:3,3]=pos
            v=dict(a);v.update(name=f'wide_{index}_{angle:+d}',view=np.linalg.inv(c).tolist(),reference=a['image'],reference_name=a['name'])
            result.append(v)
    return result


def prepare(entry,manifest,edge):
    directory=WORK/entry['folder']/(Path(entry['name']).stem+entry.get('work_suffix',''));directory.mkdir(parents=True,exist_ok=True)
    target_file=directory/'targets.json'
    if target_file.exists():return directory
    views=aligned_views(manifest['views'],entry)
    m,_=load_model(Path(entry['path']));anchors=select_views(views,48);audit=select_views(views[2::8],9)
    novels=novel_views(anchors)
    if entry.get('recipe')!='baseline':novels+=wide_views(m,anchors)
    targets=[];rows=[]
    write_json(DOCS/'live_progress.json',dict(model=entry['name'],stage='baseline render',step=0,total=len(anchors+novels+audit)))
    with torch.no_grad():
        for i,v in enumerate(anchors+novels+audit):
            kind='anchor' if i<len(anchors) else 'novel' if i<len(anchors)+len(novels) else 'audit'
            rgb,alpha=render(m,v,edge);image_path=directory/f'{kind}_{i:03d}_before.png';rgb_image(rgb).save(image_path)
            mask_path=directory/f'{kind}_{i:03d}_alpha.npy';np.save(mask_path,alpha.cpu().numpy().astype(np.float16))
            record=dict(view=v,kind=kind,before=str(image_path),alpha=str(mask_path))
            if kind=='anchor' or kind=='audit':
                reference_path=directory/f'{kind}_{i:03d}_reference.png'
                Image.open(v['image']).convert('RGB').resize(rgb_image(rgb).size,Image.Resampling.LANCZOS).save(reference_path)
                record['target']=str(reference_path)
            else:
                reference_path=directory/f'{kind}_{i:03d}_reference.png'
                Image.open(v['reference']).convert('RGB').resize(rgb_image(rgb).size,Image.Resampling.LANCZOS).save(reference_path)
                record['reference']=str(reference_path);record['target']=str(directory/f'{kind}_{i:03d}_difix.png')
            targets.append(record)
            if kind=='audit' and len(rows)<3: rows.append([record['target'],record['before']])
            if (i+1)%15==0:write_json(DOCS/'live_progress.json',dict(model=entry['name'],stage='baseline render',step=i+1,total=len(anchors+novels+audit)))
    del m;gc.collect();torch.cuda.empty_cache()
    evidence=entry['folder']+'_'+directory.name+'_before.jpg'
    montage(DOCS/evidence,rows,['Original photograph','Actual input Gaussian render'])
    write_json(target_file,dict(edge=edge,records=targets))
    wide_count=sum(v['name'].startswith('wide_') for v in novels)
    stage('Camera-aligned baseline: '+entry['name'],f'{entry["count"]:,} original Gaussians. {len(novels)-wide_count} near-camera interpolations and {wide_count} wider orbit repair poses; same capture sampling across variants.',[evidence])
    return directory


def fix(directory):
    targets=json.loads((directory/'targets.json').read_text());novels=[x for x in targets['records'] if x['kind']=='novel']
    if all(Path(x['target']).exists() for x in novels):return
    sys.path.insert(0,str(SOURCE/'src'))
    from pipeline_difix import DifixPipeline
    pipe=DifixPipeline.from_pretrained('nvidia/difix_ref',revision=MODEL_REVISION,torch_dtype=torch.float16,trust_remote_code=True,
                                     cache_dir=str(ROOT/'.local/cache/difix3d'))
    pipe.to('cuda');pipe.enable_vae_slicing();pipe.set_progress_bar_config(disable=True)
    for i,t in enumerate(novels):
        if Path(t['target']).exists():continue
        image=Image.open(t['before']).convert('RGB');ref=Image.open(t['reference']).convert('RGB')
        result=pipe('remove degradation',image=image,ref_image=ref,num_inference_steps=1,
            timesteps=[199],guidance_scale=0.,generator=torch.Generator(device='cuda').manual_seed(42+i)).images[0]
        if result.size!=image.size:raise ValueError('Difix changed target dimensions')
        result.save(t['target']);print(f'Difix target {i+1}/{len(novels)}',flush=True)
        if (i+1)%4==0:write_json(DOCS/'live_progress.json',dict(model=directory.name,stage='diffusion target generation',step=i+1,total=len(novels)))
    del pipe;gc.collect();torch.cuda.empty_cache()
    evidence=directory.parent.name+'_'+directory.name+'_diffusion_targets.jpg'
    montage(DOCS/evidence,[[x['before'],x['target'],x['reference']] for x in novels[:3]],['Input novel-view render','Difix image target (not exported 3D)','Reference photograph'])
    stage('Diffusion targets: '+directory.name,f'{len(novels)} targets generated by official nvidia/difix_ref. These images are pseudo-supervision, not proof of improved geometry.',[evidence])


def evaluate(m,records,edge,directory,tag):
    metrics=[];images=[]
    with torch.no_grad():
        for i,t in enumerate(records):
            rgb,_=render(m,t['view'],edge);gt=torch.tensor(np.asarray(Image.open(t['target'])).copy(),device='cuda',dtype=torch.float32)/255
            mse=(rgb-gt).square().mean().item();mask=torch.tensor(np.load(t['alpha']).astype(np.float32),device='cuda')>.05
            support=((rgb-gt).square()*mask[...,None]).sum()/(3*mask.sum().clamp_min(1))
            metrics.append(dict(name=t['view']['name'],psnr=-10*math.log10(max(mse,1e-12)),support_psnr=-10*math.log10(max(support.item(),1e-12))))
            path=directory/f'audit_{i:03d}_{tag}.png';rgb_image(rgb).save(path);images.append(str(path))
    return dict(mean_psnr=float(np.mean([x['psnr'] for x in metrics])),mean_support_psnr=float(np.mean([x['support_psnr'] for x in metrics])),views=metrics),images


def export(path,m,layout):
    if path.exists():raise FileExistsError('Refusing to overwrite '+str(path))
    original,names,header=layout;fields={}
    for k,cols in [('means',['x','y','z']),('quats',['rot_'+str(i) for i in range(4)]),('scales',['scale_'+str(i) for i in range(3)])]:
        a=m[k].detach().cpu().numpy()
        for i,n in enumerate(cols):fields[n]=a[:,i]
    fields['opacity']=m['opacities'].detach().cpu().numpy()
    dc=m['sh0'].detach().cpu().numpy()[:,0,:];rest=m['shN'].detach().cpu().numpy().transpose(0,2,1).reshape(len(original),45)
    for i in range(3):fields[f'f_dc_{i}']=dc[:,i]
    for i in range(45):fields[f'f_rest_{i}']=rest[:,i]
    tmp=path.with_name(path.name+'.tmp')
    with tmp.open('wb') as f:
        f.write(header)
        for start in range(0,len(original),100000):
            end=min(start+100000,len(original));a=np.array(original[start:end],copy=True)
            for n,value in fields.items():a[n]=value[start:end]
            if any(not np.isfinite(a[n]).all() for n in names):raise FloatingPointError('Nonfinite export')
            f.write(a.tobytes())
    tmp.rename(path)
    del fields


def refine(entry,directory,steps,edge):
    output=Path(entry['output'])
    if output.exists():
        if output.with_suffix('.difix3d.json').exists():return
        raise FileExistsError('Output exists without matching provenance')
    targets=json.loads((directory/'targets.json').read_text());audit=[x for x in targets['records'] if x['kind']=='audit']
    m,layout=load_model(Path(entry['path']),True);before,before_images=evaluate(m,audit,targets['edge'],directory,'before_audit')
    checkpoint=directory/'refinement.pth';initial=0
    rates={'means':1e-6,'scales':2e-4,'quats':1e-4,'opacities':2e-3,'sh0':1e-4,'shN':2e-6}
    recipe=entry.get('recipe','baseline')
    if recipe!='baseline':rates={'means':1.6e-5,'scales':1e-3,'quats':2e-4,'opacities':.01,'sh0':5e-5,'shN':2.5e-6}
    if recipe=='wide_strong':rates.update(means=3.2e-5,opacities=.02,scales=.002)
    # Geometry LR scaled to capture size, preserving COLMAP's original coordinates.
    centers=np.array([np.linalg.inv(t['view']['view'])[:3,3] for t in targets['records'] if t['kind']=='anchor'])
    extent=float(np.median(np.linalg.norm(centers-centers.mean(0),axis=1)));rates['means']*=extent
    optim={k:torch.optim.Adam([v],lr=rates[k],foreach=False) for k,v in m.items()}
    if checkpoint.exists():
        cp=torch.load(checkpoint,map_location='cuda',weights_only=False)
        for k in m:m[k].data.copy_(cp['model'][k]);optim[k].load_state_dict(cp['optimizers'][k])
        initial=cp['step'];del cp
    anchors=[x for x in targets['records'] if x['kind']=='anchor'];novels=[x for x in targets['records'] if x['kind']=='novel']
    if not novels:raise ValueError('No valid novel-view repair poses')
    rng=np.random.default_rng(42);cache={};start=time.perf_counter();torch.cuda.reset_peak_memory_stats();last_loss=0
    for step in range(initial,steps):
        # Approximately 70% source anchoring, 30% repaired novel-view supervision.
        group=novels if step%10 in ((6,7,8,9) if recipe!='baseline' else (7,8,9)) else anchors
        t=group[int(np.random.default_rng(42+step).integers(len(group)))];v=t['view']
        key=t['target']
        if key not in cache:
            w,h,_=scaled(v,edge)
            gt=np.asarray(Image.open(key).convert('RGB').resize((w,h),Image.Resampling.LANCZOS)).copy()/255.
            a=Image.fromarray(np.load(t['alpha']).astype(np.float32)).resize((w,h),Image.Resampling.BILINEAR)
            cache[key]=(torch.tensor(gt,dtype=torch.float32,device='cuda'),torch.tensor(np.asarray(a).copy(),device='cuda'))
        gt,alpha=cache[key];rgb,_=render(m,v,edge)
        # Isolated variants stay isolated: do not introduce background outside support.
        weight=(alpha>.02).float()[...,None];denom=(3*weight.sum()).clamp_min(1)
        loss=((rgb-gt).abs()*weight).sum()/denom
        if group is novels:loss*=.5 if recipe!='baseline' else .3
        if recipe=='wide_strong':
            loss+=.001*m['opacities'].sigmoid().mean()+.002*m['scales'].exp().mean()/max(extent,1e-6)
        if not torch.isfinite(loss):raise FloatingPointError(f'Loss at {step}')
        loss.backward()
        for optimizer in optim.values():optimizer.step();optimizer.zero_grad(set_to_none=True)
        last_loss=float(loss.item())
        if (step+1)%50==0:
            write_json(DOCS/'live_progress.json',dict(model=entry['name'],stage='3D refinement',step=step+1,total=steps,loss=last_loss,elapsed_s=time.perf_counter()-start,peak_cuda_gib=torch.cuda.max_memory_allocated()/2**30))
            print(f'{entry["name"]} refinement {step+1}/{steps} loss={last_loss:.5f}',flush=True)
        if (step+1)%250==0 or step+1==steps:
            torch.save(dict(step=step+1,model={k:v.detach() for k,v in m.items()},optimizers={k:o.state_dict() for k,o in optim.items()}),checkpoint.with_suffix('.tmp'))
            checkpoint.with_suffix('.tmp').replace(checkpoint)
    after,after_images=evaluate(m,audit,targets['edge'],directory,'refined')
    export(output,m,layout);data,names,_=read_ply(output)
    if len(data)!=entry['count'] or sha(Path(entry['path']))!=entry['sha256']:raise ValueError('Export count or original hash verification failed')
    result=dict(input=entry['name'],output=output.name,source_sha256=entry['sha256'],output_sha256=sha(output),
        original_preserved=True,gaussians=len(data),diffusion_model='nvidia/difix_ref',difix_commit='c76edc595586e16732c91ddee82f3a6d83a8a9cc',
        weights_revision=MODEL_REVISION,adapter=Path(__file__).name,steps=steps,training_edge=edge,target_edge=targets['edge'],
        camera_alignment=entry.get('alignment'),
        recipe=recipe,learning_rates=rates,novel_target_count=len(novels),
        loss_settings=dict(novel_probability=.4 if recipe!='baseline' else .3,novel_weight=.5 if recipe!='baseline' else .3,
                           opacity_regularization=.001 if recipe=='wide_strong' else 0,scale_regularization=.002 if recipe=='wide_strong' else 0),
        before=before,after=after,peak_cuda_gib=torch.cuda.max_memory_allocated()/2**30,
        scope='Short 3D refinement test. Audit cameras are not independently held-out from original training. Pseudo-targets are generative. No final neural image enhancement applied.',
        appearance='PPISP is not applied by this gsplat adapter. Output retains canonical SH representation; no unchanged PPISP companion is attached.',
        elapsed_refine_s=time.perf_counter()-start)
    write_json(output.with_suffix('.difix3d.json'),result);write_json(DOCS/(entry['folder']+'_'+directory.name+'_result.json'),result)
    evidence=entry['folder']+'_'+directory.name+'_comparison.jpg'
    montage(DOCS/evidence,[[audit[i]['target'],before_images[i],after_images[i]] for i in range(min(3,len(audit)))],['Original photograph','Input PLY render','Refined PLY render (no image enhancer)'])
    location='ignored prototype folder' if entry.get('recipe','baseline')!='baseline' else 'original folder, with _Difix3D suffix'
    stage('Exported 3D repair test: '+entry['name'],f'{len(data):,} Gaussians, {steps} updates. Camera audit PSNR {before["mean_psnr"]:.2f} to {after["mean_psnr"]:.2f} dB. Output saved in {location}; improvement of novel-view geometry is not established by this score.',[evidence],status='test exported; visual review required')
    del m,optim,cache,layout,data;gc.collect();torch.cuda.empty_cache()


def verify(entry,directory):
    output=Path(entry['output']);result=json.loads(output.with_suffix('.difix3d.json').read_text())
    targets=json.loads((directory/'targets.json').read_text());audit=[x for x in targets['records'] if x['kind']=='audit']
    novel=[x for x in targets['records'] if x['kind']=='novel'];m,_=load_model(output)
    metrics,images=evaluate(m,audit,targets['edge'],directory,'reopened')
    delta=abs(metrics['mean_psnr']-result['after']['mean_psnr'])
    if delta>1e-4:raise ValueError(f'Reopened PLY differs from in-memory result: {delta}')
    rows=[]
    review=[x for x in novel if x['view']['name'].startswith('wide_')][:4]+novel[:2] if entry.get('recipe','baseline')!='baseline' else novel[:6]
    with torch.no_grad():
        for i,t in enumerate(review):
            rgb,_=render(m,t['view'],targets['edge']);path=directory/f'novel_{i:03d}_reopened.png';rgb_image(rgb).save(path)
            rows.append([t['before'],str(path),t['target']])
    evidence=entry['folder']+'_'+directory.name+'_novel_comparison.jpg'
    montage(DOCS/evidence,rows,['Original PLY: novel view','Reopened Difix3D PLY: same view','Difix target image (generative)'])
    result['reopened_ply_verified']=True;result['reopened_psnr_delta_db']=delta
    write_json(output.with_suffix('.difix3d.json'),result);write_json(DOCS/(entry['folder']+'_'+directory.name+'_result.json'),result)
    stage('Saved PLY reopened: '+entry['name'],'All exported attributes decoded and rendered. Camera scores match the in-memory result. Novel-view comparisons show actual 3D output independently of the diffusion image enhancer.',[evidence],status='export verified; quality requires review')
    del m;gc.collect();torch.cuda.empty_cache()


def stress(entry,manifest,directory):
    """Test broader +/-45 degree camera orbit; no generative enhancement."""
    views=aligned_views(manifest['views'],entry)
    candidates=[v for v in views if v['name'].startswith('DJI')]
    reference=candidates[2] if len(candidates)>2 else views[0]
    original,_=load_model(Path(entry['path']));v=torch.tensor(reference['view'],device='cuda',dtype=torch.float32)
    with torch.no_grad():
        p=original['means']@v[:3,:3].T+v[:3,3];K=torch.tensor(reference['K'],device='cuda')
        uv=p@K.T;uv=uv[:,:2]/uv[:,2:3].clamp_min(1e-8)
        keep=(p[:,2]>.05)&(original['opacities'].sigmoid()>.25)&((uv[:,0]-K[0,2]).abs()<reference['width']*.12)&((uv[:,1]-K[1,2]).abs()<reference['height']*.12)
        if keep.sum()<100:raise ValueError('Insufficient central surface support for orbit')
        c=np.linalg.inv(reference['view'])
        focus=np.median(original['means'].detach().cpu().numpy(),axis=0);up=-c[:3,1];offset=c[:3,3]-focus
        orbit=[];before=[]
        for i,angle in enumerate([-45,-22.5,0,22.5,45]):
            pos=focus+Rotation.from_rotvec(up*np.deg2rad(angle)).apply(offset);forward=focus-pos;forward/=np.linalg.norm(forward)
            right=np.cross(forward,up);right/=np.linalg.norm(right);down=np.cross(forward,right)
            C=np.eye(4);C[:3,:3]=np.column_stack([right,down,forward]);C[:3,3]=pos
            q=dict(reference);q['view']=np.linalg.inv(C).tolist();q['name']=f'orbit_{angle:+g}'
            rgb,_=render(original,q,1024);path=directory/f'stress_{i:02d}_before.png';rgb_image(rgb).save(path)
            before.append(str(path));orbit.append(q)
    del original;gc.collect();torch.cuda.empty_cache();refined,_=load_model(Path(entry['output']));after=[]
    with torch.no_grad():
        for i,q in enumerate(orbit):
            rgb,_=render(refined,q,1024);path=directory/f'stress_{i:02d}_after.png';rgb_image(rgb).save(path);after.append(str(path))
    evidence=entry['folder']+'_'+directory.name+'_orbit_stress.jpg'
    montage(DOCS/evidence,[[a,b] for a,b in zip(before,after)],['Original PLY: orbit -45 to +45 deg','Difix3D PLY: identical orbit'])
    write_json(directory/'orbit_cameras.json',dict(reference=reference['name'],focus=focus.tolist(),views=orbit,scope='Visual stress test; no ground truth at these novel viewpoints'))
    stage('Broader orbit stress test: '+entry['name'],'Five matched orbit views from -45 to +45 degrees. Both columns are actual splat renderings with no final image enhancement. New views have no ground truth; residual floaters and streaks must be judged visually.',[evidence],status='visual comparison recorded')
    del refined;gc.collect();torch.cuda.empty_cache()


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['audit','prepare','fix','refine','verify','stress','batch'],required=True)
    p.add_argument('--dataset',default=r'C:\Users\mnijat\Desktop\Necto\NightV1\colmap')
    p.add_argument('--folders',nargs='+',default=[r'C:\Users\mnijat\Desktop\Necto\NightV1\MRNF_2m-90k',r'C:\Users\mnijat\Desktop\Necto\NightV1\MRNF_5m-210k'])
    p.add_argument('--index',type=int);p.add_argument('--target-edge',type=int,default=1024);p.add_argument('--training-edge',type=int,default=768);p.add_argument('--steps',type=int,default=750)
    p.add_argument('--recipe',choices=['baseline','wide_official','wide_strong'],default='baseline')
    args=p.parse_args();torch.set_num_threads(6)
    if args.stage=='audit':inspect(Path(args.dataset),[Path(x) for x in args.folders]);return
    manifest=json.loads((WORK/'manifest.json').read_text());entries=manifest['files'] if args.index is None else [manifest['files'][args.index]]
    for entry in entries:
        try:
            entry=dict(entry);entry['recipe']=args.recipe
            if args.recipe!='baseline':
                entry['work_suffix']='_'+args.recipe
                entry['output']=str(WORK/'tuning'/entry['folder']/(Path(entry['name']).stem+'_'+args.recipe+'_Difix3D.ply'))
                Path(entry['output']).parent.mkdir(parents=True,exist_ok=True)
            directory=WORK/entry['folder']/(Path(entry['name']).stem+entry.get('work_suffix',''))
            if args.stage in ('prepare','batch'):directory=prepare(entry,manifest,args.target_edge)
            if args.stage in ('fix','batch'):fix(directory)
            if args.stage in ('refine','batch'):refine(entry,directory,args.steps,args.training_edge)
            if args.stage in ('verify','batch'):verify(entry,directory)
            if args.stage=='stress':stress(entry,manifest,directory)
        except Exception as e:
            trace=traceback.format_exc();directory.mkdir(parents=True,exist_ok=True)
            (directory/'failure.log').write_text(trace,encoding='utf8')
            stage('Failed attempt: '+entry['name'],str(e),status='failed; preserved for diagnosis')
            raise


if __name__=='__main__':main()
