"""Restore SuperSplat timeline aliases from the release's unique keyframes.

Only Python's standard library is needed. Existing files must match; they are
never overwritten. Hardlinks share storage, with a copy fallback for filesystems
that do not support them. No new reconstructed motion is generated.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def inside(root, relative):
    path = (root / relative).resolve()
    path.relative_to(root)
    return path


def restore(root):
    root = root.resolve(strict=True)
    manifest = json.loads((root / 'export_manifest.json').read_text(encoding='utf-8-sig'))
    fps = manifest['timeline_fps']
    records = manifest['keyframes']
    frames = manifest['frames']
    if fps != 30 or len(records) != 214 or len(frames) != 1277:
        raise ValueError('Expected the selected 214-state, 1277-frame textile baseline')
    if manifest['persistent_material_ids'] or manifest['newly_reconstructed_30hz_motion']:
        raise ValueError('This helper restores held keyframes, not continuous motion')
    sources = {}
    for record in records:
        source = inside(root, record['path'])
        if source.stat().st_size != record['bytes'] or digest(source) != record['sha256']:
            raise ValueError('Keyframe size/hash mismatch: ' + record['path'])
        sources[record['source_index']] = (source, record)
    context = inside(root, manifest['separate_static_context'])
    if context.stat().st_size != manifest['static_context_export']['quantization']['bytes']:
        raise ValueError('Static context size mismatch')
    timeline = inside(root, manifest['supersplat_import_folder'])
    tasks = []
    for number, frame in enumerate(frames):
        if frame['frame'] != number or frame['filename'] != f'textile_{number:06d}.compressed.ply':
            raise ValueError('Unexpected timeline filename/order')
        if not math.isclose(frame['time_s'], number / fps, abs_tol=1e-9):
            raise ValueError('Unexpected timeline timestamp')
        source, record = sources[frame['source_index']]
        if frame['source_time_s'] != record['source_time_s']:
            raise ValueError('Timeline/source timestamp mismatch')
        target = inside(root, manifest['supersplat_import_folder'] + '/' + frame['filename'])
        if target.exists() and not os.path.samefile(source, target):
            if target.stat().st_size != record['bytes'] or digest(target) != record['sha256']:
                raise ValueError('Refusing to overwrite a different file: ' + str(target))
        tasks.append((source, target))
    timeline.mkdir(exist_ok=True)
    counts = {'hardlinked': 0, 'copied': 0, 'existing': 0}
    for source, target in tasks:
        if target.exists():
            counts['existing'] += 1
            continue
        try:
            os.link(source, target)
            counts['hardlinked'] += 1
        except OSError:
            # Exclusive creation prevents overwriting a file created meanwhile.
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            if digest(target) != digest(source):
                raise ValueError('Copied timeline file hash mismatch')
            counts['copied'] += 1
    return dict(status='restored and validated', timeline_frames=len(tasks),
                unique_reconstructed_times=len(records), fps=fps, **counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, default=Path(
        'outputs/dynamic_textile_001/supersplat_export_03'))
    args = parser.parse_args()
    print(json.dumps(restore(args.export), indent=2))


if __name__ == '__main__':
    main()
