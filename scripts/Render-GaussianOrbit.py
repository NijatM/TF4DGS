"""Render native-resolution RGB orbit videos directly from trained Gaussians.

No UI capture, resize, sharpening, image interpolation or model modification.
Both timelines use the recordings' source clocks and hold fitted states.
Lossless sample PNGs and render/encoding provenance accompany each local master.
"""
import argparse
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
import torch
from gsplat import rasterization


ROOT = Path(__file__).resolve().parents[1]
KEYS = ['means', 'quats', 'scales', 'opacity', 'colors']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def load(path):
    with np.load(path) as source:
        arrays = {k: source[k].copy() for k in KEYS}
    assert all(np.isfinite(v).all() for v in arrays.values())
    return {k: torch.tensor(v, device='cuda', dtype=torch.float32) for k, v in arrays.items()}


def multiply(a, b):
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack((aw*bw-ax*bx-ay*by-az*bz, aw*bx+ax*bw+ay*bz-az*by,
                        aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw), -1)


class Scene:
    def __init__(self, dataset):
        self.dataset = dataset
        if dataset == 'textile':
            self.source = ROOT / 'outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json'
            sequence = read(self.source)
            if sequence['status'] != 'complete' or len(sequence['frames']) != 214:
                raise ValueError('Finish the selected full textile baseline first')
            self.entries = sequence['frames']
            self.static_path = ROOT / sequence['table_model']
            self.actor = None
            self.duration = math.ceil(self.entries[-1]['time_s'] * 30) / 30
            self.center = np.array([.175, .10, -.045])
            self.azimuth, self.elevation, self.radius = 95., 48., .57
            self.focal_per_height = 850 / 700
            self.timing = '30fps camera path; latest fitted textile state held at each real source timestamp'
        else:
            self.source = ROOT / 'outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid/canonical_actor.npz'
            motion = read(self.source.parent / 'motion.json')
            self.poses_path = ROOT / motion['poses'].replace('\\', '/')
            poses = read(self.poses_path)
            self.entries = [dict(index=i, **f) for i, f in enumerate(poses['frames']) if f and f['valid']]
            if [f['index'] for f in self.entries] != motion['valid_indices'] or len(self.entries) != 53:
                raise ValueError('Yogurt actor and supported poses differ')
            self.actor = load(self.source)
            self.static_path = ROOT / 'outputs/dynamic_yogurt_001/static_background_03/trained_01/static_background.npz'
            self.duration = math.ceil((self.entries[-1]['time_s'] - self.entries[0]['time_s']) * 30) / 30
            self.center = np.array([.175, .105, -.025])
            self.azimuth, self.elevation, self.radius = 95.13796510437624, 42.55506917267627, .91
            self.focal_per_height = 900 / 650
            self.timing = 'Original yogurt source clock at real speed; latest supported pose held, including unsupported gaps; no pose interpolation'
        self.static = load(self.static_path)
        self.times = np.array([f['time_s'] for f in self.entries])
        self.source_start = float(self.times[0])

    @lru_cache(maxsize=2)
    def frame(self, ordinal):
        entry = self.entries[ordinal]
        if self.dataset == 'textile':
            actor = load(ROOT / entry['model'])
        else:
            rotation = Rotation.from_rotvec(entry['rvec'])
            r = torch.tensor(rotation.as_matrix(), device='cuda', dtype=torch.float32)
            q = torch.tensor(rotation.as_quat()[[3, 0, 1, 2]], device='cuda', dtype=torch.float32)
            t = torch.tensor(entry['translation_m'], device='cuda', dtype=torch.float32)
            actor = {**self.actor, 'means': self.actor['means'] @ r.T + t,
                     'quats': multiply(q.expand(len(self.actor['means']), 4), self.actor['quats'])}
        return {k: torch.cat((actor[k], self.static[k])) for k in KEYS}

    @torch.no_grad()
    def render(self, video_time, width, height):
        fraction = min(1., video_time / self.duration)
        source_time = min(float(self.times[-1]), self.source_start + video_time)
        ordinal = int(np.clip(np.searchsorted(self.times, source_time + 1e-9, side='right') - 1,
                              0, len(self.entries)-1))
        model = self.frame(ordinal)
        azimuth = self.azimuth + 45 * math.sin(2 * math.pi * fraction)
        az, el = np.deg2rad([azimuth, self.elevation])
        position = self.center + self.radius * np.array([
            math.cos(az)*math.cos(el), math.sin(az)*math.cos(el), -math.sin(el)])
        forward = self.center - position
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, [0., 0., -1.])
        right /= np.linalg.norm(right)
        rotation = np.array([right, np.cross(forward, right), forward])
        view = np.eye(4)
        view[:3, :3], view[:3, 3] = rotation, -rotation @ position
        # Preserve vertical framing; 16:9 adds genuine horizontal scene coverage.
        focal = self.focal_per_height * height
        intrinsics = np.array([[focal, 0, width/2], [0, focal, height/2], [0, 0, 1.]])
        rgb, alpha, _ = rasterization(model['means'], model['quats'], model['scales'],
            model['opacity'], model['colors'],
            torch.tensor(view, device='cuda', dtype=torch.float32)[None],
            torch.tensor(intrinsics, device='cuda', dtype=torch.float32)[None],
            width, height, packed=False, near_plane=.01, far_plane=10,
            rasterize_mode='antialiased')
        pixels = ((rgb[0] + (1-alpha[0])*.92).clamp(0, 1)*255).to(torch.uint8).cpu().numpy()
        return pixels, dict(source_index=self.entries[ordinal]['index'],
                            source_time_s=self.entries[ordinal]['time_s'],
                            azimuth_deg=azimuth, elevation_deg=self.elevation,
                            distance_m=self.radius, gaussians=len(model['means']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=['yogurt', 'textile'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--width', type=int, default=3840)
    parser.add_argument('--height', type=int, default=2160)
    parser.add_argument('--crf', type=int, default=16)
    parser.add_argument('--preview-only', action='store_true')
    args = parser.parse_args()
    if not (640 <= args.width <= 3840 and 480 <= args.height <= 2160 and 12 <= args.crf <= 20):
        raise ValueError('Invalid native rendering/quality budget')
    output = (ROOT / args.output).resolve()
    output.relative_to((ROOT / 'outputs').resolve())
    if output.exists():
        raise FileExistsError('Retain earlier render attempts; choose a new output')
    output.mkdir(parents=True)
    scene = Scene(args.dataset)
    tool = next(t for t in read(ROOT / 'static-tools.json')['portable_tools'] if t['name'] == 'FFmpeg')
    start = time.perf_counter()
    count = round(scene.duration * 30) + 1
    sample_indexes = sorted(set([0, count//4, count//2, 3*count//4, count-1]))
    if args.preview_only:
        for n in sample_indexes[:3]:
            pixels, state = scene.render(min(n/30, scene.duration), args.width, args.height)
            path = output / f'preview_{n:06d}.png'
            Image.fromarray(pixels).save(path)
            print(json.dumps(dict(preview=path.relative_to(ROOT).as_posix(), **state)), flush=True)
        print(json.dumps(dict(elapsed_s=time.perf_counter()-start,
                              peak_cuda_bytes=torch.cuda.max_memory_allocated())), flush=True)
        return
    target = output / f'{args.dataset}_reconstruction_orbit.mp4'
    command = [tool['executable_path'], '-hide_banner', '-nostdin', '-n',
               '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size',
               f'{args.width}x{args.height}', '-framerate', '30', '-i', 'pipe:0', '-an',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', str(args.crf),
               '-threads', '8', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)]
    states = []
    with (output / 'encode.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
        try:
            for n in range(count):
                t = min(n/30, scene.duration)
                pixels, state = scene.render(t, args.width, args.height)
                process.stdin.write(pixels.tobytes())
                states.append(dict(frame=n, video_time_s=n/30, **state))
                if n in sample_indexes:
                    Image.fromarray(pixels).save(output / f'reference_{n:06d}.png')
                if n % 90 == 0:
                    print(json.dumps(dict(dataset=args.dataset, rendered=n+1, requested=count,
                                          elapsed_s=time.perf_counter()-start)), flush=True)
            process.stdin.close()
            if process.wait() != 0:
                raise RuntimeError('Video encoder failed; see preserved encode.log')
        except BaseException as error:
            process.kill()
            process.wait()
            (output / 'failure.json').write_text(json.dumps(dict(
                status='failed render/encode attempt retained', error=str(error),
                rendered_frames=len(states), requested_frames=count,
                recorded_utc=datetime.now(timezone.utc).isoformat()), indent=2)+'\n', encoding='utf-8')
            raise
    probe = json.loads(subprocess.check_output([tool['ffprobe_path'], '-v', 'error',
        '-show_streams', '-show_format', '-of', 'json', str(target)], text=True))
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    if (video['width'], video['height']) != (args.width, args.height) or int(video['nb_frames']) != count:
        raise ValueError('Native video dimensions/frame count differ from the renderer')
    indexes = {s['source_index'] for s in states}
    if indexes != {f['index'] for f in scene.entries}:
        raise ValueError('The full source state sequence must remain represented')
    result = dict(status='native Gaussian render encoded', dataset=args.dataset,
        recorded_utc=datetime.now(timezone.utc).isoformat(), filename=target.name,
        width=args.width, height=args.height, fps=30, frames=count,
        duration_s=float(probe['format']['duration']), bytes=target.stat().st_size,
        sha256=digest(target), native_rasterization=True, image_upscaling=False,
        reconstructed_states=len(indexes), source=scene.source.relative_to(ROOT).as_posix(),
        source_sha256=digest(scene.source), static_model=scene.static_path.relative_to(ROOT).as_posix(),
        static_sha256=digest(scene.static_path), crf=args.crf, encoder='libx264',
        pixel_format=video['pix_fmt'], faststart=True, camera_arc_degrees=90,
        timing=scene.timing, gaussian_parameters_changed=False, pose_interpolation=False,
        source_time_start_s=scene.source_start, source_time_end_s=float(scene.times[-1]),
        continuous_textile_deformation=False, independent_30hz_geometry=False,
        rendering_elapsed_s=time.perf_counter()-start,
        peak_cuda_bytes=torch.cuda.max_memory_allocated(), source_samples=states,
        lossless_reference_frames=sample_indexes)
    (output / 'render_manifest.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='source_samples'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
