"""Observed current-recording table/marker texture as a metric Gaussian plane.

Uses only textile images. The measured board establishes z=0. Extending this
plane to the adjacent table assumes it is flat; no old room scene is merged.
"""
import argparse
import json
from pathlib import Path
from importlib.machinery import SourceFileLoader
import cv2
import numpy as np
from PIL import Image

stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_03_video');p.add_argument('--output',default='outputs/dynamic_textile_001/current_table_04')
    p.add_argument('--all-times',action='store_true',help='Use every available native mask time to recover more actually visible table pixels')
    a=p.parse_args();session=Path(a.session).resolve();root=session.parent;out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cams=stereo.cameras(session);bundles=stereo.read(root/'manifests/sync-plan.json')['bundles'];maskroot=Path(a.masks)
    x,y=np.meshgrid(np.arange(-.04,.40,.001),np.arange(-.085,.29,.001));means=np.c_[x.ravel(),y.ravel(),np.zeros(x.size)]
    best=np.full(len(means),-np.inf);colors=np.zeros((len(means),3),np.float32);seen=np.zeros(len(means),bool)
    indexes=([i for i in range(len(bundles)) if all((maskroot/'masks'/cid/f'frame_{i:06d}.png').exists() for cid in cams)]
        if a.all_times else [0,52,106,158,212,266,318,372,425])
    assert len(indexes)>=2
    for cid in ['iphone','dji','fuji']:
        c=cams[cid];xy=stereo.project(means,c);px=np.round(xy[:,0]).astype(int);py=np.round(xy[:,1]).astype(int)
        inside=(px>=0)&(px<c['size'][0])&(py>=0)&(py<c['size'][1])
        score=(c['K'][0,0]/np.linalg.norm(means-(-c['R'].T@c['t']),axis=1))
        observations=[];valid_masks=[]
        for index in indexes:
            image=np.asarray(Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB'))
            mask=cv2.imread(str(maskroot/'masks'/cid/f'frame_{index:06d}.png'),0)
            skin=cv2.imread(str(maskroot/'occlusions'/cid/f'frame_{index:06d}.png'),0)
            # Border exclusion avoids baking foreground edge pixels into the plane.
            cloth=cv2.dilate((mask>40).astype(np.uint8),np.ones((17,17),np.uint8))
            # Watches/straps are not skin. Exclude the close neighborhood of
            # moving hands/wrists as well, rather than baking them into the table.
            hands=cv2.dilate((skin>0).astype(np.uint8),np.ones((201,201),np.uint8))
            blocked=cloth|hands
            valid=inside&(stereo.sample(blocked,xy)==0)
            observations.append(stereo.sample(image,xy)/255.);valid_masks.append(valid)
        print(json.dumps(dict(camera=cid,source_times=len(indexes),status='sampled observed table pixels')),flush=True)
        observations=np.stack(observations);valid_masks=np.stack(valid_masks)
        luminance=observations.mean(-1);luminance[~valid_masks]=-np.inf
        chosen=np.argmax(luminance,axis=0)
        keep=(valid_masks.sum(0)>=2)&(score>best)
        colors[keep]=observations[chosen,np.arange(len(means))][keep];best[keep]=score[keep];seen|=keep
    # Only pixels with actual current-session evidence are exported.
    means=means[seen].astype(np.float32);colors=colors[seen]
    count=len(means);np.savez_compressed(out/'table.npz',means=means,colors=colors,
        scales=np.tile([.00058,.00058,.00005],(count,1)).astype(np.float32),
        quats=np.tile([1.,0,0,0],(count,1)).astype(np.float32),opacity=np.full(count,.96,np.float32))
    summary=dict(gaussians=count,source_session=a.session,source_indexes=indexes,source_policy='current textile capture only',
                 geometry='Measured z=0 board plane, extended flat-table assumption',
                 hidden_pixels_filled=False,other_scenes_merged=False,table_extent_m=[[-.04,-.085,0],[.40,.29,0]],
                 scope='Measured board and close tabletop only; off-table surroundings excluded')
    summary['foreground_exclusion']='SAM cloth plus 100-pixel skin-neighborhood margin to exclude moving wrists/watches'
    summary['texture_selection']='Brightest unobstructed observed sample per point/camera, with at least two available samples'
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary))


if __name__=='__main__':main()
