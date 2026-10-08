"""Check actual textile browser clips, displayed source times and decoding."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
from importlib.machinery import SourceFileLoader

ROOT=Path(__file__).resolve().parents[1]
previous=SourceFileLoader('prior_video_checks',str(Path(__file__).with_name('Validate-WebViewerRecordings.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',default='documentation/dynamic_textile_001/videos')
    p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json');a=p.parse_args()
    folder=ROOT/a.directory;sequence=previous.read(ROOT/a.sequence)
    assert sequence['status']=='complete' and len(sequence['frames'])==len(sequence['requested_indexes'])
    frames={f['index']:f for f in sequence['frames']}
    tool=next(t for t in previous.read(ROOT/'static-tools.json')['portable_tools'] if t['name']=='FFmpeg')
    reports=[]
    for name,mode in [('textile_rgb_orbit','rgb'),('textile_shape_and_appearance','combined')]:
        path=folder/f'{name}.mp4';record=previous.read(path.with_suffix('.capture.json'))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        assert path.stat().st_size==record['bytes']
        assert record['method']=='CDP Page.startScreencast actual browser PNG paint frames'
        assert record['viewer_url']=='http://127.0.0.1:8104/'
        assert (record['width'],record['height'],record['frame_rate'])==(1500,1150,'30/1')
        assert record['codec']=='h264' and record['pixel_format']=='yuv420p'
        assert abs(record['duration_error_s'])<=.06 and previous.faststart(path)
        assert not record['audio'] and record['crf']==20
        state=record['initial_state'];playback=record['playback_state']
        assert state['mode']==mode and state['keyframes']==len(frames)
        assert state['persistent_material_ids'] is False and state['time_interpolation'] is False
        samples=playback['source_samples'];indexes=[s['index'] for s in samples]
        assert indexes==playback['keyframes_displayed'] and len(set(indexes))==len(indexes)
        assert indexes[0]==sequence['frames'][0]['index'] and indexes[-1]==sequence['frames'][-1]['index']
        assert all(b['time_s']>a1['time_s'] for a1,b in zip(samples,samples[1:]))
        for sample in samples:
            assert abs(sample['time_s']-frames[sample['index']]['time_s'])<1e-8
            assert 50-1e-6<=sample['azimuth_deg']<=140+1e-6
            assert sample['elevation_deg']==48 and sample['distance_m']==.57
        offsets=[s['azimuth_deg']-95 for s in samples]
        assert min(offsets)<-40 and max(offsets)>40
        assert abs(playback['source_last_s']-sequence['frames'][-1]['time_s'])<1e-8
        assert state['source_duration_s']<=playback['wall_elapsed_s']<=state['source_duration_s']+4
        subprocess.run([tool['executable_path'],'-hide_banner','-loglevel','error','-nostdin','-i',str(path),'-f','null','-'],check=True)
        reports.append(dict(filename=path.name,mode=mode,duration_s=record['duration_s'],bytes=record['bytes'],
            source_keyframes_displayed=len(samples),source_keyframes_available=len(frames),
            source_first_s=samples[0]['time_s'],source_last_s=samples[-1]['time_s'],
            complete_decode='passed',sha256='matched',faststart=True,source_timing='matched',orbit_arc='verified',
            compression='H.264 CRF20; visually high quality, not mathematical losslessness'))
    result=dict(status='passed',checked_utc=datetime.now(timezone.utc).isoformat(),clips=reports,
        total_bytes=sum(r['bytes'] for r in reports),metric_accuracy_verified=False,
        scope='Actual browser recording integrity and displayed time provenance, not independent deformation accuracy.')
    (folder/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
