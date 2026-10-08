# Textile reconstruction revision

This journal continues the earlier [chronological capture report](../dynamic_capture_001/README.md).
Source recordings and unsuccessful attempts remain preserved. Dates use Boston's
`America/New_York` timezone.

## 01 — Rejected result and new research — 2026-10-08

The previous textile viewer showed only sparse triangulated points. Measured
LK run05 started with 45 IDs and supported 28 samples through 2.9029 seconds;
RAFT run06 did not improve coverage. Neither run trained textile RGB Gaussians.
These attempts do **not** satisfy the requested realistic nonrigid reconstruction.
Their videos remain historical failure evidence, not a finished textile result.

Inspection of the three recordings shows repeated knit patterns, folds and
substantial hand occlusion over the 42.6-second sequence. Earlier difference
masks include board markers in the DJI view. Losing a sparse point permanently
also prevents recovery after an occlusion.

The revised implementation first separates textile from board/hands, replaces
sparse initialization with dense multiview matching, and fits actual RGB Gaussian
parameters using the three calibrated views. Geometry in hidden regions must
remain identified as model inference. Existing planar calibration and manual
frame synchronization do not establish independent deformation accuracy.

Research references:

- [4C4D, CVPR 2026](https://junshengzhou.github.io/4C4D/) and its
  [official implementation](https://github.com/yangzf-1023/4C4D): dense MASt3R
  initialization addresses sparse few-camera geometry. Its four-camera results
  do not guarantee equivalent quality with this three-camera capture.
- [TrackerSplat](https://github.com/yindaheng98/TrackerSplat): tracking constraints
  guide Gaussian motion before photometric fitting.
- [Dynamic 3D Gaussians](https://github.com/JonathonLuiten/Dynamic3DGaussians):
  persistent Gaussians with temporal/local geometric constraints.
- [SAM2](https://github.com/facebookresearch/sam2): prompted video segmentation.
- [MASt3R](https://github.com/naver/mast3r): learned dense stereo descriptors;
  code and weights are CC BY-NC-SA 4.0.
- [CoTracker3](https://github.com/facebookresearch/co-tracker): joint point tracking
  with predicted visibility. Visibility is not a certificate of correct material identity.

Official source revisions, model download URLs and locally verified SHA256 values
are recorded in `configs/textile_reconstruction_sources.json`. Models and source
clones stay in ignored `.local` folders. The working Windows PyTorch 2.4 / gsplat
environment is retained; this is a project implementation informed by these
methods, not a claim to reproduce their official benchmarks.

## Current reconstruction

The full **214/214 RGB Gaussian keyframes** and recorded-pixel appearance samples
are complete and validated, covering **0–42.509 seconds** at a median interval
of **0.2002 seconds** (approximately 5 Hz). The [chronological journal](index.html)
preserves the original failure, intermediate comparisons, genuine local/online
browser screenshots and unsuccessful export/performance attempts.

Open the local interactive RGB/map viewer at <http://127.0.0.1:8104/>.
The [compressed orbit recordings](videos/README.md) show the final replay.
The local review page at <http://127.0.0.1:8105/videos/> supports video seeking;
`scripts/Serve-TextileDocumentation.py` reopens that documentation server.
The [SuperSplat guide](SUPERSPLAT.md) explains the saved numbered PLY sequence
and its **30 fps presentation of held fitted states**. This does not create
30 independently reconstructed motion samples per second.

The [portable reconstruction summary](reconstruction_summary.json) records
28,065–124,145 textile Gaussians per time (median 80,475), native-size image crops,
and median foreground fitting PSNR of 35.64/33.23/32.28 dB for DJI/Fuji/iPhone.
These are residuals on the optimization cameras, not held-out validation.
At fast/occluded times, native-view residuals are substantially worse; for
example, iPhone frame214 is18.53 dB and Fuji frame356 is20.70 dB. Motion blur,
uncertain synchronization/depth and occlusions can leave spikes, ghost surfaces
and temporal jitter. The new realistic RGB baseline is reviewable; complete
physical deformation accuracy remains unverified.

The selected method combines SAM2 cloth masks, calibrated MASt3R correspondences,
stereo-anchored neural depth for incompletely observed surfaces, and native-size
three-camera RGB/silhouette fitting with the existing Windows gsplat renderer.
Each time has its own fitted Gaussian surface. The measured marker board and
close tabletop are reconstructed as a static Gaussian layer from **this textile
recording only**. Earlier desk, pavilion and yogurt scenes are excluded.
The selected `current_table_05` uses all 214 available mask times to recover
164,708 actually observed context Gaussians. Earlier table attempts, including
the transparent-gap context04, remain preserved. Unobserved pixels are not filled.

Native image crops retain the original pixel scale; they are not resized for
training. Camera display balance is estimated from corresponding board pixels
with Fuji as the reference. It changes training/display targets, not the saved
source images. It does not measure intrinsic material color.

The 12,000-step patch-fitting trial gave weaker texture than full-crop fitting.
A degree-one spherical-harmonic trial gave similar fitting residuals and was
not selected. Color-based artifact pruning erased real knit detail; a multi-view
support filter also damaged an upright fold. Both remain separate rejected
exports. Removing opacity below 0.035 preserved the 12 checked native-view crops
to within 0.001 dB, but the viewer currently retains the original fitted models.

## Open the real RGB replay

From this repository's PowerShell terminal:

```powershell
conda activate tf4dgs-dynamic
python scripts/Serve-TextileGaussianPreview.py
```

Open <http://127.0.0.1:8104/>. If the existing task-owned viewer is already
running, use that address without starting another copy. Select **Realistic
fitted RGB**, press **Play**, or scrub time. Choose **Free orbit** and drag to
inspect the folds; Shift-drag pans and scrolling zooms. Camera presets show
the calibrated iPhone, Fuji and DJI viewpoints. The table checkbox toggles
this capture's close surroundings.

The shape map measures distance to the closest reference surface sample.
The appearance map measures encoded RGB contrast to that closest sample,
using visible recorded-camera pixels rather than individual component colors.
Skin masks and a local reconstructed point-depth buffer reject approximate
occlusions; available camera samples are combined by channelwise median.
Gray means no supported color observation. Visibility is approximate, and
texture, lighting and viewpoint changes contribute to the contrast.
Choose the first surface for cumulative change, or an earlier surface within
the adjustable recent-time window for recent surface activity. The reference
time is shown under the render; it selects an existing earlier keyframe.
**Both maps side by side** keeps the two quantities visually separate. These
are surface comparisons, not persistent material displacement, strain or
pigment measurements. Sparse tracked trails appear only where simultaneous
calibrated tracking remains supported; complete material identity was lost
after occlusion in the long-sequence trial.

The replay uses discrete fitted keyframes, with no invented interpolation.
Three-camera training residuals measure image fitting, not independent 3D
accuracy. A planar calibration board and manually aligned 29.97 fps exports
leave intrinsic/depth and sub-frame synchronization uncertainty. Occluded
surfaces inferred by the registered shape prior are not measured ground truth.

## Files and reproducibility

| Content | Location relative to the repository |
| --- | --- |
| Copied, unchanged recordings and extracted native PNGs | `data/dynamic_textile_001/` |
| Measured candidate camera/session recipe | `data/dynamic_textile_001/session_measured_candidate.json` |
| Full cloth/occlusion masks | `outputs/dynamic_textile_001/segmentation_03_video/` |
| Stereo and explicitly marked inferred depth samples | `outputs/dynamic_textile_001/dense_stereo_04_shape_prior/` |
| RGB sequence manifest, models, PLYs and native render comparisons | `outputs/dynamic_textile_001/gaussian_sequence_04/` |
| This capture's measured-plane Gaussian context | `outputs/dynamic_textile_001/current_table_05/` |
| SuperSplat animated cloth, static context and float32 archives | `outputs/dynamic_textile_001/supersplat_export_03/` |
| Board-based display balance | `outputs/dynamic_textile_001/color_balance_02/` |
| Recorded appearance samples and visibility for each Gaussian center | `gaussian_sequence_04/frames/<index>/observed_appearance.npz` under the textile outputs |
| Chronological screenshots, evidence and research references | `documentation/dynamic_textile_001/` |
| Pinned source/weight URLs and verified SHA256 values | `configs/textile_reconstruction_sources.json` |
| Windows Python package versions | `configs/dynamic_gpu_win64.lock.txt` |

Data, checkpoints, pretrained weights, source clones, raw screencast frames and
logs stay ignored by Git. The tracked code, recipes and documentation reproduce
the process; they do not include the private recordings or trained models.

For the already prepared capture and installed dynamic environment, the selected
training command is resumable after **completed** keyframes:

```powershell
python -u scripts/Reconstruct-TextileSequence.py `
  --dense outputs/dynamic_textile_001/dense_stereo_04_shape_prior `
  --output outputs/dynamic_textile_001/gaussian_sequence_04 `
  --stride 2 --steps 6000 --upsample 5 --offset-mm 8 --stop-psnr 32 `
  --depth-prior `
  --color-balance outputs/dynamic_textile_001/color_balance_02/color_balance.json
```

Do not run a second worker against the same output directory. Completed
keyframes are skipped. An interrupted unfinished frame directory must be
preserved under a different attempt name before retrying that frame; the current
trainer does not resume its optimizer. Existing masks, color balance, camera
calibration and pinned MASt3R weights are prerequisites.

Prepare the recorded-pixel appearance maps after fitting, or use `--watch` to
follow an active sequence:

```powershell
python scripts/Sample-TextileAppearance.py
```

With the local viewer running, validate the finished sequence with:

```powershell
python scripts/Validate-TextileGaussianSequence.py `
  --output .local/workflows/dynamic_setup/textile_reconstruction_02/validation_final.json
python scripts/Summarize-TextileReconstruction.py
```

During processing, `--allow-partial` checks completed models without asserting
that the full timeline exists. Model invariants, real API renders and invalid
query rejection are checked; this is not a geometry accuracy certificate.

To record a finished local viewer with the dedicated Edge debugging session
on port 8098, capture a unique attempt and compress its real browser paints:

```powershell
.\scripts\Record-TextileGaussianPreview.ps1 -Attempt rgb_orbit_new -Mode rgb
python scripts/Encode-WebViewerRecording.py `
  --capture .local/workflows/dynamic_setup/textile_reconstruction_02/browser_captures/rgb_orbit_new/capture.json `
  --output documentation/dynamic_textile_001/videos/textile_rgb_orbit_new.mp4 --crf 20
```

Use a different attempt/output name for `-Mode combined`, `geometry` or `color`.
The arc is elevated on the iPhone side, sweeping 45 degrees in either direction.
Playback follows source wall-clock time; slow renders can skip discrete
keyframes. The capture records the samples actually displayed. Compression is
visually high quality, not mathematical losslessness.

On another machine, follow the main environment installation guide first, then
run `python scripts/Setup-TextileReconstruction.py` in `tf4dgs-dynamic` to prepare
the pinned research sources and official weights. MASt3R is CC BY-NC-SA 4.0;
CoTracker3 is CC BY-NC 4.0; SAM2 is Apache 2.0. The research dependencies have
their own licensing requirements and are not relicensed by this repository.
