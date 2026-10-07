"""Fit current-capture static Gaussians with native RGB patches.

Keep the measured tabletop on z=0. Off-table geometry may move within a bounded
depth-prior neighborhood. Scores measure reconstruction of the three input
cameras, not independent novel-view or metric accuracy. Output remains separate
from the moving actor, and joins it only during 3D rasterization.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageDraw, ImageOps
import torch
import torch.nn.functional as F
from gsplat import rasterization


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,obj):Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--initialization',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--steps',type=int,default=3000);p.add_argument('--patch',type=int,default=640)
    p.add_argument('--colors-only',action='store_true',help='Conservative appearance refinement; preserve depth, footprints and opacity')
    args=p.parse_args();out=args.output;root=args.initialization
    if out.exists():raise ValueError('Preserve earlier attempts; choose a new output')
    if not 1<=args.steps<=30000 or not 256<=args.patch<=1024:raise ValueError('Invalid training budget')
    out.mkdir(parents=True);torch.manual_seed(42);torch.set_num_threads(4);rng=np.random.default_rng(42);device='cuda'
    provenance=read(root/'initialization.json');session=read(provenance['session'])
    if provenance['source_policy']!='current capture only':raise ValueError('Background source policy mismatch')
    data=np.load(root/'initial_background.npz');anchor=torch.tensor(data['means'],device=device)
    plane=torch.tensor(np.load(root/'plane_flags.npy'),device=device);n=len(anchor)
    offset=torch.nn.Parameter(torch.zeros_like(anchor));baseq=torch.tensor(data['quats'],device=device)
    qoffset=torch.nn.Parameter(torch.zeros_like(baseq));initial_scales=torch.tensor(data['scales'],device=device)
    logs=torch.nn.Parameter(initial_scales.log());logits=torch.nn.Parameter(torch.logit(torch.tensor(data['opacity'],device=device)))
    colors=torch.nn.Parameter(torch.logit(torch.tensor(data['colors'],device=device).clamp(.005,.995)))
    bounds=torch.minimum(initial_scales.max(-1).values*.4,torch.full((n,),.025,device=device))
    # Plane geometry stays measured; RGB/opacity/scales are fitted to all views.
    bounds[plane]=0
    optimizer=torch.optim.Adam([{'params':[offset],'lr':.002},{'params':[qoffset],'lr':.001},
        {'params':[logs],'lr':.003},{'params':[logits],'lr':.012},{'params':[colors],'lr':.02}])
    if args.colors_only:
        for param in [offset,qoffset,logs,logits]:param.requires_grad_(False)
        optimizer=torch.optim.Adam([colors],lr=.001)
    records=[]
    for cid in ['iphone','fuji','dji']:
        entry=next(c for c in session['cameras'] if c['id']==cid)
        c=read(Path(provenance['session']).parent/entry['calibration']);a=c['params']
        K=torch.tensor([[a[0],0,a[2]],[0,a[1],a[3]],[0,0,1.]],dtype=torch.float32,device=device)
        view=torch.eye(4,device=device);view[:3,:3]=torch.tensor(c['world_to_camera']['R'],device=device);view[:3,3]=torch.tensor(c['world_to_camera']['t'],device=device)
        source=np.array(Image.open(root/f'{cid}_empty.png').convert('RGB')).astype(np.float32)/255.
        source=np.clip(source*np.array(provenance['cameras'][cid]['rgb_gain_to_iphone']),0,1).astype(np.float32)
        mask=np.array(Image.open(root/f'{cid}_valid_mask.png'))>0
        records.append({'cid':cid,'target':torch.tensor(source,device=device),'mask':torch.tensor(mask,device=device),
            'K':K,'view':view,'height':source.shape[0],'width':source.shape[1]})
    def model():
        q=F.normalize(baseq+.15*qoffset.tanh()*(~plane)[:,None],dim=-1)
        return {'means':anchor+bounds[:,None]*offset.tanh(),'quats':q,
          'scales':logs.exp().maximum(initial_scales*.25).minimum(initial_scales*2),
          'opacity':logits.sigmoid(),'colors':colors.sigmoid()}
    def render(m,r,crop=None,factor=1.):
        if crop:
            x,y,w,h=crop;K=r['K'].clone();K[0,2]-=x;K[1,2]-=y
        else:
            w=round(r['width']*factor);h=round(r['height']*factor);K=r['K'].clone();K[:2]*=factor
        rgb,alpha,_=rasterization(m['means'],m['quats'],m['scales'],m['opacity'],m['colors'],
          r['view'][None],K[None],w,h,packed=False,near_plane=.01,far_plane=10,rasterize_mode='antialiased')
        return rgb[0]+(1-alpha[0])*.92,alpha[0,:,:,0]
    start=time.perf_counter();history=[];best=math.inf;best_step=0
    @torch.no_grad()
    def evaluate(step,save=False):
        m=model();metrics=[];sheet=Image.new('RGB',(1500,430*len(records)),'#17212b');draw=ImageDraw.Draw(sheet)
        for row,r in enumerate(records):
            factor=min(1.,1100/max(r['width'],r['height']));rgb,alpha=render(m,r,factor=factor)
            target=F.interpolate(r['target'].permute(2,0,1)[None],size=rgb.shape[:2],mode='area')[0].permute(1,2,0)
            mask=F.interpolate(r['mask'].float()[None,None],size=rgb.shape[:2],mode='nearest')[0,0]
            mse=((rgb-target).square().mean(-1)*mask).sum()/mask.sum().clamp_min(1)
            metrics.append({'camera':r['cid'],'input_fit_psnr_db':-10*math.log10(max(float(mse),1e-12)),
               'input_fit_mse':float(mse),'mean_alpha':float((alpha*mask).sum()/mask.sum().clamp_min(1))})
            if save:
                for col,(arr,label) in enumerate([(target,'current empty frame'),(rgb.clamp(0,1),'trained static Gaussians'),(alpha[:,:,None].expand(-1,-1,3),'Gaussian alpha')]):
                    im=Image.fromarray((arr.cpu().numpy()*255).astype(np.uint8));im=ImageOps.contain(im,(490,390))
                    sheet.paste(im,(col*500+(500-im.width)//2,row*430+35));draw.text((col*500+8,row*430+10),r['cid']+' | '+label,fill='white')
        result={'step':step,'mean_input_fit_mse':float(np.mean([r['input_fit_mse'] for r in metrics])),
          'cameras':metrics,'elapsed_s':time.perf_counter()-start,'independent_validation':False}
        if save:sheet.save(out/'input_fit_comparison.jpg',quality=94)
        return result
    def snapshot(step):
        m={k:v.detach().cpu() for k,v in model().items()};torch.save({'model':m,'step':step},out/'best_model.pt')
    def export():
        checkpoint=torch.load(out/'best_model.pt',map_location='cpu',weights_only=True);m=checkpoint['model']
        # Keep the stable opaque layer; discarded weak seeds are retained in .pt.
        keep=m['opacity']>=.05;m={k:v[keep] for k,v in m.items()}
        spec=importlib.util.spec_from_file_location('actor_export',Path('scripts/Train-RigidGaussianPilot.py'))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.save_ply(out/'static_background.ply',m)
        np.savez_compressed(out/'static_background.npz',**{k:v.numpy() for k,v in m.items()})
        summary={'status':'trained_current_capture_static_background','initial_gaussians':n,'gaussians':len(m['means']),
          'plane_gaussians':int(np.count_nonzero(np.load(root/'plane_flags.npy')[keep.numpy()])),
          'steps':args.steps,'selected_step':checkpoint['step'],'colors_only':args.colors_only,
          'initialization':root.as_posix(),'session':provenance['session'],'source_policy':provenance['source_policy'],
          'calibration_dir':provenance['calibration_dir'],'world_units':'metres','world_frame':'measured marker pattern; z into tabletop',
          'native_pixel_training':True,'patch_size':args.patch,'static_in_time':True,'metric_accuracy_verified':False,
          'independent_validation':False,'input_fit':history[-1],
          'elapsed_s':time.perf_counter()-start,'peak_cuda_bytes':torch.cuda.max_memory_allocated(),
          'limitations':provenance['assumptions']+['Three input cameras; this score is training-view fit, not unseen-view validation']}
        write(out/'summary.json',summary);print(json.dumps(summary),flush=True)
    write(out/'training_config.json',{'initialization':root.as_posix(),'steps':args.steps,'patch_size':args.patch,
      'native_pixel_training':True,'measured_plane_fixed':True,'source_policy':provenance['source_policy'],'seed':42})
    try:
        initial=evaluate(0,save=True);history.append(initial);print(json.dumps(initial),flush=True);best=initial['mean_input_fit_mse'];snapshot(0)
        for step in range(1,args.steps+1):
            r=records[(step-1)%len(records)];w=min(args.patch,r['width']);h=min(args.patch,r['height'])
            x=int(rng.integers(0,r['width']-w+1));y=int(rng.integers(0,r['height']-h+1))
            target=r['target'][y:y+h,x:x+w];valid=r['mask'][y:y+h,x:x+w].float()
            optimizer.zero_grad(set_to_none=True);m=model();rgb,alpha=render(m,r,[x,y,w,h])
            photo=((rgb-target).abs().mean(-1)*valid).sum()/valid.sum().clamp_min(1)
            # Low-cost local structural loss makes board marker edges less blurry.
            a=rgb.permute(2,0,1)[None];b=target.permute(2,0,1)[None]
            mean_a=F.avg_pool2d(a,7,1,3);mean_b=F.avg_pool2d(b,7,1,3)
            va=F.avg_pool2d(a*a,7,1,3)-mean_a.square();vb=F.avg_pool2d(b*b,7,1,3)-mean_b.square()
            cov=F.avg_pool2d(a*b,7,1,3)-mean_a*mean_b
            ssim=((2*mean_a*mean_b+.01**2)*(2*cov+.03**2))/((mean_a.square()+mean_b.square()+.01**2)*(va+vb+.03**2))
            structural=((1-ssim.mean(1)[0])*valid).sum()/valid.sum().clamp_min(1)
            coverage=((1-alpha)*valid).sum()/valid.sum().clamp_min(1)
            loss=(.95*photo+.05*structural) if args.colors_only else (.8*photo+.2*structural+.03*coverage+.0003*offset.tanh().square().mean())
            if not torch.isfinite(loss):raise ValueError('Non-finite background objective')
            loss.backward();optimizer.step()
            if step%100==0:print(json.dumps({'step':step,'loss':float(loss),'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
            if step%500==0 or step==args.steps:
                result=evaluate(step,save=True);history.append(result);write(out/'history.json',history);print(json.dumps(result),flush=True)
                if result['mean_input_fit_mse']<best:best=result['mean_input_fit_mse'];best_step=step;snapshot(step)
        torch.save({'model':{k:v.detach().cpu() for k,v in model().items()},'step':args.steps},out/'final_model.pt')
        # Report/display the actual selected checkpoint rather than the last step.
        selected=torch.load(out/'best_model.pt',map_location=device,weights_only=True)
        selected_model=selected['model'];model=lambda:selected_model
        history.append(evaluate(selected['step'],save=True));write(out/'history.json',history);export()
    except Exception as error:
        write(out/'failure.json',{'type':type(error).__name__,'message':str(error),'history':history});raise


if __name__=='__main__':main()
