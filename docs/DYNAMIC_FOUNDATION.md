# Multi-camera dynamic foundation

The first CPU foundation is implemented. It prepares fixed-camera recordings
using measured timestamps and previews temporal analysis on selected point
tracks. The existing COLMAP/LichtFeld static workflow remains available.

The CPU browser demonstration defaults to synthetic selected points. An
isolated GPU environment now trains and renders a **provisional real rigid
yogurt Gaussian pilot**; it has its own live viewer. The real textile point
tracks are partial, and full non-rigid training/temporal Gaussian appearance
remain unfinished. Physical accuracy is unverified. See the
[chronological report and screenshots](../documentation/dynamic_capture_001/README.md)
and [GPU environment/backend notes](DYNAMIC_BACKEND_NOTES.md).

## What works now

| Component | Implemented behavior |
| --- | --- |
| Session setup | Portable camera metadata, recording folders, baseline and scale declarations. |
| Calibration checks | PINHOLE/OPENCV intrinsics, dimensions and a proper world-to-camera rotation. These check structure, not calibration accuracy. |
| Media inspection | FFprobe decoded frame presentation times, color metadata and SHA-256 source fingerprints. |
| Synchronization | Common-cue offset and optional affine clock drift; nearest actual timestamps; reject excessive skew and reused frames. |
| Frame extraction | Selected native-size, coded-orientation, 8-bit RGB PNGs; preserved originals; stale-plan/source checks and overwrite protection. |
| Point analysis | Independent appearance and geometry quantities, reference comparison, fading recent activity and trails. |
| Local preview | Time scrubbing, playback, orbit/zoom, point selection, RGB and separate/combined scalar maps. |

## Environment and launch

The `tf4dgs` Conda environment now contains Python 3.11 and the local editable
package. No PyTorch or research CUDA extensions have been added. From this
repository in VS Code's PowerShell terminal:

```powershell
conda activate tf4dgs
python scripts/TF4DGS.py serve-preview
```

Open <http://127.0.0.1:8094>. Stop that terminal's server with Ctrl+C. If the
assistant-started preview already occupies 8094, use `--port 8096` for a new
instance. It listens only on localhost and serves a read-only API. On this
machine, 8096 currently serves the real yogurt selected features, 8097 the
processing report, 8100 the measured rigid Gaussian renderer and 8101 the
earlier run 04 comparison. The measured pilot uses user dimensions 58 mm
height/95 mm lid diameter and retains 53 supported samples with gaps. The synthetic
demonstration remains available on 8094.

For a new machine, choose one environment recipe, then install the local code:

```powershell
# Portable recipe: let Conda resolve packages for this machine.
conda env create -f environment.yml

# Alternatively, recreate the exact tested Windows 64-bit package builds:
# conda create -n tf4dgs --file environments/tf4dgs-win-64.explicit.txt

conda activate tf4dgs
python -m pip install -e . --no-deps --no-build-isolation
python -m unittest discover -s tests -v
```

The explicit file is a Windows CPU-foundation lock. It excludes the editable
project, native GUI tools and any future GPU trainer. `INSTALLATION.md` still
covers those native tools; do not rerun completed installation steps here.

## Recording locations

The initial local session is already created:

```text
data/dynamic_001/
  session.json
  raw/dji/       # original DJI video
  raw/fuji/      # original Fuji video
  raw/iphone/    # original phone video
  calibration/  # calibration inputs/results for the fixed setup
  baseline/     # unchanged-scene reference captures/reconstruction later
  manifests/    # generated timestamp, sync and extraction records
  frames/       # generated per-camera PNGs
```

Keep original filenames if useful; edit each `video` path in `session.json`
accordingly. `.mov` is supported as well as `.mp4`. Paths use forward slashes
relative to this session folder. The entire `data/` and `outputs/` trees are
ignored by Git. The tracked starting template is
`configs/dynamic_capture_template.json`; it is intentionally incomplete.

Create later sessions with:

```powershell
python scripts/TF4DGS.py init-session data/dynamic_002 --id dynamic_002
```

The command refuses existing folders. Do not reuse a completed extraction's
folder for different video, timing settings or color conversion.

## Timing and extraction

Read [the capture checklist](CAPTURE_CHECKLIST.md) before recording. Then:

1. Put the original videos in the appropriate `raw` folders and update paths
   and confirmed capture settings in `session.json`.
2. Run `probe` to record decoded frame timestamps. It does not extract images.
3. Identify matching visible cues and enter `sync_points` for every camera.
4. Choose the session interval, stable baseline, sampling rate and acceptable
   maximum timestamp span. Run `validate`, `plan`, inspect rejections, then
   `extract` if timing is acceptable.

```powershell
python scripts/TF4DGS.py probe data/dynamic_001/session.json
python scripts/TF4DGS.py validate data/dynamic_001/session.json
python scripts/TF4DGS.py plan data/dynamic_001/session.json
python scripts/TF4DGS.py extract data/dynamic_001/session.json
```

`camera_time_s` means decoded video PTS minus that video's first decoded PTS.
All cameras' `session_time_s` values refer to the same physical cue. An example
for one camera, using two observed cues, is:

```json
"sync_points": [
  {"camera_time_s": 2.500, "session_time_s": 0.000},
  {"camera_time_s": 14.505, "session_time_s": 12.000}
]
```

The transform is `session_time = scale * camera_time + offset`. One cue gives
offset only; two or more allow a drift fit. Two cues fit exactly, so a zero
residual does **not** prove sensor synchronization. Enter estimated cue/timing
uncertainty separately. Rolling shutter and unknown electronic stabilization
remain capture issues, not solved by timestamp matching.

