"""Train one persistent Gaussian actor on supported, real multi-camera poses.

This prototype fits a moving rigid container, not textile strain. Calibration,
silhouette masks and initial container shape are provisional. Native source
pixels are cropped without resizing. The held-out views are times from the
same three cameras, not independent novel-view/metric validation.
"""
import argparse
import json
import math
from pathlib import Path
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation
import torch
from gsplat import rasterization


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def project(points, camera):
    xyz=points@camera['R'].T+camera['t']
    pixels=xyz@camera['K'].T
    return pixels[:,:2]/pixels[:,2:]


def initial_surface(center, radius, height, spacing=.00065):
    # A coarse frustum is an initialization prior, not a measured hidden surface.
    xy=np.arange(-radius,radius+spacing,spacing)
    xx,yy=np.meshgrid(xy,xy);keep=xx**2+yy**2<=radius**2
    top=np.c_[xx[keep]+center[0],yy[keep]+center[1],np.full(keep.sum(),-height)]
    normals=np.tile([0.,0.,-1.],(len(top),1))
    body=[];body_normals=[]
    for z in np.arange(-height+spacing,0.,spacing):
        r=radius*(.72+.28*(-z/height))
        theta=np.arange(0,2*np.pi,spacing/r)
        body.append(np.c_[center[0]+r*np.cos(theta),center[1]+r*np.sin(theta),np.full(len(theta),z)])
        n=np.c_[np.cos(theta),np.sin(theta),np.full(len(theta),radius*.28/height)]
        body_normals.append(n/np.linalg.norm(n,axis=1,keepdims=True))
    points=np.concatenate([top,*body]);normals=np.concatenate([normals,*body_normals])
    z_axis=np.array([0.,0.,1.]);quats=np.c_[1+normals[:,2],np.cross(np.tile(z_axis,(len(normals),1)),normals)]
    opposite=quats[:,0]<1e-6;quats[opposite]=[0.,1.,0.,0.]
    quats/=np.linalg.norm(quats,axis=1,keepdims=True)
    return points.astype(np.float32),normals.astype(np.float32),quats.astype(np.float32)


def quaternion_product(a,b):
    aw,ax,ay,az=a.unbind(-1);bw,bx,by,bz=b.unbind(-1)
    return torch.stack((aw*bw-ax*bx-ay*by-az*bz,aw*bx+ax*bw+ay*bz-az*by,
                        aw*by-ax*bz+ay*bw+az*bx,aw*bz+ax*by-ay*bx+az*bw),dim=-1)


