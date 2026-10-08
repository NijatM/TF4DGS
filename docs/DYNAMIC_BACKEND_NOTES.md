# Dynamic backend status and integration plan

Research inspected on 2026-10-05; native Windows pilot added 2026-10-07.
An isolated gsplat renderer is installed and its CUDA forward/backward check
passed. The first real rigid-container trainer is implemented in TF4DGS;
the revised textile backend now fits independent-time RGB Gaussian surfaces
across 214 samples of the full recording. Persistent nonrigid material identity,
strain and independently reconstructed 30 Hz motion remain later work.
The working Windows static tools and their source pins are preserved.

The current rigid pilot uses measured 58 mm height and 95 mm lid diameter at
initialization. Its more solid run 06 retains 51,913 Gaussian identities over
53 supported samples, with unsupported gaps. A shared 24-view comparison
reduced opacity error by about 31% at a 0.62 dB RGB PSNR cost against measured
run 05. Original run 04 remains available. This is a provisional appearance
and rigid-motion demonstration, with full evidence in the chronological report.

## Installed rigid pilot

The official [gsplat project](https://github.com/nerfstudio-project/gsplat)
provides the rasterizer. The selected precompiled Windows wheel is
`gsplat 1.5.3+pt24cu124`, CPython 3.10, with `torch 2.4.0+cu124` in
`tf4dgs-dynamic`. It uses its packaged CUDA 12.4 runtime under the existing
driver; it does not replace system CUDA 13.2 or LichtFeld's runtime.
The wheel SHA-256 is
`62fae62e2cf233233527ba890fd322825476118edd4bd27a4e6cb36b1723003e`.

Create the Windows environment without Anaconda default-channel lookup:

```powershell
conda create --name tf4dgs-dynamic --override-channels --channel conda-forge --no-default-packages python=3.10 pip -y
conda activate tf4dgs-dynamic
python -m pip install torch==2.4.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r configs/dynamic_gpu_win64.lock.txt
python scripts/Test-DynamicGpu.py --output .local/workflows/dynamic_setup/gpu_validation_new_machine.json
```

`environments/tf4dgs-dynamic.yml` is the portable CPU interpreter recipe;
`environments/tf4dgs-dynamic-win-64.explicit.txt` records the tested Conda
packages. Use `conda create --name tf4dgs-dynamic --file` with that explicit
file for the exact Windows interpreter packages, then install the pip lock.
The lock replaces Conda's build-machine `packaging @ file:///...` entry with
its installed version, so it contains no build-machine filesystem dependency.

The first recipe-based creation attempt encountered an Anaconda terms plugin
while scanning default channels. No terms were accepted. The explicit
`--override-channels --channel conda-forge` command above succeeded.
Actual one-Gaussian rendering and nonzero finite position/color gradients
passed in 0.612 seconds on the RTX A4000; `pip check` passed. This verifies
the runtime, not reconstruction quality or physical accuracy.

`scripts/Train-RigidGaussianPilot.py` uses one canonical actor with stable IDs
and observed multi-camera rigid poses. It crops native pixels without resizing,
keeps held-out times and retains failed attempts in separate output folders.
Container shape initialization and masks are provisional. The observed motion
field is rigid displacement; it does not measure material strain. The first
actor uses time-constant colors, while fixed-camera observed appearance is
available on the selected lid features. See the
[chronological recording report](../documentation/dynamic_capture_001/README.md)
for current run status, failures, calibration residuals and screenshots.

The yogurt viewer now joins a separately fitted static Gaussian layer from the
current capture's empty frames with the moving actor in one rasterization.
It defaults to a fixed whole-scene camera. Earlier desk/Necto scans are
explicitly excluded. `Prepare-CurrentBackground.py` anchors the measured board
plane and initializes off-table surfaces with the official
[Depth Anything V2 Small indoor model](https://github.com/DepthAnything/Depth-Anything-V2/tree/main/metric_depth).
`Train-CurrentBackground.py` refines native RGB patches. Unverified overlapping
depth priors are removed in favor of the widest view. Its geometry outside the
measured plane is a prior, not a metrically verified room survey.

Source revision, checkpoint URL and SHA-256 are pinned in
`configs/current_background_sources.json`. Cache the official source under
`.local/tools/Depth-Anything-V2`, check out the pinned commit, and download the
pinned checkpoint under its `checkpoints/`; code/model caches stay ignored.
Use `--output` with a new name for every attempt. Current reproduction commands:

```powershell
conda run -n tf4dgs-dynamic python scripts/Prepare-CurrentBackground.py --output outputs/dynamic_yogurt_001/static_background_new
conda run -n tf4dgs-dynamic python scripts/Train-CurrentBackground.py --initialization outputs/dynamic_yogurt_001/static_background_new --output outputs/dynamic_yogurt_001/static_background_new/trained_01 --steps 3000 --colors-only
conda run -n tf4dgs-dynamic python scripts/Serve-RigidGaussianPreview.py --background outputs/dynamic_yogurt_001/static_background_new/trained_01/static_background.npz
```

`Validate-CurrentGaussianScene.py` checks all supported poses, unchanged static
images, measured plane and fields. For textile temporal correspondence, an
optional [torchvision RAFT optical-flow model](https://docs.pytorch.org/vision/0.19/models/generated/torchvision.models.optical_flow.raft_large.html)
uses the same installed PyTorch/torchvision versions, SHA-checked official
weights, forward/backward consistency and unchanged stereo rejection criteria.
This does not certify material identity through occlusion. Missing tracks stay
missing. No research CUDA extension or replacement static installation is needed.

## Candidate evidence

The official [4DGaussians repository](https://github.com/hustvl/4DGaussians)
is a candidate for a shared deformation model. Its published setup uses
Python 3.7, PyTorch 1.13.1/CUDA 11.6 and custom CUDA extensions. That setup is
not validation for this machine's Windows/CUDA 13 toolchain. Its
[arguments](https://github.com/hustvl/4DGaussians/blob/master/arguments/__init__.py)
default `no_dshs=True`; the
[deformation implementation](https://github.com/hustvl/4DGaussians/blob/master/scene/deformation.py)
includes temporal spherical-harmonic features behind that option. Temporal
color therefore needs explicit configuration and testing. The
[renderer](https://github.com/hustvl/4DGaussians/blob/master/gaussian_renderer/__init__.py)
also needs an adapter audit: its Python SH-conversion path accesses canonical
features, whereas the direct rasterizer path accepts deformed SH features.

[Dynamic 3D Gaussians](https://dynamic3dgaussians.github.io/) emphasizes
persistent Gaussian tracking with fixed color, opacity and size while
position/orientation evolve. That is useful tracking research, but its stock
appearance model does not directly provide the requested changing-color
experiment. The official [code](https://github.com/JonathonLuiten/Dynamic3DGaussians)
is a separate research implementation, not a drop-in LichtFeld mode.

The practical inference is to benchmark temporal deformation **and** appearance
together before choosing a backend. We have not established that either stock
repository meets the full TF4DGS requirements or the two-hour training budget.

## Proposed interface

```text
Original fixed-camera videos + measured timing + common calibration
  -> synchronized views with camera IDs, true timestamps and validity
  -> static initialization + temporal geometry/appearance backend [pending]
  -> time query: Gaussian parameters, persistent IDs, validity/provenance
  -> realistic rendering + assigned-point analysis
  -> validated dense fields and trajectories [later]
```

Keep this adapter in TF4DGS initially, separate from the pinned static source
build. A future LichtFeld viewer/trainer extension may use the user's existing
fork, but only after a dynamic backend is validated. Independent static PLY
training per frame is not a substitute for stable temporal identities.

The adapter must carry common-world camera poses, coded image dimensions,
actual frame times, time normalization, masks/visibility and scale. It must
support both temporal positions and temporal appearance while exposing stable
IDs and unsupported regions. Splits, additions and disappearances need an
explicit correspondence policy; dense data will need streaming rather than
the small JSON point-preview format.

Cross-camera appearance correction should be estimated from the unchanged
baseline and kept time-consistent where possible. Per-frame correction could
absorb the real color change we want to visualize. This is a design constraint
to test, not an implemented radiometric calibration method.

## First backend benchmark

Before adding CUDA research dependencies, review the candidate's license and
dependency requirements, choose an isolated compatible environment, then test
a small controlled capture. A WSL/Linux environment is an available future
fallback if native Windows builds cannot be made reliable.

Measure GPU memory, runtime, held-out RGB quality, calibration/timing residuals,
and known geometry/color changes. Compare a color-only case, geometry-only
case and combined case, including hidden/new surfaces. Begin with fewer frames
and an explicit image-size budget; retain native originals and increase
resolution only after memory/quality checks. Training duration alone is not
an accuracy claim.

Export queryable temporal parameters and stable track IDs before connecting
real data to the maps/trails. A CPU synthetic point preview validates the
analysis semantics, not a learned Gaussian trajectory or physical strain.

## Textile RGB reconstruction revision, 2026-10-08

The [revised textile implementation and journal](../documentation/dynamic_textile_001/README.md)
replace the failed sparse point replay with native-resolution, multiview-fitted
RGB Gaussian keyframes. Segmented dense stereo and an explicitly inferred,
stereo-anchored shape prior recover much more surface than the earlier 45 IDs.
The real local renderer supports RGB, free orbit, first/recent reference-surface
distance and recorded-pixel appearance contrast. Its static context comes only
from the current textile recording.

This is the reconstruction baseline, not the persistent-identity backend above.
CoTracker3's 700-node trial loses calibrated long-term support after 20.587 s;
material trajectories and strain are therefore still unverified. Surface maps
use nearest-reference association and approximate visibility, with unknown
color samples marked gray. Independent Gaussian component colors are not used
as observed material color; overlapping components can fit the same RGB image
with different individual colors. The journal records all rejected fitting,
context-layer and cleanup trials.
