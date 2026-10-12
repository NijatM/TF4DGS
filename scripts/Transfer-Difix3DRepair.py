"""Carry a reviewed raw-model repair into verified source subsets/rotations.

Does not reintroduce deleted Gaussians, overwrite originals or replace previous
repairs. Publish is a separate explicit invocation after inspecting prototypes.
"""
import argparse
import gc
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path
import shutil
import numpy as np
from scipy.spatial.transform import Rotation
import torch

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
spec2=spec_from_file_location('maps',ROOT/'scripts/Create-Difix3DVariantMaps.py');maps=module_from_spec(spec2);spec2.loader.exec_module(maps)

def run(a):
    torch.set_num_threads(6)
    manifest=json.loads((r.WORK/'manifest.json').read_text());source=Path(a.source)
    source_record=json.loads(source.with_suffix('.difix3d.json').read_text())
    if not source_record.get('reopened_ply_verified') or r.sha(source)!=source_record['output_sha256']:raise ValueError('Source repair not verified')
    if source_record.get('quality_decision','').startswith('rejected'):raise ValueError('Source repair was explicitly rejected')
    if source_record.get('starting_model_sha256'):
        starting=None
        for candidate in source.parent.glob('*.difix3d.json'):
            candidate_record=json.loads(candidate.read_text())
            if candidate_record.get('output_sha256')==source_record['starting_model_sha256']:
                starting=candidate_record;break
        if starting is None:raise ValueError('Starting model provenance missing')
        source_record['starting_recipe_provenance']=starting
    raw=next(x for x in manifest['files'] if x['name']==source_record['input'] and x['sha256']==source_record['source_sha256'])
    entries=[x for i,x in enumerate(manifest['files']) if i in a.indices]
    if any(x['folder']!=raw['folder'] for x in entries):raise ValueError('Cannot transfer between separately trained source families')
    for entry0 in entries:
        entry=dict(entry0);stem=Path(entry['name']).stem
        output=r.WORK/'selected'/entry['folder']/(stem+'_Refined_Difix3D.ply');output.parent.mkdir(parents=True,exist_ok=True)
        directory=r.WORK/entry['folder']/(stem+'_selected_refined');directory.mkdir(parents=True,exist_ok=True)
        if a.publish:
            record=json.loads(output.with_suffix('.difix3d.json').read_text())
            if not record.get('reopened_ply_verified') or not record.get('camera_audit_pass'):raise ValueError('Unverified or rejected prototype')
            if r.sha(output)!=record['output_sha256'] or r.sha(Path(entry['path']))!=entry['sha256']:raise ValueError('Hash changed')
            final=Path(entry['path']).with_name(output.name)
            if final.exists():raise FileExistsError('Refusing to overwrite '+str(final))
            temporary=final.with_suffix('.ply.tmp');shutil.copyfile(output,temporary)
            if r.sha(temporary)!=record['output_sha256']:raise ValueError('Copy failed verification')
            temporary.rename(final);r.write_json(final.with_suffix('.difix3d.json'),record)
            r.stage('Stronger repair published: '+entry['name'],f'{final.name} saved alongside the original and the first pass. Original and copied-output hashes verified.',status='reviewed prototype published')
            print(str(final),flush=True);continue
        if output.exists():raise FileExistsError(output)
        if entry['name']==raw['name']:
            shutil.copyfile(source,output)
        else:
            path=r.WORK/entry['folder']/(stem+'_identity_map.npy');mapping=np.load(path);identity=json.loads(path.with_suffix('.json').read_text())
            if identity['source_sha256']!=entry['sha256'] or identity['raw_source_sha256']!=raw['sha256']:raise ValueError('Identity map does not match sources')
            if identity['unique_source_matches']!=len(mapping):raise ValueError('Ambiguous subset identity')
            alignment=entry['alignment'];Q=np.array(alignment['rotation']);s=alignment['scale']
            original,layout=r.load_model(Path(entry['path']));old,_=r.load_model(Path(raw['path']));fixed,_=r.load_model(source)
            ids=torch.tensor(mapping.astype(np.int64),device='cuda');q=torch.tensor(Q,device='cuda',dtype=torch.float32)
            original['means']+=s*(fixed['means'][ids]-old['means'][ids])@q.T
            original['scales']+=fixed['scales'][ids]-old['scales'][ids]
            original['opacities']+=fixed['opacities'][ids]-old['opacities'][ids]
            # Apply the repaired orientation change in the variant's frame,
            # preserving original quaternion signs/equivalent orientation edits.
            qa=old['quats'][ids].cpu().numpy()[:,[1,2,3,0]];qb=fixed['quats'][ids].cpu().numpy()[:,[1,2,3,0]];qv=original['quats'].cpu().numpy()[:,[1,2,3,0]]
            for start in range(0,len(mapping),100000):
                end=min(start+100000,len(mapping));A=Rotation.from_quat(qa[start:end]);B=Rotation.from_quat(qb[start:end]);V=Rotation.from_quat(qv[start:end]);R=Rotation.from_matrix(Q)
                updated=(R*B*A.inv()*R.inv()*V).as_quat()[:,[3,0,1,2]].copy()
                original['quats'][start:end]=torch.tensor(updated,device='cuda',dtype=torch.float32)
            original['sh0']+=fixed['sh0'][ids]-old['sh0'][ids]
            matrix=maps.sh_rotation(Q)[1:,1:] if identity['sh_mode']=='rotated' else np.eye(15)
            shQ=torch.tensor(matrix,device='cuda',dtype=torch.float32)
            for start in range(0,len(mapping),100000):
                end=min(start+100000,len(mapping));index=ids[start:end]
                original['shN'][start:end]+=torch.einsum('ij,njc->nic',shQ,fixed['shN'][index]-old['shN'][index])
            r.export(output,original,layout)
            del original,old,fixed,layout,ids;gc.collect();torch.cuda.empty_cache()
        templates=json.loads((r.WORK/entry['folder']/stem/'targets.json').read_text());audit=[x for x in templates['records'] if x['kind']=='audit']
        original,_=r.load_model(Path(entry['path']));before,images_before=r.evaluate(original,audit,templates['edge'],directory,'original');del original;gc.collect();torch.cuda.empty_cache()
        first,_=r.load_model(Path(entry['output']));prior,images_prior=r.evaluate(first,audit,templates['edge'],directory,'first_pass');del first;gc.collect();torch.cuda.empty_cache()
        m,_=r.load_model(output);after,images_after=r.evaluate(m,audit,templates['edge'],directory,'selected')
        accepted=after['mean_support_psnr']>=before['mean_support_psnr'] and after['mean_support_psnr']>=prior['mean_support_psnr']-.25
        record=dict(input=entry['name'],output=output.name,source_sha256=entry['sha256'],output_sha256=r.sha(output),original_preserved=r.sha(Path(entry['path']))==entry['sha256'],gaussians=entry['count'],recipe=source_record.get('recipe'),raw_repair=source.name,raw_repair_sha256=source_record['output_sha256'],raw_recipe_provenance=source_record,camera_alignment=entry.get('alignment'),before=before,first_pass=prior,after=after,camera_audit_pass=accepted,reopened_ply_verified=True,scope='Repair deltas transferred through verified one-to-one source Gaussian identities and exact SH rotation. Existing subsets/crops retained; no deleted geometry reintroduced. Camera metrics do not prove complete novel-view repair.')
        r.write_json(output.with_suffix('.difix3d.json'),record);r.write_json(r.DOCS/(entry['folder']+'_'+stem+'_selected_result.json'),record)
        evidence=entry['folder']+'_'+stem+'_selected_comparison.jpg'
        r.montage(r.DOCS/evidence,[[images_before[i],images_prior[i],images_after[i]] for i in range(3)],['Original PLY','First Difix3D pass','Selected stronger repair'])
        r.stage('Stronger repair comparison: '+entry['name'],f'Support camera audit original {before["mean_support_psnr"]:.3f}, first pass {prior["mean_support_psnr"]:.3f}, selected {after["mean_support_psnr"]:.3f} dB. {entry["count"]:,} Gaussians; crop preserved.',[evidence],status='camera audit passed; visual review pending' if accepted else 'camera audit rejected')
        del m;gc.collect();torch.cuda.empty_cache()
        entry['output']=str(output);r.stress(entry,manifest,directory)
        print(json.dumps(dict(input=entry['name'],camera_audit_pass=accepted,support_psnr=after['mean_support_psnr'])),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--indices',nargs='+',type=int,default=[0,1,2]);p.add_argument('--publish',action='store_true');a=p.parse_args()
    try:run(a)
    except Exception as e:r.stage('Repair transfer failed',str(e),status='failed; originals preserved');raise
