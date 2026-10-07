"""Prepare real baseline views and explicit provisional intrinsics for COLMAP.

One planar board view does not independently calibrate unrestricted intrinsics.
Centered square-pixel estimates only initialize SfM; the cropped DJI view needs
multi-view refinement. Outputs are kept inside the ignored capture session.
"""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session',type=Path)
    parser.add_argument('--frame',type=int,default=360)
    args=parser.parse_args()
    session=json.loads(args.session.read_text(encoding='utf-8-sig'))
    root=args.session.parent
    out=root/'calibration/sfm'
    if out.exists():
        raise ValueError('Calibration preparation already exists; preserve it before rerunning')
    out.mkdir(parents=True)
    tools=json.loads(Path('static-tools.json').read_text(encoding='utf-8-sig'))
    ffmpeg=next(x['executable_path'] for x in tools['portable_tools'] if x['name']=='FFmpeg')
    results=[]
    # Order deliberately makes the two uncropped views the initial pair.
    for cid in ['fuji','iphone','dji']:
        camera=next(x for x in session['cameras'] if x['id']==cid)
        audit=json.loads((root/'calibration/marker_audit'/f'{cid}.json').read_text(encoding='utf-8'))
        H=np.asarray(audit['reference']['homography_board_m_to_native_px'])
        width,height=audit['image_size'];center=np.array([width/2,height/2])
        a=H[:2,0]-center*H[2,0];b=H[:2,1]-center*H[2,1]
        estimates=[]
        for numerator,denominator in [(-a@b,H[2,0]*H[2,1]),(-(a@a-b@b),H[2,0]**2-H[2,1]**2)]:
            if abs(denominator)>1e-8 and numerator/denominator>0:
                estimates.append(float(np.sqrt(numerator/denominator)))
        agrees=len(estimates)==2 and max(estimates)/min(estimates)<1.05
        focal=float(np.mean(estimates)) if agrees else 1.2*max(width,height)
        folder=out/'images'/cid;folder.mkdir(parents=True)
        destination=folder/f'baseline_{args.frame:06d}.png'
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-nostdin','-n','-noautorotate',
                        '-i',str(root/camera['video']),'-vf',f'select=eq(n\\,{args.frame})',
                        '-frames:v','1','-pix_fmt','rgb24',str(destination)],check=True)
        entry={'camera_id':cid,'image':str(destination.relative_to(out)).replace('\\','/'),
               'model':'PINHOLE','params':[focal,focal,width/2,height/2],'image_size':[width,height],
               'board_focal_diagnostics_px':estimates,'centered_assumption_consistent':agrees,
               'calibration_verified':False,'initialization_only':True}
        results.append(entry)
        (out/f'{cid}.image-list.txt').write_text(f'{cid}/{destination.name}\n',encoding='utf-8')
        print(json.dumps(entry),flush=True)
    (out/'intrinsic_initialization.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    (out/'fixed_uncropped_cameras.txt').write_text('1\n2\n',encoding='utf-8')
    (out/'sparse').mkdir()


if __name__=='__main__':
    main()
