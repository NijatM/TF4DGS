"""Verify every cleaned Gaussian's identity in its unedited source PLY (CPU).

Identity maps allow a validated source repair to be carried into existing crops
without training unrelated geometry or undoing the user's rotations/deletions.
"""
import argparse
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
import torch
from gsplat.cuda._torch_impl import _eval_sh_bases_fast

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)

def sh_rotation(Q):
    dirs=np.random.default_rng(777).normal(size=(128,3));dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    basis=_eval_sh_bases_fast(16,torch.tensor(dirs,dtype=torch.float64)).numpy()
    rotated=_eval_sh_bases_fast(16,torch.tensor(dirs@Q,dtype=torch.float64)).numpy()
    matrix=np.linalg.lstsq(basis,rotated,rcond=None)[0]
    error=np.max(np.abs(basis@matrix-rotated))
    if error>1e-10:raise ValueError('SH rotation fit failed')
    return matrix

def run(folder):
    manifest=json.loads((r.WORK/'manifest.json').read_text());entries=[x for x in manifest['files'] if x['folder']==folder]
    raw=next(x for x in entries if x['name'].startswith('splat_'))
    data,_,_=r.read_ply(Path(raw['path']));attrs=['f_dc_0','f_dc_1','f_dc_2','opacity']
    tree=cKDTree(np.stack([data[n] for n in attrs],axis=1));reports=[]
    for entry in entries:
        if entry is raw:continue
        variant,_,_=r.read_ply(Path(entry['path']));align=entry['alignment'];Q=np.array(align['rotation']);s=align['scale'];t=np.array(align['translation'])
        mapping=np.empty(len(variant),dtype=np.int32);max_feature=0.;max_residual=0.
        for start in range(0,len(variant),100000):
            end=min(start+100000,len(variant));feat=np.stack([variant[n][start:end] for n in attrs],axis=1)
            distances,ids=tree.query(feat,k=4,workers=6)
            xyz=np.stack([variant[n][start:end] for n in ['x','y','z']],axis=1)
            rawxyz=np.stack([data[n][ids] for n in ['x','y','z']],axis=2)
            residual=np.linalg.norm(s*rawxyz@Q.T+t-xyz[:,None,:],axis=2)
            residual[distances>1e-5]=np.inf
            choice=residual.argmin(1);chosen=ids[np.arange(end-start),choice]
            err=residual[np.arange(end-start),choice]
            if not np.isfinite(err).all() or err.max()>5e-4:raise ValueError(f'Gaussian identity is ambiguous or edited: {entry["name"]}; largest position residual {err.max()}')
            mapping[start:end]=chosen;max_feature=max(max_feature,float(distances[np.arange(end-start),choice].max()));max_residual=max(max_residual,float(err.max()))
        # Repeated identical source attributes can denote genuinely duplicated
        # Gaussians. Validate them by position; report repeated identity matches.
        sample=np.random.default_rng(888).choice(len(mapping),min(3000,len(mapping)),replace=False);rawids=mapping[sample]
        A=Rotation.from_quat(np.stack([data['rot_'+str(i)][rawids] for i in [1,2,3,0]],axis=1)).as_matrix()
        B=Rotation.from_quat(np.stack([variant['rot_'+str(i)][sample] for i in [1,2,3,0]],axis=1)).as_matrix()
        aa=np.exp(np.stack([data['scale_'+str(i)][rawids] for i in range(3)],axis=1))*s
        bb=np.exp(np.stack([variant['scale_'+str(i)][sample] for i in range(3)],axis=1))
        covA=(A*aa[:,None,:]**2)@A.transpose(0,2,1);covB=(B*bb[:,None,:]**2)@B.transpose(0,2,1)
        expected=Q@covA@Q.T
        covariance_relative=np.linalg.norm(covB-expected,axis=(1,2))/np.linalg.norm(expected,axis=(1,2)).clip(1e-20)
        shfields=['f_dc_'+str(i) for i in range(3)]+['f_rest_'+str(i) for i in range(45)]
        rawsh=np.concatenate((np.stack([data[n][rawids] for n in shfields[:3]],axis=1)[:,None,:],np.stack([data[n][rawids] for n in shfields[3:]],axis=1).reshape(-1,3,15).transpose(0,2,1)),axis=1)
        variants=np.concatenate((np.stack([variant[n][sample] for n in shfields[:3]],axis=1)[:,None,:],np.stack([variant[n][sample] for n in shfields[3:]],axis=1).reshape(-1,3,15).transpose(0,2,1)),axis=1)
        transformed=np.einsum('ij,njc->nic',sh_rotation(Q),rawsh)
        rotated_error=float(np.mean(np.abs(variants-transformed)));unrotated_error=float(np.mean(np.abs(variants-rawsh)))
        sh_mode='rotated' if rotated_error<unrotated_error else 'unrotated'
        if min(rotated_error,unrotated_error)>2e-4:raise ValueError('Variant SH edits require a separate repair: '+entry['name'])
        if np.quantile(covariance_relative,.99)>1e-3:raise ValueError('Variant covariance edits require separate repair: '+entry['name'])
        path=r.WORK/entry['folder']/(Path(entry['name']).stem+'_identity_map.npy');np.save(path,mapping)
        record=dict(input=entry['name'],folder=folder,matched=len(mapping),unique_source_matches=len(np.unique(mapping)),max_attribute_residual=max_feature,max_geometry_residual=max_residual,covariance_relative_p99=float(np.quantile(covariance_relative,.99)),sh_mode=sh_mode,rotated_sh_error=rotated_error,unrotated_sh_error=unrotated_error,source_sha256=entry['sha256'],raw_source_sha256=raw['sha256'])
        r.write_json(path.with_suffix('.json'),record);reports.append(record);print(json.dumps(record),flush=True)
    r.write_json(r.DOCS/(folder+'_identity_maps.json'),reports)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',default='MRNF_2m-90k');run(p.parse_args().folder)
