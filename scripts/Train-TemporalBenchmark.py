"""Matched local pilots using the pinned official model classes and CUDA renderers.

This adapter preserves heterogeneous calibrated cameras and avoids upstream
square-image loaders. It is a short controlled experiment, not a paper repro.
"""
import argparse, copy, hashlib, json, math, random, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image, ImageDraw
import torch
ROOT=Path(__file__).resolve().parents[1]

def camera(cal,timestamp):
    w,h=cal['width'],cal['height'];fx,fy,cx,cy=(cal[k] for k in ['fx','fy','cx','cy'])
    view=torch.eye(4,device='cuda');view[:3,:3]=torch.tensor(cal['R'],device='cuda');view[:3,3]=torch.tensor(cal['t'],device='cuda')
    near,far=.01,100.;proj=torch.zeros((4,4),device='cuda')
    proj[0,0]=2*fx/w;proj[1,1]=2*fy/h
    proj[0,2]=(2*cx+1)/w-1;proj[1,2]=(2*cy+1)/h-1
    proj[2,2]=far/(far-near);proj[2,3]=-far*near/(far-near);proj[3,2]=1
    vt=view.T.contiguous();pt=proj.T.contiguous()
    return SimpleNamespace(image_width=w,image_height=h,FoVx=2*math.atan(w/(2*fx)),FoVy=2*math.atan(h/(2*fy)),world_view_transform=vt,full_proj_transform=(vt@pt).contiguous(),projection_matrix=pt,camera_center=torch.linalg.inv(vt)[3,:3],time=float(timestamp),timestamp=float(timestamp),mask=None)

def validate_projection(cal,cam,xyz):
    q=xyz@np.array(cal['R']).T+cal['t'];expected=q[:,:2]/q[:,2:]*[cal['fx'],cal['fy']]+[cal['cx'],cal['cy']]
    homogeneous=torch.tensor(np.c_[xyz,np.ones(len(xyz))],dtype=torch.float32,device='cuda')@cam.full_proj_transform
    ndc=(homogeneous[:,:2]/homogeneous[:,3:]).cpu().numpy();actual=((ndc+1)*[cal['width'],cal['height']]-1)/2
    error=float(np.max(np.abs(actual-expected)))
    if error>.03:raise ValueError(f'Calibrated renderer projection failed: {error} px')
    return error

def dump(path,value):
    # Browser reads and antivirus can briefly prevent replacement on Windows.
    # Unique temporary files also prevent concurrent status writers colliding.
    import uuid
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
    try:
        for attempt in range(12):
            try:
                temp.replace(path)
                return
            except PermissionError:
                if attempt == 11: raise
                time.sleep(min(.025 * 2**attempt,.5))
    finally:
        temp.unlink(missing_ok=True)

