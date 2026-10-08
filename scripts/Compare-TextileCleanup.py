"""Measure cleanup changes against native source pixels before selecting an export."""
import argparse
from importlib.machinery import SourceFileLoader
import json
import math
from pathlib import Path
import numpy as np
import torch
from gsplat import rasterization

ROOT=Path(__file__).resolve().parents[1]
trainer=SourceFileLoader('textile_frame_trainer',str(Path(__file__).with_name('Train-TextileGaussianFrame.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--output',default='.local/workflows/dynamic_setup/textile_reconstruction_02/cleanup_comparison.json');a=p.parse_args()
    sequence=json.loads(Path(a.sequence).read_text());session=ROOT/sequence['source_session'];masks=ROOT/sequence['masks']
    balance=json.loads((ROOT/'outputs/dynamic_textile_001/color_balance_02/color_balance.json').read_text())
    rows=[]
    with torch.no_grad():
        for index in [0,158,266,425]:
            entry=next(f for f in sequence['frames'] if f['index']==index);path=ROOT/entry['model']
            views=trainer.records(session,masks,index,0,balance)
            for variant in ['model.npz','clean_model.npz','clean_support_model.npz','clean_opacity_model.npz']:
                if not path.with_name(variant).exists():continue
                raw=np.load(path.with_name(variant));m={k:torch.tensor(raw[k],device='cuda',dtype=torch.float32) for k in raw.files}
                for view in views:
                    rgb,alpha,_=rasterization(m['means'],m['quats'],m['scales'],m['opacity'],m.get('sh',m['colors']),view['view'],view['K'],view['width'],view['height'],
                        sh_degree=1 if 'sh' in m else None,packed=False,near_plane=.01,far_plane=4,rasterize_mode='antialiased')
                    rgb=rgb[0];alpha=alpha[0,:,:,0];weight=(view['mask']>.75).float()
                    mse=((rgb/alpha[...,None].clamp_min(.2)-view['target']).square().mean(-1)*weight).sum()/weight.sum().clamp_min(1)
                    rows.append(dict(index=index,camera=view['camera'],variant=variant,foreground_psnr_db=-10*math.log10(max(float(mse),1e-12)),
                         alpha_mae=float(((alpha-view['mask']).abs()*(1-view['occlusion'])).mean()),
                         mean_foreground_alpha=float((alpha*weight).sum()/weight.sum().clamp_min(1))))
                del m,raw;torch.cuda.empty_cache()
    Path(a.output).write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))


if __name__=='__main__':main()
