"""CPU diagnostic of unsupported Gaussian geometry against current-capture SfM."""
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
manifest=json.loads((r.WORK/'manifest.json').read_text());points=[]
with (Path(manifest['dataset'])/'sparse/points3D.bin').open('rb') as f:
    for _ in range(r.unpack(f,'Q')[0]):
        v=r.unpack(f,'QdddBBBdQ');f.seek(v[-1]*8,1)
        if v[-1]>=4 and v[-2]<1.5:points.append(v[1:4])
points=np.array(points);tree=cKDTree(points);spacing=tree.query(points,k=8,workers=6)[0][:,1:].mean(1)
entry=manifest['files'][2];data,_,_=r.read_ply(Path(entry['path']));xyz=np.stack([data[x] for x in ['x','y','z']],axis=1)
distance,nearest=tree.query(xyz,workers=6);local=spacing[nearest]
scales=np.sort(np.exp(np.stack([data[x] for x in ['scale_0','scale_1','scale_2']],axis=1)),axis=1)
opacity=1/(1+np.exp(-np.clip(data['opacity'],-30,30)));needle=scales[:,2]/np.maximum(scales[:,1],1e-8)
centers=np.array([np.linalg.inv(v['view'])[:3,3] for v in manifest['views']]);extent=np.median(np.linalg.norm(centers-centers.mean(0),axis=1))
candidates=(distance>np.maximum(local*4,scales[:,1]*3))&((opacity<.2)|(needle>12)|(scales[:,2]>extent*.03))
stats=dict(trusted_sfm_points=len(points),gaussians=len(data),extent=float(extent),candidates=int(candidates.sum()),
    opacity_percentiles=np.quantile(opacity,[.01,.1,.5,.9,.99]).tolist(),scale_percentiles=np.quantile(scales[:,2],[.5,.9,.99,.999]).tolist(),
    candidate_distance_median=float(np.median(distance[candidates])) if candidates.any() else 0)
r.write_json(r.DOCS/'sfm_support_diagnostic.json',stats)
np.savez(r.WORK/'sfm_support_2m.npz',distance=distance,local_spacing=local,candidates=candidates,opacity=opacity,major_scale=scales[:,2],needle=needle,extent=extent)
print(json.dumps(stats,indent=2),flush=True)
