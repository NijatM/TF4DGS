"""Validate compact pilot evidence and build an offline synchronized comparison."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/temporal_benchmark_001'
METHODS = ['4dgaussians', '4c4d']
DATASETS = ['yogurt', 'textile']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


PAGE = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TF4DGS - Continuous model comparison</title>
<style>
body{margin:24px auto;padding:0 22px;max-width:1440px;background:#131820;color:#e9eef5;font:16px system-ui}
h1{font-size:30px}p{line-height:1.5}a{color:#80c9ef}button,select{font:inherit;color:#e9eef5;background:#253244;border:1px solid #536477;border-radius:6px;padding:9px;margin:4px}
.toolbar{position:sticky;top:0;background:#131820ee;padding:10px 0;z-index:1}
.views{display:grid;grid-template-columns:1fr 1fr;gap:18px}.views.compare{grid-template-columns:1fr}
article{background:#1b2330;border:1px solid #384353;border-radius:10px;padding:16px}
video{width:100%;background:white;display:block;max-height:650px}#scrub{width:65%;vertical-align:middle}
table{border-collapse:collapse;width:100%;margin:24px 0}th,td{border-bottom:1px solid #384353;padding:12px;text-align:left}
.notice{padding:15px;border-left:4px solid #ffbf79;background:#242833}.caption{color:#b3c5d6}
@media(max-width:800px){.views{grid-template-columns:1fr}table{font-size:13px}th,td{padding:7px}}
</style></head><body>
<h1>Continuous 4D Gaussian pilot comparison</h1>
<p>Three synchronized cameras / 90 native source frames / 6000 training updates per run.<br>
Textile includes the fabric, hands and current marker-board/table context.</p>
<p class="notice">This is a 1280-pixel research pilot. 4C4D has better held-out image scores on both clips,
but neither result meets the crisp textile reconstruction target. Ghosting and unreliable unseen geometry
remain visible. These videos evaluate learned time models; they do not validate physical deformation measurements.</p>
<div class="toolbar">
<label>Experiment <select id="dataset"><option value="yogurt">Yogurt</option><option value="textile">Textile and hands</option></select></label>
<label>View <select id="mode"><option value="fixed">Fixed iPhone view</option><option value="comparison">Source beside reconstruction</option><option value="orbit30">+/-45 degree orbit - exact 30 fps</option></select></label>
<button id="play">Play both</button><button id="reset">Reset</button>
<label><input id="loop" type="checkbox" checked> Loop</label><br>
<input id="scrub" type="range" min="0" max="1000" value="0"><span id="timeLabel">Loading</span>
</div>
<p id="interval" class="caption"></p>
<div class="views" id="views">
<article><h2>4DGaussians</h2><video id="v0" muted playsinline preload="auto"></video><p id="score0"></p><p><a id="download0" download>Download video</a> / <button id="full0">Fullscreen</button></p></article>
<article><h2>4C4D</h2><video id="v1" muted playsinline preload="auto"></video><p id="score1"></p><p><a id="download1" download>Download video</a> / <button id="full1">Fullscreen</button></p></article>
</div>
<h2>Matched pilot results</h2><table><thead><tr><th>Experiment</th><th>Method</th><th>PSNR / SSIM</th><th>Optimization</th><th>Gaussians</th><th>Model size</th></tr></thead><tbody>__ROWS__</tbody></table>
<p>Scores average 45 held-out images at timestamps excluded from fitting. They include the cropped background;
they are not an independent novel-camera or geometry evaluation. Native source comparisons are 29.97 fps;
orbit exports query the model at exact 1/30-second intervals. Fullscreen shows the actual encoded detail.</p>
<p>Each ignored <code>continuous_model.pth</code> contains one temporal model. Its official CUDA decoder is
framework-specific, so it cannot be opened as an animated PLY in SuperSplat.
No independent frame-fit sequence is used here. Hidden surfaces, synchronization and off-board calibration remain unverified.</p>
<p><a href="index.html">Chronological attempts and screenshots</a> / <a href="results.json">Validation and provenance</a></p>
<script>
const runs=__RUNS__, methods=['4dgaussians','4c4d'];
const videos=[document.getElementById('v0'),document.getElementById('v1')];
const dataset=document.getElementById('dataset'),mode=document.getElementById('mode');
const play=document.getElementById('play'),scrub=document.getElementById('scrub');
let playing=false,loading=false;
function pause(){videos.forEach(v=>v.pause());playing=false;play.textContent='Play both';}
function label(){const duration=videos[0].duration;if(!Number.isFinite(duration))return;
 scrub.value=Math.round(videos[0].currentTime/duration*1000);
 document.getElementById('timeLabel').textContent=videos[0].currentTime.toFixed(2)+' / '+duration.toFixed(3)+' s';}
async function seek(seconds){await Promise.all(videos.map(v=>new Promise((resolve,reject)=>{
 if(Math.abs(v.currentTime-seconds)<.001){resolve();return;}
 const timer=setTimeout(()=>reject(Error('Video seek timed out')),5000);
 v.addEventListener('seeked',()=>{clearTimeout(timer);resolve();},{once:true});v.currentTime=seconds;
})));label();}
async function load(){pause();loading=true;document.getElementById('timeLabel').textContent='Loading';
 document.getElementById('views').classList.toggle('compare',mode.value==='comparison');
 const selected=runs[dataset.value];
 document.getElementById('interval').textContent=selected.interval;
 await Promise.all(videos.map((v,i)=>new Promise((resolve,reject)=>{
  const r=selected.methods[methods[i]],file=r.videos[mode.value];
  document.getElementById('score'+i).textContent=r.heldout_psnr_db.toFixed(2)+' dB / SSIM '+r.heldout_ssim.toFixed(3)+' / '+r.point_count.toLocaleString()+' Gaussians';
  document.getElementById('download'+i).href=file;
  const timer=setTimeout(()=>reject(Error('Video load timed out')),15000);
  v.addEventListener('loadeddata',()=>{clearTimeout(timer);resolve();},{once:true});
  v.addEventListener('error',()=>{clearTimeout(timer);reject(Error(v.error.message));},{once:true});
  v.src=file;v.load();
 })));loading=false;label();window.tf4dgsBenchmarkReady=true;}
window.tf4dgsLoadComparison=load;window.tf4dgsSeekComparison=seek;
dataset.onchange=load;mode.onchange=load;
play.onclick=async()=>{if(loading)return;if(playing){pause();return;}await seek(videos[0].currentTime);
 await Promise.all(videos.map(v=>v.play()));playing=true;play.textContent='Pause both';};
document.getElementById('reset').onclick=async()=>{pause();await seek(0);};
scrub.oninput=async()=>{pause();await seek(Number(scrub.value)/1000*videos[0].duration);};
videos[0].ontimeupdate=()=>{if(!loading){label();if(playing&&Math.abs(videos[1].currentTime-videos[0].currentTime)>.07)videos[1].currentTime=videos[0].currentTime;}};
videos[0].onended=async()=>{pause();await seek(0);if(document.getElementById('loop').checked)play.click();};
videos.forEach((v,i)=>document.getElementById('full'+i).onclick=()=>v.requestFullscreen());
load().catch(error=>{document.getElementById('timeLabel').textContent=error.message;console.error(error);});
</script></body></html>'''


def main():
    tool = next(t for t in read(ROOT / 'static-tools.json')['portable_tools'] if t['name'] == 'FFmpeg')
    cfg = read(ROOT / 'configs/temporal_benchmark_001.json')
    result = {'benchmark_id': cfg['benchmark_id'], 'datasets': {},
              'scope': 'Matched adapted pilots; temporal holdouts, no independently validated geometry.',
              'visual_assessment': '4C4D has better photometric scores. Both textile models remain blurred and ghosted; no pristine result claimed.'}
    rows = []
    for dataset in DATASETS:
        manifest = read(ROOT / 'data/temporal_benchmark_001' / dataset / 'manifest.json')
        interval = (f'Source frames {manifest["frames"][0]["source_index"]}-{manifest["frames"][-1]["source_index"]} / '
                    f'{manifest["frames"][0]["pts_s"]:.6f}-{manifest["frames"][-1]["pts_s"]:.6f} s / '
                    '1280 x 616 iPhone crop; original sources preserved.')
        group = {'interval': interval, 'methods': {}}
        for method in METHODS:
            tag = f'{method}_{dataset}_pilot_01'
            output = ROOT / 'outputs/temporal_benchmark_001' / method / dataset / 'pilot_01'
            metrics = read(DOCS / f'{tag}_metrics.json')
            setup = read(output / 'setup.json')
            if setup['initial_points_sha256'] != manifest['initial_points_sha256']:
                raise ValueError(f'Mismatched initialization: {tag}')
            videos = {'fixed': f'{tag}_rgb_fixed.mp4', 'comparison': f'{tag}_source_comparison.mp4',
                      'orbit30': f'{tag}_rgb_orbit_30fps.mp4'}
            checks = []
            for name in [*videos.values(), f'{tag}_rgb_orbit.mp4']:
                path = DOCS / name
                probe = json.loads(subprocess.check_output([
                    tool['ffprobe_path'], '-v', 'error', '-select_streams', 'v:0', '-show_streams',
                    '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(path)]))
                stream = probe['streams'][0]
                exact = name.endswith('_30fps.mp4')
                fps = 30 if exact else 30000 / 1001
                pts = [float(frame['best_effort_timestamp_time']) for frame in probe['frames']]
                maximum_error = max(abs(t - i / fps) for i, t in enumerate(pts))
                if len(pts) != 90 or maximum_error > .000001:
                    raise ValueError(f'Invalid encoded frame cadence: {name}')
                subprocess.run([tool['executable_path'], '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'], check=True)
                with urllib.request.urlopen(urllib.request.Request(
                        'http://127.0.0.1:8108/' + name, headers={'Range': 'bytes=0-1023'})) as response:
                    range_bytes = response.read()
                    if response.status != 206 or range_bytes != path.read_bytes()[:1024]:
                        raise ValueError(f'Range playback failed: {name}')
                checks.append({'file': name, 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                               'width': stream['width'], 'height': stream['height'], 'frames': len(pts),
                               'fps': stream['r_frame_rate'], 'duration_s': float(stream['duration']),
                               'maximum_timestamp_error_s': maximum_error, 'full_decode_passed': True,
                               'http_range_206_matches': True})
            validation = read(DOCS / f'{tag}_rgb_orbit_30fps.validation.json')
            model_path = output / 'continuous_model.pth'
            record = {**metrics, 'videos': videos, 'video_validation': checks,
                      'model': {'file': str(model_path.relative_to(ROOT)).replace('\\', '/'),
                                'bytes': model_path.stat().st_size, 'sha256': hashlib.sha256(model_path.read_bytes()).hexdigest()},
                      'decoder_validation': validation, 'motion_probe': read(DOCS / f'{tag}_motion.json'),
                      'initial_points_sha256': setup['initial_points_sha256'],
                      'source_commit': setup['source_commit'],
                      'camera_projection_max_error_px': setup['camera_projection_max_error_px']}
            group['methods'][method] = record
            rows.append(f'<tr><td>{dataset}</td><td>{method}</td><td>{metrics["heldout_psnr_db"]:.2f} / '
                        f'{metrics["heldout_ssim"]:.3f}</td><td>{metrics["elapsed_s"]/60:.2f} min</td><td>{metrics["point_count"]:,}</td>'
                        f'<td>{model_path.stat().st_size/1048576:.1f} MiB</td></tr>')
        result['datasets'][dataset] = group
    (DOCS / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    (DOCS / 'comparison.html').write_text(PAGE.replace('__ROWS__', ''.join(rows)).replace('__RUNS__', json.dumps(result['datasets'])), encoding='utf8')
    print(json.dumps({'runs': 4, 'videos': 16, 'status': 'Decoded, timestamp checked, HTTP ranges checked; comparison built'}))


if __name__ == '__main__':
    main()
