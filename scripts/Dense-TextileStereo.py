"""Dense learned matching followed by calibrated metric triangulation.

MASt3R descriptors are a matching prior. Geometry here comes from recorded
camera calibration, not an unaligned neural point-map. Pairwise support is
retained; reprojection does not certify correspondence in repeated knit.
"""
import argparse
import itertools
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/tools/mast3r'))
from mast3r.model import AsymmetricMASt3R
from mast3r.fast_nn import fast_reciprocal_NNs


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def cameras(session):
    root=session.parent;s=read(session);result={}
    for item in s['cameras']:
        c=read(root/item['calibration']);p=c['params']
        K=np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]])
        R=np.array(c['world_to_camera']['R']);t=np.array(c['world_to_camera']['t'])
        result[item['id']]=dict(K=K,R=R,t=t,P=K@np.c_[R,t],size=c['image_size'])
    return result


def project(x,c):
    p=x@c['P'][:,:3].T+c['P'][:,3]
    return p[:,:2]/p[:,2:]


def sample(image,xy):
    x=np.clip(np.round(xy[:,0]).astype(int),0,image.shape[1]-1)
    y=np.clip(np.round(xy[:,1]).astype(int),0,image.shape[0]-1)
    return image[y,x]


def view(image,mask,idx):
    y,x=np.where(mask>127)
    if len(x)<100:raise ValueError('No usable cloth mask')
    box=[max(0,int(x.min())-70),max(0,int(y.min())-70),
         min(image.shape[1],int(x.max())+71),min(image.shape[0],int(y.max())+71)]
    crop=image[box[1]:box[3],box[0]:box[2]]
    factor=512/max(crop.shape[:2]);w=max(32,round(crop.shape[1]*factor/16)*16);h=max(32,round(crop.shape[0]*factor/16)*16)
    tensor=torch.tensor(cv2.resize(crop,(w,h),interpolation=cv2.INTER_AREA).copy(),device='cuda',dtype=torch.float32).permute(2,0,1)[None]/127.5-1.
    return dict(img=tensor,true_shape=torch.tensor([[h,w]],device='cuda',dtype=torch.int32),idx=[idx],instance=[str(idx)]),dict(
        origin=np.array(box[:2]),scale=np.array([crop.shape[1]/w,crop.shape[0]/h]),box=box)


def triangulate(a,b,ca,cb):
    if len(a)==0:return np.empty((0,3)),np.empty(0),np.empty(0,dtype=bool)
    h=cv2.triangulatePoints(ca['P'],cb['P'],a.T,b.T).T
    x=h[:,:3]/h[:,3:]
    error=np.maximum(np.linalg.norm(project(x,ca)-a,axis=1),np.linalg.norm(project(x,cb)-b,axis=1))
    deptha=(x@ca['R'].T+ca['t'])[:,2];depthb=(x@cb['R'].T+cb['t'])[:,2]
    return x,error,(deptha>0)&(depthb>0)


def fit_similarity(source,target):
    """Robust similarity to measured stereo anchors, not a metric certificate."""
    keep=np.isfinite(source).all(1)&np.isfinite(target).all(1)
    if keep.sum()<40:return None
    for iteration in range(5):
        a=source[keep];b=target[keep];ac=a.mean(0);bc=b.mean(0);aa=a-ac;bb=b-bc
        u,s,vt=np.linalg.svd(aa.T@bb)
        sign=np.ones(3);sign[-1]=np.sign(np.linalg.det(vt.T@u.T))
        rotation=vt.T@np.diag(sign)@u.T
        scale=float((s*sign).sum()/np.square(aa).sum())
        translation=bc-scale*ac@rotation.T
        residual=np.linalg.norm(scale*source@rotation.T+translation-target,axis=1)
        median=np.median(residual[keep]);mad=np.median(np.abs(residual[keep]-median))
        nextkeep=np.isfinite(residual)&(residual<max(.004,median+2.5*mad))
        if nextkeep.sum()<40:break
        keep=nextkeep
    return scale,rotation,translation,float(np.median(residual[keep]))


