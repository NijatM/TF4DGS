"""Initialize a static Gaussian layer using only the selected dynamic capture.

Empty native frames provide appearance. The measured board fixes its plane;
Depth Anything V2 Small provides an explicitly provisional off-plane prior.
No previous scene, image billboard or synthetic room is imported. The default
table masks are specific to dynamic_yogurt_001 and require review for new data.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import torch


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,obj):Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def camera(data):
    p=data['params'];R=np.array(data['world_to_camera']['R']);t=np.array(data['world_to_camera']['t'])
    return {'K':np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]]),'R':R,'t':t,'C':-R.T@t}


def plane_intersections(c,height,width):
    yy,xx=np.mgrid[:height,:width]
    rays=np.stack(((xx-c['K'][0,2])/c['K'][0,0],(yy-c['K'][1,2])/c['K'][1,1],np.ones_like(xx)),axis=-1)@c['R']
    depth=-c['C'][2]/np.where(np.abs(rays[:,:,2])>1e-8,rays[:,:,2],np.nan)
    return c['C']+depth[:,:,None]*rays,depth,rays


def reviewed_table_region(cid,h,w):
    # Hand-reviewed conservative tabletop polygons. Raised objects are excluded
    # separately by depth, color and the border regions below.
    polygons={
      'fuji':[(0,.11),(.14,0),(.99,.02),(1,1),(0,1)],
      'iphone':[(0,.46),(.84,.44),(1,.70),(1,1),(0,1)],
      'dji':[(0,.27),(.45,.25),(.78,.30),(1,.40),(1,1),(0,1)]}
    m=np.zeros((h,w),np.uint8);cv2.fillPoly(m,[np.round(np.array(polygons[cid])*[w,h]).astype(np.int32)],255)
    return m>0


def align_depth(predicted,truth,board):
    y,x=np.where(board);sample=np.arange(len(x))[::23];x=x[sample];y=y[sample]
    p=predicted[y,x].astype(float);t=truth[y,x];valid=np.isfinite(p)&np.isfinite(t)&(p>.05)&(t>.05)
    p=p[valid];t=t[valid];held=np.arange(len(p))%5==0
    scale=float(np.median(t[~held]/p[~held]));scaled=predicted*scale
    scale_error=float(np.median(np.abs(p[held]*scale-t[held])))
    fit=least_squares(lambda ab:ab[0]/p[~held]+ab[1]-1/t[~held],[1/scale,0],bounds=([.001,-10],[100,10]),loss='soft_l1',f_scale=.01)
    denominator=fit.x[0]/np.maximum(predicted,.01)+fit.x[1]
    candidate=1/np.maximum(denominator,.0001)
    affine_error=float(np.median(np.abs(1/(fit.x[0]/p[held]+fit.x[1])-t[held])))
    usable=affine_error<.75*scale_error and float(np.mean(denominator<=0))<.001 and np.percentile(candidate,99)<6
    return (candidate if usable else scaled).astype(np.float32),{
      'method':'affine_inverse_depth' if usable else 'multiplicative_depth',
      'scale':scale,'inverse_affine':fit.x.tolist(),'board_holdout_scale_median_abs_m':scale_error,
      'board_holdout_affine_median_abs_m':affine_error,'metric_accuracy_verified':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',type=Path,default=Path('data/dynamic_yogurt_001/session_measured_candidate.json'))
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--depth-code',type=Path,default=Path('.local/tools/Depth-Anything-V2'))
    p.add_argument('--checkpoint',type=Path,default=Path('.local/tools/Depth-Anything-V2/checkpoints/depth_anything_v2_metric_hypersim_vits.pth'))
    p.add_argument('--empty-frames',type=int,default=1,help='Frame zero is clean; later startup frames include the cue hand')
    p.add_argument('--pixel-stride',type=int,default=4,help='Native pixel spacing for off-table seeds')
    p.add_argument('--reference-camera',default='iphone',choices=['iphone'],help='Resolve unverified overlapping depth priors in favor of this view')
    args=p.parse_args();root=args.session.parent;out=args.output
    if not 1<=args.empty_frames<=8:raise ValueError('Invalid empty-frame interval')
    if not 2<=args.pixel_stride<=8:raise ValueError('Invalid native seed stride')
    if out.exists():raise ValueError('Preserve previous background attempts; choose a new output')
    if root.name!='dynamic_yogurt_001':raise ValueError('Review tabletop masks and empty interval before using another session')
    out.mkdir(parents=True);cv2.setNumThreads(3);torch.set_num_threads(4)
    recipe=read('configs/current_background_sources.json')
    revision=subprocess.check_output(['git','-C',str(args.depth_code),'rev-parse','HEAD'],text=True).strip()
    if revision!=recipe['depth_code_commit']:raise ValueError('Depth initializer source revision differs from pinned recipe')
    if hashlib.sha256(args.checkpoint.read_bytes()).hexdigest()!=recipe['depth_model_sha256']:raise ValueError('Depth checkpoint hash mismatch')
    sys.path.insert(0,str((args.depth_code/'metric_depth').resolve()))
    from depth_anything_v2.dpt import DepthAnythingV2
    net=DepthAnythingV2(encoder='vits',features=64,out_channels=[48,96,192,384],max_depth=20)
    net.load_state_dict(torch.load(args.checkpoint,map_location='cpu',weights_only=True));net=net.cuda().eval()
    bundles=read(root/'manifests/sync-plan.json')['bundles'];session=read(args.session)
    cameras={};records={};diagnostic=Image.new('RGB',(1500,1100),'#17212b');draw=ImageDraw.Draw(diagnostic)
    arrays=[];audit={};gain_anchor=None
    for col,cid in enumerate(['iphone','fuji','dji']):
        entry=next(e for e in session['cameras'] if e['id']==cid);c=camera(read(root/entry['calibration']));cameras[cid]=c
        images=[cv2.imread(str(root/bundles[i]['views'][cid]['image']))[:,:,::-1] for i in range(args.empty_frames)]
        source=np.median(np.stack(images),axis=0).astype(np.uint8);h,w=source.shape[:2]
        variation=np.max(np.std(np.stack(images).astype(np.float32),axis=0),axis=-1)
        stable=cv2.erode((variation<8).astype(np.uint8),np.ones((5,5),np.uint8))>0
        Image.fromarray(source).save(out/f'{cid}_empty.png')
        predicted=net.infer_image(source[:,:,::-1].copy(),input_size=518);np.save(out/f'{cid}_depth_raw.npy',predicted)
        plane,plane_depth,rays=plane_intersections(c,h,w)
        board=(plane[:,:,0]>=0)&(plane[:,:,0]<=.35)&(plane[:,:,1]>=0)&(plane[:,:,1]<=.21)&(plane_depth>.05)
        depth,depth_audit=align_depth(predicted,plane_depth,board&stable)
        # Always preserve the measured plane, including marker pixels. Conservative
        # reviewed table areas extend this plane beyond the printed sheet.
        table=reviewed_table_region(cid,h,w)|board
        neutral=(source.max(-1).astype(float)-source.min(-1))<42
        near_plane=np.isfinite(plane_depth)&(plane_depth>.05)&(np.abs(depth-plane_depth)<.018)&neutral&(source.min(-1)>85)
        table|=near_plane
        depth[table]=plane_depth[table]
        validity=stable&np.isfinite(depth)&(depth>.08)&(depth<4)
        np.save(out/f'{cid}_depth.npy',depth);Image.fromarray((table*255).astype(np.uint8)).save(out/f'{cid}_table_mask.png')
        Image.fromarray((validity*255).astype(np.uint8)).save(out/f'{cid}_valid_mask.png')
        white=source[board&stable].astype(float)/255.;white=white[np.min(white,axis=1)>.50]
        white_level=np.median(white,axis=0)
        if gain_anchor is None:gain_anchor=white_level
        gain=np.clip(gain_anchor/white_level,.5,2.)
        target=np.clip(source.astype(np.float32)/255.*gain,0,1)
        records[cid]={'source':source,'target':target,'plane':plane,'depth':depth,'table':table,'valid':validity,'gain':gain,'shape':[w,h]}
        stride=args.pixel_stride
        yy,xx=np.mgrid[2:h-2:stride,2:w-2:stride];keep=(~table[yy,xx])&validity[yy,xx]
        points=c['C']+depth[yy,xx,None]*rays[yy,xx]
        points=points[keep];colors=target[yy,xx][keep]
        footprint=depth[yy,xx][keep]/c['K'][0,0]*stride*.70
        rejected_overlap=0
        if cid!=args.reference_camera:
            ref=cameras[args.reference_camera];pr=points@ref['R'].T+ref['t'];uv=pr@ref['K'].T;uv=uv[:,:2]/pr[:,2:]
            rw,rh=records[args.reference_camera]['shape']
            overlaps=(pr[:,2]>.05)&np.isfinite(uv).all(1)&(uv[:,0]>=0)&(uv[:,0]<rw)&(uv[:,1]>=0)&(uv[:,1]<rh)
            rejected_overlap=int(overlaps.sum());points=points[~overlaps];colors=colors[~overlaps];footprint=footprint[~overlaps]
        q=Rotation.from_matrix(c['R'].T).as_quat()[[3,0,1,2]]
        scales=np.c_[footprint,footprint,footprint*.18]
        arrays.append({'means':points,'colors':colors,'quats':np.tile(q,(len(points),1)),'scales':scales,'plane':np.zeros(len(points),bool)})
        audit[cid]={'camera_file':(root/entry['calibration']).as_posix(),'empty_frame_indices':list(range(args.empty_frames)),
          'native_size':[w,h],'depth_alignment':depth_audit,'off_plane_seeds':len(points),'rejected_unverified_depth_overlap':rejected_overlap,
          'stable_fraction':float(stable.mean()),'rgb_gain_to_iphone':gain.tolist()}
        colored=cv2.applyColorMap((np.clip(depth/2,0,1)*255).astype(np.uint8),cv2.COLORMAP_TURBO)[:,:,::-1]
        overlay=source.copy();overlay[table]=(overlay[table]*.60+[0,95,0]).clip(0,255)
        for row,img in enumerate([source,colored,overlay]):
            thumb=ImageOps.contain(Image.fromarray(img),(490,310));diagnostic.paste(thumb,(col*500+(500-thumb.width)//2,40+row*350))
        draw.text((col*500+8,10),cid+' | empty RGB / depth prior / plane mask',fill='white')
        print(json.dumps({'camera':cid,**audit[cid]}),flush=True)
    del net;torch.cuda.empty_cache()
    # One common plane grid prevents three overlapping copies of marker geometry.
    fine=.00065;coarse=.0025
    xyfine=np.array(np.meshgrid(np.arange(-.01,.361,fine),np.arange(-.01,.221,fine))).reshape(2,-1).T
    xycoarse=np.array(np.meshgrid(np.arange(-.80,1.101,coarse),np.arange(-.70,.901,coarse))).reshape(2,-1).T
    outside=~((xycoarse[:,0]>=-.01)&(xycoarse[:,0]<=.361)&(xycoarse[:,1]>=-.01)&(xycoarse[:,1]<=.221))
    xy=np.concatenate([xyfine,xycoarse[outside]]);spacing=np.r_[np.full(len(xyfine),fine),np.full(outside.sum(),coarse)]
    points=np.c_[xy,np.zeros(len(xy))];colors=np.zeros_like(points);best=np.zeros(len(points));seen=np.zeros(len(points),bool)
    for cid,c in cameras.items():
        camera_points=points@c['R'].T+c['t'];pixels=camera_points@c['K'].T;pixels=pixels[:,:2]/pixels[:,2:]
        pixels=np.nan_to_num(pixels,nan=-1e5,posinf=-1e5,neginf=-1e5)
        x=np.round(np.clip(pixels[:,0],-1e6,1e6)).astype(int);y=np.round(np.clip(pixels[:,1],-1e6,1e6)).astype(int);w,h=records[cid]['shape']
        valid=(x>=2)&(x<w-2)&(y>=2)&(y<h-2)&(camera_points[:,2]>.05)
        ids=np.flatnonzero(valid);valid[ids]&=records[cid]['table'][y[ids],x[ids]]&records[cid]['valid'][y[ids],x[ids]]
        score=c['K'][0,0]/np.maximum(camera_points[:,2],.01)
        chosen=valid&(score>best);colors[chosen]=records[cid]['target'][y[chosen],x[chosen]];best[chosen]=score[chosen];seen|=valid
    points=points[seen];colors=colors[seen];spacing=spacing[seen]
    arrays.insert(0,{'means':points,'colors':colors,'quats':np.tile([1.,0,0,0],(len(points),1)),
        'scales':np.c_[spacing*.65,spacing*.65,spacing*.07],'plane':np.ones(len(points),bool)})
    model={k:np.concatenate([a[k] for a in arrays]).astype(np.float32) for k in ['means','colors','quats','scales']}
    flags=np.concatenate([a['plane'] for a in arrays]);model['opacity']=np.full(len(flags),.97,np.float32)
    np.savez_compressed(out/'initial_background.npz',**model);np.save(out/'plane_flags.npy',flags)
    diagnostic.save(out/'initialization_diagnostic.jpg',quality=94)
    summary={'session':args.session.as_posix(),'source_root':root.as_posix(),'source_policy':'current capture only',
      'calibration_dir':'data/dynamic_yogurt_001/calibration/board_lid_refinement_02_measured',
      'gaussians':len(flags),'plane_gaussians':int(flags.sum()),'cameras':audit,
      'board_dimensions_m':[.350,.210],'fine_spacing_m':fine,'coarse_spacing_m':coarse,
      'off_plane_native_stride':args.pixel_stride,'depth_overlap_reference':args.reference_camera,
      'static_layer':True,'metric_accuracy_verified':False,
      'assumptions':['Flat tabletop extends the measured board plane within reviewed polygons',
      'Off-table surface depth is a monocular prior; unseen backsides are not reconstructed',
      'Only a reviewed empty interval is used; additional frames are not new geometric viewpoints',
      'Unverified overlapping monocular surfaces are removed in favor of the widest reference camera'],
      'depth_tool':recipe}
    write(out/'initialization.json',summary);print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
