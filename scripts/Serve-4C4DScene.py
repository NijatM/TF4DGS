"""Loopback interactive viewer for joint continuous 4C4D inference exports."""
import argparse
import io
import json
import math
import sys
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import numpy as np
from PIL import Image
import torch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local/research/4C4D'))
from scene.gaussian_model import GaussianModel
from gaussian_renderer import render
spec = spec_from_file_location('scene_camera', ROOT / 'scripts/Train-TemporalBenchmark.py')
shared = module_from_spec(spec);spec.loader.exec_module(shared)


PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TF4DGS - Whole scene continuous viewer</title><style>
body{margin:0;background:#131820;color:#edf3fa;font:15px system-ui}header{padding:16px 22px}h1{font-size:23px;margin:0 0 8px}
button,select{color:#edf3fa;background:#273649;border:1px solid #51677f;border-radius:5px;padding:8px;font:inherit;margin:4px}
#render{display:block;width:100%;max-height:75vh;object-fit:contain;cursor:grab;background:#fff;touch-action:none}
#render:fullscreen{width:100vw;height:100vh;max-height:100vh;object-fit:contain}
.bar{padding:10px 20px}input[type=range]{width:180px;vertical-align:middle}#scrub{width:60%}small{color:#bdcde0}a{color:#80c9ef}
</style><header><h1>Whole-scene continuous 4D reconstruction</h1>
<label>Experiment <select id="dataset"><option value="textile">Textile and hands</option><option value="yogurt">Yogurt</option></select></label>
<label>View <select id="camera"><option value="iphone">iPhone</option><option value="fuji">Fuji</option><option value="dji">DJI</option><option value="orbit">Free orbit</option></select></label>
<button id="play">Play</button><button id="reset">Reset view</button><button id="auto">Orbit +/-45 degrees</button>
<button id="fullscreen">Fullscreen scene</button>
<label>Preview <select id="resolution"><option value="1280">1280</option><option value="1920">1920</option><option value="3840">Native / 4K</option></select></label>
<select id="mode" hidden><option value="rgb">rgb</option></select><input id="trails" type="checkbox" hidden>
<br><small>One scene includes the subject, hands and visible surroundings. Experimental geometry; hidden surfaces remain unverified.</small></header>
<img id="render" alt="Gaussian reconstruction"><div class="bar"><input id="scrub" type="range" min="0" max="1000" value="0"><span id="timeLabel">Loading</span><br>
<label>Orbit <input id="yaw" type="range" min="-75" max="75" step="0.01" value="0"></label>
<label>Height <input id="pitch" type="range" min="-30" max="45" step="0.01" value="0"></label>
<label>Distance <input id="distance" type="range" min="50" max="180" step="0.1" value="100"></label>
<span id="status"></span> / <a href="http://127.0.0.1:8109/">Processing report</a></div>
<script>
const $=id=>document.getElementById(id);let meta,playing=false,orbiting=false,busy=false,dirty=true,last=performance.now(),seconds=0,yawStart=performance.now();
async function load(){playing=false;$('play').textContent='Play';seconds=0;$('scrub').value=0;meta=await(await fetch('/api/meta?dataset='+$('dataset').value)).json();window.tf4dgsMeta=meta;dirty=true;}
async function draw(){if(busy||!meta)return;busy=true;dirty=false;const start=performance.now(),renderSeconds=seconds,renderDataset=$('dataset').value;
 try{const query=new URLSearchParams({dataset:renderDataset,time:renderSeconds,camera:$('camera').value,edge:$('resolution').value,yaw:$('yaw').value,pitch:$('pitch').value,distance:$('distance').value});
  const response=await fetch('/api/render?'+query);if(!response.ok)throw Error(await response.text());
  if(renderDataset!==$('dataset').value)return;
  const blob=await response.blob(),url=URL.createObjectURL(blob),old=$('render').src;
  $('render').src=url;await $('render').decode();if(old.startsWith('blob:'))URL.revokeObjectURL(old);
  $('status').textContent=(performance.now()-start).toFixed(0)+' ms render';window.tf4dgsLastRenderedTime=renderSeconds;
 }catch(error){$('status').textContent=error.message;}finally{busy=false;}}
function tick(now){const dt=Math.min(.2,(now-last)/1000);last=now;
 if(playing&&meta){seconds=(seconds+dt)%meta.time_span_s;$('scrub').value=seconds/meta.time_span_s*1000;dirty=true;}
 if(orbiting){$('camera').value='orbit';$('yaw').value=45*Math.sin((now-yawStart)/1000*Math.PI/4);dirty=true;}
 if(meta)$('timeLabel').textContent=seconds.toFixed(3)+' / '+meta.time_span_s.toFixed(3)+' s';
 if(dirty&&!busy)draw();requestAnimationFrame(tick);}
$('dataset').onchange=load;$('camera').onchange=()=>{dirty=true;};$('resolution').onchange=()=>{dirty=true;};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play';};
$('auto').onclick=()=>{orbiting=!orbiting;yawStart=performance.now();$('auto').textContent=orbiting?'Stop orbit':'Orbit +/-45 degrees';};
$('scrub').oninput=()=>{playing=false;$('play').textContent='Play';seconds=Number($('scrub').value)/1000*meta.time_span_s;dirty=true;};
for(const id of ['yaw','pitch','distance'])$(id).oninput=()=>{$('camera').value='orbit';dirty=true;};
$('reset').onclick=()=>{orbiting=false;$('auto').textContent='Orbit +/-45 degrees';$('camera').value='iphone';$('yaw').value=0;$('pitch').value=0;$('distance').value=100;dirty=true;};
$('fullscreen').onclick=()=>{$('render').requestFullscreen();};
let dragging=null;$('render').onpointerdown=e=>{dragging=[e.clientX,e.clientY];$('render').setPointerCapture(e.pointerId);orbiting=false;};
$('render').onpointermove=e=>{if(!dragging)return;$('yaw').value=Math.max(-75,Math.min(75,Number($('yaw').value)+(e.clientX-dragging[0])*.15));$('pitch').value=Math.max(-30,Math.min(45,Number($('pitch').value)-(e.clientY-dragging[1])*.15));dragging=[e.clientX,e.clientY];$('camera').value='orbit';dirty=true;};
$('render').onpointerup=()=>{dragging=null;};load();requestAnimationFrame(tick);
</script></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--models', default='outputs/4c4d_scene_001/selected_models.json')
    parser.add_argument('--port', type=int, choices=[8110], default=8110)
    args = parser.parse_args()
    registry_path = (ROOT / args.models).resolve()
    allowed_roots = {(ROOT/'outputs'/name).resolve() for name in ['4c4d_scene_001','4c4d_full_001']}
    if registry_path.parent not in allowed_roots:
        raise ValueError('Registry must belong to a registered joint-scene experiment')
    record = json.loads(registry_path.read_text(encoding='utf-8-sig'))
    registry = record.get('datasets',record)
    pipe = SimpleNamespace(convert_SHs_python=False, compute_cov3D_python=False, debug=False, env_map_res=0)
    background = torch.ones(3, device='cuda')

    @lru_cache(maxsize=2)
    def load(dataset):
        entry = registry[dataset]
        path = (ROOT / entry['model']).resolve()
        if registry_path.parent not in path.parents:
            raise ValueError('Model must belong to this experiment')
        packet = torch.load(path, map_location='cuda', weights_only=False)
        if packet['method'] != '4c4d' or packet['setup'].get('separate_background_model'):
            raise ValueError('Only joint scene models accepted')
        model = GaussianModel(3, gaussian_dim=4, time_duration=[0., 1.], rot_4d=True, force_sh_3d=False, sh_degree_t=2)
        for name, value in packet['weights'].items():
            if name.startswith('_'):
                setattr(model, name, torch.nn.Parameter(value, requires_grad=False))
        model.active_sh_degree = packet['weights']['active_sh_degree']
        model.active_sh_degree_t = packet['weights']['active_sh_degree_t']
        return packet, model

    def metadata(dataset):
        packet, model = load(dataset)
        return {'source': registry[dataset]['model'], 'dataset': dataset, 'gaussians': len(model.get_xyz),
                'time_origin_pts_s': packet['time_origin_pts_s'], 'time_span_s': packet['time_span_s'],
                'camera_views': list(packet['cameras']), 'continuous_time': True, 'whole_scene': True,
                'separate_background_model': False, 'metric_accuracy_verified': False, 'persistent_material_ids': False}

    class Handler(BaseHTTPRequestHandler):
        def reply(self, body, kind, status=200):
            self.send_response(status);self.send_header('Content-Type', kind);self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store');self.send_header('X-Content-Type-Options', 'nosniff');self.end_headers();self.wfile.write(body)

        def do_GET(self):
            request = urlparse(self.path)
            query = parse_qs(request.query)
            dataset = query.get('dataset', ['textile'])[0]
            try:
                if request.path == '/':
                    self.reply(PAGE.encode(), 'text/html; charset=utf-8');return
                if dataset not in registry:
                    raise ValueError('Unknown experiment')
                if request.path == '/api/meta':
                    self.reply(json.dumps(metadata(dataset)).encode(), 'application/json');return
                if request.path != '/api/render':
                    self.reply(b'Not found', 'text/plain', 404);return
                packet, model = load(dataset)
                def number(key, default, lo, hi):
                    value = float(query.get(key, [default])[0])
                    if not math.isfinite(value):
                        raise ValueError(f'Non-finite {key}')
                    return np.clip(value, lo, hi)
                seconds = number('time', 0, 0, packet['time_span_s'])
                cid = query.get('camera', ['iphone'])[0]
                cal = packet['cameras']['iphone' if cid == 'orbit' else cid].copy()
                edge = int(number('edge', 1280, 320, 3840))
                factor = min(1., edge / max(cal['width'], cal['height']))
                width, height = int(round(cal['width'] * factor / 2)) * 2, int(round(cal['height'] * factor / 2)) * 2
                sx, sy = width / cal['width'], height / cal['height']
                cal.update(width=width, height=height, fx=cal['fx'] * sx, fy=cal['fy'] * sy, cx=(cal['cx'] + .5) * sx - .5, cy=(cal['cy'] + .5) * sy - .5)
                if cid == 'orbit':
                    norm = packet['normalization']
                    target = (np.array([.175, .105, -.045]) - norm['center_m']) * norm['scale_per_m']
                    reference = shared.camera(cal, 0)
                    origin = reference.camera_center.cpu().numpy()
                    yaw, pitch = math.radians(number('yaw', 0, -75, 75)), math.radians(number('pitch', 0, -30, 45))
                    spin_z = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
                    spin_x = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
                    position = target + spin_x @ spin_z @ (origin - target) * number('distance', 100, 50, 180) / 100
                    forward = target - position;forward /= np.linalg.norm(forward)
                    right = np.cross(forward, [0, 0, -1]);right /= np.linalg.norm(right)
                    rotation = np.stack([right, np.cross(forward, right), forward])
                    cal.update(R=rotation.tolist(), t=(-rotation @ position).tolist())
                cam = shared.camera(cal, seconds / packet['time_span_s'])
                with torch.no_grad():
                    rgb = render(cam, model, pipe, background)['render'].clamp(0, 1).permute(1, 2, 0).cpu().numpy()
                buffer = io.BytesIO()
                encoding = query.get('format', ['jpeg'])[0]
                output_image = Image.fromarray((rgb * 255).round().astype('uint8'))
                if encoding == 'png':
                    output_image.save(buffer, format='PNG')
                    self.reply(buffer.getvalue(), 'image/png')
                elif encoding == 'jpeg':
                    # Preview compression avoids expensive full-frame PNG
                    # encoding. Exact regression/evidence can request PNG.
                    output_image.save(buffer, format='JPEG', quality=95, subsampling=0)
                    self.reply(buffer.getvalue(), 'image/jpeg')
                else:
                    raise ValueError('Unknown image format')
            except (ValueError, KeyError, TypeError) as error:
                self.reply(json.dumps({'error': str(error)}).encode(), 'application/json', 400)

        def log_message(self, *args):
            pass

    print('TF4DGS joint continuous viewer: http://127.0.0.1:8110/', flush=True)
    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
