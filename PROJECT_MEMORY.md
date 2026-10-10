# Temporal Fields 4D Gaussian Splatting (TF4DGS): Project memory

Last updated: 2026-10-07 (America/New_York)

## Project identity

- Full name: **Temporal Fields 4D Gaussian Splatting**.
- Short name / repository folder: **TF4DGS**.
- Canonical project path: `C:\Users\mnijat\Desktop\Git\TF4DGS`.
- Conda environment: **`tf4dgs`**.
- Environment recipe: `environment.yml`, Python 3.11 CPU capture/analysis
  foundation; tested builds in `environments/tf4dgs-win-64.explicit.txt`.
- Identity update status: completed. The TF4DGS folder and tf4dgs environment are verified.
- Previous directory holders were identified during the completed rename;
  no folder-rename action remains. Keep the rename helper as a local record.

## Current stage

Latest completed request (2026-10-07): record actual web-viewer videos with a
raised iPhone-side orbit center -> +45 -> center -> -45 -> center, and separate
geometry/observed-color maps. Final documentation is
`documentation/dynamic_capture_001/videos/`: yogurt Gaussian RGB/displacement/
activity (55.1 s, 10.63 MB), yogurt original-calibration point maps (23.9 s,
1.49 MB), measured textile run05 point maps (15.9 s, 0.83 MB). Total MP4s
12.95 MB / 12.35 MiB, H.264 CRF18, 1500x1000 at 30 fps, fast-start, no audio.
Only camera viewpoint is smoothly animated; supported object samples stay
uninterpolated. Textile is 30 early source frames, 28 with >=12 points and two
sparse frames (10/11 points); no dense textile GS or temporal Gaussian color.
`scripts/Validate-WebViewerRecordings.py` passes full decoding, provenance,
SHA, duration, arc/pose coverage and actor visibility. First closer orbit cropped
the final actor position; its capture stays ignored, and the fitted radius
is 0.91 m across all 53 pose bounds and 181 tested arc angles. Browser playback is also checked through
local video page; final evidence is captured in chronological stages 79-84.
Reusable drivers: `scripts/viewer_recordings/`; recorder and encoder scripts
are tracked. Raw screencasts, rejected encoding trials and older presentation
attempts stay ignored in `.local/workflows/dynamic_setup/web_recording_01/`.
Encoding diagnostics: one 5.389 ms paint-event timestamp reversal corrected
by stable presentation sorting; extra EOF hold corrected by output duration.
A textile verification assertion used nonempty frames instead of the stored
>=12-point criterion and was corrected. Models/static installation unchanged.
No recording/encoding worker remains when this checkpoint is complete; own
preview/report servers remain available. No Git publication was performed.


Previous completed request (2026-10-07): reconstruct the yogurt capture's surrounding
table/room as real static Gaussians in the same calibrated world as its moving
actor. Use only these current recordings. The user explicitly forbids merging
any earlier desk/Necto scene; an unsuccessful old-scene registration experiment
(zero registered query views) was abandoned and moved into ignored
`.local/workflows/dynamic_setup/abandoned_static_room_registration_01/`.
No old scene was merged or changed. Keep the camera fixed in world space by
default so the container's movement is visible against the surroundings.
Finish and visually verify yogurt first; only then resume textile reconstruction.
Every major stage, including failures, needs chronological screenshot evidence.
Yogurt whole-scene provisional replay is now visually checked and verified:
`outputs/dynamic_yogurt_001/static_background_03/trained_01` contains 498,531
current-capture static Gaussians (250,261 on the measured z=0 tabletop), joined
with the unchanged 51,913 moving actor IDs in a single CUDA rasterization.
Viewer port 8100 defaults to world-fixed whole-scene iPhone camera; presets,
free orbit/pan/zoom, room visibility, actor fields and trails work. All 53
supported poses rendered; static-only first/last PNGs are byte-identical.
`scripts/Validate-CurrentGaussianScene.py` passed. Documentation through stage
75 includes genuine beginning/end/activity screenshots. Off-table depth uses
the official Depth Anything V2 Small indoor prior; single-view geometry and
hidden surfaces are not a measured room survey. Run02/trained_01 failed to
improve, run02/trained_02 retained ghosting; all trials remain preserved.
The visual/motion gate is satisfied for this supported-frame pilot, so textile
processing may now resume. Keep unsupported yogurt samples as gaps.
Textile retries are now complete: measured session
`data/dynamic_textile_001/session_measured_candidate.json` uses
`calibration/cameras_crop_adjusted_02_measured/`. Run
`outputs/dynamic_textile_001/material_tracking_05_measured` initializes 45
two-view IDs and supports 28 samples, 0-2.9029 s. Run06_RAFT uses the same
observed initial IDs and supports 24 samples, 0-2.5025 s at 1280-pixel flow
resolution; retain it as an unsuccessful coverage comparison. Run05 uses
1920-pixel flow, so this is not a controlled equal-resolution benchmark.
Neither is a complete non-rigid Gaussian reconstruction. Original session
and run04 remain untouched. An initial wrong-environment launch lacked cv2;
relaunching in existing tf4dgs-dynamic resolved it without package changes.
Official RAFT weight source/SHA is tracked in configs/textile_flow_sources.json;
weights stay ignored. No processing worker remains; only existing local
preview/report servers. Latest chronological report: stages 01-78.
`torchvision 0.19.0+cu124` was added only to `tf4dgs-dynamic`; static tools are
untouched. Official source/checkpoint are in ignored `.local/tools`.

Git preparation is complete: the local repository is initialized on `main`,
with LichtFeld and vcpkg registered as pinned submodules at their existing
paths. The user created private `NijatM/TF4DGS` and their LichtFeld fork,
published the packaging fix on `tf4dgs` at `b4e26dc929d23ad8c4cc266e61eb8bf7334ede36`,
and switched the submodule URL to the fork. The user pushed initial TF4DGS
commit `8e826bd113158a71ed8ab3d15e31335572ed91be` to private `NijatM/TF4DGS`;
local `main` tracks `origin/main`. Git setup/publication is complete. The desk
and multi-camera Necto static captures are trained, evaluated and documented;
Necto room cleanup is exported and reopened. The user now requested the
multi-camera dynamic processing of the supplied yogurt and textile recordings.
Verified copies are in `data/dynamic_yogurt_001` and
`data/dynamic_textile_001`. Native 10 Hz pilot extraction is complete (156 and
426 synchronized three-view bundles). The isolated `tf4dgs-dynamic` environment
has Python 3.10.22, torch 2.4.0+cu124 and gsplat 1.5.3+pt24cu124; actual CUDA
rendering and gradients passed. Calibration is provisional, using the measured
35 mm board plus matched lid texture and the user-measured 58 mm container
height. Current measured motion supports 53 samples from 7.2072 to 15.5155
seconds, with gaps. Real rigid Gaussian pilots are trained; the current more
solid measured run06 has 51,913 persistent IDs and uses the measured 95 mm
diameter at initialization. Earlier run04 remains available for comparison.
Full non-rigid textile reconstruction
and time-varying Gaussian appearance remain incomplete.
The chronological record is `documentation/dynamic_capture_001/README.md`;
include numbered actual report screenshots of successes and failed attempts.
Read the latest dynamic checkpoint before repeating setup or processing data.
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
Next, follow `docs/CAPTURE_CHECKLIST.md` for the first controlled dynamic
recording and `docs/DYNAMIC_FOUNDATION.md` for preparation. An isolated gsplat
backend is installed for a rigid moving-container pilot; the non-rigid textile
trainer is still under development. No restart is needed. Update this file
before any required restart.
The earlier requested
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

## Necto multi-camera static run: 2026-10-04 — IN PROGRESS

- User requested autonomous high-quality processing of
  `data/static_multi-camera_Necto_001/images`, preserving native Fuji training
  resolution. Pavilion stayed still with unchanged shape/lighting. Fuji used
  fixed XF 33 mm F1.4. DJI lens/zoom fixed, stabilization off; iPhone lens/zoom
  fixed, stabilization possibly on.
- 298 inputs: DJI floor 1 = 100, floor 2 = 70 (3840x2160); Fuji = 74 landscape
  7728x4344 and 4 portrait 4344x7728; iPhone = 50 at 2160x3840.
  `sfm_images` holds hard links with Fuji orientations grouped separately,
  without pixel changes. Mapping and screenshots are tracked under
  `documentation/static_multi-camera_Necto_001`. Originals remain unchanged.
- Initial visible COLMAP process 18968 finished 244 landscape images, with
  9,047,491 feature rows. At a large portrait image, GPU allocation failed and
  poisoned CUDA. Four portrait Fuji + 50 iPhone images failed. NVIDIA error
  dialog No button was clicked by native GUI automation; the failed process
  closed. Do not repeat successful feature extraction.
- Current visible COLMAP process 10700, main handle 2098940, loaded
  `data/static_multi-camera_Necto_001/project.ini`. Database is `database.db`;
  input is `sfm_images`. CPU SIFT retry started with max size 7728, target 32768,
  8 threads, OPENCV shared per folder. Recovery completed all 298 feature sets,
  11,219,052 descriptor rows. Active cameras: 1/2 DJI floors, 3 Fuji landscape,
  6 Fuji portrait, 7 iPhone; unused camera rows 4/5 are harmless. Initial focal
  values and their assumptions are recorded in the documentation calibration
  JSON; video priors are not fixed. Exhaustive guided matching started through
  the GUI on GPU 0, block size 20, maximum matching features 32768. GPU usage
  initially about 13 GiB. Matching truncates excess descriptors without resizing
  images. Matching completed at 21:14 local in 60.755 minutes: 44,253/44,253
  attempted pairs, 8,673 verified pairs (at least 15 inliers), all 298 images
  in one connected component. Matching summary JSON and completion screenshot
  are in the documentation folder. Do not repeat extraction or matching.
  Read-only progress helper is
  `.local/workflows/static_multi-camera_Necto_001/inspect_database.py`.
- Local logs/contact sheets/UI snapshots:
  `.local/workflows/static_multi-camera_Necto_001`. Recovery logs are
  `colmap_recovery_stdout.log` and `colmap_recovery_stderr.log`. Original
  `colmap_stderr.log` records the GPU allocation failure. GPU memory returned
  to approximately 630 MiB after restart. No Windows restart needed.
- Incremental reconstruction started visibly at 21:17 local. Initial pair
  #171/#176 are Fuji landscape views. Main GUI handle remains 2098940; settings
  dialogs are closed. Mapper CPU threads 16, local BA max 50, global BA max 100,
  focal and distortion refinement enabled, principal points fixed. Project.ini
  was saved through GUI with verified values. Automatic snapshots every 50
  registered frames under `data/static_multi-camera_Necto_001/snapshots`.
  Matching GPU memory was released to about 831 MiB. No training yet.