The default 10 samples/s and 35 ms maximum skew are placeholders, not approved
accuracy settings. Choose them after inspecting frame rates and motion speed.
The interval is start-inclusive/end-exclusive. Each accepted bundle uses the
reference camera's actual nearest timestamp; its other views retain their own
timestamps and deltas. `max_skew_s` limits the span between all views. A source
frame is never reused. Missing coverage or excessive skew produces a recorded
rejection rather than an invented/interpolated image.

`max_sample_offset_s` optionally separates reference-camera sampling rounding
from cross-camera `max_skew_s`. For example, native 29.97 FPS exports sampled
at 10 Hz need up to about 16.7 ms of rounding, even when all cameras have
identical exported timestamps. Use 0.017 seconds for sampling offset while
keeping a tighter camera-pairing tolerance if appropriate. When omitted,
sampling retains the original `max_skew_s` tolerance. Neither value proves
sensor synchronization; user-aligned exports still retain cue uncertainty.

Extraction preserves coded pixel dimensions, disables autorotation and does
not relight images. Calibration must match that pixel orientation. This first
extractor writes **8-bit SDR RGB**, not preserved 10-bit or linear analysis
color. PQ/HLG HDR is refused pending a chosen color workflow; unknown or log
transfer metadata requires review. Keep originals for later higher-bit-depth
and cross-camera color handling. [FFprobe documentation](https://www.ffmpeg.org/ffprobe.html)
describes the frame and stream metadata used by the implementation.

Generated manifests and frames are not overwritten. If a command fails,
inspect the recorded partial state; archive affected generated files before
retrying. Extraction checks that its plan still matches the current session
and probes and that the source videos have not changed.

## Calibration and scale contract

Each camera may reference `calibration/<camera_id>.json` with schema 1,
`camera_id`, `image_size: [width,height]`, `model`, `params` and
`world_to_camera: {R,t}`. PINHOLE parameters are `[fx,fy,cx,cy]`; OPENCV adds
`[k1,k2,p1,p2]`. Coordinates follow COLMAP/OpenCV: camera x right, y down, z
forward; `X_camera = R * X_world + t`. All cameras use the same world frame.

The example in `configs/calibration_example.synthetic.json` is deliberately
marked `synthetic_only`. Never copy its invented intrinsics/pose into real
training. An importer/solver and image-size cross-check with real footage are
still pending. `ready_for_training` consequently remains false.

COLMAP scale alone is arbitrary. Set `world.units` to `metres` and supply a
positive `metres_per_unit` only after a known-size target establishes scale.
The point-track file also declares its own scale; no scale is inferred from
the apparent size of an object or copied implicitly from another session.

## Analysis contract

Use `configs/point_tracks_example.synthetic.json` as a small schema example:

```powershell
python scripts/TF4DGS.py serve-preview --tracks configs/point_tracks_example.synthetic.json --port 8096
python scripts/TF4DGS.py analyse configs/point_tracks_example.synthetic.json --frame 2 --mode recent --history 5 --output outputs/dynamic_001/point_analysis.json
```

Point IDs must refer to the same assigned point or validated persistent
Gaussian across time. Independently trained PLY row numbers are not stable
identities. Point status is `tracked`, `new`, `occluded` or `unsupported`.
Missing correspondence returns null, displayed gray; it is not zero change.

- **Since reference:** geometric distance from the selected baseline position;
  appearance distance from baseline normalized linear RGB.
- **Recent activity:** sum of consecutive observed increments within the
  history window, each weighted by `1 - age/history`. Out-and-return motion
  remains visible. This is activity, not velocity, strain or endpoint distance.
- **Trails:** contiguous supported position segments with the same age fade.
  Segments spanning missing observations, new points or the reference boundary
  are omitted. Intervals crossing the window's oldest boundary are omitted
  instead of interpolated.

Appearance uses Euclidean distance in declared linear RGB, not perceptual
DeltaE or isolated pigment change. Reflections and lighting can affect it.
The caller must supply normalized linear colors; `analyse` does not linearize
camera video. Newly deposited slime is a new surface, not automatically the
original material's displacement. Point trajectories are estimates until
correspondence and accuracy have been validated.

The preview defaults to independent side-by-side scales and uses a shared
camera/time for both maps. Its grid is a normalized navigation aid, not a
metric ruler. Legend maxima stay fixed during playback. It is a selected-point
prototype; dense Gaussian rendering and analysis remain a later integration.

## Validation and next implementation

The tests cover offset/drift, variable timestamps, skew/reuse rejection,
baseline/recent differences, return motion, missing/new correspondences,
metric scale, input validation, read-only preview endpoints and real FFmpeg
extraction from three synthetic videos with different frame rates.

Next: validate real calibration and timing, benchmark a compatible dynamic
backend on a short capture, then connect stable tracks and temporal appearance
to the viewer. [Backend notes](DYNAMIC_BACKEND_NOTES.md) record the current
candidate research and the adapter requirements.

The [validation report and genuine preview screenshots](../documentation/dynamic_foundation/README.md)
record the tested synthetic behavior. Raw logs/browser profiles stay ignored.

## User's Git commands

No commits or pushes were performed by the assistant. From this repository in
VS Code PowerShell, the following also includes the completed Necto report
which was awaiting publication alongside the new foundation:

```powershell
git add -- .gitignore README.md INSTALLATION.md INSTALLATION_APPROVALS.md PROJECT_SCOPE.md PROJECT_MEMORY.md environment.yml pyproject.toml src tests configs docs environments scripts/TF4DGS.py documentation
git diff --cached --stat
git commit -m "Add multi-camera temporal foundation and document Necto results"
git push
```

Review the staged summary before committing. Capture data, model outputs,
environments, caches, browser profiles and native tools are ignored. The two
existing source submodule revisions were not changed by this work.
