"""Sample recorded RGB at approximately visible reconstructed surface centres.

Gaussian component colors are not unique under alpha compositing. Use measured
image pixels for qualitative surface appearance maps instead. Depth visibility
is a local point-buffer heuristic, not verified material correspondence.
"""
import argparse
import json
from pathlib import Path
import time
import warnings

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def camera_records(session):
    result={}
    for item in read(session)['cameras']:
        data=read(session.parent/item['calibration']);p=data['params']
        result[item['id']]=dict(K=np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]]),
            R=np.array(data['world_to_camera']['R']),t=np.array(data['world_to_camera']['t']))
    return result


def sample_frame(frame,session,masks,balance,bundles,cameras):
    source=ROOT/frame['model'];output=source.with_name('observed_appearance.npz')
    if output.exists():return read(output.with_suffix('.json'))
    with np.load(source) as data:
        points=data['means'].copy();opacity=data['opacity'].copy()
    samples=[];counts={}
    for cid,c in cameras.items():
        image=np.asarray(Image.open(session.parent/bundles[frame['index']]['views'][cid]['image']).convert('RGB'))
        cloth=cv2.imread(str(masks/'masks'/cid/f"frame_{frame['index']:06d}.png"),0)
        occlusion=cv2.imread(str(masks/'occlusions'/cid/f"frame_{frame['index']:06d}.png"),0)
        if cloth is None or occlusion is None:raise ValueError('Missing appearance visibility mask')
        xyz=points@c['R'].T+c['t'];projected=xyz@c['K'].T
        xy=np.round(projected[:,:2]/projected[:,2:]).astype(np.int32)
        h,w=cloth.shape;inside=(xyz[:,2]>.01)&(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h)
        x=np.clip(xy[:,0],0,w-1);y=np.clip(xy[:,1],0,h-1)
        # Low-opacity components cannot reliably supply a visible surface.
        depth=np.full(h*w,1000.,np.float32)
        front=inside&(opacity>.035)
        np.minimum.at(depth,y[front]*w+x[front],xyz[front,2])
        depth=cv2.erode(depth.reshape(h,w),np.ones((7,7),np.uint8))
        occ=cv2.dilate((occlusion>0).astype(np.uint8),np.ones((7,7),np.uint8))
        valid=front&(cloth[y,x]>200)&(occ[y,x]==0)&(xyz[:,2]<=depth[y,x]+.005)
        target=image[y,x].astype(np.float32)/255.
        correction=balance['cameras'][cid]
        target=np.clip(target*np.array(correction['gain'])+np.array(correction['bias']),0,1)
        target[~valid]=np.nan;samples.append(target);counts[cid]=int(valid.sum())
    samples=np.stack(samples);views=np.sum(np.isfinite(samples[:,:,0]),axis=0).astype(np.uint8)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        colors=np.nanmedian(samples,axis=0).astype(np.float32)
    colors[views==0]=0
    temporary=output.with_suffix('.tmp.npz');np.savez_compressed(temporary,colors=colors,visible_views=views);temporary.replace(output)
    summary=dict(index=frame['index'],gaussians=len(points),observed_points=int((views>0).sum()),
        two_or_more_views=int((views>=2).sum()),visible_by_camera=counts,
        source_model=str(source.relative_to(ROOT)).replace('\\','/'),source_session=str(session.relative_to(ROOT)).replace('\\','/'),
        color_space=balance['space'],aggregation='Channelwise median of visible recorded-camera RGB samples',
        visibility='Cloth probability >200/255; 7px skin exclusion; local 7px point-depth buffer with 5mm tolerance',
        limitation='Approximate visibility and closest-surface association; no persistent material IDs or intrinsic pigment claim.')
    output.with_suffix('.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--color-balance',default='outputs/dynamic_textile_001/color_balance_02/color_balance.json')
    p.add_argument('--indexes',type=int,nargs='+');p.add_argument('--watch',action='store_true');a=p.parse_args()
    path=ROOT/a.sequence;initial=read(path);session=ROOT/initial['source_session'];masks=ROOT/initial['masks']
    balance=read(ROOT/a.color_balance);cameras=camera_records(session);bundles=read(session.parent/'manifests/sync-plan.json')['bundles']
    cv2.setNumThreads(2);previous_count=-1
    while True:
        sequence=read(path);summaries=[]
        for frame in sequence['frames']:
            if a.indexes and frame['index'] not in a.indexes:continue
            summary=sample_frame(frame,session,masks,balance,bundles,cameras);summaries.append(summary)
        result=dict(status=('selected samples prepared' if a.indexes else
                           'complete' if sequence['status']=='complete' else 'following reconstruction'),
            frames=len(summaries),requested=len(sequence['requested_indexes']),representation='Visible recorded-camera surface RGB',
            independent_metric_accuracy_verified=False,summaries=summaries)
        out=path.parent/'observed_appearance_summary.json';temporary=out.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result,indent=2)+'\n')
        for attempt in range(40):
            try:temporary.replace(out);break
            except PermissionError:
                if attempt==39:raise
                time.sleep(.15)
        if len(summaries)!=previous_count:print(json.dumps({k:result[k] for k in ['status','frames','requested']}),flush=True);previous_count=len(summaries)
        if not a.watch or sequence['status']=='complete':break
        if sequence['status']!='training':raise RuntimeError('Reconstruction stopped before completion; observations preserved')
        time.sleep(5)


if __name__=='__main__':main()
