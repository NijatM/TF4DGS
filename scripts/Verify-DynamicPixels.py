"""Compare extracted real-video PNG pixels to an independent native decode."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tf4dgs.media import executable


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--ffmpeg')
    p.add_argument('sessions',nargs='+',type=Path);args=p.parse_args()
    if args.output.exists():raise ValueError('Preserve previous verification results')
    results=[]
    for path in args.sessions:
        root=path.parent;session=json.loads(path.read_text(encoding='utf-8-sig'))
        bundles=json.loads((root/'manifests/sync-plan.json').read_text())['bundles'];bundle=bundles[len(bundles)//2]
        for camera in session['cameras']:
            cid=camera['id'];view=bundle['views'][cid]
            command=[executable('ffmpeg',args.ffmpeg),'-v','error','-threads','2','-noautorotate','-i',str(root/camera['video']),
                     '-vf',f"select='eq(n,{view['source_index']})'",'-frames:v','1','-pix_fmt','rgb24','-f','rawvideo','pipe:1']
            raw=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
            with Image.open(root/view['image']) as image:
                size=image.size;pixels=image.convert('RGB').tobytes()
            if raw!=pixels:raise ValueError(f"{session['session_id']}/{cid}: native RGB pixels differ from independent decode")
            record={'session':session['session_id'],'camera':cid,'source_index':view['source_index'],
                    'extracted_image':view['image'],'size':list(size),'rgb_sha256':hashlib.sha256(raw).hexdigest(),'equal':True}
            results.append(record);print(json.dumps(record),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'status':'passed','checks':results,'scope':'One middle frame per real stream; extractor separately checks all frame counts/dimensions.'},indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
