"""Export real-time, numbered RGB Gaussian PLYs for the SuperSplat editor.

The 30 Hz presentation holds measured-time fitted keyframes. It does not
manufacture 30 independent reconstructions or material correspondences.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
from importlib.machinery import SourceFileLoader

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROPERTIES = ['x', 'y', 'z', 'nx', 'ny', 'nz', 'f_dc_0', 'f_dc_1',
              'f_dc_2', 'opacity', 'scale_0', 'scale_1', 'scale_2',
              'rot_0', 'rot_1', 'rot_2', 'rot_3']
# Board XY, negative Z above table -> PLY Y down; SuperSplat's default
# PLY import applies its conventional 180-degree rotation around Z.
ROTATION = np.array([[1., 0., 0.], [0., 0., 1.], [0., -1., 0.]])


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def load(path):
    with np.load(path) as source:
        model = {k: source[k] for k in ['means', 'colors', 'opacity', 'scales', 'quats']}
    count = len(model['means'])
    assert all(len(v) == count and np.isfinite(v).all() for v in model.values())
    assert np.all(model['scales'] > 0)
    assert np.all((model['colors'] >= 0) & (model['colors'] <= 1))
    assert np.all((model['opacity'] >= 0) & (model['opacity'] <= 1))
    assert np.allclose(np.linalg.norm(model['quats'], axis=1), 1, atol=2e-5)
    return model


def write_ply(path, model):
    xyz = model['means'] @ ROTATION.T
    # Left-multiply wxyz quaternions by the same Rx(-90 degrees).
    w, x, y, z = model['quats'].T
    h = math.sqrt(.5)
    q = np.column_stack((h*(w+x), h*(x-w), h*(y+z), h*(z-y)))
    alpha = np.clip(model['opacity'], 1e-6, 1-1e-6)
    rows = np.column_stack((xyz, np.zeros_like(xyz),
        (model['colors']-.5)/.28209479177387814,
        np.log(alpha/(1-alpha)), np.log(model['scales']), q)).astype('<f4')
    header = ['ply', 'format binary_little_endian 1.0',
        'comment TF4DGS RGB Gaussian snapshot; current textile capture only',
        f'element vertex {len(rows)}',
        *[f'property float {p}' for p in PROPERTIES], 'end_header']
    with path.open('xb') as stream:
        stream.write(('\n'.join(header)+'\n').encode('ascii'))
        rows.tofile(stream)
    # Read actual export bytes and check every row against transformed source.
    with path.open('rb') as stream:
        while stream.readline() != b'end_header\n':
            assert stream.tell() < 4096
        decoded = np.frombuffer(stream.read(), dtype='<f4').reshape(-1, 17)
    assert np.array_equal(decoded, rows) and len(decoded) == len(model['means'])
    return dict(gaussians=len(rows), bytes=path.stat().st_size, sha256=digest(path))


def link_or_copy(source, target):
    try:
        os.link(source, target)
        return 'hardlink'
    except OSError:
        shutil.copyfile(source, target)
        assert digest(target) == digest(source)
        return 'copy'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sequence', default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    parser.add_argument('--validation', default='.local/workflows/dynamic_setup/textile_reconstruction_02/validation_final.json')
    parser.add_argument('--output', default='outputs/dynamic_textile_001/supersplat_export_01')
    parser.add_argument('--fps', type=int, default=30)
    parser.add_argument('--compressed', action='store_true', help='Retain float32 archives and add smaller compressed PLY viewer copies')
    parser.add_argument('--table-model', help='Explicit current-capture context override; source sequence is unchanged')
    parser.add_argument('--separate-context', action='store_true', help='Import one static table layer separately; animated files contain only cloth for faster playback')
    a = parser.parse_args()
    assert 1 <= a.fps <= 60
    sequence = read(ROOT/a.sequence)
    validation = read(ROOT/a.validation)
    assert sequence['status'] == 'complete' and validation['status'] == 'passed'
    assert validation['partial'] is False and validation['completed_frames'] == len(sequence['frames'])
    assert [f['index'] for f in sequence['frames']] == sequence['requested_indexes']
    output = (ROOT/a.output).resolve()
    output.relative_to(ROOT/'outputs')
    if output.exists():
        raise FileExistsError('Preserve previous exports; choose a new output folder.')
    output.mkdir()
    keyframes = output/'keyframes_full_quality'
    compressed = output/'keyframes_compressed'
    timeline = output/f'rgb_{a.fps}fps'
    preview = output/'single_frame_preview'
    for folder in [keyframes, timeline, preview]:
        folder.mkdir()
    codec = None
    if a.compressed:
        compressed.mkdir()
        codec = SourceFileLoader('tf4dgs_compressed_ply',str(Path(__file__).with_name('Compress-GaussianPly.py'))).load_module()
    table_path = a.table_model or sequence['table_model']
    context = load(ROOT/table_path)
    table_summary = read((ROOT/table_path).with_name('summary.json'))
    assert table_summary['source_policy'] == 'current textile capture only'
    assert table_summary['other_scenes_merged'] is False
    context_file = None
    context_export = None
    if a.separate_context:
        context_folder=output/'context';context_folder.mkdir()
        context_path=context_folder/'current_table.ply'
        context_export=write_ply(context_path,context)
        if codec:
            context_copy=context_folder/'current_table.compressed.ply'
            context_export['quantization']=codec.compress(context_path,context_copy)
            context_path=context_copy
        context_file=context_path.relative_to(output).as_posix()
    records = []
    for frame in sequence['frames']:
        cloth = load(ROOT/frame['model'])
        combined = cloth if a.separate_context else {k: np.concatenate((cloth[k], context[k])) for k in cloth}
        path = keyframes/f"textile_{frame['index']:06d}.ply"
        info = write_ply(path, combined)
        archive_path = path.relative_to(output).as_posix()
        quantization = None
        if codec:
            path_compressed = compressed/f"textile_{frame['index']:06d}.compressed.ply"
            quantization = codec.compress(path,path_compressed)
            path = path_compressed
            info = dict(gaussians=len(combined['means']),bytes=path.stat().st_size,sha256=digest(path))
        records.append(dict(source_index=frame['index'], source_time_s=frame['time_s'],
            source_model=frame['model'], path=path.relative_to(output).as_posix(),
            full_quality_archive=archive_path,quantization=quantization,
            textile_gaussians=len(cloth['means']), context_gaussians=0 if a.separate_context else len(context['means']), **info))
        print(json.dumps(dict(exported_keyframes=len(records), source_index=frame['index'])), flush=True)
    last = records[-1]['source_time_s']
    count = math.ceil(last*a.fps)+1
    samples = []
    source_number = 0
    for number in range(count):
        t = number/a.fps
        while source_number+1 < len(records) and records[source_number+1]['source_time_s'] <= t+1e-9:
            source_number += 1
        record = records[source_number]
        filename = f'textile_{number:06d}'+('.compressed.ply' if codec else '.ply')
        source = output/record['path']
        method = link_or_copy(source, timeline/filename)
        assert (timeline/filename).stat().st_size == record['bytes']
        if method == 'hardlink':
            assert os.path.samefile(source, timeline/filename)
        samples.append(dict(frame=number, time_s=t, filename=filename,
            source_index=record['source_index'], source_time_s=record['source_time_s'], storage=method))
    assert samples[0]['source_index'] == records[0]['source_index']
    assert samples[-1]['source_index'] == records[-1]['source_index']
    fold = min(records, key=lambda r: abs(r['source_index']-158))
    link_or_copy(output/fold['path'], preview/('textile_fold_rgb.compressed.ply' if codec else 'textile_fold_rgb.ply'))
    report = dict(status='complete and byte-validated', recorded_utc=datetime.now(timezone.utc).isoformat(),
        source_sequence=a.sequence, context_model=table_path,
        format='PlayCanvas compressed PLY sequence' if codec else 'Standard binary 3D Gaussian PLY sequence',
        supersplat_import_folder=timeline.relative_to(output).as_posix(), timeline_fps=a.fps,
        timeline_frames=count, playback_duration_s=count/a.fps, last_fitted_time_s=last,
        unique_reconstructed_times=len(records), median_fitted_interval_s=float(np.median(np.diff([r['source_time_s'] for r in records]))),
        presentation='Hold latest fitted state at each output timestamp; no temporal interpolation',
        newly_reconstructed_30hz_motion=False, rendering_30fps_guaranteed=False,
        persistent_material_ids=False, metric_accuracy_verified=False,
        includes_current_table=True, other_scenes_merged=False,
        separate_static_context=context_file, static_context_export=context_export,
        coordinate_transform_training_to_ply=ROTATION.tolist(),
        original_gaussian_count_preserved=True,
        color_scale_opacity_rotation_precision='Chunk-quantized viewer copy; full float32 archive retained' if codec else 'float32; no compression or decimation',
        unique_keyframe_bytes=sum(r['bytes'] for r in records),
        timeline_logical_bytes=sum(records[next(i for i,r in enumerate(records) if r['source_index']==s['source_index'])]['bytes'] for s in samples),
        supersplat_reference='https://developer.playcanvas.com/user-manual/supersplat/editor/import-export/',
        official_loader_checked_at_revision='f2a1b4975b4766e0ee0c95e63c2737dc2ecb6e5b',
        keyframes=records, frames=samples)
    (output/'export_manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (output/'README.md').write_text(f'''# Textile RGB Gaussian sequence for SuperSplat

1. Open https://superspl.at/editor/ in current Edge or Chrome.
2. {'Import **'+context_file+'** first as a static layer, then import' if context_file else 'Import'} the files in **rgb_{a.fps}fps** together. Select only that folder's PLYs,
   or drop that folder; do not drop this whole export root.
3. Set Timeline FPS to **{a.fps}**, length **{count}**. Play or scrub.
4. For a quick quality check, load the PLY in **single_frame_preview** alone.

The {count}-frame timeline plays in {count/a.fps:.3f} seconds. It holds {len(records)}
fitted RGB Gaussian states covering 0–{last:.3f} seconds. This is a {a.fps} fps
presentation with approximately five new reconstructed states per second,
not independently reconstructed {a.fps} Hz motion. Actual rendering throughput
depends on the browser and GPU; real-time {a.fps} fps is not guaranteed.

{'The separate static context layer contains' if context_file else 'Every frame includes'} this recording's marker board and nearby table. No old
scenes were merged. Gaussian counts are preserved. Full float32 attributes
are retained in **keyframes_full_quality**. If a compressed timeline is selected,
it uses the supported quantized format; per-frame errors are in the manifest.
The export rotates board coordinates into the PLY convention so that the
cloth/table imports upright with SuperSplat's default orientation.

Repeated timeline files are NTFS hardlinks where available, sharing storage
with this export's keyframes. They never link to the original trained models.
Copying this folder to another drive may expand repeated files. Treat the
export as read-only; save editor changes into a new folder.

Source timestamps, aliases, SHA256 hashes, geometry limitations and total
logical/unique sizes are in **export_manifest.json**. These local models remain
excluded from Git. Hidden folds and material strain are not independently verified.
''', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['keyframes','frames']}, indent=2))


if __name__ == '__main__':
    main()
