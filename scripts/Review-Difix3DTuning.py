"""Matched native-resolution rendered evidence for 2M repair selection."""
from importlib.util import spec_from_file_location,module_from_spec
import gc
import json
from pathlib import Path
import torch

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
torch.set_num_threads(6)
manifest=json.loads((r.WORK/'manifest.json').read_text());entry=manifest['files'][2];stem=Path(entry['name']).stem
tuning=r.WORK/'tuning'/entry['folder']
methods=[('original',Path(entry['path'])),('first_pass',Path(entry['output'])),('moderate',tuning/(stem+'_wide_official_Difix3D.ply')),('aggressive',tuning/(stem+'_wide_strong_Difix3D.ply')),('pruned_balanced',tuning/(stem+'_wide_strong_pruned_balanced_Difix3D.ply')),('pruned_conservative',tuning/(stem+'_wide_official_pruned_conservative_Difix3D.ply')),('recovery',tuning/(stem+'_geometry_recovery_Difix3D.ply'))]
methods.append(('opacity_only',tuning/(stem+'_opacity_recovery_Difix3D.ply')))
targets=json.loads((r.WORK/entry['folder']/(stem+'_wide_official')/'targets.json').read_text())['records']
views=[next(x['view'] for x in targets if x['view']['name']==name) for name in ['wide_0_-35','wide_0_-20','DJI_0037.JPG']]
files={};metrics={}
for label,path in methods:
    if not path.exists():continue
    m,_=r.load_model(path);files[label]=[]
    with torch.no_grad():
        for i,v in enumerate(views):
            rgb,_=r.render(m,v,1536);image=r.DOCS/f'tuning_{label}_view_{i}.jpg';r.rgb_image(rgb).save(image,quality=96,subsampling=0);files[label].append(image.name)
    del m;gc.collect();torch.cuda.empty_cache()
    record_path=path.with_suffix('.difix3d.json')
    if record_path.exists():
        record=json.loads(record_path.read_text());after=record.get('after',record.get('after_pruning',{}));metrics[label]=after.get('mean_psnr')
labels=list(files);montage='tuning_actual_3d_comparison.jpg'
r.montage(r.DOCS/montage,[[r.DOCS/files[label][i] for label in labels] for i in range(len(views))],labels)
html='<!doctype html><meta charset="utf-8"><title>Difix3D repair comparison</title><style>body{background:#111820;color:#eee;font:16px Arial;margin:24px}img{max-width:100%;width:1536px}section{margin:30px 0}a{color:#9de}</style><h1>Actual 3D repair comparison</h1><p>Identical camera poses, 1536-pixel render edge. Open images for detail. No diffusion enhancement applied to these views. Camera PSNR measures source fit, not novel-view geometry accuracy.</p>'
for label in labels:
    html+=f'<section><h2>{label} | source-camera mean PSNR: {metrics.get(label,"original 21.147")}</h2>'
    for i,file in enumerate(files[label]):html+=f'<p>{views[i]["name"]}</p><a href="{file}"><img src="{file}"></a>'
    html+='</section>'
(r.DOCS/'tuning_comparison.html').write_text(html)
r.write_json(r.DOCS/'tuning_comparison.json',dict(images=files,source_camera_psnr=metrics,poses=[v['name'] for v in views],render_edge=1536))
r.stage('Matched repair candidates rendered',f'{len(labels)} candidates compared at the same window-side and knit-detail camera poses. Higher-resolution images are in tuning_comparison.html. Rejected filters remain labelled as candidates, not final repairs.',[montage],status='selection evidence recorded')
print(json.dumps(metrics),flush=True)
