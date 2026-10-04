# Temporal Fields 4D Gaussian Splatting (TF4DGS): Project memory

Last updated: 2026-10-04 (America/New_York)

## Project identity

- Full name: **Temporal Fields 4D Gaussian Splatting**.
- Short name / repository folder: **TF4DGS**.
- Canonical project path: `C:\Users\mnijat\Desktop\Git\TF4DGS`.
- Conda environment: **`tf4dgs`**.
- Environment recipe: `environment.yml`, currently an empty bootstrap recipe.
- Identity update status: completed. The TF4DGS folder and empty tf4dgs environment are verified.
- Previous directory holders were identified during the completed rename;
  no folder-rename action remains. Keep the rename helper as a local record.

## Current stage

Git preparation is complete: the local repository is initialized on `main`,
with LichtFeld and vcpkg registered as pinned submodules at their existing
paths. The user created private `NijatM/TF4DGS` and their LichtFeld fork,
published the packaging fix on `tf4dgs` at `b4e26dc929d23ad8c4cc266e61eb8bf7334ede36`,
and switched the submodule URL to the fork. The user pushed initial TF4DGS
commit `8e826bd113158a71ed8ab3d15e31335572ed91be` to private `NijatM/TF4DGS`;
local `main` tracks `origin/main`. Git setup/publication is complete. Next is
real static capture and reconstruction quality validation. The first real
dataset has now passed model parsing, fresh GUI loading and one full-resolution
GPU training iteration; full training and visual quality assessment remain.
See the real-dataset checkpoint below before repeating dataset preparation.
The user handles all commits/pushes; provide VS Code terminal commands and
commit messages, including for source forks. See `GIT_SETUP.md` and the latest
Git checkpoint below.

Miniconda installation is complete and verified. The user asked whether they
needed to install Conda; the assistant handled the pinned download and
per-user installation. Conda 26.7.1 and base Python 3.14.7 are installed at
`C:\Users\mnijat\miniconda3`. No restart was requested.

The user accepted the scope ("sounds good") and requested a clean, clear,
accurate installation file. `PROJECT_SCOPE.md` records the accepted scope.
`INSTALLATION.md` provides the pinned, free native Windows static setup.

Miniconda, CUDA 13.2.2, COLMAP 4.2.1 and FFmpeg 9.0.2 are installed and verified.
CUDA native/forced-PTX execution and COLMAP GPU extraction/matching passed.
LichtFeld v0.5.3 is built and installed with the recorded CUDA 13 runtime
packaging patch. Its synthetic GPU training, iteration-10 checkpoint resume
to iteration 20, PLY export, bundled Python and Vulkan viewer/model loading
passed. The installation worker completed and no restart is required. See
the final checkpoint below and `lichtfeld-validation.json`.
The user additionally requested a Conda environment definition in the repository
to make setup on another machine easier. Section 10 of `INSTALLATION.md` now
records that requirement. Miniconda is recommended over full Anaconda; the
assistant has now completed the Miniconda installation.
Next, follow Section 7 of `INSTALLATION.md` with the user's static footage to
establish reconstruction quality. The later 4D backend has not been selected
or installed. Update this file before any required restart. The earlier requested
`grill-me` / `grilling` skill installation is complete.

## User's intended sequence

The classic static COLMAP GUI -> dataset export -> LichtFeld GUI training,
viewing and export workflow must remain available after later 4D modifications.

