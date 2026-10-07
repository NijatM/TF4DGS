# Recorded web-viewer drivers

These JavaScript expressions reproduce the documentation views of this capture.
They run only in the dedicated local viewer through `Record-LocalWebViewer.ps1`.
Model files and raw PNG screencasts remain in ignored folders. The final MP4s,
posters and small capture manifests are intentional documentation artifacts.

The yogurt Gaussian arc is centered on the measured iPhone-side azimuth
(95.137965 degrees), raised from 30.555069 to 42.555069 degrees elevation.
Its 0.91-metre orbit radius fits every supported actor bounding box and the
full marker board across 181 checked arc angles. Each of
RGB, displacement and recent activity follows center -> +45 -> center ->
-45 -> center. Camera angles change smoothly; source poses are selected from
the 53 supported samples without interpolating object geometry.

The other two clips show observed selected-point geometry and appearance
side by side, with reference and three-second recent activity comparisons.
Their point-map view also sweeps +/-45 degrees with fixed framing fitted to
the whole interval. This point projection is separate from the Gaussian
camera. Yogurt points retain their original provisional calibration. Textile
uses measured run05: 30 source frames through 2.9029 seconds, 28 with at least
12 points and two sparse frames with 10 and 11 points. No dense textile
Gaussian model or fitted temporal Gaussian appearance is implied.

With the matching servers and the task-owned Edge debug browser already
running on port 8098, use a **new** ignored cache directory for each attempt:

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
& .\scripts\Record-LocalWebViewer.ps1 `
  -Url 'http://127.0.0.1:8100/' `
  -CacheDirectory '.local/workflows/dynamic_setup/my_orbit_capture' `
  -SetupExpressionFile 'scripts/viewer_recordings/yogurt_gaussian_setup.js' `
  -PlaybackExpressionFile 'scripts/viewer_recordings/yogurt_gaussian_play.js'
conda run --no-capture-output -n tf4dgs-dynamic python scripts/Encode-WebViewerRecording.py `
  --capture '.local/workflows/dynamic_setup/my_orbit_capture/capture.json' `
  --output 'documentation/dynamic_capture_001/videos/my_orbit.mp4'
```

For point clips, use the corresponding `yogurt_points_*` drivers on port
8096 or `textile_points_*` on port 8102. Existing output names and caches are
protected from overwriting. Encoding uses actual paint timestamps, H.264
CRF18, 30 fps and streaming-friendly MP4 headers. Camera animation and browser
rendering determine playback duration; the visible source clock is authoritative.