def neural_fill(pred,xy_model,anchors,viewmeta,camera,image,mask,limit=2500):
    """Fill singly observed fabric from a registered neural shape prior.

    Points lie on the real calibrated image rays, but their depths are inferred.
    Anchor proximity controls the contribution; all provenance remains explicit.
    """
    key='pts3d' if 'pts3d' in pred else 'pts3d_in_other_view'
    neural=pred[key][0].cpu().numpy();confidence=pred['desc_conf'][0].cpu().numpy()
    query=np.round(xy_model).astype(int)
    query[:,0]=np.clip(query[:,0],0,neural.shape[1]-1);query[:,1]=np.clip(query[:,1],0,neural.shape[0]-1)
    similarity=fit_similarity(neural[query[:,1],query[:,0]],anchors)
    if similarity is None:return np.empty((0,3)),np.empty((0,3)),None
    scale,R,t,residual=similarity
    y,x=np.mgrid[2:neural.shape[0]:4,2:neural.shape[1]:4];yx=np.c_[y.ravel(),x.ravel()]
    xy=yx[:,::-1]*viewmeta['scale']+viewmeta['origin']
    keep=(sample(mask,xy)>200)&(confidence[yx[:,0],yx[:,1]]>.10)
    yx=yx[keep];xy=xy[keep];raw=neural[yx[:,0],yx[:,1]]
    world=scale*raw@R.T+t
    # Keep the observed pixel ray exactly; registered neural depth supplies z.
    depth=(world@camera['R'].T+camera['t'])[:,2]
    rays=np.c_[xy,np.ones(len(xy))]@np.linalg.inv(camera['K']).T
    world=(rays*depth[:,None]-camera['t'])@camera['R']
    # Smooth correction from nearby metric stereo anchors, without claiming unseen measurement.
    anchor_depth=(anchors@camera['R'].T+camera['t'])[:,2]
    model_anchor=neural[query[:,1],query[:,0]]
    projected_anchor=(scale*model_anchor@R.T+t)@camera['R'].T+camera['t']
    distances,near=cKDTree(xy_model).query(yx[:,::-1],k=min(6,len(xy_model)))
    if distances.ndim==1:distances=distances[:,None];near=near[:,None]
    weights=1/np.maximum(distances,1.)**2;weights/=weights.sum(1,keepdims=True)
    delta=(weights*(anchor_depth-projected_anchor[:,2])[near]).sum(1)
    depth+=delta
    world=(rays*depth[:,None]-camera['t'])@camera['R']
    keep=np.isfinite(world).all(1)&(depth>0)&(world[:,2]<.004)&(world[:,2]>-.4)
    world=world[keep];xy=xy[keep]
    if len(world)>limit:
        chosen=np.linspace(0,len(world)-1,limit,dtype=int);world=world[chosen];xy=xy[chosen]
    rgb=sample(image,xy).astype(np.float32)/255.
    return world,rgb,dict(points=len(world),registration_median_m=residual,
                          provenance='Registered neural shape prior on calibrated observed rays, corrected by nearby stereo anchors')


def diagnostic(out,images,masks,points,cams,index,summary):
    canvas=Image.new('RGB',(1500,490),'#151c26');d=ImageDraw.Draw(canvas)
    for col,(cid,c) in enumerate(cams.items()):
        im=images[cid].copy();xy=project(points,c);y,x=np.where(masks[cid]>127)
        if len(x)==0:continue
        box=[max(0,x.min()-90),max(0,y.min()-90),min(im.shape[1],x.max()+91),min(im.shape[0],y.max()+91)]
        for p in xy:
            if np.isfinite(p).all():cv2.circle(im,tuple(np.round(p).astype(int)),3,(40,225,95),-1)
        small=Image.fromarray(im[box[1]:box[3],box[0]:box[2]]);small.thumbnail((480,415))
        canvas.paste(small,(col*500,55));d.text((col*500+10,8),f'{cid} | index {index} | {len(points)} dense 3D samples',fill='white')
    canvas.save(out/f'diagnostic_{index:06d}.jpg',quality=94)


def load_model():
    return AsymmetricMASt3R.from_pretrained(str(ROOT/'.local/tools/mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth')).to('cuda').eval()


