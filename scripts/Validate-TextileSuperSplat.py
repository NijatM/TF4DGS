"""Validate real exported PLY bytes, 30 fps timing and rendered compression error."""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.machinery import SourceFileLoader
import json
import math
import os
from pathlib import Path

import numpy as np
import torch
from gsplat import rasterization
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
codec=SourceFileLoader('compressed_ply_checks',str(Path(__file__).with_name('Compress-GaussianPly.py'))).load_module()
exporter=SourceFileLoader('textile_export_checks',str(Path(__file__).with_name('Export-TextileSuperSplat.py'))).load_module()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def training_coordinates(model):
    m={k:v.copy() for k,v in model.items()}
    m['means']=m['means']@exporter.ROTATION
    w,x,y,z=m['quats'].T;h=math.sqrt(.5)
    m['quats']=np.column_stack((h*(w-x),h*(x+w),h*(y-z),h*(z+y))).astype(np.float32)
    return m


def render(cloth,table):
    values={k:torch.tensor(np.concatenate((cloth[k],table[k])),device='cuda',dtype=torch.float32)for k in cloth}
    target=np.array([.175,.10,-.045]);az,el=np.deg2rad([95,48]);radius=.57
    pos=target+radius*np.array([math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),-math.sin(el)])
    forward=target-pos;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,-1]);right/=np.linalg.norm(right)
    down=np.cross(forward,right);R=np.stack((right,down,forward));view=np.eye(4);view[:3,:3]=R;view[:3,3]=-R@pos
    K=np.array([[1050,0,600],[0,1050,400],[0,0,1]],np.float32)
    with torch.no_grad():
        rgb,alpha,_=rasterization(means=values['means'],quats=values['quats'],scales=values['scales'],
            opacities=values['opacity'],colors=values['colors'],
            viewmats=torch.tensor(view,device='cuda',dtype=torch.float32)[None],
            Ks=torch.tensor(K,device='cuda')[None],width=1200,height=800,
            packed=False,near_plane=.01,far_plane=5,rasterize_mode='antialiased')
    image=(rgb[0]+(1-alpha[0])*.92).clamp(0,1).cpu().numpy()
    assert image.std()>.08 and (alpha[0]>.5).sum().item()>10000, 'Compression comparison must render a visible nonempty scene'
    return image