- Next: finish SfM, export the largest correct model and validate calibration,
  native-resolution preparation, visible LichtFeld
  training and quality checks. Tiling is advertised in Python UI but not yet
  verified implemented by installed trainer; preserve full Fuji resolution
  and check actual memory before selecting fallback.
- Prepared ignored configuration:
  `outputs/static_multi-camera_Necto_001/run_01/training_config_native_3m_ppisp.json`.
  Planned MRNF, SH3, PPISP, 30k iterations, starting 3M capacity, native images,
  save/eval 7k/15k/30k. Choose final capacity after actual native-image VRAM
  checks. Matching itself keeps about 13 GiB allocated; finish/close COLMAP
  before launching LichtFeld to release GPU resources.
- Installed CLI `--config` and Python `load_config_file` read ONLY optimization
  settings, ignoring the nested dataset section. Launch visible LichtFeld with
  explicit `-d`, `-o`, `--resize_factor 1`, `--max-width 0`, `--test-every 8`,
  `--no-fs-cache` in addition to `--config`. Verify accepted native GUI params
  and decoder image sizes before training. CPU-cache defaults reserve max of
  1 GiB or 10% RAM and choose CPU cache only if estimated dataset fits. Planned
  JSON now records these defaults, not unsupported 4 GiB/20% overrides.
  JPEG hardware decoding may bypass that cache. Disable filesystem cache to
  avoid an additional JPEG recompression path. New ignored Monitor-Training.ps1
  is adapted to Necto and calls the existing desk_002 MCP helper; do not run it
  until the new visible training process exists.
- Old desk cleanup GUI is no longer running. Its saved originals and replay
  recipe remain intact; no unsaved cleaned model was exported. No assistant
  commits, pushes, installation changes or source-pin changes were performed.

### Necto continuation: SfM exported and native dataset prepared (2026-10-04)

- User explicitly approved ignoring the four unregistered images. Do not
  spend further time recovering them. Main model completed at 21:52 local in
  35.163 minutes and was exported through GUI into
  `data/static_multi-camera_Necto_001/sparse/0`: 294 views, 553,662 points,
  2,373,914 observations. All 170 DJI, 50 iPhone, 74 Fuji views registered.
- Final audit is `documentation/static_multi-camera_Necto_001/reconstruction_quality.json`.
  Mean stored point error 0.848577 px. Per-group observation means range
  0.6264–0.9939 native pixels, no behind-camera observations. Fuji portrait
  focal ~11310 px agrees with landscape ~11335 px. CHOLMOD solver warnings
  occurred during final BA; later refinement finished and final model audited.
- Undistortion completed through visible COLMAP Dense reconstruction GUI at
  22:12 local in 0.307 min. Exact official bd1fcf6 source confirms default
  max image size -1 and JPEG quality 100. Focal lengths unchanged in pixels;
  only lens-corrected borders/canvas changed. Landscape Fuji 7724x4341,
  portrait Fuji 4333x7715, DJI 3815x2148 / 3806x2145, iPhone 2158x3841.
  Prepared dataset `data/static_multi-camera_Necto_001/undistorted`, with
  flat sparse binaries preserved and copies in sparse/0. COLMAP closed normally.
- LichtFeld visible process 23604 opened at 22:15 local with explicit native
  resolution CLI args, config, no filesystem cache. Dataset loaded successfully:
  257 training and 37 validation cameras. Native params confirm resize_factor=1,
  max_width=0, test_every=8, use_fs_cache=False, 30k iterations, MRNF, SH3,
  3M capacity and PPISP enabled. Local MCP initialized on port 45677.
  Training started through native lf.start_training() at 22:18:28 local.
  At ~22:25, >1400 iterations and ~841k Gaussians, no training errors. Full
  Fuji resolution confirmed by camera.list (7724x4341). GPU memory fluctuates
  roughly 5–10 GB at this early stage. Temporary viewport movement pauses
  resume automatically; leave view idle to improve training throughput.
  Background screenshot/checkpoint monitor PID 31628 is running, saving
  training_monitor.json/training_progress.jsonl under the ignored workflow.
  Portable training_recipe.json and actual training_split.json are in docs;
  nine Fuji views are held out. Excluded images are DSCF1352,1353,1361,1362.
  Continue monitoring checkpoints, native-resolution VRAM and evaluate final
  results. Logs are lichtfeld_stdout/stderr.log
  under the ignored Necto workflow folder. No Git writes by assistant.
- Monitor was extended to record sampled peak GPU memory, copy final metrics
  into docs, list PLY sizes/header vertex counts and capture completion screenshot.
  Its completion JSON labels visual review pending. Monitor restarted without
  stopping trainer. At ~22:38 local, ~4700 iterations / 1.76M Gaussians;
  no errors, sampled GPU peak 9438 MiB. Camera movement pauses can add runtime.
  Checkpoint source writes a temporary file then atomically replaces the final
  resume file; the monitor additionally verifies header magic and saved iteration.
- Important evaluation caveat: installed training/metrics/metrics.cpp applies
  no PPISP correction in validation. Raw canonical-render versus photo scores
  include camera appearance mismatch. Inspect saved GT/render images, including
  native Fuji weave details, rather than treating aggregate PSNR/SSIM as geometry
  accuracy. MCP render.capture with camera_index is REMOVED in this build despite
  stale tool schema. Use native camera.go_to_dataset_camera and live Vulkan GUI
  captures, or the trainer's saved evaluation image pairs.
- 7,000-iteration evaluation completed at 22:49 local: all 37 views evaluated,
  PSNR 19.814346 dB, SSIM 0.755788; 3,000,000 Gaussians. Resumable checkpoint
  with optimizer and PPISP at run_01/checkpoints/checkpoint.resume, preserved
  as checkpoint_07000.resume, both 1,254,038,585 bytes with identical SHA256
  111d0e355f2f78bea4c38472e55de9d240b15b48a05db2760e5a5d0c8df926b2.
  Verified details are in docs/checkpoint_7000_summary.json. Scheduled saves
  only write checkpoints, not PLY; final train loop synchronously saves PLY,
  PPISP companion and final checkpoint before reporting completed. This is
  confirmed in pinned trainer.cpp, so monitor won't race a partial final PLY.
- Training is continuing past 7k, no errors. Early native Fuji comparison
  follows silhouette/seams, but yarn texture remains blurred and canonical
  render is blue. Do not claim final crisp quality yet. Genuine evaluation
  previews/crops are saved as 18_eval_7000_fuji_overview.png (downsampled fit)
  and 19_eval_7000_fuji_native_crop.png (768x768 each, unresized, GT left).
  Pair 9's full 15452x4341 PNG exceeds tool IPC size; use small GDI previews
  or native crops for inspection instead of passing the entire PNG to view_image.
  Actual native dataset camera UID 261 (DSCF1310) is a useful close weave view.
- Halfway evaluation completed at 23:26 local: all 37 views, PSNR 20.256014,
  SSIM 0.771705, 3M Gaussians; checkpoint_15000.resume preserved (1,254,038,585
  bytes). GPU sampled peak 9815 MiB, no errors. Training continues past 16k.
- Evaluator shuffles order: 15k pair 9 is DJI, NOT the same Fuji image as 7k
  pair 9. An invalid crop was overwritten with a proper matched pair. Correct
  match is 15k pair 1; 128x72 GT thumbnail RMS 0.07956/255 vs next 64.5344.
  Exact SHA matching failed due tiny pixel rounding differences, so use low
  pixel RMSE with clear separation. Docs 21/22 now show the corrected Fuji
  overview/native crop; evaluation_match_15000.json records provenance.
  Fine texture improves modestly but remains softer than photo; blue cast
  persists in canonical rendering. Final 30k evaluation pending.
- Added ignored Compare-Evaluation.ps1 for the final comparison. It reads PNG
  dimensions, searches native Fuji candidates, requires unambiguous GT match
  to 7k pair 9, and writes overview/native crops plus matching JSON. Run with
  -Step 30000 -Prefix 31_eval_30000 -ProjectRoot actual TF4DGS path after final
  evaluation. Do NOT assume file index stays constant between evaluations.

### Necto completed training and conservative room cleanup (2026-10-05)

- Training finished successfully at 00:32:13 Boston local time: 30,000 MRNF
  iterations, SH3, 3M Gaussians, PPISP, native images (resize factor 1 / width
  cap 0). Native completion log reports 8,025.3 seconds (~2h14m); completed
  runtime job resets elapsed_seconds to zero, so training_result.json was
  corrected from the log. Sampled peak total GPU usage 9,815 MiB.
- All 37 final held-out images evaluated. Final canonical PSNR 20.342001 dB,
  SSIM 0.775352, best recorded scores with modest improvement after 15k.
  Canonical evaluation omits PPISP. Matched 30k Fuji pair is 2.png; reference
  thumbnail RMSE 0.10725/255 vs next 64.5348. Fine yarn remains softer and
  color cooler in held-out rendering. Calibrated training views show more
  detailed weave; no claim of physical deformation accuracy.
- Original run_01/splat_30000.ply and .ppisp saved, all three checkpoints
  preserved. Final checkpoint 1,230,038,577 bytes; SHA256
  88c28744563d82daa4a3b557691e6435ca882c9db97541db6c10000448ddf7f0.
  Final PLY 744,001,532 bytes, 3M vertices. Export/header/checkpoint audits
  and final comparison screenshots are in the Necto documentation folder.
- Documentation finalization was interrupted by an automatic approval review
  usage-limit failure; the user asked to wait, then continue with cleanup.
  Continued after reset. User confirmed KEEP ROOM and remove artifacts.
- Native GUI duplicate necto_room_cleanup received one undoable deletion pass:
  activated major scale >1.0 scene units AND opacity <0.1, removing 5,031
  large faint candidates. Avoided global opacity pruning to protect thin yarn.
  Original Model remained locked/hidden and 3M undeleted during edits. Dataset
  render binding temporarily switched to duplicate to avoid black rendering;
  training never resumed. No room crop or brightness bake was applied.
- Clean output is outputs/static_multi-camera_Necto_001/run_01/necto_room_clean_01.ply:
  2,994,969 Gaussians, 742,753,844 bytes, SHA256
  877aa5aa390d9605f2db85ca033a01ce10009ad3f74217591e746020582bdbdf.
  Complete retained binary body matches the original byte-for-byte after
  excluding recorded indices. Same-stem .ppisp companion copied intact from
  original; native node export does not automatically save the appearance file.
