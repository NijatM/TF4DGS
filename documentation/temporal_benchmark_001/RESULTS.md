# Completed continuous-model pilots

All four runs trained one temporal Gaussian model using the pinned official
model classes/renderers and the shared camera adapter. Textile includes the
hands, arms, fabric and current marker-board/table. This is a controlled local
pilot at a maximum image edge of 1280 pixels, with 6000 image updates per run.

| Experiment | Method | Held-out PSNR | SSIM | Optimization | Gaussians | Inference model |
|---|---|---:|---:|---:|---:|---:|
| Yogurt | 4DGaussians | 28.19 dB | 0.948 | 9.04 min | 180000 | 52.4 MiB |
| Yogurt | 4C4D | 32.16 dB | 0.962 | 5.45 min | 179651 | 110.3 MiB |
| Textile and hands | 4DGaussians | 22.94 dB | 0.814 | 7.55 min | 88647 | 31.8 MiB |
| Textile and hands | 4C4D | 24.35 dB | 0.826 | 5.86 min | 180000 | 110.6 MiB |

Times come from the last optimization checkpoint, excluding subsequent video
export and evaluation. Peak allocated CUDA memory was 1.36-2.20 GiB; this is
PyTorch allocation, not total system GPU usage. Scores average 45 images at
held-out timestamps across the three cameras. Textile foreground-only PSNR,
including hands, is 21.89 / 22.85 dB respectively. A high background score can
hide object errors. This does not reproduce either paper's evaluation protocol.

The matched action intervals are yogurt source frames **330-419**,
**11.011000-13.980633 s**, and textile frames **587-676**,
**19.586233-22.555867 s**. Each uses 90 native frames at 30000/1001 fps,
225 training images and 45 test images. The camera transforms, video/calibration
hashes, initial cloud hashes and every frame index/split are recorded in
[pinned_inputs.json](pinned_inputs.json).

4C4D is the stronger appearance result in these pilots. Yogurt shape and label
are clearer, but remain softer than the original camera images. Both textile
models smear knit detail, ghost moving folds and hands, and produce unreliable
geometry at new angles. The 4DGaussians orbit shows especially severe color and
geometry breakdown. Neither textile output meets the requested pristine quality
or supports a claim of accurate deformation measurement. This result concerns
these reduced-budget adapted runs, not the methods' maximum achievable quality.

The first-frame hand seed contains explicitly inferred neural shape-prior points
as well as calibrated stereo points. Three viewpoints leave hidden geometry
unobserved. Manual synchronization uncertainty, provisional off-board calibration,
occlusion, mask transport and the limited training budget remain possible error
sources; this pilot does not isolate their individual contributions. A useful
next experiment would keep these exact intervals while checking synchronization
and off-board projection, then compare stronger temporal correspondence
supervision and a larger training budget. Higher output resolution alone will
not repair the observed geometry errors.

Each local run stores `checkpoint.pth` and **one** `continuous_model.pth` under
`outputs/temporal_benchmark_001/<method>/<dataset>/pilot_01/`. The latter holds
temporal inference weights and calibrated cameras, and decodes without training
images. All four decoded reference images match the training render byte-for-byte.
Five temporal probes and queries halfway between source frames are finite;
the exact-30-fps orbit states are evaluated directly from the model. Internal
Gaussian trajectories and lifetime overlap do not establish material-point
identity or metric strain. These framework model files require the supplied
method-specific decoder and are not standard SuperSplat animated PLY assets.

[Open the comparison](comparison.html), or start the report server using
the [replay guide](../../docs/TEMPORAL_BENCHMARK.md) and visit
<http://127.0.0.1:8108/comparison.html>. Choose yogurt or textile, then fixed view,
source comparison or orbit. Both methods can play together or be scrubbed to
the same time. Fullscreen/download preserves actual encoded dimensions.

The 16 compact H.264 videos fully decode, have 90 frames each and pass constant
cadence checks. Native comparisons are 3.003 seconds at 29.97 fps; direct 30 fps
orbit exports are 3.000 seconds. All HTTP 206 range checks match local bytes.
Each browser video also passed a 1.1-second visible-viewport playback sample
after 250 ms warmup, with zero reported frame drops. Earlier startup and callback
sample failures remain in the [chronological journal](README.md), with actual
browser screenshots/state. This sample does not promise zero drops on every
device or measure real-time CUDA model-decoder throughput.

Original high-resolution footage, learned models, builds and environments stay
ignored. Documentation, recipes, scripts and compact evidence are Git candidates;
no staging, commit, push, upload or LFS changes were made. Earlier selected 4K
demos and the working static installation remain available separately.
