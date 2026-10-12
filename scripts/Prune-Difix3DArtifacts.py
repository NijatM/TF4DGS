"""Test SfM-guided artifact pruning after Difix3D, retaining originals."""
import argparse
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path
import re
import numpy as np
from scipy.spatial import cKDTree
import torch

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--index',type=int,default=2);p.add_argument('--recipe',default='wide_strong');p.add_argument('--level',choices=['conservative','balanced','strong'],default='balanced');a=p.parse_args()
manifest=json.loads((r.WORK/'manifest.json').read_text());entry=dict(manifest['files'][a.index]);entry['recipe']=a.recipe
source=r.WORK/'tuning'/entry['folder']/(Path(entry['name']).stem+'_'+a.recipe+'_Difix3D.ply')
directory=r.WORK/entry['folder']/(Path(entry['name']).stem+'_'+a.recipe)
target=r.WORK/'tuning'/entry['folder']/(Path(entry['name']).stem+'_'+a.recipe+'_pruned_'+a.level+'_Difix3D.ply')
if target.exists():raise FileExistsError(target)
points=[]
with (Path(manifest['dataset'])/'sparse/points3D.bin').open('rb') as f:
    for _ in range(r.unpack(f,'Q')[0]):
        v=r.unpack(f,'QdddBBBdQ');f.seek(v[-1]*8,1)
        if v[-1]>=4 and v[-2]<1.5:points.append(v[1:4])
points=np.array(points);tree=cKDTree(points);spacing=tree.query(points,k=8,workers=6)[0][:,1:].mean(1)
data,names,header=r.read_ply(source);xyz=np.stack([data[x] for x in ['x','y','z']],axis=1).astype(float)
alignment=entry.get('alignment')
if alignment:xyz=(xyz-np.array(alignment['translation']))@np.array(alignment['rotation'])/alignment['scale']
distance,nearest=tree.query(xyz,workers=6);local=spacing[nearest]
scales=np.sort(np.exp(np.stack([data[x] for x in ['scale_0','scale_1','scale_2']],axis=1)),axis=1)
opacity=1/(1+np.exp(-np.clip(data['opacity'],-30,30)));needle=scales[:,2]/np.maximum(scales[:,1],1e-8)
centers=np.array([np.linalg.inv(v['view'])[:3,3] for v in manifest['views']]);extent=np.median(np.linalg.norm(centers-centers.mean(0),axis=1))
threshold=3 if a.level=='strong' else 4
cut=(distance>np.maximum(local*threshold,scales[:,1]*3))&((opacity<(.35 if a.level=='strong' else .2))|(needle>(8 if a.level=='strong' else 12))|(scales[:,2]>extent*(.02 if a.level=='strong' else .03)))
if a.level=='conservative':cut&=distance>extent*.25
keep=~cut;removed=int(cut.sum())
if not 0<removed<len(data)*.12:raise ValueError(f'Unexpected pruning amount {removed}; inspect before proceeding')
targets=json.loads((directory/'targets.json').read_text());audit=[x for x in targets['records'] if x['kind']=='audit']
review_dir=directory.with_name(directory.name+'_pruned_'+a.level);review_dir.mkdir(exist_ok=True)
model,layout=r.load_model(source)
before,images_before=r.evaluate(model,audit,targets['edge'],review_dir,'unpruned')
ids=torch.tensor(np.flatnonzero(keep),device='cuda');model={k:v[ids].contiguous() for k,v in model.items()}
after,images_after=r.evaluate(model,audit,targets['edge'],review_dir,'pruned')
drop=after['mean_psnr']-before['mean_psnr']
accepted=drop>=-.25 and after['mean_support_psnr']-before['mean_support_psnr']>=-.25
newheader=re.sub(rb'element vertex \d+',f'element vertex {int(keep.sum())}'.encode(),header)
r.export(target,model,(np.array(data[keep],copy=True),names,newheader))
record=dict(method='Difix3D plus SfM-guided artifact pruning',source=source.name,output=target.name,
    source_sha256=r.sha(source),output_sha256=r.sha(target),original_sha256=entry['sha256'],
    before_pruning=before,after_pruning=after,removed=removed,remaining=int(keep.sum()),level=a.level,
    camera_audit_pass=accepted,source_camera_change_db=drop,scope='Extra geometric filter, not part of official Difix3D. Lack of sparse SfM support does not prove a point is false; visual review and source audit remain necessary.')
r.write_json(target.with_suffix('.difix3d.json'),record);np.save(review_dir/'removed_source_indices.npy',np.flatnonzero(cut))
evidence=entry['folder']+'_'+review_dir.name+'_camera_comparison.jpg'
r.montage(r.DOCS/evidence,[[audit[i]['target'],images_before[i],images_after[i]] for i in range(3)],['Photograph','Stronger Difix3D','After support-guided pruning'])
r.stage('Artifact pruning test: '+entry['name'],f'{removed:,} unsupported candidates removed ({removed/len(data):.2%}); camera audit change {drop:+.3f} dB. This is an additional SfM-support filter, not diffusion alone.',[evidence],status='camera audit passed; inspect wide views' if accepted else 'rejected camera audit')
entry['output']=str(target);r.stress(entry,manifest,review_dir)
# Independently reload export and reproduce audit scores.
del model;torch.cuda.empty_cache();model,_=r.load_model(target)
reopened,_=r.evaluate(model,audit,targets['edge'],review_dir,'reopened')
if abs(reopened['mean_psnr']-after['mean_psnr'])>1e-4:raise ValueError('Pruned export differs from tested model')
record['reopened_ply_verified']=True;r.write_json(target.with_suffix('.difix3d.json'),record)
print(json.dumps(dict(level=a.level,removed=removed,change_db=drop,camera_audit_pass=accepted,output=target.name)),flush=True)
