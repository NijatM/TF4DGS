"""Conservative export cleanup; preserve every original fitted checkpoint.

The optional chroma rule is specific to this inspected neutral-gray textile,
and must not be used for paint/color-change or colored-material experiments.
"""
import argparse
import json
from pathlib import Path
from importlib.machinery import SourceFileLoader
import cv2
import numpy as np
from PIL import Image

stereo=SourceFileLoader('textile_stereo',str(Path(__file__).with_name('Dense-TextileStereo.py'))).load_module()


def main():
    p=argparse.ArgumentParser();p.add_argument('--sequence',default='outputs/dynamic_textile_001/gaussian_sequence_04/sequence.json')
    p.add_argument('--neutral-knit',action='store_true');p.add_argument('--output-name',default='clean_support_model.npz')
    p.add_argument('--opacity-only',action='store_true')
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    if Path(a.output_name).name!=a.output_name or not a.output_name.endswith('.npz'):raise ValueError('Export name must be a local NPZ filename')
    sequence=stereo.read(a.sequence);session=root/sequence['source_session'];masks=root/sequence['masks'];cams=stereo.cameras(session)
    summaries=[]
    for entry in sequence['frames']:
        source=root/entry['model'];out=source.with_name(a.output_name);summary=out.with_suffix('.cleanup.json')
        if out.exists():summaries.append(stereo.read(summary));continue
        data=np.load(source);means=data['means'];supports=np.zeros(len(means),int);observed=np.zeros(len(means),int)
        for cid,c in cams.items():
            xy=stereo.project(means,c)
            cloth=cv2.imread(str(masks/'masks'/cid/f"frame_{entry['index']:06d}.png"),0)
            occ=cv2.imread(str(masks/'occlusions'/cid/f"frame_{entry['index']:06d}.png"),0)
            cloth=cv2.dilate((cloth>90).astype(np.uint8),np.ones((9,9),np.uint8))
            if occ is None:occ=np.zeros_like(cloth)
            occ=cv2.dilate((occ>0).astype(np.uint8),np.ones((31,31),np.uint8))
            valid=(xy[:,0]>=0)&(xy[:,0]<cloth.shape[1])&(xy[:,1]>=0)&(xy[:,1]<cloth.shape[0])
            iscloth=valid&(stereo.sample(cloth,xy)>0);unknown=valid&(stereo.sample(occ,xy)>0)
            observed+=iscloth;supports+=iscloth|unknown
        valid=data['opacity']>.035
        if not a.opacity_only:valid&=(supports>=2)&(observed>=1)
        removed_low_opacity=int((data['opacity']<=.035).sum())
        chroma=(data['colors'].max(1)-data['colors'].min(1))/np.maximum(data['colors'].max(1),.05)
        removed_chroma=0
        if a.neutral_knit:
            bad=chroma>.48;removed_chroma=int((bad&valid).sum());valid&=~bad
        if valid.sum()<.85*len(means):
            # Large removals deserve review; export remains possible, explicitly flagged.
            status='review required: more than 15% removed'
        else:status='conservative cleanup exported; review renders'
        arrays={k:data[k][valid] for k in data.files};np.savez_compressed(out,**arrays)
        result=dict(index=entry['index'],input_gaussians=len(means),output_gaussians=int(valid.sum()),
                    removed_low_opacity=removed_low_opacity,removed_neutral_material_chroma=removed_chroma,
                    source=str(source.relative_to(root)).replace('\\','/'),output=str(out.relative_to(root)).replace('\\','/'),
                    status=status,neutral_material_prior=a.neutral_knit,
                    opacity_only=a.opacity_only,
                    limitations=('Opacity-only export; original fit retained.' if a.opacity_only else
                        'Automatic mask support and optional neutral-material chroma prior; original fit retained.'))
        summary.write_text(json.dumps(result,indent=2)+'\n');summaries.append(result)
    output=Path(a.sequence).parent/'cleanup_summary.json';output.write_text(json.dumps(summaries,indent=2)+'\n')
    print(json.dumps(dict(frames=len(summaries),removed=sum(r['input_gaussians']-r['output_gaussians'] for r in summaries),
                         review_required=sum('review required' in r['status'] for r in summaries))))


if __name__=='__main__':main()
