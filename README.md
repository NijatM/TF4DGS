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
- [Dynamic backend research and integration plan](docs/DYNAMIC_BACKEND_NOTES.md)
- [Submodules, fork and first-push commands](GIT_SETUP.md)

The `tf4dgs` Conda environment contains Python 3.11 and the CPU capture/analysis
foundation. Its portable recipe and tested Windows package lock are tracked.
Research GPU dependencies remain pending backend selection. LichtFeld's static
build manages its own runtime through vcpkg.

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
remain local and excluded from Git. The 4D GPU backend and Gaussian analysis
viewer remain later phases; the selected-point preview is available now.

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
foundation guide above before extracting a real capture.

LichtFeld and vcpkg are pinned Git submodules under `.local/src`. TF4DGS tracks
their commit references; future trainer/viewer changes belong in your LichtFeld
fork. The packaging fix is published in `NijatM/LichtFeld-Studio` on `tf4dgs`.
The main project is published to private `NijatM/TF4DGS`. See GIT_SETUP.md for
the completed setup and recursive-clone instructions.

Actual versions, paths and resumable stages are recorded in PROJECT_MEMORY.md
and local installation JSON records. Generated tools, builds, caches, data and
machine-specific JSON snapshots are ignored by Git. The resolved native package
inventory is retained in `native-dependencies.json`.
