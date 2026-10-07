"""Local interactive renderer for the actual persistent rigid Gaussian pilot.

This shows model-based rigid displacement/activity, not physical strain. No
time interpolation or time-varying Gaussian color is asserted. A single-thread
server keeps CUDA renders sequential; only the loopback interface is exposed.
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
import math
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation
import torch
from gsplat import rasterization


def quaternion_product(a,b):
    aw,ax,ay,az=a.unbind(-1);bw,bx,by,bz=b.unbind(-1)
    return torch.stack((aw*bw-ax*bx-ay*by-az*bz,aw*bx+ax*bw+ay*bz-az*by,
                        aw*by-ax*bz+ay*bw+az*bx,aw*bz+ax*by-ay*bx+az*bw),dim=-1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,default=Path('outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid/canonical_actor.npz'))
    parser.add_argument('--poses',type=Path,help='Defaults to the model motion.json; incompatible canonical motion is rejected')
    parser.add_argument('--background',type=Path,help='Current-session static Gaussian layer; no earlier-scene background is accepted')
    parser.add_argument('--actor-only',action='store_true',help='Open the separate actor comparison without its static surroundings')
    parser.add_argument('--port',type=int,default=8100);args=parser.parse_args()
    motion=json.loads((args.model.parent/'motion.json').read_text(encoding='utf-8'))
    model_poses=Path(motion['poses'])
    if args.poses is not None and args.poses.resolve()!=model_poses.resolve():
        raise ValueError('Model and motion differ; use the rigid poses recorded in this model motion.json')
    args.poses=model_poses
    data=np.load(args.model);model={key:torch.tensor(data[key],dtype=torch.float32,device='cuda') for key in data.files}
    poses=json.loads(args.poses.read_text(encoding='utf-8'));valid=[i for i,p in enumerate(poses['frames']) if p and p['valid']]
    transforms={}
    for index in valid:
        p=poses['frames'][index];rotation=Rotation.from_rotvec(p['rvec'])
        transforms[index]=(torch.tensor(rotation.as_matrix(),dtype=torch.float32,device='cuda'),
                           torch.tensor(p['translation_m'],dtype=torch.float32,device='cuda'),
                           torch.tensor(rotation.as_quat()[[3,0,1,2]],dtype=torch.float32,device='cuda'))
    def world(index):
        R,t,q=transforms[index];return model['means']@R.T+t
    reference=world(valid[0]);reference_center=reference.mean(0).cpu().numpy()
    default_background=Path('outputs/dynamic_yogurt_001/static_background_03/trained_01/static_background.npz')
    if args.background is None and not args.actor_only and args.model.parent.name=='gaussian_pilot_06_measured_solid' and default_background.exists():
        args.background=default_background
    background=None;cameras={};scene_center=np.array([.175,.105,-.025])
    if args.background is not None:
        info=json.loads((args.background.parent/'summary.json').read_text(encoding='utf-8'))
        if info.get('source_policy')!='current capture only' or Path(info['calibration_dir']).resolve()!=Path(motion['canonical_calibration']).resolve():
            raise ValueError('Background must come from this current session and share the actor calibration')
        if Path(info['session']).parent.resolve()!=Path('data/dynamic_yogurt_001').resolve():
            raise ValueError('An earlier/different scene cannot supply this background')
        raw=np.load(args.background);background={k:torch.tensor(raw[k],dtype=torch.float32,device='cuda') for k in raw.files}
        session=json.loads(Path(info['session']).read_text(encoding='utf-8-sig'))
        for entry in session['cameras']:
            c=json.loads((Path(info['session']).parent/entry['calibration']).read_text(encoding='utf-8-sig'));p=c['params']
            cameras[entry['id']]={'K':np.array([[p[0],0,p[2]],[0,p[1],p[3]],[0,0,1.]]),
              'R':np.array(c['world_to_camera']['R']),'t':np.array(c['world_to_camera']['t']),'size':c['image_size']}
    metadata={'gaussians':len(data['means']),'reference_time_s':poses['frames'][valid[0]]['time_s'],
              'frames':[{'index':i,'time_s':poses['frames'][i]['time_s']} for i in valid],
              'metric_accuracy_verified':False,'motion':'Rigid container pose, not material strain',
              'appearance':'Fixed trained RGB; temporal appearance is not fitted',
              'poses_source':args.poses.as_posix(),
              'source':args.model.as_posix()}
    metadata.update({'background_gaussians':0 if background is None else len(background['means']),
      'background_source':None if args.background is None else args.background.as_posix(),
      'background_static_in_time':True,'background_geometry':'Measured tabletop; off-table depth prior, unverified',
      'default_camera':'iphone' if background is not None else 'orbit','camera_views':list(cameras),
      'default_follow':False,'default_distance':1. if background is not None else .35,
      'scene_center_m':scene_center.tolist(),'source_policy':'current capture only'})
    html=Path('src/tf4dgs/assets/rigid_gaussian_preview.html').read_bytes()
    @torch.no_grad()
    def render(query):
        def number(key,default,low,high):
            result=float(query.get(key,[default])[0])
            if not math.isfinite(result) or not low<=result<=high:raise ValueError('Invalid '+key)
            return result
        index=int(query.get('frame',[str(valid[0])])[0])
        if index not in transforms:raise ValueError('Unsupported frame; no pose interpolation')
        mode=query.get('mode',['rgb'])[0]
        if mode not in ('rgb','displacement','recent'):raise ValueError('Unknown field')
        az=math.radians(number('azimuth',30,-360,360));el=math.radians(number('elevation',35,5,85))
        distance=number('distance',metadata['default_distance'],.13,4);history=number('history',5,.1,30);maximum=number('maximum',.1,.0001,1)
        means=world(index);following=query.get('follow',['0'])[0]=='1'
        show_background=background is not None and query.get('background',['1'])[0]=='1'
        show_actor=query.get('actor',['1'])[0]=='1'
        if not show_actor and not show_background:raise ValueError('No visible Gaussian layer')
        camera_name=query.get('camera',[metadata['default_camera']])[0]
        if camera_name not in ['orbit',*cameras]:raise ValueError('Unknown camera')
        if camera_name=='orbit':
            fixed_center=scene_center if show_background else reference_center
            center=means.mean(0).cpu().numpy() if following else fixed_center
            center=center+np.array([number('pan_x',0,-2,2),number('pan_y',0,-2,2),0])
            position=center+distance*np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),-math.sin(el)])
            forward=center-position;forward/=np.linalg.norm(forward);right=np.cross(forward,[0.,0.,-1.]);right/=np.linalg.norm(right);down=np.cross(forward,right)
            R=np.array([right,down,forward]);view=np.eye(4);view[:3,:3]=R;view[:3,3]=-R@position
            width,height=900,650;K=np.array([[900.,0,width/2],[0,900.,height/2],[0,0,1.]])
        else:
            c=cameras[camera_name];factor=min(900/c['size'][0],650/c['size'][1]);width=round(c['size'][0]*factor);height=round(c['size'][1]*factor)
            R=c['R'];position=-R.T@c['t']
            if following:position+=means.mean(0).cpu().numpy()-reference_center
            view=np.eye(4);view[:3,:3]=R;view[:3,3]=-R@position;K=c['K'].copy();K[:2]*=factor
        value=torch.linalg.norm(means-reference,dim=1);now=poses['frames'][index]['time_s']
        window=[i for i in valid if i<=index and poses['frames'][i]['time_s']>=now-history]
        field_status='supported'
        if mode=='recent':
            value=torch.zeros(len(means),device='cuda')
            supported_pairs=0
            for older,newer in zip(window,window[1:]):
                if newer!=older+1:continue
                supported_pairs+=1
                fade=max(0,1-(now-poses['frames'][newer]['time_s'])/history)
                value+=torch.linalg.norm(world(newer)-world(older),dim=1)*fade
            if not supported_pairs:field_status='no contiguous motion history'
        colors=model['colors']
        if mode!='rgb':
            u=(value/maximum).clamp(0,1)
            colors=torch.stack((u,(1-torch.abs(2*u-1))*.8,1-u),dim=1)
            if field_status!='supported':colors=torch.full_like(colors,.5)
        q=transforms[index][2].expand(len(means),4)
        render_model={'means':means,'quats':quaternion_product(q,model['quats']),'scales':model['scales'],'opacity':model['opacity'],'colors':colors}
        if not show_actor:render_model=background
        elif show_background:
            # A single world-space rasterization gives Gaussian depth ordering and
            # occlusion. Fields affect the actor; the static layer stays RGB.
            render_model={k:torch.cat((v,background[k]),dim=0) for k,v in render_model.items()}
        rgb,alpha,_=rasterization(render_model['means'],render_model['quats'],render_model['scales'],render_model['opacity'],render_model['colors'],
            torch.tensor(view,dtype=torch.float32,device='cuda')[None],torch.tensor(K,dtype=torch.float32,device='cuda')[None],
            width,height,packed=False,near_plane=.01,far_plane=10,rasterize_mode='antialiased')
        pixels=((rgb[0]+(1-alpha[0])*.92).clamp(0,1).cpu().numpy()*255).astype(np.uint8)
        image=Image.fromarray(pixels)
        if show_actor and query.get('trails',['0'])[0]=='1':
            overlay=Image.new('RGBA',image.size);draw=ImageDraw.Draw(overlay)
            ids=np.linspace(0,len(means)-1,35,dtype=int)
            for older,newer in zip(window,window[1:]):
                if newer!=older+1:continue
                a=world(older)[ids].cpu().numpy();b=world(newer)[ids].cpu().numpy()
                def project(points):
                    camera=points@R.T+view[:3,3];p=camera@K.T
                    return p[:,:2]/p[:,2:],camera[:,2]
                pa,za=project(a);pb,zb=project(b);fade=max(0,1-(now-poses['frames'][newer]['time_s'])/history)
                for j in range(len(ids)):
                    if za[j]>.01 and zb[j]>.01:draw.line([tuple(pa[j]),tuple(pb[j])],fill=(224,77,29,round(180*fade)),width=2)
            image=Image.alpha_composite(image.convert('RGBA'),overlay).convert('RGB')
        stream=io.BytesIO();image.save(stream,format='PNG');return stream.getvalue(),field_status
    class Handler(BaseHTTPRequestHandler):
        def reply(self,body,kind,code=200,field_status=None):
            self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            if field_status:self.send_header('X-TF4DGS-Field-Status',field_status)
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            p=urlparse(self.path)
            try:
                if p.path=='/':self.reply(html,'text/html; charset=utf-8')
                elif p.path=='/api/meta':self.reply(json.dumps(metadata).encode(),'application/json')
                elif p.path=='/api/render':
                    body,field_status=render(parse_qs(p.query));self.reply(body,'image/png',field_status=field_status)
                else:self.reply(b'{"error":"Not found"}','application/json',404)
            except (ValueError,KeyError,TypeError) as error:self.reply(json.dumps({'error':str(error)}).encode(),'application/json',400)
        def log_message(self,*args):pass
    print(f'Real rigid Gaussian preview: http://127.0.0.1:{args.port}',flush=True)
    HTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