def main():
    p=argparse.ArgumentParser();p.add_argument('--export',default='outputs/dynamic_textile_001/supersplat_export_03')
    p.add_argument('--output',default='documentation/dynamic_textile_001/supersplat_export_summary.json');a=p.parse_args()
    folder=ROOT/a.export;manifest=read(folder/'export_manifest.json')
    sequence=read(ROOT/manifest['source_sequence']);source={f['index']:f for f in sequence['frames']}
    assert sequence['status']=='complete' and len(source)==manifest['unique_reconstructed_times']==214
    assert manifest['timeline_fps']==30 and manifest['timeline_frames']==1277
    assert manifest['newly_reconstructed_30hz_motion'] is False and manifest['persistent_material_ids'] is False
    assert manifest['context_model']==sequence['table_model']
    assert manifest['separate_static_context'] and not manifest['other_scenes_merged']
    models={};errors=[];archives=[]
    for frame in manifest['keyframes']:
        path=folder/frame['path'];assert exporter.digest(path)==frame['sha256'] and path.stat().st_size==frame['bytes']
        decoded=codec.read_compressed(path)
        assert len(decoded['means'])==frame['gaussians']==source[frame['source_index']]['gaussians']
        assert all(np.isfinite(v).all()for v in decoded.values())
        assert np.all(decoded['scales']>0) and np.all((decoded['colors']>=-1e-6)&(decoded['colors']<=1+1e-6))
        archive=codec.read_standard(folder/frame['full_quality_archive'])
        original=exporter.load(ROOT/frame['source_model'])
        assert len(archive)==len(original['means'])
        assert np.allclose(archive[:,:3],original['means']@exporter.ROTATION.T,atol=1e-7)
        assert np.allclose(archive[:,6:9]*codec.SH_C0+.5,original['colors'],atol=1e-6)
        assert np.allclose(np.exp(archive[:,10:13]),original['scales'],rtol=1e-6)
        models[frame['source_index']]=frame;errors.append(frame['quantization']);archives.append(len(archive))
    timeline=folder/manifest['supersplat_import_folder'];aliases=[];records=manifest['keyframes']
    for i,frame in enumerate(manifest['frames']):
        assert frame['frame']==i and abs(frame['time_s']-i/30)<1e-9
        expected=max((r for r in records if r['source_time_s']<=frame['time_s']+1e-9),key=lambda r:r['source_time_s'])
        assert frame['source_index']==expected['source_index'] and frame['source_time_s']==expected['source_time_s']
        path=timeline/frame['filename'];source_path=folder/expected['path']
        assert path.stat().st_size==expected['bytes']
        if frame['storage']=='hardlink':assert os.path.samefile(path,source_path)
        else:assert exporter.digest(path)==expected['sha256']
        aliases.append(frame['source_index'])
    assert set(aliases)==set(source) and aliases[0]==0 and aliases[-1]==425
    table=exporter.load(ROOT/manifest['context_model'])
    compressed_table=training_coordinates(codec.read_compressed(folder/manifest['separate_static_context']))
    assert len(table['means'])==len(compressed_table['means'])==164708
    comparisons=[]
    for index in [0,158,266,425]:
        record=models[index];original=exporter.load(ROOT/record['source_model'])
        decoded=training_coordinates(codec.read_compressed(folder/record['path']))
        before=render(original,table);after=render(decoded,compressed_table)
        mse=float(np.mean((before-after)**2));psnr=-10*math.log10(max(mse,1e-12))
        assert psnr>38, f'Inspect compression quality at {index}: {psnr:.2f} dB'
        comparisons.append(dict(source_index=index,rgb_render_psnr_db=psnr,view='Elevated iPhone-side orbit, 1200x800',
            comparison='Decoded compressed cloth+table vs retained uncompressed Gaussian scene'))
        if index==158:
            panel=Image.new('RGB',(2400,830),'#17212b');draw=ImageDraw.Draw(panel)
            panel.paste(Image.fromarray((before*255).round().astype(np.uint8)),(0,30))
            panel.paste(Image.fromarray((after*255).round().astype(np.uint8)),(1200,30))
            draw.text((12,8),'Actual full float32 Gaussian render',fill='white')
            draw.text((1212,8),f'Actual decoded compressed PLY render | {psnr:.2f} dB',fill='white')
            panel.save(ROOT/'documentation/dynamic_textile_001/29_compression_render_comparison.jpg',quality=94)
    browser=read(ROOT/'documentation/dynamic_textile_001/26_supersplat_static_context_playback_test.capture.json')['state']
    assert browser['timeline_frames']==1277 and browser['timeline_fps']==30
    assert browser['playhead']>=140 and browser['actual_data_swaps']>100
    assert len(browser['layers'])==2 and any(v['name']=='current_table.compressed.ply'for v in browser['layers'])
    result=dict(status='passed',checked_utc=datetime.now(timezone.utc).isoformat(),export=a.export,
        format=manifest['format'],timeline_fps=30,timeline_frames=1277,playback_duration_s=manifest['playback_duration_s'],
        distinct_reconstructed_times=214,median_fitted_interval_s=manifest['median_fitted_interval_s'],
        presentation=manifest['presentation'],independently_reconstructed_30hz_motion=False,
        full_quality_keyframes_checked=len(archives),compressed_keyframes_checked=len(errors),timeline_aliases_checked=len(aliases),
        unique_compressed_cloth_bytes=manifest['unique_keyframe_bytes'],
        unique_compressed_context_bytes=manifest['static_context_export']['quantization']['bytes'],
        maximum_cloth_position_quantization_error_mm=max(e['maximum_position_error_mm']for e in errors),
        maximum_cloth_rgb_channel_quantization_error=max(e['maximum_rgb_channel_error']for e in errors),
        maximum_cloth_opacity_quantization_error=max(e['maximum_opacity_error']for e in errors),
        gaussian_count_preserved=True,full_float32_archive_retained=True,
        compression_render_comparisons=comparisons,actual_online_editor='SuperSplat 3.5.2',
        actual_online_playback_test=browser,sustained_30_data_swaps_per_second_verified=False,
        online_playback_scope='Five-second machine-specific test; timeline advances at source speed, data swaps can skip held duplicates',
        hidden_geometry_accuracy_verified=False,persistent_material_ids=False,published=False,
        source_policy='Current textile capture only',files_ignored_by_git=True)
    (ROOT/a.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
