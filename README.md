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
- [Submodules, fork and first-push commands](GIT_SETUP.md)

The named Conda environment starts empty. Python, research dependencies and
validated package locks will be added when the dynamic implementation is chosen.
LichtFeld's static build manages its own runtime through vcpkg.

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
remain local and excluded from Git. The 4D backend and analysis viewer remain
later project phases.

LichtFeld and vcpkg are pinned Git submodules under `.local/src`. TF4DGS tracks
their commit references; future trainer/viewer changes belong in your LichtFeld
fork. The packaging fix is published in `NijatM/LichtFeld-Studio` on `tf4dgs`.
The main project is published to private `NijatM/TF4DGS`. See GIT_SETUP.md for
the completed setup and recursive-clone instructions.

Actual versions, paths and resumable stages are recorded in PROJECT_MEMORY.md
and local installation JSON records. Generated tools, builds, caches, data and
machine-specific JSON snapshots are ignored by Git. The resolved native package
inventory is retained in `native-dependencies.json`.
