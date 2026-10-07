"""Refit observed lid motion with explicit pixel-outlier rejection and provenance.

Single-view planar pose hypotheses only initialize the solve. Accepted frames
still require >=4 retained observations in each of >=2 cameras and >=12 total.
No missing frame interpolation or independent metric accuracy is asserted.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import least_squares


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=Path('outputs/dynamic_yogurt_001/rigid_tracking_03'))
    p.add_argument('--output',type=Path,default=Path('outputs/dynamic_yogurt_001/rigid_tracking_04'))
    p.add_argument('--calibration-dir',type=Path,help='New joint fit with lid_tracks.npz; refit the observed pixels to its canonical coordinates')
    p.add_argument('--tabletop',action='store_true',help='Assume upright sliding on the board plane: yaw and XY translation, no tilt/lift')
    p.add_argument('--session',type=Path,default=Path('data/dynamic_yogurt_001/session.json'));args=p.parse_args()
    out=args.output
    if out.exists():raise ValueError('Preserve previous rigid motion attempts')
    out.mkdir(parents=True);s=read(args.session);root=args.session.parent
    poses=read(args.input/'rigid_poses.json');canonical=np.array(poses['canonical_points_m']);observed=np.load(args.input/'observations.npz')
    tracks=read(args.input/'point_tracks.json');cameras={}
    if args.calibration_dir:
        seed=np.load(args.calibration_dir/'lid_tracks.npz')
        reference=poses['canonical_source_frame']
        bundles=read(root/'manifests/sync-plan.json')['bundles']
        ref=next(i for i,b in enumerate(bundles) if b['views']['fuji']['source_index']==reference)
        if seed['positions'].shape!=canonical.shape or not np.allclose(seed['fuji_pixels'],observed['fuji'][ref],atol=.01):
            raise ValueError('New canonical features do not correspond to the saved optical-flow identities')
        canonical=seed['positions'].copy()
        poses['canonical_points_m']=canonical.tolist()
        poses['canonical_calibration']=args.calibration_dir.as_posix()
    for entry in s['cameras']:
        cid=entry['id'];c=read(root/entry['calibration']);q=c['params']
        cameras[cid]={'K':np.array([[q[0],0,q[2]],[0,q[1],q[3]],[0,0,1.]]),'R':np.array(c['world_to_camera']['R']),'t':np.array(c['world_to_camera']['t'])}
    def full_pose(params):
        return np.array([0.,0.,params[0],params[1],params[2],0.]) if args.tabletop else params
    def seed_pose(params):
        if not args.tabletop:return params
        R=cv2.Rodrigues(np.asarray(params[:3]))[0]
        return np.array([np.arctan2(R[1,0],R[0,0]),params[3],params[4]])
    refined=[];previous=np.zeros(3 if args.tabletop else 6)
    for index,frame in enumerate(tracks['frames']):
        observations={cid:np.flatnonzero(np.isfinite(observed[cid][index]).all(1)) for cid in cameras}
        observations={cid:ids for cid,ids in observations.items() if len(ids)>=4}
        if len(observations)<2 or sum(map(len,observations.values()))<12:refined.append(None);continue
        def errors(params,selection):
            params=full_pose(params)
            R=cv2.Rodrigues(params[:3])[0];world=canonical@R.T+params[3:];result={}
            for cid,ids in selection.items():
                c=cameras[cid];camera=world[ids]@c['R'].T+c['t'];px=camera@c['K'].T
                result[cid]=px[:,:2]/px[:,2:]-observed[cid][index,ids]
            return result
        def fit(seed,selection):
            return least_squares(lambda params:np.concatenate([v.reshape(-1) for v in errors(params,selection).values()]),
                 seed,loss='soft_l1',f_scale=2.,max_nfev=70,x_scale='jac')
        seeds=[previous]
        if poses['frames'][index]:seeds.append(seed_pose(np.r_[poses['frames'][index]['rvec'],poses['frames'][index]['translation_m']]))
        for cid,ids in observations.items():
            if len(ids)<6:continue
            c=cameras[cid]
            solved=cv2.solvePnPGeneric(canonical[ids].astype(np.float64),observed[cid][index,ids].astype(np.float64),c['K'],None,flags=cv2.SOLVEPNP_IPPE)
            if solved[0]:
                for rv,tv in zip(solved[1],solved[2]):
                    R=c['R'].T@cv2.Rodrigues(rv)[0];t=c['R'].T@(tv.reshape(3)-c['t'])
                    seeds.append(seed_pose(np.r_[cv2.Rodrigues(R)[0].reshape(3),t]))
        candidates=[]
        for seed in seeds:
            result=fit(seed,observations);residual=errors(result.x,observations)
            lengths=np.concatenate([np.linalg.norm(v,axis=1) for v in residual.values()])
            candidates.append((float(np.median(lengths)),result))
        _,best=min(candidates,key=lambda item:item[0]);selection=observations
        for _ in range(3):
            residual=errors(best.x,selection)
            selection={cid:ids[np.linalg.norm(residual[cid],axis=1)<8.] for cid,ids in selection.items()}
            selection={cid:ids for cid,ids in selection.items() if len(ids)>=4}
            if len(selection)<2 or sum(map(len,selection.values()))<12:break
            best=fit(best.x,selection)
        if len(selection)<2 or sum(map(len,selection.values()))<12:refined.append(None);continue
        residual=errors(best.x,selection);lengths=np.concatenate([np.linalg.norm(v,axis=1) for v in residual.values()])
        median=float(np.median(lengths));rms=float(np.sqrt(np.mean(lengths**2)))
        result_pose=full_pose(best.x)
        world=canonical@cv2.Rodrigues(result_pose[:3])[0].T+result_pose[3:]
        front=all(np.all((world[ids]@cameras[cid]['R'].T+cameras[cid]['t'])[:,2]>.05) for cid,ids in selection.items())
        valid=bool(best.success and front and median<4 and rms<6)
        record={'time_s':frame['time_s'],'valid':valid,'rvec':result_pose[:3].tolist(),'translation_m':result_pose[3:].tolist(),
            'median_reprojection_px':median,'rms_reprojection_px':rms,'support_cameras':list(selection),
            'observations':int(len(lengths)),'input_observations':sum(map(len,observations.values())),
            'retained_point_indices':{cid:ids.tolist() for cid,ids in selection.items()},'world_positions':world.tolist(),
            'residual_scope':'Retained inliers after 8 px rejection; raw observation counts reported separately'}
        refined.append(record)
        if valid:previous=best.x
        if index%20==0:print('frame',index,'valid',valid,'inliers',len(lengths),'median',round(median,3),flush=True)
    supported=[i for i,pose in enumerate(refined) if pose and pose['valid']]
    if not supported:raise ValueError('No supported multi-view poses after outlier rejection')
    reference=min(supported,key=lambda i:abs(tracks['frames'][i]['time_s']-s['baseline']['start_s']))
    for index,frame in enumerate(tracks['frames']):
        pose=refined[index];inliers=set()
        if pose and pose['valid']:inliers={j for ids in pose['retained_point_indices'].values() for j in ids}
        for j,point in enumerate(frame['points']):
            point['position']=pose['world_positions'][j] if j in inliers else None;point['status']='tracked' if j in inliers else 'occluded'
    tracks['reference_frame']=reference;tracks['source']='Observed video features with explicit multi-view pixel outlier rejection; calibration remains provisional'
    poses['frames']=refined;poses['source_observations']=args.input.as_posix();poses['rejection_threshold_px']=8
    poses['session']=args.session.as_posix()
    poses['camera_calibrations']={entry['id']:entry['calibration'] for entry in s['cameras']}
    poses['motion_assumption']='Upright planar sliding: yaw and XY translation; no tilt or lift' if args.tabletop else 'Unconstrained rigid rotation and translation'
    write(out/'rigid_poses.json',poses);write(out/'point_tracks.json',tracks)
    np.savez_compressed(out/'observations.npz',**{key:observed[key] for key in observed.files})
    summary={'status':'provisional','valid_pose_frames':len(supported),'total_frames':len(refined),'assigned_points':len(canonical),
         'first_valid_time_s':tracks['frames'][supported[0]]['time_s'],'last_valid_time_s':tracks['frames'][supported[-1]]['time_s'],
         'reference_time_s':tracks['frames'][reference]['time_s'],
         'median_inlier_fit_error_px':float(np.median([refined[i]['median_reprojection_px'] for i in supported])),
         'pixel_outlier_threshold':8,'metric_accuracy_verified':False,'no_missing_frame_interpolation':True,
         'session':args.session.as_posix(),'canonical_calibration':None if args.calibration_dir is None else args.calibration_dir.as_posix(),
         'source_observations':args.input.as_posix(),'motion_assumption':poses['motion_assumption']}
    write(out/'summary.json',summary);print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
