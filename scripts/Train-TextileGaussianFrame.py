"""Fit actual multiview RGB Gaussians to a densely initialized textile frame.

Independent-frame fitting is an appearance/shape baseline. It does not assert
material identity across frames. Native crops are retained for final fitting.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
import torch
from gsplat import rasterization

sys.path.insert(0,str(Path(__file__).resolve().parent))
from importlib.machinery import SourceFileLoader
stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def initial_surface(data,upsample=5):
    points=data['points'];colors=data['colors'];vox=np.floor(points/.0007).astype(np.int64)
    _,index=np.unique(vox,axis=0,return_index=True);points=points[index];colors=colors[index]
    tree=cKDTree(points);distance,near=tree.query(points,k=min(20,len(points)))
    neighbor=points[near];delta=neighbor-neighbor.mean(axis=1,keepdims=True)
    _,vectors=np.linalg.eigh(np.einsum('nki,nkj->nij',delta,delta))
    normals=vectors[:,:,0];normals[normals[:,2]>0]*=-1
    tangent1=vectors[:,:,1];tangent2=np.cross(normals,tangent1)
    rng=np.random.default_rng(42)
    offsets=rng.normal(0,.00048,(len(points),upsample,2))
    expanded=points[:,None,:]+offsets[:,:,0:1]*tangent1[:,None]+offsets[:,:,1:2]*tangent2[:,None]
    expanded[:,0,:]=points
    xyz=expanded.reshape(-1,3).astype(np.float32);rgb=np.repeat(colors,upsample,axis=0).astype(np.float32)
    n=np.repeat(normals,upsample,axis=0)
    quats=np.c_[1+n[:,2],-n[:,1],n[:,0],np.zeros(len(n))]
    qnorm=np.linalg.norm(quats,axis=1);quats[qnorm<1e-7]=[0,1,0,0];quats/=np.linalg.norm(quats,axis=1,keepdims=True)
    return xyz,rgb,quats.astype(np.float32)


def records(session,masks,index,max_edge,color_balance=None):
    root=session.parent;bundles=stereo.read(root/'manifests/sync-plan.json')['bundles'];cams=stereo.cameras(session)
    result=[]
    for cid,c in cams.items():
        image=np.asarray(Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB')).copy()
        mask=np.asarray(Image.open(masks/'masks'/cid/f'frame_{index:06d}.png'))/255.
        occlusion=masks/'occlusions'/cid/f'frame_{index:06d}.png'
        occ=np.asarray(Image.open(occlusion))/255. if occlusion.exists() else np.zeros_like(mask)
        y,x=np.where(mask>.5);box=[max(0,x.min()-45),max(0,y.min()-45),min(image.shape[1],x.max()+46),min(image.shape[0],y.max()+46)]
        crop=image[box[1]:box[3],box[0]:box[2]];mask=mask[box[1]:box[3],box[0]:box[2]];occ=occ[box[1]:box[3],box[0]:box[2]]
        K=c['K'].copy();K[0,2]-=box[0];K[1,2]-=box[1]
        scale=min(1.,max_edge/max(crop.shape[:2])) if max_edge else 1.
        if scale<1:
            size=(round(crop.shape[1]*scale),round(crop.shape[0]*scale))
            sx=size[0]/crop.shape[1];sy=size[1]/crop.shape[0];K[0]*=sx;K[1]*=sy
            crop=cv2.resize(crop,size,interpolation=cv2.INTER_AREA);mask=cv2.resize(mask,size);occ=cv2.resize(occ,size)
        view=np.eye(4);view[:3,:3]=c['R'];view[:3,3]=c['t']
        target=crop/255.
        if color_balance:
            balance=color_balance['cameras'][cid];target=np.clip(target*np.array(balance['gain'])+np.array(balance['bias']),0,1)
        result.append(dict(camera=cid,target=torch.tensor(target,device='cuda',dtype=torch.float32),
            mask=torch.tensor(mask,device='cuda',dtype=torch.float32),occlusion=torch.tensor(occ,device='cuda',dtype=torch.float32),
            K=torch.tensor(K,device='cuda',dtype=torch.float32)[None],view=torch.tensor(view,device='cuda',dtype=torch.float32)[None],
            width=crop.shape[1],height=crop.shape[0],crop=[int(v) for v in box],resize_factor=scale,index=index,time_s=bundles[index]['time_s']))
    return result


def save_ply(path,m):
    xyz,rgb,opacity,scales,q=(m[k] for k in ['means','colors','opacity','scales','quats'])
    rest=m['sh'][:,1:].transpose(0,2,1).reshape(len(xyz),-1) if 'sh' in m else np.empty((len(xyz),0))
    values=np.c_[xyz,np.zeros_like(xyz),(rgb-.5)/.28209479177387814,rest,
                 np.log(np.clip(opacity,1e-6,1-1e-6)/(1-np.clip(opacity,1e-6,1-1e-6))),np.log(scales),q].astype('<f4')
    names=['x','y','z','nx','ny','nz','f_dc_0','f_dc_1','f_dc_2']+['f_rest_'+str(i) for i in range(rest.shape[1])]+['opacity','scale_0','scale_1','scale_2','rot_0','rot_1','rot_2','rot_3']
    header='ply\nformat binary_little_endian 1.0\nelement vertex '+str(len(xyz))+'\n'+''.join('property float '+n+'\n' for n in names)+'end_header\n'
    with path.open('wb') as f:f.write(header.encode('ascii'));f.write(values.tobytes())


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_03_video');p.add_argument('--dense',default='outputs/dynamic_textile_001/dense_stereo_02')
    p.add_argument('--output',default='outputs/dynamic_textile_001/gaussian_frame_02');p.add_argument('--index',type=int,default=0)
    p.add_argument('--steps',type=int,default=2500);p.add_argument('--max-edge',type=int,default=0);p.add_argument('--upsample',type=int,default=5)
    p.add_argument('--offset-mm',type=float,default=4.)
    p.add_argument('--color-balance')
    p.add_argument('--stop-psnr',type=float,default=0.,help='Optional all-camera fitting threshold after 3000 iterations')
    p.add_argument('--patch-size',type=int,default=0,help='Native-pixel stochastic crop; zero uses the full crop')
    p.add_argument('--sh-degree',type=int,choices=[0,1],default=0,help='Optional regularized view-dependent RGB')
    a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);torch.manual_seed(42);torch.set_num_threads(4);cv2.setNumThreads(2)
    balance=stereo.read(a.color_balance) if a.color_balance else None
    views=records(Path(a.session).resolve(),Path(a.masks),a.index,a.max_edge,balance)
    if a.patch_size:
        for v in views:v['fg_samples']=torch.nonzero(v['mask'][::8,::8]>.75).cpu().numpy()*8
    data=np.load(Path(a.dense)/f'frame_{a.index:06d}.npz');base,colors,q=initial_surface(data,a.upsample)
    anchor=torch.tensor(base,device='cuda');offset=torch.nn.Parameter(torch.zeros_like(anchor))
    quats=torch.nn.Parameter(torch.tensor(q,device='cuda'))
    logscale=torch.nn.Parameter(torch.log(torch.tensor([.00065,.00065,.00035],device='cuda').expand(len(base),3).clone()))
    opacity=torch.nn.Parameter(torch.full((len(base),),1.8,device='cuda'))
    color=torch.nn.Parameter(torch.logit(torch.tensor(colors,device='cuda').clamp(.01,.99)))
    sh_rest=torch.nn.Parameter(torch.zeros((len(base),3,3),device='cuda'))
    optim=torch.optim.Adam([{'params':[offset],'lr':.008},{'params':[quats],'lr':.003},
         {'params':[logscale],'lr':.006},{'params':[opacity],'lr':.01},{'params':[color],'lr':.025}])
    if a.sh_degree:optim.add_param_group({'params':[sh_rest],'lr':.008})
    def model():
        m=dict(means=anchor+(a.offset_mm/1000)*offset.tanh(),quats=torch.nn.functional.normalize(quats,dim=-1),
               scales=logscale.exp().clamp(.00008,.002),opacity=opacity.sigmoid(),colors=color.sigmoid())
        if a.sh_degree:m['sh']=torch.cat([((m['colors']-.5)/.28209479177387814)[:,None],sh_rest],dim=1)
        return m
    def render(m,v):
        rgb,alpha,info=rasterization(m['means'],m['quats'],m['scales'],m['opacity'],m.get('sh',m['colors']),v['view'],v['K'],v['width'],v['height'],
             sh_degree=a.sh_degree if a.sh_degree else None,packed=False,near_plane=.01,far_plane=4.,rasterize_mode='antialiased')
        return rgb[0],alpha[0,:,:,0]
    start=time.time();history=[];rng=np.random.default_rng(42)
    def patch(v):
        size=a.patch_size
        if not size:return v
        w=min(size,v['width']);h=min(size,v['height'])
        if len(v['fg_samples']) and rng.random()<.8:
            cy,cx=v['fg_samples'][int(rng.integers(len(v['fg_samples'])))];cx+=int(rng.integers(-w//4,w//4+1));cy+=int(rng.integers(-h//4,h//4+1))
            x=int(np.clip(cx-w//2,0,v['width']-w));y=int(np.clip(cy-h//2,0,v['height']-h))
        else:x=int(rng.integers(v['width']-w+1));y=int(rng.integers(v['height']-h+1))
        K=v['K'].clone();K[:,0,2]-=x;K[:,1,2]-=y
        return {**v,'K':K,'width':w,'height':h,**{k:v[k][y:y+h,x:x+w] for k in ['target','mask','occlusion']}}
    @torch.no_grad()
    def evaluate(step,save=False):
        m=model();rows=[];metrics=[]
        for v in views:
            rgb,alpha=render(m,v);mask=v['mask'];weight=(mask>.75).float()
            mse=((rgb/alpha[...,None].clamp_min(.2)-v['target']).square().mean(-1)*weight).sum()/weight.sum().clamp_min(1)
            metrics.append(dict(camera=v['camera'],foreground_psnr_db=-10*math.log10(max(float(mse),1e-12)),
               alpha_mae=float(((alpha-mask).abs()*(1-v['occlusion'])).mean()),mean_foreground_alpha=float((alpha*weight).sum()/weight.sum().clamp_min(1))))
            if save:
                source=v['target']*mask[...,None]+(1-mask[...,None])*.92
                composite=rgb+(1-alpha[...,None])*.92
                panels=[source,composite,alpha[...,None].expand(-1,-1,3)]
                row=Image.new('RGB',(1500,425),'#18202a');d=ImageDraw.Draw(row)
                for col,value in enumerate(panels):
                    im=Image.fromarray((value.clamp(0,1).cpu().numpy()*255).astype(np.uint8));im.thumbnail((485,375));row.paste(im,(col*500,40))
                    d.text((col*500+6,8),v['camera']+' | '+['masked source RGB','actual Gaussian RGB','Gaussian alpha'][col],fill='white')
                rows.append(row)
                Image.fromarray((composite.clamp(0,1).cpu().numpy()*255).astype(np.uint8)).save(out/f"{v['camera']}_render.png")
        if save:
            canvas=Image.new('RGB',(1500,len(rows)*425));
            for i,row in enumerate(rows):canvas.paste(row,(0,i*425))
            canvas.save(out/'comparison.jpg',quality=95)
        result=dict(step=step,views=metrics,elapsed_s=time.time()-start);history.append(result)
        (out/'history.json').write_text(json.dumps(history,indent=2)+'\n');print(json.dumps(result),flush=True)
        return result
    evaluate(0,True)
    try:
        for step in range(1,a.steps+1):
            v=patch(views[int(rng.integers(3))]);optim.zero_grad(set_to_none=True);m=model();rgb,alpha=render(m,v)
            mask=v['mask'];valid=1-v['occlusion'];desired=v['target']*mask[...,None]
            photo=((rgb-desired).abs().mean(-1)*valid*(.1+mask)).sum()/(valid*(.1+mask)).sum().clamp_min(1)
            silhouette=((alpha-mask).abs()*valid).sum()/valid.sum().clamp_min(1)
            regular=.0005*offset.tanh().square().mean()+.0001*(m['scales']/.001).square().mean()
            if a.sh_degree:regular+=.002*sh_rest.square().mean()
            loss=photo+.15*silhouette+regular
            if not torch.isfinite(loss):raise ValueError('Nonfinite loss')
            loss.backward();optim.step()
            if step%250==0:print(json.dumps(dict(step=step,loss=float(loss),elapsed_s=time.time()-start)),flush=True)
            if step%1000==0 or step==a.steps:
                current=evaluate(step,step==a.steps)
                early=bool(a.stop_psnr and step>=3000 and all(v['foreground_psnr_db']>=a.stop_psnr and v['alpha_mae']<.01 for v in current['views']))
                if step%2000==0 or step==a.steps or early:
                    arrays={k:v.detach().cpu().numpy() for k,v in model().items()}
                    np.savez_compressed(out/'model.npz',**arrays);save_ply(out/'snapshot.ply',arrays)
                if early:
                    current=evaluate(step,True)
                    print(json.dumps(dict(early_stop='all-camera fit criterion',step=step)),flush=True);break
        summary=dict(status='trained_multiview_rgb_frame',index=a.index,time_s=views[0]['time_s'],gaussians=len(base),steps=step,maximum_steps=a.steps,
          elapsed_s=time.time()-start,peak_cuda_bytes=torch.cuda.max_memory_allocated(),source_session=a.session,source_dense=a.dense,masks=a.masks,
          views=[{k:v[k] for k in ['camera','index','crop','width','height','resize_factor']} for v in views],metrics=history[-1]['views'],
          actual_rgb_gaussian_fit=True,temporal_model=False,metric_accuracy_verified=False,
          neural_depth_prior_points=int((data['support_kind']==1).sum()) if 'support_kind' in data else 0,
          geometry_offset_bound_mm=a.offset_mm,
          color_balance=a.color_balance,
          native_patch_size=a.patch_size,
          sh_degree=a.sh_degree,
          validation_note='Fitting residuals on the three optimization cameras; no independent held-out novel view.',
          limitations=['Provisional off-plane calibration','Automatic masks and repeated-pattern dense matching','Independent frame: no material identity claim'])
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
    except Exception as e:
        (out/'failure.json').write_text(json.dumps(dict(error=repr(e),history=history),indent=2));raise


if __name__=='__main__':main()