- Clean PLY reopened successfully in visible LichtFeld PID23604, SH3; native
  logs confirm its 5-camera/257-frame PPISP companion loaded. CURRENT GUI is
  VIEWER MODE with only necto_room_clean_01 and trainer state idle; original
  dataset/camera nodes were cleared by reopening the file. Restore original
  training with saved checkpoint, not by treating this viewer as a live trainer.
  Useful overview eye/target/up/FOV saved in cleaned_overview_camera.json.
- Before/after screenshots 40/42 (overview), 43/44 (weave), 45/46 (room);
  screenshot 47 proves cleaned export reopened. cleanup_recipe.json, exact
  source indices and cleanup_verification.json record the pass. Room and weave
  remain in reviewed views; softness/reflections and unseen-angle artifacts
  can remain. Original metrics were not rerun after deletion. Pre-existing
  splat_30000_CleanupV1.ply was preserved untouched and not assessed.
- No installation changes, source pin changes, commits or pushes. Images,
  checkpoints, PLYs, caches and workflow logs remain ignored. Reports and
  genuine GUI screenshots are ready for the user's own commit/push.

### Multi-camera dynamic CPU foundation (2026-10-05)

- User requested slowly building the multi-camera 4D base while recordings
  are unavailable. Implemented a useful CPU foundation, not a real 4D trainer.
  Static native apps and source pins were preserved: LichtFeld
  b4e26dc929d23ad8c4cc266e61eb8bf7334ede36; vcpkg
  930ecc42b512b564571d767f70775d284a6fa307. No Git commits/pushes or restart.
- Existing empty Conda environment received Python 3.11.16, pip 26.2.1,
  setuptools 84.0.0 and resolved conda-forge CPU dependencies (20 Conda
  packages, ~35.4 MB downloaded). Local package tf4dgs 0.1.0 installed editable
  with no added pip dependencies/no build isolation. `pip check` passed.
  Python executable: C:/Users/mnijat/miniconda3/envs/tf4dgs/python.exe.
  Base Python and LichtFeld bundled Python were not modified.
- `environment.yml` now specifies Python 3.11/pip/setuptools and conda-forge
  plus nodefaults. `environments/tf4dgs-win-64.explicit.txt` records exact
  Windows CPU package URLs, with no machine prefix or credentials. Recreate
  Conda first, then pip install -e . --no-deps --no-build-isolation. No research
  PyTorch/CUDA stack is selected/installed or covered by this lock.
- New source package `src/tf4dgs`, pyproject.toml and scripts/TF4DGS.py provide
  init-session, validate, probe, plan, extract, analyse and serve-preview.
  Pure standard-library Python; native FFmpeg/FFprobe reused. Checks support
  portable paths, fixed cameras, baseline/time/scale metadata and calibration
  structure (PINHOLE/OPENCV, world-to-camera proper rotation). Actual camera
  calibration solving/import and real-data accuracy are not implemented.
- Synchronization uses decoded PTS relative to each video's first frame.
  Shared cues fit offset or affine clock drift. Bundles use actual reference
  timestamps and reject excessive cross-camera timestamp span or reuse of any
  source frame. Plan records accepted/rejected samples and per-view deltas;
  sensor_sync_accuracy_verified remains false. Two cues fit exactly and are
  not an accuracy certificate. 10 Hz/35 ms template values are placeholders.
- Extraction verifies source SHA-256 and plan freshness, refuses existing
  outputs, uses FFmpeg 9's filter argument file and selects decoded indices.
  Native coded dimensions/no autorotation/no resize, 8-bit RGB PNG only.
  PQ/HLG HDR refused until color workflow chosen. Unknown/log transfer needs
  review. Original video remains untouched; cross-camera photometric
  normalization and high-bit-depth analysis are pending. Partial failure
  leaves an in-progress extraction record; inspect/archive before retry.
- Point analysis requires assigned point or declared persistent Gaussian IDs,
  normalized linear RGB and explicit scale. Reference displacement and RGB
  distance are independent. Recent mode is a linearly fading sum of contiguous
  increments within the history window, not speed or strain; trails share the
  fade and never bridge missing/occluded/new identities. Missing values are
  null/gray, not zero. Independent PLY row indices are not stable identities.
- Initial ignored session created at data/dynamic_001/session.json with
  raw/dji, raw/fuji, raw/iphone, calibration, manifests, baseline and frames.
  No videos or real calibration supplied. Local preflight correctly reports
  three missing videos, pending calibration/cues/capture locks and training
  not ready. Keep the template incomplete; do not substitute synthetic poses.
  Tracked configs include capture template and explicitly synthetic
  calibration/point-track examples. data/outputs/.local/egg-info are ignored.
- Local read-only synthetic point preview opened visibly in Edge at
  http://127.0.0.1:8094, hidden server PID32832 at this checkpoint. PID/logs
  under .local/workflows/dynamic_foundation. It may not survive a Windows
  restart/session end; health-check the URL before starting another server.
  Start with conda activate tf4dgs then python scripts/TF4DGS.py serve-preview
  (or --port 8096 if occupied). Ctrl+C stops a foreground server. Preview
  renders points, not splats: RGB, appearance, geometry and both maps; time
  scrub/play, orbit/zoom, point selection, fixed scales and fading trails.
- Final 23 tests passed without skips in ~1.7 seconds. Real FFmpeg test uses
  three 160x96 synthetic videos (12/8/16 FPS), four bundles each; selected PNGs
  matched independent single-frame decode hashes. Includes stale-plan,
  altered-source, HDR and repeat-extraction rejection. Tests also cover drift,
  irregular timestamps, skew/reuse, return motion, new/missing points, metric
  scale and invalid API inputs. Python compilation and Git diff checks passed.
- Isolated headless Edge exercised four view modes at t=4 s, no page errors,
  correct combined visibility/RGB legend hiding and playback restart. Return
  point recent activity 0.875 reconstruction units vs reference displacement
  ~1e-32 (numerical zero). Genuine screenshots/report are in
  documentation/dynamic_foundation; helper, browser profile and detailed logs
  remain ignored. Visible browser also opened, refreshed and screenshot checked.
- Updated README, scope, installation/current-state docs and this memory;
  docs/DYNAMIC_FOUNDATION.md provides commands/contracts/reproducibility and
  user's Git commands; CAPTURE_CHECKLIST.md covers a controlled first capture;
  DYNAMIC_BACKEND_NOTES.md records research and pending adapter requirements.
- Backend research: official 4DGaussians has a temporal SH branch disabled
  by default (no_dshs=True), legacy Python3.7/torch1.13.1+cu116 setup and a
  renderer path needing temporal-feature audit. Not verified Windows/CUDA13
  compatible. Dynamic3DGaussians keeps appearance persistent by design, so
  stock configuration does not match requested changing color. No repository
  cloned/forked/pinned and no claim of completed Gaussian training integration.
- NEXT: await controlled 5–10 s recordings with fixed cameras, shared before
  and after timing cues, stable baseline and board/known scale captures. Probe
  originals, enter measured cues, inspect timing/capture/photometric constraints
  and solve/import common calibration. Benchmark a compatible temporal geometry
  AND appearance backend in isolation (native Windows or later WSL fallback),
  then connect validated point tracks and temporal Gaussian rendering. Preserve
  classic static GUI training throughout; do not restart Necto training.

### Printable ChArUco base targets (2026-10-06)

- User proposed a first yogurt-container translation test using a thin rope
  over the white desk and requested research on a printable marker base.
  Recommended ChArUco, with official OpenCV/ArUco references. User requested
  directly printable PDFs; created both US Letter and US Tabloid/Ledger.
- Final PDFs and matching target JSON are in documentation/reference_markers:
  TF4DGS_ChArUco_US_Letter_8x6_30mm.pdf (11x8.5 inch landscape, 8x6 squares,
  square30mm/marker22mm, 240x180mm pattern); and
  TF4DGS_ChArUco_US_Tabloid_10x6_35mm.pdf (17x11 inch landscape, 10x6,
  square35mm/marker25mm, 350x210mm pattern). Tabloid recommended if supported.
- PDFs use exact-size vector fills, no embedded raster images, seamless black
  modules, print-scaling None preference, and horizontal/vertical 100mm checks.
  Dictionary DICT_5X5_100, borderBits1, legacyPattern=false, top-left black.
  IDs0-23/0-29 overlap: use one chosen board at a time. JSON records geometry,
  dictionary/PDF hashes, package versions and target coordinate convention.
- Delivered PDFs rendered at 240DPI; OpenCV detected all 24/30 markers and
  35/45 ChArUco corners. Maximum expected-coordinate disagreement ~0.17 pixels.
  Page sizes verified within0.001mm, square sizes/counts checked; final previews
  visually inspected under ignored .local/workflows/calibration_boards.
- Reusable generator scripts/Create-CalibrationBoards.py and optional pinned
  configs/board_print_requirements.txt retained. Printing tools installed only
  in ignored .local/tools/board-print-env: OpenCVheadless4.13.0.92,
  reportlab5.0.1, PyMuPDF1.28.2, numpy2.4.6, pillow12.3.0,
  charset-normalizer3.5.2. Main tf4dgs and static native tools unchanged.
- Printing README includes citations, regeneration and user's commit commands;
  root README/capture checklist link the targets. No commits/pushes/restart.
  NEXT: user selects matching paper, prints100%/ActualSize without fitting,
  measures BOTH100mm checks and square intervals, mounts flat/matte/secure.
  Physical print dimensions remain unverified. This is a target definition,
  not camera calibration or proof of metric reconstruction accuracy. Real
  recordings/calibration and 4D GPU backend remain pending.

### Illustrator-editable ChArUco artwork (2026-10-06)

- User requested editable Illustrator files. Illustrator was not found in
  Adobe installation directories, running processes, App Paths, COM or
  uninstall entries. No native .ai file was fabricated or saved locally.
- Added exact-size Letter and Tabloid SVGs beside the verified PDFs, with
  Paper, Checkerboard, Markers, Measurements and Labels groups, named marker
  IDs and live text. SVGs contain vector geometry only. Rendered at 240DPI,
  all24/30 markers and35/45 corners passed; maximum position error ~0.17px.
  Checks/hashes are recorded in editable_artwork_validation.json.
- Create-Native-Illustrator-Boards.jsx contains the original board geometry
  and creates genuine native AI files when run INSIDE Illustrator via
  File > Scripts > Other Script. Five named layers, per-ID marker groups,
  CMYK black fills, live text, locked Paper layer and PDF-compatible saving.
  Refuses existing AI files. Illustrator runtime/export remains untested;
  inspect generated documents and rulers before printing. It recreates the
  originals, not edits made to SVGs. SVGs can instead be opened and saved as
  AI directly in Illustrator.
