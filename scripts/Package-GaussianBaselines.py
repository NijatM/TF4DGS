"""Package selected Gaussian baselines as GitHub Release assets, not Git/LFS.

Uses only the standard library. Captures, training checkpoints and failed trials
are excluded. ZIP entries are verified by CRC and SHA-256 after compression.
The originals are read only; existing packages are never overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_bundle(target, paths, description, overrides=None):
    overrides = overrides or {}
    records = []
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for path in sorted(set(paths)):
            name = path.relative_to(ROOT).as_posix()
            original = path.read_bytes()
            content = overrides.get(name, original)
            archive.writestr(name, content)
            records.append(dict(path=name, bytes=len(content), sha256=sha(content),
                                source_sha256=sha(original)))
        archive.writestr(target.stem + '.README.md', description)
        archive.writestr(target.stem + '.manifest.json', json.dumps(dict(
            files=records, original_captures_included=False,
            training_checkpoints_included=False,
            path_separators_normalized=sorted(overrides)), indent=2) + '\n')
    with zipfile.ZipFile(target) as archive:
        error = archive.testzip()
        if error:
            raise ValueError('ZIP CRC failure: ' + error)
        for record in records:
            content = archive.read(record['path'])
            if len(content) != record['bytes'] or sha(content) != record['sha256']:
                raise ValueError('ZIP SHA-256 failure: ' + record['path'])
    report = dict(filename=target.name, bytes=target.stat().st_size,
                  uncompressed_selected_bytes=sum(r['bytes'] for r in records),
                  selected_files=len(records), zip_crc_and_sha256_passed=True,
                  sha256=sha(target.read_bytes()))
    print(json.dumps(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=Path('outputs/release_assets/baseline_2026-10-08'))
    parser.add_argument('--summary', type=Path,
                        default=Path('documentation/baseline_release/package_summary.json'))
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    output.relative_to((ROOT / 'outputs').resolve())
    summary_path = (ROOT / args.summary).resolve()
    summary_path.relative_to((ROOT / 'documentation').resolve())
    if output.exists() or summary_path.exists():
        raise FileExistsError('Use new output/summary paths; earlier packages are retained')
    textile = ROOT / 'outputs/dynamic_textile_001/supersplat_export_03'
    manifest = read(textile / 'export_manifest.json')
    if len(manifest['keyframes']) != 214 or manifest['timeline_frames'] != 1277:
        raise ValueError('Selected textile sequence is incomplete')
    textile_files = [textile / r['path'] for r in manifest['keyframes']]
    for record, path in zip(manifest['keyframes'], textile_files):
        if path.stat().st_size != record['bytes'] or sha(path.read_bytes()) != record['sha256']:
            raise ValueError('Selected textile keyframe changed: ' + str(path))
    textile_files += [textile / manifest['separate_static_context'],
                      textile / 'export_manifest.json']
    actor = ROOT / 'outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid'
    background = ROOT / 'outputs/dynamic_yogurt_001/static_background_03/trained_01'
    motion = read(actor / 'motion.json')
    motion['poses'] = motion['poses'].replace('\\', '/')
    poses = ROOT / motion['poses']
    pose_data = read(poses)
    valid = [i for i, p in enumerate(pose_data['frames']) if p and p['valid']]
    if valid != motion['valid_indices'] or len(valid) != 53 or len(motion['persistent_ids']) != 51913:
        raise ValueError('Selected yogurt model/poses disagree')
    background_info = read(background / 'summary.json')
    session = ROOT / background_info['session']
    session_data = read(session)
    yogurt_files = [actor / name for name in (
        'canonical_actor.npz', 'canonical_actor.ply', 'motion.json', 'summary.json')]
    yogurt_files += [background / name for name in (
        'static_background.npz', 'static_background.ply', 'summary.json')]
    yogurt_files += [poses, session]
    yogurt_files += [session.parent / c['calibration'] for c in session_data['cameras']]
    if background_info['source_policy'] != 'current capture only':
        raise ValueError('A different recording cannot supply the yogurt background')
    for path in textile_files + yogurt_files:
        path.resolve(strict=True).relative_to(ROOT)
        if '/raw/' in path.as_posix() or path.suffix not in {'.ply', '.npz', '.json'}:
            raise ValueError('Unexpected bundle input: ' + str(path))
    output.mkdir(parents=True)
    reports = []
    reports.append(write_bundle(output / 'TF4DGS-textile-baseline.zip', textile_files,
        '# Textile RGB Gaussian baseline\n\n'
        'Extract into a fresh TF4DGS checkout root. Then run:\n\n'
        '```powershell\nconda run -n tf4dgs python scripts/Restore-TextileTimeline.py\n```\n\n'
        'Import context/current_table.compressed.ply from '
        'outputs/dynamic_textile_001/supersplat_export_03 first in SuperSplat, '
        'then all restored rgb_30fps files together. Set 30 FPS and 1277 frames.\n\n'
        'Contains all 214 selected compressed keyframes and the static table. '
        'Approximately five new fitted states per second; held 30 FPS presentation, '
        '42.567 seconds. No continuous deformation, material strain or guaranteed '
        '30 FPS rendering. Native float32 archives remain local and are not bundled. '
        'Original Gaussian counts are preserved; quantization errors are in the manifest.\n'))
    portable_motion = (json.dumps(motion, indent=2) + '\n').encode('utf-8')
    reports.append(write_bundle(output / 'TF4DGS-yogurt-baseline.zip', yogurt_files,
        '# Yogurt rigid Gaussian baseline\n\n'
        'Extract into a fresh TF4DGS checkout root, with the documented '
        'tf4dgs-dynamic CUDA environment installed. Then run:\n\n'
        '```powershell\nconda run --no-capture-output -n tf4dgs-dynamic '
        'python scripts/Serve-RigidGaussianPreview.py\n```\n\n'
        'Open http://127.0.0.1:8100/. Original footage is not required for playback. '
        'The bundle includes the full-precision actor/background NPZs and static '
        'PLYs, 53 supported rigid poses, session and camera calibration. '
        'The 51913 actor IDs persist. Unsupported times are not interpolated. '
        'Appearance is time-constant; off-table depth and metric accuracy are '
        'unverified. These PLYs alone do not store animation. '
        'Only the motion metadata path separator is normalized for portability.\n',
        overrides={(actor / 'motion.json').relative_to(ROOT).as_posix(): portable_motion}))
    result = dict(status='complete and archive-validated',
                  recorded_utc=datetime.now(timezone.utc).isoformat(),
                  distribution='GitHub Release assets; no Git LFS tracking',
                  local_output=args.output.as_posix(),
                  archives=reports, total_archive_bytes=sum(r['bytes'] for r in reports),
                  uploaded=False, git_staging_or_commit_performed=False,
                  continuous_textile_deformation_model=False)
    (output / 'SHA256SUMS.txt').write_text(''.join(
        r['sha256'] + '  ' + r['filename'] + '\n' for r in reports), encoding='ascii')
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
