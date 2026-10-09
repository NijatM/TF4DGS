"""Validate and install native 4K orbit masters in the existing demo gallery.

Retains the rejected cropped videos and all diagnostics under ignored .local.
The selected UI recordings are unchanged. Git staging/publication is manual.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def probe(path, tool):
    return json.loads(subprocess.check_output([tool['ffprobe_path'], '-v', 'error',
        '-show_streams', '-show_format', '-of', 'json', str(path)], text=True))


def validate_native(folder, cache, tool):
    manifest = read(folder/'render_manifest.json')
    path = folder/manifest['filename']
    info = probe(path, tool)
    video = next(s for s in info['streams'] if s['codec_type']=='video')
    if ((video['width'], video['height']) != (3840, 2160)
            or video['avg_frame_rate'] != '30/1'
            or int(video['nb_frames']) != manifest['frames']
            or sha(path) != manifest['sha256']):
        raise ValueError('The video differs from the native render manifest')
    if path.stat().st_size >= 100*1024*1024:
        raise ValueError('Keep this master local; it exceeds the regular Git per-file budget')
    packets = json.loads(subprocess.check_output([tool['ffprobe_path'], '-v', 'error',
        '-select_streams', 'v:0', '-show_packets', '-show_entries', 'packet=pts_time',
        '-of', 'json', str(path)], text=True))['packets']
    pts = np.sort([float(p['pts_time']) for p in packets])
    if len(pts) != manifest['frames'] or not np.allclose(pts, np.arange(len(pts))/30, atol=1e-6):
        raise ValueError('Every rendered frame must have its own constant-30fps timestamp')
    cache.mkdir(parents=True)
    # Decode the entire video while extracting the exact five lossless-reference frames.
    refs = manifest['lossless_reference_frames']
    selection = '+'.join(f'eq(n\\,{n})' for n in refs)
    subprocess.run([tool['executable_path'], '-hide_banner', '-v', 'error', '-nostdin', '-n',
        '-i', str(path), '-vf', f'select={selection}', '-fps_mode', 'vfr',
        '-start_number', '0', str(cache/'decoded_%02d.png')], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    quality = []
    panel = Image.new('RGB', (1600, 510), '#17212b')
    draw = ImageDraw.Draw(panel)
    for ordinal, n in enumerate(refs):
        source = np.asarray(Image.open(folder/f'reference_{n:06d}.png').convert('RGB'), dtype=np.float32)
        decoded_path = cache/f'decoded_{ordinal:02d}.png'
        with Image.open(decoded_path) as image:
            decoded = np.asarray(image.convert('RGB'), dtype=np.float32)
            mse = float(np.mean((source-decoded)**2))
            psnr = float(10*np.log10(255**2/max(mse, 1e-12)))
            quality.append(dict(frame=n, psnr_rgb_db=psnr,
                note='Decoded RGB against the exact same native lossless Gaussian render'))
            if ordinal in [0, 2, 4]:
                col = [0, 2, 4].index(ordinal)
                thumb = ImageOps.contain(image.convert('RGB'), (520, 430))
                panel.paste(thumb, (col*533+(533-thumb.width)//2, 48))
                draw.text((col*533+10, 12), f'{manifest["dataset"]} native 4K | frame {n}', fill='white')
    panel.save(cache/'decoded_review.jpg', quality=94)
    report = dict(full_decode_passed=True, frames=len(pts), fps='30/1',
        maximum_timestamp_error_s=float(np.max(np.abs(pts-np.arange(len(pts))/30))),
        missing_or_duplicate_presentation_timestamps=0, lossless_reference_comparison=quality,
        mean_reference_psnr_rgb_db=float(np.mean([q['psnr_rgb_db'] for q in quality])),
        compression_quality_is_not_reconstruction_accuracy=True)
    write(cache/'validation.json', report)
    print(json.dumps(dict(dataset=manifest['dataset'], **report)), flush=True)
    return manifest, report


def stutter_report():
    sources = {
        'yogurt': '.local/workflows/dynamic_setup/web_recording_01/yogurt_gaussian_fitted_capture/capture.json',
        'textile': '.local/workflows/dynamic_setup/textile_reconstruction_02/browser_captures/rgb_orbit_02/capture.json'}
    data = []
    for name, source in sources.items():
        capture = read(ROOT/source)
        times = np.array([f['timestamp_s'] for f in capture['frames']])
        dt = np.diff(times)
        data.append(dict(dataset=name, source_capture=source, source_sha256=sha(ROOT/source),
            browser_paints=len(times), wall_duration_s=float(times[-1]-times[0]),
            average_captured_fps=float(1/dt.mean()),
            median_paint_interval_s=float(np.median(dt)),
            p95_paint_interval_s=float(np.quantile(dt, .95)),
            largest_paint_interval_s=float(dt.max()),
            intervals_over_66ms=int((dt>2/30).sum()), intervals_over_100ms=int((dt>.1).sum())))
    return dict(recorded_utc=datetime.now(timezone.utc).isoformat(), old_browser_captures=data,
        causes=['Clean videos were limited to approximately 1K browser viewport pixels.',
            'Irregular browser paints skipped camera renders; encoding at 30fps repeated those paints.',
            'Textile geometry consists of 214 separate fits, approximately 5Hz; model changes can pop.',
            'Yogurt has 53 supported poses and gaps up to 2.002s; holds and jumps remain in those gaps.'],
        fix='Native 4K offline rasterization of every camera frame, source-time playback and constant 30fps encoding.',
        camera_frame_drops_in_new_file=0, fabricated_material_motion=False,
        underlying_temporal_model_fixed=False,
        remaining='A temporally consistent reconstruction is still required to remove geometric popping; slower recording alone cannot repair missing poses or independent geometry.')


def gallery(clips):
    by_path = {c['path']:c for c in clips}
    cards = []
    for name, title in [('yogurt', 'Yogurt'), ('textile', 'Textile')]:
        articles = []
        for kind, heading in [('ui', 'Viewer interface'), ('reconstruction_orbit', 'Native 4K reconstruction')]:
            c = by_path[f'{name}/{name}_{kind}.mp4']
            label = ('RGB and analysis controls' if kind=='ui' else '3840 x 2160 / every camera frame rendered / 30 fps')
            articles.append(f'''<article><h3>{heading}</h3>
<p>{label}<br>{c['duration_s']:.2f} s / {c['bytes']/1e6:.2f} MB</p>
<video id="{name}-{'ui' if kind=='ui' else 'clean'}" controls playsinline preload="metadata"
poster="{c['path'][:-4]}.jpg" src="{c['path']}?v=native4k"></video></article>''')
        note = ('Original source speed; all 53 supported rigid poses. Pose gaps remain held, including one 2-second gap.'
            if name=='yogurt' else 'All 214 fitted textile states and the current table. The camera is 30fps; fitted shape updates remain about 5Hz.')
        cards.append(f'<section><h2>{title}</h2><div class="grid">'+''.join(articles)+f'</div><p class="note">{note}</p></section>')
    total = sum(c['bytes'] for c in clips)/1e6
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>TF4DGS experiment demos</title>
<style>:root{{color-scheme:dark;font-family:system-ui,sans-serif;background:#111820;color:#e9eff5}}
body{{margin:0}}main{{max-width:1240px;margin:auto;padding:32px 24px 48px}}h1{{margin:0 0 10px;font-size:32px}}
h2{{margin:30px 0 14px;font-size:24px}}p{{line-height:1.6;color:#bac8d6}}header p{{margin:0}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}article{{background:#1b2632;border:1px solid #344454;border-radius:12px;overflow:hidden}}
article h3{{font-size:18px;margin:16px 18px 8px}}article p{{font-size:14px;margin:0 18px 16px}}
video{{display:block;width:100%;background:#0b1016}}a{{color:#9bd1ff}}.note{{font-size:14px}}
footer{{margin-top:30px;border-top:1px solid #344454;padding-top:12px}}
@media(max-width:780px){{.grid{{grid-template-columns:1fr}}main{{padding:24px 16px}}}}</style></head>
<body><main><header><h1>TF4DGS experiment demos</h1><p>Yogurt and textile / elevated +/-45 degree orbital sweep</p></header>
{''.join(cards)}<footer><p class="note">{total:.2f} MB total / <a href="README.md">Recording notes</a> /
<a href="validation.json">Validation</a> / <a href="stutter_diagnosis.json">Stutter diagnosis</a><br>
Use the player's full-screen button to inspect the native 4K videos.</p></footer></main>
<script>for(const v of document.querySelectorAll('video'))v.addEventListener('play',()=>{{for(const o of document.querySelectorAll('video'))if(o!==v)o.pause()}});</script>
</body></html>'''


def notes(clips):
    c = {entry['path']:entry for entry in clips}
    rows = []
    for name in ['yogurt', 'textile']:
        ui = c[f'{name}/{name}_ui.mp4']
        clean = c[f'{name}/{name}_reconstruction_orbit.mp4']
        rows.append(f"| {name.title()} | [{ui['duration_s']:.2f} s / {ui['bytes']/1e6:.2f} MB]({ui['path']}) | "
                    f"[{clean['duration_s']:.2f} s / {clean['bytes']/1e6:.2f} MB]({clean['path']}) |")
    return '''# Final experiment demos

Open [the gallery](index.html), or play the MP4 files directly. Each experiment
has its selected viewer-interface recording and a **native 3840 x 2160 / 30 fps**
RGB Gaussian orbit. Use the player's full-screen button to inspect fine detail.

| Experiment | Viewer interface | Native 4K reconstruction only |
| --- | --- | --- |
'''+ '\n'.join(rows)+f'''

The four videos total **{sum(x['bytes'] for x in clips)/1e6:.2f} MB**; the two new
4K videos total **{sum(x['bytes'] for x in clips if x['native_gaussian_render'])/1e6:.2f} MB**.
The UI files are unchanged copies of recordings already in Git, so identical
blobs are reused. Every selected MP4 is below 50 MiB. These paths use ordinary
Git; no LFS tracking rule is added. Models, footage, raw frames and local masters
remain ignored.

The clean videos are rasterized directly from the full-precision fitted
Gaussian models, with antialiasing and one render for **every output frame**.
They are not enlarged screen captures. H.264/yuv420p, CRF16, slow preset and
fast-start playback preserve detail with compact files. The camera follows an
elevated iPhone-side **center -> +45 degrees -> center -> -45 degrees -> center**
orbit. No UI, labels or overlays appear in the clean MP4s.

Offline rendering waits for each render and encoding step, so wall-clock
loading pauses cannot skip camera frames. Both clean videos play at the original
source speed; yogurt covers source time 7.2072-15.5155 s, rather than stretching
those poses into the former 22.7-second cinematic clip. The last state is padded
by less than two video frames to end the orbit.

**Camera smoothness and geometry continuity are separate.** Textile retains all
214 independently fitted states, approximately five shape updates per second.
It can still pop or flicker when the fitted state changes. Yogurt retains all
53 supported poses; unsupported gaps, including one 2.002-second gap, hold the
latest supported pose and can jump afterward. No missing movement, material
correspondences or intermediate cloth deformation are invented. A temporally
consistent reconstruction is required to resolve those model limitations.
The UI clips retain their original recording resolution and browser timing.

[Stutter diagnosis](stutter_diagnosis.json) records the old irregular browser
paints: about 19.6 fps averaged across yogurt's three modes and 22.5 fps for
textile RGB. [Validation](validation.json) verifies full decoding, exact 30 fps
presentation timestamps, dimensions, hashes and comparison with five lossless
native-render reference frames per clean video. Those compression comparisons
measure encoding fidelity, not reconstruction accuracy. Each clean video's
`.capture.json` includes every output frame's source state and camera angle.

The genuine [4K gallery screenshot](gallery_review_4k.png),
[browser playback samples](browser_validation.json) and
[byte-range checks](range_validation.json) document actual served playback.
The browser samples cover about 1.1 seconds per clip after seeking;
full-file timestamp and decode checks are recorded separately. Keep the gallery
in the foreground and run `scripts/Validate-DemoPlayback.ps1` to repeat that check.

The initial low-resolution attempt passed playback checks and was then rejected
for visual quality. Its small evidence records remain in
[history/initial_browser_crop](history/initial_browser_crop/README.md).
Rejected MP4s, encode logs and lossless reference images are retained under
ignored `.local/workflows/dynamic_setup/native_demo_gallery_02/` and `outputs/`.
Chronological experiment reports retain the failed attempt and the correction.

For locally served playback and seeking:

```powershell
conda run --no-capture-output -n tf4dgs python scripts/Serve-Demos.py
```

Open <http://127.0.0.1:8107/>. Playback needs no models or source footage.
To reproduce the clean masters from the retained fitted models, use
`scripts/Render-GaussianOrbit.py` once for each dataset with a new ignored output
folder, then `scripts/Finalize-NativeDemoGallery.py --masters <folder> --attempt <new-name>`.
The original cropped workflow is historical: `scripts/Build-DemoGallery.py`.
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--masters', type=Path, default=Path('outputs/demos_native4k_01'))
    p.add_argument('--attempt', default='native_demo_gallery_02')
    a = p.parse_args()
    masters = (ROOT/a.masters).resolve()
    masters.relative_to((ROOT/'outputs').resolve())
    cache = (ROOT/'.local/workflows/dynamic_setup'/a.attempt).resolve()
    cache.relative_to((ROOT/'.local/workflows/dynamic_setup').resolve())
    if cache.exists():
        raise FileExistsError('Preserve diagnostics and choose a new attempt name')
    cache.mkdir(parents=True)
    docs = ROOT/'documentation/demos'
    tool = next(t for t in read(ROOT/'static-tools.json')['portable_tools'] if t['name']=='FFmpeg')
    # Complete validation before replacing any selected clip.
    validated = {name:validate_native(masters/name, cache/name, tool) for name in ['yogurt', 'textile']}
    shutil.copytree(docs, cache/'rejected_browser_crop_gallery')
    history = docs/'history/initial_browser_crop'
    history.mkdir(parents=True, exist_ok=True)
    for name in ['validation.json', 'browser_validation.json', 'range_validation.json']:
        shutil.copyfile(docs/name, history/name)
    (history/'README.md').write_text('''# Rejected initial browser-crop attempt

The initial clean clips used 990 x 710 yogurt and 1060 x 736 textile browser
viewports. Playback and seeking passed, but the user rejected low detail and
jagged motion. These records preserve that attempt; they do not describe the
current native 4K videos. The original gallery screenshot and capture metadata
remain two directories above as gallery_review.png and gallery_review.capture.json.
The full rejected gallery, including its MP4s, is retained in ignored
.local/workflows/dynamic_setup/native_demo_gallery_02/rejected_browser_crop_gallery/.
''', encoding='utf-8')
    clips = []
    for name in ['yogurt', 'textile']:
        manifest, check = validated[name]
        target = docs/name/manifest['filename']
        shutil.copyfile(masters/name/manifest['filename'], target)
        if sha(target) != manifest['sha256']:
            raise ValueError('Native gallery copy differs from the validated master')
        middle = manifest['lossless_reference_frames'][2]
        with Image.open(masters/name/f'reference_{middle:06d}.png') as image:
            ImageOps.contain(image.convert('RGB'), (1920, 1080)).save(target.with_suffix('.jpg'), quality=95)
        meta = dict(manifest, variant='reconstruction_only', validation=check,
            source_master=(masters/name/manifest['filename']).relative_to(ROOT).as_posix(),
            source_manifest=(masters/name/'render_manifest.json').relative_to(ROOT).as_posix(),
            camera_relative_range_degrees=[-45,45], camera_path='center -> +45 -> center -> -45 -> center',
            browser_screen_recording=False, reconstruction_accuracy_changed=False)
        write(target.with_suffix('.capture.json'), meta)
        for kind in ['ui', 'reconstruction_orbit']:
            file = docs/name/f'{name}_{kind}.mp4'
            info = probe(file, tool)
            stream = next(s for s in info['streams'] if s['codec_type']=='video')
            clips.append(dict(dataset=name, path=file.relative_to(docs).as_posix(), codec=stream['codec_name'],
                width=stream['width'], height=stream['height'], fps=stream['avg_frame_rate'],
                frames=int(stream['nb_frames']), duration_s=float(info['format']['duration']),
                bytes=file.stat().st_size, sha256=sha(file),
                native_gaussian_render=kind=='reconstruction_orbit',
                full_decode_passed=True, **({'validation':check} if kind!='ui' else {})))
    write(docs/'validation.json', dict(status='native 4K render, full decode and frame timestamps passed',
        recorded_utc=datetime.now(timezone.utc).isoformat(), clips=clips,
        total_video_bytes=sum(c['bytes'] for c in clips),
        new_native_video_bytes=sum(c['bytes'] for c in clips if c['native_gaussian_render']),
        ui_copies_byte_identical=True, camera_arc_degrees=90,
        clean_orbits_encoded_from_lossless_png=False, clean_orbits_native_rasterization=True,
        underlying_temporal_model_changed=False, git_staging_commit_push_performed=False))
    write(docs/'stutter_diagnosis.json', stutter_report())
    (docs/'index.html').write_text(gallery(clips), encoding='utf-8')
    (docs/'README.md').write_text(notes(clips), encoding='utf-8')
    print(json.dumps(dict(status='native gallery installed', clips=[{k:v for k,v in c.items() if k!='validation'} for c in clips],
        total_bytes=sum(c['bytes'] for c in clips), previous_attempt=cache.relative_to(ROOT).as_posix()), indent=2), flush=True)


if __name__=='__main__':
    main()
