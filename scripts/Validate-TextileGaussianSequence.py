"""Check model/timeline invariants and exercise the real local Gaussian renderer."""
import argparse
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import io
import numpy as np
from PIL import Image


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--port',type=int,default=8104);p.add_argument('--allow-partial',action='store_true')
    p.add_argument('--output',default='.local/workflows/dynamic_setup/textile_reconstruction_02/validation.json');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];sequence=json.loads(Path(a.sequence).read_text(encoding='utf-8-sig'));frames=sequence['frames']
    if not a.allow_partial:
        assert sequence['status']=='complete';assert [f['index'] for f in frames]==sequence['requested_indexes']
    assert len(set(f['index'] for f in frames))==len(frames)
    assert all(b['time_s']>a1['time_s'] for a1,b in zip(frames,frames[1:]))
    assert sequence['persistent_material_ids'] is False and sequence['time_interpolation'] is False
    checks=[]
    for frame in frames:
        modelpath=root/frame['model'];data=np.load(modelpath);count=len(data['means'])
        assert count==frame['gaussians']
        assert all(len(data[k])==count and np.isfinite(data[k]).all() for k in data.files)
        assert np.all(data['scales']>0) and np.all((data['opacity']>=0)&(data['opacity']<=1))
        assert np.all((data['colors']>=0)&(data['colors']<=1))
        assert np.max(np.abs(np.linalg.norm(data['quats'],axis=1)-1))<2e-5
        # Verify the standard binary 3DGS export remains usable independently.
        ply=modelpath.with_name('snapshot.ply')
        with ply.open('rb') as stream:
            header=[]
            while True:
                line=stream.readline().decode('ascii').strip();header.append(line)
                assert len(header)<100
                if line=='end_header':break
            assert header[:2]==['ply','format binary_little_endian 1.0']
            assert f'element vertex {count}' in header
            properties=[line.split()[-1] for line in header if line.startswith('property float ')]
            assert len(properties)==17
            assert ply.stat().st_size==stream.tell()+count*17*4
            values=np.frombuffer(stream.read(17*4*min(count,10)),dtype='<f4').reshape(-1,17)
            assert np.allclose(values[:,:3],data['means'][:len(values)],atol=1e-7)
            assert np.allclose(values[:,6:9]*.28209479177387814+.5,data['colors'][:len(values)],atol=1e-6)
        observation=(root/frame['model']).with_name('observed_appearance.npz')
        appearance_checked=False
        if observation.exists():
            with np.load(observation) as appearance:
                assert appearance['colors'].shape==(count,3) and appearance['visible_views'].shape==(count,)
                assert np.isfinite(appearance['colors']).all() and np.all((appearance['colors']>=0)&(appearance['colors']<=1))
                assert np.all((appearance['visible_views']>=0)&(appearance['visible_views']<=3))
                appearance_checked=True
        elif not a.allow_partial:raise AssertionError('Recorded appearance samples are unfinished')
        checks.append(dict(index=frame['index'],gaussians=count,ply_checked=True,recorded_appearance_checked=appearance_checked))
    base=f'http://127.0.0.1:{a.port}'
    meta=json.load(urllib.request.urlopen(base+'/api/meta',timeout=30));renders=[]
    for target in [0,158,266,425]:
        frame=min(frames,key=lambda f:abs(f['index']-target))
        for mode in ['rgb','geometry','color','combined']:
            q=urllib.parse.urlencode(dict(frame=frame['index'],mode=mode,camera='orbit',azimuth=95,elevation=48))
            with urllib.request.urlopen(base+'/api/render?'+q,timeout=60) as response:
                image=Image.open(io.BytesIO(response.read())).convert('RGB');pixels=np.asarray(image)
                assert image.width>=800 and image.height>=400 and pixels.std()>8
                renders.append(dict(index=frame['index'],mode=mode,size=image.size,field_status=response.headers.get('X-TF4DGS-Field-Status')))
    rejected=[]
    recent=[]
    for mode in ['geometry','color']:
        frame=min(frames,key=lambda f:abs(f['index']-158))
        expected=max((f for f in frames if f['time_s']<=max(frames[0]['time_s'],frame['time_s']-5)),key=lambda f:f['time_s'])
        q=urllib.parse.urlencode(dict(frame=frame['index'],mode=mode,reference='recent',history=5,camera='orbit'))
        with urllib.request.urlopen(base+'/api/render?'+q,timeout=60) as response:
            status=response.headers.get('X-TF4DGS-Field-Status')
            assert f"t={expected['time_s']:.3f}s" in status
            Image.open(io.BytesIO(response.read())).verify()
            recent.append(dict(mode=mode,index=frame['index'],reference_index=expected['index'],reference_time_s=expected['time_s'],field_status=status))
    for query in ['frame=-1','mode=invalid','distance=nan&camera=orbit','camera=unknown','maximum=0','reference=invalid','history=0']:
        try:urllib.request.urlopen(base+'/api/render?'+query,timeout=30);raise AssertionError('Invalid query accepted')
        except urllib.error.HTTPError as e:assert e.code==400;rejected.append(query)
    result=dict(status='passed',models_checked=checks,completed_frames=len(frames),requested_frames=len(sequence['requested_indexes']),
                partial=a.allow_partial,renders=renders,recent_reference_checks=recent,invalid_queries_rejected=rejected,
                metric_accuracy_verified=False,claim='Finite actual Gaussian models and timeline/API behavior; no independent geometry accuracy certificate.')
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(status='passed',models=len(frames),renders=len(renders))))


if __name__=='__main__':main()
