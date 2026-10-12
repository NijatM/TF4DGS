"""Record reviewed parameter selection, final copies and source preservation."""
import argparse
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
p=argparse.ArgumentParser();p.add_argument('--selected',required=True);p.add_argument('--reason',required=True);a=p.parse_args()
manifest=json.loads((r.WORK/'manifest.json').read_text());entry=manifest['files'][2];tuning=r.WORK/'tuning'/entry['folder']
rows=[]
baseline=json.loads(Path(entry['output']).with_suffix('.difix3d.json').read_text())
rows.append(dict(recipe='first_pass',steps=baseline['steps'],edge=baseline['training_edge'],psnr=baseline['after']['mean_psnr'],status='user found little visible repair'))
for recipe in ['wide_official','wide_strong','wide_strong_pruned_balanced','wide_official_pruned_conservative','geometry_recovery','opacity_recovery']:
    path=tuning/('splat_90000_'+recipe+'_Difix3D.difix3d.json')
    if not path.exists():continue
    record=json.loads(path.read_text());metrics=record.get('after',record.get('after_pruning',{}))
    status='selected' if recipe==a.selected else 'not selected'
    if 'pruned' in recipe or recipe=='geometry_recovery':status='rejected: damaged source reconstruction'
    rows.append(dict(recipe=recipe,steps=record.get('steps'),edge=record.get('training_edge'),psnr=metrics.get('mean_psnr'),status=status))
final=[]
for e in manifest['files'][:3]:
    path=Path(e['path']).with_name(Path(e['name']).stem+'_Refined_Difix3D.ply')
    if not path.exists():raise FileNotFoundError(path)
    record=json.loads(path.with_suffix('.difix3d.json').read_text())
    if not record.get('reopened_ply_verified') or r.sha(path)!=record['output_sha256']:raise ValueError('Unverified final export')
    final.append(dict(input=e['name'],output=path.name,gaussians=e['count'],before=record['before']['mean_support_psnr'],first_pass=record['first_pass']['mean_support_psnr'],selected=record['after']['mean_support_psnr'],output_sha256=record['output_sha256'],reopened_ply_verified=True))
for e in manifest['files']:
    if r.sha(Path(e['path']))!=e['sha256']:raise ValueError('Original modified: '+e['name'])
report=dict(selected=a.selected,reason=a.reason,candidates=rows,final_2m=final,all_eight_original_hashes_preserved=True,limitations='Window/glass streaks and unobserved surfaces are not fully repaired. Source-camera scores are not independent novel-view accuracy. No diffusion enhancer applied to evidence.')
r.write_json(r.DOCS/'tuning_results.json',report)
text='# Stronger 2M repair results\n\n'+a.reason+'\n\nOriginal camera audit:21.147dB. These scores measure fit to existing photographs, not independent geometry accuracy.\n\n| Candidate | Updates | Training edge | Camera PSNR | Decision |\n| --- | ---: | ---: | ---: | --- |\n'
for row in rows:text+=f'| {row["recipe"]} | {row["steps"] or "filter only"} | {row["edge"] or "1024 audit"} | {row["psnr"]:.3f} | {row["status"]} |\n'
text+='\nFinal stronger copies are saved in the original `MRNF_2m-90k` folder with `_Refined_Difix3D.ply` suffix. Previous repairs remain available. Crops, rotations and Gaussian counts are preserved. All eight original SHA256 hashes were rechecked.\n\n| Export | Gaussian count | Support camera PSNR: original / first pass / selected |\n| --- | ---: | --- |\n'
for row in final:text+=f'| {row["output"]} | {row["gaussians"]:,} | {row["before"]:.3f} / {row["first_pass"]:.3f} / {row["selected"]:.3f} |\n'
text+='\nResidual window/glass streaks remain. Missing surfaces outside the photographs are not established as recovered. Rejected attempts are retained in ignored work folders and chronological evidence.\n\n[Actual rendered comparison](tuning_comparison.html) · [Chronological report](index.html)\n'
(r.DOCS/'TUNING_RESULTS.md').write_text(text,encoding='utf8')
r.stage('Stronger 2M repair tests completed',a.reason+' Three saved variants independently reopened and all eight original hashes preserved. Residual artifacts are documented.',status='completed; limitations recorded')
print(json.dumps(report),flush=True)
