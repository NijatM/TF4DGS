"""Sequential, resumable local short trials with chronological screenshot evidence."""
import argparse
import datetime
import hashlib
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPERIMENT='4c4d_hypotheses_001'
DOCS=ROOT/'documentation'/EXPERIMENT
GPU=ROOT/'.local/envs/4c4d/Scripts/python.exe'
CPU=ROOT/'.local/envs/temporal-base/python.exe'
CONFIG=f'configs/{EXPERIMENT}.json'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def note(title,detail,status='in progress',images=()):
    subprocess.run([str(CPU),str(ROOT/'scripts/Temporal-BenchmarkReport.py'),'--docs',f'documentation/{EXPERIMENT}',
                    '--title',title,'--detail',detail,'--status',status,'--images',*images],cwd=ROOT,check=True)
    number=len(read(DOCS/'journal.json'))
    for port,label in [(8099,'headless'),(8098,'visible')]:
        try:
            subprocess.run(['powershell.exe','-NoProfile','-File',str(ROOT/'scripts/Capture-LocalPreview.ps1'),
                '-Url','http://127.0.0.1:8109/','-DebugPort',str(port),'-OutputFile',
                f'documentation/{EXPERIMENT}/{number:03d}_{label}.png','-Reload'],cwd=ROOT,check=True,timeout=45)
        except (OSError,subprocess.SubprocessError) as error:
            print(f'SCREENSHOT_FAILED: {error}',flush=True)
            subprocess.run([str(CPU),str(ROOT/'scripts/Temporal-BenchmarkReport.py'),'--docs',f'documentation/{EXPERIMENT}',
                '--title',title+' screenshot failed','--detail',str(error),'--status','documentation failure; renders retained'],cwd=ROOT)