def main(model=None):
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_02');p.add_argument('--output',default='outputs/dynamic_textile_001/dense_stereo_02')
    p.add_argument('--indexes',type=int,nargs='+',default=[0]);p.add_argument('--stride',type=int)
    p.add_argument('--max-reprojection',type=float,default=5.)
    p.add_argument('--depth-prior',action='store_true',help='Explicit neural shape fill for singly observed fabric')
    args=p.parse_args();session=Path(args.session).resolve();root=session.parent;cams=cameras(session)
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True);mroot=Path(args.masks)
    bundles=read(root/'manifests/sync-plan.json')['bundles'];indexes=args.indexes
    if args.stride:
        indexes=list(range(0,len(bundles),args.stride))
        if indexes[-1]!=len(bundles)-1:indexes.append(len(bundles)-1)
    if model is None:model=load_model()
    started=time.time();summaries=[]
    for index in indexes:
        if (out/f'frame_{index:06d}.npz').exists():
            summaries.append(read(out/f'frame_{index:06d}.json'));continue
        images={cid:np.asarray(Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB')).copy() for cid in cams}
        masks={cid:np.asarray(Image.open(mroot/'masks'/cid/f'frame_{index:06d}.png')) for cid in cams}
        views={cid:view(images[cid],masks[cid],i) for i,cid in enumerate(cams)}
        points=[];colors=[];pairids=[];errors=[];matches={};statistics=[];prior_points=[];prior_colors=[];prior_statistics=[]
        with torch.inference_mode():
            for pairid,(a,b) in enumerate(itertools.combinations(cams,2)):
                pred1,pred2=model(views[a][0],views[b][0])
                xy1,xy2=fast_reciprocal_NNs(pred1['desc'][0],pred2['desc'][0],subsample_or_initxy1=4,
                                          device='cuda',dist='dot',block_size=2048)
                descconf1=pred1['desc_conf'][0].cpu().numpy();descconf2=pred2['desc_conf'][0].cpu().numpy()
                conf=np.minimum(descconf1[xy1[:,1],xy1[:,0]],descconf2[xy2[:,1],xy2[:,0]])
                xy1=xy1*views[a][1]['scale']+views[a][1]['origin']
                xy2=xy2*views[b][1]['scale']+views[b][1]['origin']
                keep=(sample(masks[a],xy1)>180)&(sample(masks[b],xy2)>180)&np.isfinite(conf)&(conf>0)
                raw=int(keep.sum());xy1=xy1[keep];xy2=xy2[keep]
                xyz,err,front=triangulate(xy1,xy2,cams[a],cams[b])
                keep=front&np.isfinite(xyz).all(axis=1)&(err<args.max_reprojection)
                keep&=(xyz[:,2]<.003)&(xyz[:,2]>-.35)&(xyz[:,0]>-.15)&(xyz[:,0]<.55)&(xyz[:,1]>-.15)&(xyz[:,1]<.45)
                if index<14:keep&=xyz[:,2]>-.065
                xyz=xyz[keep];xy1=xy1[keep];xy2=xy2[keep];err=err[keep]
                if args.depth_prior and len(xyz)>=100:
                    for cid,pred,xy in [(a,pred1,xy1),(b,pred2,xy2)]:
                        modelxy=(xy-views[cid][1]['origin'])/views[cid][1]['scale']
                        fill,fillrgb,fillinfo=neural_fill(pred,modelxy,xyz,views[cid][1],cams[cid],images[cid],masks[cid])
                        if len(fill):
                            prior_points.append(fill);prior_colors.append(fillrgb);prior_statistics.append(dict(camera=cid,pair=[a,b],**fillinfo))
                # Third-view silhouette is diagnostic: folds can hide real pairwise points.
                rgb=(sample(images[a],xy1).astype(float)+sample(images[b],xy2).astype(float))/510.
                points.append(xyz);colors.append(rgb);pairids.append(np.full(len(xyz),pairid));errors.append(err)
                matches[a+'_'+b]={'xy1':xy1,'xy2':xy2,'xyz':xyz}
                statistics.append({'pair':[a,b],'cloth_candidates':raw,'triangulated':len(xyz),
                                   'descriptor_confidence_median':float(np.median(conf)),
                                   'median_reprojection_px':float(np.median(err)) if len(err) else None})
                print(json.dumps({'index':index,**statistics[-1]}),flush=True)
                del pred1,pred2;torch.cuda.empty_cache()
        xyz=np.concatenate(points);rgb=np.concatenate(colors);pair=np.concatenate(pairids);err=np.concatenate(errors)
        if len(xyz)<40:raise ValueError(f'Dense stereo insufficient at index {index}: {len(xyz)}')
        distances,_=cKDTree(xyz).query(xyz,k=min(9,len(xyz)))
        keep=distances[:,-1]<.014
        xyz=xyz[keep];rgb=rgb[keep];pair=pair[keep];err=err[keep]
        observed_count=len(xyz)
        support_kind=np.zeros(len(xyz),np.uint8)
        if prior_points:
            fill=np.concatenate(prior_points);fillrgb=np.concatenate(prior_colors)
            xyz=np.concatenate([xyz,fill]);rgb=np.concatenate([rgb,fillrgb]);pair=np.r_[pair,np.full(len(fill),-1)]
            err=np.r_[err,np.full(len(fill),np.nan)];support_kind=np.r_[support_kind,np.ones(len(fill),np.uint8)]
        # Duplicate coordinates from different pairs are retained for support checks;
        # voxel merging is performed when initializing the Gaussian surface.
        np.savez_compressed(out/f'frame_{index:06d}.npz',points=xyz.astype(np.float32),colors=rgb.astype(np.float32),
                            pair_ids=pair,reprojection_px=err.astype(np.float32),
                            support_kind=support_kind,
                            **{k+'_'+field:value for k,v in matches.items() for field,value in v.items()})
        summary={'index':index,'time_s':bundles[index]['time_s'],'points':len(xyz),'pairs':statistics,
                 'observed_stereo_points':observed_count,'neural_prior_points':len(xyz)-observed_count,'neural_prior':prior_statistics,
                 'median_reprojection_px':float(np.nanmedian(err)),'bounds_m':[xyz.min(0).tolist(),xyz.max(0).tolist()],
                 'claim_limit':'Calibrated matching samples; repeated-pattern correspondence and hidden surfaces are not independently certified.'}
        (out/f'frame_{index:06d}.json').write_text(json.dumps(summary,indent=2)+'\n')
        diagnostic(out,images,masks,xyz,cams,index,summary);summaries.append(summary)
    (out/'summary.json').write_text(json.dumps({'frames':summaries,'elapsed_s':time.time()-started,
                                               'session':str(args.session),'masks':str(args.masks)},indent=2)+'\n')


if __name__=='__main__':main()