1. Understand and agree on the project scope through questions.
2. When the user asks, write a clean installation Markdown guide in this folder.
3. After that, install the necessary tools and validate the setup.
4. Establish a good-quality static Gaussian splatting workflow using COLMAP SfM
   and, provisionally, LichtFeld Studio (the user's wording was "lichtfield").
5. Develop multi-camera 4D Gaussian splatting.
6. Compute reference-relative scalar fields for subject color/appearance change
   and geometric change, and visualize RGB, color change, geometry change, and
   both quantities. Initial field definitions are recorded in the accepted
   scope; numerical accuracy and later combined presentation need validation.

## Persistence and restart instructions

Keep this file suitable for committing and pushing with the project. Never put
credentials, tokens, or private authentication material here.

Before a required restart, record:

- Completed work and validation results.
- Installed versions, source references, and relevant executable locations.
- Failed or unfinished steps, including exact errors when useful.
- The reason a restart is required and what the user needs to do.
- The exact next command/action and its expected result.

Tell the user when a restart is required. Resume from this file when the user
returns after restarting; verify the relevant machine state before continuing.
Do not repeat completed installations merely because the conversation restarted.

## Confirmed environment facts

- Project folder was completely empty, including no `.git` directory, at the
  beginning of this session.
- No applicable `AGENTS.md` was found in the project or its ancestor folders.
- PowerShell is the current shell. Windows Enterprise 25H2, build 26200.9168,
  was identified through registry release/build information.
- CPU: Intel Core i7-13700, 24 logical processors; physical RAM: 31.70 GiB.
- C: storage at inspection: 952.43 GiB total, 819.22 GiB free.
- GPU: NVIDIA RTX A4000, 16,376 MiB VRAM, NVIDIA driver 595.95.
- `git` was not available on the current PATH, but Git 2.55.0.windows.5 is
  installed with Visual Studio at
  `C:\Program Files\Microsoft Visual Studio\18\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe`.
- `python` and `python3` on PATH were Windows Store aliases.
- A real interpreter exists outside PATH:
  `C:\Users\mnijat\.local\bin\python3.14.exe` (Python 3.14.8), backed by uv's
  managed Python installation. This is an existing installation; do not assume
  Python 3.14 is compatible with the eventual research stack.
- WSL reports that the subsystem is not installed; no distros were registered.
- Visual Studio Community 2026 18.10.3 is installed and reports no reboot
  required. MSVC x64 toolchains 14.44.35207 and 14.51.36231, bundled CMake
  4.3.1-msvc1, Ninja, and Windows SDK headers 10.0.26100.0/10.0.28000.0 exist.
  CUDA 13.2.2 documents support for this compiler generation. Local compiler
  and application-build validation have not yet been executed.
- No CUDA developer toolkit was found on PATH, in standard install locations,
  or its standard registry key. The installed NVIDIA driver does not establish
  developer toolkit availability.
- COLMAP and LichtFeld Studio were not found in focused standard install and
  portable-location checks. This does not rule out copies elsewhere.

The environment inspection was read-only. No environment variables or machine
configuration were changed. The listed existing tools were not installed by
this session.

## Skill setup completed

Installed Matt Pocock's `grill-me` and its required `grilling` companion with the
existing Codex skill-installer helper and existing Python interpreter.

- Repository: https://github.com/mattpocock/skills
- Source commit: `d81f3a183412e71a5b1e84ca21bc1a35eea03a60`
- Source paths: `skills/productivity/grill-me` and `skills/productivity/grilling`
- Installed paths:
  `C:\Users\mnijat\.codex\skills\grill-me\SKILL.md` and
  `C:\Users\mnijat\.codex\skills\grilling\SKILL.md`
- Installed files were read and the interview instructions are being used now.
  The installer states skills become available for discovery on the next turn.

The current grilling instructions use rounds of independent questions with a
recommended answer for each. Ask dependent questions only after their
prerequisites are resolved. Investigate environment facts rather than asking
the user to look them up. Await the user's confirmation of shared understanding
before implementing the plan; this agrees with the user's requested sequence.

## Verified technical context (research, not selected implementations)

- LichtFeld Studio documents static 3DGS training from COLMAP datasets, export,
  and extensibility. Treat it as the initial static baseline; the later dynamic
  implementation has not been chosen.
- Its current README describes current Windows prebuilt binaries as available
  through paid portal access and source builds as free on Windows and Linux.
  The user chose a free setup, so plan a source-build route for LichtFeld;
  exact versions and platform still need compatibility research and decisions.
- COLMAP provides SfM camera poses and sparse reconstruction, and documents
  multi-camera rig support. The capture and calibration plan remains open.
- For quantitative analysis, distinguish displacement of a tracked physical
  region from visually plausible motion of optimized rendering primitives.
  Scale, alignment, temporal correspondence, and validation need explicit
  decisions. Rendering quality alone is not an accuracy criterion.

Sources checked on 2026-10-02:

- https://github.com/MrNeRF/LichtFeld-Studio
- https://colmap.github.io/tutorial.html
- https://colmap.github.io/rigs.html
- https://github.com/hustvl/4DGaussians
- https://dynamic3dgaussians.github.io/
- https://md-splatting.github.io/

Additional read-only research after round one (provisional; recheck the chosen
versions when writing the installation guide):

- COLMAP's official Windows CUDA ZIP is free; a native binary route avoids a
  COLMAP source build for the baseline. The current release found was 4.2.1.
- LichtFeld source requirements differ between tags and current master. Current
  guides list CUDA >=12.8, CMake >=3.30, vcpkg, and modern compilers, with Windows
  Clang components for libplacebo in current master. Application training does
  not require installing LibTorch solely for optional developer tests.
- Existing VS2026 must be matched to a compatible CUDA toolkit. CUDA13.2
  documents VS2026 support; LichtFeld includes a Windows CUDA13.2 fix. A native
  Windows source build is a provisional candidate, not a validated installation.
  Older Windows wiki requirements and newer source docs conflict; pin a version
  and test compatibility before deciding whether another compiler is necessary.
- DJI Action6 documentation includes EIS Off, fixed FOV selection, PRO controls,
  and USB-C timecode. Disabling electronic stabilization and keeping mode,
  resolution, FOV/crop and zoom fixed are recommended calibration precautions.
- A shared frame rate or synchronized timecode labels do not by themselves
  establish simultaneous sensor exposure. Verify timing using a common visible
  event and check drift over the recording; exact Fuji/iPhone capabilities are
  unknown until the models and apps are specified.
- Treat each DJI/Fuji/iPhone calibration separately; share intrinsics only
  within genuinely unchanged settings of the same physical camera.
- With two/three viewpoints, overlapping visibility and the desired viewing
  region need explicit decisions. Additional training cannot guarantee recovery
  of unobserved geometry or a numeric deformation accuracy.
- Dynamic3DGaussians fixes per-Gaussian color through time. The updated
  MD-Splatting paper/code, now DeformGS, uses a scalar shadow modulation of
  canonical RGB. These are useful tracking references, but arbitrary changing
  subject hue may require a different model or extensions. No backend selected.

Additional primary references:

- https://github.com/colmap/colmap/releases/tag/4.2.1
- https://github.com/MrNeRF/LichtFeld-Studio/blob/master/docs/building_and_distribution.md
- https://github.com/MrNeRF/LichtFeld-Studio/blob/master/docs/docs/development/build.md
- https://docs.nvidia.com/cuda/archive/13.2.0/cuda-installation-guide-microsoft-windows/index.html
- https://github.com/MrNeRF/LichtFeld-Studio/pull/1224
- https://dl.djicdn.com/downloads/DJI_Osmo_Action_6/UM/1104/DJI_Osmo_Action_6_User_Manual_v1.0_en.pdf
- https://colmap.github.io/cameras.html
- https://dynamic3dgaussians.github.io/paper.pdf
- https://arxiv.org/html/2312.00583v2
- https://github.com/momentum-robotics-lab/deformgs
- https://arxiv.org/abs/2604.04063

## First discovery round: user answers received

Confirmed by the user:

- Scene: a desk setup, roughly 1-2 m in size.
- Dynamic duration: under one minute; the precise motion and speed are open.
- Desired outputs: subject color change and geometric deformation, with options
  to examine each independently or together if feasible without excessive
  complexity. Treat actual appearance change as the working interpretation;
  ask whether deformation heatmaps and color-change measurement are also wanted.
- Accuracy: as accurate as possible on the existing hardware with a couple of
  hours of training. No numeric accuracy target was specified or promised.
- Dynamic cameras: a DJI action camera, a Fuji mirrorless camera, and potentially
  an iPhone with what the user called RAW captured video. Exact Fuji/iPhone
  models, lens, video app/format, camera count, mounting and synchronization
  remain open. Do not assume Log or ProRes is sensor RAW.
- Initial static workflow: a single DJI action camera, interpreted as DJI Osmo
  Action 6 based on the user's wording, with COLMAP SfM and LichtFeld Studio.
- Data: the user's own recordings and datasets; do not switch to a public
  reference dataset as a default requirement.
- Cost: focus on a free setup.

No implementation/backend, capture settings, numeric accuracy, or platform
choice was approved by these answers.

## Second discovery round: user answers received

Confirmed by the user:

- Experiments: pour water, a thin colorant, or slime on an object; alternatively
  inflate a balloon from medium to high inflation.
- For water/thin colorant, the user expects the substrate to remain approximately
  static while appearance changes. They want that color change mapped to a
  scalar field.
- For thick slime or balloon inflation, geometry changes should also produce
  a scalar field. Distinguish deposited new surfaces from displacement of the
  same material points when defining this quantity.
- Cameras: DJI Osmo Action 6, Fujifilm X-T5, and an iPhone described literally as
  "iphone 5 pro". Do not silently assume iPhone 15 Pro; ask for confirmation.
  The Fuji lens and iPhone recording app remain unknown.
- "RAW" means unedited original phone footage, with as little computational
  photography distortion as practical, rather than a requirement for sensor RAW.
- Cameras will stay fixed during each dynamic recording. The user intends to
  trim and align the videos manually with one-frame accuracy. Record this as
  the initial alignment plan, not a guarantee of synchronized exposures.
- Viewer must allow navigation from arbitrary viewpoints and toggling realistic
  RGB, color-change field, geometry-change field, and both fields with distinct
  scales or a better proposed representation.
- The user can provide static lighting and accurately printed calibration
  boards/patterns/paper sheets. Independent motion/shape measurements remain
  to be specified for validation.
- Platform: start with native Windows; later switching/adapting to a more
  efficient setup is acceptable if warranted.

Recommendations from read-only research, not yet user-approved definitions:

- Use a first pre-change frame as the default reference and allow changing it.
- First color scalar: observed appearance-change magnitude after normalizing
  capture color/exposure and comparing corresponding locations consistently.
  Water/gloss/refraction can change observed RGB without intrinsic pigment
  changes. Intrinsic albedo separation is a separate modeling task.
- First geometry scalar: registered surface difference in physical units, with
  a documented sign/direction convention. Persistent material displacement and
  strain can be later measurements after tracking correspondence is validated.
- Newly deposited slime should have a new-surface/unsupported-correspondence
  status where needed, rather than falsely being assigned substrate displacement.
- Static orbital DJI capture plus pre-event frames from the three fixed cameras
  is a candidate initialization/calibration workflow, contingent on overlapping
  static features. The orbit improves initial coverage but cannot observe later
  changes on regions hidden from every fixed camera.
- Provide explicit confidence/observation status for hidden, newly appearing,
  or poorly reconstructed regions. Arbitrary viewer navigation is possible;
  reliable quantitative 360-degree coverage is conditional on actual capture.
- Combined display: synchronized side-by-side fields with independent legends
  and stable scales across time is the proposed minimal version. Single-view
  contour/vector overlays can follow if useful; avoid silently combining the
  two independent quantities into one unlabeled scalar.
- Proposed progression: unchanged static desk baseline, controlled appearance
  change on a rigid textured target, slow patterned balloon inflation, then
  more challenging transparent water and slime deposition.
- One-frame timing is a useful initial alignment. The relation
  `scene_difference ~= motion_speed * timing_offset` gives a simple sensitivity
  estimate; for an illustrative 0.1 m/s motion, one frame corresponds to 3.3 mm
  at 30 fps or 1.7 mm at 60 fps. These are timing-induced scene differences,
  not predictions of achieved reconstruction accuracy. Check drift and rolling
  shutter effects on moving regions.
- Stable lens/focus/zoom/crop, exposure, white balance and disabled electronic
  stabilization are recommended capture settings. Specific settings await
  confirmation of the iPhone model, Fuji lens, and chosen recording modes.

Additional primary references from this research:

- https://colmap.github.io/faq.html#register-localize-new-images-into-an-existing-reconstruction
- https://support.apple.com/en-asia/111829
- https://support.apple.com/guide/iphone/change-video-recording-settings-iphc1827d32f/ios
- https://fujifilm-dsc.com/en/manual/x-t5/menu_shooting/movie_setting/index.html
- https://xiuming.info/projects/nerfactor/
- https://arxiv.org/abs/cs/0503076
- https://ojs.aaai.org/index.php/AAAI/article/view/38197

## Third discovery round: user answers received

Confirmed by the user:

- Phone: iPhone 15 Pro, using Blackmagic Camera for video recording.
- Fuji lenses: XF 16-80 mm F4 and XF 33 mm F1.4, with the X-T5 body.
- Color terminology remains confusing to the user. Explain it with ordinary
  examples instead of repeating technical terminology or making them choose a
  color-science method. Proposed default: measure how the recorded appearance
  changes under fixed capture settings; isolate physical causes only later.
- Two temporal analysis modes are wanted, for geometry and potentially color:
  total change relative to the first frame; and adjustable recent activity,
  e.g. a five-second buffer, with older changes fading away.
- They associate recent activity with the fading trajectory lines demonstrated
  in 4D Gaussian splatting, and want to see change speed. The requirement for
  a numerical speed field versus visual trails first still needs clarification.
- The user intends synchronization before pouring. Distinguish this alignment
  cue from the baseline frame, which should be a stable frame before the event.
- They agree to start with easy experiments and develop harder cases over time.

Proposed implementation meaning of temporal modes:

- Since start: current appearance/geometry versus the first stable pre-event
  frame; optional selectable baseline remains a reasonable control.
- Recent activity: configurable time window, initially five seconds, retaining
  recent changes and fading older contributions. Geometry shows fading trails
  where corresponding points can be tracked; appearance shows fading change
  highlights on corresponding surface regions.
- A current-versus-five-seconds-ago comparison reports net change. It can become
  zero after out-and-back motion, although movement occurred. Recent activity
  should therefore retain changes between successive times rather than rely
  exclusively on endpoint comparison. Trajectory history serves this purpose.
- Numeric speed is distance traveled between successive tracked positions
  divided by elapsed time, with appropriate noise filtering. Average speed
  over a window uses summed traveled distance divided by time. Shape distance
  alone does not establish material speed. Record this distinction when
  deciding the dynamic backend and validation requirements.
- Display fading applies to the analysis overlays/trails; it must not make the
  reconstructed physical geometry or RGB history revert to the starting state.

The user has not selected a specific dynamic backend or explicitly chosen
surface difference versus material-point displacement. Their desire for motion
trails favors validated persistent correspondences, at least for the balloon
test; retain surface-change measurements as separately labeled outputs for
deposition experiments.

Blackmagic's official camera documentation was checked. It provides recording
and manual camera controls; capture choices will be verified on the user's
actual device/app version. No cloud account or paid accessory is required by
the project scope:

- https://www.blackmagicdesign.com/products/blackmagiccamera

## Fourth discovery round: user answers received

- Start with several assigned/selected points for the first motion prototype.
- The longer-term goal is deformation analysis of all Gaussians.
- Begin with maps and trails; numerical speed is deferred until tracking is
  validated.

Record the dense goal as change fields and trajectories throughout the Gaussian
representation, with persistent identities/correspondence where supported.
New, removed, split or occluded Gaussians need appropriate reference and
validity handling rather than a fabricated zero-change value.

The practical initial color interpretation remains observed appearance change.
The user has not explicitly answered whether wetness/highlights should count;
retain it as a proposed default in the reviewable scope rather than asking the
same technical question repeatedly or blocking the static setup on it.

The scope draft is saved in `PROJECT_SCOPE.md`. Selected points versus dense
analysis and maps/trails versus immediate numeric speed are now resolved at
the phase level. Dynamic method selection, actual capture tuning and validation
remain implementation research decisions at the relevant later phase.

Scope research is read-only apart from updating this memory. No project setup
has started, and recommended capture/modeling choices remain proposals until
the user agrees to the scope.

## Later decisions to explore

- Static baseline acceptance criteria and reproducible validation.
- Capture overlap, synchronization, calibration, exposure/lighting, masks,
  coordinate system, scale, and independent reference measurements.
- Continuous motion versus repeated-survey analysis and rigid-motion removal.
- Initial dynamic dataset size and compute/storage/time budget.
- Windows versus WSL/Linux where applicable; binary use versus source changes.
- Dynamic method choice and whether LichtFeld extension or a separate research
  backend best supports the agreed measurements.
- Viewer controls, time/reference selection, color scale, geometry outputs,
  exported measurements, and uncertainty visualization.
- Research/commercial constraints, code ownership and upstream licenses.
- Documentation, dependency version pins, experiment tracking, and Git workflow.

## Installation guide prepared on 2026-10-02

The user's latest request accepts the scope and asks for the installation
Markdown file. `INSTALLATION.md` has been saved. Its commands are documented
for the next installation phase and have not been executed.

Selected versions and route:

- Reuse Visual Studio Community 2026 18.10.3, MSVC 14.51.36231, Windows SDK
  10.0.26100.0, bundled CMake 4.3.1-msvc1, Ninja 1.13.2 and Git 2.55.0.windows.5.
- Install CUDA Toolkit 13.2.2 Update 2 (nvcc 13.2.86), retain driver 595.95 for
  initial verification, and compile/run a small sm_86 kernel before the full build.
- COLMAP 4.2.1 Windows CUDA archive SHA-256:
  `e9c5cbd84c2ea986d2e970a2473fc2d2e6b34a2cdcf5d3df2765c319a63af881`.
- FFmpeg 9.0.2 Gyan essentials Windows build. Pinned archive SHA-256 from its
  provider checksum:
  `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba`.
  Actual download verification remains to be run.
- LichtFeld Studio v0.5.3 commit
  `d8c50c6a3e2273cb74130a6e9023de8d068af52d`.
- vcpkg registry/bootstrap pin
  `c3867e714dd3a51c272826eea77267876517ed99`, matching the source manifest.
- Direct Ninja Release build with portable runtime bundling and minimum CUDA
  architecture 86. No CMake presets exist at this release; avoid its older
  PowerShell helper that restricts CUDA to 12.x and fetches unneeded LibTorch.
- Expected installed executable:
  `.local\apps\lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe`.
- Use a temporary R: alias for the project to reduce Windows path lengths.
  R: was free at inspection; verify it again before mapping. The guide's alias
  and developer-shell environment have not been applied to the user's shell.
- The documented developer-shell command was checked in an isolated tool
  process: it successfully selected MSVC 14.51.36231 and SDK 10.0.26100.0.
  This did not persist environment changes in the user's shell.
- All 17 PowerShell blocks in the guide passed a parser-only syntax check
  after adding the completed Miniconda setup instructions.
  No download, installer, clone or build command was executed by that check.
- No separate Python/Conda/PyTorch or WSL installation is needed for this phase.
- The first-dataset instructions normalize undistorted model files into
  `undistorted\sparse\0` while preserving flat COLMAP workspace files.
  This uses a conventional Gaussian dataset layout; flat sparse acceptance
  by the pinned LichtFeld loader was not independently established.

Important limits: CUDA's official compiler support and the release's CUDA 13.2
fix establish a reasonable route, but the upstream Windows CI uses VS2022 /
CUDA12.8. Successful full compilation on this computer remains to be established.
No driver/toolkit/COLMAP/FFmpeg/LichtFeld installation has happened yet.

Primary guide sources:

- https://docs.nvidia.com/cuda/archive/13.2.2/cuda-installation-guide-microsoft-windows/index.html
- https://docs.nvidia.com/cuda/archive/13.2.2/cuda-toolkit-release-notes/index.html
- https://github.com/MrNeRF/LichtFeld-Studio/releases/tag/v0.5.3
- https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/CMakeLists.txt
- https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/vcpkg.json
- https://github.com/colmap/colmap/releases/tag/4.2.1
- https://ffmpeg.org/download.html
- https://www.gyan.dev/ffmpeg/builds/

## Conda portability request on 2026-10-02

The user asked whether to download Miniconda or Anaconda, with the intention
of keeping Conda setup files in the project Git repository.

- Recommend Miniconda for Windows x86_64 between those two distributions.
- Keep a project `environment.yml` and, after validation, a lockfile or Windows
  explicit Conda package specification. Preserve pip requirements separately
  where needed, and omit machine-specific absolute prefix paths.
- Keep any installer EXE under ignored `.local\downloads`; record its version,
  URL and checksum in tracked documentation.
- A Conda environment does not reproduce the installed GPU driver or the full
  native MSVC/COLMAP/LichtFeld source-build setup. Retain the installation guide.
- `environment.yml` now reserves the user-selected `tf4dgs` name, with no
  Python/research dependencies until their supported versions are chosen.
- Miniconda was subsequently downloaded, installed and verified as recorded
  below. Project environment creation is tracked in the identity status above.

## Completed Miniconda installation on 2026-10-02

- Helper: `scripts\Install-Miniconda.ps1`.
- Installer: `Miniconda3-py314_26.7.1-1-Windows-x86_64.exe` (Conda 26.7.1).
- Official URL: https://repo.anaconda.com/miniconda/Miniconda3-py314_26.7.1-1-Windows-x86_64.exe
- Official SHA-256:
  `27f1f8ae8c27bc22bbc383b84bf08c63a20a6e190f3975f3502625b1045330b2`.
- Installed target: `C:\Users\mnijat\miniconda3`, checked absent before setup.
- JustMe installation completed with no PATH addition and no default Python
  registration; no shell initialization was requested.
- Installer SHA-256 matched the official index and its Authenticode signature
  was valid, signed by Anaconda, Inc.
- Installer exit code: 0. No restart was requested.
- Passed actual checks: `conda --version` = 26.7.1, base `python --version` =
  3.14.7, `conda info --base` = the intended target, and `conda list` succeeded.
- Executables: `C:\Users\mnijat\miniconda3\Scripts\conda.exe` and
  `C:\Users\mnijat\miniconda3\python.exe`.
- Tracked provenance: `conda-installation.json`. Local records:
  `.local\logs\miniconda-installer-exit.txt` and
  `.local\logs\miniconda-base-packages.txt`.
- Miniconda base Python is separate from the eventual research environment.
  No research Python/PyTorch pins are selected by this manager installation.
- A root `.gitignore` now excludes `.local`, captures and outputs.
- The tool approval for download and per-user installation was granted and
  the helper completed with exit code 0. Do not rerun this installer against
  the completed target.
- The installation guide now includes the pinned helper, version record,
  verification results and new-machine instructions.

## Next action

The project identity update is complete. The user requested an installation
analysis and consolidated approval, then approved INSTALLATION_APPROVALS.md
including conditional fallbacks. CUDA, COLMAP and FFmpeg are installed and
their GPU/media checks passed. Continue the pinned LichtFeld dependency/build
autonomously within that scope. The tf4dgs environment is an empty bootstrap;
research dependencies remain pending.

Proceed to installation in the user's requested sequence using
`INSTALLATION.md`. Preserve its version pins, run the CUDA preflight before the
dependency build, and update this memory with actual results and physical paths.
Before a required restart, save completed/unfinished stages and the exact next
action, then tell the user to restart. Resume from that checkpoint afterward.
Do not repeat settled scope questions or claim unexecuted checks have passed.



## Project identity update completed

- Full name: Temporal Fields 4D Gaussian Splatting.
- Short name / project folder: TF4DGS.
- Project path: C:\Users\mnijat\Desktop\Git\TF4DGS.
- Conda environment: tf4dgs, created and verified with zero packages.
- Environment path: C:\Users\mnijat\miniconda3\envs\tf4dgs.
- README, installation guide, scope, memory, environment.yml and installer
  metadata use the chosen project identity.
- The independent helper completed the physical folder rename after the editor
  directory lock was released. The retained installer SHA-256 was verified.
- Python/research dependencies and the native reconstruction stack remain
  pending. Continue from the installation guide without repeating Miniconda setup.
- Rename completion UTC: 2026-10-03T04:17:49.7619375Z

## Installation authorization review on 2026-10-03

- User confirmed the renamed folder and asked for a complete prerequisites and
  approval analysis before installation, aiming to authorize the work once.
- `INSTALLATION_APPROVALS.md` records the concrete proposed actions and scoped
  conditional fallbacks. User approval was subsequently received below. This review
  did not install new software; network reads retrieved only source/metadata.
- Current preflight confirms the existing GPU, driver, Visual Studio, selected
  MSVC 14.51/SDK 26100, CMake, Ninja, Git, Miniconda and empty environment.
- Current free C: storage approximately 814 GiB. R: is free. Existing x64 VC
  runtime 14.51.36247 is installed. Shell is non-admin.
- Generic pending-file rename queue contains 15 deletion-only pairs, primarily
  temporary Windows/MSI files. Windows Update/CBS reboot flags are absent and
  VS reports no required restart. Do not force a restart based on this queue;
  compare the baseline with actual installer outcomes.
- CUDA 13.2.2 Windows full installer verified in NVIDIA page metadata:
  `cuda_13.2.2_windows.exe`, 2,499,003,640 bytes, official MD5
  `9e4bcad21f296561fa834a4eeda079d2`. Check NVIDIA Authenticode before execution
  and record the downloaded file's SHA-256.
- COLMAP/FFmpeg selected release assets and SHA-256 values remain available.
- Corrected a build-blocking guide mistake: the vcpkg tool/repository checkout
  must be `930ecc42b512b564571d767f70775d284a6fa307`, separate from the unchanged
  LichtFeld manifest baseline `c3867e714dd3a51c272826eea77267876517ed99`.
  The older checkout lacks glslang 16.2.0 and shader-slang 2026.5. All exact
  manifest overrides and port versions resolve at the new checkout.
- Pinned LichtFeld bundles Python 3.12.13 and fetches Astral uv 0.10.2. Its
  Vulkan/shader dependencies come through vcpkg; separate Vulkan SDK/Clang,
  LibTorch developer tests and nvJPEG2000 are not initial requirements.
- Added a forced-PTX kernel check alongside the ordinary CUDA kernel test,
  because the selected portable build uses driver PTX compilation.
- Following approval, run the corrected INSTALLATION.md stages in order,
  saving a checkpoint before any installer-required restart. Reuse Miniconda
  and the existing environment; do not repeat the completed rename.

## Installation approval received on 2026-10-03

- Recorded at 04:33:58 UTC (America/New_York local date 2026-10-03).
- User: "I approve the static installation plan, including conditional fallbacks."
- User requested starting with CUDA and showing its administrator prompt early
  where practical. Download and verify the full installer before launching it.
- Scope: all actions and conditional fallbacks in INSTALLATION_APPROVALS.md.
  Retain this approval across turns/restarts; do not repeat confirmations for
  authorized actions.
- Never reboot automatically. Save actual completed/unfinished stages and the
  exact resume command here before asking the user to restart.
- Current action: download/verify CUDA 13.2.2 Windows installer, install the
  toolkit with elevation and automatic reboot suppressed, then verify ordinary
  and forced-PTX kernel operation with the selected compiler.

## CUDA installation checkpoint on 2026-10-03

- CUDA 13.2.2 installed successfully; installer exit code 0. No restart was
  requested by the installer. Automatic reboot was suppressed with `-n`.
- Installer MD5 matched the official NVIDIA index. Authenticode signature was
  Valid, NVIDIA Corporation. Downloaded installer SHA-256:
  `e2993402df252e74e7fde5f1d8a5a6a05f2049065f351663ae949a9cdf3ebace`.
- Toolkit: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2`.
- nvcc 13.2.86 verified. Compiler, CUDA C++ headers and runtime/development
  libraries installed; optional Nsight/VS integration and driver packages were
  omitted. Existing NVIDIA driver remains in use.
- GPU preflight compiled using MSVC 14.51 and SDK 26100. Both ordinary kernel
  execution and forced-PTX driver compilation passed, reporting RTX A4000,
  compute capability 8.6 and result 42 with exit code 0.
- Reusable helpers: `scripts\Install-Cuda.ps1`, `scripts\Test-Cuda.ps1` and
  `scripts\Initialize-BuildSession.ps1`. The session helper restores tool PATH,
  compiler/SDK/CUDA selection; `-UseDriveAlias` enables the project R: alias.
- Provenance/logs: `.local\logs\cuda-installation.json`,
  `.local\logs\cuda-preflight-*.log`; tracked validation: `cuda-validation.json`.
- Next action: verify/download/extract COLMAP 4.2.1 and FFmpeg 9.0.2, run their
  functional checks, then clone/build the pinned LichtFeld/vcpkg sources.
- User approval, including conditional fallbacks, remains valid. No need to
  repeat CUDA installation or ask for the same authorization.

## Portable tools and source-preparation checkpoint on 2026-10-03

- COLMAP 4.2.1 CUDA ZIP and FFmpeg 9.0.2 Gyan essentials ZIP downloaded,
  verified against their published SHA-256 values, and extracted completely.
- COLMAP launcher: `.local\tools\colmap-4.2.1\COLMAP.bat`.
- FFmpeg/FFprobe: `.local\tools\ffmpeg-9.0.2\ffmpeg-9.0.2-essentials_build\bin`.
- Actual CLI checks passed. A generated 1-second H.264 clip encoded/decoded,
  probed as 640x480, and produced five extracted frames.
- Real COLMAP GPU SIFT extraction/matching passed with two generated texture
  images: 5,785 keypoints and 2,737 stored descriptor matches. Logs confirm GPU
  extractor/matcher initialization. This is a software check, not SfM quality.
- Tracked records: `static-tools.json`, `static-tools-validation.json`,
  `cuda-installation.json`, `cuda-validation.json`.
- LichtFeld v0.5.3 and its libvterm submodule cloned at the specified revisions.
  vcpkg cloned with full history, checked out at 930ecc42..., bootstrapped with
  metrics disabled. vcpkg executable version 2026-05-27-d5b6777d... .
- R: maps to this project's physical folder. Source/build/install paths use
  that alias; recreate it through `Initialize-BuildSession.ps1 -UseDriveAlias`
  after a restart before resuming the existing build tree.
- Reusable source/build helper: `scripts\Install-LichtFeld.ps1`, stages
  Prepare/Configure/Build/Install. Configuration started, using four jobs and
  the unchanged manifest baseline and corrected tool checkout.
- vcpkg fetched local build utilities including CMake 4.3.3 and 7-Zip 26.01.
  These are project build dependencies; the existing system tools remain usable.
- Current checkpoint: configure/build dependencies via
  `& .\scripts\Install-LichtFeld.ps1 -Stage Configure`, then run the Build and
  Install stages. Record a failure before changing pins or the build tree.
- User footage remains needed for full SfM/training/checkpoint/export quality
  acceptance. Do not claim those dataset checks have already passed.

## LichtFeld dependency download correction on 2026-10-03

- First configure attempt stopped at x264 0.164.3108#2 (package 33/92), after
  32 dependency stages completed and were cached. Its vcpkg double-slash URL
  returned a 7,490-byte HTML bot-check page, correctly rejected by SHA-512.
- The canonical single-slash VideoLAN URL returned the 943,381-byte archive
  with the exact original expected SHA-512:
  `707ff486677a1b5502d6d8faa588e7a03b0dee45491c5cba89341be4be23d3f2e48272c3b11d54cfc7be1b8bf4a3dfc3c3bb6d9643a6b5a2ed77539c85ecf294`.
- `Install-LichtFeld.ps1` now prefetches/verifies that canonical archive into
  vcpkg's download cache before configuring. No source pin, port or expected
  checksum is changed. Resume Configure using the existing build/cache.
- The initial subsequent CMake messages about missing Ninja/compiler were
  consequences of the earlier failed vcpkg install; no compiler change is
  warranted by this download failure.
- A generated software-only dataset is ready at
  `.local\build\lichtfeld-smoke-dataset`: 8 known-pose 128x128 images, 405 sparse
  points, 1,620 observations. COLMAP binary conversion/model analysis passed.
  This fixture is for a short loading/GPU training check after installation.

## Installation resume audit on 2026-10-03 (America/New_York)

- User requested checking the apparently stuck stage and continuing. Earlier
  static installation authorization, including conditional fallbacks, remains
  valid; no new approval is needed for resuming the approved work.
- Audit at 2026-10-04 00:09 UTC: the previous tool session/process no longer
  exists, no active vcpkg/compiler processes were found, and Windows has booted
  since the earlier build. R: is no longer mapped and must be restored.
- CUDA nvcc remains 13.2.86. Current NVIDIA driver is 596.71, changed from the
  earlier 595.95 outside this installation's recorded CUDA toolkit operation.
  Recheck GPU execution after the changed machine state before continuing.
- x264 logs show successful Debug and Release compilation/install into its
  package staging directory, ending during post-build validation. The shared
  vcpkg installed-status record still ends at the earlier 32 completed package
  stages. Do not mistake staged files for a fully installed dependency.
- Resume through Test-Cuda.ps1, then Install-LichtFeld.ps1 -Stage Configure,
  reusing the pinned source, verified x264 archive and dependency caches.
- Full LichtFeld Configure/Build/Install and its application checks remain
  incomplete. No restart is currently being requested by this agent.

## Confirmed resume progress on 2026-10-03 (America/New_York)

- Post-restart CUDA compilation, native GPU execution and forced-PTX driver
  compilation all passed again; see the refreshed `cuda-validation.json`.
- Post-restart FFmpeg media and COLMAP GPU extraction/matching checks also
  passed again at 2026-10-04 00:25 UTC. Counts remain 5 frames, 5,785 keypoints
  and 2,737 matches; see the refreshed `static-tools-validation.json`.
- The resumed CMake/vcpkg operation reports 84 of 92 dependencies already
  installed, including x264. This supersedes the earlier audit's count of 32:
  the active manifest build has more completed dependencies than that older
  status record showed. Its caches and completed packages are being reused.
- Eight remaining packages are hwloc, TBB, USD, volk, Vulkan headers/loader,
  Vulkan and Vulkan Memory Allocator. Configure is currently compiling them.
- Next stages remain Build, Install and application validation. User approval
  is unchanged, and no restart is currently required by this installation.

## VS Code closure and durable build worker on 2026-10-03

- User closed/reopened VS Code because its UI showed a grey background. The
  tool session and all compiler/build processes ended; Windows did not restart
  and the GPU driver remains 596.71. Completed installations remain intact.
- hwloc 2.11.2 and TBB 2022.3.0 finished successfully. OpenUSD 26.3 reached
  2,252/2,325 Debug build steps before interruption; its port is not installed
  yet. Ordinary vcpkg retry regenerates unfinished port builds, while completed
  dependencies and verified downloads are reused.
- Use `scripts\Start-StaticInstallationWorker.ps1 -StartStage Configure` to
  launch the remaining approved stages through Windows WMI. The hidden worker
  runs independently of the editor terminal, with below-normal CPU priority,
  one exclusive worker lock, saved state and timestamped transcript.
- `installation-worker.json` records its process ID and current/completed stage.
  Check the live process before starting another worker: an old saved state
  alone does not prove the worker is running. A reboot still stops the worker.
- It runs Configure, Build, Install, then the short synthetic LichtFeld check,
  stopping on the first error. No service, scheduled task, startup entry or
  automatic Windows restart is created. Viewer validation follows separately.

## Completed compilation and CUDA runtime packaging fix on 2026-10-03

- All 92 dependency ports installed successfully. LichtFeld's complete Release
  build passed (680 steps), using MSVC 14.51 and CUDA 13.2.86; no older compiler
  or toolkit fallback is needed for this build.
- Install stopped while resolving `nvjpeg64_13.dll`. The existing DLL is at
  `CUDA\v13.2\bin\x64`; the pinned application's runtime search list omitted
  that subdirectory. This is a packaging search-path failure.
- Recorded local fix: `patches\lichtfeld-v0.5.3-cuda13-runtime-search.patch`.
  It adds the existing Windows `bin/x64` directory to dependency search paths.
  The source Git revision and vcpkg pins remain unchanged. Configure applies
  the patch idempotently, recording its SHA-256 in the installation record.
- Resume Configure to regenerate install rules, then incremental Build,
  Install and Validate. Completed dependency ports and object files are reused.

- Static worker 2026-10-04 00:52:38 UTC: Starting Configure; run 61d03aead65146ae90b995172de42280, process 25824.

- Static worker 2026-10-04 01:18:10 UTC: Completed Configure.

- Static worker 2026-10-04 01:18:10 UTC: Starting Build; run 61d03aead65146ae90b995172de42280, process 25824.

- Static worker 2026-10-04 01:35:41 UTC: Completed Build.

- Static worker 2026-10-04 01:35:41 UTC: Starting Install; run 61d03aead65146ae90b995172de42280, process 25824.

- Static worker 2026-10-04 01:36:03 UTC: Failed at Install: cmake.exe failed with exit code 1. Log: R:\.local\logs\lichtfeld-install.log. Inspect the transcript and stage log before resuming.

- Static worker 2026-10-04 01:40:55 UTC: Starting Configure; run e32e117a0fbe4af5a9ae80c624dcd006, process 22136.

- Static worker 2026-10-04 01:41:43 UTC: Completed Configure.

- Static worker 2026-10-04 01:41:43 UTC: Starting Build; run e32e117a0fbe4af5a9ae80c624dcd006, process 22136.

- Static worker 2026-10-04 01:44:06 UTC: Completed Build.

- Static worker 2026-10-04 01:44:06 UTC: Starting Install; run e32e117a0fbe4af5a9ae80c624dcd006, process 22136.

- Static worker 2026-10-04 01:44:25 UTC: Completed Install.

- Static worker 2026-10-04 01:44:25 UTC: Starting Validate; run e32e117a0fbe4af5a9ae80c624dcd006, process 22136.

- Static worker 2026-10-04 01:44:28 UTC: Failed at Validate: R:\.local\apps\lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe failed with exit code 1. Log: R:\.local\logs\lichtfeld-training-smoke.log. Inspect the transcript and stage log before resuming.

- Static worker 2026-10-04 01:46:03 UTC: Starting Validate; run b4efabfbf1a245b499f22823ee9987dd, process 11380.

- Static worker 2026-10-04 01:46:57 UTC: Completed Validate.

- Static worker 2026-10-04 01:46:57 UTC: Configure, build, install and synthetic training checks completed; interactive viewer validation remains separate.

## Static installation completed on 2026-10-03 (America/New_York)

This checkpoint supersedes the earlier unfinished stages. The approved static
software installation is complete. No Windows restart is required, and no
installation worker or verification viewer remains running.

- Installed/reused: Miniconda 26.7.1, empty `tf4dgs` environment, CUDA Toolkit
  13.2.2 Update 2 (nvcc 13.2.86), COLMAP 4.2.1 CUDA, FFmpeg/FFprobe 9.0.2,
  Visual Studio 2026/MSVC 14.51.36231/SDK 10.0.26100.0, and LichtFeld v0.5.3.
  Current GPU driver is 596.71; it was not replaced by this CUDA installation.
- All 92 native dependency cores installed successfully. Their resolved
  versions/triplet/ABIs are saved in `native-dependencies.json` for Git.
- LichtFeld source HEAD is `d8c50c6a3e2273cb74130a6e9023de8d068af52d`.
  vcpkg tool HEAD is `930ecc42b512b564571d767f70775d284a6fa307`, with unchanged
  manifest baseline `c3867e714dd3a51c272826eea77267876517ed99`.
- The only local source change is the four-line CUDA 13 Windows runtime
  packaging patch in `patches\lichtfeld-v0.5.3-cuda13-runtime-search.patch`.
  SHA-256: `46eb8140286204ed53c27c82c4434bc44ec79383cf29a207fb78dd0378e9a202`.
  The executable therefore reports `v0.5.3-dirty (d8c50c6a)`.
- CUDA native-kernel and forced-PTX checks passed with the current driver.
  FFmpeg encode/probe/decode produced five frames. COLMAP GPU SIFT extraction
  and matching passed with 5,785 keypoints and 2,737 stored matches.
- LichtFeld loaded the eight-view known-pose fixture with 405 sparse points,
  initialized its bundled Python 3.12.13 and GPU image decoding, and completed
  20 optimizer iterations with checkpoint and PLY export. A Python callback
  preserved the genuine iteration-10 checkpoint; resume performed the remaining
  ten iterations to the checkpoint's stored limit of 20.
- The first synthetic check failed because our minimal JSON omitted mandatory
  optimizer settings. `Test-LichtFeld.ps1` now uses the pinned source's complete
  MCMC configuration with only smoke-test iteration/save overrides; validation
  then passed. No dependency or model change was required.
- Installed viewer startup passed at 2026-10-04 01:51:42 UTC, with build tools
  and external Python/CUDA settings removed from the child process environment.
  Logs show RTX A4000 Vulkan initialization, CUDA external memory/timeline
  semaphore sharing, UI/resource and embedded-Python startup, and loading the
  exported 405-Gaussian PLY. Only the verification process was closed afterward.
- Validation evidence: `cuda-validation.json`, `static-tools-validation.json`,
  `lichtfeld-validation.json`; detailed logs are under ignored `.local\logs`.
  The completed worker's final record is `installation-worker.json`.
- Final static checks parsed all 12 PowerShell helpers and all 21 PowerShell
  command blocks in `INSTALLATION.md`; JSON records and source patch checks
  passed. Source revisions and complete installed executable locations were
  rechecked. The guide, README and scope now reflect the completed setup.

Executable locations (physical paths; launching the viewer needs no R: alias):

```text
C:\Users\mnijat\Desktop\Git\TF4DGS\.local\apps\lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe
C:\Users\mnijat\Desktop\Git\TF4DGS\.local\tools\colmap-4.2.1\COLMAP.bat
C:\Users\mnijat\Desktop\Git\TF4DGS\.local\tools\ffmpeg-9.0.2\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe
C:\Users\mnijat\miniconda3\Scripts\conda.exe
```

Next action: follow Section 7 of `INSTALLATION.md` using an unchanged textured
scene recorded with the DJI camera. Extract frames, reconstruct/undistort with
COLMAP, train in LichtFeld, and inspect/export the result. No real footage was
provided in this installation pass, so SfM completeness, rendering quality and
measurement accuracy remain unvalidated. The tiny synthetic fixture verifies
software operation only.

The later 4D reconstruction backend, analysis maps and trails are not installed
or implemented yet. Select that backend before adding Python/PyTorch research
dependencies to `tf4dgs`. Keep generated apps, source, downloads, captures and
outputs ignored; the documentation, scripts, patch and root JSON records are
suitable for committing to Git. No Git repository was initialized or pushed.

## Git and submodule setup on 2026-10-03 (America/New_York)

This checkpoint supersedes the earlier statement that Git was not initialized.
The user approved setting up submodules and asked for first-push commands.
Their screenshot identifies the GitHub account as `NijatM`; the proposed remote
names are `NijatM/TF4DGS` and `NijatM/LichtFeld-Studio`. Remote existence could
not be verified through web access. No GitHub repository or fork was created.

- Initialized this local Git repository on `main`, with repository-local
  `core.longpaths=true`. No TF4DGS commit or main remote exists yet; no pushes
  or source commits were performed by the assistant.
- Registered the existing source checkouts as submodules, preserving the
  working build/source paths and the uncommitted CUDA packaging fix:
  `lichtfeld` at `.local/src/LichtFeld-Studio`, commit `d8c50c6a...`, and
  `vcpkg` at `.local/src/vcpkg`, commit `930ecc42...`. LichtFeld's nested
  libvterm remains at `934bc2fb...`.
- `.gitmodules` currently uses the working upstream URLs. `GIT_SETUP.md`
  instructs the user to create their fork, publish the existing packaging fix
  on its `tf4dgs` branch, and then switch the LichtFeld submodule URL to the
  fork before committing/pushing TF4DGS.
- An optional `git submodule absorbgitdirs` metadata migration stopped with
  Windows `Permission denied`. The source checkouts retain their existing
  embedded Git directories, a supported submodule layout. Recursive status,
  Git references and build source files remain valid; no source edits were
  discarded, and no build directory move/rebuild is required.
- Updated `.gitignore` to expose only the two source submodule paths under
  `.local`. Installers/apps/builds/cache/logs/data/outputs/environments/editor
  files and root installation/validation/worker JSON snapshots are excluded.
  `native-dependencies.json`, setup scripts, the patch and useful Markdown
  summaries remain eligible for Git. Added `.gitattributes` for text files.
- `Get-ProjectSubmoduleCommit.ps1` reads the parent's recorded gitlink.
  `Install-LichtFeld.ps1` now uses those selected commits and initializes
  submodules, so future fork commits can be built without changing a hardcoded
  trainer SHA. It refuses to overwrite unrecorded source commits and preserves
  the selected manifest baseline. The runtime patch remains idempotent.
- Updated README, installation guide and scope; added `GIT_SETUP.md` with
  commands for source-fork setup/review/commit/push, the main first commit/push,
  recursive cloning, and later source-reference updates. Added `AGENTS.md` to
  preserve the user's Git preference for future assistant sessions.
- Validation: all 13 PowerShell scripts, 21 installation command blocks,
  seven Git-setup command blocks and the README launch block parsed. Local links
  passed. Recorded source revisions match the existing checkouts; recursive
  submodule status and patch whitespace checks passed. The prospective first
  commit includes only project files and two gitlinks, with no generated
  artifacts; the largest regular file is under 60 KB. The installed app and
  build source paths remain present, and the patch SHA-256 is unchanged.
- Final integration check: `git submodule update --init --recursive` completed
  successfully with both existing source pins and the four-line packaging edit
  preserved. A first-commit `git add --dry-run .` included only intended project
  files; the real index still contains only `.gitmodules` and the two gitlinks.

Persistent user instruction: never perform commits or pushes on the user's
behalf, including the LichtFeld fork. Always provide VS Code terminal commands
and suitable commit text. The current initial Git/submodule registration is
complete; all publishing steps are now for the user to run from `GIT_SETUP.md`.
Git author name/email were found unset in both repositories. The guide includes
repository-local identity commands, with the email supplied by the user from
their verified GitHub email/noreply settings; no identity was set by the assistant.
Once their commands finish, verify the new fork URL and source reference when
continuing project work, then proceed to real static capture quality validation.

## User terminal progress: staged source fix and Git pager

The user's pasted terminal output stopped at Git's diff pager (`:` / `(END)`),
not a failed setup command. Exit that viewer with **q**. Saved Git review
commands in `GIT_SETUP.md` now use `--no-pager`.

Read-only verification confirmed that the user has configured author name/email
in both repositories, created the LichtFeld `tf4dgs` branch, renamed the original
source remote to `upstream`, added `origin` pointing to
`https://github.com/NijatM/LichtFeld-Studio.git`, and staged exactly the intended
four-line CMake packaging fix. No author email is recorded here.

The source fix is still uncommitted. The main repository has no remote and its
`.gitmodules` still points to upstream LichtFeld. Next user commands are the
source commit/push, then switching the submodule URL and making the main first
commit/push. Do not repeat the already completed branch/remote creation steps.
The assistant performed no commits or pushes.

## GitHub CLI setup and fork-command correction

The user installed official GitHub CLI 2.102.0 with WinGet, authenticated as
`NijatM`, and successfully created private `NijatM/TF4DGS` on GitHub. Do not
repeat those steps. No authentication token or one-time login code is saved
in this project.

The assistant's proposed fork command incorrectly combined an explicit
repository argument with `--remote=false`; CLI 2.102.0 rejected that combination
before creating the fork. The corrected user command is:

```powershell
$Gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
& $Gh repo fork MrNeRF/LichtFeld-Studio --clone=false
```

The installed CLI's help confirms the explicit-repository `--clone=false`
example. `GIT_SETUP.md` now includes this corrected terminal alternative and
the user's current checkpoint. Read-only source inspection still shows the
four-line `CMakeLists.txt` fix staged and uncommitted on `tf4dgs`.

After successful fork creation, the user should commit/push that fix, switch
the parent's submodule URL to the fork, review/stage the TF4DGS files and make
the main first commit/push. Do not recreate the existing source branch/remotes.
The assistant has not created remote repositories, committed, or pushed.

## User published the source fix; main first push is next

The user successfully created `NijatM/LichtFeld-Studio`, committed the recorded
four-line packaging fix and pushed branch `tf4dgs`. Published source commit:
`b4e26dc929d23ad8c4cc266e61eb8bf7334ede36`. The source working tree is clean,
and its local `origin/tf4dgs` reference matches that commit.

The user then switched the parent's LichtFeld submodule URL to
`https://github.com/NijatM/LichtFeld-Studio.git`. Read-only checks confirmed the
new URL in `.gitmodules`. The parent index still holds the original source
reference until the user's next `git add .`; that command records the published
fork commit along with the updated URL and project files.

No main-project commit or local main remote exists yet. Its prospective file
list contains only intended project documents/scripts/configuration/patches,
the native package inventory and the two source gitlinks. Generated artifacts
and local status JSON remain excluded. Updated the guide, README, installation
source note and current checkpoint to reflect the published fork.

Next user sequence: `git add .`, inspect `git status --short` and
`git --no-pager diff --cached --stat`, commit with
`Initialize TF4DGS with pinned source submodules and reproducible Windows setup`,
add `origin` as `https://github.com/NijatM/TF4DGS.git`, then run
`git push --recurse-submodules=check -u origin main`.
The assistant performed no commits or pushes. After the user reports success,
verify the main remote/reference and update this checkpoint before continuing
with real static capture validation.

## Initial GitHub publication completed on 2026-10-03

The user successfully made and pushed TF4DGS's first commit:
`8e826bd113158a71ed8ab3d15e31335572ed91be`, message
`Initialize TF4DGS with pinned source submodules and reproducible Windows setup`.
The main remote is `https://github.com/NijatM/TF4DGS.git`; branch `main` tracks
`origin/main`. Local HEAD and the remote-tracking reference matched, and the
working tree was clean when checked immediately after the push.

The commit contains 30 entries, including two source gitlinks:
LichtFeld fork `b4e26dc929d23ad8c4cc266e61eb8bf7334ede36` and upstream vcpkg
`930ecc42b512b564571d767f70775d284a6fa307`. The push's submodule availability
check passed. Its payload was 77.59 KiB; installers, apps/builds/cache/logs,
footage, outputs and local status JSON were not included. LF/CRLF messages
were informational text normalization warnings and did not prevent the push.

Updated README, installation guide, Git guide and this checkpoint to mark
publication complete. These documentation changes can be saved by the user's
next commit, suggested message `Record completed GitHub publication`; no code
or source references were changed. The initial publication hash above is a
stable baseline, not a requirement to record every later documentation commit.

No Git setup step remains to repeat. Next project phase is the first real
static capture/reconstruction quality check in Section 7 of `INSTALLATION.md`.
The assistant has performed no commits or pushes.

## First real static dataset and import recovery: 2026-10-04

- Capture: DJI Osmo Action 6, Standard (Dewarp) view, as confirmed by the user.
  There are 128 JPEG frames, all 3840 x 2160. The user explicitly requests
  full-resolution training. Start with shared PINHOLE intrinsics and SIFT.
- Initial reconstruction was attempted before matching; read-only database
  inspection found 128 feature/descriptor entries and zero matched pairs.
  The user subsequently completed matching and reconstruction.
- COLMAP's real-model analysis reports 128/128 registered images and frames,
  one camera, 52,553 points, 345,025 observations, mean track length 6.565277,
  and mean reprojection error 0.745140 px. These checks do not establish final
  Gaussian rendering quality.
- Undistortion originally landed in
  `data/static_desk_001/sparse/0/undistorted`. The intended dataset root was
  empty, then absent during preparation. Copied the original dataset into
  `data/static_desk_001/undistorted`, preserving the nested original, and copied
  its five binary model files into `undistorted/sparse/0`. All 128 image files
  are present; copied model files match originals byte for byte. The corrected
  camera dimensions remain 3840 x 2160.
- The user's saved configuration at
  `data/static_desk_001/run_01/training_config.json` allows 5,000,000 Gaussians.
  Created a separate retry configuration at
  `outputs/static_desk_001/run_01/training_config_4k_1m.json`: 30,000 iterations,
  MRNF, 1,000,000 maximum Gaussians, SH degree 3, resize factor 1, no width cap,
  and checkpoint steps 10,000/20,000/30,000. Original configuration preserved.
- The user encountered an import error classified as corrupted data, wrapping
  `CUDA out of memory: failed to allocate 630636 bytes`. The original GUI
  failure's exact cause has not been isolated. About 11.7 GiB GPU memory was
  free after the failure; the small allocation error alone does not prove the
  4K dataset exceeds VRAM or that its files are corrupt.
- A fresh headless diagnostic completed exactly one real-data GPU training
  iteration with MRNF, SH3, 1M capacity and resize factor 1. Decoder logs
  confirm 3840x2160 -> 3840x2160; training completed successfully, with a
  diagnostic PLY and checkpoint. Artifacts/logs are ignored under
  `.local/build/real-dataset-import-e3248456c565462caf9e022968a6ad33`.
- A separate fresh GUI successfully loaded 52,553 points and all 128 views;
  no CUDA allocation/import error appeared in its log. Training was not
  started in that GUI. Its ignored logs are under
  `.local/build/real-dataset-gui-6cb649e2e30548c9a0858098a77a8374`. Both diagnostic
  processes had exited when checked. The assistant did not close the user's
  applications, restart Windows, commit, push, or modify source submodules.
- Next user action: open a fresh LichtFeld instance; import the prepared retry
  config; import the absolute dataset root
  `C:\Users\mnijat\Desktop\Git\TF4DGS\data\static_desk_001\undistorted`; set
  output to `C:\Users\mnijat\Desktop\Git\TF4DGS\outputs\static_desk_001\run_01`;
  disable downscaling and verify resize factor 1, then train and assess the
  result. A long training run was not started by the assistant. Avoid relative
  output paths that resolve inside the model directory. Data, configs, logs
  and training results in these locations remain excluded from Git.

## Daylight dataset GUI run in progress: 2026-10-04

- User authorized autonomous visible-GUI reconstruction and highest practical
  quality training for `data/static_desk_002/images`, with screenshots of every
  major step under `documentation/static_desk_002` and a brighter presentation.
- All 300 JPEG frames are 3840 x 2160. Originals remain unchanged. Views cover
  the desk, underside, floor and ceiling, not just the tabletop.
- Visible COLMAP process 29092 is reconstructing cameras. Shared PINHOLE,
  native-size SIFT, 16,384 feature cap, GPU 0. Extraction: 1,738,530 entries.
  Exhaustive guided matching completed in 14.582 minutes; 9,836 verified
  pairs and 3,986,056 inlier correspondences. All 300 images are connected.
- Saved GUI project: `data/static_desk_002/project.ini`. Sparse export and
  undistortion have not yet completed. Training has not started.
- Prepared planned full-4K MRNF/SH3/3M-cap/30k PPISP configuration under
  `outputs/static_desk_002/run_01/training_config_4k_3m_ppisp.json`, with held-out
  evaluation every eighth image and save/eval steps 7k/15k/30k. Verify accepted
  settings and memory use before relying on this configuration.
- Ignored helpers/logs live under `.local/workflows/static_desk_002`.
  `Gui-Control.ps1` operates and captures real visible windows. `Lfs-Mcp.ps1`
  will use the visible application's local MCP interface for training and
  screenshots. LichtFeld has not successfully launched for this dataset yet;
  launch with both `-d` and `-o` once undistortion is complete.
- No changes to installations or source pins; no assistant Git commits/pushes.
  Continue camera reconstruction, export/validate the model, undistort through
  the GUI, train visibly, evaluate, adjust exposure, save results and update
  the report/checkpoint. Do not repeat matching or discard completed work.

### Dataset 002 training started, 16:23 local time

- COLMAP finished: 300/300 registered, 168,166 points, 985,960 observations,
  mean track 5.863016, mean reprojection 0.995828 px; 9.886 minutes.
  Shared PINHOLE fx=1519.166753, fy=1519.855750, cx=1920, cy=1080.
- Sparse model exported to `data/static_desk_002/sparse/0`. GUI undistortion
  completed; all 300 full-4K images are SHA-256 identical to originals.
  Both flat `undistorted/sparse` binaries and conventional `sparse/0` copies
  exist. No source frames were edited or discarded.
- Visible LichtFeld process 11088 is actively training: MRNF, SH3, 3M capacity,
  30k iterations, PPISP enabled, 262 training / 38 evaluation views, full 4K
  confirmed by decoder logs. The model starts from the 168,166 SfM points.
- Native GUI MCP is available at `http://127.0.0.1:45677/mcp`; helper
  `.local/workflows/static_desk_002/Lfs-Mcp.ps1` initializes and calls it.
  Tool/resource schemas are saved beside the helper. It captures real GUI
  screenshots with `render.capture_window`, without headless training.
- Output root: `outputs/static_desk_002/run_01`. Save/eval steps: 7k/15k/30k.
  Native checkpoint files may be overwritten at each save; preserve copies if
  intermediate resumable states are needed. Do not start a second training run
  while this GUI is active. Query `runtime.job.describe` for `training.main`.
- App opened maximized; startup splash dismissed. Selected desk camera
  `frame_04622.jpeg`, UID 51, and hid camera frustums/grid for the preview.
  PPISP manual exposure remains 0 EV pending assessment after training.
- The installed binary does not accept `--no-splash`; omit that flag. Earlier
  attempted launches exited before training. Use both `-d` and `-o` in future
  CLI-assisted GUI launches. No installation/source changes were made.
- Continue monitoring checkpoints, evaluation quality and GPU memory; assess
  brightness, save final results and update documentation. No Git push/commit.

### Dataset 002 halfway checkpoint, approximately 17:01 local time

- The visible GUI is still training, now beyond 15,000 of 30,000 iterations.
  Gaussian count reached the configured 3M cap. Keep process 11088 running;
  do not reset the scene or launch another trainer.
- Held-out metrics: 7k PSNR 22.429337 / SSIM 0.821145; 15k PSNR 23.948362 /
  SSIM 0.846573. Native checkpoints are preserved as `checkpoint_07000.resume`
  and `checkpoint_15000.resume` under the run's checkpoints directory.
- Hidden monitor process 32724 records actual GUI state every 30 seconds,
  captures milestones and copies checkpoints only when their binary header
  contains the expected iteration. Its state is in
  `.local/workflows/static_desk_002/training_monitor.json`.
- Generic `session.pause` and `training.get_state` do not bind to this GUI
  trainer. Use `runtime.job.describe/control` for job `training.main`; named
  pause/resume were verified and the brief diagnostic pause was resumed.
- The Vulkan preview ignores stored PPISP manual exposure. Controlled paused
  captures at 0/0.8/1.2 EV were visually and numerically almost identical;
  pinned source confirms its preview path bypasses appearance correction.
  PPISP remains enabled in training and the native checkpoint. Native held-out
  evaluation is performed on the model render, without the planned brightness
  variant. Do not describe the stored preview exposure as effective.
- Added `scripts/Adjust-SplatBrightness.ps1` for a separate brighter SH3 PLY.
  It preserves original PLY, verifies every non-color attribute byte and
  Gaussian order by SHA-256, and publishes only the adjusted copy. It has not
  yet been run against the final PLY. After training, export canonical PLY,
  run and validate this script, reopen both versions in the GUI at the same
  camera, capture the actual brightness comparison, and finish the report.
- Portable `documentation/static_desk_002/training_recipe.json` was copied
  from actual saved training parameters with relative dataset/output paths.
  `held_out_frames.txt` records the 38 validation views; its order is not a
  guarantee of native evaluation PNG numbering.

## Daylight dataset 002 completed: 2026-10-04, final save 17:46:17 local

- This checkpoint supersedes the earlier in-progress dataset 002 entries.
  All reconstruction, preparation, full-4K Gaussian training, validation,
  brightness adjustment and GUI reopening requested by the user are complete.
- COLMAP registered 300/300 images in one shared PINHOLE model: 168,166 points,
  985,960 observations and 0.995828 px mean reprojection error. All 300 prepared
  images remain byte-identical to the originals. Dataset/project paths above
  remain valid; do not repeat matching or reconstruction for this result.
- Visible LichtFeld finished MRNF, SH3, 3M capacity, 30k iterations, PPISP and
  full 3840 x 2160 decoding. There were 262 training and 38 held-out views.
  Final PSNR 25.855387 dB / SSIM 0.875689 improved on both earlier evaluations.
  The native training-manager log reports 4917.5 seconds (81m58s); wall time
  was about 83 minutes. The runtime job's elapsed field changes after finish
  and must not be used for the completed duration.
- Outputs under `outputs/static_desk_002/run_01`: original `splat_30000.ply`,
  `splat_30000.ppisp`, and separate `static_desk_002_bright_rgb_1p4.ply`.
  Both PLYs contain 3M Gaussians and are 744,001,532 bytes. Native checkpoints
  `checkpoint_07000.resume`, `checkpoint_15000.resume` and
  `checkpoint_30000.resume` are preserved in the checkpoints subfolder.
  The final header confirms 30k/3M/SH3/PPISP. Do not retrain automatically.
- `scripts/Adjust-SplatBrightness.ps1` successfully processed the actual
  final PLY at RGB gain 1.4. All 48 SH color properties were adjusted; every
  non-color byte and vertex order remained identical. Non-color SHA-256:
  `65facfb43cd9e1bbfc94edf6029a99cc4d62e38e1579b857ccbbc6c763907918`.
  This is a viewing brightness derivative, not physically simulated relighting.
  Use the original model/checkpoint for future color analysis or training.
- Both PLYs were reopened in the same visible GUI and verified as one model,
  3M Gaussians each. Same-view sampled luma changed 54.8298 -> 76.7540 (~40%).
  A nearby novel view rendered correctly. The brighter model is left open in
  process 11088, with the original overview camera restored and Rendering tab
  visible. Loading a PLY cleared the completed trainer from memory; its saved
  checkpoint remains available through File > Import Checkpoint.
- Monitor process 32724 completed and exited after preserving the 30k
  checkpoint and screenshot. Its ignored status/progress/log files remain.
  No restart is needed. Installation, source pins and originals are unchanged.
- `documentation/static_desk_002/README.md` has the final report, screenshots,
  before/after previews, held-out examples and reopening instructions. Small
  portable JSON/CSV records and the verified training recipe are also there.
  Root README links this completed real-data validation. Models, data and local
  helpers/logs remain ignored; only useful documentation and the reusable script
  belong in Git. The assistant made no Git commits or pushes.
- Remaining project phases are the 4D reconstruction backend and deformation/
  appearance analysis viewer. This completed static run is a baseline, not
  measured deformation accuracy. Future capture quality work can target dark
  regions, reflective surfaces and more complete viewpoint coverage.

## Dataset 002 cleanup preview: 2026-10-04 — UNSAVED, awaiting user review

- This supersedes the completed-run entry's GUI state only. Training and saved
  originals remain complete and unchanged. No retraining, model export, Git
  commit or push was performed.
- Visible LichtFeld process 11088 has hidden/locked original node
  `static_desk_002_bright_rgb_1p4` (3,000,000 intact) and an editable duplicate
  `workspace_cleanup_preview` (2,848,365 undeleted). Three native undoable
  Gaussian deletion passes removed 151,635 splats. The last operation removed
  192 more bright candidates near a window glare spot.
- User requested keeping the existing oriented crop, removing floaters and
  super-bright glare, then asked to finalize promptly. Crop dimensions and
  transform were preserved as a reversible render filter, not baked. Approximate
  scope is 3 x 3 metres and 4.5 metres high, referenced to a 150 cm desktop.
- Final display uses 3DGUT, SH3, render scale 1, black background, crop filtering
  enabled and crop outline hidden. Initial close desk camera restored. Some
  haze and glare remain; do not claim every artifact is gone. Avoid further
  aggressive edits without review. The native 3DGS crop preview was inconsistent
  after deletion; inspect the crop when changing renderers or preparing export.
- Documentation: `documentation/static_desk_002/CLEANUP_REVIEW.md`, screenshots
  28–34, `cleanup_recipe.json`, `cleanup_window_spot_indices.json`. These small
  records can recreate cleanup against the unchanged bright source PLY if the
  GUI closes. No cleaned model is saved; preserve the live scene for review.
- IMPORTANT: User explicitly asked to see cleanup before saving. Wait for their
  acceptance before saving/exporting a separate cleaned output. Preserve both
  original PLYs and checkpoint. The assistant must not commit or push to Git.