def run(command,label):
    logs=ROOT/'.local/workflows'/EXPERIMENT
    logs.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
    log=logs/f'{label}_{stamp}.log'
    with log.open('w',encoding='utf8') as stream:
        stream.write(json.dumps([str(x) for x in command])+'\n');stream.flush()
        result=subprocess.run([str(x) for x in command],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:
        tail=log.read_text(encoding='utf8',errors='replace').splitlines()[-18:]
        note(label+' failed','\n'.join(tail)+f'\nFull ignored log: {log.relative_to(ROOT)}','failed; prior artifacts retained')
        raise RuntimeError(f'{label} exited {result.returncode}; see {log}')

def seeds(dataset):
    import numpy as np
    from PIL import Image
    cfg=read(ROOT/CONFIG)
    manifest=read(ROOT/f'data/4c4d_scene_001/{dataset}/edge_1280/manifest.json')
    dest=ROOT/f'outputs/{EXPERIMENT}/{dataset}/multi_time'
    if (dest/'initial_points.npz').exists():return
    points=[];colors=[];times=[];kinds=[];sources=[]
    # The existing tf4dgs-dynamic Conda environment owns MASt3R.
    depth_python=Path('C:/Users/mnijat/miniconda3/envs/tf4dgs-dynamic/python.exe')
    if not depth_python.exists():raise FileNotFoundError(depth_python)
    for frame in [18,42,72]:
        label=f'seed_{frame:06d}'
        path=ROOT/f'outputs/{EXPERIMENT}/{dataset}/{label}/initial_points.npz'
        if not path.exists():
            run([depth_python,'scripts/Initialize-4C4DScene.py','--dataset',dataset,'--config',CONFIG,
                '--frame',frame,'--label',label,'--max-points',30000],f'{dataset}_{label}')
        cloud=np.load(path)
        xyz=cloud['points']
        moving=np.zeros(len(xyz),bool)
        for cid,cal in manifest['cameras'].items():
            camera=xyz@np.array(cal['R']).T+np.array(cal['t'])
            uv=camera[:,:2]/np.maximum(camera[:,2:3],1e-8)*[cal['fx'],cal['fy']]+[cal['cx'],cal['cy']]
            x,y=np.rint(uv).astype('int64').T
            valid=(camera[:,2]>.01)&(x>=0)&(y>=0)&(x<cal['width'])&(y<cal['height'])
            mask=np.array(Image.open(ROOT/f'data/4c4d_scene_001/{dataset}/edge_1280/{cid}_motion_priority.png'))>127
            idx=np.flatnonzero(valid);moving[idx]|=mask[y[idx],x[idx]]
        rng=np.random.default_rng(42+frame)
        dynamic=np.flatnonzero(moving);static=np.flatnonzero(~moving)
        selected=np.concatenate([rng.choice(dynamic,min(7500,len(dynamic)),replace=False),
                                 rng.choice(static,min(15000-min(7500,len(dynamic)),len(static)),replace=False)])
        points.append(xyz[selected]);colors.append(cloud['colors'][selected]);times.append(cloud['times'][selected]);kinds.append(cloud['support_kind'][selected])
        sources.append({'frame':frame,'source_frame':manifest['frames'][frame]['source_index'],
                       'points':len(selected),'motion_priority_points':int(moving[selected].sum()),
                       'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    dest.mkdir(parents=True,exist_ok=True)
    path=dest/'initial_points.npz'
    np.savez_compressed(path,points=np.concatenate(points),colors=np.concatenate(colors),times=np.concatenate(times),support_kind=np.concatenate(kinds))
    summary={'sources':sources,'points':sum(len(x) for x in points),'initial_points_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'scope':'One timestamped cloud to inject into the joint trainable model. Source timestamps are training-only. No pretrained base or old scene. Motion weighting also seeds the rest of the room.'}
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    (DOCS/f'{dataset}_multi_time_seed.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    note(dataset+' multi-time geometry prepared',json.dumps(summary),'prepared',
         [f'{dataset}_seed_{i:06d}_scene_seed_projection.jpg' for i in [18,42,72]])

def gallery():
    results=[];cards=[]
    for path in sorted(DOCS.glob('*_step_*_metrics.json')):
        m=read(path);results.append(m)
        tag=f'{m["dataset"]}_{m["attempt"]}_step_{m["step"]:06d}'
        cards.append(f'<article><h2>{html.escape(m["dataset"]+" / "+m["attempt"])}</h2><p>Common PSNR {m["validation_psnr_common_1280"]:.3f} / motion {m["motion_region_psnr_common_1280"]:.3f} dB / SSIM {m["validation_ssim_at_1280"]:.4f}</p><div><img src="{tag}_preview.png"><img src="{tag}_orbit.png"></div></article>')
    page='<!doctype html><meta charset="utf8"><title>TF4DGS - Hypotheses</title><style>body{background:#131820;color:#eee;font:17px system-ui;margin:30px}article{border:1px solid #456;padding:20px;margin:20px 0}div{display:flex}img{width:50%;object-fit:contain}a{color:#9cf}</style><h1>Eight matched 4C4D hypotheses</h1><p><a href="index.html">Chronological stages</a> / <a href="hypotheses.json">Protocol</a></p>'+''.join(cards)+'<script>window.tf4dgsSceneGalleryReady=true;</script>'
    (DOCS/'comparison.html').write_text(page,encoding='utf8')
    (DOCS/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')

def trial(dataset,variant,attempt=None,stop=10600,quick=True):
    name=attempt or 'h_'+variant
    path=ROOT/f'outputs/{EXPERIMENT}/{dataset}/{name}/metrics_{stop:06d}.json'
    if path.exists():return read(path)['summary']
    edge=1920 if variant=='native_detail' else 1280
    preset='slow_motion' if dataset=='yogurt' else 'baseline'
    note(f'{dataset}: {variant} begins',f'600 optimizer updates from the immutable 10k whole-scene parent, edge {edge}; preset {preset}. Same checkpoint/RNG, full pixels and three held-out times.', 'short trial running')
    command=[GPU,'scripts/Train-4C4DScene.py','--dataset',dataset,'--attempt',name,'--config',CONFIG,
        '--variant',variant,'--preset',preset,'--edge',edge,'--stop',stop,
        '--parent',f'outputs/4c4d_scene_001/{dataset}/baseline_01/checkpoint_010000.pth']
    if quick:command.append('--quick-eval')
    cp=path.parent/'checkpoint.pth'
    if cp.exists():command.append('--resume')
    run(command,f'{dataset}_{name}')
    m=read(path)['summary'];gallery()
    tag=f'{dataset}_{name}_step_{stop:06d}'
    note(f'{dataset}: {variant} finished',f'{m["evaluation_image_count"]} validation camera images. Common whole-frame {m["validation_psnr_common_1280"]:.4f} dB; motion {m["motion_region_psnr_common_1280"]:.4f} dB; SSIM {m["validation_ssim_at_1280"]:.5f}. {m["point_count"]} Gaussians; current-run elapsed {m["run_elapsed_s"]:.1f}s; peak allocated {m["peak_cuda_allocated_gib"]:.2f} GiB. Orbit checked separately; scores do not certify metric geometry.',
         'screen completed; review pending',[tag+'_preview.png',tag+'_orbit.png'])
    return m

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['seeds','screen','trials'],required=True)
    parser.add_argument('--datasets',nargs='+',default=['textile','yogurt'])
    parser.add_argument('--variants',nargs='+',default=['control'])
    parser.add_argument('--all-validation',action='store_true')
    args=parser.parse_args()
    if args.stage=='seeds':
        for dataset in args.datasets:seeds(dataset)
    elif args.stage=='screen':
        for variant in read(ROOT/CONFIG)['variants']:trial('textile',variant)
    else:
        for dataset in args.datasets:
            for variant in args.variants:
                trial(dataset,variant,attempt='confirm_'+variant if args.all_validation else None,quick=not args.all_validation)
    print('STAGE_COMPLETE '+args.stage,flush=True)

if __name__=='__main__':main()
