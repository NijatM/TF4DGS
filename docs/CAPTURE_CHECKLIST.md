# First controlled three-camera recording

Verified [Letter and Tabloid ChArUco PDFs](../documentation/reference_markers/README.md)
are ready to print for calibration and the white-desk reference base. Print at
actual size and measure the scale checks before using their nominal dimensions.

Start with a 5–10 second event plus a quiet period before and after. Use a
rigid matte target with slow opaque color change, or a patterned balloon with
slow inflation. Keep water/glossy slime for later tests. These are initial
experiment choices, not guarantees of reconstruction accuracy.

1. Fix DJI, Fuji and iPhone on supports with overlapping views of the target.
   A triangle of viewpoints is a useful starting arrangement; keep the actual
   event visible to every camera. Three cameras provide sparse coverage, so
   hidden changing surfaces may remain uncertain when viewing from elsewhere.
2. Use one lens/view mode per device. The Fuji XF 33 mm is a straightforward
   fixed-lens starting point if it frames the full event. Choose comparable
   frame rates where supported and enough light for sharp individual frames.
   Avoid digital zoom, lens switching, autofocus breathing and camera movement.
3. Disable electronic stabilization where available; also record any optical
   stabilization setting. Lock exposure, ISO/shutter, focus and white balance
   where the recording mode permits. Record the actual settings rather than
   assuming the app enforces them. For the first test, ordinary SDR is easier
   to validate than mixed HDR/log capture.
4. Use steady lighting and leave the target/background unchanged while
   calibrating. Record clear calibration-board views in each camera at several
   board positions/orientations, without changing camera pose, lens, zoom,
   focus, resolution or recording orientation. Include a shared fixed pattern
   or markers and a known-size reference to establish common pose and scale.
5. Keep the complete original videos. Start all recordings, show a common
   visible timing cue, wait for a stable baseline, perform the event, then
   show another common cue before stopping. A cue visible to all three cameras
   is better evidence than relying only on independently recorded audio.
6. Avoid blocking the target with the pouring hand/container for most of the
   event. Keep the background still. Record a short unchanged-scene orbital
   capture separately if practical; it can help initialize the static model.
   It does not reveal how unobserved surfaces change during the event.
7. Save original files under `data/dynamic_001/raw/dji`, `raw/fuji` and
   `raw/iphone`; save board/scale captures under `calibration`. Keep originals
   uncut: the software can select a common time interval without destructive
   edits. Update `session.json` paths and capture settings afterwards.

Also note board dimensions, approximate target size, lens/view mode, image
orientation, FPS, shutter/ISO, white balance, focus and whether stabilization
could be disabled. A short setup photo is useful. All footage and calibration
images stay inside the Git-ignored `data/` tree.

Use [the foundation guide](DYNAMIC_FOUNDATION.md) for timestamp inspection and
sync planning. One-frame manual alignment is a useful starting estimate, not
a guarantee of simultaneous sensor exposure; verify the end cue and inspect
the fastest moving parts before trusting a dynamic reconstruction.