def save_img(tensor,path):
    array=(tensor.detach().clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype('uint8');Image.fromarray(array).save(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--method',choices=['4dgaussians','4c4d'],required=True);p.add_argument('--dataset',choices=['textile','yogurt'],required=True);p.add_argument('--updates',type=int,default=6000);p.add_argument('--coarse',type=int,default=1000);p.add_argument('--attempt',default='pilot_01');p.add_argument('--resume',action='store_true');p.add_argument('--render-only',action='store_true');p.add_argument('--make-videos',action='store_true');a=p.parse_args()
    cfg=json.loads((ROOT/'configs/temporal_benchmark_001.json').read_text());data=ROOT/'data/temporal_benchmark_001'/a.dataset
    manifest=json.loads((data/'manifest.json').read_text());repo=ROOT/'.local/research'/('4DGaussians' if a.method=='4dgaussians' else '4C4D')
    sys.path.insert(0,str(repo))
    from arguments import OptimizationParams,PipelineParams
    from scene.gaussian_model import GaussianModel
    from gaussian_renderer import render
    from utils.loss_utils import ssim
    parser=argparse.ArgumentParser();opt_group=OptimizationParams(parser);pipe_group=PipelineParams(parser)
    hidden=None
    if a.method=='4dgaussians':
        from arguments import ModelHiddenParams
        hidden_group=ModelHiddenParams(parser)
    parsed=parser.parse_args([]);opt=opt_group.extract(parsed);pipe=pipe_group.extract(parsed)
    opt.iterations=a.updates;opt.position_lr_max_steps=a.updates;opt.lambda_dssim=.2
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);random.seed(cfg['seed'])
    initial=np.load(data/'initial_points.npz');points=initial['points'];colors=initial['colors'];extent=2.5
    pcd=SimpleNamespace(points=points,colors=colors,normals=np.zeros_like(points),time=None)
    if a.method=='4dgaussians':
        hidden=hidden_group.extract(parsed);hidden.no_dshs=False;hidden.no_do=False
        hidden.multires=[1,2,4];hidden.kplanes_config={**hidden.kplanes_config,'resolution':[32,32,32,45]}
        model=GaussianModel(3,hidden);model.create_from_pcd(pcd,extent,90)
        norm=cfg['normalization'];lo=(np.array(cfg['world_roi_m']['min'])-norm['center_m'])*norm['scale_per_m'];hi=(np.array(cfg['world_roi_m']['max'])-norm['center_m'])*norm['scale_per_m']
        model._deformation.deformation_net.set_aabb(hi.tolist(),lo.tolist())
        model._deformation.to('cuda')
        opt.coarse_iterations=a.coarse
    else:
        from module import Coefficient
        coefficient=Coefficient().cuda()
        model=GaussianModel(3,gaussian_dim=4,time_duration=[0.,1.],rot_4d=True,force_sh_3d=False,sh_degree_t=2,coefficient=coefficient)
        model.create_from_pcd(pcd,extent,redundant_ratio=0.)
    model.training_setup(opt)
    render_args=SimpleNamespace(opacity_decay=True,decay_from_iter=500,time_aware=True,f_min=.996,f_max=.998)
    output=ROOT/'outputs/temporal_benchmark_001'/a.method/a.dataset/a.attempt;output.mkdir(parents=True,exist_ok=True)
    docs=ROOT/'documentation/temporal_benchmark_001';tag=f'{a.method}_{a.dataset}_{a.attempt}'
    background=torch.tensor(cfg['photometric_loss']['background_rgb'],device='cuda');cameras={cid:camera(cal,0) for cid,cal in manifest['cameras'].items()}
    projection={cid:validate_projection(manifest['cameras'][cid],cam,points[:200]) for cid,cam in cameras.items()}
    records=[]
    for frame in manifest['frames']:
        for cid in cameras:
            record={'frame':frame,'cid':cid,'pixels':np.array(Image.open(data/'images'/cid/f'{frame["index"]:06d}.png').convert('RGB'))}
            if a.dataset=='textile':
                cloth=np.array(Image.open(data/'masks'/cid/f'{frame["index"]:06d}.png'))>127
                hands=np.array(Image.open(data/'occlusions'/cid/f'{frame["index"]:06d}.png'))>127
                record['foreground']=cloth|hands if cfg['photometric_loss']['include_hands'] else cloth
                record['valid']=np.ones_like(cloth) if cfg['photometric_loss']['include_hands'] else ~hands
            records.append(record)
    train=[r for r in records if r['frame']['split']=='train'];test=[r for r in records if r['frame']['split']=='test']
    def call(cam,step,training=True):
        if a.method=='4dgaussians':return render(cam,model,pipe,background,stage='coarse' if training and step<=a.coarse else 'fine')
        return render(cam,model,pipe,background,args=render_args if training else None,iteration=step)
    start_iteration=0;checkpoint=output/'checkpoint.pth';elapsed_previous=0.
    if a.resume or a.render_only:
        saved=torch.load(checkpoint,map_location='cuda',weights_only=False);model.restore(saved['model'],opt);start_iteration=saved['step'];elapsed_previous=saved['elapsed_s']
        torch.set_rng_state(saved['torch_rng'].cpu());torch.cuda.set_rng_state(saved['cuda_rng'].cpu());np.random.set_state(saved['numpy_rng']);random.setstate(saved['random_rng'])
    elif checkpoint.exists():raise ValueError('Output already has a checkpoint; use --resume or a new attempt name')
    setup={'method':a.method,'dataset':a.dataset,'attempt':a.attempt,'source_commit':cfg['methods'][a.method]['commit'],'updates':a.updates,'coarse':a.coarse if a.method=='4dgaussians' else 0,'training_args':vars(opt),'hidden_args':vars(hidden) if hidden else None,'camera_projection_max_error_px':projection,'initial_points_sha256':manifest['initial_points_sha256'],'train_images':len(train),'heldout_images':len(test),'torch':torch.__version__,'cuda_runtime':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'adapter':str(Path(__file__).relative_to(ROOT))}
    dump(output/'setup.json',setup)
    started=time.perf_counter();torch.cuda.reset_peak_memory_stats();losses=[]
    progress_path=docs/f'{tag}_progress.json'
    for step in range(start_iteration+1,a.updates+1) if not a.render_only else []:
        model.update_learning_rate(step);model.oneupSHdegree() if step%1000==0 else None
        if a.method=='4c4d' and step%1000==0:model.active_sh_degree_t=min(2,step//1000)
        record=train[random.randrange(len(train))];cam=copy.copy(cameras[record['cid']]);cam.time=cam.timestamp=record['frame']['time']
        gt=torch.tensor(record['pixels'],dtype=torch.float32,device='cuda').permute(2,0,1)/255.
        result=call(cam,step);prediction=result['render']
        if a.dataset=='textile':
            valid=torch.tensor(record['valid'],device='cuda');fg=torch.tensor(record['foreground'],device='cuda')
            weight=valid*(1+(cfg['photometric_loss']['textile_foreground_weight']-1)*fg)
            l1=((prediction-gt).abs()*weight).sum()/(3*weight.sum().clamp_min(1))
            similarity=ssim(torch.where(valid,prediction,gt.detach()),gt)
        else:l1=(prediction-gt).abs().mean();similarity=ssim(prediction,gt)
        loss=.8*l1+.2*(1-similarity)
        if a.method=='4dgaussians' and step>a.coarse:loss=loss+model.compute_regulation(.001,.0001,.0001)
        if not torch.isfinite(loss):raise FloatingPointError(f'Non-finite loss at step {step}')
        loss.backward()
        with torch.no_grad():
            vis=result['visibility_filter'];model.max_radii2D[vis]=torch.maximum(model.max_radii2D[vis],result['radii'][vis])
            if a.method=='4dgaussians':model.add_densification_stats(result['viewspace_points'].grad,vis)
            else:model.add_densification_stats(result['viewspace_points'],vis,model._t.grad.detach().abs())
            # Use upstream splitting/pruning with an explicit short-pilot budget.
            if step>=500 and step<=4500 and step%200==0:
                count=len(model.get_xyz)
                if a.method=='4dgaussians':
                    if count<cfg['training']['max_points']:model.densify(.0002,.005,extent,None,20,20)
                    model.prune(.0002,.005,extent,None)
                else:model.densify_and_prune(.0002,.005,extent,None,.0002/40,prune_only=count>=cfg['training']['max_points'])
                if len(model.get_xyz)>cfg['training']['max_points']:
                    keep=torch.topk(model.get_opacity.flatten(),cfg['training']['max_points']).indices
                    prune_mask=torch.ones(len(model.get_xyz),dtype=torch.bool,device='cuda');prune_mask[keep]=False;model.prune_points(prune_mask)
            model.optimizer.step();model.optimizer.zero_grad(set_to_none=True)
            if a.method=='4c4d':model.coef_optimizer.step();model.coef_optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach()))
        if step==1 or step%100==0 or step==a.updates:
            torch.cuda.synchronize();elapsed=elapsed_previous+time.perf_counter()-started
            stats={'step':step,'total':a.updates,'stage':'coarse' if a.method=='4dgaussians' and step<=a.coarse else 'temporal','loss':float(np.mean(losses[-100:])),'point_count':len(model.get_xyz),'elapsed_s':elapsed,'peak_cuda_allocated_gib':torch.cuda.max_memory_allocated()/2**30,'selected_camera':record['cid'],'selected_source_frame':record['frame']['source_index'],'status':'training'}
            dump(progress_path,stats)
            dump(docs/'live_progress.json',{**stats,'method':a.method,'dataset':a.dataset,'attempt':a.attempt,'preview':f'{tag}_preview.png' if (docs/f'{tag}_preview.png').exists() else None})
            print(json.dumps(stats),flush=True)
        if step%1000==0 or step==a.updates:
            torch.save({'model':model.capture(),'step':step,'elapsed_s':elapsed_previous+time.perf_counter()-started,'torch_rng':torch.get_rng_state(),'cuda_rng':torch.cuda.get_rng_state(),'numpy_rng':np.random.get_state(),'random_rng':random.getstate()},output/'checkpoint.tmp');(output/'checkpoint.tmp').replace(checkpoint)
            # Preview a genuine render at a fixed held-out timestamp.
            with torch.no_grad():
                c=copy.copy(cameras['iphone']);c.time=c.timestamp=manifest['frames'][47]['time'];im=call(c,step,False)['render'];save_img(im,docs/f'{tag}_preview.png')
    if a.updates<100:return
    # Held-out temporal interpolation; all 45 images are excluded from fitting.
    training_elapsed=elapsed_previous+time.perf_counter()-started if not a.render_only else elapsed_previous
    metrics=[]
    with torch.no_grad():
        if a.method=='4c4d':model.coefficient.eval()
        for record in test:
            cam=copy.copy(cameras[record['cid']]);cam.time=cam.timestamp=record['frame']['time'];prediction=call(cam,a.updates,False)['render'].clamp(0,1)
            gt=torch.tensor(record['pixels'],dtype=torch.float32,device='cuda').permute(2,0,1)/255.
            mse=(prediction-gt).square().mean().clamp_min(1e-12);entry={'camera':record['cid'],'local_frame':record['frame']['index'],'psnr_db':float(-10*torch.log10(mse)),'ssim':float(ssim(prediction,gt))}
            if a.dataset=='textile':
                foreground=torch.tensor(record['foreground'] & record['valid'],device='cuda')
                fg_mse=((prediction-gt).square()*foreground).sum()/(3*foreground.sum().clamp_min(1));entry['foreground_psnr_db']=float(-10*torch.log10(fg_mse.clamp_min(1e-12)))
            metrics.append(entry)
            if record['frame']['index']==47:
                save_img(prediction,docs/f'{tag}_{record["cid"]}_heldout.png');save_img(gt,docs/f'{a.dataset}_{record["cid"]}_heldout_gt.png')
    summary={'method':a.method,'dataset':a.dataset,'attempt':a.attempt,'updates':a.updates,'point_count':len(model.get_xyz),'elapsed_s':training_elapsed,'peak_cuda_allocated_gib':torch.cuda.max_memory_allocated()/2**30,'heldout_psnr_db':float(np.mean([m['psnr_db'] for m in metrics])),'heldout_ssim':float(np.mean([m['ssim'] for m in metrics])),'per_camera':{cid:{'psnr_db':float(np.mean([m['psnr_db'] for m in metrics if m['camera']==cid])),'ssim':float(np.mean([m['ssim'] for m in metrics if m['camera']==cid]))} for cid in cameras},'scope':'Full cropped-image held-out timestamps; not independent novel-view geometry accuracy.'}
    if a.dataset=='textile':summary['heldout_foreground_psnr_db']=float(np.mean([m['foreground_psnr_db'] for m in metrics]))
    if a.render_only and (output/'metrics.json').exists():summary['peak_cuda_allocated_gib']=json.loads((output/'metrics.json').read_text())['summary']['peak_cuda_allocated_gib']
    dump(output/'metrics.json',{'summary':summary,'images':metrics});dump(docs/f'{tag}_metrics.json',summary)
    dump(progress_path,{**summary,'step':a.updates,'total':a.updates,'status':'complete'})
    dump(docs/'live_progress.json',{**summary,'step':a.updates,'total':a.updates,'status':'complete','preview':f'{tag}_preview.png'})
    if a.make_videos:
        render_videos(a,cfg,manifest,cameras,records,model,pipe,call,output,docs,tag)
    print('COMPLETE '+json.dumps(summary),flush=True)

