"""Decode one exported continuous model without its training images/checkpoint.

Run with that method's isolated Python environment. Official CUDA extensions
are required. This is a framework decoder, not an animated-PLY converter.
"""
import argparse, copy, json, math, subprocess, sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--output',required=True);p.add_argument('--fps',type=float,default=30);p.add_argument('--orbit',action='store_true');p.add_argument('--probe-only',action='store_true');p.add_argument('--reference-image');p.add_argument('--reference-time',type=float,default=47/89);p.add_argument('--crf',type=int,default=17);a=p.parse_args()
    if a.fps<=0:raise ValueError('Output fps must be positive')
    if not 0<=a.crf<=51:raise ValueError('H.264 CRF must be between 0 and 51')
    packet=torch.load(a.model,map_location='cuda',weights_only=False);method=packet['method'];weights=packet['weights']
    source=ROOT/'.local/research'/('4DGaussians' if method=='4dgaussians' else '4C4D');sys.path.insert(0,str(source))
    from scene.gaussian_model import GaussianModel
    from gaussian_renderer import render
    if method=='4dgaussians':
        model=GaussianModel(3,SimpleNamespace(**packet['setup']['hidden_args']))
        model._deformation.load_state_dict(weights['deformation_state']);model._deformation.cuda()
        model._deformation_table=weights['deformation_table']
    else:
        model=GaussianModel(3,gaussian_dim=4,time_duration=[0.,1.],rot_4d=True,force_sh_3d=False,sh_degree_t=2)
        model.active_sh_degree_t=weights['active_sh_degree_t']
    for name,value in weights.items():
        if name.startswith('_'):setattr(model,name,torch.nn.Parameter(value,requires_grad=False))
    model.active_sh_degree=weights['active_sh_degree']
    pipe=SimpleNamespace(convert_SHs_python=False,compute_cov3D_python=False,debug=False,env_map_res=0)
    spec=spec_from_file_location('temporal_shared',ROOT/'scripts/Train-TemporalBenchmark.py');shared=module_from_spec(spec);spec.loader.exec_module(shared)
    cal=packet['cameras']['iphone'];reference=shared.camera(cal,0);bg=torch.ones(3,device='cuda')
    def query(cam):
        return render(cam,model,pipe,bg,stage='fine')['render'] if method=='4dgaussians' else render(cam,model,pipe,bg)['render']
    with torch.no_grad():
        for t in [0.,.25,.5,.75,1.]:
            cam=copy.copy(reference);cam.time=cam.timestamp=t;im=query(cam)
            if not torch.isfinite(im).all():raise ValueError('Non-finite decoded image')
            print(json.dumps({'method':method,'normalized_time':t,'image_shape':list(im.shape),'mean_rgb':im.mean((1,2)).tolist(),'gaussians':len(model.get_xyz)}),flush=True)
        if a.reference_image:
            cam=copy.copy(reference);cam.time=cam.timestamp=a.reference_time
            decoded=(query(cam).clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype('uint8')
            expected=np.array(Image.open(a.reference_image).convert('RGB'))
            if decoded.shape!=expected.shape:raise ValueError('Export reference dimensions differ')
            delta=np.abs(decoded.astype('int16')-expected.astype('int16'))
            validation={'reference_image':Path(a.reference_image).name,'normalized_time':a.reference_time,'maximum_channel_error_8bit':int(delta.max()),'mean_channel_error_8bit':float(delta.mean()),'matching_fraction':float((delta==0).mean()),'independent_decoder':True}
            if delta.max()>1:raise ValueError(f'Export changed reference render: {validation}')
            validation_path=Path(a.output).with_suffix('.validation.json');validation_path.parent.mkdir(parents=True,exist_ok=True)
            validation_path.write_text(json.dumps(validation,indent=2)+'\n',encoding='utf8')
            print('EXPORT_VALIDATION '+json.dumps(validation),flush=True)
    if a.probe_only:return
    tool=next(t for t in json.loads((ROOT/'static-tools.json').read_text(encoding='utf-8-sig'))['portable_tools'] if t['name']=='FFmpeg')
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    width,height=reference.image_width,reference.image_height
    # Query exact output-time seconds; do not duplicate native-frame states.
    duration=packet['time_span_s']+1001/30000;count=round(duration*a.fps)
    cmd=[tool['executable_path'],'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}','-framerate',str(a.fps),'-i','pipe:0','-an','-vf','scale=in_range=full:out_color_matrix=bt709:out_range=tv,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709','-c:v','libx264','-preset','slow','-crf',str(a.crf),'-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv','-movflags','+faststart',str(output)]
    encoder=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    norm=packet['normalization'];target=(np.array([.175,.105,-.045])-norm['center_m'])*norm['scale_per_m'];initial=reference.camera_center.cpu().numpy()
    try:
        with torch.no_grad():
            for i in range(count):
                t=min(1.,(i/a.fps)/packet['time_span_s']);cam=copy.copy(reference);cam.time=cam.timestamp=t
                if a.orbit:
                    theta=math.radians(45)*math.sin(2*math.pi*i/max(1,count-1));spin=np.array([[math.cos(theta),-math.sin(theta),0],[math.sin(theta),math.cos(theta),0],[0,0,1]])
                    position=target+spin@(initial-target);position[2]-=.02*norm['scale_per_m'];forward=target-position;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,-1]);right/=np.linalg.norm(right);R=np.stack([right,np.cross(forward,right),forward])
                    cam=shared.camera({**cal,'R':R.tolist(),'t':(-R@position).tolist()},t)
                image=(query(cam).clamp(0,1).permute(1,2,0).cpu().numpy()*255).round().astype('uint8');encoder.stdin.write(image.tobytes())
        encoder.stdin.close()
        if encoder.wait()!=0:raise RuntimeError('Video encoding failed')
    finally:
        if encoder.poll() is None:encoder.terminate();encoder.wait()
    record={'model':str(Path(a.model).name),'method':method,'frames':count,'fps':a.fps,'duration_s':count/a.fps,'source_time_origin_pts_s':packet['time_origin_pts_s'],'source_time_span_s':packet['time_span_s'],'frame_states':'Direct continuous-model queries at exact output seconds; no training images or discrete PLY sequence used.','orbit_degrees':45 if a.orbit else 0,'width':width,'height':height,'encoding':{'codec':'libx264','preset':'slow','crf':a.crf,'pixel_format':'yuv420p','matrix':'bt709','range':'tv'}}
    output.with_suffix('.render.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
    print(json.dumps(record),flush=True)

if __name__=='__main__':main()
