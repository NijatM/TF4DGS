"""Adapt a shared physical rig to a clip's measured constant pixel translation.

Changes principal point only; validates all visible marker corners afterward.
Refuses to treat rotation/scale/distortion or rig movement as a simple crop.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,help='New crop-correction directory, relative to the session folder')
    parser.add_argument('--no-update-session',action='store_true',help='Keep the session references unchanged while evaluating this candidate')
    args=parser.parse_args();root=args.session.parent
    out=root/(args.output or Path('calibration/cameras_crop_adjusted'))
    if out.exists():raise ValueError('Crop-adjusted cameras already exist')
    out.mkdir(parents=True)
    definition=json.loads(Path('documentation/reference_markers/TF4DGS_ChArUco_US_Tabloid_10x6_35mm.json').read_text())
    geometry={m['id']:np.array(m['corners_m'],float) for m in definition['layout']['markers']}
    session=json.loads(args.session.read_text(encoding='utf-8-sig'));summaries=[]
    for camera in session['cameras']:
        cid=camera['id'];value=json.loads((args.source/f'{cid}.json').read_text())
        audit=json.loads((root/'calibration/marker_audit'/f'{cid}.json').read_text())
        obs=audit['reference']['markers'];points=np.vstack([geometry[m['id']] for m in obs]);pixels=np.vstack([m['pixels'] for m in obs])
        K=np.array([[value['params'][0],0,value['params'][2]],[0,value['params'][1],value['params'][3]],[0,0,1.]])
        rv=cv2.Rodrigues(np.array(value['world_to_camera']['R']))[0];t=np.array(value['world_to_camera']['t'])
        predicted=cv2.projectPoints(points,rv,t,K,None)[0].reshape(-1,2)
        shift=np.median(pixels-predicted,axis=0)
        before=float(np.sqrt(np.mean(np.sum((pixels-predicted)**2,axis=1))))
        after=float(np.sqrt(np.mean(np.sum((pixels-predicted-shift)**2,axis=1))))
        if after>4:
            raise ValueError(f'{cid}: translation-only crop model has {after:.2f}px RMS; rig/framing model needs review')
        value['params'][2]+=float(shift[0]);value['params'][3]+=float(shift[1])
        value['clip_crop_adjustment']={'dx_px':float(shift[0]),'dy_px':float(shift[1]),'before_board_rms_px':before,'after_board_rms_px':after,
                                       'physical_camera_pose_preserved':True,'validation':'Visible marker corners; independently calibrated intrinsics unavailable'}
        if cid=='fuji':value['lid_heldout_rms_px']=None
        (out/f'{cid}.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        camera['calibration']=(out/f'{cid}.json').relative_to(root).as_posix()
        summaries.append({'camera_id':cid,**value['clip_crop_adjustment']});print(json.dumps(summaries[-1]),flush=True)
    (out/'summary.json').write_text(json.dumps({'status':'provisional','results':summaries},indent=2)+'\n',encoding='utf-8')
    if not args.no_update_session:args.session.write_text(json.dumps(session,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
