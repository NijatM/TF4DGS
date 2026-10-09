"""Full-frame data for one joint temporal scene; no actor/base model merge."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--edge', type=int, default=1280)
    parser.add_argument('--datasets', nargs='+', default=['yogurt', 'textile'])
    parser.add_argument('--config', default='configs/4c4d_scene_001.json')
    args = parser.parse_args()
    cfg = read(ROOT / args.config)
    tool = next(t for t in read(ROOT / 'static-tools.json')['portable_tools'] if t['name'] == 'FFmpeg')
    docs = ROOT / 'documentation' / cfg['experiment_id']
    docs.mkdir(parents=True, exist_ok=True)
    norm = cfg['scene']['normalization']
    for dataset in args.datasets:
        spec = cfg['datasets'][dataset]
        frame_count = spec['end_frame_exclusive'] - spec['start_frame']
        if frame_count < 2: raise ValueError('Need at least two timeline samples')
        session_path = ROOT / spec['session']
        session = read(session_path)
        dest = ROOT / 'data' / cfg['experiment_id'] / dataset / f'edge_{args.edge}'
        dest.mkdir(parents=True, exist_ok=True)
        cameras, provenance = {}, {}
        for item in session['cameras']:
            cid = item['id']
            cal_path = session_path.parent / item['calibration']
            cal = read(cal_path)
            width, height = cal['image_size']
            scale = min(1., args.edge / max(width, height))
            nw, nh = int(round(width * scale / 2)) * 2, int(round(height * scale / 2)) * 2
            sx, sy = nw / width, nh / height
            out = dest / 'images' / cid
            out.mkdir(parents=True, exist_ok=True)
            video = session_path.parent / item['video']
            marker = out / 'extraction.json'
            settings = {'video_sha256': sha(video), 'first': spec['start_frame'], 'last_exclusive': spec['end_frame_exclusive'], 'width': nw, 'height': nh}
            if not marker.exists() or read(marker) != settings or len(list(out.glob('*.png'))) != frame_count:
                filt = f"select=between(n\\,{spec['start_frame']}\\,{spec['end_frame_exclusive']-1}),scale={nw}:{nh}:flags=lanczos"
                subprocess.run([tool['executable_path'], '-hide_banner', '-loglevel', 'error', '-y', '-noautorotate', '-i', str(video), '-vf', filt, '-fps_mode', 'passthrough', '-frames:v', str(frame_count), '-start_number', '0', str(out / '%06d.png')], check=True)
                marker.write_text(json.dumps(settings, indent=2), encoding='utf8')
            if len(list(out.glob('*.png'))) != frame_count:
                raise ValueError(f'Expected exactly {frame_count} native source frames')
            fx, fy, cx, cy = cal['params']
            rotation = np.array(cal['world_to_camera']['R'])
            translation = np.array(cal['world_to_camera']['t'])
            cameras[cid] = {'width': nw, 'height': nh, 'fx': fx * sx, 'fy': fy * sy,
                            'cx': (cx + .5) * sx - .5, 'cy': (cy + .5) * sy - .5,
                            'R': rotation.tolist(), 't': ((translation + rotation @ norm['center_m']) * norm['scale_per_m']).tolist(),
                            'crop_xyxy': [0, 0, width, height], 'source_image_size': [width, height]}
            # Time-independent motion priority from training RGB only. Every pixel
            # contributes to loss; this never masks out the surroundings or hands.
            count = 0
            mean = np.zeros((nh, nw, 3), np.float32)
            m2 = np.zeros_like(mean)
            for i in range(frame_count):
                if i % 6 == 5:
                    continue
                pixels = np.array(Image.open(out / f'{i:06d}.png').convert('RGB'), dtype=np.float32) / 255
                count += 1
                delta = pixels - mean
                mean += delta / count
                m2 += delta * (pixels - mean)
            activity = np.sqrt((m2 / max(count - 1, 1)).mean(2)) > .04
            activity = cv2.dilate(activity.astype('uint8'), np.ones((9, 9), np.uint8)) > 0
            Image.fromarray(activity.astype('uint8') * 255).save(dest / f'{cid}_motion_priority.png')
            source = np.array(Image.open(out / '000000.png').convert('RGB'))
            overlay = source.copy()
            overlay[activity] = (source[activity] * .65 + np.array([30, 240, 100]) * .35).astype('uint8')
            Image.fromarray(overlay).save(docs / f'{dataset}_{cid}_full_frame_edge_{args.edge}.jpg', quality=92)
            provenance[cid] = {**settings, 'video': str(video.relative_to(ROOT)).replace('\\', '/'),
                               'calibration_sha256': sha(cal_path), 'motion_priority_area_fraction': float(activity.mean()),
                               'images_sha256': [sha(out / f'{i:06d}.png') for i in range(frame_count)]}
            print(json.dumps({'dataset': dataset, 'camera': cid, 'size': [nw, nh], 'motion_priority_fraction': float(activity.mean()), 'full_frame': True}), flush=True)
        frames = [{'index': i, 'source_index': spec['start_frame'] + i,
                   'pts_s': (spec['start_frame'] + i) * 1001 / 30000,
                   'time': i / (frame_count-1), 'split': 'test' if i % 6 == 5 else 'train'} for i in range(frame_count)]
        manifest = {'experiment_id': cfg['experiment_id'], 'dataset': dataset, 'edge': args.edge,
                    'cameras': cameras, 'frames': frames, 'normalization': norm, 'provenance': provenance,
                    'config_sha256': sha(ROOT / args.config),
                    'scene_policy': 'Full frames, all pixels supervised, one jointly optimized temporal model; no separate or frozen background.'}
        (dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
        sheet = Image.new('RGB', (1500, 3 * 285 + 40), '#141b25')
        draw = ImageDraw.Draw(sheet)
        draw.text((15, 12), f'{dataset}: WHOLE FRAME / ONE JOINT SCENE / edge {args.edge}', fill='white')
        for row, cid in enumerate(cameras):
            for col, i in enumerate([0, frame_count//3, 2*frame_count//3, frame_count-1]):
                im = Image.open(dest / 'images' / cid / f'{i:06d}.png')
                im.thumbnail((365, 250))
                sheet.paste(im, (col * 375 + (375 - im.width) // 2, row * 285 + 40))
                draw.text((col * 375 + 8, row * 285 + 300), f'{cid} / source {frames[i]["source_index"]} / {frames[i]["pts_s"]:.3f}s', fill='white')
        sheet.save(docs / f'{dataset}_full_scene_inputs_edge_{args.edge}.jpg', quality=94, subsampling=0)


if __name__ == '__main__':
    main()
