"""Estimate provisional shared cameras from a measured board and real matches.

The two uncropped views assume centered principal points. Their triangulated
non-planar matches constrain the cropped DJI camera. Low reprojection error
does not certify physical accuracy: no independent intrinsic calibration or
sensor synchronization is available. Output provenance retains these limits.
"""
import argparse
import json
from pathlib import Path
import sqlite3

import cv2
import numpy as np
from scipy.optimize import least_squares


def project(points, K, rv, tv):
    return cv2.projectPoints(points,rv,tv,K,None)[0].reshape(-1,2)


def homography_intrinsics(H, width, height):
    a=H[:2,0]-np.array([width/2,height/2])*H[2,0]
    b=H[:2,1]-np.array([width/2,height/2])*H[2,1]
    az,bz=H[2,0],H[2,1]
    invf=np.linalg.solve([[a[0]*b[0],a[1]*b[1]],
                         [a[0]**2-b[0]**2,a[1]**2-b[1]**2]],[-az*bz,-az**2+bz**2])
    if not np.all(invf>0):
        raise ValueError('Centered principal-point model is unsuitable')
    fx,fy=1/np.sqrt(invf)
    return np.array([[fx,0,width/2],[0,fy,height/2],[0,0,1.]])


def dji_family(H):
    def solve(cx):
        ax=H[0,0]-cx*H[2,0];bx=H[0,1]-cx*H[2,1]
        ay,by=H[1,0],H[1,1];az,bz=H[2,0],H[2,1]
        matrix=[[-(ay*bz+by*az),az*bz],[-2*(ay*az-by*bz),az*az-bz*bz]]
        cy,value=np.linalg.solve(matrix,[-ax*bx-ay*by,-ax*ax+bx*bx-ay*ay+by*by])
        return cy,value-cy*cy
    xs=np.array([-1000.,0,1000.]);coefficients=np.polyfit(xs,[solve(x)[1] for x in xs],2)
    peak=-coefficients[1]/(2*coefficients[0])
    roots=np.sort(np.roots(coefficients).real)
    for cx in np.linspace(roots[0],roots[-1],13)[1:-1]:
        cy,f2=solve(cx)
        if f2>0:
            focal=np.sqrt(f2)
            yield np.array([[focal,0,cx],[0,focal,cy],[0,0,1.]])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    args=parser.parse_args()
    session=json.loads(args.session.read_text(encoding='utf-8-sig'))
    root=args.session.parent
    output=root/'calibration/board_bootstrap'
    if output.exists():
        raise ValueError('Board bootstrap exists; preserve it before rerunning')
    output.mkdir(parents=True)
    definition=json.loads(Path('documentation/reference_markers/TF4DGS_ChArUco_US_Tabloid_10x6_35mm.json').read_text())
    geometry={m['id']:np.array(m['corners_m'],dtype=float) for m in definition['layout']['markers']}
    cameras={}
    for cid in ['fuji','iphone','dji']:
        audit=json.loads((root/'calibration/marker_audit'/f'{cid}.json').read_text())
        obj=np.vstack([geometry[m['id']] for m in audit['reference']['markers']])
        pixels=np.vstack([m['pixels'] for m in audit['reference']['markers']]).astype(float)
        cameras[cid]={'object':obj,'pixels':pixels,'H':np.array(audit['reference']['homography_board_m_to_native_px']),
                      'size':audit['image_size']}
        if cid!='dji':
            data=cameras[cid]
            data['K']=homography_intrinsics(data['H'],*data['size'])
            ok,data['rv'],data['tv']=cv2.solvePnP(obj,pixels,data['K'],None)
            if not ok:raise ValueError('Uncropped board pose failed')
            data['R']=cv2.Rodrigues(data['rv'])[0]
            data['P']=data['K']@np.column_stack((data['R'],data['tv']))
    db=sqlite3.connect(root/'calibration/sfm/database.db')
    images={name.split('/')[0]:image_id for image_id,name in db.execute('select image_id,name from images')}
    def features(cid):
        rows,cols,blob=db.execute('select rows,cols,data from keypoints where image_id=?',(images[cid],)).fetchone()
        return np.frombuffer(blob,np.float32).reshape(rows,cols)[:,:2].astype(float)
    keys={cid:features(cid) for cid in images}
    def matches(cid1,cid2):
        a,b=images[cid1],images[cid2]
        reverse=a>b
        if reverse:a,b=b,a
        result=db.execute('select rows,data from two_view_geometries where pair_id=?',(a*2147483647+b,)).fetchone()
        if result is None:return np.empty((0,2),dtype=int)
        pairs=np.frombuffer(result[1],np.uint32).reshape(result[0],2).astype(int)
        return pairs[:,::-1] if reverse else pairs
    pair=matches('fuji','iphone');p1=keys['fuji'][pair[:,0]];p2=keys['iphone'][pair[:,1]]
    homogeneous=cv2.triangulatePoints(cameras['fuji']['P'],cameras['iphone']['P'],p1.T,p2.T)
    points=(homogeneous[:3]/homogeneous[3]).T
    errors=[];depths=[]
    for cid,pix in [('fuji',p1),('iphone',p2)]:
        data=cameras[cid]
        errors.append(np.linalg.norm(project(points,data['K'],data['rv'],data['tv'])-pix,axis=1))
        depths.append((points@data['R'].T+data['tv'].reshape(1,3))[:,2])
    valid=(np.max(errors,axis=0)<2)&(np.min(depths,axis=0)>0)&np.isfinite(points).all(axis=1)
    valid&=(points[:,0]>-.2)&(points[:,0]<.6)&(points[:,1]>-.2)&(points[:,1]<.45)&(points[:,2]>-.2)&(points[:,2]<.025)
    map13=dict(matches('fuji','dji'));map23=dict(matches('iphone','dji'))
    dji_world=[];dji_pixels=[];nonplanar=[]
    for i,(index1,index2) in enumerate(pair):
        if not valid[i]:continue
        index3=map13.get(index1,map23.get(index2))
        if index3 is None or (index1 in map13 and index2 in map23 and map13[index1]!=map23[index2]):continue
        # Board points have known metric coordinates; depth information must
        # come from independently triangulated off-board material features.
        if points[i,2]>=-.012:continue
        dji_world.append(points[i]);dji_pixels.append(keys['dji'][index3]);nonplanar.append(i)
    print('Triangulated acceptable pair matches:',int(valid.sum()),'non-planar triple matches:',len(nonplanar),flush=True)
    data=cameras['dji']
    world=data['object'];pixels=data['pixels']
    if len(dji_world)<6:
        raise ValueError(f'Only {len(dji_world)} off-plane triple matches; DJI crop calibration is not sufficiently constrained')
    world=np.vstack((world,np.array(dji_world)));pixels=np.vstack((pixels,np.array(dji_pixels)))
    fits=[]
    for K in dji_family(data['H']):
        ok,rv,tv=cv2.solvePnP(data['object'],data['pixels'],K,None)
        if not ok:continue
        initial=np.r_[np.log(K[0,0]),K[0,2],K[1,2],rv.reshape(-1),tv.reshape(-1)]
        def residual(parameters):
            f=np.exp(parameters[0]);matrix=np.array([[f,0,parameters[1]],[0,f,parameters[2]],[0,0,1.]])
            return (project(world,matrix,parameters[3:6],parameters[6:9])-pixels).reshape(-1)
        fit=least_squares(residual,initial,loss='soft_l1',f_scale=2.,max_nfev=400,
                          bounds=([np.log(400),-4000,-7000,-np.inf,-np.inf,-np.inf,-np.inf,-np.inf,-np.inf],
                                  [np.log(15000),6000,7000,np.inf,np.inf,np.inf,np.inf,np.inf,np.inf]),x_scale='jac')
        fits.append((float(np.mean(residual(fit.x)**2)),fit))
    if not fits:raise ValueError('No physically admissible cropped-camera initialization')
    _,fit=min(fits,key=lambda value:value[0]);f=np.exp(fit.x[0])
    data['K']=np.array([[f,0,fit.x[1]],[0,f,fit.x[2]],[0,0,1.]])
    data['rv']=fit.x[3:6].reshape(3,1);data['tv']=fit.x[6:9].reshape(3,1)
    data['R']=cv2.Rodrigues(data['rv'])[0]
    data['P']=data['K']@np.column_stack((data['R'],data['tv']))
    summaries=[]
    for cid,data in cameras.items():
        K=data['K']
        rms=float(np.sqrt(np.mean(np.sum((project(data['object'],K,data['rv'],data['tv'])-data['pixels'])**2,axis=1))))
        center=(-data['R'].T@data['tv']).reshape(-1)
        value={'schema_version':1,'camera_id':cid,'image_size':data['size'],'model':'PINHOLE',
               'params':[float(K[0,0]),float(K[1,1]),float(K[0,2]),float(K[1,2])],
               'world_to_camera':{'R':data['R'].tolist(),'t':data['tv'].reshape(-1).tolist()},
               'world_units':'metres','intrinsic_accuracy_verified':False,'sensor_sync_accuracy_verified':False,
               'status':'provisional_board_and_multiview_bootstrap','board_reprojection_rms_px':rms,
               'assumptions':['Zero lens distortion','Centered principal point in Fuji/iPhone exports','DJI square pixels; crop principal point fitted','Manual one-frame video alignment'],
               'independent_calibration_validation_available':False}
        (output/f'{cid}.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        summary={'camera_id':cid,'params':value['params'],'board_rms_px':rms,'camera_center_m':center.tolist()}
        summaries.append(summary);print(json.dumps(summary),flush=True)
    native=cv2.imread(str(root/'calibration/sfm/images/fuji/baseline_000360.png'))
    selected=np.flatnonzero(valid)
    uv=np.round(p1[selected]).astype(int);colors=native[uv[:,1],uv[:,0],::-1].copy()/255.
    np.savez(output/'sparse_seed.npz',positions=points[selected],rgb=colors,
             source_pair_indices=pair[selected],off_plane_triple_indices=np.array(nonplanar))
    summary={'status':'provisional','physical_board_measured':True,'independent_accuracy_verified':False,
             'pair_matches':len(pair),'accepted_pair_points':int(valid.sum()),'off_plane_triple_matches':len(nonplanar),
             'cameras':summaries,'dji_fit_condition':float(np.linalg.cond(fit.jac))}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