- Reusable scripts/Create-EditableCalibrationBoards.py and
  scripts/Illustrator-Boards.template.jsx retained. Original PDFs/target JSON
  preserved. Board README explains editing, regeneration and user Git commands.
  Marker bits must remain intact; altered geometry requires updated target
  definition and validation. No main-environment/static-tool changes,
  installations, commits, pushes or restart during this editable-artwork step.

### Reference marker folder organization (2026-10-06)

- User requested a descriptive folder for the PDF/SVG targets and current-stage
  commit/push commands. Renamed documentation/calibration_boards to
  documentation/reference_markers, keeping both PDFs, both SVGs, matching
  target JSON, validation report, Illustrator JSX and instructions together.
- All nine files moved intact with SHA256 checked before/after. Updated root
  README, capture checklist, both generator output defaults and board README
  Git commands. Ignored local preview/tool paths remain unchanged.
- Only the portable reference files, sources, requirements and documentation
  belong in this commit. Data, training results, local tools, environments and
  previews remain ignored. No staging, commits, pushes or source-pin changes
  performed. Native Illustrator runtime remains untested; physical print
  dimensions and camera calibration remain pending.

### First real yogurt/textile processing checkpoint (2026-10-07)

- User supplied D:/Yogurt and D:/Textile, three Premiere-exported videos each.
  Copied all six into ignored data/dynamic_yogurt_001/raw/{dji,fuji,iphone}
  and data/dynamic_textile_001/raw/{dji,fuji,iphone}; SHA-256 copies verified.
  Originals untouched. Both session.json files, source-copy manifests, decoded
  PTS/fingerprints, extraction plans and all failed attempts are retained locally.
- User aligned a dropped-box impact in Premiere at 30 FPS, trimmed/exported
  each camera from one timeline. No originals/calibration capture available.
  Fuji XF33 mm fixed; DJI Natural additionally cropped. Cameras fixed, exposure/
  WB manual, stabilization probably off (unverified). User measured 35 mm board
  squares and confirmed unchanged physical camera/board positions between tests.
  Equal exported timestamps do not certify sensor timing: retain 33.37 ms
  uncertainty. Sources are H.264 High, 8-bit SDR BT.709, 30000/1001 FPS;
  Fuji/iPhone 3840x2160, DJI 1536x2304. Yogurt 467 frames/15.582 s;
  textile 1277/42.609 s. These are exported video inputs, not sensor RAW.
- Native 10 Hz extraction completed: 156 yogurt/426 textile bundles, 468/1278
  PNGs, no resize/exposure change/frame reuse. Independent middle-frame RGB
  comparisons passed for all six streams. Original full-rate videos remain.
  Fixed reference-sampling tolerance (17 ms) separately from camera skew (1 ms).
  Fixed FFmpeg long-selection parser depth with balanced expressions. Earlier
  sparse selection and failed expression outputs were preserved, not deleted.
- Added isolated tf4dgs-dynamic: Python3.10.22, torch2.4.0+cu124,
  gsplat1.5.3+pt24cu124 precompiled official CP310 Windows wheel. GPU render/
  backward and pip check passed. System CUDA13.2.2, main tf4dgs/Python3.11 and
  static native installation remain unchanged; no restart required.
  First Conda recipe attempt hit the default-channel ToS plugin; accepted no
  terms, succeeded using --override-channels --channel conda-forge. Portable
  recipes/locks: environments/tf4dgs-dynamic.yml,
  environments/tf4dgs-dynamic-win-64.explicit.txt,
  configs/dynamic_gpu_win64.lock.txt. Build-machine packaging URL sanitized.
  Official wheel SHA256:
  62fae62e2cf233233527ba890fd322825476118edd4bd27a4e6cb36b1723003e.
- Automatic COLMAP baseline failed: planar verified pairs included repeated-
  marker aliases. Preserved DB/logs; no sparse model fabricated. Centered-crop
  board bootstrap rejected insufficient off-plane support. Rectified actual
  lid texture plus measured board jointly fit provisional square-pixel pinhole
  cameras (zero distortion), 46 material candidates/7 triple-view candidates.
  Held-out board RMS Fuji/iPhone/DJI=1.67/1.15/1.14 px; held-out lid predictions
  in iPhone/DJI=7.45/3.85 px. Estimated lid height56.7 mm; not independently
  verified. Provisional calibration is not a physical accuracy certificate.
- Yogurt calibration: data/dynamic_yogurt_001/calibration/cameras/{id}.json.
  Textile direct transfer failed for DJI (90.34 px board error); corrected only
  export principal-point shifts while preserving physical poses. Textile uses
  calibration/cameras_crop_adjusted/{id}.json. DJI shift(+90.13,-4.77)px;
  corrected board RMS DJI/Fuji/iPhone=1.00/1.51/.92 px. Keep failed transfer.
- Original strict yogurt tracking: outputs/dynamic_yogurt_001/rigid_tracking_01,
  46 assigned features, 46 valid poses/156 samples,9.3093-14.014 s, median
  residual2.89 px. No gap interpolation. Filled-rim tracking attempts02/03 added
  observations but reduced valid poses (34/28); preserve them, do not replace
  the stronger original result. Explicit pixel-outlier pose refinement04
  finished:40 valid frames10.6106-15.2152 s, median inlier residual2.94px.
  Later reach improved but overall coverage did not; keep original01 selected.
  User supplied measured table-to-lid height58 mm and lid diameter95 mm.
  Portable provenance:documentation/dynamic_capture_001/container_measurements.json.
  New board_lid_refinement_02_measured fixes58 mm during fitting;95 mm is an
  excluded-from-fit contour check (Fuji/iPhone/DJI96.64/96.98/94.70 mm).
  Candidate session: data/dynamic_yogurt_001/session_measured_candidate.json.
  Original session/calibration/models are preserved; never mix old canonical
  coordinates or transforms with the new cameras. Measured refit05 was rejected
  for a126-degree lid flip despite low residual. Refit06 from expanded observed
  pixels gives53 supported frames7.2072-15.5155 s,median2.84px,tilt<=7.87deg.
  Tabletop-only trial07 removes tilt/lift but passes only43 frames; retain trial.
  Measured Gaussian05 trained51,913 GS/30k steps,20.82dB on24 held-out crops
  (different split from original04). Visible opacity holes motivated measured
  solid retry06 completed with silhouette0.2/offset0.65mm and is selected.
  outputs/dynamic_yogurt_001/measured_comparison_01 independently renders the
  same24 held-out native crops/masks: alphaMAE0.06395->0.04421(31%lower),
  meanforegroundalpha0.9435->0.9654; PSNR20.82->20.20dB. Keep both models.
  This selection split is not an untouched test or metric-accuracy certificate.
  Textile transfer candidate saved under
  calibration/cameras_crop_adjusted_02_measured; existing session not updated.
- Real rigid Gaussian actor trained, one canonical model with persistent IDs
  and time-dependent rigid transforms. Not independent static PLYs per frame.
  Run02:15,077 Gaussians/3k steps; fixed evaluation screenshot-subset reporting
  error while preserving original summary. Run03:51,469/10k steps, held-out-time
  foreground PSNR21.37dB. Run04:51,469/30k steps, tighter1.5mm offsets/.9mm
  scales,20.82dB; cleaner edges, earlier selected preview. Current preview is
  measured run06; original04 stays as comparison. Models/text remain imperfect.
  Runs: outputs/dynamic_yogurt_001/gaussian_pilot_02,03,04. Best checkpoint,
  canonical_actor.ply/npz, motion.json, comparison images and per-time renders
  saved. PLY is a static snapshot; animation requires NPZ+poses. Training uses
  encoded video RGB, constant Gaussian colors, an unmeasured frustum prior for
  hidden geometry, and approximate automatic masks. No temporal Gaussian color
  or physical strain is claimed. Validation times use the same three cameras
  and select checkpoints; there is no untouched independent test.
- Textile: raw-perspective stereo initialization failed; rectification plus
  marker exclusion initialized39 two-view material candidates. Tracking03/04
  retain>=12 triangulated points only for0-1.7017 s (18/426 samples). Native29.97Hz
  tracking did not materially improve support through hand occlusions/folds.
  outputs/dynamic_textile_001/material_tracking_04 holds the latest partial
  point tracks; full non-rigid Gaussian training remains incomplete. Do not
  turn missing/ambiguous correspondence into a validated dense field.
- Live local GUIs:8100 actual Gaussian renderer (measured solid run06),8101
  earlier run04 comparison,8096 real
  yogurt selected-feature maps,8097 chronological report,8094 earlier synthetic
  point demonstration. Own server/browser PID files/logs in ignored
  .local/workflows/dynamic_setup. Only stop verified task-owned processes.
  scripts/Serve-RigidGaussianPreview.py reopens the actual model; scripts/
  TF4DGS.py serve-preview --tracks outputs/dynamic_yogurt_001/rigid_tracking_01/
  point_tracks.json --port8096 reopens real point analysis. Gaussian viewer:
  RGB/orbit/time, all-Gaussian displacement/activity,35 sampled fading trails;
  no interpolation, gray unsupported recent history. Point viewer alone has
  observed appearance/geometry combined maps. These are different tools.
- Documentation: documentation/dynamic_capture_001/README.md,index.html,
  numbered report screenshots, genuine live-view screenshots and capture
  metadata. Preserve chronological numbering and every failed attempt.
  Retrospective report screenshots are labeled, not fabricated original
  terminal/GUI captures. Actual diagnostic source images are distinguished.
  Fixed UTF16 log decoding, PowerShell manifest array nesting, screenshot image/
  slider readiness and report-tab recovery; failures recorded in the journal.
- Validation at stage43 passed: six independent real-stream pixel comparisons;
  51,469 finite/unit-quaternion/positive-scale Gaussian parameters; PLY matches
  NPZ; stable IDs/pose validity; six live RGB/displacement/activity renders;
  unsupported-frame/invalid-query rejection and missing-history semantics;
  26 CPU foundation tests; git diff --check; no data/models/logs tracked.
  Static pins unchanged: LichtFeldb4e26dc929d23ad8c4cc266e61eb8bf7334ede36,
  vcpkg930ecc42b512b564571d767f70775d284a6fa307. Full validation JSON/logs ignored
  under .local/workflows/dynamic_setup/current_stage_validation.*.
- Measured stage60 verification passed: canonical camera/pose provenance,
  measured actor initialization58/95mm,51,913 finite Gaussian parameters,
  PLY/NPZ agreement,53 supported poses,6 live renders, invalid-frame rejection,
  missing recent-history behavior,26 foundation tests and6 native-pixel checks.
  Result/logs:.local/workflows/dynamic_setup/measured_stage_validation.*.
  Documentation now has60 chronological report screenshots plus7 genuine live
  previews; stage58RGB12.012s and stage59activity13.013s record measured run06.
  Viewer automatically reads matching motion.json and rejects an explicit
  different pose file. No processing worker remains; only own local servers.
