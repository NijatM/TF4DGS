"""Train complete recordings as single joint continuous 4C4D models.

Resumable stage records, bounded image cache, sequential GPU ownership,
chronological screenshots and explicit native-resolution fallback.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXPERIMENT='4c4d_full_001'
DOCS=ROOT/'documentation'/EXPERIMENT
CONFIG=f'configs/{EXPERIMENT}.json'
GPU=ROOT/'.local/envs/4c4d/Scripts/python.exe'
CPU=ROOT/'.local/envs/temporal-base/python.exe'
DEPTH=Path('C:/Users/mnijat/miniconda3/envs/tf4dgs-dynamic/python.exe')

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.write.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
    import time
    for attempt in range(12):
        try:temporary.replace(path);return
        except PermissionError:
            if attempt==11:raise
            time.sleep(min(.025*2**attempt,.5))

def note(title,detail,status='in progress',images=()):
    subprocess.run([str(CPU),'scripts/Temporal-BenchmarkReport.py','--docs',f'documentation/{EXPERIMENT}',
                    '--title',title,'--detail',detail,'--status',status,'--images',*images],cwd=ROOT,check=True)
    number=len(read(DOCS/'journal.json'))
    for port,label in [(8099,'headless'),(8098,'visible')]:
        try:
            subprocess.run(['powershell.exe','-NoProfile','-File','scripts/Capture-LocalPreview.ps1',
                '-Url','http://127.0.0.1:8109/','-DebugPort',str(port),
                '-OutputFile',f'documentation/{EXPERIMENT}/{number:03d}_{label}.png','-Reload'],cwd=ROOT,check=True,timeout=45)
        except (OSError,subprocess.SubprocessError) as error:
            subprocess.run([str(CPU),'scripts/Temporal-BenchmarkReport.py','--docs',f'documentation/{EXPERIMENT}',
                '--title',title+' screenshot failed','--detail',str(error),'--status','documentation failure; models preserved'],cwd=ROOT)

def run(command,label,allow_oom=False):
    folder=ROOT/'.local/workflows'/EXPERIMENT;folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
    log=folder/f'{label}_{stamp}.log'
    with log.open('w',encoding='utf8') as stream:
        stream.write(json.dumps([str(x) for x in command])+'\n');stream.flush()
        code=subprocess.run([str(x) for x in command],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT).returncode
    if code:
        content=log.read_text(encoding='utf8',errors='replace')
        oom='out of memory' in content.lower()
        note(label+' failed','\n'.join(content.splitlines()[-20:])+f'\nIgnored log: {log.relative_to(ROOT)}',
             'CUDA memory failure; fallback next' if oom and allow_oom else 'failed; checkpoint preserved')
        if oom and allow_oom:return False
        raise RuntimeError(f'{label} failed with code {code}; {log}')
    return True

def init(dataset):
    import numpy as np
    from PIL import Image
    cfg=read(ROOT/CONFIG)
    manifest=read(ROOT/f'data/{EXPERIMENT}/{dataset}/edge_1280/manifest.json')
    dest=ROOT/f'outputs/{EXPERIMENT}/{dataset}/initialization'
    path=dest/'initial_points.npz'
    if path.exists():return
    count=len(manifest['frames']);span=manifest['frames'][-1]['pts_s']
    if cfg['scene'].get('initialization_mode')=='single_action_cloud':
        frame=cfg['datasets'][dataset]['initial_source_frame']
        label=f'initial_action_{frame:06d}'
        source=ROOT/f'outputs/{EXPERIMENT}/{dataset}/{label}/initial_points.npz'
        if not source.exists():
            run([DEPTH,'scripts/Initialize-4C4DScene.py','--config',CONFIG,'--dataset',dataset,
                 '--frame',frame,'--label',label,'--max-points',cfg['scene']['initial_max_points']],dataset+'_initialize_action')
        cloud=np.load(source)
        rng=np.random.default_rng(cfg['seed'])
        dest.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,points=cloud['points'],colors=cloud['colors'],support_kind=cloud['support_kind'],
            times=rng.uniform(0,1,(len(cloud['points']),1)).astype('float32'),
            temporal_sigmas_s=np.full((len(cloud['points']),1),cfg['scene']['initial_temporal_sigma_s'],np.float32))
        summary={'dataset':dataset,'points':len(cloud['points']),'source_frame':frame,
            'source_cloud_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'initial_points_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'initial_temporal_sigma_s':cfg['scene']['initial_temporal_sigma_s'],
            'policy':'One fresh whole-scene action-frame cloud, uniform temporal centers across the full timeline. Every primitive is trainable; no separately trained background or old scene. Multi-time injection rejected by the brief trials.',
            'claim_limit':'Metric matching plus labelled inferred depths, not independently verified room geometry.'}
        write(dest/'summary.json',summary);write(DOCS/f'{dataset}_initialization.json',summary)
        note(dataset+' full-recording cloud initialized',json.dumps(summary),'initialized',
             [f'{dataset}_{label}_scene_seed_projection.jpg'])
        return
    # About one training timestamp per second; the empty first frame supplies
    # broad initial support for the observed room. Every seed stays trainable.
    desired=np.linspace(0,count-1,max(3,round(span)+1)).round().astype(int)
    frames=sorted(set(int(i-1 if i%6==5 else i) for i in desired))
    points=[];colors=[];times=[];sigmas=[];kinds=[];sources=[]
    for frame in frames:
        label=f'seed_{frame:06d}'
        cloud_path=ROOT/f'outputs/{EXPERIMENT}/{dataset}/{label}/initial_points.npz'
        if not cloud_path.exists():
            run([DEPTH,'scripts/Initialize-4C4DScene.py','--config',CONFIG,'--dataset',dataset,
                 '--frame',frame,'--label',label,'--max-points',40000],f'{dataset}_{label}')
        cloud=np.load(cloud_path)
        xyz=cloud['points'];moving=np.zeros(len(xyz),bool)
        for cid,cal in manifest['cameras'].items():
            camera=xyz@np.array(cal['R']).T+np.array(cal['t'])
            uv=camera[:,:2]/np.maximum(camera[:,2:3],1e-8)*[cal['fx'],cal['fy']]+[cal['cx'],cal['cy']]
            x,y=np.rint(uv).astype('int64').T
            valid=(camera[:,2]>.01)&(x>=0)&(y>=0)&(x<cal['width'])&(y<cal['height'])
            mask=np.array(Image.open(ROOT/f'data/{EXPERIMENT}/{dataset}/edge_1280/{cid}_motion_priority.png'))>127
            idx=np.flatnonzero(valid);moving[idx]|=mask[y[idx],x[idx]]
        rng=np.random.default_rng(42+frame)
        budget=40000 if frame==0 else max(3000,round(160000/(len(frames)-1)))
        if frame==0:
            selected=rng.choice(len(xyz),min(budget,len(xyz)),replace=False)
        else:
            active=np.flatnonzero(moving);rest=np.flatnonzero(~moving)
            active_count=min(round(budget*.8),len(active))
            selected=np.concatenate([rng.choice(active,active_count,replace=False),
                      rng.choice(rest,min(budget-active_count,len(rest)),replace=False)])
        points.append(xyz[selected]);colors.append(cloud['colors'][selected]);times.append(cloud['times'][selected]);kinds.append(cloud['support_kind'][selected])
        # Initial broad support is a trainable parameter, not a frozen or
        # separately reconstructed base. Later geometry has localized support.
        sigmas.append(np.full((len(selected),1),max(.6,span*.6) if frame==0 else .6,np.float32))
        sources.append({'local_frame':frame,'source_frame':manifest['frames'][frame]['source_index'],
            'pts_s':manifest['frames'][frame]['pts_s'],'points':len(selected),
            'motion_priority_points':int(moving[selected].sum()),'cloud_sha256':hashlib.sha256(cloud_path.read_bytes()).hexdigest()})
        write(DOCS/f'{dataset}_seed_progress.json',{'completed':len(sources),'total':len(frames),'latest_frame':frame,'sources':sources})
        if len(sources)==1 or len(sources)%10==0 or len(sources)==len(frames):
            note(f'{dataset}: full-duration initialization {len(sources)}/{len(frames)}',
                f'New timestamped cloud at source frame {frame}; {len(selected)} points retained. Full camera frames, calibrated matching plus labelled inferred depth. All points enter the same joint model; no old scene or separately trained base.',
                'initialization running',[f'{dataset}_{label}_scene_seed_projection.jpg'])
    dest.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,points=np.concatenate(points),colors=np.concatenate(colors),times=np.concatenate(times),
                        temporal_sigmas_s=np.concatenate(sigmas),support_kind=np.concatenate(kinds))
    summary={'dataset':dataset,'points':sum(len(x) for x in points),'timestamps':sources,
        'initial_points_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'time_span_s':span,'initial_support':'First whole-scene observations start broad; subsequent whole-scene points start at 0.6 s sigma. All temporal/spatial/appearance parameters remain trainable in one model.',
        'policy':'Fresh calibrated training-only timestamped seeds from this capture. No previously trained actor/base/background is merged.',
        'claim_limit':'Neural depth is inferred; three-camera photometric fit does not establish physical material correspondence.'}
    write(dest/'summary.json',summary);write(DOCS/f'{dataset}_initialization.json',summary)
    note(dataset+' full recording initialization ready',f'{summary["points"]} points across {len(sources)} training timestamps, covering {span:.3f} s. All finite arrays and provenance saved.', 'ready')

def train(dataset,attempt,edge,stop,parent=None,refine=False,fit_all=False):
    cfg=read(ROOT/CONFIG)
    output=ROOT/f'outputs/{EXPERIMENT}/{dataset}/{attempt}'
    metrics=output/f'metrics_{stop:06d}.json'
    if metrics.exists():return output/'checkpoint.pth'
    command=[GPU,'scripts/Train-4C4DScene.py','--config',CONFIG,'--dataset',dataset,'--attempt',attempt,
             '--edge',edge,'--variant',dataset+'_selected','--preset',cfg['selected_presets'][dataset],'--stop',stop]
    if parent:command+=['--parent',parent]
    if refine:command+=['--refine']
    if fit_all:command+=['--fit-all']
    if (output/'checkpoint.pth').exists():command+=['--resume']
    role='all-frame production fitting' if fit_all else 'validation-selected training'
    note(f'{dataset}: {attempt} begins',f'{stop} updates at edge {edge}; {role}. Complete recording, all three cameras, subject/hands and visible surroundings in one continuous model. Checkpoints are resumable.', 'training running')
    write(DOCS/'pipeline_state.json',{'dataset':dataset,'attempt':attempt,'edge':edge,'stop':stop,'status':'running',
        'command':[str(x) for x in command],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    success=run(command,f'{dataset}_{attempt}',allow_oom=edge==3840)
    if not success:return None
    m=read(metrics)['summary'];tag=f'{dataset}_{attempt}_step_{stop:06d}'
    note(f'{dataset}: {attempt} completed',f'Common 1280 appearance PSNR {m["validation_psnr_common_1280"]:.3f} dB / motion {m["motion_region_psnr_common_1280"]:.3f} dB / {m["point_count"]} Gaussians. Evaluation role: {m["evaluation_role"]}. Visual geometry and time playback still require review.',
        'checkpoint ready',[tag+'_preview.png',tag+'_orbit.png'])
    return output/'checkpoint.pth'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['seeds','smoke','train'],required=True)
    parser.add_argument('--datasets',nargs='+',default=['textile','yogurt'])
    args=parser.parse_args()
    DOCS.mkdir(parents=True,exist_ok=True)
    cfg=read(ROOT/CONFIG)
    if args.stage=='seeds':
        for dataset in args.datasets:init(dataset)
    elif args.stage=='smoke':
        for dataset in args.datasets:train(dataset,'whole_1280',1280,100)
    else:
        # Single GPU: train both full timelines first, then progressively refine.
        for dataset in args.datasets:train(dataset,'whole_1280',1280,cfg['training']['total_updates'])
        registry={'schema_version':1,'experiment_id':EXPERIMENT,'datasets':{}}
        for dataset in args.datasets:
            parent=ROOT/f'outputs/{EXPERIMENT}/{dataset}/whole_1280/checkpoint.pth'
            parent=train(dataset,'refine_1920',1920,cfg['refinement']['updates_per_stage'],parent,True)
            native=train(dataset,'refine_3840',3840,cfg['refinement']['updates_per_stage'],parent,True)
            if native is None:
                run([CPU,'scripts/Prepare-4C4DScene.py','--config',CONFIG,'--datasets',dataset,'--edge',2560],dataset+'_prepare_fallback_2560')
                native=train(dataset,'refine_2560',2560,cfg['refinement']['updates_per_stage'],parent,True)
                edge=2560
            else:edge=3840
            fitted=train(dataset,'production_'+str(edge),edge,cfg['production']['updates'],native,True,True)
            packet=fitted.parent/'continuous_model.pth'
            registry['datasets'][dataset]={'model':str(packet.relative_to(ROOT)).replace('\\','/'),
                'sha256':hashlib.sha256(packet.read_bytes()).hexdigest(),'edge':edge,'status':'trained; final visual review pending'}
            write(ROOT/f'outputs/{EXPERIMENT}/selected_models.json',registry)
        write(DOCS/'pipeline_state.json',{'status':'all models trained; final visual review pending','registry':str((ROOT/f'outputs/{EXPERIMENT}/selected_models.json').relative_to(ROOT))})
        note('Full-recording models trained','Both continuous models are saved; final time playback and geometry review remain. No Git changes have been staged or pushed.','training complete; review pending')
    print('STAGE_COMPLETE '+args.stage,flush=True)

if __name__=='__main__':main()
