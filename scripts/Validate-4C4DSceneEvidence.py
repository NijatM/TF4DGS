"""Validate final videos, cadence, hashes and byte-range replay; no GPU needed."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/4c4d_scene_001'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    ffmpeg = next(tool for tool in read(ROOT / 'static-tools.json')['portable_tools'] if tool['name'] == 'FFmpeg')
    registry = read(ROOT / 'outputs/4c4d_scene_001/selected_models.json')
    checks = []
    for dataset in ['textile', 'yogurt']:
        model = ROOT / registry[dataset]['model']
        if ROOT / 'outputs/4c4d_scene_001' not in model.resolve().parents:
            raise ValueError('Foreign model in selected registry')
        for mode in ['fixed', 'orbit']:
            video = DOCS / f'{dataset}_selected_{mode}_30fps.mp4'
            probe = json.loads(subprocess.check_output([ffmpeg['ffprobe_path'], '-v', 'error',
                '-select_streams', 'v:0', '-show_streams', '-show_frames', '-show_entries',
                'frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
            stream = probe['streams'][0]
            pts = [float(frame['best_effort_timestamp_time']) for frame in probe['frames']]
            error = max(abs(value - i / 30) for i, value in enumerate(pts))
            if len(pts) != 90 or error > .000001 or stream['r_frame_rate'] != '30/1':
                raise ValueError(f'Invalid 30fps cadence: {video.name}')
            if any(stream.get(key) != 'bt709' for key in ['color_space', 'color_transfer', 'color_primaries']) or stream.get('color_range') != 'tv':
                raise ValueError(f'Unexpected encoded color metadata: {video.name}')
            subprocess.run([ffmpeg['executable_path'], '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'], check=True)
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8109/' + video.name,
                    headers={'Range': 'bytes=0-1023'})) as response:
                if response.status != 206 or response.read() != video.read_bytes()[:1024]:
                    raise ValueError(f'HTTP byte range mismatch: {video.name}')
            reference = read(video.with_suffix('.validation.json'))
            if reference['maximum_channel_error_8bit'] > 1:
                raise ValueError('Continuous decoder differs from training render')
            checks.append({'dataset': dataset, 'mode': mode, 'file': video.name,
                'bytes': video.stat().st_size, 'sha256': hashlib.sha256(video.read_bytes()).hexdigest(),
                'width': stream['width'], 'height': stream['height'], 'frames': len(pts),
                'fps': '30/1', 'duration_s': float(stream['duration']),
                'color_matrix': stream['color_space'], 'color_transfer': stream['color_transfer'],
                'color_primaries': stream['color_primaries'], 'color_range': stream['color_range'],
                'max_timestamp_error_s': error, 'full_decode_passed': True,
                'http_206_bytes_match': True, 'decoder_reference': reference,
                'model': str(model.relative_to(ROOT)).replace('\\', '/'),
                'model_bytes': model.stat().st_size, 'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest()})
    result = {'scope': 'Full file decode, cadence, reference decoder and HTTP ranges; browser playback checked separately.',
              'videos': checks, 'documentation_video_bytes': sum(item['bytes'] for item in checks)}
    (DOCS / 'video_validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'validated_videos': len(checks), 'bytes': result['documentation_video_bytes']}))


if __name__ == '__main__':
    main()
