"""Verify every requested output and preserve unaligned-attempt evidence."""
from importlib.util import spec_from_file_location,module_from_spec
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=spec_from_file_location('repair',ROOT/'scripts/Repair-Difix3DSplats.py');r=module_from_spec(spec);spec.loader.exec_module(r)
manifest=json.loads((r.WORK/'manifest.json').read_text());summary=[]
for entry in manifest['files']:
    output=Path(entry['output']);record=json.loads(output.with_suffix('.difix3d.json').read_text())
    assert r.sha(Path(entry['path']))==entry['sha256'], 'Original changed: '+entry['name']
    assert r.sha(output)==record['output_sha256'], 'Output hash mismatch'
    assert record['reopened_ply_verified'], 'Reopened render check missing'
    data,_,_=r.read_ply(output);assert len(data)==entry['count']
    summary.append(dict(input=entry['name'],output=output.name,folder=entry['folder'],gaussians=len(data),
        bytes=output.stat().st_size,before_psnr=record['before']['mean_psnr'],after_psnr=record['after']['mean_psnr'],
        change_db=record['after']['mean_psnr']-record['before']['mean_psnr'],
        support_change_db=record['after']['mean_support_psnr']-record['before']['mean_support_psnr'],
        reopened_ply_verified=True,original_preserved=True,peak_cuda_gib=record['peak_cuda_gib']))
    directory=r.WORK/entry['folder']/Path(entry['name']).stem
    archive=directory.with_name(directory.name+'_failed_unaligned_01')
    if archive.exists() and (archive/'targets.json').exists():
        old=json.loads((archive/'targets.json').read_text());audit=[x for x in old['records'] if x['kind']=='audit'];novel=[x for x in old['records'] if x['kind']=='novel']
        prefix=entry['folder']+'_'+Path(entry['name']).stem
        before=prefix+'_failed_unaligned_01_before.jpg'
        r.montage(r.DOCS/before,[[archive/Path(x['target']).name,archive/Path(x['before']).name] for x in audit[:3]],['Photograph','FAILED: unaligned camera render'])
        photos=[];comp=prefix+'_failed_unaligned_01_comparison.jpg'
        for i,x in enumerate(audit[:3]):
            after=archive/f'audit_{i:03d}_refined.png'
            if after.exists():photos.append([archive/Path(x['target']).name,archive/Path(x['before']).name,after])
        if photos:r.montage(r.DOCS/comp,photos,['Photograph','FAILED: unaligned input','FAILED: unaligned refinement'])
        journal=json.loads((r.DOCS/'journal.json').read_text());cutoff=min(x['number'] for x in journal if x['title']=='Failed camera alignment: '+entry['name'])
        for row in journal:
            if row['number']>=cutoff or entry['name'] not in row['title']:continue
            row['status']='failed camera alignment; superseded by corrected test'
            row['detail']+=' Later review identified camera/model misalignment; this attempt is rejected.'
            row['images']=[comp if photos and 'Exported' in row['title'] else before]
        r.write_json(r.DOCS/'journal.json',journal)
        r.stage('Preserved failed alignment evidence: '+entry['name'],'Actual unaligned input/output renderings regenerated from the archived failed attempt. These are rejected results, retained separately from the corrected export.',[before]+([comp] if photos else []),status='failed attempt documented')
    elif archive.exists():
        pairs=[]
        for image in sorted(archive.glob('anchor_*_before.png'))[:3]:
            reference=image.with_name(image.name.replace('_before.png','_reference.png'))
            if reference.exists():pairs.append([reference,image])
        if pairs:
            evidence=entry['folder']+'_'+Path(entry['name']).stem+'_failed_partial_alignment.jpg'
            r.montage(r.DOCS/evidence,pairs,['Original photograph','FAILED: interrupted unaligned render'])
            r.stage('Preserved interrupted alignment evidence: '+entry['name'],'Partial renderings from the stopped unaligned attempt. No incorrect final export is retained in the source folder.',[evidence],status='interrupted attempt documented')
r.write_json(r.DOCS/'summary.json',dict(models=summary,total=len(summary),originals_preserved=True,
    scope='Camera audit, not independent held-out evaluation; 750-update repair tests with actual exported 3D PLY verification.'))
lines=['# Difix3D Necto repair tests','','All eight original PLYs preserved. Outputs saved beside originals with `_Difix3D` suffix. These are bounded repair tests; residual novel-view artifacts remain possible.','','| Input | Count | Before / after camera PSNR | Change |','| --- | ---: | --- | ---: |']
for x in summary:lines.append(f'| {x["input"]} | {x["gaussians"]:,} | {x["before_psnr"]:.2f} / {x["after_psnr"]:.2f} | {x["change_db"]:+.2f} dB |')
lines+=['','Camera scores use images available during original training. They do not establish physical accuracy or recovery of unobserved surfaces. Isolated variants are evaluated with support scores in JSON as well.','','[Chronological evidence](index.html) · [Adapter and reproducibility](../../docs/DIFIX3D_NECTO_TEST.md)']
(r.DOCS/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
r.stage('All requested PLY repair tests verified',f'{len(summary)}/8 exports reopened and rendered; all originals match their pre-test SHA256. Camera audit results are recorded in RESULTS.md and summary.json. Full comparison includes original images, actual splats and separately labelled diffusion targets.',status='batch complete; review quality comparisons')
print(json.dumps(summary,indent=2),flush=True)
