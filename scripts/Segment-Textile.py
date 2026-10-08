"""SAM2 textile masks; preserve source images and retain diagnostics.

Prompts below are specific to the inspected dynamic_textile_001 first frame.
Masks are appearance segmentation, not certified material correspondence.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.local/tools/sam2'))
from sam2.build_sam import build_sam2, build_sam2_video_predictor
from sam2.sam2_image_predictor import SAM2ImagePredictor

BOXES = {'dji':[0,870,1535,1730], 'fuji':[390,380,3100,1420],
         'iphone':[1500,915,2765,1810]}
POINTS = {'dji':[[400,1170],[1000,1300],[740,1490]],
          'fuji':[[1000,720],[1800,850],[2550,1110]],
          'iphone':[[1990,1320],[2230,1540],[1700,1650]]}


def skin_mask(image):
    """Conservative colored-skin exclusion; ambiguous pixels remain unclassified."""
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    ycc = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
    skin = ((hsv[:,:,0]<28) & (hsv[:,:,1]>48) & (ycc[:,:,1]>137) &
            (ycc[:,:,2]<129) & (image[:,:,0]>image[:,:,2]+12))
    skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
    return skin.astype(bool)


def diagnostic(root, output, indexes):
    canvas=Image.new('RGB',(1500,len(indexes)*330),'#171d26')
    draw=ImageDraw.Draw(canvas)
    for row,index in enumerate(indexes):
        for col,cid in enumerate(BOXES):
            mask_path=output/'masks'/cid/f'frame_{index:06d}.png'
            if not mask_path.exists(): continue
            image=np.asarray(Image.open(root/'frames'/cid/f'frame_{index:06d}.png').convert('RGB')).copy()
            mask=np.asarray(Image.open(mask_path))>127
            y,x=np.where(mask)
            if len(x)==0:continue
            x0,x1=max(0,x.min()-80),min(image.shape[1],x.max()+81)
            y0,y1=max(0,y.min()-80),min(image.shape[0],y.max()+81)
            image[mask]=(image[mask]*.7+np.array([10,100,20])*.3).astype(np.uint8)
            im=Image.fromarray(image[y0:y1,x0:x1]);im.thumbnail((480,295))
            canvas.paste(im,(col*500,row*330+30))
            draw.text((col*500+10,row*330+8),f'{cid} | index {index} | green: cloth mask',fill='white')
    canvas.save(output/'mask_diagnostic.jpg',quality=94)


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--output',default='outputs/dynamic_textile_001/segmentation_02')
    p.add_argument('--first-only',action='store_true');p.add_argument('--stride',type=int,default=2)
    p.add_argument('--camera',choices=list(BOXES));args=p.parse_args()
    root=Path(args.session).resolve().parent;out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    bundles=json.loads((root/'manifests/sync-plan.json').read_text())['bundles']
    indexes=list(range(0,len(bundles),args.stride))
    if indexes[-1]!=len(bundles)-1:indexes.append(len(bundles)-1)
    source=ROOT/'.local/tools/sam2/checkpoints/sam2_hiera_tiny.pt'
    started=time.time();counts=[]
    cameras=[args.camera] if args.camera else list(BOXES)
    if args.first_only:
        predictor=SAM2ImagePredictor(build_sam2('sam2_hiera_t.yaml',str(source),apply_postprocessing=False))
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
            for cid in cameras:
                image=np.asarray(Image.open(root/bundles[0]['views'][cid]['image']).convert('RGB'))
                predictor.set_image(image)
                masks,scores,logits=predictor.predict(point_coords=np.array(POINTS[cid]),point_labels=np.ones(3),
                                                     box=np.array(BOXES[cid]),multimask_output=True)
                mask=masks[np.argmax(scores)]
                target=out/'masks'/cid;target.mkdir(parents=True,exist_ok=True)
                Image.fromarray(mask.astype(np.uint8)*255).save(target/'frame_000000.png')
                counts.append({'camera':cid,'index':0,'pixels':int(mask.sum()),'sam_score':float(max(scores))})
        indexes=[0]
    else:
        predictor=build_sam2_video_predictor('sam2_hiera_t.yaml',str(source),apply_postprocessing=False)
        for cid in cameras:
            cache=ROOT/'.local/workflows/dynamic_setup/textile_reconstruction_02/sam_jpeg'/cid
            cache.mkdir(parents=True,exist_ok=True)
            target=out/'masks'/cid;target.mkdir(parents=True,exist_ok=True)
            scale=None
            for order,index in enumerate(indexes):
                image=Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB')
                native_size=image.size;scale=min(1.,1280/max(image.size))
                path=cache/f'{order:06d}.jpg'
                if not path.exists():
                    image.resize((round(image.width*scale),round(image.height*scale))).save(path,quality=95)
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
                state=predictor.init_state(str(cache),offload_video_to_cpu=True,offload_state_to_cpu=True)
                predictor.add_new_points_or_box(state,0,1,points=np.array(POINTS[cid])*scale,
                                                labels=np.ones(3),box=np.array(BOXES[cid])*scale)
                for frame,ids,logits in predictor.propagate_in_video(state):
                    index=indexes[frame]
                    probability=torch.sigmoid(logits[0,0].float()).cpu().numpy()
                    mask=cv2.resize(probability,native_size,interpolation=cv2.INTER_LINEAR)
                    image=np.asarray(Image.open(root/bundles[index]['views'][cid]['image']).convert('RGB'))
                    skin=skin_mask(image)
                    mask[skin]=0
                    Image.fromarray(np.round(mask*255).astype(np.uint8)).save(target/f'frame_{index:06d}.png')
                    skin_out=out/'occlusions'/cid;skin_out.mkdir(parents=True,exist_ok=True)
                    Image.fromarray(skin.astype(np.uint8)*255).save(skin_out/f'frame_{index:06d}.png')
                    counts.append({'camera':cid,'index':index,'pixels':int((mask>.5).sum())})
                    if frame%20==0:print(f'{cid}: {frame+1}/{len(indexes)} masks; {time.time()-started:.1f}s',flush=True)
            del state;torch.cuda.empty_cache()
    diagnostic(root,out,[i for i in [0,52,106,158,212,266,318,372,425] if i in indexes])
    (out/'summary.json').write_text(json.dumps({'model':'SAM2.0 tiny, pinned official weights',
       'frames':indexes,'counts':counts,'elapsed_s':time.time()-started,
       'source_session':str(Path(args.session)),'skin_exclusion':'Conservative YCrCb/HSV colored-skin mask',
       'limitation':'Automatic segmentation requires visual review; mask membership does not prove material identity.'},indent=2)+'\n')


if __name__=='__main__':main()
