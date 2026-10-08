"""Resumable dense multiview RGB Gaussian sequence; no invented material IDs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from importlib.machinery import SourceFileLoader

ROOT=Path(__file__).resolve().parents[1]


def write_manifest(output,session,dense,masks,requested,status):
    bundles=json.loads((session.parent/'manifests/sync-plan.json').read_text())['bundles'];frames=[]
    for index in requested:
        path=output/'frames'/f'{index:06d}'
        if (path/'summary.json').exists():
            info=json.loads((path/'summary.json').read_text())
            frames.append(dict(index=index,time_s=bundles[index]['time_s'],model=str((path/'model.npz').relative_to(ROOT)).replace('\\','/'),
                               gaussians=info['gaussians'],metrics=info['metrics']))
    manifest=dict(status=status,representation='Multiview-fitted RGB Gaussian keyframe sequence',source_session=str(session.relative_to(ROOT)).replace('\\','/'),
        source_dense=str(dense.relative_to(ROOT)).replace('\\','/'),masks=str(masks.relative_to(ROOT)).replace('\\','/'),
        frames=frames,requested_indexes=requested,time_interpolation=False,persistent_material_ids=False,
        temporal_rgb_fitted=True,metric_accuracy_verified=False,
        table_model='outputs/dynamic_textile_001/current_table_04/table.npz',
        geometry_field='Distance to closest baseline surface sample; shape difference, not material displacement/strain',
        appearance_field='RGB difference at closest baseline surface; appearance contrast, not intrinsic pigment change',
        validation_note='Three-camera fitting residuals. Novel-view images are visual diagnostics, not independent validation.')
    temporary=output/'sequence.json.tmp';temporary.write_text(json.dumps(manifest,indent=2)+'\n')
    # Windows readers/antivirus may briefly deny replacement of an open file.
    # Retry the atomic publish; never remove the existing valid timeline.
    for attempt in range(40):
        try:
            temporary.replace(output/'sequence.json');break
        except PermissionError:
            if attempt==39:raise
            time.sleep(.15)
    return manifest


def main():
    p=argparse.ArgumentParser();p.add_argument('--session',default='data/dynamic_textile_001/session_measured_candidate.json')
    p.add_argument('--masks',default='outputs/dynamic_textile_001/segmentation_03_video');p.add_argument('--dense',default='outputs/dynamic_textile_001/dense_stereo_04_shape_prior')
    p.add_argument('--output',default='outputs/dynamic_textile_001/gaussian_sequence_04');p.add_argument('--stride',type=int,default=2)
    p.add_argument('--indexes',type=int,nargs='+');p.add_argument('--steps',type=int,default=6000);p.add_argument('--upsample',type=int,default=5)
    p.add_argument('--depth-prior',action='store_true',default=True);p.add_argument('--no-depth-prior',dest='depth_prior',action='store_false')
    p.add_argument('--offset-mm',type=float,default=8.)
    p.add_argument('--color-balance',default='outputs/dynamic_textile_001/color_balance_02/color_balance.json')
    p.add_argument('--stop-psnr',type=float,default=32.)
    p.add_argument('--patch-size',type=int,default=0)
    a=p.parse_args();session=(ROOT/a.session).resolve();masks=(ROOT/a.masks).resolve();dense=(ROOT/a.dense).resolve();output=(ROOT/a.output).resolve();output.mkdir(parents=True,exist_ok=True)
    count=len(json.loads((session.parent/'manifests/sync-plan.json').read_text())['bundles'])
    indexes=a.indexes or list(range(0,count,a.stride))
    if not a.indexes and indexes[-1]!=count-1:indexes.append(count-1)
    for i in indexes:
        if not (masks/'masks/iphone'/f'frame_{i:06d}.png').exists():raise ValueError(f'Missing mask for {i}; select prepared times')
    start=time.time();write_manifest(output,session,dense,masks,indexes,'training')
    trainer=SourceFileLoader('textile_frame_trainer',str(ROOT/'scripts/Train-TextileGaussianFrame.py')).load_module()
    stereo=trainer.stereo;matching_model=None
    try:
        for order,index in enumerate(indexes):
            frame=output/'frames'/f'{index:06d}'
            if (frame/'summary.json').exists():continue
            if not (dense/f'frame_{index:06d}.npz').exists():
                command=[str(ROOT/'scripts/Dense-TextileStereo.py'),'--session',str(session),'--masks',str(masks),
                    '--output',str(dense),'--indexes',str(index)]
                if a.depth_prior:command.append('--depth-prior')
                if matching_model is None:matching_model=stereo.load_model()
                previous_argv=sys.argv
                try:
                    sys.argv=command;stereo.main(model=matching_model)
                finally:sys.argv=previous_argv
            command=[sys.executable,'-u',str(ROOT/'scripts/Train-TextileGaussianFrame.py'),'--session',str(session),
                    '--masks',str(masks),'--dense',str(dense),'--output',str(frame),'--index',str(index),'--steps',str(a.steps),'--upsample',str(a.upsample),'--offset-mm',str(a.offset_mm),'--stop-psnr',str(a.stop_psnr)]
            if a.color_balance:command.extend(['--color-balance',a.color_balance])
            if a.patch_size:command.extend(['--patch-size',str(a.patch_size)])
            previous_argv=sys.argv
            try:
                sys.argv=command[2:]
                trainer.main()
            finally:
                sys.argv=previous_argv
            manifest=write_manifest(output,session,dense,masks,indexes,'training')
            print(json.dumps(dict(completed=len(manifest['frames']),requested=len(indexes),index=index,elapsed_s=time.time()-start)),flush=True)
        manifest=write_manifest(output,session,dense,masks,indexes,'complete')
        print(json.dumps(dict(status='complete',frames=len(manifest['frames']),elapsed_s=time.time()-start)),flush=True)
    except Exception as e:
        write_manifest(output,session,dense,masks,indexes,'interrupted or failed; partial frames preserved')
        (output/'failure.json').write_text(json.dumps(dict(error=repr(e),elapsed_s=time.time()-start),indent=2)+'\n');raise


if __name__=='__main__':main()