def load_training_data(session_path, poses, output, spacing=.00065, calibration_dir=None):
    root=session_path.parent;session=read_json(session_path);bundles=read_json(root/'manifests/sync-plan.json')['bundles']
    if poses.get('camera_calibrations') and poses['camera_calibrations']!={c['id']:c['calibration'] for c in session['cameras']}:
        raise ValueError('Motion and training camera calibrations differ; refit motion before training')
    if poses.get('canonical_calibration') and Path(poses['canonical_calibration']).resolve()!=calibration_dir.resolve():
        raise ValueError('Motion canonical points and actor initialization use different calibrations')
    cameras={}
    for item in session['cameras']:
        c=read_json(root/item['calibration']);p=c['params']
        cameras[item['id']]={'K':np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]]),
             'R':np.array(c['world_to_camera']['R']),'t':np.array(c['world_to_camera']['t'])}
    calibration=read_json(calibration_dir/'summary.json')
    height=calibration['estimated_lid_height_m']
    centers=[];radii=[]
    reference=120
    baseline={}
    for cid,camera in cameras.items():
        image=cv2.imread(str(root/bundles[reference]['views'][cid]['image']))
        baseline[cid]=image
        hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
        mask=cv2.inRange(hsv,np.array([85,65,35]),np.array([140,255,255]))
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        contour=max(contours,key=cv2.contourArea).reshape(-1,2)
        H=camera['K']@np.c_[camera['R'][:,0],camera['R'][:,1],camera['t']-height*camera['R'][:,2]]
        xy=cv2.perspectiveTransform(contour.astype(np.float32)[None],np.linalg.inv(H))[0]
        fit=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],np.sum(xy**2,axis=1),rcond=None)[0]
        centers.append(fit[:2]);radii.append(math.sqrt(fit[2]+np.sum(fit[:2]**2)))
    center=np.median(centers,axis=0);contour_radius=float(np.median(radii))
    measured_diameter=calibration.get('measured_lid_diameter_mm')
    radius=contour_radius if measured_diameter is None else measured_diameter/2000
    base,normals,quats=initial_surface(center,radius,height,spacing)
    valid=[i for i,p in enumerate(poses['frames']) if p and p['valid']]
    colors=np.zeros((len(base),3));best=np.full(len(base),-np.inf)
    for cid,c in cameras.items():
        pixels=project(base,c);image=baseline[cid]
        direction=(-c['R'].T@c['t'])-base
        direction/=np.linalg.norm(direction,axis=1,keepdims=True)
        score=(direction*normals).sum(axis=1)
        x=np.round(pixels[:,0]).astype(int);y=np.round(pixels[:,1]).astype(int)
        visible=(x>=0)&(y>=0)&(x<image.shape[1])&(y<image.shape[0])&(score>best)
        colors[visible]=image[y[visible],x[visible],::-1]/255.;best[visible]=score[visible]
    records=[];entries=[];diagnostic=[]
    for order,index in enumerate(valid):
        pose=poses['frames'][index];R=Rotation.from_rotvec(pose['rvec']).as_matrix();t=np.array(pose['translation_m'])
        world=base@R.T+t
        for cid,c in cameras.items():
            image=cv2.imread(str(root/bundles[index]['views'][cid]['image']))
            empty=cv2.imread(str(root/bundles[0]['views'][cid]['image']))
            xy=project(world,c)
            x0,y0=np.maximum(0,np.floor(xy.min(axis=0)-28)).astype(int)
            x1,y1=np.minimum([image.shape[1],image.shape[0]],np.ceil(xy.max(axis=0)+28)).astype(int)
            if x1-x0<64 or y1-y0<64:continue
            target=image[y0:y1,x0:x1,::-1].copy()/255.
            background=empty[y0:y1,x0:x1,::-1].copy()/255.
            prior=np.zeros((y1-y0,x1-x0),np.uint8)
            hull=cv2.convexHull((xy-[x0,y0]).astype(np.float32)).round().astype(np.int32)
            cv2.fillConvexPoly(prior,hull,255)
            allowed=cv2.dilate(prior,np.ones((15,15),np.uint8))
            difference=(np.max(np.abs(target-background),axis=2)>.055).astype(np.uint8)*255
            difference=cv2.bitwise_and(difference,allowed)
            difference=cv2.morphologyEx(difference,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
            contours,_=cv2.findContours(difference,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            mask=np.zeros_like(prior)
            if contours:cv2.drawContours(mask,[max(contours,key=cv2.contourArea)],-1,255,cv2.FILLED)
            mask_fraction=float(np.mean(mask>0))
            if mask_fraction<.04 or mask_fraction>.85:continue
            cropK=c['K'].copy();cropK[0,2]-=x0;cropK[1,2]-=y0
            view=np.eye(4);view[:3,:3]=c['R'];view[:3,3]=c['t']
            quat=Rotation.from_matrix(R).as_quat()[[3,0,1,2]]
            record={'target':torch.tensor(target,dtype=torch.float32),
                 'background':torch.tensor(background,dtype=torch.float32),
                 'mask':torch.tensor(mask/255.,dtype=torch.float32),
                 'K':torch.tensor(cropK,dtype=torch.float32,device='cuda')[None],
                 'view':torch.tensor(view,dtype=torch.float32,device='cuda')[None],
                 'R':torch.tensor(R,dtype=torch.float32,device='cuda'),
                 't':torch.tensor(t,dtype=torch.float32,device='cuda'),
                 'quat':torch.tensor(quat,dtype=torch.float32,device='cuda'),
                 'width':int(x1-x0),'height':int(y1-y0),'camera':cid,'index':index,'time_s':bundles[index]['time_s'],
                 'heldout':order%7==0,'crop':[int(x0),int(y0),int(x1),int(y1)]}
            records.append(record)
            entries.append({k:record[k] for k in ['camera','index','time_s','heldout','crop','width','height']})
            if index==reference:
                overlay=(target*255).astype(np.uint8);overlay[mask>0]=(overlay[mask>0]*.6+[0,100,0]).clip(0,255)
                diagnostic.append((cid,Image.fromarray(overlay)))
    canvas=Image.new('RGB',(1500,600),'#151c25');draw=ImageDraw.Draw(canvas)
    for column,(cid,image) in enumerate(diagnostic):
        image.thumbnail((480,540));canvas.paste(image,(column*500,35));draw.text((column*500+10,10),cid+' | provisional foreground mask',fill='white')
    canvas.save(output/'mask_diagnostic.jpg',quality=94)
    write_json(output/'training_views.json',entries)
    initialization={'center_xy_m':center.tolist(),'radius_m':radius,'lid_height_m':height,'gaussians':len(base),
           'calibration':calibration_dir.as_posix(),'lid_height_source':calibration.get('lid_height_source','fitted'),
           'radius_source':'projected rim contour' if measured_diameter is None else 'user measured lid diameter',
           'contour_radius_m':contour_radius,
           'shape_prior':'Frustum initialized from projected lid contour; bottom radius 72% of lid radius is an unmeasured prior.',
           'mask_method':'Native empty-frame difference, morphological fill, bounded by provisional projected object hull. Shadows/rope can remain.',
           'native_pixels':True,'cropped_not_resized':True,'views':len(records),'heldout_views':sum(r['heldout'] for r in records)}
    write_json(output/'initialization.json',initialization)
    print(json.dumps(initialization),flush=True)
    return base,quats,colors,records,valid


def save_ply(path,model):
    arrays=[model['means'],model['colors'],model['opacity'][:,None],model['scales'],model['quats']]
    arrays=[x.detach().cpu().numpy() for x in arrays]
    xyz,rgb,opacity,scales,quats=arrays
    # Standard 3DGS PLY expects SH DC, opacity logits, log scales and wxyz quats.
    dc=(rgb-.5)/.28209479177387814
    values=np.c_[xyz,np.zeros_like(xyz),dc,np.log(np.clip(opacity,1e-6,1-1e-6)/(1-np.clip(opacity,1e-6,1-1e-6))),np.log(scales),quats].astype('<f4')
    properties=['x','y','z','nx','ny','nz','f_dc_0','f_dc_1','f_dc_2','opacity','scale_0','scale_1','scale_2','rot_0','rot_1','rot_2','rot_3']
    header='ply\nformat binary_little_endian 1.0\nelement vertex '+str(len(xyz))+'\n'+''.join('property float '+key+'\n' for key in properties)+'end_header\n'
    with open(path,'wb') as stream:stream.write(header.encode('ascii'));stream.write(values.tobytes())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',type=Path,default=Path('data/dynamic_yogurt_001/session.json'))
    p.add_argument('--poses',type=Path,default=Path('outputs/dynamic_yogurt_001/rigid_tracking_01/rigid_poses.json'))
    p.add_argument('--calibration-dir',type=Path,help='Joint calibration used by the motion/cameras; defaults to the original fit')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--steps',type=int,default=3000)
    p.add_argument('--spacing-mm',type=float,default=.65)
    p.add_argument('--shape-offset-mm',type=float,default=6)
    p.add_argument('--max-scale-mm',type=float,default=1.4)
    p.add_argument('--silhouette-weight',type=float,default=.035,help='Opacity/silhouette loss weight; higher values discourage transparency holes')
    args=p.parse_args();out=args.output
    calibration_dir=args.calibration_dir or args.session.parent/'calibration/board_lid_refinement_01'
    if out.exists():raise ValueError('Output exists; preserve completed and failed runs under separate names')
    out.mkdir(parents=True);torch.manual_seed(42);rng=np.random.default_rng(42);cv2.setNumThreads(2);torch.set_num_threads(4)
    if not .2<=args.spacing_mm<=2 or not 0<args.shape_offset_mm<=12 or not .1<=args.max_scale_mm<=4 or not 0<args.silhouette_weight<=1 or args.steps<1:
        raise ValueError('Invalid training budget or surface limits')
    write_json(out/'training_config.json',{'steps':args.steps,'spacing_mm':args.spacing_mm,'shape_offset_mm':args.shape_offset_mm,
        'maximum_scale_mm':args.max_scale_mm,'surface_quaternions_fixed':True,'seed':42,'session':args.session.as_posix(),'poses':args.poses.as_posix(),
        'canonical_calibration':calibration_dir.as_posix(),'silhouette_weight':args.silhouette_weight})
    base,quats,colors,records,valid=load_training_data(args.session,read_json(args.poses),out,args.spacing_mm/1000,calibration_dir)
    if not records or not any(r['heldout'] for r in records):raise ValueError('No supported training/held-out views')
    device='cuda';anchor=torch.tensor(base,device=device);offset=torch.nn.Parameter(torch.zeros_like(anchor))
    q=torch.tensor(quats,device=device);log_scales=torch.nn.Parameter(torch.log(torch.tensor([.00048,.00048,.00012],device=device).expand(len(base),3).clone()))
    logits=torch.nn.Parameter(torch.full((len(base),),1.4,device=device));color_logits=torch.nn.Parameter(torch.logit(torch.tensor(colors,dtype=torch.float32,device=device).clamp(.01,.99)))
    optimizer=torch.optim.Adam([{'params':[offset],'lr':.008},
              {'params':[log_scales],'lr':.005},{'params':[logits],'lr':.015},{'params':[color_logits],'lr':.025}])
    def model():
        return {'means':anchor+(args.shape_offset_mm/1000)*torch.tanh(offset),'quats':q,
                'scales':torch.exp(log_scales).clamp(.00005,args.max_scale_mm/1000),'opacity':logits.sigmoid(),'colors':color_logits.sigmoid()}
    def render(m,r):
        means=m['means']@r['R'].T+r['t'];world_quats=quaternion_product(r['quat'].expand(len(base),4),m['quats'])
        rgb,alpha,_=rasterization(means,world_quats,m['scales'],m['opacity'],m['colors'],r['view'],r['K'],r['width'],r['height'],
                            packed=False,near_plane=.01,far_plane=10,rasterize_mode='antialiased')
        return rgb[0],alpha[0,:,:,0]
    train=[r for r in records if not r['heldout']];held=[r for r in records if r['heldout']]
    history=[];best=math.inf;best_state=None;start=time.perf_counter()
    @torch.no_grad()
    def evaluate(step,save_images=False):
        m=model();metrics=[];alpha_errors=[];rows=[]
        selected=held
        panel_indices={min((i for i,r in enumerate(held) if r['camera']==cid),key=lambda i:abs(held[i]['time_s']-12.012)) for cid in ['dji','fuji','iphone']}
        for view_index,r in enumerate(selected):
            rgb,alpha=render(m,r);target=r['target'].to(device);background=r['background'].to(device);mask=r['mask'].to(device)
            composite=rgb+(1-alpha[:,:,None])*background
            error=((composite-target).square().sum(-1)*mask).sum()/(3*mask.sum().clamp_min(1))
            metrics.append(float(error))
            alpha_errors.append(float((alpha-mask).abs().mean()))
            if save_images and view_index in panel_indices:
                panels=[(target.cpu().numpy()*255).astype(np.uint8),(composite.clamp(0,1).cpu().numpy()*255).astype(np.uint8),
                        (alpha[:,:,None].expand(-1,-1,3).cpu().numpy()*255).astype(np.uint8)]
                row=Image.new('RGB',(1500,450),'#151c25');draw=ImageDraw.Draw(row)
                for column,values in enumerate(panels):
                    image=Image.fromarray(values);image.thumbnail((480,405));row.paste(image,(column*500,35))
                    draw.text((column*500+8,8),r['camera']+f' | t={r["time_s"]:.3f}s | '+['source crop','Gaussian + empty background','Gaussian alpha'][column],fill='white')
                rows.append(row)
        result={'step':step,'heldout_foreground_psnr_db':-10*math.log10(max(float(np.mean(metrics)),1e-12)),
                'heldout_foreground_mse':float(np.mean(metrics)),'heldout_alpha_mae':float(np.mean(alpha_errors)),
                'elapsed_s':time.perf_counter()-start}
        if save_images:
            sheet=Image.new('RGB',(1500,450*len(rows)))
            for i,row in enumerate(rows):sheet.paste(row,(0,i*450))
            sheet.save(out/'heldout_comparison.jpg',quality=94)
        return result
    initial=evaluate(0);history.append(initial);print(json.dumps(initial),flush=True)
    try:
        for step in range(1,args.steps+1):
            r=train[int(rng.integers(len(train)))];optimizer.zero_grad(set_to_none=True)
            m=model();rgb,alpha=render(m,r);target=r['target'].to(device);background=r['background'].to(device);mask=r['mask'].to(device)
            composite=rgb+(1-alpha[:,:,None])*background
            weights=.15+mask
            photo=((composite-target).abs().mean(-1)*weights).mean()
            silhouette=(alpha-mask).abs().mean()
            regularizer=.004*(torch.tanh(offset).square().mean())+.0003*(m['scales'][:,:2]/.001).square().mean()
            loss=photo+args.silhouette_weight*silhouette+regularizer
            if not torch.isfinite(loss):raise ValueError('Non-finite training objective')
            loss.backward();torch.nn.utils.clip_grad_norm_([offset,log_scales,logits,color_logits],10.);optimizer.step()
            if step%100==0:print(json.dumps({'step':step,'loss':float(loss),'seconds':round(time.perf_counter()-start,2)}),flush=True)
            if step%500==0 or step==args.steps:
                result=evaluate(step);history.append(result);print(json.dumps(result),flush=True)
                if result['heldout_foreground_mse']<best:
                    best=result['heldout_foreground_mse'];best_state={key:value.detach().clone() for key,value in model().items()}
                    torch.save({'model':{k:v.cpu() for k,v in best_state.items()},'step':step,'metric':result},out/'best_model.pt')
                write_json(out/'history.json',history)
        # Restore best held-out checkpoint for exports, rather than the final step.
        checkpoint=torch.load(out/'best_model.pt',map_location=device,weights_only=True)
        m=checkpoint['model'];save_ply(out/'canonical_actor.ply',m)
        np.savez_compressed(out/'canonical_actor.npz',**{k:v.cpu().numpy() for k,v in m.items()})
        # Diagnostic comparison must use exported best model.
        def best_model():return m
        model=best_model
        final=evaluate(checkpoint['step'],save_images=True)
        video_dir=out/'renders';video_dir.mkdir()
        reference_pose=read_json(args.poses)['frames'][valid[0]]
        reference_R=torch.tensor(Rotation.from_rotvec(reference_pose['rvec']).as_matrix(),dtype=torch.float32,device=device)
        reference_t=torch.tensor(reference_pose['translation_m'],dtype=torch.float32,device=device)
        reference_world=m['means']@reference_R.T+reference_t
        displacement=[]
        with torch.no_grad():
            for number,index in enumerate(valid):
                r=next((r for r in records if r['index']==index and r['camera']=='iphone'),None)
                if r is None:continue
                rgb,alpha=render(m,r);actor=(rgb+(1-alpha[:,:,None])*.9).clamp(0,1)
                world=m['means']@r['R'].T+r['t'];d=torch.linalg.norm(world-reference_world,dim=-1)
                displacement.append({'index':index,'time_s':r['time_s'],'mean_displacement_m':float(d.mean()),'max_displacement_m':float(d.max())})
                values=(actor.cpu().numpy()*255).astype(np.uint8)
                panel=Image.new('RGB',(800,600),'#e6e6e6');image=Image.fromarray(values);image.thumbnail((760,535));panel.paste(image,((800-image.width)//2,45))
                ImageDraw.Draw(panel).text((15,15),f'TF4DGS rigid Gaussian pilot | t={r["time_s"]:.3f}s | provisional calibration',fill='black')
                panel.save(video_dir/f'frame_{number:06d}.png')
        write_json(out/'all_gaussian_motion_summary.json',displacement)
        write_json(out/'motion.json',{'canonical_actor':'canonical_actor.npz','persistent_ids':list(range(len(base))),
                    'poses':str(args.poses),'valid_indices':valid,'interpolate_missing':False,'motion':'rigid translation + rotation',
                    'motion_assumption':read_json(args.poses).get('motion_assumption','Unconstrained rigid rotation and translation'),
                    'canonical_calibration':calibration_dir.as_posix(),
                    'appearance_model':'One time-constant RGB per Gaussian; observed point appearance available separately.',
                    'metric_accuracy_verified':False})
        summary={'status':'trained_provisional_rigid_pilot','steps':args.steps,'best_step':checkpoint['step'],'gaussians':len(base),
                  'canonical_calibration':calibration_dir.as_posix(),'poses':args.poses.as_posix(),
                  'supported_pose_frames':len(valid),'training_views':len(train),'heldout_views':len(held),
                  'initial_heldout_foreground_psnr_db':initial['heldout_foreground_psnr_db'],
                  'best_heldout_foreground_psnr_db':final['heldout_foreground_psnr_db'],
                  'heldout_alpha_mae':final['heldout_alpha_mae'],
                  'elapsed_s':time.perf_counter()-start,'peak_cuda_bytes':torch.cuda.max_memory_allocated(),
                  'metric_accuracy_verified':False,'time_varying_appearance_trained':False,'nonrigid_deformation_trained':False,
                  'limitations':['Provisional calibration and manually synchronized video','Automatic masks can include shadows/rope',
                                 'Unseen container geometry follows initialization prior','Validation uses the same three cameras at held-out times']}
        write_json(out/'summary.json',summary);print(json.dumps(summary,indent=2),flush=True)
    except Exception as error:
        write_json(out/'failure.json',{'error_type':type(error).__name__,'message':str(error),'history':history})
        raise


if __name__=='__main__':main()
