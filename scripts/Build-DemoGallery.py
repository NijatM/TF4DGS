"""Reproduce the historical browser-cropped demo attempt (quality rejected).

No model, pose, appearance or camera motion is changed. Clean videos crop the
reconstruction viewport from lossless browser paints, not from an existing MP4.
Original UI clips and chronological reports are retained. The selected native
4K workflow uses Render-GaussianOrbit.py and Finalize-NativeDemoGallery.py.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def probe(path, tool):
    info = json.loads(subprocess.check_output([
        tool['ffprobe_path'], '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path)], text=True))
    stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    return dict(codec=stream['codec_name'], pixel_format=stream['pix_fmt'],
                width=stream['width'], height=stream['height'],
                fps=stream['avg_frame_rate'], duration_s=float(info['format']['duration']),
                bytes=path.stat().st_size, sha256=sha(path))


def selected_frames(capture, dataset):
    folder = capture.parent
    record = read(capture)
    frames = sorted(record['frames'], key=lambda f: f['timestamp_s'])
    if dataset == 'yogurt':
        # The stable mode-label pixels identify the transition out of RGB.
        # Actual screenshots and the captured phase metadata verify this region.
        label_box = (1140, 518, 1330, 538)
        with Image.open(folder / frames[0]['filename']) as image:
            reference = image.crop(label_box).tobytes()
        end = None
        for i, frame in enumerate(frames[1:], 1):
            with Image.open(folder / frame['filename']) as image:
                if image.crop(label_box).tobytes() != reference:
                    end = frame['timestamp_s']
                    frames = frames[:i]
                    break
        if end is None:
            raise ValueError('RGB phase boundary was not found')
        phase = record['playback_state']['phases'][0]
        if phase['mode'] != 'rgb' or len(phase['source_samples']) != 121:
            raise ValueError('Unexpected yogurt RGB orbit')
        samples = phase['source_samples']
        supported = {f['index'] for f in record['initial_state']['frames']}
        if {f['index'] for f in samples} != supported:
            raise ValueError('RGB orbit does not include every supported pose')
        # 8px inset removes CSS rounded corners; no header, controls or status.
        crop = (91, 157, 990, 710)
        skipped = 0
    else:
        # One startup paint still shows the previous camera's shorter image.
        # Start at the first fully rendered orbit viewport; source t=0 remains.
        skipped = 0
        while frames:
            with Image.open(folder / frames[0]['filename']) as image:
                pixel = image.getpixel((1110, 855))[:3]
            if pixel != (19, 27, 37):
                break
            frames = frames[1:]
            skipped += 1
        if skipped != 1 or len(frames) != 958:
            raise ValueError('Unexpected textile startup/viewport layout')
        samples = record['playback_state']['source_samples']
        if record['playback_state']['mode'] != 'rgb' or len(samples) != 214:
            raise ValueError('Expected all 214 final textile RGB states')
        end = frames[-1]['timestamp_s'] + .8
        crop = (58, 128, 1060, 736)
    angles = [s['azimuth_deg'] for s in samples]
    center = record['initial_state'].get('orbit', {}).get('center_azimuth_deg', 95.) if dataset == 'yogurt' else 95.
    if min(angles) > center - 44.9 or max(angles) < center + 44.9:
        raise ValueError('Orbit does not cover both sides of the 90-degree arc')
    return record, frames, end, crop, samples, skipped


def clean_clip(dataset, source, target, cache, tool):
    record, frames, end, crop, samples, skipped = selected_frames(source, dataset)
    folder = source.parent
    width, height = record['width'], record['height']
    x, y, w, h = crop
    if min(crop) < 0 or x + w > width or y + h > height or w % 2 or h % 2:
        raise ValueError('Invalid reconstruction viewport crop')
    for frame in frames:
        name = frame['filename']
        if not re.fullmatch(r'frame_\d{6}\.png', name):
            raise ValueError('Unexpected paint filename')
        (folder / name).resolve(strict=True).relative_to(folder.resolve())
    cache.mkdir(parents=True)
    lines = ['ffconcat version 1.0']
    times = [f['timestamp_s'] for f in frames]
    for i, frame in enumerate(frames):
        next_time = times[i + 1] if i + 1 < len(times) else end
        path = (folder / frame['filename']).as_posix()
        if "'" in path or '\n' in path:
            raise ValueError('Unsupported quote/newline in capture path')
        lines += [f"file '{path}'", 'option framerate 1000',
                  f'duration {max(.001, next_time - times[i]):.9f}']
    lines += [f"file '{(folder / frames[-1]['filename']).as_posix()}'", 'option framerate 1000']
    concat = cache / 'frames.ffconcat'
    concat.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    duration = end - times[0]
    command = [tool['executable_path'], '-hide_banner', '-nostdin', '-n',
               '-f', 'concat', '-safe', '0', '-i', str(concat), '-vf',
               f'crop={w}:{h}:{x}:{y},fps=30', '-t', f'{duration:.9f}', '-an',
               '-c:v', 'libx264', '-preset', 'slow', '-tune', 'animation',
               '-crf', '20', '-threads', '8', '-pix_fmt', 'yuv420p',
               '-movflags', '+faststart', str(target)]
    print(json.dumps(dict(encoding=dataset, actual_paints=len(frames), crop=crop,
                          duration_s=duration)), flush=True)
    with (cache / 'encode.log').open('w', encoding='utf-8') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    info = probe(target, tool)
    if (info['width'], info['height']) != (w, h) or abs(info['duration_s'] - duration) > .067:
        raise ValueError('Clean video dimensions/timing differ from captured paints')
    # Decode representative output frames for actual visual review.
    panel = Image.new('RGB', (1500, 420), '#17212b')
    draw = ImageDraw.Draw(panel)
    for col, t in enumerate([.2, info['duration_s'] / 2, info['duration_s'] - .2]):
        decoded = cache / f'decoded_{col}.png'
        subprocess.run([tool['executable_path'], '-hide_banner', '-loglevel', 'error',
                        '-nostdin', '-n', '-ss', str(t), '-i', str(target),
                        '-frames:v', '1', str(decoded)], check=True)
        with Image.open(decoded) as image:
            pixels = np.asarray(image.convert('RGB'))
            if pixels.std() < 8:
                raise ValueError('Empty reconstruction video frame')
            thumb = ImageOps.contain(image.convert('RGB'), (490, 360))
            panel.paste(thumb, (col * 500 + (500 - thumb.width) // 2, 35))
            if col == 1:
                image.convert('RGB').save(target.with_suffix('.jpg'), quality=94)
        draw.text((col * 500 + 8, 8), f'{dataset} RGB | {t:.2f}s', fill='white')
    panel.save(cache / 'decoded_review.jpg', quality=94)
    metadata = dict(filename=target.name, variant='reconstruction_only', **info,
                    source_capture=source.relative_to(ROOT).as_posix(),
                    source_capture_sha256=sha(source), source_png_paints=len(frames),
                    skipped_startup_paints=skipped, crop_xywh=list(crop),
                    crop_reason='Reconstruction viewport only; 8px CSS-corner inset',
                    source_samples=samples, source_states_displayed=len({s['index'] for s in samples}),
                    camera_arc_degrees=90, camera_relative_range_degrees=[-45, 45],
                    camera_path='center -> +45 -> center -> -45 -> center',
                    source_duration_s=samples[-1]['time_s'] - samples[0]['time_s'],
                    timing='Original browser paint timestamps; no geometry/motion interpolation',
                    encoder='libx264', preset='slow', crf=20, faststart=True,
                    recompressed_existing_mp4=False, reconstruction_changed=False)
    target.with_suffix('.capture.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('documentation/demos'))
    parser.add_argument('--attempt', default='demo_gallery_01')
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.relative_to((ROOT / 'documentation').resolve())
    if output.exists() or not re.fullmatch(r'[A-Za-z0-9_-]+', args.attempt):
        raise ValueError('Use a new gallery folder and simple unique attempt name')
    cache = ROOT / '.local/workflows/dynamic_setup' / args.attempt
    if cache.exists():
        raise FileExistsError('Preserve earlier demo attempts')
    tool = next(t for t in read(ROOT / 'static-tools.json')['portable_tools'] if t['name'] == 'FFmpeg')
    sources = {
        'yogurt': ('documentation/dynamic_capture_001/videos/yogurt_gaussian_orbit.mp4',
                   '.local/workflows/dynamic_setup/web_recording_01/yogurt_gaussian_fitted_capture/capture.json'),
        'textile': ('documentation/dynamic_textile_001/videos/textile_rgb_orbit.mp4',
                    '.local/workflows/dynamic_setup/textile_reconstruction_02/browser_captures/rgb_orbit_02/capture.json')}
    output.mkdir(parents=True)
    clips = []
    for dataset, (ui_path, capture_path) in sources.items():
        folder = output / dataset
        folder.mkdir()
        ui_source = ROOT / ui_path
        ui = folder / f'{dataset}_ui.mp4'
        shutil.copyfile(ui_source, ui)
        if sha(ui) != sha(ui_source):
            raise ValueError('UI copy differs from the validated final source')
        shutil.copyfile(ui_source.with_suffix('.jpg'), ui.with_suffix('.jpg'))
        ui_meta = read(ui_source.with_suffix('.capture.json'))
        ui_meta.update(filename=ui.name, poster=ui.with_suffix('.jpg').name,
                       variant='interface', source_video=ui_path, source_video_sha256=sha(ui_source),
                       byte_identical_to_validated_final=True)
        ui.with_suffix('.capture.json').write_text(json.dumps(ui_meta, indent=2) + '\n', encoding='utf-8')
        clips.append(dict(dataset=dataset, path=ui.relative_to(output).as_posix(), **probe(ui, tool)))
        clean = folder / f'{dataset}_reconstruction_orbit.mp4'
        meta = clean_clip(dataset, ROOT / capture_path, clean, cache / dataset, tool)
        clips.append(dict(dataset=dataset, path=clean.relative_to(output).as_posix(),
                          **{k: meta[k] for k in ['bytes', 'duration_s', 'width', 'height', 'sha256']}))
    # Full decode each final clip, not just its header or representative frames.
    for clip in clips:
        subprocess.run([tool['executable_path'], '-hide_banner', '-v', 'error',
                        '-nostdin', '-i', str(output / clip['path']),
                        '-map', '0:v:0', '-f', 'null', '-'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    summary = dict(status='complete; hashes, timing and full decoding passed',
                   recorded_utc=datetime.now(timezone.utc).isoformat(), experiments=['yogurt', 'textile'],
                   clips=clips, total_video_bytes=sum(c['bytes'] for c in clips),
                   ui_copies_byte_identical=True, clean_orbits_encoded_from_lossless_png=True,
                   camera_arc_degrees=90, model_parameters_changed=False,
                   git_staging_commit_push_performed=False)
    (output / 'validation.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
