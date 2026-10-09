"""Reconstruct one full-frame initial cloud and audit measured camera consistency.

All points enter the same trainable temporal model. Neural depths are explicitly
inferred and registered to calibrated stereo; no old actor or background is used.
"""
import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local/tools/mast3r'))
from mast3r.model import AsymmetricMASt3R
from mast3r.fast_nn import fast_reciprocal_NNs


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def skew(value):
    x, y, z = value
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def camera(cal, norm):
    rotation = np.array(cal['R'])
    translation = np.array(cal['t']) / norm['scale_per_m'] - rotation @ norm['center_m']
    matrix = np.array([[cal['fx'], 0, cal['cx']], [0, cal['fy'], cal['cy']], [0, 0, 1.]])
    return dict(K=matrix, R=rotation, t=translation, P=matrix @ np.c_[rotation, translation])


def projection(points, cam):
    q = points @ cam['P'][:, :3].T + cam['P'][:, 3]
    return q[:, :2] / q[:, 2:]


def epipolar(a, b, ca, cb):
    rotation = cb['R'] @ ca['R'].T
    translation = cb['t'] - rotation @ ca['t']
    fundamental = np.linalg.inv(cb['K']).T @ skew(translation) @ rotation @ np.linalg.inv(ca['K'])
    ah, bh = np.c_[a, np.ones(len(a))], np.c_[b, np.ones(len(b))]
    la, lb = bh @ fundamental, ah @ fundamental.T
    residual = np.abs(np.sum(bh * lb, axis=1))
    return residual / np.sqrt(np.sum(la[:, :2] ** 2 + lb[:, :2] ** 2, axis=1)).clip(1e-12)


def triangulate(a, b, ca, cb):
    if not len(a): return np.empty((0,3)), np.empty(0), np.empty(0,bool)
    h = cv2.triangulatePoints(ca['P'], cb['P'], a.T, b.T).T
    points = h[:, :3] / h[:, 3:]
    error = np.maximum(np.linalg.norm(projection(points, ca) - a, axis=1), np.linalg.norm(projection(points, cb) - b, axis=1))
    da, db = (points @ ca['R'].T + ca['t'])[:, 2], (points @ cb['R'].T + cb['t'])[:, 2]
    good = np.isfinite(points).all(1) & (error < 2.) & (da > .05) & (db > .05) & (da < 6.) & (db < 6.)
    return points, error, good


def similarity(source, target):
    keep = np.isfinite(source).all(1) & np.isfinite(target).all(1)
    if keep.sum() < 40:
        return None
    for _ in range(6):
        a, b = source[keep], target[keep]
        ac, bc = a.mean(0), b.mean(0)
        aa, bb = a - ac, b - bc
        u, values, vt = np.linalg.svd(aa.T @ bb)
        sign = np.ones(3)
        sign[-1] = np.sign(np.linalg.det(vt.T @ u.T))
        rotation = vt.T @ np.diag(sign) @ u.T
        scale = float((values * sign).sum() / (aa ** 2).sum())
        translation = bc - scale * ac @ rotation.T
        residual = np.linalg.norm(scale * source @ rotation.T + translation - target, axis=1)
        median = np.median(residual[keep])
        mad = np.median(np.abs(residual[keep] - median))
        candidate = np.isfinite(residual) & (residual < max(.015, median + 2.5 * mad))
        if candidate.sum() < 40:
            break
        keep = candidate
    if scale <= 0:
        return None
    return scale, rotation, translation, float(np.median(residual[keep]))


def tensor_view(pixels, index):
    height, width = pixels.shape[:2]
    factor = 512 / max(width, height)
    w, h = max(32, round(width * factor / 16) * 16), max(32, round(height * factor / 16) * 16)
    small = cv2.resize(pixels, (w, h), interpolation=cv2.INTER_AREA)
    tensor = torch.tensor(small, device='cuda', dtype=torch.float32).permute(2, 0, 1)[None] / 127.5 - 1
    return {'img': tensor, 'true_shape': torch.tensor([[h, w]], device='cuda', dtype=torch.int32), 'idx': [index], 'instance': [str(index)]}, np.array([width / w, height / h])


def colors(pixels, xy):
    x = np.round(xy[:, 0]).astype(int).clip(0, pixels.shape[1] - 1)
    y = np.round(xy[:, 1]).astype(int).clip(0, pixels.shape[0] - 1)
    return pixels[y, x].astype('float32') / 255


