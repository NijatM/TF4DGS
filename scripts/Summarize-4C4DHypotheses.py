"""Summarize actual trials; draft and then select a confirmed full-training recipe."""
import argparse
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'documentation/4c4d_hypotheses_001'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--draft-combination',action='store_true')
    parser.add_argument('--select-full',action='store_true')
    args=parser.parse_args()
    cfg_path=ROOT/'configs/4c4d_hypotheses_001.json'
    cfg=read(cfg_path)
    paths=sorted(DOCS.glob('*_step_*_metrics.json'))
    results=[read(path) for path in paths]
    mapping={(r['dataset'],r['variant']):r for r in results}
    if args.draft_combination:
        t=mapping['textile','control']
        capacity=max([mapping['textile',v] for v in ['point_capacity','capacity_900k'] if ('textile',v) in mapping],
                     key=lambda r:r['motion_region_psnr_common_1280'])
        combination=copy.deepcopy(cfg['variants'][capacity['variant']])
        for variant in ['motion_priority','temporal_support']:
            m=mapping['textile',variant]
            if m['motion_region_psnr_common_1280']>t['motion_region_psnr_common_1280']+.03:
                combination.update(cfg['variants'][variant])
        multi=mapping.get(('textile','multi_time_support'))
        if multi and multi['motion_region_psnr_common_1280']>mapping['textile','point_capacity']['motion_region_psnr_common_1280']+.03:
            combination.update({k:v for k,v in cfg['variants']['multi_time_support'].items() if k!='max_points'})
        cfg['variants']['combination']=combination
        write(cfg_path,cfg)
    if args.select_full:
        full=read(ROOT/'configs/4c4d_full_001_plan.json')
        full['evaluation']['max_validation_timestamps']=18
        full['training']['time_lr_reference_span_s']=89*1001/30000
        full['scene']['initialization_mode']='single_action_cloud'
        full['scene']['initialization']='Fresh whole-scene calibrated SIFT/MASt3R cloud at one training action timestamp. Uniform initial temporal centers, learned temporal support, every point jointly trainable. Multi-time point injection was rejected after losing against the capacity-only trial.'
        full['scene']['initial_temporal_sigma_s']=(89*1001/30000)/5**.5
        full['scene']['initial_max_points']=cfg['scene']['initial_max_points']
        full['datasets']['yogurt']['initial_source_frame']=330
        full['datasets']['textile']['initial_source_frame']=588
        full['variants']={};full['selected_presets']={};selected={}
        for dataset in ['textile','yogurt']:
            # The confirmation candidates use every temporal validation image.
            candidates=[r for r in results if r['dataset']==dataset and r['evaluation_image_count']==45]
            if not candidates:raise ValueError(f'Missing all-validation confirmation for {dataset}')
            winner=max(candidates,key=lambda r:r['motion_region_psnr_common_1280'])
            params=copy.deepcopy(cfg['variants'][winner['variant']])
            # The full model is freshly initialized across its complete timeline,
            # so do not inject the separate short-trial cloud into it.
            params.pop('inject_points',None);params.pop('injection_sigma_s',None)
            # Preserve the winning capacity, including the original 450k
            # control when it wins. Do not silently increase its budget.
            params['max_points']=params.get('max_points',cfg['training']['max_points'])
            full['variants'][dataset+'_selected']=params
            full['selected_presets'][dataset]=winner['preset']
            selected[dataset]={'variant':winner['variant'],'validation_psnr_common_1280':winner['validation_psnr_common_1280'],
                'motion_region_psnr_common_1280':winner['motion_region_psnr_common_1280'],
                'confirmation_images':45,'parameters':params,'preset':winner['preset'],
                'selection_scope':'Single-seed short-clip screening plus all-temporal-validation confirmation. Full-duration convergence is not yet measured.'}
        full['selection']=selected
        full['training']['max_points']=max(x['parameters']['max_points'] for x in selected.values())
        full['refinement']['max_points']=full['training']['max_points']
        write(ROOT/'configs/4c4d_full_001.json',full)
        write(DOCS/'selection.json',selected)
        full_docs=ROOT/'documentation/4c4d_full_001';full_docs.mkdir(parents=True,exist_ok=True)
        write(full_docs/'report.json',{'title':'TF4DGS: full-recording continuous 4C4D training',
            'intro':'Yogurt: all 467 synchronized frames/camera (15.58 s). Textile: all 1277 frames/camera (42.61 s). Fresh whole-scene action-frame initialization, one joint model per capture, hands and surroundings included. Selected recipe comes from eight brief matched hypotheses. Native 4K refinement is queued; final quality and playback are pending.'})
        write(full_docs/'selection.json',selected)
    lines=['# Measured short-trial results','',
           'Each screening trial uses 600 updates from the same immutable 10k parent and nine validation images. Confirmations use all 45 temporal validation images. Comparisons must use the same evaluation-image count. All fields below come from saved metric JSON.','',
           '| Capture | Variant | Validation images | Whole PSNR | Motion PSNR | SSIM | Points | Run seconds | Peak allocated GiB |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in results:
        lines.append(f'| {r["dataset"]} | {r["variant"]} | {r["evaluation_image_count"]} | {r["validation_psnr_common_1280"]:.4f} | {r["motion_region_psnr_common_1280"]:.4f} | {r["validation_ssim_at_1280"]:.5f} | {r["point_count"]} | {r["run_elapsed_s"]:.1f} | {r["peak_cuda_allocated_gib"]:.2f} |')
    lines += ['','The substantial early gain is point capacity. Smaller temporal-support and motion-weighting improvements require combination confirmation. Raising resolution alone was not a substitute for better geometry/capacity. Loss and SH changes that regress the measured moving region are excluded.','',
              'Novel orbit views remain underconstrained by the three same-side cameras, and the cloth still contains streaks/ghosts. No pristine reconstruction or independently validated geometric accuracy is claimed. More iterations and higher resolution are follow-up stages, not measured outcomes yet.','',
              'Multi-time seed injection did not improve on the capacity-only trial and is excluded from the selected recipe. Full training starts with a fresh whole-scene action-frame cloud and uniformly initialized temporal centers, retaining the same physical initial temporal sigma as the three-second trials. This is one model with every primitive trainable; no separately trained base is merged. Temporal center learning rates are rescaled to preserve their physical-time step. The longer-duration adaptation is checked for finite forward/backward operations before the full jobs begin.']
    if (DOCS/'selection.json').exists():
        lines+=['','## Selected full-training recipes','',json.dumps(read(DOCS/'selection.json'),indent=2)]
    (DOCS/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({'results':len(results),'selection':read(DOCS/'selection.json') if (DOCS/'selection.json').exists() else None},indent=2))

if __name__=='__main__':main()
