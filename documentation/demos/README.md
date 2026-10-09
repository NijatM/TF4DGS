# Final experiment demos

Open [the gallery](index.html), or play the MP4 files directly. Each experiment
has its selected viewer-interface recording and a **native 3840 x 2160 / 30 fps**
RGB Gaussian orbit. Use the player's full-screen button to inspect fine detail.

| Experiment | Viewer interface | Native 4K reconstruction only |
| --- | --- | --- |
| Yogurt | [55.10 s / 10.63 MB](yogurt/yogurt_ui.mp4) | [8.37 s / 21.33 MB](yogurt/yogurt_reconstruction_orbit.mp4) |
| Textile | [43.47 s / 5.45 MB](textile/textile_ui.mp4) | [42.57 s / 44.97 MB](textile/textile_reconstruction_orbit.mp4) |

The four videos total **82.37 MB**; the two new
4K videos total **66.30 MB**.
The UI files are unchanged copies of recordings already in Git, so identical
blobs are reused. Every selected MP4 is below 50 MiB. These paths use ordinary
Git; no LFS tracking rule is added. Models, footage, raw frames and local masters
remain ignored.

The clean videos are rasterized directly from the full-precision fitted
Gaussian models, with antialiasing and one render for **every output frame**.
They are not enlarged screen captures. H.264/yuv420p, CRF16, slow preset and
fast-start playback preserve detail with compact files. The camera follows an
elevated iPhone-side **center -> +45 degrees -> center -> -45 degrees -> center**
orbit. No UI, labels or overlays appear in the clean MP4s.

Offline rendering waits for each render and encoding step, so wall-clock
loading pauses cannot skip camera frames. Both clean videos play at the original
source speed; yogurt covers source time 7.2072-15.5155 s, rather than stretching
those poses into the former 22.7-second cinematic clip. The last state is padded
by less than two video frames to end the orbit.

**Camera smoothness and geometry continuity are separate.** Textile retains all
214 independently fitted states, approximately five shape updates per second.
It can still pop or flicker when the fitted state changes. Yogurt retains all
53 supported poses; unsupported gaps, including one 2.002-second gap, hold the
latest supported pose and can jump afterward. No missing movement, material
correspondences or intermediate cloth deformation are invented. A temporally
consistent reconstruction is required to resolve those model limitations.
The UI clips retain their original recording resolution and browser timing.

[Stutter diagnosis](stutter_diagnosis.json) records the old irregular browser
paints: about 19.6 fps averaged across yogurt's three modes and 22.5 fps for
textile RGB. [Validation](validation.json) verifies full decoding, exact 30 fps
presentation timestamps, dimensions, hashes and comparison with five lossless
native-render reference frames per clean video. Those compression comparisons
measure encoding fidelity, not reconstruction accuracy. Each clean video's
`.capture.json` includes every output frame's source state and camera angle.

The genuine [4K gallery screenshot](gallery_review_4k.png),
[browser playback samples](browser_validation.json) and
[byte-range checks](range_validation.json) document actual served playback.
The browser samples cover about 1.1 seconds per clip after seeking;
full-file timestamp and decode checks are recorded separately. Keep the gallery
in the foreground and run `scripts/Validate-DemoPlayback.ps1` to repeat that check.

The initial low-resolution attempt passed playback checks and was then rejected
for visual quality. Its small evidence records remain in
[history/initial_browser_crop](history/initial_browser_crop/README.md).
Rejected MP4s, encode logs and lossless reference images are retained under
ignored `.local/workflows/dynamic_setup/native_demo_gallery_02/` and `outputs/`.
Chronological experiment reports retain the failed attempt and the correction.

For locally served playback and seeking:

```powershell
conda run --no-capture-output -n tf4dgs python scripts/Serve-Demos.py
```

Open <http://127.0.0.1:8107/>. Playback needs no models or source footage.
To reproduce the clean masters from the retained fitted models, use
`scripts/Render-GaussianOrbit.py` once for each dataset with a new ignored output
folder, then `scripts/Finalize-NativeDemoGallery.py --masters <folder> --attempt <new-name>`.
The original cropped workflow is historical: `scripts/Build-DemoGallery.py`.