def render_videos(a,cfg,manifest,cameras,records,model,pipe,call,output,docs,tag):
    encoders=[]
    try:
        _render_videos(a,cfg,manifest,cameras,records,model,pipe,call,output,docs,tag,encoders)
    finally:
        for encoder in encoders:
            if encoder.poll() is None:encoder.terminate();encoder.wait()

def _render_videos(a,cfg,manifest,cameras,records,model,pipe,call,output,docs,tag,encoders):
    tool=next(t for t in json.loads((ROOT/'static-tools.json').read_text(encoding='utf-8-sig'))['portable_tools'] if t['name']=='FFmpeg')
    reference=cameras['iphone'];cal=manifest['cameras']['iphone'];w,h=reference.image_width,reference.image_height
    def encode(name,width,height):
        path=docs/name
        cmd=[tool['executable_path'],'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate','30000/1001','-i','pipe:0','-an','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
        encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE);encoders.append(encoder)
        return path,encoder
    fixed_path,fixed=encode(f'{tag}_rgb_fixed.mp4',w,h)
    orbit_path,orbit=encode(f'{tag}_rgb_orbit.mp4',w,h)
    compare_path,compare=encode(f'{tag}_source_comparison.mp4',w*2,h+40)
    actual=[r for r in records if r['cid']=='iphone'];norm=cfg['normalization'];center=(np.array([.175,.105,-.045])-norm['center_m'])*norm['scale_per_m']
    original_position=reference.camera_center.cpu().numpy()
    with torch.no_grad():
        for i,frame in enumerate(manifest['frames']):
            cam=copy.copy(reference);cam.time=cam.timestamp=frame['time']
            image=call(cam,a.updates,False)['render'].clamp(0,1)
            rgb=(image.permute(1,2,0).cpu().numpy()*255).round().astype('uint8');fixed.stdin.write(rgb.tobytes())
            theta=math.radians(45)*math.sin(2*math.pi*i/(len(manifest['frames'])-1))
            spin=np.array([[math.cos(theta),-math.sin(theta),0],[math.sin(theta),math.cos(theta),0],[0,0,1]])
            position=center+spin@(original_position-center);position[2]-=.02*norm['scale_per_m']
            forward=center-position;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,-1]);right/=np.linalg.norm(right);down=np.cross(forward,right);R=np.stack([right,down,forward])
            orbit_cal={**cal,'R':R.tolist(),'t':(-R@position).tolist()};orbit_cam=camera(orbit_cal,frame['time'])
            orbit_rgb=(call(orbit_cam,a.updates,False)['render'].clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype('uint8');orbit.stdin.write(orbit_rgb.tobytes())
            sheet=Image.new('RGB',(w*2,h+40),(22,26,33));sheet.paste(Image.fromarray(actual[i]['pixels']),(0,40));sheet.paste(Image.fromarray(rgb),(w,40));draw=ImageDraw.Draw(sheet)
            draw.text((15,12),f'Source iPhone · {frame["pts_s"]:.3f}s · raw frame {frame["source_index"]}',fill='white');draw.text((w+15,12),f'{a.method} continuous model · t={frame["time"]:.3f}',fill='white');compare.stdin.write(np.array(sheet).tobytes())
            if i in [0,30,60,89]:sheet.save(docs/f'{tag}_comparison_{i:02d}.jpg',quality=94,subsampling=0)
        # Continuous-time probes halfway between video frame samples.
        samples=[]
        for timestamp in [0.,.5/89,.5,.5+.5/89,1.]:
            if a.method=='4dgaussians':
                times=torch.full((len(model.get_xyz),1),timestamp,device='cuda')
                xyz,scales,rot,opacity,features=model._deformation(model.get_xyz,model._scaling,model._rotation,model._opacity,model.get_features,times)
                color=features[:,0,:]*.28209479177387814+.5;op=torch.sigmoid(opacity).flatten()
            else:
                _,offset=model.get_current_covariance_and_mean_offset(1.,timestamp);xyz=model.get_xyz+offset
                color=model.get_features[:,0,:]*.28209479177387814+.5;op=(model.get_opacity*model.get_marginal_t(timestamp)).flatten()
            samples.append((timestamp,xyz.clone(),color.clone(),op.clone()))
        first,last=samples[0],samples[-1];stable=(first[3]>.01)&(last[3]>.01)
        displacement=torch.linalg.norm(last[1]-first[1],dim=1)/norm['scale_per_m']*1000
        motion={'query_timestamps':[s[0] for s in samples],'half_frame_queries_are_model_evaluations':True,'endpoint_shared_visible_count':int(stable.sum()),'endpoint_displacement_median_mm':float(displacement[stable].median()) if stable.any() else None,'endpoint_displacement_p95_mm':float(torch.quantile(displacement[stable],.95)) if stable.any() else None,'scope':'Internal Gaussian motion for shared visible primitives; not verified material correspondence, strain or measurement accuracy.'}
        fields=['_xyz','_features_dc','_features_rest','_scaling','_rotation','_opacity']
        if a.method=='4c4d':fields+=['_t','_scaling_t','_rotation_r']
        weights={name:getattr(model,name).detach().cpu() for name in fields}
        weights['active_sh_degree']=model.active_sh_degree
        if a.method=='4dgaussians':weights['deformation_state']={k:v.detach().cpu() for k,v in model._deformation.state_dict().items()};weights['deformation_table']=model._deformation_table.detach().cpu()
        else:weights['active_sh_degree_t']=model.active_sh_degree_t;weights['coefficient_state']={k:v.detach().cpu() for k,v in model.coefficient.state_dict().items()}
        torch.save({'schema_version':1,'method':a.method,'source_commit':cfg['methods'][a.method]['commit'],'weights':weights,'setup':json.loads((output/'setup.json').read_text()),'normalization':norm,'cameras':manifest['cameras'],'time_origin_pts_s':manifest['frames'][0]['pts_s'],'time_span_s':manifest['frames'][-1]['pts_s']-manifest['frames'][0]['pts_s']},output/'continuous_model.pth')
    for path,encoder in [(fixed_path,fixed),(orbit_path,orbit),(compare_path,compare)]:
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError(f'Video encoder failed: {path}')
    motion['continuous_model_bytes']=(output/'continuous_model.pth').stat().st_size
    dump(docs/f'{tag}_motion.json',motion);dump(output/'motion_validation.json',motion)
    print('VIDEOS '+json.dumps({'fixed':fixed_path.name,'orbit':orbit_path.name,'comparison':compare_path.name,**motion}),flush=True)

if __name__=='__main__':main()
