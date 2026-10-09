"""Check +/-2-frame alignment hypotheses without altering source timestamps.

Repeated textile texture/calibration errors can affect this diagnostic. A minimum
matching residual is not a sensor-sync certificate and is never silently applied.
Only source indices marked training are used in this audit.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('scene_init', ROOT / 'scripts/Initialize-4C4DScene.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    args = parser.parse_args()
    data = ROOT / 'data/4c4d_scene_001' / args.dataset / 'edge_1280'
    manifest = shared.read(data / 'manifest.json')
    cams = {cid: shared.camera(cal, manifest['normalization']) for cid, cal in manifest['cameras'].items()}
    masks = {cid: np.array(Image.open(data / f'{cid}_motion_priority.png')) for cid in cams}
    model = shared.AsymmetricMASt3R.from_pretrained(str(ROOT / '.local/tools/mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth')).cuda().eval()
    records = []
    with torch.inference_mode():
        for anchor in [32, 62]:
            for other in ['dji', 'fuji']:
                first = np.array(Image.open(data / 'images/iphone' / f'{anchor:06d}.png'))
                a, af = shared.tensor_view(first, 0)
                for offset in [-2, -1, 0, 1, 2]:
                    index = anchor + offset
                    assert manifest['frames'][anchor]['split'] == manifest['frames'][index]['split'] == 'train'
                    second = np.array(Image.open(data / 'images' / other / f'{index:06d}.png'))
                    b, bf = shared.tensor_view(second, 1)
                    p1, p2 = model(a, b)
                    q1, q2 = shared.fast_reciprocal_NNs(p1['desc'][0], p2['desc'][0], subsample_or_initxy1=4, device='cuda', dist='dot', block_size=2048)
                    xy1, xy2 = q1 * af, q2 * bf
                    active = (shared.colors(np.repeat(masks['iphone'][..., None], 3, axis=2), xy1)[:, 0] > .5) & (shared.colors(np.repeat(masks[other][..., None], 3, axis=2), xy2)[:, 0] > .5)
                    epi = shared.epipolar(xy1[active], xy2[active], cams['iphone'], cams[other])
                    record = {'camera': other, 'anchor_local_index': anchor, 'candidate_frame_offset': offset,
                              'active_matches': int(active.sum()), 'median_epipolar_px': float(np.median(epi)) if len(epi) else None,
                              'fraction_below_2px': float((epi < 2).mean()) if len(epi) else None}
                    records.append(record)
                    print(json.dumps(record), flush=True)
                    del p1, p2
    aggregate = {}
    for cid in ['dji', 'fuji']:
        aggregate[cid] = {str(offset): float(np.mean([r['fraction_below_2px'] for r in records if r['camera'] == cid and r['candidate_frame_offset'] == offset])) for offset in [-2, -1, 0, 1, 2]}
    result = {'dataset': args.dataset, 'records': records, 'aggregate_fraction_below_2px': aggregate,
              'applied_offset': {'dji': 0, 'fuji': 0, 'iphone': 0},
              'claim_limit': 'Diagnostic correspondence score only; repeated texture, occlusion and provisional calibration confound physical sensor alignment. Original common timeline preserved.'}
    (ROOT / 'documentation/4c4d_scene_001' / f'{args.dataset}_sync_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')


if __name__ == '__main__':
    main()
