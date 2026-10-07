"""Provisional joint camera refinement with measured board and matched flat lid.

Uses two distinct planes and three views, retaining held-out board markers and
lid tracks. Assumptions (pinhole, square pixels, flat lid, manual video timing)
remain explicit; reprojection validation is not an independent metric survey.
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
    parser.add_argument('--output',type=Path,help='New calibration directory; previous attempts are never overwritten')
    parser.add_argument('--lid-height-mm',type=float,help='User-measured table-to-lid height, fixed during camera fitting')
    parser.add_argument('--lid-diameter-mm',type=float,help='User-measured outer lid diameter, used only as a contour cross-check')
    args=parser.parse_args();root=args.session.parent
    if args.lid_height_mm is not None and not 15<args.lid_height_mm<150:
        raise ValueError('Lid height must be between 15 and 150 mm')
    if args.lid_diameter_mm is not None and args.lid_diameter_mm<=0:
        raise ValueError('Lid diameter must be positive')
    out=args.output or root/'calibration/board_lid_refinement_01'
    if out.exists():raise ValueError('Joint calibration attempt already exists')
    out.mkdir(parents=True)
    records=json.loads((root/'calibration/rectified_lid_matches_01/matches.json').read_text())
    record=max(records,key=lambda x:len(set(x['matches']['iphone']['fuji_key_indices'])&set(x['matches']['dji']['fuji_key_indices'])))
    definition=json.loads(Path('documentation/reference_markers/TF4DGS_ChArUco_US_Tabloid_10x6_35mm.json').read_text())
    geometry={m['id']:np.array(m['corners_m'],dtype=float) for m in definition['layout']['markers']}
    ids=['fuji','iphone','dji'];parameters=[];board_data=[]
    for cid in ids:
        data=record['assumed_cameras'][cid];K=np.array(data['K']);R=np.array(data['R']);tv=np.array(data['t'])
        parameters.extend([np.log(np.sqrt(K[0,0]*K[1,1])),K[0,2],K[1,2],*cv2.Rodrigues(R)[0].reshape(-1),*tv])
        audit=json.loads((root/'calibration/marker_audit'/f'{cid}.json').read_text())
        markers=audit['reference']['markers']
        points=np.vstack([geometry[m['id']] for m in markers]);pixels=np.vstack([m['pixels'] for m in markers])
        train=np.repeat([m['id']%5!=0 for m in markers],4)
        board_data.append({'points':points,'pixels':pixels,'train':train,'size':audit['image_size']})
    tracks={}
    for other in ['iphone','dji']:
        pair=record['matches'][other]
        for key,uv1,uv2 in zip(pair['fuji_key_indices'],pair['fuji_native_pixels'],pair['other_native_pixels']):
            tracks.setdefault(key,{'fuji':np.array(uv1)})[other]=np.array(uv2)
    keys=sorted(tracks);initial_height=.059 if args.lid_height_mm is None else args.lid_height_mm/1000
    data=record['assumed_cameras']['fuji'];K=np.array(data['K']);R=np.array(data['R']);t=np.array(data['t'])
    P=K@np.column_stack((R,t));plane=np.column_stack((P[:,0],P[:,1],P[:,3]-initial_height*P[:,2]))
    xy=cv2.perspectiveTransform(np.array([tracks[key]['fuji'] for key in keys]).reshape(-1,1,2),np.linalg.inv(plane)).reshape(-1,2)
    parameters=np.r_[parameters,np.log(initial_height),xy.reshape(-1)]
    # Track-level holdout prevents one observation of a fitted point from
    # being reported as independent validation of that same point.
    train_tracks=np.array([i%5!=0 for i in range(len(keys))])
    def unpack(p):
        cameras=[]
        for i in range(3):
            q=p[i*9:(i+1)*9];f=np.exp(q[0]);K=np.array([[f,0,q[1]],[0,f,q[2]],[0,0,1.]])
            cameras.append((K,q[3:6],q[6:9]))
        positions=np.column_stack((p[28:].reshape(-1,2),np.full(len(keys),-np.exp(p[27]))))
        return cameras,positions
    def residual(p):
        cameras,positions=unpack(p);parts=[]
        for i,(K,rv,tv) in enumerate(cameras):
            data=board_data[i];keep=data['train']
            pr=cv2.projectPoints(data['points'][keep],rv,tv,K,None)[0].reshape(-1,2)
            parts.append((pr-data['pixels'][keep]).reshape(-1))
            track_indices=[j for j,key in enumerate(keys) if train_tracks[j] and ids[i] in tracks[key]]
            if track_indices:
                pr=cv2.projectPoints(positions[track_indices],rv,tv,K,None)[0].reshape(-1,2)
                pix=np.array([tracks[keys[j]][ids[i]] for j in track_indices])
                parts.append((pr-pix).reshape(-1))
        # Weak principal-point priors only for the uncropped exports. They
        # are assumptions and are not calibration observations.
        for i in range(2):
            width,height=board_data[i]['size']
            parts.append(np.array([(p[i*9+1]-width/2)/300,(p[i*9+2]-height/2)/300]))
        return np.concatenate(parts)
    lower=np.full(len(parameters),-np.inf);upper=np.full(len(parameters),np.inf)
    for i in range(3):
        lower[i*9]=np.log(400);upper[i*9]=np.log(15000)
        lower[i*9+1:i*9+3]=[-4000,-7000];upper[i*9+1:i*9+3]=[8000,8000]
    lower[27]=np.log(.015);upper[27]=np.log(.15)
    # Held-out point XYs are left out of the optimization and later solved
    # independently from their Fuji observation on the learned lid plane.
    active=np.array([i for i in range(len(parameters)) if i<28 or train_tracks[(i-28)//2]])
    if args.lid_height_mm is not None:active=active[active!=27]
    fixed=parameters.copy()
    def expand(values):
        p=fixed.copy();p[active]=values;return p
    start_error=float(np.sqrt(np.mean(residual(parameters)**2)))
    fit=least_squares(lambda values:residual(expand(values)),parameters[active],loss='soft_l1',f_scale=2.,
                      max_nfev=500,x_scale='jac',bounds=(lower[active],upper[active]))
    final=expand(fit.x);cameras,positions=unpack(final)
    # Validate held-out tracks by predicting other cameras from Fuji on the
    # lid plane, without fitting their hidden XY coordinates across views.
    K,rv,tv=cameras[0];R=cv2.Rodrigues(rv)[0];P=K@np.column_stack((R,tv))
    plane=np.column_stack((P[:,0],P[:,1],P[:,3]-np.exp(final[27])*P[:,2]))
    withheld=np.flatnonzero(~train_tracks)
    held_xy=cv2.perspectiveTransform(np.array([tracks[keys[j]]['fuji'] for j in withheld]).reshape(-1,1,2),np.linalg.inv(plane)).reshape(-1,2)
    positions[withheld,:2]=held_xy
    summaries=[]
    for i,(K,rv,tv) in enumerate(cameras):
        data=board_data[i];pr=cv2.projectPoints(data['points'],rv,tv,K,None)[0].reshape(-1,2)
        errors=np.linalg.norm(pr-data['pixels'],axis=1)
        indices=[j for j,key in enumerate(keys) if ids[i] in tracks[key]]
        predictions=cv2.projectPoints(positions[indices],rv,tv,K,None)[0].reshape(-1,2)
        observed=np.array([tracks[keys[j]][ids[i]] for j in indices]);lid_errors=np.linalg.norm(predictions-observed,axis=1)
        train_mask=train_tracks[indices]
        rms=lambda x:None if not len(x) else float(np.sqrt(np.mean(x*x)))
        R=cv2.Rodrigues(rv)[0]
        value={'schema_version':1,'camera_id':ids[i],'image_size':data['size'],'model':'PINHOLE',
               'params':[float(K[0,0]),float(K[1,1]),float(K[0,2]),float(K[1,2])],
               'world_to_camera':{'R':R.tolist(),'t':tv.tolist()},'world_units':'metres',
               'status':'provisional_joint_board_and_lid','intrinsic_accuracy_verified':False,
               'calibration_run':out.as_posix(),
               'measured_lid_height_m':None if args.lid_height_mm is None else args.lid_height_mm/1000,
               'sensor_sync_accuracy_verified':False,'independent_metric_accuracy_verified':False,
               'board_fit_rms_px':rms(errors[data['train']]),'board_heldout_rms_px':rms(errors[~data['train']]),
               'lid_fit_rms_px':rms(lid_errors[train_mask]),'lid_heldout_rms_px':None if i==0 else rms(lid_errors[~train_mask]),
               'holdout_note':'Held-out point XYs use Fuji only; validation is in the other cameras.',
               'assumptions':['Square pixels and zero lens distortion','Flat circular container lid','Weak centered principal-point priors in uncropped views','Manual 33.37 ms synchronization uncertainty']}
        (out/f'{ids[i]}.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        summaries.append(value);print(json.dumps({k:value[k] for k in ['camera_id','params','board_fit_rms_px','board_heldout_rms_px','lid_fit_rms_px','lid_heldout_rms_px']}),flush=True)
    np.savez(out/'lid_tracks.npz',positions=positions,fuji_pixels=np.array([tracks[key]['fuji'] for key in keys]),train=train_tracks,key_indices=np.array(keys))
    # The colored outer contour is an approximate rim observation, independent
    # of the matched texture used in fitting. Do not fit the cameras to it or
    # call it an independent metric survey: lid foil and segmentation can bias
    # the detected outline. Store its error against the user's second dimension.
    diameter_checks=[]
    bundles=json.loads((root/'manifests/sync-plan.json').read_text())['bundles']
    reference=next(b for b in bundles if b['views']['fuji']['source_index']==360)
    for cid,(K,rv,tv) in zip(ids,cameras):
        image=cv2.imread(str(root/reference['views'][cid]['image']))
        if image is None:raise ValueError(f'{cid}: missing native reference frame')
        hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
        mask=cv2.inRange(hsv,np.array([85,65,35]),np.array([140,255,255]))
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        if not contours:raise ValueError(f'{cid}: cannot check the outer lid contour')
        contour=max(contours,key=cv2.contourArea).reshape(-1,2)
        R=cv2.Rodrigues(rv)[0];H=K@np.column_stack((R[:,0],R[:,1],tv-np.exp(final[27])*R[:,2]))
        xy=cv2.perspectiveTransform(contour.astype(float)[None],np.linalg.inv(H))[0]
        circle=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],np.sum(xy**2,axis=1),rcond=None)[0]
        radius=float(np.sqrt(circle[2]+np.sum(circle[:2]**2)))
        diameter_mm=radius*2000
        check={'camera_id':cid,'contour_diameter_mm':diameter_mm,'center_xy_m':circle[:2].tolist(),
               'radial_rms_mm':float(np.sqrt(np.mean((np.linalg.norm(xy-circle[:2],axis=1)-radius)**2)))*1000,
               'measured_diameter_mm':args.lid_diameter_mm,
               'difference_mm':None if args.lid_diameter_mm is None else diameter_mm-args.lid_diameter_mm}
        diameter_checks.append(check)
        theta=np.linspace(0,2*np.pi,241)
        drawing_radius=radius if args.lid_diameter_mm is None else args.lid_diameter_mm/2000
        rim=np.c_[circle[0]+drawing_radius*np.cos(theta),circle[1]+drawing_radius*np.sin(theta),np.full(len(theta),-np.exp(final[27]))]
        uv=cv2.projectPoints(rim,rv,tv,K,None)[0].reshape(-1,2).round().astype(np.int32)
        cv2.drawContours(image,[contour.reshape(-1,1,2)],-1,(0,180,255),2)
        cv2.polylines(image,[uv],True,(0,255,0),2)
        factor=min(1.,1400/max(image.shape[:2]))
        preview=cv2.resize(image,None,fx=factor,fy=factor,interpolation=cv2.INTER_AREA)
        cv2.putText(preview,f'{cid}: contour {diameter_mm:.2f} mm; green = measured rim; orange = detected',(15,30),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2)
        cv2.imwrite(str(out/f'{cid}_rim_check.jpg'),preview)
    summary={'status':'provisional','optimizer_success':bool(fit.success),'message':fit.message,'initial_rms_component_px':start_error,
             'final_rms_component_px':float(np.sqrt(np.mean(residual(final)**2))),'estimated_lid_height_m':float(np.exp(final[27])),
             'lid_tracks':len(keys),'triple_tracks':sum(len(x)==3 for x in tracks.values()),'holdout_tracks':len(withheld),
             'lid_height_source':'fitted' if args.lid_height_mm is None else 'user measurement, fixed during fitting',
             'measured_lid_diameter_mm':args.lid_diameter_mm,'diameter_used_in_camera_fit':False,
             'diameter_cross_checks':diameter_checks,
             'diameter_check_note':'Approximate blue-rim segmentation; not an independent calibration or physical accuracy certificate.',
             'intrinsic_accuracy_verified':False,'independent_metric_accuracy_verified':False,'cameras':summaries}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print('Joint calibration status:',fit.message,'lid height',summary['estimated_lid_height_m'],flush=True)


if __name__=='__main__':main()
