"""Recover cleaned PLY edit transforms from preserved per-Gaussian attributes."""
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path
import shutil
import numpy as np
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
manifest=json.loads((r.WORK/'manifest.json').read_text());trees={};sources={};reports=[]


def fit(x,y):
    xc=x-x.mean(0);yc=y-y.mean(0)
    u,s,vt=np.linalg.svd(yc.T@xc);d=np.eye(3);d[2,2]=np.linalg.det(u@vt)
    rotation=u@d@vt;scale=float(np.sum(s*np.diag(d))/np.sum(xc*xc))
    translation=y.mean(0)-scale*rotation@x.mean(0)
    return scale,rotation,translation


for entry in manifest['files']:
    folder=entry['folder'];raw_name='splat_90000.ply' if folder=='MRNF_2m-90k' else 'splat_210000.ply'
    if folder not in trees:
        data,_,_=r.read_ply(Path(entry['path']).parent/raw_name)
        features=np.stack([data[n] for n in ('f_dc_0','f_dc_1','f_dc_2','opacity')],axis=1)
        trees[folder]=cKDTree(features);sources[folder]=data
    data,_,_=r.read_ply(Path(entry['path']));ids=np.random.default_rng(123).choice(len(data),min(3000,len(data)),replace=False)
    features=np.stack([data[n][ids] for n in ('f_dc_0','f_dc_1','f_dc_2','opacity')],axis=1)
    distance,matched=trees[folder].query(features)
    good=distance<1e-5
    if good.sum()<100:raise ValueError('Insufficient preserved Gaussian attributes: '+entry['name'])
    raw=sources[folder];x=np.stack([raw[n][matched[good]] for n in ('x','y','z')],axis=1).astype(float)
    y=np.stack([data[n][ids[good]] for n in ('x','y','z')],axis=1).astype(float)
    tolerance=max(1e-5,float(np.median(np.linalg.norm(y-np.median(y,axis=0),axis=1)))*2e-5)
    rng=np.random.default_rng(321);best=None
    for _ in range(100):
        selection=rng.choice(len(x),3,replace=False);scale,Q,t=fit(x[selection],y[selection])
        error=np.linalg.norm(x@(scale*Q).T+t-y,axis=1);inliers=error<tolerance
        if best is None or inliers.sum()>best.sum():best=inliers
    if best.sum()<100 or best.mean()<.85:raise ValueError('No reliable edit transform: '+entry['name'])
    scale,Q,t=fit(x[best],y[best]);error=np.linalg.norm(x[best]@(scale*Q).T+t-y[best],axis=1)
    transform=np.eye(4);transform[:3,:3]=scale*Q;transform[:3,3]=t
    alignment=dict(scale=scale,rotation=Q.tolist(),translation=t.tolist(),matrix=transform.tolist(),
        matched_attributes=int(good.sum()),inliers=int(best.sum()),residual_p99=float(np.quantile(error,.99)))
    changed=not np.allclose(transform,np.eye(4),atol=1e-5)
    previously_aligned=entry.get('alignment') is not None and np.allclose(np.array(entry['alignment']['matrix']),transform,atol=1e-6)
    entry['alignment']=alignment
    directory=r.WORK/folder/Path(entry['name']).stem
    if changed and not previously_aligned and directory.exists():
        archive=directory.with_name(directory.name+'_failed_unaligned_01')
        if archive.exists():raise FileExistsError(archive)
        directory.rename(archive)
        output=Path(entry['output']);provenance=output.with_suffix('.difix3d.json')
        if output.exists():
            record=json.loads(provenance.read_text())
            if record['output_sha256']!=r.sha(output):raise ValueError('Generated output changed; preserve and inspect')
            # Move only our verified generated files. Original PLYs are untouched.
            shutil.move(str(output),str(archive/output.name));shutil.move(str(provenance),str(archive/provenance.name))
        r.stage('Failed camera alignment: '+entry['name'],'Cleaned export has a scene edit transform. Unaligned attempts/output were archived; original remains untouched. Recovered transform will be applied to cameras before rerunning.',status='failed attempt retained; alignment corrected')
    reports.append(dict(name=entry['name'],folder=folder,requires_camera_transform=changed,**alignment))
    print(entry['name'], 'scale',round(scale,6),'inliers',int(best.sum()),'p99',float(np.quantile(error,.99)),flush=True)
r.write_json(r.WORK/'manifest.json',manifest);r.write_json(r.DOCS/'variant_alignment.json',reports)
r.stage('Edited variants aligned to their capture cameras','Recovered per-variant similarity transforms from unchanged Gaussian color/opacity correspondences. All fits passed >=85% inliers and geometry residual checks. Cameras move into each edited PLY frame; splats retain user edits.',status='alignment verified')