- No staging, commits, pushes or Windows restart performed. User owns Git.
  NEXT: measured rigid pass is complete; review current previews and improve
  material correspondence before textile
  deformation and temporal Gaussian appearance. Do not repeat installations.

### Whole-scene yogurt and textile retry checkpoint (2026-10-07)

- Yogurt: current actor06 plus current-capture background03/trained_01;
  51,913 moving and 498,531 static Gaussians. World-fixed iPhone camera default.
  `Validate-CurrentGaussianScene.py` passed all 53 supported time samples,
  static-only first/last identity, measured z=0 plane, fields and camera presets.
- User explicitly forbids merging earlier static scenes. None was merged.
  Rejected registration test/helper live only in the ignored abandoned archive.
- Current-view RGB, motion start/end/activity and all background failures are
  documented chronologically. Depth prior outside the measured plane and
  hidden geometry are not independently metrically verified.
- Textile measured LK run05 is the latest partial track set: 45 initial IDs,
  28 supported samples through 2.9029 s. RAFT run06 (24 through 2.5025 s)
  did not improve coverage in this configuration. Dense textile training and
  Gaussian temporal appearance remain outstanding; never fill occlusion gaps
  as observed deformation.
- All training/tracking workers have completed. Static submodule pins remain
  unchanged. Data, models, weights and logs remain excluded from Git.
- The previous documentation update could not run when automatic approval
  review hit a usage limit; this checkpoint records the completed trials.
- No staging, commit or push performed. User owns Git publication.

### Textile reconstruction revision checkpoint (2026-10-08, active)

- User rejected the sparse textile result and missing RGB reconstruction.
  Actual nonrigid RGB Gaussian reconstruction is now the active task.
- Reviewed original 42.6-second three-camera recordings and failures. Earlier
  masks include board features; sparse point loss/occlusion is unresolved.
- Research: 4C4D, TrackerSplat, Dynamic3DGaussians, SAM2, MASt3R, CoTracker3.
  Local implementation will use existing Windows gsplat rather than replacing
  the working static/PyTorch installation with untested upstream environments.
- Official code clones pinned under ignored .local/tools: SAM2
  0f6515ae853c40420ea8e3dd250f8031bbf03023; CoTracker
  82e02e8029753ad4ef13cf06be7f4fc5facdda4d; MASt3R
  f5209afc300cec36239a7ac992263f36847bbba0 with pinned dust3r/croco.
- scripts/Setup-TextileReconstruction.py prepares official weights and SHA256
  manifest without upgrading torch2.4.0+cu124/gsplat. Dependencies installed;
  official model downloads complete. MASt3R is noncommercial research licensed.
- scripts/Segment-Textile.py implements inspected first-frame prompts and
  SAM2 propagation with a conservative colored-skin exclusion.
- Full SAM2 masks:214 times, all3 cameras; nine times visually reviewed,
  board/hands excluded. outputs/dynamic_textile_001/segmentation_03_video.
- Dense stereo02:7,425 initial samples. Actual native RGB frame02:36,790GS,
  visible yarn/ridges. Folded frame03 has holes and is rejected. Dense
  stereo04_shape_prior adds explicitly inferred neural depth on calibrated
  rays, anchored/corrected by stereo. Fold frame04 improves to57,260GS,
  10ksteps, fittingPSNR34.94/35.80/27.28dB andforegroundalpha~.995.
- CoTracker3 dense_tracking02:700nodes,70/214times>=100 supported; all
  triangulated support lost after20.587s. Full material identity still rejected.
- Selected direction: actual multiview RGB Gaussian keyframe sequence. No
  persistent material-ID/strain claim. Fields compare nearest baseline surface;
  sparse tracked trails remain partial. Color_balance02 uses corresponding
  board pixels/reference Fuji; display alignment, not pigment calibration.
- Nine-time proof completed (621.99s). Real free-orbit fold/upright views passed
  visual review; actual screenshots06–09. Patch fitting trial05 rejected for
  weaker RGB detail (158:31.43/30.62/28.67dB vs native35.6/36.0/30.4dB).
- Active FULL worker PID26828 (verify command before stopping):all2145Hz times,
  gaussian_sequence_04,6000steps cap/time,all-camera32dB early-stop>=3k,
  upsample5,offset8mm,depthprior/colorbalance; native full crops. Reuses MASt3R
  on GPU and trainer process; checkpoints/models/manifest are resumable.
  Logs/PIDs:.local/workflows/dynamic_setup/textile_reconstruction_02.
- Real textile renderer8104, own report8103, dedicated Edge CDP8098.
  current_table02 rejected for off-table plane projection;03 still bakes a
  moving wrist/watch into texture. Corrected04 excludes nearby skin/watches,
  uses>=2 unobstructed samples and brighter observed texture:136,474GS.
  Live8104 renderer and growing sequence use04; screenshot09 verifies cleanup.
- Journal/screen evidence:documentation/dynamic_textile_001; stages01–05
  reports plus06–09 genuine live screenshots. NEXT:document RGB/fold/table/
  patch trials chronologically, monitor full worker to completion, cleanup
  artifact GS if needed, fields/finite model validation, temporal browser video,
  reproducible instructions and final Git hygiene. Do not stop with partial
  training merely to save time. No Git actions. Latest observed12/214 complete.
- Latest full worker still26828, observed20/214 completed. A separate SH1 RGB
  trial PID24500 runs frame158 with 6k cap; do not select it automatically.
  It currently gives similar RGB residuals; compare completed summary/visuals.
  All current sequence04 models are DC RGB; do not mix appearance bases.
- Added conservative cleanup and finite/timeline/render validator scripts.
  Cleanup writes clean_model.npz beside originals; not selected in viewer yet.
  Neutral-knit chroma pruning is specific to gray cloth, not future paint tests.
- Player wall-clock scheduling corrected in HTML; current8104 server caches
  earlier HTML until its next verified task-owned restart. Need final playback
  check after reload/restart; keep true supported keyframes, no interpolation.
- SH1 trial complete:158 fitting34.94/35.81/32.61dB, essentially similar to
  DC native prototype35.30/35.71/32.47. Retain trial; do not change the selected
  appearance model or mix bases. Both source data and geometry remain inferred.
- Cleanup trial comparison on12 native camera/time crops: raw33.78dB mean,
  neutral-chroma-pruned29.48dB (reject); support-pruned33.33dB with a4.28dB
  loss onDJI266 (reject). Neither selected in live viewer. Original fits retained.
  Try opacity-only export or retain raw if any real detail is lost; don't blindly
  prune legitimate dark thread Gaussians. Latest full progress35/214.
- Preserve all earlier attempts. No Git staging, commit, push or restart.

- Active checkpoint at stage13: full worker26828 is healthy, observed86/214
  completed. Continue until all214, not merely representative previews.
- Opacity-only cleanup on12native views changes PSNR by<.001dB, but viewer
  retains raw fitted models; aggressive color/support cleanup stays rejected.
- Renderer now own PID11816 (verify its command before stopping),8104.
  First/recent-reference surface maps supported; wall-clock player is reloaded.
- New Sample-TextileAppearance.py samples balanced recorded pixels with cloth/
  skin and approximate local depth visibility. Own watcherPID3084 follows the
  full worker and writes observed_appearance.npz per completed frame. Gaussian
  component colors were too noisy for meaningful maps; only the RGB renderer
  uses those directly now. Gray map points have no visible recorded sample.
- Genuine browser screenshots10(cleanup journal),11(original field display),
  12(recorded-pixel field revision),13(stretched RGB). Journal now13stages.
  Dedicated README has research, current-state limitations and reproduction.
- Checks:26CPU tests,pip check,source parse,static pins unchanged;83completed
  models plus16mode/time and2recent-reference renders passed observed-field
  checks. Validator now also checks standard binary PLY exports; rerun at end.
- Recording helper for finished textile: Record-TextileGaussianPreview.ps1,
  records actual browser wall-clock paint frames from8104, iPhone-side elevated
  +/-45deg arc. Needs full statuscomplete. Intended two clips: RGB and combined
  maps,1500x1150/H264CRF20. New Validate-TextileGaussianRecordings.py checks
  clips/times/arc/full decode. Clips not recorded yet.
- NEXT: monitor full worker, verify all214/appearance watcher completes, finite/
  PLY/live-render full validation, actual temporal/orbit recordings+compression,
  final docs/summary/Git hygiene. No stage/commit/push/restart.

- Latest mid-run progress115/214, screenshot14 verifies the newly fitted fold
  at21.989s beyond failed tracker coverage. Full worker26828 remains healthy.
  Appearance watcher3084 caught up. Renderer11816 uses recorded pixel maps.
- Validator with standard PLY checks passed101completed models/16mode renders.
  Added Summarize-TextileReconstruction.py to publish portable quality evidence
  only after validation_final.json asserts all214completed andobserved arrays.
  Selected coordinator defaults now match04/native6k/ups5/depthprior/balance02.
- Final remaining: all214complete, final validator/summary, actual RGB+combined
  browser orbit captures, encodeCRF20 and validateclips, completed README/memory
  and final Git hygiene. Do not stop at the partial result. No Git publication.
- Windows transient manifest replacement failed at171/214 after completed336;
  no model loss. Screenshot15 and original traceback/failure JSON preserved.
  Added bounded atomic replace retries; resumed at338 with same settings.
  ACTIVE full worker4920; appearance watcher16520. Renderer11816 is unchanged.
  Logs now full_sequence_resume_01.* andobserved_appearance_resume_01.*.
  Preserve the original failed logs. Current PID files identify live processes.
- A legacy Windows text decoder blocked one checkpoint append. Explicit UTF8
  handling restores the committed memory prefix and retains this task's full
  checkpoint history; the pre-repair file is backed up in the ignored cache.


### Textile reconstruction revision completed (2026-10-08)

- The previous sparse LK/RAFT textile preview had no trained realistic RGB.
  New independent-time RGB Gaussian fitting is complete for all 214 times,
  covering 0 to 42.509133 seconds; median interval 0.2002 s, approximately 5 Hz.
  Native DJI/Fuji/iPhone crop pixels are retained. Selected models remain in
  outputs/dynamic_textile_001/gaussian_sequence_04/frames/<index>/model.npz,
  with standard snapshot.ply exports and recorded-pixel appearance samples.
