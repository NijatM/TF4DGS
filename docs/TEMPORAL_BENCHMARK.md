# Short continuous 4D benchmark

The repeatable inputs are in [configs/temporal_benchmark_001.json](../configs/temporal_benchmark_001.json).
The [chronological report](../documentation/temporal_benchmark_001/README.md)
preserves setup failures, training stages, screenshots and visual comparisons.
Open the report at `http://127.0.0.1:8108/` while its local server is running.
The [finished comparison](../documentation/temporal_benchmark_001/comparison.html)
offers synchronized scrubbing, realistic fixed views, source comparisons and
exact-30-fps orbit videos. [Results and limitations](../documentation/temporal_benchmark_001/RESULTS.md)
describe what these four pilots establish.

| Capture | Original source frames, zero based | Original first / last PTS | Length |
|---|---|---|---|
| Yogurt | 330 through 419 | 11.011000 / 13.980633 seconds | 90 frames |
| Textile, including hands | 587 through 676 | 19.586233 / 22.555867 seconds | 90 frames |

Both exports have a native rate of **30000/1001 fps**, approximately 29.97.
Each clip lasts 3.003 seconds when encoded at that rate. Images come from the
original exported videos, not interpolation of the earlier 10 Hz extracted
images. Local indices 5, 11, ... 89 are held out in all three cameras: 225
training images and 45 test images. These are temporal holdouts, not a fourth
independent camera or ground-truth geometry.

The shared adapter calls the official **4DGaussians Gaussian/deformation model
and CUDA renderer**, and the official **4C4D native 4D Gaussian model, neural
opacity-decay network and CUDA renderer**. A separate child environment for
each renderer prevents their identically named extension modules colliding.
The image crop is fixed for the complete clip. Aspect ratio and per-camera
intrinsics, including the principal point, are preserved. Pixel-center resize
conventions and clip-space projection are checked against the calibration.

This is a local adapted pilot, not a reproduction of either published benchmark.
It uses the same initial XYZ/RGB cloud and 6000 single-image updates per method,
with 1000 coarse updates included in the 4DGaussians budget. The 180000-point
cap prunes the lowest-opacity points when upstream densification exceeds it.
The 4DGaussians grid is smaller than its default and enables time-dependent
SH color and opacity. All these choices are recorded in each ignored run's
`setup.json`. No later-frame 3D shape or rigid pose is supplied to a trainer.

Textile's RGB-derived cloth/hand masks are transported from available 5 Hz
samples to each native frame with 2D optical flow. Hands are reconstructed,
not removed. Cloth and hands receive equal foreground priority. The transported
mask boundaries are approximate; they do not establish material correspondence.
The textile seed combines the existing first-frame cloth cloud with a new
cloth-and-hands reconstruction at extracted bundle 196, source frame 587.
The new cloud has 793 accepted stereo anchors and 7930 registered neural-prior
points before ROI filtering. Those prior points are inferred geometry;
their small registration residual is not a measured reconstruction accuracy.
Both methods receive the identical final 35338-point textile seed. Yogurt uses
40000 points. The current table comes from these recordings with the same
camera/board positions; unrelated older desk reconstructions are excluded.

## Isolated Windows installation

Prerequisites on the tested machine: NVIDIA RTX A4000, CUDA Toolkit 13.2,
Visual Studio 2026 with MSVC 14.44 and Windows SDK 10.0.26100.0. The existing
LichtFeld/static and `tf4dgs-dynamic` installations are preserved.

Run from the TF4DGS root; stop if a command fails. Substitute the local Conda
executable if necessary.

```powershell
$Conda = "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
& $Conda env create --prefix '.local/envs/temporal-base' --file 'environments/temporal-native.yml'
$BasePython = '.local/envs/temporal-base/python.exe'
& $BasePython -m pip install torch==2.9.1 torchvision==0.24.1 --index-url https://download.pytorch.org/whl/cu130
& $BasePython -m pip install -r 'environments/temporal-native-requirements.txt'
& $BasePython -m pip install mmcv==1.6.0 --no-build-isolation --no-deps
& $BasePython -m pip install addict==2.4.0 regex==2026.9.29
& $BasePython -m venv --system-site-packages '.local/envs/4dgaussians'
& $BasePython -m venv --system-site-packages '.local/envs/4c4d'
git clone --recursive https://github.com/hustvl/4DGaussians.git '.local/research/4DGaussians'
git -C '.local/research/4DGaussians' checkout 843d5ac636c37e4b611242287754f3d4ed150144
git -C '.local/research/4DGaussians' submodule update --init --recursive
git clone https://github.com/yangzf-1023/4C4D.git '.local/research/4C4D'
git -C '.local/research/4C4D' checkout ed6a3cb69782c4147151b3898944bc38132bae00
& $BasePython 'scripts/Patch-TemporalSources.py'
& 'scripts/Initialize-TemporalNative.ps1' -Method base -Build
& 'scripts/Initialize-TemporalNative.ps1' -Method 4dgaussians -Build
& 'scripts/Initialize-TemporalNative.ps1' -Method 4c4d -Build
```

