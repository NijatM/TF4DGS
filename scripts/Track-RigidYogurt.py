"""Track observed printed-lid features and fit provisional multi-view rigid poses.

Tracks never bridge an optical-flow failure. Geometry uses the declared rigid
container assumption; color is sampled from one fixed camera per point and
inverse BT.709 encoded-video transfer. This is not independent metric/color
accuracy validation or a non-rigid Gaussian deformation estimator.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from scipy.optimize import least_squares


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    parser.add_argument('--output',type=Path,default=Path('outputs/dynamic_yogurt_001/rigid_tracking_01'))
    parser.add_argument('--whole-lid-mask',action='store_true',help='Allow white/green printed features inside the detected blue lid rim')
    args=parser.parse_args();root=args.session.parent;out=args.output
    if out.exists():raise ValueError('Rigid tracking output exists; preserve it before rerunning')
    out.mkdir(parents=True);cv2.setNumThreads(2)
    session=json.loads(args.session.read_text(encoding='utf-8-sig'))
    plan=json.loads((root/'manifests/sync-plan.json').read_text());bundles=plan['bundles']
    model=json.loads((root/'calibration/board_lid_refinement_01/summary.json').read_text())
    records=json.loads((root/'calibration/rectified_lid_matches_01/matches.json').read_text())
    record=max(records,key=lambda x:len(set(x['matches']['iphone']['fuji_key_indices'])&set(x['matches']['dji']['fuji_key_indices'])))
    observations={}
    for cid in ['iphone','dji']:
        pair=record['matches'][cid]
        for key,fuji,other in zip(pair['fuji_key_indices'],pair['fuji_native_pixels'],pair['other_native_pixels']):
            observations.setdefault(key,{'fuji':fuji})[cid]=other
    keys=sorted(observations);seed=np.load(root/'calibration/board_lid_refinement_01/lid_tracks.npz')
    canonical=seed['positions'];n=len(keys)
    ref=min(range(len(bundles)),key=lambda i:abs(bundles[i]['views']['fuji']['source_index']-360))
    if bundles[ref]['views']['fuji']['source_index']!=360:raise ValueError('Canonical source frame is absent from the extraction')
    cameras={};flows={};colors={};quality={}
    for camera in session['cameras']:
        cid=camera['id'];data=json.loads((root/camera['calibration']).read_text());p=data['params']
        K=np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]])
        cameras[cid]={'K':K,'R':np.array(data['world_to_camera']['R']),'t':np.array(data['world_to_camera']['t'])}
        gray=[];blue=[];small=[]
        for bundle in bundles:
            image=cv2.imread(str(root/bundle['views'][cid]['image']))
            factor=min(1.,1920/max(image.shape[:2]));size=(round(image.shape[1]*factor),round(image.shape[0]*factor))
            image=cv2.resize(image,size,interpolation=cv2.INTER_AREA)
            small.append(image);gray.append(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY))
            hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
            mask=cv2.inRange(hsv,np.array([85,55,30]),np.array([140,255,255]))
            if args.whole_lid_mask:
                original_mask=mask.copy()
                connected=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
                contours,_=cv2.findContours(connected,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                mask=np.zeros_like(mask)
                if contours:
                    hull=cv2.convexHull(max(contours,key=cv2.contourArea))
                    if cv2.contourArea(hull)>500:cv2.fillConvexPoly(mask,hull,255)
                mask=cv2.bitwise_or(mask,original_mask)
            blue.append(mask)
        width,height=data['image_size'];scale=np.array([small[0].shape[1]/width,small[0].shape[0]/height])
        points=np.full((len(bundles),n,2),np.nan,dtype=np.float32)
        q=np.full((len(bundles),n),np.nan,dtype=float)
        initial=np.array([observations[key].get(cid,[np.nan,np.nan]) for key in keys],dtype=np.float32)
        points[ref]=initial;q[ref]=0
        for direction in [-1,1]:
            previous=ref
            for index in range(ref+direction,len(bundles) if direction>0 else -1,direction):
                active=np.flatnonzero(np.isfinite(points[previous]).all(axis=1))
                if not len(active):break
                old=(points[previous,active]*scale).astype(np.float32).reshape(-1,1,2)
                new,status,error=cv2.calcOpticalFlowPyrLK(gray[previous],gray[index],old,None,
                    winSize=(25,25),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.01))
                back,back_status,_=cv2.calcOpticalFlowPyrLK(gray[index],gray[previous],new,None,
                    winSize=(25,25),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.01))
                fb=np.linalg.norm(back.reshape(-1,2)-old.reshape(-1,2),axis=1)
                valid=(status.reshape(-1)>0)&(back_status.reshape(-1)>0)&(fb<1.)&(error.reshape(-1)<35)
                for j,point in enumerate(new.reshape(-1,2)):
                    x,y=np.round(point).astype(int)
                    if x<8 or y<8 or x>=gray[index].shape[1]-8 or y>=gray[index].shape[0]-8:
                        valid[j]=False
                    elif np.mean(blue[index][y-7:y+8,x-7:x+8]>0)<.025:
                        valid[j]=False
                selected=active[valid]
                points[index,selected]=new.reshape(-1,2)[valid]/scale;q[index,selected]=fb[valid]
                previous=index
        sampled=np.full((len(bundles),n,3),np.nan)
        for index,image in enumerate(small):
            for j in np.flatnonzero(np.isfinite(points[index]).all(axis=1)):
                x,y=np.round(points[index,j]*scale).astype(int)
                x=np.clip(x,1,image.shape[1]-2);y=np.clip(y,1,image.shape[0]-2)
                encoded=np.median(image[y-1:y+2,x-1:x+2,::-1].reshape(-1,3),axis=0)/255.
                sampled[index,j]=np.where(encoded<.081,encoded/4.5,((encoded+.099)/1.099)**(1/.45))
        flows[cid]=points;quality[cid]=q;colors[cid]=sampled
        print(cid,'tracked point/frame observations',int(np.isfinite(points[:,:,0]).sum()),'of',len(bundles)*n,flush=True)
        del gray,blue,small
    poses=[None]*len(bundles)
    def fit_frame(index,initial):
        supported=[cid for cid in cameras if np.isfinite(flows[cid][index]).all(axis=1).sum()>=4]
        if len(supported)<2:return None
        obs=[(cid,np.flatnonzero(np.isfinite(flows[cid][index]).all(axis=1))) for cid in supported]
        if sum(len(x[1]) for x in obs)<12:return None
        def residual(p):
            rotation=cv2.Rodrigues(p[:3])[0];world=canonical@rotation.T+p[3:]
            terms=[]
            for cid,indices in obs:
                data=cameras[cid];camera=world[indices]@data['R'].T+data['t']
                predicted=camera@data['K'].T;predicted=predicted[:,:2]/predicted[:,2:]
                terms.append((predicted-flows[cid][index,indices]).reshape(-1))
            return np.concatenate(terms)
        fit=least_squares(residual,initial,loss='soft_l1',f_scale=3,max_nfev=80,x_scale='jac')
        errors=np.linalg.norm(residual(fit.x).reshape(-1,2),axis=1)
        median=float(np.median(errors));rms=float(np.sqrt(np.mean(errors**2)))
        rotation=cv2.Rodrigues(fit.x[:3])[0];world=canonical@rotation.T+fit.x[3:]
        valid=fit.success and median<7 and rms<14 and np.all(np.isfinite(fit.x))
        return {'time_s':bundles[index]['time_s'],'valid':bool(valid),'rvec':fit.x[:3].tolist(),
                'translation_m':fit.x[3:].tolist(),'median_reprojection_px':median,'rms_reprojection_px':rms,
                'support_cameras':supported,'observations':int(len(errors)),'world_positions':world.tolist()}
    poses[ref]=fit_frame(ref,np.zeros(6))
    if poses[ref] is None or not poses[ref]['valid']:raise ValueError('Baseline rigid-pose fit failed')
    for direction in [-1,1]:
        previous=np.r_[poses[ref]['rvec'],poses[ref]['translation_m']]
        for index in range(ref+direction,len(bundles) if direction>0 else -1,direction):
            pose=fit_frame(index,previous);poses[index]=pose
            if pose and pose['valid']:previous=np.r_[pose['rvec'],pose['translation_m']]
    valid=[i for i,p in enumerate(poses) if p and p['valid']]
    if not valid:raise ValueError('No supported rigid poses')
    reference=min(valid,key=lambda i:abs(bundles[i]['time_s']-2.5))
    color_sources=['iphone' if 'iphone' in observations[key] else 'fuji' for key in keys]
    frames=[]
    for index,bundle in enumerate(bundles):
        pose=poses[index];points=[]
        for j,key in enumerate(keys):
            seen=any(np.isfinite(flows[cid][index,j]).all() for cid in cameras)
            tracked=pose is not None and pose['valid'] and seen
            rgb=colors[color_sources[j]][index,j]
            points.append({'id':f'lid_feature_{j:03d}','position':pose['world_positions'][j] if tracked else None,
                           'rgb':rgb.tolist() if np.isfinite(rgb).all() else None,
                           'status':'tracked' if tracked else 'occluded','geometry_source':'multi-view rigid pose estimate',
                           'appearance_camera':color_sources[j]})
        frames.append({'time_s':bundle['time_s'],'points':points})
    tracks={'schema_version':1,'identity_kind':'assigned_points','color_space':'linear_rgb','reference_frame':reference,
            'metres_per_unit':1.,'frames':frames,'source':'Actual video features + provisional camera calibration + rigid container assumption',
            'metric_accuracy_verified':False,'color_note':'Inverse BT.709 video transfer, fixed source camera per feature; not radiometric/material-color calibration.'}
    (out/'point_tracks.json').write_text(json.dumps(tracks,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'rigid_poses.json').write_text(json.dumps({'canonical_source_frame':360,'canonical_points_m':canonical.tolist(),
        'frames':poses,'metric_accuracy_verified':False,'no_interpolation_across_failed_tracks':True},indent=2)+'\n',encoding='utf-8')
    np.savez(out/'observations.npz',**{cid:points for cid,points in flows.items()})
    summary={'status':'provisional','assigned_points':n,'whole_lid_mask':args.whole_lid_mask,'valid_pose_frames':len(valid),'total_frames':len(bundles),
             'first_valid_time_s':bundles[valid[0]]['time_s'],'last_valid_time_s':bundles[valid[-1]]['time_s'],
             'reference_time_s':bundles[reference]['time_s'],'median_fit_error_px':float(np.median([poses[i]['median_reprojection_px'] for i in valid])),
             'metric_accuracy_verified':False}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8');print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
