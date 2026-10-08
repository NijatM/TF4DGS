"""Local CUDA renderer for reconstructed textile RGB Gaussian keyframes.

Shape/appearance fields use nearest reference surface association, not material
identity. Source-session table geometry is rendered in the same Gaussian pass.
"""
import argparse
from functools import lru_cache
from http.server import BaseHTTPRequestHandler,HTTPServer
import io
import json
import math
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from importlib.machinery import SourceFileLoader

import numpy as np
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
import torch
from gsplat import rasterization

ROOT=Path(__file__).resolve().parents[1]
stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--port',type=int,default=8104);a=p.parse_args();sequence=Path(a.sequence).resolve()
    raw=stereo.read(sequence);session=ROOT/raw['source_session'];cams=stereo.cameras(session)
    if session.parent.resolve()!=(ROOT/'data/dynamic_textile_001').resolve():raise ValueError('Only this textile capture is accepted')
    table=None
    if raw.get('table_model'):
        tablepath=ROOT/raw['table_model'];info=stereo.read(tablepath.parent/'summary.json')
        if info['source_policy']!='current textile capture only' or (ROOT/info['source_session']).resolve()!=session.resolve():raise ValueError('Incompatible table source')
        data=np.load(tablepath);table={k:torch.tensor(data[k],device='cuda',dtype=torch.float32) for k in data.files}
    center=np.array([.175,.10,-.045]);first=next(f for f in raw['frames'] if f['index']==0)
    trackpath=ROOT/'outputs/dynamic_textile_001/dense_tracking_02/multiview_nodes.npz'
    tracks=np.load(trackpath) if trackpath.exists() else None
    html=(ROOT/'src/tf4dgs/assets/textile_gaussian_preview.html').read_bytes()
    def meta():
        r=stereo.read(sequence)
        return dict(source=str(sequence.relative_to(ROOT)).replace('\\','/'),frames=r['frames'],status=r['status'],requested=len(r['requested_indexes']),
           gaussians=r['frames'][0]['gaussians'],table_gaussians=0 if table is None else len(table['means']),
           representation=r['representation'],metric_accuracy_verified=False,persistent_material_ids=False,
           geometry_field=r['geometry_field'],appearance_field='Visible recorded-camera RGB contrast to the closest reference surface; unknown is gray',camera_views=['iphone','fuji','dji'],
           time_interpolation=False,appearance='Actual per-keyframe fitted RGB',source_policy='current textile capture only',
           field_references=['first','recent'])
    @lru_cache(maxsize=6)
    def reference_surface(path):
        file=(ROOT/path).resolve();allowed=(ROOT/'outputs/dynamic_textile_001').resolve()
        if allowed not in file.parents:raise ValueError('Reference is outside the textile output folder')
        with np.load(file) as data:
            return cKDTree(data['means'])
    @lru_cache(maxsize=6)
    def observed_reference(path):
        file=ROOT/path;observation=file.with_name('observed_appearance.npz')
        if not observation.exists():raise ValueError('Recorded appearance for the reference time is still processing')
        points=reference_surface(path).data
        with np.load(observation) as appearance:
            valid=appearance['visible_views']>0
            if len(valid)!=len(points) or not valid.any():raise ValueError('Invalid recorded appearance reference')
            return cKDTree(points[valid]),appearance['colors'][valid].copy()
    @lru_cache(maxsize=6)
    def load_model(index,path):
        file=(ROOT/path).resolve();allowed=(ROOT/'outputs/dynamic_textile_001').resolve()
        if allowed not in file.parents:raise ValueError('Model is outside the textile output folder')
        with np.load(file) as data:
            arrays={k:data[k].copy() for k in data.files}
        return {k:torch.tensor(v,device='cuda',dtype=torch.float32) for k,v in arrays.items()},arrays
    @lru_cache(maxsize=6)
    def geometry_field(index,path,reference_index,reference_path):
        _,data=load_model(index,path);distance,_=reference_surface(reference_path).query(data['means'])
        if index==reference_index:distance[:]=0
        return torch.tensor(distance,device='cuda',dtype=torch.float32)
    @lru_cache(maxsize=6)
    def appearance_field(index,path,reference_index,reference_path):
        _,data=load_model(index,path);tree,reference_colors=observed_reference(reference_path)
        observation=(ROOT/path).with_name('observed_appearance.npz')
        if not observation.exists():raise ValueError('Recorded appearance for this time is still processing')
        with np.load(observation) as appearance:
            colors=appearance['colors'];known=appearance['visible_views']>0
        if len(known)!=len(data['means']):raise ValueError('Appearance and Gaussian counts differ')
        _,nearest=tree.query(data['means']);contrast=np.linalg.norm(colors-reference_colors[nearest],axis=1)/math.sqrt(3.)
        if index==reference_index:contrast[:]=0
        return torch.tensor(contrast,device='cuda',dtype=torch.float32),torch.tensor(known,device='cuda')
    @torch.no_grad()
    def render(query):
        def number(key,default,low,high):
            value=float(query.get(key,[str(default)])[0])
            if not math.isfinite(value) or not low<=value<=high:raise ValueError('Invalid '+key)
            return value
        index=int(query.get('frame',['0'])[0]);r=stereo.read(sequence);entry=next((f for f in r['frames'] if f['index']==index),None)
        if entry is None:raise ValueError('Frame has no trained model; no time interpolation')
        model,_=load_model(index,entry['model']);mode=query.get('mode',['rgb'])[0]
        if mode not in ['rgb','geometry','color','combined']:raise ValueError('Unknown mode')
        reference_kind=query.get('reference',['first'])[0]
        if reference_kind not in ['first','recent']:raise ValueError('Unknown reference surface')
        history=number('history',5,.2,10)
        reference=first
        if reference_kind=='recent':
            earlier=max(first['time_s'],entry['time_s']-history)
            reference=max((f for f in r['frames'] if f['time_s']<=earlier),key=lambda f:f['time_s'])
        distance=geometry_field(index,entry['model'],reference['index'],reference['model']) if mode in ['geometry','combined'] else None
        contrast,known=appearance_field(index,entry['model'],reference['index'],reference['model']) if mode in ['color','combined'] else (None,None)
        camera=query.get('camera',['iphone'])[0];width,height=1000,700
        if camera=='orbit':
            az=math.radians(number('azimuth',95,-360,360));el=math.radians(number('elevation',40,5,85));radius=number('distance',.57,.18,2)
            target=center+np.array([number('pan_x',0,-.8,.8),number('pan_y',0,-.8,.8),0])
            pos=target+radius*np.array([math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),-math.sin(el)])
            forward=target-pos;forward/=np.linalg.norm(forward);right=np.cross(forward,[0.,0.,-1.]);right/=np.linalg.norm(right);down=np.cross(forward,right)
            R=np.array([right,down,forward]);view=np.eye(4);view[:3,:3]=R;view[:3,3]=-R@pos
            K=np.array([[850,0,width/2],[0,850,height/2],[0,0,1.]])
        elif camera in cams:
            c=cams[camera];box={'iphone':[950,440,3450,1950],'fuji':[0,0,3330,1780],'dji':[0,330,1536,2304]}[camera]
            factor=min(width/(box[2]-box[0]),height/(box[3]-box[1]));width=round((box[2]-box[0])*factor);height=round((box[3]-box[1])*factor)
            K=c['K'].copy();K[0,2]-=box[0];K[1,2]-=box[1];K[:2]*=factor
            view=np.eye(4);R=c['R'];view[:3,:3]=R;view[:3,3]=c['t']
        else:raise ValueError('Unknown camera')
        maximum=number('maximum',.1,.001,.5);color_max=number('color_max',.30,.005,1.)
        def draw(field):
            if field=='rgb':colors=model['colors']
            elif field=='geometry':
                u=(distance/maximum).clamp(0,1);colors=torch.stack([u,.75*(1-(2*u-1).abs()),1-u],dim=1)
            else:
                u=(contrast/color_max).clamp(0,1);colors=torch.stack([.3+.7*u,.1+.85*u,.65*(1-u)],dim=1)
                colors[~known]=.45
            m={**model,'colors':colors}
            if table is not None and query.get('table',['1'])[0]=='1':m={k:torch.cat([v,table[k]]) for k,v in m.items()}
            rgb,alpha,_=rasterization(m['means'],m['quats'],m['scales'],m['opacity'],m['colors'],
                torch.tensor(view,dtype=torch.float32,device='cuda')[None],torch.tensor(K,dtype=torch.float32,device='cuda')[None],
                width,height,packed=False,near_plane=.01,far_plane=5,rasterize_mode='antialiased')
            return Image.fromarray(((rgb[0]+(1-alpha[0])*.92).clamp(0,1).cpu().numpy()*255).astype(np.uint8))
        if mode=='combined':
            image=Image.new('RGB',(width*2,height+28),'#19232f');image.paste(draw('geometry'),(0,28));image.paste(draw('color'),(width,28))
            d=ImageDraw.Draw(image);d.text((10,8),'Reference-surface distance',fill='white');d.text((width+10,8),'Recorded-camera appearance contrast (gray: unknown)',fill='white')
        else:image=draw(mode)
        field_status=('RGB keyframe fit' if mode=='rgb' else
            f"Nearest-surface comparison to t={reference['time_s']:.3f}s; not material displacement or pigment change")
        if mode in ['color','combined']:field_status+='; recorded RGB samples, gray is unknown'
        if query.get('trails',['0'])[0]=='1' and tracks is not None and mode!='combined':
            now=entry['time_s'];ids=np.arange(0,tracks['canonical'].shape[0],20)
            window=np.flatnonzero((tracks['times_s']<=now)&(tracks['times_s']>=now-history));d=ImageDraw.Draw(image)
            for older,newer in zip(window,window[1:]):
                valid=tracks['supported'][older,ids]&tracks['supported'][newer,ids]
                if not valid.any():continue
                aa=tracks['positions'][older,ids[valid]];bb=tracks['positions'][newer,ids[valid]]
                def project(points):
                    xyz=points@R.T+view[:3,3];pix=xyz@K.T;return pix[:,:2]/pix[:,2:],xyz[:,2]
                pa,za=project(aa);pb,zb=project(bb)
                fade=max(0,1-(now-tracks['times_s'][newer])/history)
                for i in range(len(pa)):
                    if za[i]>.01 and zb[i]>.01:d.line([tuple(pa[i]),tuple(pb[i])],fill=(round(235*fade),80,30),width=2)
            field_status+='; trails only where calibrated tracks are supported'
        stream=io.BytesIO();image.save(stream,format='PNG');return stream.getvalue(),field_status
    class Handler(BaseHTTPRequestHandler):
        def reply(self,body,kind,status=200,field=None):
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            if field:self.send_header('X-TF4DGS-Field-Status',field)
            self.end_headers();self.wfile.write(body)
        def do_GET(self):
            request=urlparse(self.path)
            try:
                if request.path=='/':self.reply(html,'text/html; charset=utf-8')
                elif request.path=='/api/meta':self.reply(json.dumps(meta()).encode(),'application/json')
                elif request.path=='/api/render':
                    body,status=render(parse_qs(request.query));self.reply(body,'image/png',field=status)
                else:self.reply(b'{"error":"Not found"}','application/json',404)
            except (ValueError,TypeError,KeyError) as error:self.reply(json.dumps({'error':str(error)}).encode(),'application/json',400)
        def log_message(self,*args):pass
    print(f'Actual textile Gaussian RGB viewer: http://127.0.0.1:{a.port}',flush=True)
    HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()


if __name__=='__main__':main()
