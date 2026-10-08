"""Match camera display RGB using corresponding visible printed-board pixels.

This removes a global capture color mismatch, not illumination or intrinsic
pigment changes. Source recordings remain unmodified.
"""
import argparse
import json
from pathlib import Path
from importlib.machinery import SourceFileLoader
import cv2
import numpy as np
from PIL import Image
from scipy.optimize import least_squares

stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_03_video');p.add_argument('--output',default='outputs/dynamic_textile_001/color_balance_02')
    a=p.parse_args();session=Path(a.session).resolve();root=session.parent;out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cams=stereo.cameras(session);bundles=stereo.read(root/'manifests/sync-plan.json')['bundles'];maskroot=Path(a.masks)
    x,y=np.meshgrid(np.arange(.008,.343,.0025),np.arange(.008,.203,.0025));points=np.c_[x.ravel(),y.ravel(),np.zeros(x.size)]
    pairs={c:[] for c in ['dji','iphone']}
    for index in [0,52,106,158,212,266,318,372,425]:
        values={};valid={}
        for cid,c in cams.items():
            xy=stereo.project(points,c)
            image=np.asarray(Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB'))
            mask=cv2.imread(str(maskroot/'masks'/cid/f'frame_{index:06d}.png'),0);skin=cv2.imread(str(maskroot/'occlusions'/cid/f'frame_{index:06d}.png'),0)
            blocked=cv2.dilate(((mask>30)|(skin>0)).astype(np.uint8),np.ones((21,21),np.uint8))
            value=stereo.sample(image,xy)/255.;values[cid]=value
            valid[cid]=(stereo.sample(blocked,xy)==0)&(value.min(1)>.04)&(value.max(1)<.97)
        for cid in pairs:
            keep=valid[cid]&valid['fuji'];pairs[cid].append(np.c_[values[cid][keep],values['fuji'][keep]])
    result=dict(reference_camera='fuji',space='encoded SDR RGB, global diagonal gain and offset',source_session=a.session,
                 claim_limit='Display color alignment from the printed board; not radiometric/pigment calibration.',cameras={'fuji':{'gain':[1,1,1],'bias':[0,0,0]}})
    for cid,rows in pairs.items():
        data=np.concatenate(rows);test=np.arange(len(data))%7==0;train=~test
        gain=[];bias=[]
        for channel in range(3):
            fitted=least_squares(lambda p:p[0]*data[train,channel]+p[1]-data[train,channel+3],
                    [1.,0.],loss='soft_l1',f_scale=.025,bounds=([.5,-.2],[2.,.2]))
            gain.append(float(fitted.x[0]));bias.append(float(fitted.x[1]))
        before=np.mean(np.abs(data[test,:3]-data[test,3:]));after=np.mean(np.abs(data[test,:3]*gain+bias-data[test,3:]))
        result['cameras'][cid]=dict(gain=gain,bias=bias,samples=len(data),heldout_board_mae_before=float(before),heldout_board_mae_after=float(after))
    (out/'color_balance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