- All 214 finite models, binary PLYs and observed-appearance arrays passed full
  validation; 16 real mode/time renders, two recent references and seven invalid
  query rejections passed. Portable summary: documentation/dynamic_textile_001/
  reconstruction_summary.json. Median camera fitting PSNR: DJI35.64/Fuji33.23/
  iPhone32.28 dB; these are optimization-camera residuals, not held-out accuracy.
- Final current-session table is current_table_05/table.npz: 164,708 Gaussians
  from all 214 unobstructed mask times, replacing the gaps in context04. No old
  scene merged and no hidden table pixel fabricated. Earlier contexts and
  source sequence before the context update remain preserved in ignored storage.
- Full sequence worker4920 and appearance watcher16520 finished successfully.
  Original Windows lock failure, retry repair and failed logs remain preserved.
  Current renderer is task-owned PID13976 at http://127.0.0.1:8104/; verify its
  command before stopping. It now uses context05 and real fitted RGB. Reopen:
  conda run --no-capture-output -n tf4dgs-dynamic python scripts/Serve-TextileGaussianPreview.py
- Selected SuperSplat export: outputs/dynamic_textile_001/supersplat_export_03.
  Import context/current_table.compressed.ply first, then all rgb_30fps PLYs.
  Timeline30 fps,1277frames,42.566667s; the timeline holds214 reconstructed states.
  It is NOT independently reconstructed30Hz motion and has no material IDs.
  Unique compressed cloth284.41MB plus static context2.68MB; float32 archives
  retained, no Gaussian-count decimation. Repeated files use NTFS hardlinks;
  copying may expand the timeline to1.69GB. Original export01/02 trials retained.
- Verified actual online SuperSplat3.5.2 local-file import, first/fold/lifted/last
  times and both static/animated layers. No upload or publication performed.
  Separating table improved five-second data-swap throughput14.16->23.57/s;
  sustained30swaps/s NOT verified. Compression round-trip: <=0.116mm position,
  <=0.00196 RGB-channel error; four real nonempty render comparisons64.41-66.29dB.
  These are file-compression metrics, not geometric accuracy. All214compressed
  models, float32 archives and1277source-time aliases checked; portable evidence
  in documentation/dynamic_textile_001/supersplat_export_summary.json.
- RGB and combined map videos: documentation/dynamic_textile_001/videos/, with
  README and offline index.html. Final actual browser captures rgb_orbit_02 and
  combined_orbit_02 are ignored. Final videos H264/1500x1150/30fps/CRF20 total
  8.250756MB. RGB displays214/214 times; maps89/214 while retaining wall-clock
  speed. SHA256, timing, full decode, faststart and +/-45degree arc passed.
  Both final MP4s actually played in the browser without errors. Old context04
  videos preserved in .local/workflows/dynamic_setup/textile_reconstruction_02/
  documentation_videos_context04; old point-only capture documentation untouched.
- Chronological journal: documentation/dynamic_textile_001/index.html, stages
  01-33 including failed training/cleanup/context, Windows lock, online wrapper
  targeting, camera-expression and playback-performance attempts. Real browser
  screenshots and diagnostic renders are distinguished. Opening instructions:
  documentation/dynamic_textile_001/README.md and SUPERSPLAT.md.
- Surface maps compare closest earlier reconstructed surfaces (first or recent
  adjustable time window); RGB maps use approximately visible source pixels,
  with unknown gray. These are NOT validated material displacement, strain or
  pigment change. CoTracker trails lose supported material association after
  occlusion. Motion-blurred/occluded frames214/356 retain spikes/ghost geometry;
  source comparison and low residual-quality examples are documented explicitly.
- Existing Torch/gsplat and static installation retained. Research packages,
  source/model hashes and licenses pinned; captures/models/weights/clones/logs
  ignored by Git. No restart, Git staging, commit, push or publication performed.
  Further work: temporal material correspondence, better off-plane calibration,
  true30Hz independent motion fitting and sustained30Hz browser data swaps.

- Final documentation playback correction: simple8103 HTTP preview did not
  support reliable video seeking. Preserve its failure evidence; use new
  loopback-only scripts/Serve-TextileDocumentation.py on8105 for videos/journal.
  Own documentation processPID9056. Three exact byte-range checks pass, and
  both clips actually seek to5s/play beyond5s/decode without errors. Reopen:
  conda run --no-capture-output -n tf4dgs python scripts/Serve-TextileDocumentation.py
  Video page http://127.0.0.1:8105/videos/. Journal now35strictly chronological
  stages; original stage IDs retained as provenance after timestamp ordering.
- Final checks: Python/PowerShell syntax valid,98local documentation links
  resolved,all full model/export/video validations passed,diff whitespace clean,
  no ignored data/outputs/tools/logs tracked, no staged files. Static submodule
  pins remain LichtFeldb4e26dc9 andvcpkg930ecc42. No Git publication performed.

- Final36-stage journal remains chronological. Interactive8104 viewer left on
  realisticRGB, first time, corrected context05 and elevated free orbit; ready
  for user review. Seekable documentation8105 also remains available.

### Commit and downloadable baseline preparation (2026-10-08)

- User wants to commit/push this checkpoint themselves before deciding the next
  dynamic backend. No Git staging, commit, push, release creation or upload by
  Codex. Current branch main, origin NijatM/TF4DGS; previous HEAD bdad39b.
- Clarified that independent textile RGB states are a baseline, not the original
  persistent/continuous deformation objective. Shared deformation, temporal RGB
  and tracking regularization are the next candidate direction; no new trainer
  selected, installed or claimed complete. Existing static pins are preserved.
- Selected models are packaged as GitHub Release assets to avoid Git LFS quota
  and source-history growth. No change to ignore rules or LFS attributes.
  Documentation and the two new standard-library helpers belong in Git.
- Local assets: outputs/release_assets/baseline_2026-10-08/.
  Textile ZIP 283,093,188 bytes: all 214 unique compressed cloth states, the
  selected static context05 and export timing manifest. Float32 textile archives
  stay local. Restore-TextileTimeline.py recreates 1,277 aliases via hardlinks
  or verified copies, without interpolating or inventing material identities.
  Yogurt ZIP 25,835,758 bytes: full actor/background NPZ and PLY, selected run06
  motion/53 supported poses, current-session session/calibration. Its motion
  metadata path separator is normalized for portability; original files unchanged.
- Both ZIP CRC and every selected member SHA-256 verified. Total assets
  308,928,946 bytes; checksums in SHA256SUMS.txt. Tracked portable evidence:
  documentation/baseline_release/package_summary.json. Upload/restore guide:
  docs/BASELINE_RELEASE.md; user release notes in documentation/baseline_release/.
- Models, recordings, environments and packages remain ignored under data/,
  outputs/ and .local/. No LFS paths are configured in this repository. GitHub
  Release uploads are a separate optional user command after source push.
- Fresh extraction check passed with no cross-archive path collisions. Restored
  all 1,277 textile aliases as hardlinks; repeat run validates without rewriting.
  Both full-precision yogurt NPZs match the original source bytes. A temporary
  CUDA viewer on port8106 rendered first/last supported poses from the unpacked
  files without footage; actor51,913/static498,531/53 poses match. Task-owned
  validation viewer stopped afterward; existing viewers remain untouched.
  Evidence: restore_validation.json and yogurt_playback_validation.json in
  documentation/baseline_release/. First metadata draft retained in ignored
  outputs/release_assets/baseline_2026-10-08_metadata_draft/.

### Final demo gallery (2026-10-08)

- User requested documentation/demos with the best final UI and reconstruction-only
  90-degree orbital videos, and confirmed yogurt/textile only. Earlier desk and
  Necto are excluded from this gallery. Source models and recordings are unchanged.
- Build-DemoGallery.py copies the validated final UI clips byte-for-byte and
  encodes clean RGB viewports directly from retained lossless browser PNGs.
  It preserves actual paint times and center/+45/center/-45/center camera motion.
  Yogurt clean selects the complete first RGB phase (348 paints, all53 poses);
  textile clean omits one startup paint with the old viewport, retaining all214
  selected source states. CSS-corner crop removes interface text/controls.
- Four videos: yogurt_ui.mp4 10,630,560 bytes/55.10s; yogurt_reconstruction_orbit.mp4
  2,310,365 bytes/22.70s; textile_ui.mp4 5,446,646 bytes/43.47s;
  textile_reconstruction_orbit.mp4 4,699,518 bytes/43.43s. Total23,087,089 bytes.
  UI copies reuse existing Git content; newly encoded videos total7,009,883 bytes.
  H264/yuv420p/30fps, clean CRF20, no upscaling, faststart. Not new30Hz geometry.
- Full video decoding, SHA256, viewport dimensions, phase/source identities and
  +/-45degree trajectory checks pass. Decoded start/middle/end clean images were
  visually reviewed and show only the reconstructed space. Proof and per-video
  provenance live in documentation/demos/; raw frames/encoding diagnostics stay
  ignored in .local/workflows/dynamic_setup/demo_gallery_01/.
- Gallery index.html is offline; Serve-Demos.py reuses the validated byte-range
  handler and serves only documentation/demos on loopback8107. Screenshot helper
  now allows this dedicated gallery port. No Git staging, commit or push by Codex.
- Actual Edge playback check passed for all four videos: seek5s, play beyond5.4s,
  nonzero decoded frames, no video errors. HTTP206 ranges match all four MP4 bytes.
  Genuine screenshot gallery_review.png and metadata, browser_validation.json
  and range_validation.json are saved in documentation/demos. Chronological
  textile journal stage37 links that genuine gallery screenshot and remains sorted.
- Gallery is task-owned PID26676 at http://127.0.0.1:8107/. Reopen with:
  conda run --no-capture-output -n tf4dgs python scripts/Serve-Demos.py
  Existing reconstruction viewers and source pins were not changed. No training,
  environment installation, restart, Git staging, commit or upload in this task.

### Native 4K demo correction (2026-10-08; supersedes the cropped gallery above)

- User rejected low detail/jagged clean demos and suggested slower rendering
  followed by real-time encoding. Old browser capture averages: yogurt 19.59 fps
  across three modes, max paint gap 3.135 s; textile 22.46 fps, max gap 0.197 s.
- Render-GaussianOrbit.py rasterizes full-precision fitted NPZ models directly
  at 3840 x 2160 with gsplat antialiasing and one render for every 30 fps camera frame.
  Elevated iPhone-side +/-45degree sine orbit; H264/yuv420p CRF 16 slow/faststart.
  Offline encoder waits for each frame; no source-model edit or image enlargement.
- Original source speeds: yogurt 7.2072-15.5155 s in 8.366667 s / 251 frames; textile
  0-42.509133 s in 42.566667 s / 1,277 frames. All 53 supported poses / all 214 fits remain.
  Last state is padded by less than two frames; unsupported yogurt gaps hold.
  The prior 22.7 s yogurt cinematic pose-order stretch is superseded for clean RGB.
