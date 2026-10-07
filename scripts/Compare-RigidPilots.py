"""Compare measured rigid actors on identical native crops and foreground masks.

The shared held-out times were used for checkpoint selection. This comparison
is a quality diagnostic, not an untouched test or physical accuracy certificate.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps
import torch
from gsplat import rasterization


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve previous comparison records')
    configs=[read(folder/'training_config.json') for folder in [args.baseline,args.candidate]]
    for key in ['session','poses','canonical_calibration','spacing_mm']:
        if configs[0][key]!=configs[1][key]:raise ValueError(f'Comparison uses different {key}')
    if read(args.baseline/'training_views.json')!=read(args.candidate/'training_views.json'):
        raise ValueError('Comparison view splits or native crops differ')
    args.output.mkdir(parents=True);inputs=args.output/'shared_inputs';inputs.mkdir()
    spec=importlib.util.spec_from_file_location('rigid_pilot_training',Path(__file__).with_name('Train-RigidGaussianPilot.py'))
    trainer=importlib.util.module_from_spec(spec);spec.loader.exec_module(trainer)
    config=configs[0]
    _,_,_,records,_=trainer.load_training_data(Path(config['session']),read(config['poses']),inputs,
        config['spacing_mm']/1000,Path(config['canonical_calibration']))
    held=[r for r in records if r['heldout']]
    panel={cid:min((i for i,r in enumerate(held) if r['camera']==cid),key=lambda i:abs(held[i]['time_s']-12.012))
           for cid in ['dji','fuji','iphone']}
    models=[]
    for folder in [args.baseline,args.candidate]:
        with np.load(folder/'canonical_actor.npz') as data:
            models.append({key:torch.tensor(data[key],dtype=torch.float32,device='cuda') for key in data.files})
    errors=[[],[]];alpha_errors=[[],[]];foreground_alpha=[[],[]];panels={};metrics=[]
    with torch.no_grad():
        for index,r in enumerate(held):
            mask=r['mask'].to('cuda');target=r['target'].to('cuda');background=r['background'].to('cuda')
            views=[]
            for model_index,m in enumerate(models):
                means=m['means']@r['R'].T+r['t']
                quats=trainer.quaternion_product(r['quat'].expand(len(means),4),m['quats'])
                rgb,alpha,_=rasterization(means,quats,m['scales'],m['opacity'],m['colors'],r['view'],r['K'],r['width'],r['height'],
                    packed=False,near_plane=.01,far_plane=10,rasterize_mode='antialiased')
                alpha=alpha[0,:,:,0];composite=rgb[0]+(1-alpha[:,:,None])*background
                mse=float(((composite-target).square().sum(-1)*mask).sum()/(3*mask.sum().clamp_min(1)))
                alpha_mae=float((alpha-mask).abs().mean())
                mean_alpha=float((alpha*mask).sum()/mask.sum().clamp_min(1))
                errors[model_index].append(mse);alpha_errors[model_index].append(alpha_mae);foreground_alpha[model_index].append(mean_alpha)
                views.append((composite,alpha))
                metrics.append({'model':model_index,'camera':r['camera'],'index':r['index'],'time_s':r['time_s'],
                    'foreground_mse':mse,'alpha_mae':alpha_mae,'mean_foreground_alpha':mean_alpha})
            if index==panel[r['camera']]:
                panels[r['camera']]=(r,target,views)
        sheet=Image.new('RGB',(1600,1230),'#151c25');draw=ImageDraw.Draw(sheet)
        for row,cid in enumerate(['dji','fuji','iphone']):
            r,target,views=panels[cid]
            arrays=[target,views[0][0],views[1][0],views[1][1][:,:,None].expand(-1,-1,3)]
            labels=['source crop','measured model 05','solid model 06','model 06 alpha']
            for col,(array,label) in enumerate(zip(arrays,labels)):
                values=(array.clamp(0,1).cpu().numpy()*255).astype(np.uint8)
                thumb=ImageOps.contain(Image.fromarray(values),(390,365))
                sheet.paste(thumb,(col*400+(400-thumb.width)//2,row*410+38))
                draw.text((col*400+8,row*410+10),f'{cid} | {r["time_s"]:.3f}s | {label}',fill='white')
        sheet.save(args.output/'comparison.jpg',quality=95)
    summaries=[]
    for index,folder in enumerate([args.baseline,args.candidate]):
        summaries.append({'model':folder.as_posix(),'gaussians':len(models[index]['means']),
            'foreground_psnr_db':-10*math.log10(max(float(np.mean(errors[index])),1e-12)),
            'alpha_mae':float(np.mean(alpha_errors[index])),
            'mean_foreground_alpha':float(np.mean(foreground_alpha[index]))})
    report={'status':'passed','identical_native_crops_and_masks':True,'heldout_views':len(held),
        'heldout_indices':sorted({r['index'] for r in held}), 'models':summaries,
        'scope':'Shared held-out-time comparison, used for checkpoint/model selection; not an untouched independent test or metric certificate.'}
    (args.output/'summary.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (args.output/'per_view.json').write_text(json.dumps(metrics,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
