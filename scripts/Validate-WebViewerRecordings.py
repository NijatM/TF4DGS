"""Check documentation clips, source sample provenance and complete decoding.

These checks validate the recordings, not physical reconstruction accuracy.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess

import numpy as np
from scipy.spatial.transform import Rotation


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def faststart(path):
    atoms={}
    with path.open('rb') as stream:
        while stream.tell()<path.stat().st_size:
            offset=stream.tell();header=stream.read(8)
            if len(header)!=8:raise ValueError('Truncated MP4 atom')
            size,kind=struct.unpack('>I4s',header)
            if size==1:size=struct.unpack('>Q',stream.read(8))[0]
            if size==0:size=path.stat().st_size-offset
            if size<8:raise ValueError('Invalid MP4 atom')
            atoms.setdefault(kind,offset);stream.seek(offset+size)
    return atoms[b'moov']<atoms[b'mdat']


def main():
    out=Path('documentation/dynamic_capture_001/videos')
    names=['yogurt_gaussian_orbit','yogurt_geometry_and_appearance','textile_geometry_and_appearance']
    tool=next(t for t in read('static-tools.json')['portable_tools'] if t['name']=='FFmpeg')
    assert sorted(p.stem for p in out.glob('*.mp4'))==sorted(names)
    reports=[]
    poses=read('outputs/dynamic_yogurt_001/rigid_tracking_06_measured/rigid_poses.json')['frames']
    valid={i for i,p in enumerate(poses) if p and p['valid']}
    actor=np.load('outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid/canonical_actor.npz')['means']
    boxes={}
    for i in valid:
        p=poses[i];world=actor@Rotation.from_rotvec(p['rvec']).as_matrix().T+np.array(p['translation_m'])
        lo=world.min(0)-.003;hi=world.max(0)+.003
        boxes[i]=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    for name in names:
        path=out/f'{name}.mp4';record=read(out/f'{name}.capture.json')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        assert path.stat().st_size==record['bytes']
        assert record['method']=='CDP Page.startScreencast actual browser PNG paint frames'
        assert (record['width'],record['height'],record['frame_rate'])==(1500,1000,'30/1')
        assert record['codec']=='h264' and record['pixel_format']=='yuv420p'
        assert abs(record['duration_error_s'])<=.06 and faststart(path)
        assert not record['audio'] and record['crf']==18
        subprocess.run([tool['executable_path'],'-hide_banner','-loglevel','error','-nostdin',
                        '-i',str(path),'-f','null','-'],check=True)
        phases=record['playback_state']['phases'];state=record['initial_state']
        if name=='yogurt_gaussian_orbit':
            assert state['viewer_kind']=='actual_gaussian_geometry'
            assert state['actor_gaussians']==51913 and state['background_gaussians']==498531
            assert 'gaussian_pilot_06_measured_solid' in state['source']
            assert 'static_background_03/trained_01' in state['background']
            assert not state['follow'] and not state['temporal_gaussian_color']
            assert [p['mode'] for p in phases]==['rgb','displacement','recent']
            base=state['orbit']['center_azimuth_deg']
            for phase in phases:
                samples=phase['source_samples']
                assert {s['index'] for s in samples}==valid
                for s in samples:assert abs(s['time_s']-poses[s['index']]['time_s'])<1e-5
                offsets=[s['azimuth_deg']-base for s in samples]
                assert abs(min(offsets)+45)<1e-6 and abs(max(offsets)-45)<1e-6
                assert abs(offsets[0])<1e-6 and abs(offsets[-1])<1e-6
                # Keep the moving actor visible throughout the recorded arc.
                el=math.radians(state['orbit']['elevation_deg']);distance=state['orbit']['distance_m']
                for s in samples:
                    az=math.radians(s['azimuth_deg'])
                    forward=np.array([-math.cos(el)*math.cos(az),-math.cos(el)*math.sin(az),math.sin(el)])
                    right=np.cross(forward,[0,0,-1]);right/=np.linalg.norm(right);down=np.cross(forward,right)
                    q=boxes[s['index']]-np.array([.175,.105,-.025]);depth=distance+q@forward
                    assert np.all(depth>.01)
                    x=450+900*(q@right)/depth;y=325+900*(q@down)/depth
                    assert np.all((x>15)&(x<885)&(y>15)&(y<635)), 'Actor cropped during orbit'
            scope='Actual yogurt Gaussian RGB and motion; all 53 supported poses in each camera arc'
            supported_samples=53
        else:
            dataset=state['dataset'];run='rigid_tracking_01' if dataset=='yogurt' else 'material_tracking_05_measured'
            tracks=read(f'outputs/dynamic_{dataset}_001/{run}/point_tracks.json')
            assert not state['synthetic'] and not state['gaussian_temporal_color']
            assert state['color_space']=='linear_rgb'
            assert [p['mode'] for p in phases]==['since_start','recent']
            expected=set(range(state['start_frame'],state['end_frame']+1))
            supported=set();nonempty=set()
            threshold=12 if dataset=='textile' else 1
            for phase in phases:
                assert {s['index'] for s in phase['source_samples']}==expected
                assert phase['point_map_orbit_arc_deg']==45
                for s in phase['source_samples']:
                    source=tracks['frames'][s['index']]
                    count=sum(p.get('position') is not None and p['status']=='tracked' for p in source['points'])
                    assert s['supported_positions']==count
                    assert abs(s['time_s']-source['time_s'])<1e-5
                    if count:nonempty.add(s['index'])
                    if count>=threshold:supported.add(s['index'])
            supported_samples=len(supported)
            assert supported_samples==(46 if dataset=='yogurt' else 28)
            scope=f'{dataset.title()} observed point maps; not a temporal Gaussian color reconstruction'
        reports.append({'filename':path.name,'duration_s':record['duration_s'],'bytes':record['bytes'],
                        'complete_decode':'passed','faststart':True,'source_samples':'matched',
                        'supported_samples':supported_samples,'scope':scope,
                        'representative_png_comparisons':record['representative_checks']})
    total=sum(r['bytes'] for r in reports)
    assert total<15*1024*1024
    result={'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),
            'clips':reports,'total_video_bytes':total,'total_video_mib':total/(1024*1024),
            'metric_accuracy_verified':False,'dense_textile_gaussian_replay':False,
            'temporal_gaussian_color_fitted':False,
            'compression':'1500 x 1000, H.264 CRF18, 30 fps; visually high quality, not mathematical losslessness',
            'visual_review':'Decoded beginning, middle and end reviewed; Gaussian RGB arc extremes also inspected',
            'actor_visibility':'Every displayed Gaussian actor bounding box stays inside the orbit render with margins',
            'validation_diagnosis':'Initial textile coverage assertion counted all nonempty frames; corrected to the recorded >=12-point criterion: 28 sufficiently populated frames, plus two sparse frames with 10 and 11 genuine points',
            'scope':'Recording integrity, sample provenance and readable playback; no independent physical accuracy certification'}
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
