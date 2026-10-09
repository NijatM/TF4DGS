"""CPU-only diagnostics of learned temporal support; not material tracking."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local/research/4C4D'))
from utils.general_utils import build_rotation_4d


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    path = (ROOT / args.model).resolve()
    if ROOT / 'outputs/4c4d_scene_001' not in path.parents:
        raise ValueError('Inspect only models belonging to this whole-scene experiment')
    torch.set_num_threads(4)
    packet = torch.load(path, map_location='cpu', weights_only=False)
    weights = packet['weights']
    for key, value in weights.items():
        if isinstance(value, torch.Tensor) and not torch.isfinite(value).all():
            raise ValueError(f'Non-finite model tensor: {key}')
    count = len(weights['_xyz'])
    ids = np.random.default_rng(42).choice(count, min(20000, count), replace=False)
    rotation = build_rotation_4d(weights['_rotation'][ids], weights['_rotation_r'][ids])
    scales = torch.cat([weights['_scaling'][ids], weights['_scaling_t'][ids]], dim=1).exp()
    transform = rotation * scales[:, None, :]
    covariance = transform @ transform.transpose(1, 2)
    variance = covariance[:, 3, 3].clamp_min(1e-20)
    span = packet['time_span_s']
    sigma_s = (variance.sqrt() * span).numpy()
    velocity = (covariance[:, :3, 3] / variance[:, None])
    speed = velocity.norm(dim=1).numpy() / (packet['normalization']['scale_per_m'] * span)
    opacity = weights['_opacity'][ids].sigmoid().flatten().numpy()
    centers = weights['_xyz'][ids].numpy() / packet['normalization']['scale_per_m'] + packet['normalization']['center_m']
    workspace = ((centers >= [0., -.05, -.3]) & (centers <= [.4, .28, .10])).all(1)
    groups = {'all_sampled': np.ones(len(ids), dtype=bool),
              'workspace_opaque': workspace & (opacity > .01),
              'workspace_opaque_model_speed_above_20mm_s': workspace & (opacity > .01) & (speed > .02)}
    stats = {}
    for label, mask in groups.items():
        if not mask.any():
            stats[label] = {'samples': 0}
            continue
        stats[label] = {'samples': int(mask.sum()),
            'temporal_sigma_s_p10_p50_p90': np.quantile(sigma_s[mask], [.1, .5, .9]).tolist(),
            'model_speed_m_s_p10_p50_p90': np.quantile(speed[mask], [.1, .5, .9]).tolist(),
            'fraction_sigma_below_source_frame_duration': float((sigma_s[mask] < 1001 / 30000).mean()),
            'fraction_sigma_above_0p25s': float((sigma_s[mask] > .25).mean())}
    result = {'model': str(path.relative_to(ROOT)).replace('\\', '/'),
        'model_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'dataset': packet['setup']['dataset'], 'step': packet['step'], 'edge': packet['setup']['edge'],
        'gaussians': count, 'sample_seed': 42, 'sampled_gaussians': len(ids),
        'official_rotation_function': 'utils.general_utils.build_rotation_4d',
        'source_commit': packet['source_commit'], 'source_frame_duration_s': 1001 / 30000,
        'groups': stats,
        'interpretation': 'Temporal sigma is not a hard lifetime. The 0.05 marginal gate reaches about +/-2.45 sigma; visibility/opacity/occlusion also matter. Model speed comes from conditional 4D Gaussian means, not validated physical material motion. Broad support may struggle with nonlinear folds; narrow support may leave temporal interpolation gaps. These distributions alone do not prove either cause.'}
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
