"""Attempt observed multi-view textile material tracks, retaining every failure.

No flow track is reidentified after loss. Rigid motion is not assumed. Initial
stereo matches are constrained by board geometry and native pixel reprojection;
scale and off-plane geometry remain provisional camera-model estimates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def project(points,c):
    camera=points@c['R'].T+c['t'];p=camera@c['K'].T
    return p[:,:2]/p[:,2:]


def triangulate(observations,cameras):
    terms=[]
    for cid,xy in observations.items():
        P=cameras[cid]['P'];terms.extend([xy[0]*P[2]-P[0],xy[1]*P[2]-P[1]])
    _,_,v=np.linalg.svd(np.array(terms));point=v[-1,:3]/v[-1,3]
    errors={cid:float(np.linalg.norm(project(point[None],cameras[cid])[0]-xy)) for cid,xy in observations.items()}
    front=all((cameras[cid]['R']@point+cameras[cid]['t'])[2]>.05 for cid in observations)
    return point,errors,front


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',type=Path,default=Path('data/dynamic_textile_001/session.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/dynamic_textile_001/material_tracking_01'))
    p.add_argument('--rectified',action='store_true',help='Detect/match on a provisional plane-rectified view')
    p.add_argument('--allow-stereo',action='store_true',help='Allow points initialized in two views; preserve per-point visibility')
    p.add_argument('--native-flow',action='store_true',help='Track every original 29.97 Hz video frame, then sample the existing 10 Hz plan')
    p.add_argument('--empty-calibration',type=Path,default=Path('data/dynamic_yogurt_001/calibration/cameras'),
        help='Calibration of the matched empty-board yogurt images; use the corresponding measured fit when testing measured textile cameras')
    p.add_argument('--flow-backend',choices=['lk','raft'],default='lk')
    p.add_argument('--tracking-long-side',type=int,default=1920,help='Diagnostic/flow resolution; source PNGs remain native')
    p.add_argument('--raft-checkpoint',type=Path,default=Path('.local/tools/flow/checkpoints/raft_large_C_T_SKHT_V2-ff5fadd5.pth'))
    p.add_argument('--initialization-source',type=Path,help='Reuse observed initial IDs for a temporal-backend comparison')
    args=p.parse_args();root=args.session.parent;out=args.output
    if out.exists():raise ValueError('Preserve previous attempts under their original name')
    out.mkdir(parents=True);cv2.setNumThreads(3)
    if not 640<=args.tracking_long_side<=1920:raise ValueError('Invalid flow resolution')
    network=None
    if args.flow_backend=='raft':
        import torch
        import torch.nn.functional as F
        from torchvision.models.optical_flow import raft_large
        expected='ff5fadd56d26b40647388883af1547351ea17868b765c05b27231e72dd16a322'
        if hashlib.sha256(args.raft_checkpoint.read_bytes()).hexdigest()!=expected:raise ValueError('RAFT weight checksum mismatch')
        torch.set_num_threads(4)
        network=raft_large(weights=None).cuda().eval()
        network.load_state_dict(torch.load(args.raft_checkpoint,map_location='cpu',weights_only=True))
        @torch.no_grad()
        def dense_flow(previous,current):
            h,w=current.shape[:2]
            a=torch.from_numpy(previous[:,:,::-1].copy()).permute(2,0,1).cuda().float()/127.5-1
            b=torch.from_numpy(current[:,:,::-1].copy()).permute(2,0,1).cuda().float()/127.5-1
            pad=(0,(-w)%8,0,(-h)%8)
            a=F.pad(a,pad,mode='replicate');b=F.pad(b,pad,mode='replicate')
            # Forward/backward consistency is checked independently of the learned
            # flow confidence. Stereo reprojection thresholds remain unchanged.
            forward=network(a[None],b[None],num_flow_updates=12)[-1][0,:,:h,:w].permute(1,2,0).cpu().numpy()
            backward=network(b[None],a[None],num_flow_updates=12)[-1][0,:,:h,:w].permute(1,2,0).cpu().numpy()
            return forward,backward
    s=read(args.session);bundles=read(root/'manifests/sync-plan.json')['bundles'];cameras={};initial={};gray={};images={};masks={};sizes={};descriptors={};pixels={}
    for entry in s['cameras']:
        cid=entry['id'];data=read(root/entry['calibration']);q=data['params']
        K=np.array([[q[0],0,q[2]],[0,q[1],q[3]],[0,0,1.]])
        c={'K':K,'R':np.array(data['world_to_camera']['R']),'t':np.array(data['world_to_camera']['t'])};c['P']=K@np.c_[c['R'],c['t']];cameras[cid]=c
        image=cv2.imread(str(root/bundles[0]['views'][cid]['image']));source=cv2.imread(str(Path('data/dynamic_yogurt_001/frames')/cid/'frame_000000.png'))
        old=read(args.empty_calibration/f'{cid}.json')['params']
        translation=np.float32([[1,0,q[2]-old[2]],[0,1,q[3]-old[3]]])
        source=cv2.warpAffine(source,translation,(image.shape[1],image.shape[0]))
        factor=min(1.,args.tracking_long_side/max(image.shape[:2]));size=(round(image.shape[1]*factor),round(image.shape[0]*factor))
        image=cv2.resize(image,size,interpolation=cv2.INTER_AREA);source=cv2.resize(source,size,interpolation=cv2.INTER_AREA)
        scale=np.array([image.shape[1]/data['image_size'][0],image.shape[0]/data['image_size'][1]])
        sizes[cid]=(size,scale);images[cid]=image;gray[cid]=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        bounds=np.array([[-.02,-.02,0],[.37,-.02,0],[.37,.23,0],[-.02,.23,0.]])
        polygon=(project(bounds,c)*scale).round().astype(np.int32);region=np.zeros(image.shape[:2],np.uint8);cv2.fillConvexPoly(region,polygon,255)
        delta=image.astype(float)-source.astype(float);bias=np.median(delta[region>0],axis=0)
        diff=(np.max(np.abs(delta-bias),axis=2)>32).astype(np.uint8)*255;diff=cv2.bitwise_and(diff,region)
        diff=cv2.morphologyEx(diff,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
        contours,_=cv2.findContours(diff,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if not contours:raise ValueError(f'No textile candidate mask for {cid}')
        mask=np.zeros_like(region);cv2.drawContours(mask,[max(contours,key=cv2.contourArea)],-1,255,cv2.FILLED)
        mask=cv2.erode(mask,np.ones((11,11),np.uint8));masks[cid]=mask
        # Exclude visible printed markers from the material-feature candidate mask.
        dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
        corners,ids,_=cv2.aruco.ArucoDetector(dictionary).detectMarkers(gray[cid])
        if ids is not None:
            for box in corners:
                polygon=box[0].round().astype(np.int32);cv2.fillConvexPoly(mask,polygon,0)
        detector=cv2.SIFT_create(nfeatures=10000,contrastThreshold=.01,edgeThreshold=15)
        if args.rectified:
            plane=c['K']@np.c_[c['R'][:,0],c['R'][:,1],c['t']-.012*c['R'][:,2]]
            grid=np.array([[2500.,0,100.],[0,2500.,100.],[0,0,1.]])
            transform=grid@np.linalg.inv(plane)@np.diag([1/scale[0],1/scale[1],1.])
            rect=cv2.warpPerspective(gray[cid],transform,(1100,750));rect_mask=cv2.warpPerspective(mask,transform,(1100,750),flags=cv2.INTER_NEAREST)
            rect=cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(rect)
            key,desc=detector.detectAndCompute(rect,rect_mask)
            coords=np.array([k.pt for k in key],dtype=np.float32)
            native=cv2.perspectiveTransform(coords[None],np.linalg.inv(transform))[0]/scale
            cv2.imwrite(str(out/f'{cid}_rectified.jpg'),rect)
        else:
            key,desc=detector.detectAndCompute(gray[cid],mask);native=np.array([k.pt for k in key])/scale
        if desc is None:raise ValueError(f'No textile features in {cid}')
        pixels[cid]=native;descriptors[cid]=desc
        print(cid,'masked SIFT features',len(key),flush=True)
    ref='fuji';uv=pixels[ref];c=cameras[ref]
    H=c['K']@np.c_[c['R'][:,0],c['R'][:,1],c['t']-.012*c['R'][:,2]]
    xy=cv2.perspectiveTransform(uv.astype(np.float32)[None],np.linalg.inv(H))[0]
    estimate=np.c_[xy,np.full(len(xy),-.012)];pairs={}
    for cid in ['dji','iphone']:
        expected=project(estimate,cameras[cid]);tree=cKDTree(pixels[cid]);matches={}
        for index,candidates in enumerate(tree.query_ball_point(expected,65)):
            if len(candidates)<2:continue
            distances=np.linalg.norm(descriptors[cid][candidates]-descriptors[ref][index],axis=1);order=np.argsort(distances)
            if distances[order[0]]<.78*distances[order[1]]:
                other=int(candidates[order[0]]);point,errors,front=triangulate({ref:uv[index],cid:pixels[cid][other]},cameras)
                if front and max(errors.values())<2.5 and -.045<point[2]<-.002 and -.03<point[0]<.38 and -.03<point[1]<.24:
                    matches[index]=other
        # Ambiguous many-to-one assignments are removed, not silently duplicated.
        counts={other:list(matches.values()).count(other) for other in set(matches.values())}
        pairs[cid]={i:j for i,j in matches.items() if counts[j]==1}
        print(cid,'accepted spatial/stereo matches',len(pairs[cid]),flush=True)
    features=[];positions=[]
    candidates=(set(pairs['dji'])|set(pairs['iphone'])) if args.allow_stereo else (set(pairs['dji'])&set(pairs['iphone']))
    for index in sorted(candidates):
        obs={ref:uv[index],**{cid:pixels[cid][pairs[cid][index]] for cid in ['dji','iphone'] if index in pairs[cid]}}
        point,errors,front=triangulate(obs,cameras)
        if front and max(errors.values())<3.5 and -.045<point[2]<-.002:
            features.append(obs);positions.append(point)
    if args.initialization_source:
        reference=read(args.initialization_source)
        if Path(reference['session']).resolve()!=args.session.resolve():raise ValueError('Initialization and tracking session differ')
        features=[{cid:np.array(xy) for cid,xy in obs.items()} for obs in reference['initial_observations']]
        positions=reference['initial_positions_m']
    canvas=Image.new('RGB',(1500,800),'#141c25');draw=ImageDraw.Draw(canvas)
    for column,cid in enumerate(['dji','fuji','iphone']):
        image=images[cid].copy();image[masks[cid]>0]=(image[masks[cid]>0]*.65+[0,70,0]).clip(0,255)
        for obs in features:
            if cid in obs:cv2.circle(image,tuple(np.round(obs[cid]*sizes[cid][1]).astype(int)),5,(0,0,255),-1)
        im=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB));im.thumbnail((490,745));canvas.paste(im,(column*500,35));draw.text((column*500+10,10),cid+' | textile mask + accepted stereo points',fill='white')
    canvas.save(out/'initial_stereo_diagnostic.jpg',quality=94)
    write(out/'initialization.json',{'accepted_points':len(features),'triple_view_points':sum(len(obs)==3 for obs in features),'rectified':args.rectified,
         'session':args.session.as_posix(),'empty_calibration':args.empty_calibration.as_posix(),
         'initialization_source':None if args.initialization_source is None else args.initialization_source.as_posix(),
         'mask':'Static-background difference after known crop shift and visible-marker exclusion; provisional.',
         'initial_positions_m':np.array(positions).tolist(),
         'initial_observations':[{cid:xy.tolist() for cid,xy in obs.items()} for obs in features],'metric_accuracy_verified':False})
    if len(features)<12:
        write(out/'failure.json',{'status':'insufficient_correspondences','triple_view_points':len(features),'minimum':12,
             'reason':'Do not create a non-rigid field from repeated-knit aliases or insufficient stereo support.'})
        raise ValueError(f'Only {len(features)} accepted multi-view initialization points; tracking refused')
    n=len(features)
    length=max(b['views']['fuji']['source_index'] for b in bundles)+1 if args.native_flow else len(bundles)
    flows={cid:np.full((length,n,2),np.nan) for cid in cameras};colors={cid:np.full((length,n,3),np.nan) for cid in cameras}
    for cid in cameras:flows[cid][0]=np.array([obs.get(cid,[np.nan,np.nan]) for obs in features])
    decoders={};error_files={};previous_rgb={cid:images[cid].copy() for cid in cameras}
    if args.native_flow:
        ffmpeg=next(tool['executable_path'] for tool in read('static-tools.json')['portable_tools'] if tool['name']=='FFmpeg')
        for entry in s['cameras']:
            cid=entry['id'];width,height=sizes[cid][0];error_files[cid]=open(out/f'{cid}_decode_errors.txt','wb')
            command=[ffmpeg,'-v','error','-threads','2','-noautorotate','-i',str(root/entry['video']),'-map','0:v:0','-an','-vf',f'scale={width}:{height}:flags=area','-pix_fmt','bgr24','-fps_mode','passthrough','-f','rawvideo','pipe:1']
            decoders[cid]=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=error_files[cid])
    try:
        for frame_index in range(length):
            for cid in cameras:
                active=np.flatnonzero(np.isfinite(flows[cid][max(0,frame_index-1)]).all(axis=1))
                if not len(active):continue
                size,scale=sizes[cid]
                if args.native_flow:
                    raw=decoders[cid].stdout.read(size[0]*size[1]*3)
                    if len(raw)!=size[0]*size[1]*3:raise ValueError(f'{cid}: decoded video ended at frame {frame_index}')
                    images[cid]=np.frombuffer(raw,np.uint8).reshape(size[1],size[0],3)
                elif frame_index:
                    image=cv2.imread(str(root/bundles[frame_index]['views'][cid]['image']));images[cid]=cv2.resize(image,size,interpolation=cv2.INTER_AREA)
                new_gray=cv2.cvtColor(images[cid],cv2.COLOR_BGR2GRAY)
                if frame_index:
                    old=(flows[cid][frame_index-1,active]*scale).astype(np.float32).reshape(-1,1,2)
                    if network is None:
                        new,status,error=cv2.calcOpticalFlowPyrLK(gray[cid],new_gray,old,None,winSize=(31,31),maxLevel=4,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.01))
                        back,bst,_=cv2.calcOpticalFlowPyrLK(new_gray,gray[cid],new,None,winSize=(31,31),maxLevel=4)
                        valid=(status[:,0]>0)&(bst[:,0]>0)&(np.linalg.norm(back[:,0]-old[:,0],axis=1)<.8)&(error[:,0]<30)
                    else:
                        forward,backward=dense_flow(previous_rgb[cid],images[cid])
                        coordinates=old[:,0]
                        delta=cv2.remap(forward,coordinates[:,0,None],coordinates[:,1,None],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)[:,0]
                        new=(coordinates+delta)[:,None]
                        reverse=cv2.remap(backward,new[:,0,0,None],new[:,0,1,None],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)[:,0]
                        valid=np.linalg.norm(delta+reverse,axis=1)<.8
                    xy=new[:,0];valid&=(xy[:,0]>5)&(xy[:,1]>5)&(xy[:,0]<size[0]-5)&(xy[:,1]<size[1]-5)
                    flows[cid][frame_index,active[valid]]=xy[valid]/scale
                gray[cid]=new_gray
                previous_rgb[cid]=images[cid].copy()
                for j in np.flatnonzero(np.isfinite(flows[cid][frame_index]).all(axis=1)):
                    x,y=np.round(flows[cid][frame_index,j]*scale).astype(int);image=images[cid];x=np.clip(x,1,image.shape[1]-2);y=np.clip(y,1,image.shape[0]-2)
                    encoded=np.median(image[y-1:y+2,x-1:x+2,::-1].reshape(-1,3),axis=0)/255.
                    colors[cid][frame_index,j]=np.where(encoded<.081,encoded/4.5,((encoded+.099)/1.099)**(1/.45))
            remaining=sum(np.isfinite(flows[cid][frame_index,:,0]).sum() for cid in cameras)
            if frame_index%25==0:print('tracked frame',frame_index,'remaining views/point',remaining,'backend',args.flow_backend,flush=True)
            if remaining==0:break
    finally:
        for cid,process in decoders.items():
            if process.poll() is None:process.terminate()
            process.wait(timeout=10);process.stdout.close();error_files[cid].close()
    if args.native_flow:
        for cid in cameras:
            selection=[b['views'][cid]['source_index'] for b in bundles]
            flows[cid]=flows[cid][selection];colors[cid]=colors[cid][selection]
    frames=[];counts=[]
    for index,bundle in enumerate(bundles):
        points=[];count=0
        for j in range(n):
            obs={cid:flows[cid][index,j] for cid in cameras if np.isfinite(flows[cid][index,j]).all()};valid=False;point=None
            if len(obs)>=2:
                estimate,errors,front=triangulate(obs,cameras)
                valid=front and max(errors.values())<4 and -.8<estimate[2]<.015 and -.4<estimate[0]<.8 and -.4<estimate[1]<.6
                if valid:point=estimate.tolist();count+=1
            rgb=colors['fuji'][index,j]
            points.append({'id':f'knit_feature_{j:04d}','position':point,'rgb':rgb.tolist() if np.isfinite(rgb).all() else None,
                'status':'tracked' if valid else 'occluded','appearance_camera':'fuji','geometry_source':'Multi-view triangulated material feature; provisional intrinsics'})
        frames.append({'time_s':bundle['time_s'],'points':points});counts.append(count)
    tracks={'schema_version':1,'identity_kind':'assigned_points','color_space':'linear_rgb','reference_frame':0,'metres_per_unit':1.,
            'frames':frames,'metric_accuracy_verified':False,'source':'Actual textile SIFT + '+args.flow_backend+' optical flow + calibrated multi-view triangulation',
            'color_note':'Fixed Fuji camera sampled video appearance, inverse BT.709 transfer; not pigment change.'}
    write(out/'point_tracks.json',tracks);np.savez_compressed(out/'observations.npz',**flows)
    supported=[i for i,count in enumerate(counts) if count>=12]
    summary={'status':'provisional_observed_material_tracks','initial_points':n,'frames':len(frames),'native_flow':args.native_flow,'frames_with_12_points':len(supported),
            'flow_backend':args.flow_backend,'tracking_long_side':args.tracking_long_side,'session':args.session.as_posix(),
            'first_supported_time_s':frames[supported[0]]['time_s'] if supported else None,'last_supported_time_s':frames[supported[-1]]['time_s'] if supported else None,
            'per_frame_supported_points':counts,'metric_accuracy_verified':False,'gaussian_training_complete':False,
            'limitations':['Optical flow can still follow a similar stitch; no independently validated material identity','Hands/folds cause gaps; no bridging/reidentification','Only visible tracked surface is supported']}
    write(out/'summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='per_frame_supported_points'}),flush=True)


if __name__=='__main__':main()