The patches request the CUDA 13 conforming MSVC preprocessor, keep Python
bindings out of CUDA-only tensor headers, select MSVC optimization flags, and
defer imports of unused pointops operations. The official mathematical CUDA
kernels are unchanged. Explicit patch diffs are retained under
`configs/temporal_patches`. The upstream source repositories retain their
original licenses. PyTorch uses its official CUDA 13.0 wheel with the installed
13.2 compiler; the minor-version compiler warning is recorded.

## Run or resume

Input preparation requires the existing measured-candidate camera files,
source exports and shared initialization assets; copying this repository alone
does not copy those ignored recordings and trained priors. The preparer writes
video, calibration and image hashes and every source index/PTS into the ignored
dataset manifests. Initial hand reconstruction is described in the journal.

On this machine the first-frame hand seed was built with the existing
`tf4dgs-dynamic` MASt3R installation. Its input masks are the pixelwise union of
`masks/<camera>/frame_000196.png` and `occlusions/<camera>/frame_000196.png`
under `outputs/dynamic_textile_001/segmentation_03_video`, copied into
`data/temporal_benchmark_001/textile/initial_hand_masks/<camera>/`.

```powershell
& "$env:USERPROFILE/miniconda3/envs/tf4dgs-dynamic/python.exe" scripts/Dense-TextileStereo.py --session data/dynamic_textile_001/session_measured_candidate.json --masks data/temporal_benchmark_001/textile/initial_hand_masks --output outputs/temporal_benchmark_001/textile_initial_stereo_hands --indexes 196 --max-reprojection 3 --depth-prior
$Tools = Get-Content static-tools.json -Raw | ConvertFrom-Json
$FFmpeg = ($Tools.portable_tools | Where-Object name -eq 'FFmpeg').executable_path
& '.local/envs/temporal-base/python.exe' scripts/Prepare-TemporalBenchmark.py --ffmpeg $FFmpeg
```

Preparation also needs the earlier first-frame cloth, yogurt canonical actor
and first pose, and current table assets named in the preparation script.
Preserve those ignored inputs in your local dataset backup. The benchmark
recipe alone cannot recreate them from an empty checkout. Preparation is
already complete on this machine; it need not be repeated to view results.

```powershell
& 'scripts/Run-TemporalBenchmarks.ps1' -SmokeOnly -Attempt smoke_new
& 'scripts/Run-TemporalBenchmarks.ps1' -Attempt pilot_new
```

Models and resumable optimizer/RNG checkpoints stay under
`outputs/temporal_benchmark_001/<method>/<dataset>/<attempt>/`.
Do not rerun into an existing completed attempt. To resume an interrupted run:

```powershell
& '.local/envs/4dgaussians/Scripts/python.exe' -u 'scripts/Train-TemporalBenchmark.py' --method 4dgaussians --dataset textile --attempt pilot_01 --updates 6000 --coarse 1000 --resume
```

Create genuine continuous-time RGB renders and inference weights from a
completed checkpoint:

```powershell
& '.local/envs/4dgaussians/Scripts/python.exe' 'scripts/Train-TemporalBenchmark.py' --method 4dgaussians --dataset textile --attempt pilot_01 --render-only --make-videos
```

Each `continuous_model.pth` holds one learned temporal model, not a sequence
of independent PLY fits. Its decoder is method specific; it is not a standard
animated PLY or a claim of SuperSplat compatibility. Fixed-view source
comparisons and +/-45-degree orbit renders use the same native timestamps.
Half-frame queries evaluate the learned model directly. Rendered MP4s are
compressed documentation; original recordings and high-resolution models stay
local. Internal Gaussian trajectories do not by themselves prove deformation
measurement accuracy or physical material-point identity.

Decode an exported single model without loading its training images or
optimizer checkpoint. Substitute the matching method, dataset and environment:

```powershell
& '.local/envs/4c4d/Scripts/python.exe' scripts/Render-ContinuousTemporal.py --model outputs/temporal_benchmark_001/4c4d/textile/pilot_01/continuous_model.pth --output outputs/temporal_benchmark_001/4c4d/textile/pilot_01/replay_30fps.mp4 --fps 30 --orbit
```

The 30 fps export queries physical time at `i / 30`, giving 90 frames over
3.000 seconds. Its end is approximately 3 ms earlier than the 3.003-second
native-rate export; no source geometry frames are duplicated to change cadence.
All four standalone exports matched the PNG training-reference render exactly
at normalized time 47/89. Optional `--reference-image` repeats that regression
check; `--probe-only` checks finite temporal decoding without making a video.

Start the seekable local comparison server after reopening the project:

```powershell
& "$env:USERPROFILE/miniconda3/envs/tf4dgs/python.exe" scripts/Temporal-BenchmarkReport.py --serve
```

Open <http://127.0.0.1:8108/comparison.html>. It plays compact rendered MP4s;
the learned models remain local under ignored `outputs/`. Browser checks,
full decoding, frame timestamps, SHA-256s, HTTP byte ranges and the source
intervals are retained in the report. Capture metadata distinguishes actual
visible-browser screenshots from headless documentation screenshots.

## Primary references

- [4DGaussians official implementation](https://github.com/hustvl/4DGaussians)
- [4DGaussians project and paper](https://guanjunwu.github.io/4dgs/)
- [4C4D official implementation](https://github.com/yangzf-1023/4C4D)
- [4C4D project and paper](https://junshengzhou.github.io/4C4D/)
- [Official PyTorch wheel versions](https://pytorch.org/get-started/previous-versions/)
