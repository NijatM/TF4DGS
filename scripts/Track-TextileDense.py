"""Occlusion-aware dense temporal anchors, with calibrated multiview checks.

CoTracker outputs are hypotheses. Only cloth-masked, mutually consistent
multiview observations become supported 3D anchors; hidden geometry is inferred.
"""
import argparse
import itertools
import json
from pathlib import Path
import sys
import time
from importlib.machinery import SourceFileLoader

import cv2
import numpy as np
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.local/tools/co-tracker'))
from cotracker.predictor import CoTrackerOnlinePredictor
stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def select_nodes(points,count):
    selected=[int(np.argmin(np.linalg.norm(points-np.median(points,axis=0),axis=1)))]
    distance=np.full(len(points),np.inf)
    for i in range(min(count,len(points))-1):
        distance=np.minimum(distance,np.linalg.norm(points-points[selected[-1]],axis=1))
        selected.append(int(np.argmax(distance)))
    return points[selected].astype(np.float32)


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_03_video');p.add_argument('--dense',default='outputs/dynamic_textile_001/dense_stereo_02')
    p.add_argument('--output',default='outputs/dynamic_textile_001/dense_tracking_02');p.add_argument('--nodes',type=int,default=700)
    a=p.parse_args();session=Path(a.session).resolve();root=session.parent;out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    maskroot=Path(a.masks);indexes=stereo.read(maskroot/'summary.json')['frames'];bundles=stereo.read(root/'manifests/sync-plan.json')['bundles'];cams=stereo.cameras(session)
    initial=np.load(Path(a.dense)/'frame_000000.npz');good=initial['reprojection_px']<2.
    nodes=select_nodes(initial['points'][good],a.nodes);np.save(out/'canonical_nodes.npy',nodes)
    predictor=CoTrackerOnlinePredictor(checkpoint=str(ROOT/'.local/tools/co-tracker/checkpoints/scaled_online.pth')).to('cuda').eval()
    torch.set_num_threads(4);cv2.setNumThreads(2);started=time.time();observations={};visibility={};metadata=[]
    for cid,c in cams.items():
        path=out/f'{cid}_tracks.npz'
        if path.exists():
            cached=np.load(path);observations[cid]=cached['xy'];visibility[cid]=cached['visible'];continue
        bounds=[]
        for index in indexes[::12]+[indexes[-1]]:
            mask=cv2.imread(str(maskroot/'masks'/cid/f'frame_{index:06d}.png'),cv2.IMREAD_GRAYSCALE)
            y,x=np.where(mask>127)
            if len(x):bounds.append([x.min(),y.min(),x.max()+1,y.max()+1])
        bounds=np.array(bounds);box=np.array([max(0,bounds[:,0].min()-80),max(0,bounds[:,1].min()-80),
                                             min(c['size'][0],bounds[:,2].max()+80),min(c['size'][1],bounds[:,3].max()+80)])
        w,h=box[2:]-box[:2];factor=min(1.,640/max(w,h));size=(round(w*factor),round(h*factor));scale=np.array([size[0]/w,size[1]/h])
        frames=[]
        for index in indexes:
            image=cv2.imread(str(root/bundles[index]['views'][cid]['image']))
            crop=image[box[1]:box[3],box[0]:box[2],::-1]
            frames.append(cv2.resize(crop,size,interpolation=cv2.INTER_AREA))
        video=np.stack(frames);del frames
        queryxy=(stereo.project(nodes,c)-box[:2])*scale
        queries=torch.tensor(np.c_[np.zeros(len(nodes)),queryxy],device='cuda',dtype=torch.float32)[None]
        with torch.inference_mode():
            first=torch.tensor(video[:8].copy(),device='cuda',dtype=torch.float32).permute(0,3,1,2)[None]
            predictor(first,is_first_step=True,queries=queries,add_support_grid=True)
            for start in range(0,len(indexes)-8,8):
                end=min(start+16,len(indexes));chunk=video[start:end]
                tensor=torch.tensor(chunk.copy(),device='cuda',dtype=torch.float32).permute(0,3,1,2)[None]
                tracks,vis=predictor(tensor,add_support_grid=True)
                if start%40==0:print(f'{cid}: {end}/{len(indexes)} frames; {time.time()-started:.1f}s',flush=True)
            # Last chunk needs its true overlap and length, as in the upstream online demo.
            if tracks.shape[1]<len(indexes):
                start=(len(indexes)//8-1)*8
                chunk=video[start:]
                tensor=torch.tensor(chunk.copy(),device='cuda',dtype=torch.float32).permute(0,3,1,2)[None]
                tracks,vis=predictor(tensor,add_support_grid=True)
        xy=tracks[0,:len(indexes)].cpu().numpy()/scale+box[:2];visible=vis[0,:len(indexes)].cpu().numpy()
        if len(xy)!=len(indexes):raise ValueError('Online output length differs from timeline')
        for order,index in enumerate(indexes):
            mask=cv2.imread(str(maskroot/'masks'/cid/f'frame_{index:06d}.png'),cv2.IMREAD_GRAYSCALE)
            inside=(xy[order,:,0]>=0)&(xy[order,:,0]<mask.shape[1])&(xy[order,:,1]>=0)&(xy[order,:,1]<mask.shape[0])
            visible[order]&=inside&(stereo.sample(mask,xy[order])>180)
        np.savez_compressed(path,xy=xy.astype(np.float32),visible=visible,box=box,scale=scale,indexes=indexes)
        observations[cid]=xy;visibility[cid]=visible;metadata.append(dict(camera=cid,crop=box.tolist(),resize_scale=scale.tolist()))
        del video,tracks,vis,tensor,first;torch.cuda.empty_cache()
    positions=np.full((len(indexes),len(nodes),3),np.nan,np.float32);supported=np.zeros((len(indexes),len(nodes)),bool)
    errors=np.full(supported.shape,np.nan,np.float32);stats=[]
    for order,index in enumerate(indexes):
        candidates=[];candidate_errors=[]
        for a1,b1 in itertools.combinations(cams,2):
            xyz,err,front=stereo.triangulate(observations[a1][order],observations[b1][order],cams[a1],cams[b1])
            keep=visibility[a1][order]&visibility[b1][order]&front&(err<6.)
            keep&=(xyz[:,2]<.008)&(xyz[:,2]>-.40)&(xyz[:,0]>-.2)&(xyz[:,0]<.6)&(xyz[:,1]>-.25)&(xyz[:,1]<.6)
            for cid in cams:
                if cid in [a1,b1]:continue
                third=np.linalg.norm(stereo.project(xyz,cams[cid])-observations[cid][order],axis=1)
                keep&=(~visibility[cid][order])|(third<9.)
                err=np.maximum(err,np.where(visibility[cid][order],third,0))
            candidates.append(xyz);candidate_errors.append(np.where(keep,err,np.inf))
        candidate_errors=np.stack(candidate_errors);best=np.argmin(candidate_errors,axis=0)
        chosen=np.stack(candidates)[best,np.arange(len(nodes))];error=candidate_errors[best,np.arange(len(nodes))]
        keep=np.isfinite(error)
        positions[order,keep]=chosen[keep];supported[order]=keep;errors[order,keep]=error[keep]
        stats.append(dict(index=index,time_s=bundles[index]['time_s'],supported_nodes=int(keep.sum()),
                          median_reprojection_px=float(np.median(error[keep])) if keep.any() else None))
    np.savez_compressed(out/'multiview_nodes.npz',positions=positions,supported=supported,reprojection_px=errors,
                         canonical=nodes,indexes=indexes,times_s=[bundles[i]['time_s'] for i in indexes])
    summary=dict(frames=stats,nodes=len(nodes),camera_processing=metadata,elapsed_s=time.time()-started,
        supported_frames_100_nodes=sum(s['supported_nodes']>=100 for s in stats),
        metric_accuracy_verified=False,material_identity_verified=False,
        method='CoTracker3 online visibility plus cloth masks and calibrated 2/3-view consistency',
        limitation='Repeated knit aliases and reidentification under folds can remain; unsupported nodes require explicitly model-inferred deformation.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
    # Real-camera diagnostic; green=multiview-supported, red=visible tracking rejected in 3D.
    chosenorders=[min(range(len(indexes)),key=lambda j:abs(indexes[j]-i)) for i in [0,52,106,158,212,266,318,372,425]]
    canvas=Image.new('RGB',(1500,len(chosenorders)*310),'#151c26');d=ImageDraw.Draw(canvas)
    for row,order in enumerate(chosenorders):
        index=indexes[order]
        for col,cid in enumerate(cams):
            image=cv2.imread(str(root/bundles[index]['views'][cid]['image']))[:,:,::-1].copy()
            mask=cv2.imread(str(maskroot/'masks'/cid/f'frame_{index:06d}.png'),0);y,x=np.where(mask>127)
            if len(x)==0:continue
            box=[max(0,x.min()-80),max(0,y.min()-80),min(image.shape[1],x.max()+81),min(image.shape[0],y.max()+81)]
            for node in np.flatnonzero(visibility[cid][order]):
                cv2.circle(image,tuple(np.round(observations[cid][order,node]).astype(int)),4,(35,220,75) if supported[order,node] else (245,60,65),-1)
            im=Image.fromarray(image[box[1]:box[3],box[0]:box[2]]);im.thumbnail((480,270));canvas.paste(im,(col*500,row*310+30))
            d.text((col*500+8,row*310+5),f'{cid} t={bundles[index]["time_s"]:.3f}s | supported {supported[order].sum()}/{len(nodes)}',fill='white')
    canvas.save(out/'tracking_diagnostic.jpg',quality=94)


if __name__=='__main__':main()