- Clean MP4 sizes: yogurt 21,325,401 bytes; textile 44,970,237 bytes. New native
  videos total 66,295,638 bytes; all four gallery MP4s 82,372,844 bytes. Every file
  below 50 MiB. UI clips remain identical to already tracked source videos and
  retain their original recording resolution/timing. No LFS rule added.
- Finalize-NativeDemoGallery.py verifies SHA256, full decoding, native dimensions
  and all exact n/30 presentation timestamps (error < 0.34 microseconds; no missing
  or duplicate frames) before replacing clips. Five exact lossless-render RGB
  compression comparisons average 44.60 dB / 47.77 dB; not reconstruction accuracy.
- Native masters/lossless references/manifests are ignored under
  outputs/demos_native4k_01/. Earlier previews remain in demos_native4k_probe_01/.
  Full rejected gallery/decoded diagnostics remain ignored in
  .local/workflows/dynamic_setup/native_demo_gallery_02/. Compact history and
  genuine earlier screenshot remain tracked under documentation/demos/.
- Four foreground browser samples seek and present 33 frames each over ~1.1 s,
  with zero drops/errors. Validate-DemoPlayback.ps1 repeats that check. Earlier
  hidden-browser tests and screenshot timeouts are documented with actual
  failed-page state and native_playback_attempt_01.png. All four HTTP206 ranges
  match current MP4 bytes. Final screenshot: gallery_review_4k.png.
- Textile journal stages 38-40 record native correction, failed hidden-browser
  check, and verified playback. Native montage is labelled as decoded model
  renders, not a desktop capture. All 40 stages remain in chronological order.
  Initial journal validation hit Python 3.10's inability to parse 7-digit .NET
  fractional seconds; the existing Python 3.11 environment verified original
  timestamps successfully without altering them.
- Geometric continuity remains unresolved: textile has about 5 independent fits
  per second and can pop/flicker; yogurt has 53 supported poses with a 2.002 s gap.
  30 fps camera rendering fixes capture stutter, not these model discontinuities.
  Continuous reconstruction/tracking remains the next model-development phase.
- Gallery: http://127.0.0.1:8107/ (task PID 26676); Serve-Demos.py provides seekable
  loopback playback. No source-pin/environment changes, training, restart,
  Git staging, commit, push or upload. The user owns publication.

### Matched continuous-model pilots (2026-10-08 local; journal timestamps UTC)

- User authorized short action tests of both 4DGaussians and 4C4D for yogurt and
  textile, then required textile hands to be reconstructed. All four 6000-update
  pilot_01 runs completed. Textile masks include hands and arms with the same
  foreground priority as cloth; the common first-frame seed was rebuilt before
  both full textile runs. No old unrelated scene was merged.
