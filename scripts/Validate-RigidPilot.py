"""Validate real pilot exports, renderer responses and missing-data behavior."""
import argparse
import ast
import io
import json
from pathlib import Path
import re
import subprocess
from urllib.error import HTTPError
from urllib.request import urlopen

import numpy as np
from PIL import Image


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model-dir',type=Path,default=Path('outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid'))
    p.add_argument('--cpu-python',default='C:/Users/mnijat/miniconda3/envs/tf4dgs/python.exe')
    p.add_argument('--base-url',default='http://127.0.0.1:8100');args=p.parse_args()
    if args.output.exists():raise ValueError('Preserve earlier validation records')
    if not args.base_url.startswith('http://127.0.0.1:'):raise ValueError('Only the local pilot may be validated')
    model=np.load(args.model_dir/'canonical_actor.npz');n=len(model['means'])
    for key,shape in [('means',(n,3)),('colors',(n,3)),('scales',(n,3)),('quats',(n,4)),('opacity',(n,))]:
        assert model[key].shape==shape and np.isfinite(model[key]).all(),key
    assert (model['scales']>0).all() and np.allclose(np.linalg.norm(model['quats'],axis=1),1,atol=1e-5)
    for key in ['opacity','colors']:assert ((model[key]>=0)&(model[key]<=1)).all()
    motion=json.loads((args.model_dir/'motion.json').read_text());poses=json.loads(Path(motion['poses']).read_text())
    if motion.get('canonical_calibration'):
        assert motion['canonical_calibration']==poses['canonical_calibration'],'Mixed canonical calibrations'
        config=json.loads((args.model_dir/'training_config.json').read_text())
        session_path=Path(config['session']);session=json.loads(session_path.read_text(encoding='utf-8-sig'))
        assert poses['camera_calibrations']=={c['id']:c['calibration'] for c in session['cameras']}
        initialization=json.loads((args.model_dir/'initialization.json').read_text())
        calibration=json.loads((Path(motion['canonical_calibration'])/'summary.json').read_text())
        assert initialization['lid_height_m']==calibration['estimated_lid_height_m']
        if calibration.get('measured_lid_diameter_mm') is not None:
            assert initialization['radius_m']*2000==calibration['measured_lid_diameter_mm']
    valid=[i for i,pose in enumerate(poses['frames']) if pose and pose['valid']]
    assert motion['persistent_ids']==list(range(n)) and motion['valid_indices']==valid and not motion['interpolate_missing']
    with (args.model_dir/'canonical_actor.ply').open('rb') as stream:
        header=[]
        while True:
            line=stream.readline().decode('ascii').strip();header.append(line)
            if line=='end_header':break
            if not line:raise ValueError('Invalid PLY header')
        assert f'element vertex {n}' in header and len([line for line in header if line.startswith('property float ')])==17
        values=np.frombuffer(stream.read(),dtype='<f4').reshape(n,17)
    assert np.isfinite(values).all() and np.array_equal(values[:,:3],model['means'])
    assert np.allclose(values[:,6:9]*.28209479177387814+.5,model['colors'],atol=1e-6)
    assert np.allclose(np.exp(values[:,10:13]),model['scales'],rtol=1e-5)
    with urlopen(args.base_url+'/api/meta',timeout=30) as response:meta=json.load(response)
    assert meta['gaussians']==n and meta['frames'][0]['index']==valid[0]
    assert Path(meta['source']).resolve()==(args.model_dir/'canonical_actor.npz').resolve()
    renders=[]
    for index in [valid[0],valid[-1]]:
        for mode in ['rgb','displacement','recent']:
            url=args.base_url+f'/api/render?frame={index}&mode={mode}&follow=0&distance=.55&history=3'
            with urlopen(url,timeout=30) as response:
                raw=response.read();status=response.headers.get('X-TF4DGS-Field-Status')
            with Image.open(io.BytesIO(raw)) as image:
                assert image.size==(900,650);pixels=np.array(image)
            assert pixels.std()>1,'Blank render'
            if mode=='recent' and index==valid[0]:assert status=='no contiguous motion history'
            else:assert status=='supported'
            renders.append({'frame':index,'mode':mode,'image_size':[900,650],'field_status':status,'bytes':len(raw)})
    rejected=[]
    for query in ['frame=0','frame='+str(valid[0])+'&mode=unknown','frame='+str(valid[0])+'&history=0']:
        try:
            with urlopen(args.base_url+'/api/render?'+query,timeout=30):pass
            raise AssertionError('Invalid/unsupported query was accepted')
        except HTTPError as error:
            assert error.code==400;rejected.append({'query':query,'http_status':error.code})
    sources=0
    for directory in ['scripts','src','tests']:
        for path in Path(directory).rglob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path));sources+=1
    tests=subprocess.run([args.cpu_python,'-m','unittest','discover','-s','tests'],capture_output=True,text=True)
    result_text=tests.stdout+tests.stderr
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.with_suffix('.tests.txt').write_text(result_text,encoding='utf-8')
    assert tests.returncode==0,result_text
    match=re.search(r'Ran (\d+) tests',result_text);assert match
    native=json.loads(Path('.local/workflows/dynamic_setup/real_pixel_verification.json').read_text())
    assert native['status']=='passed' and len(native['checks'])==6
    pins=subprocess.run(['git','submodule','status'],capture_output=True,text=True,check=True).stdout.strip().splitlines()
    assert all(not line.startswith(('+','-','U')) for line in pins),pins
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stdout+diff.stderr
    tracked=subprocess.run(['git','ls-files','--','data','outputs','.local/workflows'],capture_output=True,text=True,check=True).stdout
    assert not tracked.strip(),'Data/models/logs accidentally tracked'
    report={'status':'passed','gaussians':n,'ply_matches_canonical_model':True,'persistent_ids_and_pose_validity':True,
       'live_render_checks':renders,'rejected_queries':rejected,'python_sources_parsed':sources,
       'foundation_tests':int(match.group(1)),'independent_native_pixel_checks':6,'static_submodule_pins':pins,
       'git_diff_check':'passed','data_models_logs_tracked':False,
       'scope':'Software/export checks, not a physical-accuracy certificate or completed textile reconstruction.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
