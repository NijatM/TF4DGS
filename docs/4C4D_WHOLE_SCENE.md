# Whole-scene continuous 4C4D

This experiment trains one continuous 4D Gaussian model per capture. The subject,
hands, marker board, table and visible surroundings share the same optimizer.
There is no separate background model, frozen base or imported older room.
Existing static LichtFeld processing and the earlier short pilots are preserved.

The exact recipe is [4c4d_scene_001.json](../configs/4c4d_scene_001.json). Progress,
attempts and screenshots are recorded in chronological order in the
[experiment journal](../documentation/4c4d_scene_001/README.md).

## Inputs and time

| Capture | Source frames, inclusive | Source time | Camera frames |
| --- | --- | --- | --- |
| Yogurt | 330–419 | 11.011000–13.980633 s | 90 per camera |
| Textile and hands | 587–676 | 19.586233–22.555867 s | 90 per camera |

All three cameras use the existing synchronized exports at 30000/1001 fps.
The new data uses full frames, without the previous subject crop. Local indices
5, 11, …, 89 are excluded from training in every camera: 75 training and 15
validation timestamps, giving 225 training and 45 validation images per capture.
Validation is used to select settings and is not an independent final test.

Data stays under `data/4c4d_scene_001/<capture>/edge_<resolution>/`. Manifests
record source/video/calibration/image hashes, source frame indices, camera
matrices and the train/validation split. Native Fuji/iPhone frames are 3840×2160;
the exported DJI view is 1536×2304. A 3840-edge stage preserves these dimensions
and does not upscale the DJI recording.

Fresh initialization uses only the first selected timestamp from these three
recordings. Filtered stereo correspondences are supplemented with registered
MASt3R depth. The inferred portion is labeled in the seed and summary; it is
not a physical measurement. No previously reconstructed actor or table is used.
RGB variance gives moving regions more weight, while every camera pixel still
contributes to training. Hands and moving shadows are included in this priority.

## Environment and training

Use the installed isolated 4C4D Python, not the static LichtFeld environment.
Its Windows build, pinned source and patches are described in
[TEMPORAL_BENCHMARK.md](TEMPORAL_BENCHMARK.md). This is a project training harness
around the pinned official 4C4D model and renderer, not an unmodified reproduction
of the paper's benchmarks.

The main horizon is 30,000 updates with a 450,000-Gaussian limit. First train to
12,000, preserving the 10,000 checkpoint. Two branches start from that same
checkpoint and RNG state: slower time/rotation optimization and gentler opacity
decay. Compare all three at 12,000 using whole-frame and motion-region validation
scores plus actual camera/orbit renders. Continue the chosen branch to 30,000.
An additional textile-only `fast_time` trial doubles the time learning rate while
keeping baseline rotation and decay, after the conservative settings failed to
clear cloth streaking. It uses the same parent checkpoint and 2,000-update span.

From the selected model, run 4,000 lower-rate updates at edge 1920 and then 4,000
at native resolution, with a 600,000-Gaussian limit. Resolution stages reuse the
whole temporal model and reset the optimizer at lower rates. Both the 2,000- and
4,000-update checkpoints are retained and evaluated. If native training
runs out of memory, preserve and document that attempt before using edge 2560.
Higher pixel counts do not guarantee better geometric reconstruction.
The decoded-image CPU cache is bounded to 5 GiB, fitting this workstation's
measured 32 GiB RAM while avoiding repeated native PNG decoding. Reduce
`host_image_cache_mib` in the recipe if another machine has less available RAM.

Example commands in the project PowerShell terminal:

```powershell
& scripts/Run-4C4DScene.ps1 -Dataset textile -Attempt baseline_01 -Stop 12000
& scripts/Run-4C4DScene.ps1 -Dataset textile -Attempt slow_motion_01 -Preset slow_motion -Stop 12000 -Parent outputs/4c4d_scene_001/textile/baseline_01/checkpoint_010000.pth
# After visual selection, resume the chosen attempt (example: baseline).
& scripts/Run-4C4DScene.ps1 -Dataset textile -Attempt baseline_01 -Stop 30000 -Resume
& scripts/Run-4C4DScene.ps1 -Dataset textile -Attempt refine_1920_01 -Edge 1920 -Stop 4000 -Refine -Parent outputs/4c4d_scene_001/textile/baseline_01/checkpoint_030000.pth
& scripts/Run-4C4DScene.ps1 -Dataset textile -Attempt refine_native_01 -Edge 3840 -Stop 4000 -Refine -Parent outputs/4c4d_scene_001/textile/refine_1920_01/checkpoint_004000.pth
```

Do not run training twice into an existing attempt; use `-Resume` to continue an
interruption. `checkpoint.pth` contains optimizer and RNG state. Named milestone
checkpoints remain immutable. `continuous_model.pth` is the inference export.
All models, frames, caches and full training logs remain ignored by Git.

## Viewing and export

Start the chronological report:

```powershell
& .local/envs/temporal-base/python.exe scripts/Temporal-BenchmarkReport.py --docs documentation/4c4d_scene_001 --port 8109 --serve
```

Open <http://127.0.0.1:8109/>. The selected-model registry is created after actual
training and review. Once it exists, start the interactive model viewer:

```powershell
& .local/envs/4c4d/Scripts/python.exe scripts/Serve-4C4DScene.py
```

Open <http://127.0.0.1:8110/>. Choose a capture, recorded camera or free orbit,
scrub continuous time, and orbit with the mouse. The native/4K control renders
from the learned model; it does not enlarge the pixels beyond the selected
model's training camera dimensions. Interactive GPU throughput is distinct from
the cadence of an offline encoded video.

For a smooth exact-30-fps export, substitute the selected attempt:

```powershell
& .local/envs/4c4d/Scripts/python.exe scripts/Render-ContinuousTemporal.py --model outputs/4c4d_scene_001/textile/refine_native_01/continuous_model.pth --output outputs/4c4d_scene_001/textile/replay_30fps.mp4 --fps 30 --orbit
```

This directly queries the continuous model at `i/30` seconds. A three-second
clip contains 90 rendered frames, with a smooth ±45° orbit. Export can render
slower than playback, so preview loading cannot drop geometry frames. The single
framework-specific `.pth` model requires the matching CUDA decoder; it is not
an animated PLY and cannot be opened directly in SuperSplat.

## Accuracy limits

Surroundings means surfaces visible in these recordings. Hidden room surfaces
are not measured. Off-board calibration, depth inference, repeated knit texture,
occlusion and residual sub-frame timing can limit reconstruction. The timing
audit is diagnostic and retained the original timeline; in particular, the
yogurt Fuji matches suggested a possible one- or two-frame offset without
independent verification. Whole-image PSNR can improve while the textile stays
blurred, so motion-region and orbit evidence must accompany reported results.
Gaussian identities and internal motion are not yet validated material-point
tracking or strain measurements.

Primary sources: [4C4D implementation](https://github.com/yangzf-1023/4C4D),
[4C4D project and paper](https://junshengzhou.github.io/4C4D/).
