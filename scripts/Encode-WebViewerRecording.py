"""Compress a real browser screencast, retaining paint timestamps and provenance.

PNG capture intermediates remain ignored. H.264 CRF18 is visually high quality,
not mathematical losslessness. Browser playback is recorded at wall-clock speed;
the visible viewer clock is the source timeline. Model gaps are not interpolated.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image,ImageDraw,ImageOps


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--crf',type=int,default=18);args=p.parse_args()
    if not 12<=args.crf<=23:raise ValueError('Invalid quality setting')
    if args.output.exists():raise ValueError('Preserve earlier encodings; choose a new name')
    root=Path('.').resolve();cache=(root/'.local/workflows/dynamic_setup').resolve();docs=(root/'documentation').resolve()
    args.capture.resolve().relative_to(cache);args.output.resolve().relative_to(docs)
    record=read(args.capture);frames=record['frames'];folder=args.capture.parent
    if len(frames)<10:raise ValueError('Insufficient real browser capture frames')
    arrival_times=np.array([f['timestamp_s'] for f in frames],float)
    if not np.isfinite(arrival_times).all():raise ValueError('Invalid browser paint times')
    # PNG events can arrive a few milliseconds out of order. Use the actual
    # paint timestamps, preserving every frame and the untouched raw record.
    reverse=np.diff(arrival_times)
    if reverse.min(initial=0)<-.1:raise ValueError('Large paint-time reversal needs inspection')
    ordering={'negative_adjacent_pairs':int(np.sum(reverse<0)),
              'largest_reversal_s':float(max(0,-reverse.min(initial=0))),
              'presentation_order':'Stable sort by browser paint timestamp; no frames removed'}
    frames=[frames[i] for i in np.argsort(arrival_times,kind='stable')]
    names=[f['filename'] for f in frames];times=np.array([f['timestamp_s'] for f in frames],float)
    for name in names:
        path=(folder/name).resolve();path.relative_to(folder.resolve())
        with Image.open(path) as im:
            if im.size!=(record['width'],record['height']):raise ValueError('Screencast frame dimensions changed')
    durations=np.maximum(np.diff(times),.001);last=.8
    expected_duration=float(times[-1]-times[0]+last)
    concat=folder/'frames.ffconcat'
    # Generated simple frame names, with no source/user paths in concat syntax.
    if any(re.fullmatch(r'frame_\d{6}\.png',n) is None for n in names):raise ValueError('Invalid capture filename')
    lines=['ffconcat version 1.0']
    # Millisecond input time base prevents PNG's default 25 Hz demuxer from
    # accumulating timing error across sub-40 ms browser paint events.
    for name,dt in zip(names,[*durations,last]):lines.extend([f"file '{name}'",'option framerate 1000',f'duration {dt:.9f}'])
    lines.extend([f"file '{names[-1]}'",'option framerate 1000']);concat.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    tool=next(t for t in read('static-tools.json')['portable_tools'] if t['name']=='FFmpeg')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    candidate=folder/'encoded_candidate.mp4'
    # safe=0 permits our generated framerate directive; all relative input
    # filenames are strictly validated above and remain inside this cache.
    command=[tool['executable_path'],'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),
      '-vf','fps=30','-t',f'{expected_duration:.9f}','-an','-c:v','libx264','-preset','slow','-tune','animation','-crf',str(args.crf),'-pix_fmt','yuv420p',
      '-movflags','+faststart','-metadata','comment=Actual TF4DGS browser capture; provisional geometry and observed appearance',str(candidate)]
    with (folder/'encode.log').open('w',encoding='utf-8') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
    probe=json.loads(subprocess.check_output([tool['ffprobe_path'],'-v','error','-show_streams','-show_format','-of','json',str(candidate)],text=True))
    video=next(s for s in probe['streams'] if s['codec_type']=='video');duration=float(probe['format']['duration'])
    if video['codec_name']!='h264' or video['pix_fmt']!='yuv420p' or abs(duration-expected_duration)>.06:
        raise ValueError(f'Encoded properties differ: {video["codec_name"]}/{video["pix_fmt"]}; duration {duration}, expected {expected_duration}')
    # Decode representative actual video frames to check legibility/quality.
    picks=[0,len(frames)//2,len(frames)-1];panel=Image.new('RGB',(1500,420),'#17212b');draw=ImageDraw.Draw(panel);quality=[]
    for col,i in enumerate(picks):
        seek=max(0,min(duration-.05,times[i]-times[0]+.025))
        decoded=folder/f'encoded_check_{i:06d}.png'
        subprocess.run([tool['executable_path'],'-hide_banner','-loglevel','error','-nostdin','-y','-ss',str(seek),'-i',str(candidate),'-frames:v','1',str(decoded)],check=True)
        with Image.open(decoded) as im:
            rgb=np.array(im.convert('RGB')).astype(float);thumb=ImageOps.contain(im.convert('RGB'),(490,350));panel.paste(thumb,(col*500+(500-thumb.width)//2,35))
        with Image.open(folder/names[i]) as im:source=np.array(im.convert('RGB')).astype(float)
        mse=float(np.mean((rgb-source)**2));psnr=99. if mse==0 else float(10*np.log10(255**2/mse))
        quality.append({'capture_frame':i,'video_time_s':seek,'rgb_psnr_db':psnr,'comparison_scope':'Representative decoded video frame vs actual PNG; timing can select an adjacent paint frame'})
        draw.text((col*500+8,8),f'{args.output.stem} | video {seek:.2f} s',fill='white')
    panel.save(folder/'encoded_review.jpg',quality=94)
    poster=args.output.with_suffix('.jpg')
    subprocess.run([tool['executable_path'],'-hide_banner','-loglevel','error','-nostdin','-n','-ss',str(min(5,duration*.5)),'-i',str(candidate),'-frames:v','1','-q:v','2',str(poster)],check=True)
    candidate.rename(args.output)
    manifest={'filename':args.output.name,'poster':poster.name,'method':record['method'],'viewer_url':record['url'],
      'codec':video['codec_name'],'pixel_format':video['pix_fmt'],'width':video['width'],'height':video['height'],
      'frame_rate':video['avg_frame_rate'],'duration_s':duration,'bytes':args.output.stat().st_size,
      'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'capture_frames':len(frames),
      'capture_start_timestamp_s':float(times[0]),'capture_end_timestamp_s':float(times[-1]),
      'expected_duration_s':expected_duration,'duration_error_s':duration-expected_duration,
      'encoder':'libx264','preset':'slow','crf':args.crf,'faststart':True,'audio':False,
      'paint_event_ordering':ordering,
      'quality':'Visually high quality H.264; not mathematical losslessness','representative_checks':quality,
      'initial_state':record['initial_state'],'playback_state':record['playback_state'],
      'timing':'Actual browser wall-clock playback. Source time remains visible; missing model samples are not interpolated.'}
    args.output.with_suffix('.capture.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ['filename','duration_s','bytes','width','height','capture_frames','quality']},indent=2))


if __name__=='__main__':main()
