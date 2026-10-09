"""Extract pinned native-rate action clips and shared calibrated benchmark inputs."""
import argparse, hashlib, itertools, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / 'configs/temporal_benchmark_001.json'

def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''): h.update(block)
    return h.hexdigest()

def project(points, cal):
    R = np.array(cal['world_to_camera']['R']); t = np.array(cal['world_to_camera']['t'])
    q = points @ R.T + t
    fx, fy, cx, cy = cal['params']
    return q[:, :2] / q[:, 2:] * [fx, fy] + [cx, cy]

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--ffmpeg', required=True)
    parser.add_argument('--datasets',nargs='+',choices=['yogurt','textile'],default=['yogurt','textile'])
    args = parser.parse_args(); cfg = json.loads(CFG.read_text())
    root = ROOT / 'data/temporal_benchmark_001'; root.mkdir(parents=True, exist_ok=True)
    docs = ROOT / 'documentation/temporal_benchmark_001'; docs.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(cfg['seed']); summaries = {}
    for label, spec in cfg['datasets'].items():
        if label not in args.datasets:continue
        rng=np.random.default_rng(cfg['seed'])
        session_path = ROOT / spec['session']; session = json.loads(session_path.read_text()); parent = session_path.parent
        dest = root / label; dest.mkdir(exist_ok=True)
        lo = np.array(cfg['world_roi_m']['min']); hi = np.array(cfg['world_roi_m']['max'])
        corners = np.array(list(itertools.product(*zip(lo, hi))))
        cameras = {}; camera_records = {}
        for cam in session['cameras']:
            cid = cam['id']; cal_path = parent / cam['calibration']; cal = json.loads(cal_path.read_text())
            video = parent / cam['video']; w, h = cal['image_size']
            # One fixed crop for the complete interval; no tracking/recentering.
            crop = cfg['fixed_crop_fractions'][cid]
            x0,y0,x1,y1 = (int(round(v*s/2))*2 for v,s in zip(crop,[w,h,w,h]))
            factor = min(1., cfg['max_image_edge'] / max(x1-x0, y1-y0))
            nw, nh = int(round((x1-x0)*factor/2))*2, int(round((y1-y0)*factor/2))*2
            sx, sy = nw/(x1-x0), nh/(y1-y0)
            out = dest / 'images' / cid; out.mkdir(parents=True, exist_ok=True)
            filt = f"select=between(n\\,{spec['source_start_frame']}\\,{spec['source_end_frame_exclusive']-1}),crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={nw}:{nh}:flags=lanczos"
            command = [args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-noautorotate', '-i', str(video), '-vf', filt, '-fps_mode', 'passthrough', '-frames:v', str(cfg['frame_count']), '-start_number', '0', str(out/'%06d.png')]
            subprocess.run(command, check=True)
            assert len(list(out.glob('*.png'))) == cfg['frame_count']
            fx, fy, cx, cy = cal['params']; R = np.array(cal['world_to_camera']['R']); t = np.array(cal['world_to_camera']['t'])
            center = np.array(cfg['normalization']['center_m']); scale = cfg['normalization']['scale_per_m']
            cameras[cid] = {'width': nw, 'height': nh, 'fx': fx*sx, 'fy': fy*sy, 'cx': (cx-x0+.5)*sx-.5, 'cy': (cy-y0+.5)*sy-.5, 'R': R.tolist(), 't': ((t+R@center)*scale).tolist(), 'crop_xyxy': [int(x0),int(y0),int(x1),int(y1)], 'source_image_size': [w,h]}
            camera_records[cid] = {'video': str(video.relative_to(ROOT)), 'video_sha256': digest(video), 'calibration': str(cal_path.relative_to(ROOT)), 'calibration_sha256': digest(cal_path), 'extraction_command': command, 'images': [{'local_index': i, 'source_index': spec['source_start_frame']+i, 'pts_s': (spec['source_start_frame']+i)*1001/30000, 'file': f'images/{cid}/{i:06d}.png', 'sha256': digest(out/f'{i:06d}.png')} for i in range(cfg['frame_count'])]}
            print(label,cid,'ROI',cameras[cid]['crop_xyxy'],'size',nw,nh,flush=True)
            if label=='textile':
                import cv2
                bundles=json.loads((parent/'manifests/sync-plan.json').read_text())['bundles'];times=np.array([b['time_s'] for b in bundles])
                for kind in ['masks','occlusions']:
                    out_masks=dest/kind/cid;out_masks.mkdir(parents=True,exist_ok=True)
                    source_masks=ROOT/f'outputs/dynamic_textile_001/segmentation_03_video/{kind}/{cid}'
                    available=np.array(sorted(int(p.stem.split('_')[-1]) for p in source_masks.glob('frame_*.png')))
                    if not len(available):raise ValueError(f'No source masks: {source_masks}')
                    cache={};max_dt=0.
                    small_w=min(512,nw);small_h=round(nh*small_w/nw)
                    for i in range(cfg['frame_count']):
                        pts=(spec['source_start_frame']+i)*1001/30000;nearest=int(available[np.argmin(abs(times[available]-pts))]);max_dt=max(max_dt,abs(times[nearest]-pts))
                        if nearest not in cache:
                            mask=np.array(Image.open(source_masks/f'frame_{nearest:06d}.png').convert('L').crop((x0,y0,x1,y1)).resize((small_w,small_h),Image.Resampling.NEAREST))
                            reference=np.array(Image.open(parent/bundles[nearest]['views'][cid]['image']).convert('RGB').crop((x0,y0,x1,y1)).resize((small_w,small_h),Image.Resampling.BILINEAR))
                            cache[nearest]=(mask,cv2.cvtColor(reference,cv2.COLOR_RGB2GRAY))
                        mask,reference=cache[nearest]
                        current=np.array(Image.open(out/f'{i:06d}.png').convert('RGB').resize((small_w,small_h),Image.Resampling.BILINEAR))
                        gray=cv2.cvtColor(current,cv2.COLOR_RGB2GRAY)
                        flow=cv2.calcOpticalFlowFarneback(gray,reference,None,.5,3,21,4,5,1.2,0)
                        yy,xx=np.indices(gray.shape,dtype=np.float32)
                        warped=cv2.remap(mask,xx+flow[:,:,0],yy+flow[:,:,1],cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
                        image=Image.fromarray(warped).resize((nw,nh),Image.Resampling.NEAREST)
                        image.save(out_masks/f'{i:06d}.png')
                    camera_records[cid][kind+'_max_source_delta_s']=max_dt
                camera_records[cid]['mask_source']='outputs/dynamic_textile_001/segmentation_03_video'
                camera_records[cid]['mask_sampling']='Nearest available 5 Hz RGB mask transported by 2D Farneback flow to each native frame. This is an inferred image mask, not 3D geometry or verified material correspondence.'
        if label == 'textile':
            actor_path = ROOT / cfg['initialization']['textile_source']
            actor = np.load(actor_path); xyz, rgb = actor['points'], actor['colors']
            cloth_path=ROOT/'outputs/dynamic_textile_001/dense_stereo_04_shape_prior/frame_000196.npz'
            cloth=np.load(cloth_path)
            xyz=np.concatenate([cloth['points'],xyz]);rgb=np.concatenate([cloth['colors'],rgb])
            # Reject registered-prior points outside the measured action volume.
            valid=np.isfinite(xyz).all(1)&np.all((xyz>=lo)&(xyz<=hi),axis=1)
            xyz,rgb=xyz[valid],rgb[valid]
        else:
            actor_path = ROOT / 'outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid/canonical_actor.npz'
            actor = np.load(actor_path); xyz, rgb = actor['means'], actor['colors']
            import cv2
            poses = json.loads((ROOT/'outputs/dynamic_yogurt_001/rigid_tracking_06_measured/rigid_poses.json').read_text())
            pose = poses['frames'][spec['source_10hz_first_index']]
            R = cv2.Rodrigues(np.array(pose['rvec']))[0]; xyz = xyz@R.T+np.array(pose['translation_m'])
        idx = rng.choice(len(xyz), min(len(xyz),cfg['initialization']['max_actor_points']), replace=False)
        xyz, rgb = xyz[idx], rgb[idx]
        table = np.load(ROOT/'outputs/dynamic_textile_001/current_table_05/table.npz')
        valid = np.all((table['means']>=lo)&(table['means']<=hi),axis=1)
        idx = np.flatnonzero(valid); idx = rng.choice(idx,min(len(idx),cfg['initialization']['max_table_points']),replace=False)
        xyz = np.concatenate([xyz,table['means'][idx]]); rgb = np.concatenate([rgb,table['colors'][idx]])
        normalized = (xyz-np.array(cfg['normalization']['center_m']))*cfg['normalization']['scale_per_m']
        np.savez_compressed(dest/'initial_points.npz',points=normalized.astype('float32'),colors=rgb.astype('float32'))
        frames = [{'index': i, 'source_index': spec['source_start_frame']+i, 'pts_s': (spec['source_start_frame']+i)*1001/30000, 'time': i/(cfg['frame_count']-1), 'split': 'test' if i%6==5 else 'train'} for i in range(cfg['frame_count'])]
        manifest = {'benchmark_id':cfg['benchmark_id'],'dataset':label,'config_sha256':digest(CFG),'cameras':cameras,'frames':frames,'provenance':camera_records,'initial_points_sha256':digest(dest/'initial_points.npz'),'initial_actor_source':str(actor_path.relative_to(ROOT)),'initial_actor_sha256':digest(actor_path),'initial_point_count':len(xyz),'normalization':cfg['normalization']}
        (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        summaries[label] = {k:v for k,v in manifest.items() if k!='provenance'}
        # Diagnostic contact sheet preserves the actual selected cropped inputs.
        sheet = Image.new('RGB',(1200,3*255+75),(22,26,33)); d=ImageDraw.Draw(sheet)
        d.text((20,10),f'{label}: source frames {spec["source_start_frame"]}–{spec["source_end_frame_exclusive"]-1}; native 30000/1001 fps',fill='white')
        for row,cid in enumerate(cameras):
            for col,i in enumerate([0,30,60,89]):
                im=Image.open(dest/'images'/cid/f'{i:06d}.png'); im.thumbnail((290,220))
                sheet.paste(im,(col*300+(300-im.width)//2,row*255+50))
                d.text((col*300+10,row*255+275),f'{cid}  {frames[i]["pts_s"]:.3f}s',fill='white')
        sheet.save(docs/f'{label}_selected_inputs.jpg',quality=94,subsampling=0)
    summary_path=docs/'input_summary.json'
    previous=json.loads(summary_path.read_text()) if summary_path.exists() else {}
    summary_path.write_text(json.dumps({**previous,**summaries},indent=2)+'\n')
    print('Pinned preparation complete',flush=True)

if __name__=='__main__': main()
