"""Publish compact, portable evidence for a fully validated textile sequence."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def statistics(values):
    a=np.asarray(values,float)
    assert len(a) and np.isfinite(a).all()
    return dict(minimum=float(a.min()),median=float(np.median(a)),mean=float(a.mean()),maximum=float(a.max()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--validation',default='.local/workflows/dynamic_setup/textile_reconstruction_02/validation_final.json')
    p.add_argument('--output',default='documentation/dynamic_textile_001/reconstruction_summary.json');a=p.parse_args()
    sequence=read(ROOT/a.sequence);checks=read(ROOT/a.validation)
    assert sequence['status']=='complete' and len(sequence['frames'])==len(sequence['requested_indexes'])
    assert checks['status']=='passed' and checks['partial'] is False
    assert checks['completed_frames']==len(sequence['frames'])
    assert all(c['ply_checked'] and c['recorded_appearance_checked'] for c in checks['models_checked'])
    camera_metrics={cid:[] for cid in ['dji','fuji','iphone']};steps=[];times=[];observed=[];inferred=[];coverage=[];memory=[]
    for frame in sequence['frames']:
        folder=(ROOT/frame['model']).parent;fit=read(folder/'summary.json')
        assert fit['index']==frame['index'] and all(v['resize_factor']==1 for v in fit['views'])
        for metric in frame['metrics']:camera_metrics[metric['camera']].append(metric['foreground_psnr_db'])
        steps.append(fit['steps']);times.append(fit['elapsed_s']);memory.append(fit['peak_cuda_bytes'])
        dense=read(ROOT/sequence['source_dense']/f"frame_{frame['index']:06d}.json")
        observed.append(dense['observed_stereo_points']);inferred.append(dense['neural_prior_points'])
        appearance=read(folder/'observed_appearance.json');coverage.append(appearance['observed_points']/frame['gaussians'])
    table=read((ROOT/sequence['table_model']).parent/'summary.json')
    assert table['source_policy']=='current textile capture only' and table['other_scenes_merged'] is False
    times_s=np.array([f['time_s'] for f in sequence['frames']]);counts=[f['gaussians'] for f in sequence['frames']]
    report=dict(status='complete and validated',recorded_utc=datetime.now(timezone.utc).isoformat(),
        sequence=a.sequence,representation=sequence['representation'],keyframes=len(counts),
        first_time_s=float(times_s[0]),last_time_s=float(times_s[-1]),median_keyframe_interval_s=float(np.median(np.diff(times_s))),
        time_interpolation=False,persistent_material_ids=False,actual_rgb_gaussian_fit=True,
        native_camera_crop_pixels=True,gaussians_per_keyframe=statistics(counts),static_context_gaussians=table['gaussians'],
        context_source_policy=table['source_policy'],source_views=['dji','fuji','iphone'],
        foreground_fitting_psnr_db={cid:statistics(v) for cid,v in camera_metrics.items()},
        fitting_metric_scope='Same three optimization cameras; not independent held-out novel-view or geometry validation',
        optimization_steps=statistics(steps),summed_frame_optimization_s=float(sum(times)),
        peak_process_cuda_bytes=int(max(memory)),observed_stereo_seeds_per_time=statistics(observed),
        inferred_neural_depth_seeds_per_time=statistics(inferred),recorded_appearance_coverage_fraction=statistics(coverage),
        field_references=['first surface','existing earlier keyframe within adjustable recent window'],
        geometry_field='Closest-reference surface distance in candidate calibrated metres; not material displacement or strain',
        appearance_field='Visible balanced camera RGB at approximately visible centres, median across available views; unknown gray',
        metric_accuracy_verified=False,pigment_accuracy_verified=False,
        validation=dict(models_checked=len(checks['models_checked']),binary_ply_checked=True,
            appearance_arrays_checked=True,mode_time_renders=len(checks['renders']),
            recent_reference_renders=len(checks['recent_reference_checks']),invalid_query_rejections=len(checks['invalid_queries_rejected'])),
        limitations=['Provisional planar/known-object camera calibration and manual frame synchronization',
                    'Neural depth fills surfaces not independently triangulated',
                    'Hand occlusions and repeated knit leave unverified geometry and material correspondence',
                    'Discrete independent-time RGB Gaussian fitting can show temporal surface jitter',
                    'Closest-surface color contrast includes texture, viewpoint and illumination differences'],
        originals_and_failed_trials_preserved=True,footage_weights_and_models_excluded_from_git=True)
    output=ROOT/a.output;output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