def fill(pred, matched_xy, anchors, factor, cam, pixels):
    key = 'pts3d' if 'pts3d' in pred else 'pts3d_in_other_view'
    neural = pred[key][0].cpu().numpy()
    confidence = pred['desc_conf'][0].cpu().numpy()
    q = np.round(matched_xy / factor).astype(int)
    q[:, 0] = q[:, 0].clip(0, neural.shape[1] - 1)
    q[:, 1] = q[:, 1].clip(0, neural.shape[0] - 1)
    fit = similarity(neural[q[:, 1], q[:, 0]], anchors)
    if fit is None:
        return np.empty((0, 3)), np.empty((0, 3)), {'status': 'insufficient registration anchors'}
    scale, rotation, translation, residual = fit
    yy, xx = np.mgrid[1:neural.shape[0]:2, 1:neural.shape[1]:2]
    yx = np.c_[yy.ravel(), xx.ravel()]
    world = scale * neural[yx[:, 0], yx[:, 1]] @ rotation.T + translation
    depth = (world @ cam['R'].T + cam['t'])[:, 2]
    xy = yx[:, ::-1] * factor
    good = np.isfinite(world).all(1) & (depth > .05) & (depth < 6.) & (confidence[yx[:, 0], yx[:, 1]] > .2)
    xy, yx, depth = xy[good], yx[good], depth[good]
    # Nearby metric anchors correct local registered depth. Pixels/rays are observed.
    distance, near = cKDTree(q).query(yx[:, ::-1], k=min(6, len(q)))
    if distance.ndim == 1:
        distance, near = distance[:, None], near[:, None]
    anchor_depth = (anchors @ cam['R'].T + cam['t'])[:, 2]
    predicted_anchor = (scale * neural[q[:, 1], q[:, 0]] @ rotation.T + translation) @ cam['R'].T + cam['t']
    weight = 1 / np.maximum(distance, 1.) ** 2
    weight /= weight.sum(1, keepdims=True)
    correction = (weight * (anchor_depth - predicted_anchor[:, 2])[near]).sum(1)
    depth += correction * np.exp(-distance[:, 0] / 40)
    rays = np.c_[xy, np.ones(len(xy))] @ np.linalg.inv(cam['K']).T
    world = (rays * depth[:, None] - cam['t']) @ cam['R']
    return world, colors(pixels, xy), {'status': 'registered inferred depth', 'points': len(world), 'registration_median_m': residual}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', choices=['yogurt', 'textile'], required=True)
    parser.add_argument('--config', default='configs/4c4d_scene_001.json')
    parser.add_argument('--frame', type=int, default=0)
    parser.add_argument('--label', default='initialization')
    parser.add_argument('--max-points', type=int)
    args = parser.parse_args()
    cfg = read(ROOT / args.config)
    experiment = cfg['experiment_id']
    data = ROOT / 'data' / cfg.get('data_experiment_id',experiment) / args.dataset / 'edge_1280'
    manifest = read(data / 'manifest.json')
    norm = manifest['normalization']
    docs = ROOT / 'documentation' / experiment
    docs.mkdir(parents=True,exist_ok=True)
    output = ROOT / 'outputs' / experiment / args.dataset / args.label
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'initial_points.npz').exists():
        raise ValueError('Initialization already exists; preserve it rather than overwrite')
    if manifest['frames'][args.frame]['split'] != 'train':
        raise ValueError('Initialization must use a training timestamp')
    pixels = {cid: np.array(Image.open(data / 'images' / cid / f'{args.frame:06d}.png').convert('RGB')) for cid in manifest['cameras']}
    cams = {cid: camera(cal, norm) for cid, cal in manifest['cameras'].items()}
    sift = cv2.SIFT_create(nfeatures=20000)
    features = {cid: sift.detectAndCompute(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), None) for cid, image in pixels.items()}
    matcher = cv2.BFMatcher()
    clouds, rgb, kinds, audit = [], [], [], []
    for a, b in itertools.combinations(cams, 2):
        ka, da = features[a]
        kb, db = features[b]
        pairs = matcher.knnMatch(da, db, k=2) if da is not None and db is not None else []
        matches = [pair[0] for pair in pairs if len(pair)==2 and pair[0].distance < .7 * pair[1].distance]
        xy1 = np.array([ka[m.queryIdx].pt for m in matches],dtype=np.float64).reshape(-1,2)
        xy2 = np.array([kb[m.trainIdx].pt for m in matches],dtype=np.float64).reshape(-1,2)
        # Some sparse-camera pairs have fewer than the eight correspondences
        # required by this estimator. Keep that failed-match evidence and use
        # calibrated MASt3R for the pair rather than crashing the whole cloud.
        inlier = None
        if len(matches)>=8:
            _, inlier = cv2.findFundamentalMat(xy1, xy2, cv2.USAC_MAGSAC, 1., .999)
        robust = inlier.ravel().astype(bool) if inlier is not None else np.zeros(len(matches), bool)
        epi = epipolar(xy1, xy2, cams[a], cams[b])
        xyz, error, valid = triangulate(xy1, xy2, cams[a], cams[b])
        valid &= robust
        clouds.append(xyz[valid]);rgb.append((colors(pixels[a], xy1[valid]) + colors(pixels[b], xy2[valid])) / 2);kinds.append(np.zeros(valid.sum(), np.uint8))
        info = {'pair': [a, b], 'method': 'SIFT', 'ratio_matches': len(matches), 'robust_matches': int(robust.sum()), 'metric_points': int(valid.sum()), 'calibrated_epipolar_median_px': float(np.median(epi[robust])) if robust.any() else None, 'median_reprojection_px': float(np.median(error[valid])) if valid.any() else None}
        audit.append(info);print(json.dumps(info), flush=True)
    model = AsymmetricMASt3R.from_pretrained(str(ROOT / '.local/tools/mast3r/checkpoints/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth')).cuda().eval()
    views = {cid: tensor_view(image, i) for i, (cid, image) in enumerate(pixels.items())}
    with torch.inference_mode():
        for a, b in itertools.combinations(cams, 2):
            p1, p2 = model(views[a][0], views[b][0])
            q1, q2 = fast_reciprocal_NNs(p1['desc'][0], p2['desc'][0], subsample_or_initxy1=4, device='cuda', dist='dot', block_size=2048)
            xy1, xy2 = q1 * views[a][1], q2 * views[b][1]
            xyz, error, valid = triangulate(xy1, xy2, cams[a], cams[b])
            xyz, xy1, xy2, error = xyz[valid], xy1[valid], xy2[valid], error[valid]
            clouds.append(xyz);rgb.append((colors(pixels[a], xy1) + colors(pixels[b], xy2)) / 2);kinds.append(np.zeros(len(xyz), np.uint8))
            info = {'pair': [a, b], 'method': 'MASt3R', 'metric_points': len(xyz), 'median_reprojection_px': float(np.median(error)) if len(error) else None, 'inferred_fills': []}
            for cid, pred, matched in [(a, p1, xy1), (b, p2, xy2)]:
                points, color, record = fill(pred, matched, xyz, views[cid][1], cams[cid], pixels[cid])
                clouds.append(points);rgb.append(color);kinds.append(np.ones(len(points), np.uint8))
                info['inferred_fills'].append({'camera': cid, **record})
            audit.append(info);print(json.dumps(info), flush=True)
            del p1, p2
            torch.cuda.empty_cache()
    xyz, color, kind = np.concatenate(clouds), np.concatenate(rgb), np.concatenate(kinds)
    valid = np.isfinite(xyz).all(1) & np.isfinite(color).all(1)
    xyz, color, kind = xyz[valid], color[valid], kind[valid]
    # One spatial cloud, without assigning actor/table/background model identities.
    _, unique = np.unique(np.floor(xyz / .0015).astype('int64'), axis=0, return_index=True)
    xyz, color, kind = xyz[unique], color[unique], kind[unique]
    rng = np.random.default_rng(42)
    maximum = args.max_points or cfg['scene']['initial_max_points']
    if len(xyz) > maximum:
        chosen = rng.choice(len(xyz), maximum, replace=False)
        xyz, color, kind = xyz[chosen], color[chosen], kind[chosen]
    points = ((xyz - norm['center_m']) * norm['scale_per_m']).astype('float32')
    np.savez_compressed(output / 'initial_points.npz', points=points, colors=color.astype('float32'), support_kind=kind,
                        times=np.full((len(points),1),manifest['frames'][args.frame]['time'],np.float32))
    summary = {'dataset': args.dataset, 'points': len(xyz), 'stereo_points': int((kind == 0).sum()), 'inferred_depth_points': int((kind == 1).sum()),
               'world_bounds_m': [xyz.min(0).tolist(), xyz.max(0).tolist()], 'pairs': audit,
               'initial_points_sha256': hashlib.sha256((output / 'initial_points.npz').read_bytes()).hexdigest(),
               'source_frame': manifest['frames'][args.frame]['source_index'], 'first_pts_s': manifest['frames'][args.frame]['pts_s'],
               'local_frame':args.frame, 'time_normalized':manifest['frames'][args.frame]['time'],
               'policy': 'New full-scene cloud from one training timestamp. Points carry that timestamp. No separate/frozen base or older actor/table model.',
               'claim_limit': 'Calibrated matching plus explicitly inferred depth. Registration and reprojection are not independent metric accuracy.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    (docs / f'{args.dataset}_{args.label}_initialization.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf8')
    sheet = Image.new('RGB', (1500, 610), '#151c26')
    draw = ImageDraw.Draw(sheet)
    draw.text((15, 10), f'{args.dataset} whole-scene initialization: {len(xyz)} points / inferred depth labelled in JSON', fill='white')
    for col, (cid, image) in enumerate(pixels.items()):
        canvas = image.copy()
        xy = projection(xyz, cams[cid])
        for p in xy[::max(1, len(xy) // 5000)]:
            if np.isfinite(p).all() and 0 <= p[0] < image.shape[1] and 0 <= p[1] < image.shape[0]:
                cv2.circle(canvas, tuple(np.round(p).astype(int)), 1, (30, 220, 95), -1)
        small = Image.fromarray(canvas);small.thumbnail((490, 550))
        sheet.paste(small, (col * 500, 50));draw.text((col * 500 + 8, 34), cid, fill='white')
    sheet.save(docs / f'{args.dataset}_{args.label}_scene_seed_projection.jpg', quality=94)
    print('INITIALIZED ' + json.dumps({k: v for k, v in summary.items() if k != 'pairs'}), flush=True)


if __name__ == '__main__':
    main()