- Fixed source intervals: yogurt native source frames330-419 / PTS11.011000-
  13.980633s; textile587-676 /19.586233-22.555867s. Native30000/1001fps,
  90 frames, train local indices modulo6 other than5 / test modulo6=5.
  Three cameras yield225 training/45 held-out images per run. Pixel-center
  calibrated crops maxedge1280; iPhone1280x616, Fuji1280x736, DJI1096x1280.
  Exact inputs/hashes/transformed cameras are documentation/temporal_benchmark_001/
  pinned_inputs.json and ignored data/temporal_benchmark_001/*/manifest.json.
- Official sources: .local/research/4DGaussians at843d5ac636c37e4b611242287754f3d4ed150144;
  .local/research/4C4D ated6a3cb69782c4147151b3898944bc38132bae00. Isolated
  Conda base .local/envs/temporal-base (Python3.10.22/Torch2.9.1+cu130), child
  venvs .local/envs/4dgaussians and .local/envs/4c4d prevent incompatible rasterizer
  extension name collisions. CUDA13.2, MSVC14.44.35207, SDK10.0.26100.0.
  Existing tf4dgs/static and tf4dgs-dynamic are preserved; no reboot needed.
- Windows patches: CUDA13 /Zc:preprocessor; tensor-only headers in CUDA translation
  units avoid PyTorch/NVCC compiled-autograd header collisions; Windows optimization
  flags; lazy unused pointops imports. Mathematical CUDA kernels unchanged.
  Source patches, environment recipe/observed freeze and setup commands are tracked
  candidates. Raw clones, compiled extensions, envs and logs stay ignored.
- Common shared adapter Train-TemporalBenchmark.py uses official Gaussian model
  classes/renderers with heterogeneous calibrated cameras. It avoids the upstream
  square loader and Windows data-loader assumptions. Smaller 4DGS grids,
  180000-Gaussian cap and first-frame XYZ/RGB initialization are explicit pilot
  choices; this is not a reproduction of published paper evaluations.
- Shared initial seeds: yogurt40000 points SHAecdbf2043da88bd9e54b1638c2192fb2d0191f1ab145d83e791dd715755fac4f;
  textile35338 SHA384213743256162cf878c656593a5babef6fff501fcccd255a96ed7fac7dafb9.
  Textile bundle196 is exactly source587/19.586233s, not raw source index196.
  New hand/cloth dense seed has793 accepted stereo anchors and7930 registered
  inferred neural-prior points before ROI clipping, combined with existing first
  cloth cloud/current table. No subsequent poses/geometry supplied to training.
  Yogurt uses canonical actor in first tracked pose/current table, same capture
  positions confirmed by user. RGB mask transport is inferred2D flow, not motion
  ground truth. Off-board calibration and one-frame physical sync remain unverified.
- Optimization checkpoint timings and temporal-holdout scores:
  yogurt4DGS542.5s/180000/28.19dB/.948SSIM/2.20GiB peak;
  yogurt4C4D327.2s/179651/32.16dB/.962/1.57GiB;
  textile4DGS453.2s/88647/22.94dB/.814/1.36GiB;
  textile4C4D351.4s/180000/24.35dB/.826/1.54GiB.
  Textile cloth+hand foregroundPSNR21.89/22.85. These are image scores, not
  independently measured metric geometry. 4C4D is stronger within these pilots;
  both textile results remain blurred/ghosted, and 4DGS novel-view orbit breaks
  down severely. Do not label pristine or replace earlier selected demos.
- Outputs: outputs/temporal_benchmark_001/<method>/<dataset>/pilot_01/checkpoint.pth
  includes optimizer/RNG; continuous_model.pth includes inference weights/cameras.
  Model sizes4DGS yogurt54,944,873B/textile33,294,057B;4C4D yogurt115,703,975B/
  textile115,928,999B. All remain ignored, no LFS. Decoder Render-ContinuousTemporal.py
  needs the matching child Python and native source/extension, not training footage.
  All four decoded reference images match saved training render byte-for-byte.
  Models support arbitrary time queries; not animated-PLY/SuperSplat-compatible.
  Gaussian motion/lifetimes do not establish material identity or metric strain.
- Compact evidence includes native29.97fps fixed/orbit/source-comparison clips
  and directly queried exact30fps orbits,90 frames each. All16 fully decode,
  presentation cadence error<1us, HTTP206 ranges match local bytes. Each of12
  browser files passed individual in-view1.1s warm playback with zero drops.
  Native duration3.003s vs30fps3.000s; encoded cadence is not CUDA throughput proof.
- Full failed setup/export/capture history is chronological in
  documentation/temporal_benchmark_001/README.md and journal.json. Failures include
  MMCV build isolation/pkg_resources, CUDA/MSVC headers, AABB initialization,
  mask-rate assumption, inactive headed-browser capture, live-panel punctuation,
  BOM JSON video export, startup drops and offscreen callbacks. Original logs
  ignored; actual browser screenshots/capture state retained, headless vs visible
  clearly labeled. Final visible comparison screenshot033_visible_textile_comparison.png.
- Documentation report/comparison local server loopback8108, PID26092. Restart:
  tf4dgs Python scripts/Temporal-BenchmarkReport.py --serve; open
  http://127.0.0.1:8108/comparison.html. Dedicated headed Edge CDP8098 and headless
  report Edge8099 are task browsers. Earlier8104/8105/8107 services preserved.
  New report reuses existing byte-range handler; no external content/CDN.
- Static source pins unchanged: LichtFeldb4e26dc929d23ad8c4cc266e61eb8bf7334ede36;
  vcpkg930ecc42b512b564571d767f70775d284a6fa307. Git commits/pushes/uploads,
  staging and repository creation remain exclusively the user's responsibility.
  No restart, Git mutation, upload or release in this task. Full-duration and
  high-quality textile deformation analysis still require further work.


### Whole-scene 4C4D refinement in progress (2026-10-09)

- User approved all longer-training/parameter/resolution recommendations and requires
  subject, hands, board, table and visible surroundings in one joint scene. No
  separate/frozen base or previous actor/table is imported. New experiment
  configs/4c4d_scene_001.json; data/outputs/documentation under 4c4d_scene_001.
- Original reference intervals preserved: yogurt source330-419 /11.011-13.980633s,
  textile587-676 /19.586233-22.555867s. Full frames, not the earlier crops.
- Fresh initial120000-point clouds from first whole frames, calibrated SIFT/MASt3R
  stereo plus explicitly registered inferred depth. Yogurt10277 stereo/109723 prior,
  textile3289 stereo/116711 prior after filtering/sampling. No independent metric
  accuracy is claimed. No previous actor/table or neural later-frame geometry supplied.
- Camera sync +/-2-frame audit completed on training timestamps32/62. Textile Fuji
  favors0; DJI is inconsistent. Yogurt Fuji favors -1/-2, but this correspondence
  diagnostic alone does not certify physical timing; original timestamps retained.
  Ordinary SIFT matches are sparse/repeated and unreliable for off-board calibration.
- Planned30k horizon with10k/12k/20k/30k checkpoints,450k cap/growth until15k.
  Three matched presets: baseline, slower time/rotation, gentler opacity decay.
  Branches start from identical10k checkpoint/RNG and compare at12k; selected run
  continues to30k. Then1920/3840 full-frame4000-update stages,600k cap, lower rates.
  Native memory fallback2560 recorded if needed. Temporal holdouts used for
  selection become validation, not an independent final test. All source/model files
  remain ignored and existing pilot/demos/static tools preserved.
- New report loopback8109 PID33932: Temporal-BenchmarkReport.py --docs
  documentation/4c4d_scene_001 --port8109 --serve (arguments separated in commands).
  Existing8108 comparison/8104/8105/8107 preserved. New report visible in dedicated
  Edge8098; headless capture8099. First preparation screenshots saved.
- Scripts: Prepare-4C4DScene.py, Initialize-4C4DScene.py, Audit-4C4DSceneSync.py,
  Train-4C4DScene.py. Full training/resolution stages not completed yet.
  User alone handles staging, commits, pushes and uploads. No reboot required.

- Progress: textile baseline_01 completed12000 updates (30k schedule, full
  frames),450000 Gaussians,23.5682dB whole-frame/22.6943dB motion-priority
  validation,SSIM.833818,peak3.89153GiB. Its10000 checkpoint scores24.0060/
  22.7743dB and is immutable for matched branches. The12000 result did not
  consistently improve; retain all milestones and select by actual evidence.
  Yogurt baseline is now training to12000 in the same sequential job.
- Dedicated visible checkpoint gallery: http://127.0.0.1:8109/comparison.html.
  Build-4C4DSceneReport.py collects actual checkpoints. Guide:
  docs/4C4D_WHOLE_SCENE.md. Tuning runner: Run-4C4DSceneTuning.ps1 (matched
  baseline10000 parent,2k continuation per alternative preset). Viewer8110
  script exists but selected registry is not created and it is not running yet.
  Native1920/3840 inputs are complete. Long continuations/refinement remain
  outstanding; do not report final models ready.
- Future training invocations record10k/20k checkpoints/screenshots themselves;
  wrapper records each stop or failure. First textile process preceded this
  addition, so its10k stage was documented manually. An initially mistyped
  report score was corrected from saved metrics; the original screenshot and
  corrected screenshot remain labeled in the journal.

- Matched tuning finished: textile baseline23.568/22.694dB,slow22.947/22.581,
  gentle23.662/22.680,extra fast_time23.162/22.219 (whole/motion). Baseline
  selected; all textile views still streaked. Yogurt baseline30.318/26.694,
  slow30.697/27.678,gentle31.179/26.865; slow selected for moving-object quality.
  Exact choices/candidate metric hashes in documentation/4c4d_scene_001/selection.json.
  Both selected runs now resume to30000 in exec session23945 via
  scripts/Continue-4C4DScene.ps1, sequential textile then yogurt. At this update
  textile is approximately14000. All final resolution stages remain pending.
- Resolution checkpoints2000/4000 and CPU image cache5120MiB added. Measured
  workstation RAM31.7GiB with15.67GiB free; cache is bounded by actual image
  bytes and270 images. Uses the same pixels; no added dependency. No model
  trajectory change from the cache. Earlier project GPU preview13976 on8104
  was positively identified and paused; this freed approximately367MiB.
  Restore with tf4dgs-dynamic Python scripts/Serve-TextileGaussianPreview.py
  only when needed. CPU docs8103/8105/report8108/demos8107 remain running.
- Inference export tool now accepts --crf (default17; new final clips planned15)
  and explicitly encodes BT709 frame/container tags. Two-frame preflight passed;
  initial missing transfer/primaries tags were corrected and documented. Exact
  30fps/native4K final video generation and continuous-viewer8110 checks are
  still outstanding. Validate-4C4DSceneEvidence.py will check real final files.

## 2026-10-09 — confirmed recipes and full-recording training started

- This entry supersedes the earlier statement that session23945 is running.
  It failed at update20500 on Windows replacement of browser-read
  live_progress.json. The immutable20k textile checkpoint remains safe:
  whole/motion PSNR25.95274455/24.04601364dB. Short30k continuations are closed;
  yogurt30k never started. Failure and closing-stage screenshots are retained.
  Shared atomic JSON writes now use unique temp names and bounded retries.
- User authorized finishing short experiments, testing5–10 hypotheses and
  starting full training; explicitly reaffirmed full training on2026-10-09.
  Eight hypotheses, nine screening trials, a900k follow-up and eight45-image
  confirmations completed without a training failure. A seed-time SIFT pair
  with fewer than8 matches failed; its log/screenshots are recorded. The
  initializer now records insufficient SIFT support and continues with
  calibrated MASt3R. All previous experiments and static tools are preserved.
- Exact evidence/configuration: configs/4c4d_hypotheses_001.json and
  documentation/4c4d_hypotheses_001/{HYPOTHESES.md,RESULTS.md,selection.json,
  comparison.html,journal.json}. Each trial starts at the same immutable10k
  whole-scene checkpoint/RNG and runs600updates. Screen uses9validation
  images; confirmations use45. Do not compare scores across these scopes.
- Textile winner: point_capacity,600000Gaussians,baseline motion/decay rates.
  Confirmation whole/motion25.48057098/23.58763627dB versus control
  23.60640466/22.77447014(+1.8742/+0.8132dB),SSIM.86276371. Combination
  did not beat capacity alone;900k was worse. Yogurt winner: control450000,
  slow_motion preset,timeLRfactor.5/rotation.7,whole/motion31.13026869/
  27.15968030dB. Extra loss/SH/seed changes are not carried into full training.
  Textile streaks/novel-view errors remain; no pristine result is claimed.
- Full input probe: yogurt467frames/camera,15.582233s; textile1277frames/
  camera,42.609233s. All6streams30000/1001fps. Common source index intervals
  0–466/0–1276. Full frames at1280/1920/native3840 are completely extracted,
  hashed and calibrated under ignored data/4c4d_full_001. DJI native1536x2304;
  Fuji/iPhone3840x2160. Original videos and Premiere synchronization unchanged.
- Selected reproducible config: configs/4c4d_full_001.json. Fresh single
  whole-scene SIFT/MASt3R/inferred-depth clouds from training source330yogurt /
  588textile,120kpoints each,uniform initial temporal centers. Physical sigma
  retained from3s trial (1.328s); temporal-centerLR scaled by3s/full span.
  All primitives/visible surroundings/hands stay jointly trainable. No old
  model, separate base or frozen background is merged. Multi-time injection
  was rejected; optional experimental code is not the selected recipe.
- Both full models completed100-update finite-forward/backward smoke checks,
  optimizer/RNG checkpoints and inference packets. Projection max errors
  textile DJI.000134/Fuji.004303/iPhone.000151px; yogurt.000213/.002290/.000138px.
  These test matrix consistency, not independent physical calibration accuracy.
  Training-image counts3195textile/1170yogurt; temporal validation withheld.
- Long worker STARTED2026-10-09T18:46:44.7383019Z,PID33372:
  .local/envs/temporal-base/python.exe scripts/Run-4C4DFullTraining.py --stage train.
  Hidden detached process, sequential textile then yogurt,60000updates each
  at1280, checkpoints every1000, major scored/evidence milestones. Then8000
  updates1920,8000native3840(with actualOOM fallback2560),4000all-frame
  production fit per model. Final fitted scores are not held-out validation.
  Process metadata ignored .local/workflows/4c4d_full_worker.json; parent logs
  .local/workflows/4c4d_full_worker.{out,err}.log; child logs in4c4d_full_001/.
- Active report server PID34640,port8109,documentation/4c4d_full_001.
  Dedicated EdgeCDP8098visible/8099headless records chronological stage shots.
  Live status/pipeline_state.json/journal.json are in that folder. This worker
  runs independently of the chat. Check actual PID/command/current JSON/logs
  before resuming; never launch another GPU worker against its output directory.
- Recovery if worker is absent: run scripts/Run-4C4DFullTraining.py --stage train
  using temporal-basePython from actual repo TF4DGS. Completed stages skip;
  interrupted stages restore checkpoint optimizer/RNG. No Windows restart.
  Final model registry and interactive8110launch remain pending; guide
  docs/4C4D_FULL_TRAINING.md explains stages and quality-review limits.
- No Git files were staged, committed or pushed. Data/models/cache/envs/logs
  remain ignored; useful configs/scripts/documentation stay available to commit.

### Textile checkpoint preview requested during full training

- User asked where to inspect textile in the4D viewer. Full worker33372 is
  still active, main trainer36620/25012; live progress32100/60000 and GPU
  nearly full (~15934/16376MiB). Peak allocated rose to15.56GiB, with slow
  updates; do not start another CUDA process concurrently. Investigate this
  growth/quality after viewer inspection rather than claiming convergence.
- Interactive8110 is not running. Report8109 remains available. Asked user
  whether to temporarily pause training for interactive viewing or keep it
  running. Do not stop/restart the training worker without that choice.
- CPU-only scripts/Export-4C4DCheckpointPreview.py preserves a saved checkpoint
  via a transient hardlink and maps the pinned official4D capture tuple to the
  same inference fields, without CUDA. It exported step32000,599996Gaussians,
  edge1280,full42.576s model span (42.609s capture including final frame).
  Immutable packet: outputs/4c4d_full_001/previews/textile/
  step_032000_continuous_model.pth, SHA256
  250224c3b53c5f77f05d4126db173b2e8ec9198aea564ec2f8579838b28bc06c.
  Ignored registry: outputs/4c4d_full_001/preview_models.json. Metadata saved
  documentation/4c4d_full_001/textile_preview_export.json.
- Viewer now handles a textile-only registry and labels intermediate step/
  trained edge. After safely pausing the verified worker/trainer at a saved
  checkpoint, launch4c4dPython scripts/Serve-4C4DScene.py --models
  outputs/4c4d_full_001/preview_models.json and validate metadata/render on8110.
  Verify CPU-export decoder output before calling it ready; GPU render check
  has not been done. It is not a final or native4K-trained result.
- Latest completed full-duration validation at20k is16.0028dB whole /17.9526dB
  motion,SSIM.69850. Full duration differs from3s tests; don't compare these
  as matched scores or describe the current fabric as pristine.

### Full-duration 4C4D experiment ended at user request

- User inspected the textile preview and rejected the reconstruction as a failure.
  This supersedes the running/paused state described above. Do not resume this
  full-training pipeline or start yogurt/refinement without new user direction.
- Training had already stopped. Verified and stopped only the preview viewer
  processes 32844/33108; no active full-training or scene-training worker found.
- Last saved textile checkpoint: 32000 updates, 599996 Gaussians, edge1280.
  Last unsaved progress: 32500. Native-resolution refinement was not reached.
  Yogurt full-duration training remains at its initial smoke-test checkpoint.
- Retain footage, models/checkpoints, configuration, failure evidence and logs
  for diagnosis. The complete-duration cloth remains blurry with streaks and
  does not meet the requested reconstruction quality. Successful HTTP playback
  checks establish viewer function only, not reconstruction quality.
- Review evidence: documentation/4c4d_full_001/textile_step_032000_viewer_20s.png,
  textile_step_032000_interactive_viewer_visible.png,
  textile_step_032000_playback_verified_visible.png,
  textile_step_032000_orbit_verified_visible.png. Failure is recorded in the
  chronological report and pipeline status. Static installation is preserved.
- No Git staging, commits or pushes were performed.
