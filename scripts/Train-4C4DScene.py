"""Joint whole-scene 4C4D training with controlled branches and resolution stages.

Uses the pinned official model, opacity-decay network and CUDA renderer.
Every camera pixel and every primitive remains trainable, including surroundings.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import random
import subprocess
import sys
import time
from collections import OrderedDict
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image, ImageDraw
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'documentation/4c4d_scene_001'
sys.path.insert(0, str(ROOT / '.local/research/4C4D'))
from arguments import OptimizationParams, PipelineParams
from scene.gaussian_model import GaussianModel
from gaussian_renderer import render
from module import Coefficient
from utils.loss_utils import ssim
from utils.general_utils import build_rotation_4d

spec = importlib.util.spec_from_file_location('pilot_shared', ROOT / 'scripts/Train-TemporalBenchmark.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def smaller(image, edge):
    height, width = image.shape[-2:]
    if max(width, height) <= edge:
        return image
    factor = edge / max(width, height)
    return F.interpolate(image[None], size=(round(height * factor), round(width * factor)), mode='area')[0]


def dump(path, value):
    shared.dump(path, value)


def image(path):
    return np.array(Image.open(path).convert('RGB'))


class Pixels:
    """Bounded CPU cache keeps native 4K training from retaining all frames."""
    def __init__(self, data, capacity, byte_limit=5120 * 2 ** 20):
        self.data, self.capacity, self.cache = data, capacity, OrderedDict()
        self.byte_limit, self.bytes = byte_limit, 0

    def get(self, cid, index):
        key = cid, index
        if key not in self.cache:
            self.cache[key] = image(self.data / 'images' / cid / f'{index:06d}.png')
            self.bytes += self.cache[key].nbytes
            while len(self.cache) > self.capacity or self.bytes > self.byte_limit and len(self.cache) > 1:
                _, removed = self.cache.popitem(last=False)
                self.bytes -= removed.nbytes
        self.cache.move_to_end(key)
        return self.cache[key]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', choices=['yogurt', 'textile'], required=True)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--edge', type=int, default=1280)
    parser.add_argument('--preset', choices=['baseline', 'slow_motion', 'gentle_decay', 'fast_time'], default='baseline')
    parser.add_argument('--stop', type=int, default=30000)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--parent')
    parser.add_argument('--refine', action='store_true')
    parser.add_argument('--fit-all', action='store_true')
    parser.add_argument('--render-only', action='store_true')
    parser.add_argument('--config', default='configs/4c4d_scene_001.json')
    parser.add_argument('--variant', default='control')
    parser.add_argument('--quick-eval', action='store_true')
    args = parser.parse_args()
    if args.fit_all and not args.refine:
        raise ValueError('Production fit must refine an existing whole-scene model')
    cfg_path = ROOT / args.config
    cfg = read(cfg_path)
    experiment = cfg['experiment_id']
    global DOCS
    DOCS = ROOT / 'documentation' / experiment
    DOCS.mkdir(parents=True, exist_ok=True)
    variant = cfg.get('variants', {}).get(args.variant, {})
    data_experiment = cfg.get('data_experiment_id', experiment)
    data = ROOT / 'data' / data_experiment / args.dataset / f'edge_{args.edge}'
    manifest = read(data / 'manifest.json')
    output = ROOT / 'outputs' / experiment / args.dataset / args.attempt
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / 'checkpoint.pth'
    tag = f'{args.dataset}_{args.attempt}'
    if checkpoint.exists() and not (args.resume or args.render_only):
        raise ValueError('Completed/interrupted attempt exists; resume it or choose a new name')
    opt_parser = argparse.ArgumentParser()
    opt_group, pipe_group = OptimizationParams(opt_parser), PipelineParams(opt_parser)
    parsed = opt_parser.parse_args([])
    opt, pipe = opt_group.extract(parsed), pipe_group.extract(parsed)
    opt.iterations = cfg['refinement']['updates_per_stage'] if args.refine else cfg['training']['total_updates']
    if args.fit_all:
        opt.iterations = cfg['production']['updates']
    opt.position_lr_max_steps = opt.iterations
    if args.refine:
        for name in ['position_lr_init', 'position_lr_final', 'feature_lr', 'opacity_lr', 'scaling_lr', 'rotation_lr']:
            setattr(opt, name, cfg['refinement'][name])
    preset = cfg['tuning']['presets'][args.preset]
    opt.position_t_lr_init = opt.position_lr_init * preset['time_lr_factor']
    reference_span = cfg['training'].get('time_lr_reference_span_s')
    if reference_span:
        opt.position_t_lr_init *= reference_span / (manifest['frames'][-1]['pts_s'] - manifest['frames'][0]['pts_s'])
    opt.rotation_lr *= preset['rotation_lr_factor']
    max_points = cfg['refinement']['max_points'] if args.refine else cfg['training']['max_points']
    max_points = variant.get('max_points', max_points)
    milestones = cfg['refinement']['checkpoints'] if args.refine else cfg['training']['checkpoints']
    if args.fit_all:
        milestones = cfg['production']['checkpoints']
    densify_until = cfg['refinement']['densify_until'] if args.refine else cfg['training']['densify_until']
    if args.fit_all:
        densify_until = cfg['production']['densify_until']
    interval = cfg['refinement']['densify_interval'] if args.refine else cfg['training']['densify_interval']
    torch.manual_seed(cfg['seed']);np.random.seed(cfg['seed']);random.seed(cfg['seed'])
    coefficient = Coefficient().cuda()
    model = GaussianModel(3, gaussian_dim=4, time_duration=[0., 1.], rot_4d=True, force_sh_3d=False, sh_degree_t=2, coefficient=coefficient)
    initial_path = ROOT / cfg.get('initialization_paths', {}).get(args.dataset,
                 f'outputs/{experiment}/{args.dataset}/initialization/initial_points.npz')
    initial = np.load(initial_path)
    cameras = {cid: shared.camera(cal, 0) for cid, cal in manifest['cameras'].items()}
    centers = np.stack([cam.camera_center.cpu().numpy() for cam in cameras.values()])
    extent = max(2.5, float(np.linalg.norm(centers - centers.mean(0), axis=1).max()) * 1.1)
    model.create_from_pcd(SimpleNamespace(points=initial['points'], colors=initial['colors'], normals=np.zeros_like(initial['points']),
                          time=initial['times'] if 'times' in initial.files else None), extent, redundant_ratio=0.)
    if 'initial_temporal_sigma_s' in cfg['scene']:
        span = manifest['frames'][-1]['pts_s'] - manifest['frames'][0]['pts_s']
        with torch.no_grad():
            if 'temporal_sigmas_s' in initial.files:
                model._scaling_t.copy_(torch.tensor(np.log(initial['temporal_sigmas_s']/span),device='cuda'))
            else:
                model._scaling_t.fill_(math.log(cfg['scene']['initial_temporal_sigma_s'] / span))
    model.training_setup(opt)
    projection = {cid: shared.validate_projection(manifest['cameras'][cid], cam, initial['points'][:200]) for cid, cam in cameras.items()}
    start, elapsed_before = 0, 0.
    load_path = (Path(args.parent) if args.render_only and args.parent else checkpoint
                 if args.resume or args.render_only else Path(args.parent) if args.parent else None)
    if load_path:
        saved = torch.load(load_path, map_location='cuda', weights_only=False)
        model.restore(saved['model'], opt)
        start = saved['step']
        elapsed_before = saved['elapsed_s']
        torch.set_rng_state(saved['torch_rng'].cpu());torch.cuda.set_rng_state(saved['cuda_rng'].cpu())
        np.random.set_state(saved['numpy_rng']);random.setstate(saved['random_rng'])
        if args.refine and not (args.resume or args.render_only):
            model.training_setup(opt)
            start, elapsed_before = 0, 0.
        del saved
        torch.cuda.empty_cache()
    injection = variant.get('inject_points', {}).get(args.dataset)
    if injection and not (args.resume or args.render_only):
        extra = np.load(ROOT / injection)
        added = GaussianModel(3, gaussian_dim=4, time_duration=[0.,1.], rot_4d=True, force_sh_3d=False, sh_degree_t=2, coefficient=coefficient)
        added.create_from_pcd(SimpleNamespace(points=extra['points'], colors=extra['colors'], normals=np.zeros_like(extra['points']),time=extra['times']), extent, redundant_ratio=0.)
        with torch.no_grad():
            added._scaling_t.fill_(math.log(variant.get('injection_sigma_s',.12) / (manifest['frames'][-1]['pts_s'] - manifest['frames'][0]['pts_s'])))
            model.densification_postfix(*[getattr(added, n).detach() for n in ['_xyz','_features_dc','_features_rest','_opacity','_scaling','_rotation','_t','_scaling_t','_rotation_r']])
        del added, extra
    sh_limit = variant.get('sh_limit', [3,2])
    model.active_sh_degree = min(model.active_sh_degree, sh_limit[0])
    model.active_sh_degree_t = min(model.active_sh_degree_t, sh_limit[1])
    # Restore the intended branch rates; upstream restore keeps the parent
    # optimizer groups' rates, while its schedule only updates spatial position.
    for group in model.optimizer.param_groups:
        if group['name'] == 't':group['lr'] = opt.position_t_lr_init * model.spatial_lr_scale
        if group['name'] in ['rotation', 'rotation_r']:group['lr'] = opt.rotation_lr
    decay = SimpleNamespace(opacity_decay=True, decay_from_iter=500 if not args.refine else 0, time_aware=True, f_min=preset['f_min'], f_max=preset['f_max'])
    background = torch.ones(3, device='cuda')
    pixels = Pixels(data, len(manifest['frames']) * len(cameras), cfg['refinement']['host_image_cache_mib'] * 2 ** 20)
    priorities = {cid: torch.tensor(np.array(Image.open(data / f'{cid}_motion_priority.png')) > 127, device='cuda') for cid in cameras}
    common_data = ROOT / 'data' / data_experiment / args.dataset / 'edge_1280'
    common_priorities = {cid: torch.tensor(np.array(Image.open(common_data / f'{cid}_motion_priority.png')) > 127, device='cuda') for cid in cameras}
    train = [(frame, cid) for frame in manifest['frames'] if args.fit_all or frame['split'] == 'train' for cid in cameras]
    heldout = [(frame, cid) for frame in manifest['frames'] if frame['split'] == 'test' for cid in cameras]
    preview_index = cfg['evaluation'].get('preview_per_dataset',{}).get(args.dataset,cfg['evaluation']['preview_local_frame'])
    max_evaluations = cfg['evaluation'].get('max_validation_timestamps')
    if max_evaluations and not args.quick_eval:
        values=sorted(set(frame['index'] for frame,cid in heldout))
        selected=set(np.array(values)[np.linspace(0,len(values)-1,min(max_evaluations,len(values))).round().astype(int)].tolist())
        selected.add(preview_index)
        heldout=[(frame,cid) for frame,cid in heldout if frame['index'] in selected]
    if args.quick_eval:
        indices = set(cfg['evaluation'].get('quick_indices',[17,47,77]))
        heldout = [(frame,cid) for frame,cid in heldout if frame['index'] in indices]
    if not heldout: raise ValueError('Evaluation reference frames must be present')
    setup = {'schema_version': 1, 'method': '4c4d', 'dataset': args.dataset, 'attempt': args.attempt, 'edge': args.edge,
             'source_commit': cfg['source_commit'], 'preset': args.preset, 'training_args': vars(opt), 'decay_args': vars(decay),
             'max_points': max_points, 'densify_until': densify_until, 'densify_interval': interval,
             'parent': str(load_path.relative_to(ROOT)).replace('\\', '/') if load_path and load_path.is_absolute() and ROOT in load_path.parents else str(load_path) if load_path else None,
             'optimizer_reset_for_resolution': args.refine and not (args.resume or args.render_only), 'camera_projection_max_error_px': projection,
             'initial_points_sha256': read(initial_path.parent / 'summary.json')['initial_points_sha256'],
             'scene_policy': manifest['scene_policy'], 'all_primitives_trainable': True, 'separate_background_model': False,
             'motion_priority': 'Time-independent RGB variance from training images; all pixels remain supervised.',
             'ssim_edge': cfg['training']['ssim_max_edge'], 'torch': torch.__version__, 'train_images': len(train),
             'heldout_images': 0 if args.fit_all else len(heldout), 'evaluation_reference_images': len(heldout),
             'fit_all_frames': args.fit_all,
             'config_sha256': hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
             'variant': args.variant, 'variant_parameters': variant, 'experiment_id': experiment,
             'quick_evaluation': args.quick_eval,
             'effective_config': cfg}
    dump(output / 'setup.json', setup)
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    losses = []
    coefficient.train()

    def call(cam, step=0, training=False):
        return render(cam, model, pipe, background, args=decay if training else None, iteration=step)['render']

    def export(step):
        weights = {name: getattr(model, name).detach().cpu() for name in ['_xyz', '_features_dc', '_features_rest', '_scaling', '_rotation', '_opacity', '_t', '_scaling_t', '_rotation_r']}
        weights.update(active_sh_degree=model.active_sh_degree, active_sh_degree_t=model.active_sh_degree_t,
                       coefficient_state={key: value.detach().cpu() for key, value in model.coefficient.state_dict().items()})
        torch.save({'schema_version': 1, 'method': '4c4d', 'source_commit': cfg['source_commit'], 'weights': weights, 'setup': setup,
                    'normalization': manifest['normalization'], 'cameras': manifest['cameras'],
                    'time_origin_pts_s': manifest['frames'][0]['pts_s'],
                    'time_span_s': manifest['frames'][-1]['pts_s'] - manifest['frames'][0]['pts_s'], 'step': step}, output / 'continuous_model.pth')

    def evaluate(step):
        entries = []
        coefficient.eval()
        with torch.no_grad():
            for frame, cid in heldout:
                cam = copy.copy(cameras[cid]);cam.time = cam.timestamp = frame['time']
                predicted = call(cam).clamp(0, 1)
                gt = torch.tensor(pixels.get(cid, frame['index']), device='cuda', dtype=torch.float32).permute(2, 0, 1) / 255
                mse = (predicted - gt).square()
                mask = priorities[cid]
                region_mse = (mse * mask).sum() / (3 * mask.sum().clamp_min(1))
                entries.append({'camera': cid, 'index': frame['index'], 'psnr_db': float(-10 * torch.log10(mse.mean().clamp_min(1e-12))),
                                'motion_region_psnr_db': float(-10 * torch.log10(region_mse.clamp_min(1e-12))),
                                'ssim_at_1280': float(ssim(smaller(predicted, 1280), smaller(gt, 1280)))})
                common_mask = common_priorities[cid]
                common_gt = torch.tensor(image(common_data / 'images' / cid / f'{frame["index"]:06d}.png'), device='cuda', dtype=torch.float32).permute(2, 0, 1) / 255
                common_prediction = F.interpolate(predicted[None], size=common_mask.shape, mode='area')[0]
                common_mse = (common_prediction - common_gt).square()
                entries[-1]['psnr_common_1280'] = float(-10 * torch.log10(common_mse.mean().clamp_min(1e-12)))
                entries[-1]['motion_psnr_common_1280'] = float(-10 * torch.log10(((common_mse * common_mask).sum() / (3 * common_mask.sum().clamp_min(1))).clamp_min(1e-12)))
                if frame['index'] == preview_index:
                    shared.save_img(predicted, output / f'{cid}_{"reference" if args.fit_all else "heldout"}.png')
                    if cid != 'iphone':
                        shared.save_img(smaller(predicted, 1920), DOCS / f'{tag}_step_{step:06d}_{cid}_preview.png')
                    if cid == 'iphone':
                        shared.save_img(smaller(predicted, 1920), DOCS / f'{tag}_step_{step:06d}_preview.png')
                        shared.save_img(smaller(gt, 1920), DOCS / f'{args.dataset}_edge_{args.edge}_heldout_gt.png')
            # Preview at a previously unrecorded angle; no new supervision.
            cal = manifest['cameras']['iphone'];cam = cameras['iphone']
            norm = manifest['normalization'];target = (np.array([.175, .105, -.045]) - norm['center_m']) * norm['scale_per_m']
            origin = cam.camera_center.cpu().numpy()
            angle = math.radians(35)
            spin = np.array([[math.cos(angle), -math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1]])
            position = target + spin @ (origin - target)
            forward = target - position;forward /= np.linalg.norm(forward)
            right = np.cross(forward, [0, 0, -1]);right /= np.linalg.norm(right)
            rotation = np.stack([right, np.cross(forward, right), forward])
            novel = shared.camera({**cal, 'R': rotation.tolist(), 't': (-rotation @ position).tolist()}, manifest['frames'][preview_index]['time'])
            shared.save_img(smaller(call(novel), 1920), DOCS / f'{tag}_step_{step:06d}_orbit.png')
        coefficient.train()
        result = {'dataset': args.dataset, 'attempt': args.attempt, 'step': step, 'edge': args.edge, 'preset': args.preset,
                  'variant': args.variant, 'point_count': len(model.get_xyz), 'elapsed_s': elapsed_before + time.perf_counter() - started,
                  'run_elapsed_s': time.perf_counter() - started, 'evaluation_image_count':len(heldout),
                  'peak_cuda_allocated_gib': torch.cuda.max_memory_allocated() / 2 ** 30,
                  'validation_psnr_db': float(np.mean([e['psnr_db'] for e in entries])),
                  'motion_region_psnr_db': float(np.mean([e['motion_region_psnr_db'] for e in entries])),
                  'validation_ssim_at_1280': float(np.mean([e['ssim_at_1280'] for e in entries])),
                  'validation_psnr_common_1280': float(np.mean([e['psnr_common_1280'] for e in entries])),
                  'motion_region_psnr_common_1280': float(np.mean([e['motion_psnr_common_1280'] for e in entries])),
                  'per_camera': {cid: {key: float(np.mean([e[key] for e in entries if e['camera'] == cid])) for key in ['psnr_db', 'motion_region_psnr_db', 'ssim_at_1280']} for cid in cameras},
                  'evaluation_role': 'fitted_reference' if args.fit_all else 'validation',
                  'fit_all_frames': args.fit_all,
                  'scope': cfg['production']['evaluation_scope'] if args.fit_all else 'Full frames and train-derived motion region. Holdouts used for parameter selection are validation, not an independent final test.',
                  'scene_policy': manifest['scene_policy']}
        dump(output / f'metrics_{step:06d}.json', {'summary': result, 'images': entries})
        dump(output / 'metrics.json', {'summary': result, 'images': entries})
        dump(DOCS / f'{tag}_step_{step:06d}_metrics.json', result)
        export(step)
        print('EVALUATION ' + json.dumps(result), flush=True)
        return result

    def save(step):
        elapsed = elapsed_before + time.perf_counter() - started
        state = {'model': model.capture(), 'step': step, 'elapsed_s': elapsed,
                 'torch_rng': torch.get_rng_state(), 'cuda_rng': torch.cuda.get_rng_state(),
                 'numpy_rng': np.random.get_state(), 'random_rng': random.getstate(), 'setup': setup}
        torch.save(state, output / 'checkpoint.tmp')
        (output / 'checkpoint.tmp').replace(checkpoint)
        if step in milestones or step == args.stop:
            # Windows hardlink retains this immutable checkpoint without duplicating bytes.
            preserved = output / f'checkpoint_{step:06d}.pth'
            if not preserved.exists():
                import os
                os.link(checkpoint, preserved)

    def document_checkpoint(step, metric):
        # Stop checkpoints are documented by the PowerShell runner. Record the
        # intermediate milestones while this process still owns the GPU.
        if step == args.stop:
            return
        python = ROOT / '.local/envs/temporal-base/python.exe'
        title = f'{tag} checkpoint {step} updates'
        role = 'Fitted-reference' if args.fit_all else 'Validation'
        detail = (f'Joint full-frame model at edge {args.edge}; {len(model.get_xyz)} Gaussians. '
                  f'{role} whole-frame PSNR {metric["validation_psnr_db"]:.2f} dB, '
                  f'motion-priority PSNR {metric["motion_region_psnr_db"]:.2f} dB. '
                  'Every primitive remains trainable. Camera-view scores do not verify novel-view geometry.')
        try:
            subprocess.run([str(python), str(ROOT / 'scripts/Temporal-BenchmarkReport.py'),
                            '--docs', f'documentation/{experiment}', '--title', title,
                            '--detail', detail, '--status', 'checkpoint; training continues',
                            '--images', f'{tag}_step_{step:06d}_preview.png',
                            f'{tag}_step_{step:06d}_orbit.png'], cwd=ROOT, check=True)
            if experiment == '4c4d_scene_001':
                subprocess.run([str(python), str(ROOT / 'scripts/Build-4C4DSceneReport.py')], cwd=ROOT, check=True)
            subprocess.run(['powershell.exe', '-NoProfile', '-File',
                            str(ROOT / 'scripts/Capture-LocalPreview.ps1'),
                            '-Url', cfg.get('report_url','http://127.0.0.1:8109/'), '-DebugPort', '8099',
                            '-OutputFile', f'documentation/{experiment}/{tag}_step_{step:06d}_checkpoint.png',
                            '-Reload'], cwd=ROOT, check=True, timeout=90)
        except (subprocess.SubprocessError, OSError) as error:
            # Training and the saved render/checkpoint survive browser failures.
            print(f'DOCUMENTATION_CAPTURE_FAILED {title}: {error}', flush=True)
            subprocess.run([str(python), str(ROOT / 'scripts/Temporal-BenchmarkReport.py'),
                            '--docs', f'documentation/{experiment}',
                            '--title', title + ' documentation capture failed',
                            '--detail', str(error) + '; model checkpoint, metrics and direct renders remain saved.',
                            '--status', 'documentation failure; training continues'], cwd=ROOT, check=False)

    if args.render_only:
        evaluate(start)
        return
    for step in range(start + 1, args.stop + 1):
        model.update_learning_rate(step)
        if step % 1000 == 0:
            model.oneupSHdegree()
            model.active_sh_degree_t = min(2, max(model.active_sh_degree_t, step // 1000))
            model.active_sh_degree = min(model.active_sh_degree, sh_limit[0])
            model.active_sh_degree_t = min(model.active_sh_degree_t, sh_limit[1])
        frame, cid = train[random.randrange(len(train))]
        cam = copy.copy(cameras[cid]);cam.time = cam.timestamp = frame['time']
        gt = torch.tensor(pixels.get(cid, frame['index']), device='cuda', dtype=torch.float32).permute(2, 0, 1) / 255
        result = render(cam, model, pipe, background, args=decay, iteration=step)
        predicted = result['render']
        weight = 1 + (variant.get('motion_region_weight', cfg['training']['motion_region_weight']) - 1) * priorities[cid]
        l1 = ((predicted - gt).abs() * weight).sum() / (3 * weight.sum())
        loss = .8 * l1 + .2 * (1 - ssim(smaller(predicted, cfg['training']['ssim_max_edge']), smaller(gt, cfg['training']['ssim_max_edge'])))
        if variant.get('detail_weight',0):
            dx = (predicted[:,:,1:] - predicted[:,:,:-1]) - (gt[:,:,1:] - gt[:,:,:-1])
            dy = (predicted[:,1:,:] - predicted[:,:-1,:]) - (gt[:,1:,:] - gt[:,:-1,:])
            loss = loss + variant['detail_weight'] * ((dx.abs()*weight[:,1:]).mean() + (dy.abs()*weight[1:,:]).mean()) / weight.mean()
        if variant.get('temporal_floor_weight',0) or variant.get('anisotropy_weight',0):
            # Deterministic subset preserves matched RNG/camera sampling between branches.
            idx = torch.arange(0,len(model.get_xyz),max(1,len(model.get_xyz)//8192),device='cuda')[:8192]
            rot = build_rotation_4d(model._rotation[idx],model._rotation_r[idx])
            scales = model.get_scaling_xyzt[idx]
            transform = rot * scales[:,None,:]
            cov = transform @ transform.transpose(1,2)
            if variant.get('temporal_floor_weight',0):
                seconds = (manifest['frames'][-1]['pts_s'] - manifest['frames'][0]['pts_s']) * cov[:,3,3].clamp_min(1e-12).sqrt()
                penalty = F.relu(torch.log(variant.get('temporal_floor_s',.04)/seconds)).square()
                loss = loss + variant['temporal_floor_weight'] * penalty.mean()
            if variant.get('anisotropy_weight',0):
                conditional = cov[:,:3,:3] - cov[:,:3,3:4] * cov[:,3:4,:3] / cov[:,3:4,3:4].clamp_min(1e-12)
                eigen = torch.linalg.eigvalsh(conditional).clamp_min(1e-10)
                ratio = (eigen[:,-1]/eigen[:,0]).sqrt()
                loss = loss + variant['anisotropy_weight'] * F.relu(torch.log(ratio/variant.get('anisotropy_limit',12))).square().mean()
        if not torch.isfinite(loss):
            raise FloatingPointError(f'Non-finite whole-scene loss at {step}')
        loss.backward()
        if step == start + 1 or step % 1000 == 0:
            for group in model.optimizer.param_groups:
                gradient = group['params'][0].grad
                if gradient is not None and not torch.isfinite(gradient).all():
                    raise FloatingPointError(f'Non-finite {group["name"]} gradient at {step}')
        with torch.no_grad():
            visible = result['visibility_filter']
            model.max_radii2D[visible] = torch.maximum(model.max_radii2D[visible], result['radii'][visible])
            if step <= densify_until:
                model.add_densification_stats(result['viewspace_points'], visible, model._t.grad.detach().abs())
                if step >= cfg['training']['densify_from'] and step % interval == 0:
                    model.densify_and_prune(cfg['training']['densify_threshold'], .005, extent, None,
                                           cfg['training']['densify_t_threshold'], prune_only=len(model.get_xyz) >= max_points)
                    if len(model.get_xyz) > max_points:
                        keep = torch.topk(model.get_opacity.flatten(), max_points).indices
                        prune = torch.ones(len(model.get_xyz), device='cuda', dtype=torch.bool);prune[keep] = False
                        model.prune_points(prune)
            model.optimizer.step();model.optimizer.zero_grad(set_to_none=True)
            model.coef_optimizer.step();model.coef_optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss.detach()))
        del loss, l1, predicted, gt, result
        if step % 100 == 0 or step == start + 1:
            torch.cuda.synchronize()
            latest_preview = DOCS / f'{tag}_live_preview.png'
            progress = {'method': '4c4d', 'dataset': args.dataset, 'attempt': args.attempt, 'step': step, 'total': args.stop,
                        'loss': float(np.mean(losses[-100:])), 'point_count': len(model.get_xyz), 'elapsed_s': elapsed_before + time.perf_counter() - started,
                        'peak_cuda_allocated_gib': torch.cuda.max_memory_allocated() / 2 ** 30, 'status': 'training', 'edge': args.edge,
                        'preview': latest_preview.name if latest_preview.exists() else None}
            dump(output / 'progress.json', progress);dump(DOCS / 'live_progress.json', progress)
            print(json.dumps(progress), flush=True)
        if step % 1000 == 0 or step == args.stop:
            save(step)
            with torch.no_grad():
                cam = copy.copy(cameras['iphone']);cam.time = cam.timestamp = manifest['frames'][preview_index]['time']
                shared.save_img(smaller(call(cam), 1920), DOCS / f'{tag}_live_preview.png')
        if step in milestones or step == args.stop:
            metric = evaluate(step)
            # Metric/render IO time is part of this elapsed run, explicitly reported.
            dump(DOCS / 'live_progress.json', {**metric, 'method': '4c4d', 'total': args.stop, 'status': 'checkpoint' if step < args.stop else 'complete',
                                             'preview': f'{tag}_step_{step:06d}_preview.png'})
            document_checkpoint(step, metric)
    print('COMPLETE ' + json.dumps({'dataset': args.dataset, 'attempt': args.attempt, 'step': args.stop}), flush=True)


if __name__ == '__main__':
    main()
