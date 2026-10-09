"""Build the whole-scene checkpoint gallery from actual saved evidence."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/4c4d_scene_001'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    runs = []
    for path in sorted(DOCS.glob('*_step_*_metrics.json')):
        metric = read(path)
        tag = f'{metric["dataset"]}_{metric["attempt"]}_step_{metric["step"]:06d}'
        runs.append({**metric, 'image': tag + '_preview.png', 'orbit': tag + '_orbit.png',
                     'metrics_file': path.name,
                     'common_psnr': metric.get('validation_psnr_common_1280', metric['validation_psnr_db'] if metric['edge'] == 1280 else None),
                     'common_motion_psnr': metric.get('motion_region_psnr_common_1280', metric['motion_region_psnr_db'] if metric['edge'] == 1280 else None)})
    selection_path = DOCS / 'selection.json'
    selection = read(selection_path) if selection_path.exists() else {}
    rows = []
    cards = []
    for item in runs:
        label = f'{item["dataset"]} / {item["attempt"]} / {item["step"]:,} updates / edge {item["edge"]}'
        psnr = '-' if item['common_psnr'] is None else f'{item["common_psnr"]:.2f}'
        motion = '-' if item['common_motion_psnr'] is None else f'{item["common_motion_psnr"]:.2f}'
        rows.append(f'<tr data-dataset="{item["dataset"]}"><td><a href="#{html.escape(item["image"])}">{html.escape(label)}</a></td>'
                    f'<td>{psnr}</td><td>{motion}</td><td>{item["validation_ssim_at_1280"]:.3f}</td>'
                    f'<td>{item["point_count"]:,}</td><td>{item["peak_cuda_allocated_gib"]:.2f}</td></tr>')
        cards.append(f'<article data-dataset="{item["dataset"]}" id="{html.escape(item["image"])}"><h2>{html.escape(label)}</h2>'
                     f'<div class="views"><figure><img src="{item["image"]}"><figcaption>iPhone validation timestamp 47</figcaption></figure>'
                     f'<figure><img src="{item["orbit"]}"><figcaption>Unrecorded +35° orbit, same timestamp</figcaption></figure></div>'
                     f'<p><a href="{item["metrics_file"]}">Recorded metrics</a></p></article>')
    videos = []
    for dataset in ['textile', 'yogurt']:
        clips = list(DOCS.glob(f'{dataset}_selected_*30fps.mp4'))
        if clips:
            parts = ''.join(f'<figure><video src="{clip.name}" controls muted loop playsinline preload="metadata"></video>'
                            f'<figcaption><a href="{clip.name}" download>{clip.name}</a></figcaption></figure>' for clip in clips)
            videos.append(f'<article data-dataset="{dataset}"><h2>{dataset}: selected continuous model</h2>{parts}</article>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TF4DGS - Whole-scene training comparison</title><style>
body{max-width:1600px;margin:24px auto;padding:0 22px;background:#131820;color:#e9eef5;font:16px system-ui}p{line-height:1.55}a{color:#80c9ef}
article{padding:20px;margin:24px 0;background:#1b2330;border:1px solid #384353;border-radius:8px}.views{display:grid;grid-template-columns:1fr 1fr;gap:12px}
figure{margin:8px 0}img,video{width:100%;max-height:720px;object-fit:contain;background:white}figcaption{margin-top:8px;color:#b3c5d6}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #384353}select{font:inherit;padding:8px;background:#273649;color:white}
@media(max-width:850px){.views{grid-template-columns:1fr}table{font-size:12px}td,th{padding:5px}}
</style><h1>Joint whole-scene 4C4D</h1><p>Each capture has one learned continuous model for the subject, hands, table, board and visible surroundings.
No separate or frozen background model is used. Camera views and orbit checks are shown together because image scores alone do not establish correct geometry.</p>
<p>Yogurt source frames 330–419 / textile 587–676, 90 frames each at 30000/1001 fps. All settings use the same action intervals.
The 45 held-out camera images are validation data for parameter selection. Native-resolution scores are resampled to a common 1280-edge reference for cross-resolution comparisons.</p>
<p><a href="index.html">Chronological stages and screenshots</a> / <a href="http://127.0.0.1:8110/">Interactive continuous model viewer</a> / <a href="selection.json">Selection record</a></p>
<label>Show <select id="dataset"><option value="all">Both captures</option><option value="textile">Textile and hands</option><option value="yogurt">Yogurt</option></select></label>
<table><thead><tr><th>Capture / attempt / checkpoint</th><th>Common PSNR (dB)</th><th>Motion PSNR (dB)</th><th>SSIM ≤1280</th><th>Gaussians</th><th>Peak allocated GiB</th></tr></thead><tbody>__ROWS__</tbody></table>
__VIDEOS____CARDS__<p>Visible but unseen-angle surfaces may be incomplete; calibration, synchronization and neural depth remain provisional.
Motion-priority masks are train-only RGB variance, including moving hands and shadows; they are not physical material labels.</p>
<script>window.tf4dgsSceneGalleryReady=true;document.getElementById('dataset').onchange=e=>document.querySelectorAll('[data-dataset]').forEach(node=>{node.hidden=e.target.value!=='all'&&node.dataset.dataset!==e.target.value;});</script></html>'''
    page = page.replace('__ROWS__', ''.join(rows)).replace('__CARDS__', ''.join(cards)).replace('__VIDEOS__', ''.join(videos))
    (DOCS / 'comparison.html').write_text(page, encoding='utf8')
    (DOCS / 'results.json').write_text(json.dumps({'checkpoints': runs, 'selection': selection,
        'scores': 'Validation camera images, not independent novel-view or metric geometry tests.'}, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'actual_checkpoint_count': len(runs), 'gallery': 'documentation/4c4d_scene_001/comparison.html'}))


if __name__ == '__main__':
    main()
