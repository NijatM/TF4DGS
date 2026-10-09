"""Append chronological evidence and serve a loopback-only benchmark report."""
import argparse
import datetime
import html
import json
from functools import partial
from importlib.util import module_from_spec, spec_from_file_location
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/temporal_benchmark_001'

LIVE_SCRIPT = '''<script>
async function tick() {
  if (window.tf4dgsFreezeReport) return;
  try {
    const response = await fetch('live_progress.json?' + Date.now());
    if (!response.ok) return;
    const state = await response.json();
    const parts = [state.method, state.dataset, state.attempt, state.status,
      'update ' + state.step + '/' + state.total];
    if (typeof state.loss === 'number') parts.push('loss ' + state.loss.toFixed(4));
    if (typeof state.point_count === 'number') parts.push(state.point_count + ' Gaussians');
    if (typeof state.elapsed_s === 'number') parts.push(state.elapsed_s.toFixed(1) + ' seconds');
    document.getElementById('liveText').textContent = parts.filter(Boolean).join(' / ');
    if (state.preview) {
      let image = document.getElementById('liveImage');
      if (!image) {
        image = document.createElement('img');
        image.id = 'liveImage';
        document.getElementById('liveImageHost').appendChild(image);
      }
      image.src = state.preview + '?' + Math.floor(Date.now() / 10000);
    }
  } catch (error) { console.error('Live report refresh:', error); }
}
tick(); setInterval(tick, 3000);
</script>'''


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def capture_links(stage):
    records = []
    for path in DOCS.glob('*.capture.json'):
        record = read(path)
        if record.get('page_state', {}).get('stage') == stage:
            screenshot = path.name.replace('.capture.json', '.png')
            if (DOCS / screenshot).exists():
                records.append((record.get('captured_utc', ''), screenshot))
    return [name for _, name in sorted(records)]


def build():
    journal = read(DOCS / 'journal.json')
    profile = read(DOCS / 'report.json') if (DOCS / 'report.json').exists() else None
    sections = []
    for entry in reversed(journal):
        media = ''.join(f'<img src="{html.escape(p)}">' for p in entry.get('images', []))
        media += ''.join(f'<video src="{html.escape(p)}" controls loop muted playsinline></video>'
                         for p in entry.get('videos', []))
        media += ''.join(f'<p><a href="{html.escape(p)}">Stage screenshot</a></p>'
                         for p in capture_links(entry['number']))
        sections.append(f'<section><small>{entry["number"]:03d} / {html.escape(entry["utc"])} / '
                        f'{html.escape(entry["status"])}</small><h2>{html.escape(entry["title"])}</h2>'
                        f'<p>{html.escape(entry["detail"])}</p>{media}</section>')
    page = '''<!doctype html><meta charset="utf-8"><title>TF4DGS - Continuous 4D benchmark</title>
<style>body{background:#131820;color:#e9eef5;font:17px system-ui;max-width:1350px;margin:30px auto;padding:0 24px}h1{font-size:32px}section{border:1px solid #384353;background:#1b2330;border-radius:10px;padding:22px;margin:22px 0}small{color:#a1bed3}p{line-height:1.6}img,video{max-width:100%;max-height:650px;display:block;margin:12px auto}a{color:#80c9ef}</style>
<h1>Temporal Fields 4D Gaussian Splatting</h1>
<p>Matched continuous-model pilots / 4DGaussians and 4C4D / three fixed cameras</p>
<p>Yogurt: source frames 330-419 (11.011-13.981 s). Textile: 587-676 (19.586-22.556 s).
90 frames each at 30000/1001 fps. Same inputs, initialization and held-out timestamps.
Textile reconstruction includes the hands.</p>'''
    if profile:
        prefix = page.index('<h1>')
        page = page[:prefix] + '<h1>' + html.escape(profile['title']) + '</h1><p>' + html.escape(profile['intro']) + '</p>'
    if (DOCS / 'comparison.html').exists():
        page += '<section><h2>Reconstruction comparison</h2><p><a href="comparison.html">Open saved reconstruction and orbit evidence</a></p></section>'
    page += '<section id="live"><h2>Live training progress</h2><p id="liveText">Waiting for trainer</p><div id="liveImageHost"></div></section>'
    page += ''.join(sections)
    page += f'<script>window.tf4dgsReportReady=true;window.tf4dgsReportStage={len(journal)};</script>'
    page += LIVE_SCRIPT
    (DOCS / 'index.html').write_text(page, encoding='utf8')
    lines = ['# Continuous 4D short benchmark', '',
             'The source intervals are pinned in [the configuration](../../configs/temporal_benchmark_001.json). '
             'Both methods use the same calibrated crops, shared initial point cloud, and 75 training / 15 held-out '
             'timestamps across all three cameras. Textile includes the hands. This is a local pilot with a shared '
             'adapter, not a reproduction of the published evaluations. Models, raw clips, caches and build logs remain ignored.', '']
    if profile:
        lines = ['# ' + profile['title'], '', profile['intro'], '']
    if (DOCS / 'comparison.html').exists():
        lines += ['[Finished video comparison](comparison.html)', '']
    lines += ['## Chronological record', '']
    for entry in journal:
        lines += [f'### {entry["number"]:03d} - {entry["title"]}', '',
                  f'{entry["utc"]} / {entry["status"]}', '', entry['detail'], '']
        lines += [f'![Evidence]({p})' for p in entry.get('images', [])] + ['']
        lines += [f'[Video]({p})' for p in entry.get('videos', [])] + ['']
        lines += [f'[Stage screenshot]({p})' for p in capture_links(entry['number'])] + ['']
    (DOCS / 'README.md').write_text('\n'.join(lines), encoding='utf8')


def main():
    global DOCS
    parser = argparse.ArgumentParser()
    parser.add_argument('--title')
    parser.add_argument('--detail', default='')
    parser.add_argument('--status', default='in progress')
    parser.add_argument('--images', nargs='*', default=[])
    parser.add_argument('--videos', nargs='*', default=[])
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--docs', default='documentation/temporal_benchmark_001')
    parser.add_argument('--port', type=int, choices=[8108, 8109], default=8108)
    args = parser.parse_args()
    DOCS = (ROOT / args.docs).resolve()
    if ROOT / 'documentation' not in DOCS.parents:
        raise ValueError('Report directory must be inside project documentation')
    DOCS.mkdir(parents=True, exist_ok=True)
    journal_path = DOCS / 'journal.json'
    if not journal_path.exists():
        journal_path.write_text('[]\n', encoding='utf8')
    if args.title:
        entries = read(journal_path)
        entries.append({'number': len(entries) + 1, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'title': args.title, 'detail': args.detail, 'status': args.status,
                        'images': args.images, 'videos': args.videos})
        journal_path.write_text(json.dumps(entries, indent=2) + '\n', encoding='utf8')
    build()
    if args.serve:
        spec = spec_from_file_location('temporal_report_http', ROOT / 'scripts/Serve-TextileDocumentation.py')
        server = module_from_spec(spec)
        spec.loader.exec_module(server)
        server.DOCS = DOCS
        ThreadingHTTPServer(('127.0.0.1', args.port), partial(server.Handler, directory=str(DOCS))).serve_forever()


if __name__ == '__main__':
    main()
