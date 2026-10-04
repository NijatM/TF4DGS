# Temporal Fields 4D Gaussian Splatting (TF4DGS): Project scope

Scope accepted on 2026-10-02 after the discovery conversation.

Full name: **Temporal Fields 4D Gaussian Splatting**.
Short name / project folder: **TF4DGS**.
Conda environment: **`tf4dgs`**.

The user accepted the scope and requested the installation guide, saved as
`INSTALLATION.md`. Miniconda, CUDA, COLMAP and FFmpeg are installed and their
software checks passed. LichtFeld is built and installed; synthetic training,
checkpoint resume, PLY export and viewer/model loading passed. Reconstruction
quality with the user's footage remains to be validated. Research dependencies
will follow the dynamic backend selection.
Implementation details and the dynamic backend will be selected and tested as
the relevant phase begins.

## Objective

Establish a reliable static Gaussian splatting workflow, then develop dynamic
reconstruction and analysis of appearance and geometry changes over time.
Start with several selected points for motion analysis; eventually extend the
change fields and trajectories across the Gaussian representation.

## Agreed constraints and resources

- Scenes: desk-scale setups, approximately 1-2 m across.
- Dynamic recordings: under one minute.
- Data: the user's own captures and datasets.
- Software: free setup, initially on native Windows. Later platform changes
  are acceptable if they improve the research workflow.
- Compute: NVIDIA RTX A4000 with 16 GB VRAM, approximately 32 GB system RAM.
- Training budget: approximately a couple of hours; achieved accuracy will be
  measured rather than assumed from the training duration.
- Initial static camera: DJI Osmo Action 6.
- Dynamic cameras: DJI Osmo Action 6, Fujifilm X-T5, and iPhone 15 Pro with
  Blackmagic Camera. Fuji lenses available: XF 16-80 mm F4 and XF 33 mm F1.4.
- Phone video: original unedited files, with computational image distortions
  minimized through suitable recording settings; sensor RAW is not required.
- Dynamic cameras remain fixed during each recording. The user's initial
  synchronization plan is manual alignment to one-frame accuracy using an
  event before pouring/inflation.
- Controlled lighting and printed calibration/scale patterns are available.

## Development phases

### 1. Static reconstruction baseline

Use the installation guide to set up and validate a free
native Windows workflow using COLMAP SfM and a LichtFeld Studio source build.
Reuse suitable existing tools and pin a compatible compiler/CUDA combination.

Use an unchanged scene captured with the DJI camera. Produce a calibrated
COLMAP reconstruction, train a static splat, inspect it interactively, and
export a reusable result. Evaluate visible completeness, stability and
rendering quality, including held-out images where practical. Record settings
and results so the workflow can be repeated.

### 2. Controlled multi-camera dynamic prototype

Calibrate each physical camera and unchanged recording mode separately. Use
fixed cameras, overlapping views, a common timing cue, and a stable pre-event
baseline. Verify timing/drift instead of treating manual alignment as exact
sensor synchronization.

Begin with easy appearance-change and geometry-change experiments. Suitable
proposed tests are a thin opaque colorant on a rigid textured target and slow
inflation of a patterned balloon. Progress to water, thicker slime and more
complex combined changes after the initial pipeline is working.

Choose a dynamic implementation that supports both temporal appearance and
geometric changes. LichtFeld is the static baseline; the later dynamic backend
and its integration with the viewer remain implementation research decisions.

### 3. Selected-point maps and trails

Support analysis at several user-assigned points or regions, with stable
correspondences where they can be established. Initially prioritize change
maps and fading trails. Numerical speed and strain are later extensions after
motion tracking is validated.

Keep two scalar quantities separate:

- Appearance-change magnitude at a corresponding location.
- Geometric change, with explicitly labeled tracked-point displacement or
  surface difference depending on the experiment and available correspondence.

For deposited slime, a new surface can produce surface change without being
displacement of the original object's material. Preserve that distinction in
the displayed metric.

### 4. Dense Gaussian analysis

Extend selected-point analysis to change fields and trajectories throughout
the reconstructed Gaussians. Preserve temporal identities/correspondences
where possible and handle newly created, removed, split and occluded Gaussians.

Every analyzed Gaussian needs a value where supported and a validity status
where its reference or correspondence is unavailable. Gaussian-center motion
is an estimated model trajectory; validate its relation to physical material
motion before interpreting it as measured deformation.

## Shared temporal controls

| Mode | Behavior |
| --- | --- |
| Since start | Compare the current state with the first stable frame before the event. |
| Recent activity | Retain changes over an adjustable history window, initially about five seconds, with older highlights and trails fading away. |

These controls apply to appearance and geometry. Fading affects analysis
overlays, not the actual reconstructed RGB or shape at the selected time.

Recent activity must retain intervening motion/change: a point that moves out
and returns may have zero displacement from its initial position while still
having a visible recent trajectory. A future numerical speed quantity will
use traveled distance and elapsed time with validated point correspondence.

## Viewer requirements

- Free camera navigation and time scrubbing/playback.
- Realistic RGB, appearance-change map, geometry-change map, and a combined view.
- Independent legends and scales for appearance and geometry, stable across
  time for meaningful comparisons.
- Adjustable recent-history duration and fading motion trails.
- Point selection for the first analysis prototype, followed by dense fields.
- Clear treatment of unsupported, newly visible or uncertain regions.

The proposed first combined view uses synchronized side-by-side maps. A
single-view overlay is a later presentation option. This is a recommended
default, not a user-approved restriction on the final viewer.

Free navigation does not establish complete observation of later changes on
surfaces hidden from all capture cameras. A static orbital capture can improve
the initial model; changing hidden regions still require uncertainty handling.

## Initial color interpretation

Map observed appearance changes under fixed lighting and capture settings.
For example, paint can alter a target's color, and water can alter its observed
brightness or gloss. Separating pigment changes from reflections, shadows and
refraction is deferred as an additional research problem.

The user's acceptance of the scope adopts this practical starting definition.
More specific separation of wetness, highlights and pigment can be refined
when the first appearance-change experiment is designed.

## Reproducibility and restart handling

Keep source references, version pins, capture settings, calibration, training
settings and validation results with the project. The user wants documentation
and memory suitable for committing/pushing to Git.

TF4DGS tracks LichtFeld and vcpkg as pinned submodules. Trainer/viewer source
modifications will be published by the user to their LichtFeld fork, then
referenced by TF4DGS. The user performs commits and pushes using the commands
and suggested commit messages provided by the assistant. `GIT_SETUP.md`
records the initial fork and first-push workflow.

Before any required restart, update `PROJECT_MEMORY.md` with completed work,
checks, relevant versions/paths, unfinished steps, the restart reason, and
the exact next action. Resume from that checkpoint after the user returns.

Do not store credentials or authentication material in project documentation.

## Current deliverable and next phase

The clean `INSTALLATION.md` requested after scope review is saved in this
folder. The approved static software installation and functional checks are
complete, with no restart required. Next, capture a static scene, reconstruct
it with COLMAP and train/inspect a splat in LichtFeld to establish the quality
baseline. Add the dynamic research stack when its implementation has been
chosen.
