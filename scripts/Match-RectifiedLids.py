"""Search actual lid correspondences after provisional metric-plane rectification.

Rectification is a matching aid; it does not certify the camera parameters.
Native-coordinate matches and diagnostic images are retained for inspection.
"""
import argparse
import json
from pathlib import Path
import runpy

import cv2
import numpy as np


BOOT=runpy.run_path(str(Path(__file__).with_name('Solve-BoardBootstrap.py')))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    args=parser.parse_args();root=args.session.parent
    out=root/'calibration/rectified_lid_matches_01'
    if out.exists():raise ValueError('Rectified match attempt already exists')
    out.mkdir(parents=True)
    cv2.setNumThreads(2)
    definition=json.loads(Path('documentation/reference_markers/TF4DGS_ChArUco_US_Tabloid_10x6_35mm.json').read_text())
    geometry={m['id']:np.array(m['corners_m'],dtype=float) for m in definition['layout']['markers']}
    cameras={}
    grid=np.array([[3000.,0,300.],[0,3000.,300.],[0,0,1.]])
    for cid in ['fuji','iphone','dji']:
        audit=json.loads((root/'calibration/marker_audit'/f'{cid}.json').read_text())
        H=np.array(audit['reference']['homography_board_m_to_native_px'])
        if cid=='dji':
            family=list(BOOT['dji_family'](H));K=family[len(family)//2]
        else:K=BOOT['homography_intrinsics'](H,*audit['image_size'])
        obj=np.vstack([geometry[m['id']] for m in audit['reference']['markers']])
        pixels=np.vstack([m['pixels'] for m in audit['reference']['markers']]).astype(float)
        ok,rv,tv=cv2.solvePnP(obj,pixels,K,None)
        if not ok:raise ValueError('Initial board pose failed')
        R=cv2.Rodrigues(rv)[0];P=K@np.column_stack((R,tv))
        native=cv2.imread(str(root/f'calibration/sfm/images/{cid}/baseline_000360.png'))
        cameras[cid]={'K':K,'R':R,'rv':rv,'tv':tv,'P':P,'native':native}
    results=[]
    sift=cv2.SIFT_create(nfeatures=4000,contrastThreshold=.012,edgeThreshold=15)
    matcher=cv2.BFMatcher(cv2.NORM_L2)
    for height in [.025,.04,.055,.075,.095]:
        views={}
        for cid,data in cameras.items():
            plane=np.column_stack((data['P'][:,0],data['P'][:,1],data['P'][:,3]-height*data['P'][:,2]))
            transform=grid@np.linalg.inv(plane)
            image=cv2.warpPerspective(data['native'],transform,(1800,1200),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
            hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
            blue=cv2.inRange(hsv,np.array([85,65,35]),np.array([135,255,255]))
            blue=cv2.morphologyEx(blue,cv2.MORPH_CLOSE,np.ones((17,17),np.uint8))
            contours,_=cv2.findContours(blue,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            mask=np.zeros(blue.shape,np.uint8)
            if contours:
                largest=max(contours,key=cv2.contourArea)
                cv2.fillConvexPoly(mask,cv2.convexHull(largest),255)
                mask=cv2.dilate(mask,np.ones((19,19),np.uint8))
            gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            clahe=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8))
            key,descriptors=sift.detectAndCompute(clahe.apply(gray),mask)
            cv2.imwrite(str(out/f'{cid}_height_{round(height*1000):03d}.jpg'),image,[cv2.IMWRITE_JPEG_QUALITY,94])
            views[cid]={'image':image,'key':key,'descriptors':descriptors,'transform':transform}
        matches={}
        for other in ['iphone','dji']:
            a,b=views['fuji'],views[other]
            candidates=[]
            if a['descriptors'] is not None and b['descriptors'] is not None:
                for pair in matcher.knnMatch(a['descriptors'],b['descriptors'],k=2):
                    if len(pair)==2 and pair[0].distance<.85*pair[1].distance:candidates.append(pair[0])
            if len(candidates)>=4:
                pa=np.array([a['key'][m.queryIdx].pt for m in candidates],dtype=float)
                pb=np.array([b['key'][m.trainIdx].pt for m in candidates],dtype=float)
                H,inliers=cv2.findHomography(pa,pb,cv2.RANSAC,2.5)
                accepted=np.flatnonzero(inliers.reshape(-1)) if H is not None else np.array([],dtype=int)
            else:accepted=np.array([],dtype=int)
            na=[];nb=[]
            for index in accepted:
                na.append(pa[index]);nb.append(pb[index])
            if len(na):
                native_a=cv2.perspectiveTransform(np.array(na).reshape(-1,1,2),np.linalg.inv(a['transform'])).reshape(-1,2)
                native_b=cv2.perspectiveTransform(np.array(nb).reshape(-1,1,2),np.linalg.inv(b['transform'])).reshape(-1,2)
            else:native_a=native_b=np.empty((0,2))
            match_data={'candidate_count':len(candidates),'homography_inliers':len(accepted),
                        'fuji_native_pixels':native_a.tolist(),'other_native_pixels':native_b.tolist(),
                        'fuji_key_indices':[candidates[i].queryIdx for i in accepted]}
            matches[other]=match_data
            visual=cv2.drawMatches(a['image'],a['key'],b['image'],b['key'],[candidates[i] for i in accepted],None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            cv2.imwrite(str(out/f'fuji_{other}_height_{round(height*1000):03d}_matches.jpg'),visual,[cv2.IMWRITE_JPEG_QUALITY,92])
        record={'height_m':height,'matches':matches,'assumed_cameras':{cid:{'K':data['K'].tolist(),'R':data['R'].tolist(),'t':data['tv'].reshape(-1).tolist()} for cid,data in cameras.items()}}
        results.append(record)
        print('Rectification height',height,'inliers:',{cid:value['homography_inliers'] for cid,value in matches.items()},flush=True)
    (out/'matches.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
