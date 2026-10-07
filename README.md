# Temporal Fields 4D Gaussian Splatting (TF4DGS)

Multi-camera Gaussian reconstruction and analysis of appearance and geometry
changes over time, with scalar maps and fading motion trails.

| Project identity | Value |
| --- | --- |
| Full name | Temporal Fields 4D Gaussian Splatting |
| Short name / repository folder | TF4DGS |
| Conda environment | `tf4dgs` |

Start with the static COLMAP and LichtFeld Studio workflow, then develop the
dynamic reconstruction and change-analysis pipeline.

- [Installation and machine setup](INSTALLATION.md)
- [Installation approval plan](INSTALLATION_APPROVALS.md)
- [Project scope](PROJECT_SCOPE.md)
- [Progress and restart checkpoints](PROJECT_MEMORY.md)
- [Daylight desk reconstruction and GUI training report](documentation/static_desk_002/README.md)
- [Conda environment definition](environment.yml)
- [Multi-camera dynamic foundation and preview](docs/DYNAMIC_FOUNDATION.md)
- [First dynamic recording checklist](docs/CAPTURE_CHECKLIST.md)
- [Reference markers: printable and Illustrator-editable ChArUco boards](documentation/reference_markers/README.md)
- [Dynamic backend research and integration plan](docs/DYNAMIC_BACKEND_NOTES.md)
- [First real dynamic recordings: chronological evidence and screenshots](documentation/dynamic_capture_001/README.md)
- [Submodules, fork and first-push commands](GIT_SETUP.md)

The `tf4dgs` Conda environment contains Python 3.11 and the CPU capture/analysis
foundation. Its portable recipe and tested Windows package lock are tracked.
The isolated `tf4dgs-dynamic` environment adds a verified Windows gsplat CUDA
renderer for the first moving rigid-container prototype. LichtFeld's static
build manages its own runtime through vcpkg. The two runtimes are independent.

Current setup: CUDA 13.2.2, COLMAP 4.2.1 and FFmpeg 9.0.2 are installed and their
GPU/media checks passed. LichtFeld v0.5.3 is built and installed with a documented
CUDA 13 packaging patch. Synthetic GPU training, checkpoint resume, PLY export,
and Vulkan viewer/model loading passed. No restart is required.

Open LichtFeld from PowerShell in this folder:

```powershell
& .\.local\apps\lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe
```

The daylight `static_desk_002` capture is reconstructed and trained: all 300
4K images registered, 30,000 MRNF iterations, three million Gaussians, and
held-out PSNR 25.86 dB / SSIM 0.876. The report above contains GUI screenshots,
original/brighter previews and reopening instructions. Source images and models
remain local and excluded from Git. A real rigid yogurt Gaussian pilot is now
trained, with an interactive renderer for RGB, displacement and fading motion
activity/trails. Full non-rigid textile training and temporal Gaussian appearance
remain unfinished. The real selected-point appearance/geometry preview is
available separately; see the chronological dynamic report.

The current yogurt preview uses the measured 58 mm height and 95 mm lid
diameter, with 51,913 persistent Gaussians and 53 supported pose samples.
The viewer on <http://127.0.0.1:8100/> now joins the actor with 498,531 static
surroundings Gaussians reconstructed from this capture's clean empty frames.
It defaults to a fixed whole-scene iPhone view; earlier desk/Necto scenes are
excluded. Free orbit, camera presets, motion fields and trails remain available.
The measured tabletop is anchored; off-table depth and hidden geometry remain
provisional. Earlier run 04 is retained on <http://127.0.0.1:8101/>.
Reopen the current Gaussian viewer with:

```powershell
conda run --no-capture-output -n tf4dgs-dynamic python scripts/Serve-RigidGaussianPreview.py
```

The report documents the controlled quality
comparison and all failed trials; missing times and unseen surfaces remain
unverified.

Textile processing resumed after the yogurt visual/motion checks passed.
Measured-calibration tracking now supports 28 samples through 2.9029 seconds.
A RAFT comparison on the same initial IDs did not extend coverage in that
trial. Dense non-rigid textile Gaussian replay remains unfinished.

The multi-camera Necto pavilion test is reconstructed and trained from 294
registered views at native resolution, including the approximately 7K Fuji
photos. The completed 30,000-iteration run has three million Gaussians;
held-out PSNR is 20.34 dB / SSIM 0.775. A separate conservative cleanup keeps
the room and contains 2,994,969 Gaussians. Its
[processing report, model paths and GUI screenshots](documentation/static_multi-camera_Necto_001/README.md)
record calibration, settings, validation and quality limitations. Fine yarn
remains softer in held-out renders than in the original photos.

The first dynamic foundation provides camera/session validation, measured-PTS
synchronization with drift/skew checks, native-size frame extraction, and
separate appearance/geometry analysis with fading trails. Run its synthetic
selected-point preview with:

```powershell
conda activate tf4dgs
python scripts/TF4DGS.py serve-preview
```

Open <http://127.0.0.1:8094>. This is a synthetic analysis demonstration, not a
trained 4D Gaussian model. The real recording folders are prepared under
`data/dynamic_001/raw/{dji,fuji,iphone}` and remain ignored by Git. Follow the
foundation guide above before extracting a real capture. The supplied real
recordings are now copied to `data/dynamic_yogurt_001/raw` and
`data/dynamic_textile_001/raw`, with separate camera folders, verified hashes,
native-resolution 10 Hz extraction and provisional measured-board calibration.
The chronological report above records each success and failed attempt.

LichtFeld and vcpkg are pinned Git submodules under `.local/src`. TF4DGS tracks
their commit references; future trainer/viewer changes belong in your LichtFeld
fork. The packaging fix is published in `NijatM/LichtFeld-Studio` on `tf4dgs`.
The main project is published to private `NijatM/TF4DGS`. See GIT_SETUP.md for
the completed setup and recursive-clone instructions.

Actual versions, paths and resumable stages are recorded in PROJECT_MEMORY.md
and local installation JSON records. Generated tools, builds, caches, data and
machine-specific JSON snapshots are ignored by Git. The resolved native package
inventory is retained in `native-dependencies.json`.
