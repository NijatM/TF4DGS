"""CPU-only immutable preview export from a saved full-training checkpoint.

Uses the pinned official 4D capture tuple; no training images or per-frame
geometry are used. A hardlink protects the checkpoint while the trainer
atomically advances checkpoint.pth. Starting a GPU viewer is a separate step.
"""
import argparse
import hashlib
import json
import os
import uuid
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[1]

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dataset',choices=['textile','yogurt'],default='textile')
    args=parser.parse_args()
    experiment=ROOT/'outputs/4c4d_full_001'
    source=experiment/args.dataset/'whole_1280/checkpoint.pth'
    folder=experiment/'previews'/args.dataset
    folder.mkdir(parents=True,exist_ok=True)
    snapshot=folder/('capture_'+uuid.uuid4().hex+'.pth')
    os.link(source,snapshot)
    try:
        saved=torch.load(snapshot,map_location='cpu',weights_only=False)
        state=saved['model']
        if len(state)!=21 or not state[17]:
            raise ValueError('Expected pinned official rotated 4D capture tuple')
        indices={'_xyz':1,'_features_dc':2,'_features_rest':3,'_scaling':4,'_rotation':5,
                 '_opacity':6,'_t':14,'_scaling_t':15,'_rotation_r':16}
        weights={key:state[i].detach().cpu() for key,i in indices.items()}
        weights.update(active_sh_degree=state[0],active_sh_degree_t=state[19],coefficient_state=state[20])
        manifest=read(ROOT/f'data/4c4d_full_001/{args.dataset}/edge_1280/manifest.json')
        step=saved['step']
        dest=folder/f'step_{step:06d}_continuous_model.pth'
        packet={'schema_version':1,'method':'4c4d','source_commit':saved['setup']['source_commit'],
                'weights':weights,'setup':saved['setup'],'normalization':manifest['normalization'],
                'cameras':manifest['cameras'],'time_origin_pts_s':manifest['frames'][0]['pts_s'],
                'time_span_s':manifest['frames'][-1]['pts_s']-manifest['frames'][0]['pts_s'],'step':step}
        if not dest.exists():torch.save(packet,dest)
        digest=hashlib.sha256(dest.read_bytes()).hexdigest()
        record={'model':str(dest.relative_to(ROOT)).replace('\\','/'),'sha256':digest,
                'step':step,'edge':1280,'gaussians':len(weights['_xyz']),
                'status':'intermediate full-duration checkpoint; not final or 4K-refined',
                'source':'Saved optimizer checkpoint, CPU export with official capture layout; no training images or discrete frame models.'}
        registry_path=experiment/'preview_models.json'
        registry=read(registry_path) if registry_path.exists() else {'schema_version':1,'experiment_id':'4c4d_full_001','datasets':{}}
        registry['datasets'][args.dataset]=record
        registry_path.write_text(json.dumps(registry,indent=2)+'\n',encoding='utf8')
        (ROOT/f'documentation/4c4d_full_001/{args.dataset}_preview_export.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
        print(json.dumps(record,indent=2))
    finally:
        snapshot.unlink(missing_ok=True)

if __name__=='__main__':main()
