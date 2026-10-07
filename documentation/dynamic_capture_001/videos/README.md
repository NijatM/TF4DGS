# Browser recordings: yogurt and textile

Open [the video page](index.html), or the live report server at
<http://127.0.0.1:8097/videos/>. All three MP4s play without the model files.
Recorded 2026-10-07 from the actual project web viewers.

| Recording | Duration | Size | Contents and limits |
| --- | --- | --- | --- |
| [Yogurt: elevated Gaussian orbit](yogurt_gaussian_orbit.mp4) | 55.1 s | 10.63 MB | Actual Gaussian scene: RGB, reference displacement, then three-second fading motion activity. Each mode sweeps center, +45 degrees, center, -45 degrees, center, near the raised iPhone-side viewpoint. Static surroundings remain RGB. |
| [Yogurt: geometry and observed appearance](yogurt_geometry_and_appearance.mp4) | 23.9 s | 1.49 MB | Observed lid-point maps side by side, with reference and recent comparisons and a +/-45-degree point-map orbit. Original provisional tracking calibration, source 9.3093-14.014 s, 46 supported frames. Color is sampled video appearance; Gaussian colors remain fixed. |
| [Textile: partial geometry and observed appearance](textile_geometry_and_appearance.mp4) | 15.9 s | 0.83 MB | Measured run05 point maps with reference and recent comparisons and a +/-45-degree point-map orbit. Source 0-2.9029 s: 28 frames have at least 12 points; two sparse frames retain 10 and 11 genuine points. This is a partial tracking preview; dense non-rigid Gaussian reconstruction is unfinished. |

Together the MP4s are **12.95 MB**
(12.35 MiB). H.264 CRF18 preserves clear visual
quality at 1500 x 1000 with 30 fps output and fast-start headers. This is
high-quality lossy compression, not mathematical losslessness. Source photos,
training models and recordings were not resized or recompressed.

Camera animation is captured at actual browser wall-clock speed. The visible
source time may advance unevenly and jump unsupported samples; repeated
supported poses allow a smoother camera arc. No object poses or occluded
material points were invented between observations. Point-map projection is
separate from the Gaussian camera and does not register the older yogurt
analysis into the measured Gaussian scene.

The Gaussian orbit uses 51,913 actor Gaussians and 498,531 current-capture
static surroundings Gaussians. Its arc is centered at azimuth 95.137965 degrees,
elevation 42.555069 degrees, radius 0.91 m. Compared with the calibrated
iPhone position about the same target, elevation is raised by 12 degrees and
radius is fitted to keep all 53 supported actor bounding boxes and the full
marker board visible throughout the arc. A first closer orbit cropped the
container near its final position and was retained only in the ignored cache. Off-table geometry and unseen surfaces
remain approximate. Displacement includes rigid translation/rotation, not
material strain. Recent maps/trails are fading sums, not speed. Observed color
can include shadows and view/lighting changes; it is not calibrated pigment
change or a trained time-varying Gaussian color field.

[Validation](validation.json) checks full decoding, dimensions, codec,
fast-start layout, SHA-256, duration error below two output frames, source
sample identity and all 53 supported yogurt poses in each arc. Decoded
beginning/middle/end frames were visually reviewed. All three clips also
seek, decode and advance successfully in the actual browser; see the
[live video-library screenshot](../84_live_video_library.png). PNG/video comparison
scores are indicative only because a seek can select an adjacent paint event;
they are not a scientific reconstruction-quality score.

Initial fixed-view capture, small point-map framing attempts, and rejected
encoding trials are preserved in ignored
`.local/workflows/dynamic_setup/web_recording_01/`. One browser paint event
arrived 5.389 ms out of timestamp order. Sorting by actual paint timestamp
preserves every raw event. An extra final hold was rejected by the duration
check; explicit output duration corrected it. The initial textile validation
assertion used nonempty frames rather than the recorded >=12-point criterion;
correcting the check matches the existing run05 summary. These diagnostics
are recorded in chronological stages 79-84; models were unchanged.

Only these compact final videos, posters, manifests and documentation are
intended for Git. Raw lossless PNG captures, earlier presentations, rejected
MP4s and complete logs remain ignored. Reproduction instructions are in
[scripts/viewer_recordings](../../../scripts/viewer_recordings/README.md).

Implementation references: [Chrome DevTools screencast](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-startScreencast)
and [FFmpeg concat format](https://ffmpeg.org/ffmpeg-formats.html#concat-1).
