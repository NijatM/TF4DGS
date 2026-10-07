"""Check current-scene provenance, static depth composition and observed motion."""
import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy.spatial.transform import Rotation


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8100)
    p.add_argument('--output',type=Path,default=Path('.local/workflows/dynamic_setup/current_scene_validation.json'))
    args=p.parse_args();base=f'http://127.0.0.1:{args.port}';meta=json.load(urlopen(base+'/api/meta',timeout=30))
    summary=read(Path(meta['background_source']).parent/'summary.json');bg=np.load(meta['background_source']);actor=np.load(meta['source'])
    assert summary['source_policy']=='current capture only'
    assert Path(summary['session']).parent.name=='dynamic_yogurt_001'
    assert len(bg['means'])==meta['background_gaussians']==summary['gaussians']
    assert len(actor['means'])==meta['gaussians']==51913
    assert meta['default_follow'] is False and meta['default_camera']=='iphone'
    for model in [bg,actor]:
        assert all(np.isfinite(model[k]).all() for k in model.files)
        assert np.allclose(np.linalg.norm(model['quats'],axis=1),1,atol=1e-5)
        assert (model['scales']>0).all() and ((model['opacity']>=0)&(model['opacity']<=1)).all()
    plane=np.load(Path(summary['initialization'])/'plane_flags.npy')
    assert len(plane)==len(bg['means']) and np.max(np.abs(bg['means'][plane,2]))==0
    def render(index,**q):
        response=urlopen(base+'/api/render?'+urlencode({'frame':index,'camera':'iphone',**q}),timeout=60)
        raw=response.read();im=Image.open(io.BytesIO(raw)).convert('RGB')
        return np.array(im),hashlib.sha256(raw).hexdigest()
    first=meta['frames'][0]['index'];last=meta['frames'][-1]['index']
    static_a,hash_a=render(first,actor=0);static_b,hash_b=render(last,actor=0)
    assert hash_a==hash_b,'Static surroundings/camera moved with the actor'
    frames=[];motion=[]
    for entry in meta['frames']:
        image,_=render(entry['index']);delta=np.max(np.abs(image.astype(int)-static_a.astype(int)),axis=-1)
        yy,xx=np.where(delta>8);assert len(xx)>400,'Actor unexpectedly absent/occluded'
        motion.append({'index':entry['index'],'time_s':entry['time_s'],'visible_changed_pixels':len(xx),
            'screen_center_xy':[float(xx.mean()),float(yy.mean())]})
        if entry['index'] in [first,120,last]:frames.append((entry,image))
    assert np.linalg.norm(np.array(motion[0]['screen_center_xy'])-motion[-1]['screen_center_xy'])>100
    rgb,_=render(130);field,_=render(130,mode='displacement')
    # White actor pixels can equal white background RGB while still occupying
    # geometry. Use the projected actor bounds, not a color-difference mask.
    pose=read(meta['poses_source'])['frames'][130]
    c=read(Path(summary['calibration_dir'])/'iphone.json');params=c['params'];scale=rgb.shape[1]/c['image_size'][0]
    world=actor['means']@Rotation.from_rotvec(pose['rvec']).as_matrix().T+pose['translation_m']
    cp=world@np.array(c['world_to_camera']['R']).T+c['world_to_camera']['t']
    xy=np.c_[params[0]*cp[:,0]/cp[:,2]+params[2],params[1]*cp[:,1]/cp[:,2]+params[3]]*scale
    lo=np.maximum(0,np.floor(xy.min(0)-30)).astype(int);hi=np.minimum([rgb.shape[1],rgb.shape[0]],np.ceil(xy.max(0)+30)).astype(int)
    outside=np.ones(rgb.shape[:2],bool);outside[lo[1]:hi[1],lo[0]:hi[0]]=False
    assert np.max(np.abs(field[outside].astype(int)-static_a[outside].astype(int)))<=1,'Static RGB changed with actor field'
    for view in ['fuji','dji','orbit']:
        im,_=render(120,camera=view);assert im.shape[0]>=400 and im.std()>12
    for query in [{'frame':0},{'frame':first,'camera':'missing'},{'frame':first,'mode':'missing'}]:
        try:urlopen(base+'/api/render?'+urlencode(query),timeout=30);raise AssertionError('Invalid query was accepted')
        except HTTPError as e:assert e.code==400
    canvas=Image.new('RGB',(1500,420),'#17212b');draw=ImageDraw.Draw(canvas)
    for col,(entry,img) in enumerate(frames):
        thumb=ImageOps.contain(Image.fromarray(img),(490,365));canvas.paste(thumb,(col*500+(500-thumb.width)//2,40))
        draw.text((col*500+10,10),f"t = {entry['time_s']:.3f} s | fixed current-scene Gaussian view",fill='white')
    montage=Path('outputs/dynamic_yogurt_001/static_background_03/current_scene_motion_check.jpg');canvas.save(montage,quality=94)
    result={'status':'passed','actor_gaussians':meta['gaussians'],'background_gaussians':meta['background_gaussians'],
      'source_policy':summary['source_policy'],'background_source':meta['background_source'],'model_source':meta['source'],
      'measured_table_plane_preserved':True,'static_only_first_last_png_sha256':hash_a,'static_rgb_unchanged_by_actor_fields':True,
      'supported_renders':len(motion),'motion_observations':motion,'unsupported_samples_rejected':True,
      'all_camera_presets_rendered':True,'metric_accuracy_verified':False,
      'limits':'Checks show the renderer works; monocular room depth and motion calibration are still provisional.'}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='motion_observations'},indent=2))


if __name__=='__main__':main()
