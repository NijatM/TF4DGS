"""Record eight testable hypotheses and probe the complete capture timelines."""
import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')

def main():
    base = read(ROOT/'configs/4c4d_scene_001.json')
    cfg = copy.deepcopy(base)
    cfg['experiment_id'] = '4c4d_hypotheses_001'
    cfg['data_experiment_id'] = '4c4d_scene_001'
    cfg['initialization_paths'] = {d:f'outputs/4c4d_scene_001/{d}/initialization/initial_points.npz' for d in base['datasets']}
    cfg['evaluation']['quick_indices'] = [17,47,77]
    cfg['training']['checkpoints'] = [10600]
    cfg['report_url'] = 'http://127.0.0.1:8109/'
    cfg['variants'] = {
        'control': {},
        'temporal_support': {'temporal_floor_s':.04,'temporal_floor_weight':.005},
        'compact_geometry': {'anisotropy_weight':.002,'anisotropy_limit':12},
        'pattern_detail': {'detail_weight':.15},
        'motion_priority': {'motion_region_weight':8},
        'point_capacity': {'max_points':600000},
        'native_detail': {},
        'simpler_appearance': {'sh_limit':[1,1]},
        'multi_time_support': {'max_points':600000,'injection_sigma_s':.12,
          'inject_points':{d:f'outputs/4c4d_hypotheses_001/{d}/multi_time/initial_points.npz' for d in base['datasets']}}
    }
    hypotheses = [
      ('temporal_support','Very short temporal support leaves gaps between captured frames. A soft 40 ms minimum marginal standard deviation may improve interpolation without forcing all Gaussians to be persistent.'),
      ('compact_geometry','Long conditional spatial ellipsoids produce cloth streaks and floaters. A mild aspect-ratio penalty may recover compact geometry rather than view-specific streaks.'),
      ('pattern_detail','Global RGB/SSIM objectives dilute small textile patterns. A motion-weighted image-gradient loss may recover weave, printed detail and hand boundaries.'),
      ('motion_priority','The surrounding room competes with the changing subject. Raising motion-region weight from 4 to 8 may improve the subject while retaining supervision on every room pixel.'),
      ('point_capacity','The early 450k cap limits births and fine detail. Allowing 600k Gaussians may reduce missing folds and preserve newly visible surfaces.'),
      ('native_detail','1280-edge supervision loses source detail. A matched 1920-edge continuation may improve detail at a common 1280 evaluation resolution, justifying later native 4K refinement.'),
      ('simpler_appearance','High-degree space/time color coefficients can fit appearance before geometry. Limiting active SH to spatial 1 / temporal 1 may reduce view-specific overfitting.'),
      ('multi_time_support','First-frame-only geometry misses later folds and hand positions. Timestamped calibrated seeds at three training times may improve coverage within the same joint model.')
    ]
    plan = {'hypotheses':[{'id':k,'hypothesis':v} for k,v in hypotheses],
            'protocol':{'parent_step':10000,'updates_per_trial':600,'textile_trials':['control']+list(cfg['variants'])[1:],
              'validation_local_indices':[17,47,77],'validation_camera_images':9,'preview_local_index':47,
              'same_parent_rng':True,'same_cameras_and_action_intervals':True,
              'exceptions':'1920 trial uses more pixels; multi-time trial adds timestamped points and increases capacity. Compare capacity-only to separate the additional seed contribution.',
              'confirmation':'Repeat control and the leading compatible variants on yogurt; run a matched combination confirmation on both captures.',
              'scope':'Brief one-seed screening, not statistically conclusive convergence tests or independent geometric accuracy.'},
            'sources':[{'url':'https://github.com/yangzf-1023/4C4D','pin':base['source_commit'],
                        'use':'Official sparse-camera initialization, geometry/appearance imbalance, neural opacity decay and analytic 4D covariance. The eight modifications are local hypotheses, not claims made by the paper.'}]}
    write(ROOT/'configs/4c4d_hypotheses_001.json',cfg)
    docs=ROOT/'documentation/4c4d_hypotheses_001'
    write(docs/'hypotheses.json',plan)
    write(docs/'report.json',{'title':'TF4DGS: eight improvement hypotheses and full-recording training',
        'intro':'Matched 600-update action-clip trials from immutable 10k checkpoints. Textile first, yogurt confirmation. Every visible surface and the hands stay in one jointly trained 4C4D model. Full duration training follows selection; no separate base or old room is merged.'})
    tools=read(ROOT/'static-tools.json')
    probe=next(x['ffprobe_path'] for x in tools['portable_tools'] if x['name']=='FFmpeg')
    full=copy.deepcopy(base)
    full['experiment_id']='4c4d_full_001'
    full['training'].update(total_updates=60000,checkpoints=[1000,10000,20000,40000,60000],max_points=600000,densify_until=40000)
    full['refinement'].update(updates_per_stage=8000,checkpoints=[2000,4000,8000])
    full['production'].update(updates=4000,checkpoints=[2000,4000])
    full['report_url']='http://127.0.0.1:8109/'
    # A fixed physical initial lifetime avoids 42-second cloth Gaussians
    # inheriting the upstream normalized sigma of 0.447 (~19 seconds).
    full['scene']['initial_temporal_sigma_s']=.35
    full['scene']['initialization']='Timestamped whole-scene calibrated MASt3R/SIFT seeds distributed over each full recording; one joint trainable model, no separate/frozen background.'
    full['scene']['initial_max_points']=200000
    evidence={}
    for dataset,spec in full['datasets'].items():
        session_path=ROOT/spec['session']
        session=read(session_path)
        records=[]
        for camera in session['cameras']:
            video=session_path.parent/camera['video']
            result=json.loads(subprocess.check_output([probe,'-v','error','-select_streams','v:0',
                '-show_entries','stream=width,height,avg_frame_rate,r_frame_rate,nb_frames,duration','-of','json',str(video)],text=True))['streams'][0]
            if result['avg_frame_rate']!='30000/1001':raise ValueError(f'Unexpected source cadence: {video}')
            result.update(camera=camera['id'],video=str(video.relative_to(ROOT)).replace('\\','/'))
            records.append(result)
        common=min(int(x['nb_frames']) for x in records)
        spec.update(start_frame=0,end_frame_exclusive=common)
        evidence[dataset]={'cameras':records,'common_frame_count':common,'duration_s':common*1001/30000,
            'first_source_index':0,'last_source_index':common-1,
            'policy':'Use the full common export interval at native cadence, retaining the user Premiere alignment. No new verified sensor synchronization is claimed.'}
    full['evaluation'].update(preview_local_frame=587,quick_indices=[17,47,77])
    full['evaluation']['preview_per_dataset']={'yogurt':377,'textile':635}
    # Final recipe is written only after empirical selection, not here.
    write(ROOT/'configs/4c4d_full_001_plan.json',full)
    write(docs/'full_capture_probe.json',evidence)
    lines=['# Eight 4C4D improvement hypotheses','',
      'These are local hypotheses based on our observed errors and the [official 4C4D implementation](https://github.com/yangzf-1023/4C4D). They are not guaranteed improvements.','',
      '| Test | Reason and prediction |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in hypotheses]
    lines += ['','All trials start at the same immutable 10k checkpoint and RNG state and run 600 updates. Nine held-out camera images (three times × three cameras) screen whole-frame and motion appearance. Positive results are candidates for confirmation, not proof of final quality. The higher-resolution trial has more pixel work; initialization-plus-capacity is compared against capacity alone.','',
       'Existing long experiments: textile reached 20k (25.95 dB whole-frame / 24.05 dB motion PSNR), but visible cloth streaks remain. Yogurt favored reduced time/rotation learning rates at 12k. Prior opacity/learning-rate branches did not fix cloth geometry.','',
       'The previous 30k continuation ended at 20,500 because Windows denied replacement of the browser-read live-progress JSON. The last saved and evaluated checkpoint is 20,000. Atomic writes now use unique temporary names and bounded retries; failed-run logs and screenshots are preserved.','',
       '## Full recordings','']
    lines += [f'- {d}: {v["common_frame_count"]} frames/camera, {v["duration_s"]:.4f} seconds, three cameras.' for d,v in evidence.items()]
    (docs/'HYPOTHESES.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'plan':str(docs/'HYPOTHESES.md'),'captures':evidence},indent=2))

if __name__=='__main__':main()
