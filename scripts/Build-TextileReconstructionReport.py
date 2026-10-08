"""Append chronological reconstruction evidence and make a local HTML journal."""
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'documentation/dynamic_textile_001'


def append(title, text, image=None, status='in progress', recorded_utc=None):
    DOCS.mkdir(parents=True,exist_ok=True)
    path=DOCS/'journal.json'
    rows=json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else []
    row=dict(stage=len(rows)+1,title=title,text=text,status=status,
             recorded_utc=recorded_utc or datetime.now(timezone.utc).isoformat())
    if image:
        source=Path(image);name=f"{row['stage']:02d}_diagnostic{source.suffix.lower()}"
        if source.resolve().parent==DOCS.resolve():name=source.name
        else:shutil.copyfile(source,DOCS/name)
        row['image']=name
        row['image_kind']=('Genuine local browser screenshot; see accompanying capture metadata'
            if source.with_suffix('.capture.json').exists() else 'Diagnostic from real source images or model renders; not a desktop screenshot')
        metadata=source.with_suffix('.capture.json')
        if metadata.exists() and recorded_utc is None:
            evidence=json.loads(metadata.read_text(encoding='utf-8-sig'))
            row['recorded_utc']=evidence.get('captured_utc',row['recorded_utc'])
    rows.append(row);path.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    build(rows)
    return row


def build(rows):
    def card(r):
        return (f"<article id='stage-{r['stage']}'><p class='label'>STAGE {r['stage']:02d} · {html.escape(r['status'])} · {html.escape(r['recorded_utc'])}</p>"
                f"<h2>{html.escape(r['title'])}</h2><p>{html.escape(r['text']).replace(chr(10),'<br>')}</p>"+
                (f"<img src='{html.escape(r['image'])}'><p class='label'>{r['image_kind']}</p>" if r.get('image') else '')+'</article>')
    def page(body,stage=None):
        return "<!doctype html><meta charset='utf-8'><title>TF4DGS — textile reconstruction journal</title><style>body{background:#121820;color:#e6edf5;font:19px/1.5 system-ui;margin:30px}h1{font-size:30px}h2{font-size:26px}.label{color:#9eb4cc;font-size:14px}article{padding:22px;background:#1c2633;margin:22px 0;border:1px solid #34475c;border-radius:12px}img{max-width:100%;display:block}a{color:#8cc5ff}</style><h1>Temporal Fields 4D Gaussian Splatting</h1><p>Textile reconstruction revision · chronological evidence</p>"+body+f"<script>window.tf4dgsReportReady=true;window.tf4dgsReportStage={json.dumps(stage)};</script>"
    (DOCS/'index.html').write_text(page(''.join(card(r) for r in rows)),encoding='utf-8')
    for r in rows:
        (DOCS/f"stage_{r['stage']:02d}.html").write_text(page(card(r),r['stage']),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--title',required=True);p.add_argument('--text',required=True)
    p.add_argument('--image');p.add_argument('--status',default='in progress');p.add_argument('--recorded-utc');a=p.parse_args()
    print(json.dumps(append(a.title,a.text,a.image,a.status,a.recorded_utc)))
