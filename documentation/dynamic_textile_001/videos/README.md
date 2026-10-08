# Revised textile RGB and map recordings

Open [the offline video page](index.html), or play:

For the local web page with reliable seeking, open
<http://127.0.0.1:8105/videos/>. To reopen its documentation server:

```powershell
conda run --no-capture-output -n tf4dgs python scripts/Serve-TextileDocumentation.py
```

- [Realistic RGB orbit](textile_rgb_orbit.mp4): 43.47 s, 5.45 MB; all 214 fitted states actually displayed.
- [Surface and recorded RGB contrast maps](textile_shape_and_appearance.mp4): 43.97 s, 2.80 MB; 89 of 214 states displayed at real-time speed.

The pair totals **8.25 MB**. These are genuine browser PNG paint captures,
compressed to 1500 × 1150 H.264/yuv420p, 30 fps, CRF20, with fast-start playback.
The elevated iPhone-side view follows a ±45° back-and-forth arc across the
0–42.509-second source timeline. The ending includes a short painted hold.
Raw lossless screencast frames, earlier context04 clips and source videos remain
in the ignored local cache/data folders. Compression is visually high quality,
not mathematical losslessness.

The reconstruction has 214 distinct fitted times, approximately 5 Hz. The 30 fps
MP4 encoding does not generate new geometry or interpolate material identities.
The RGB clip renders actual fitted Gaussian colors; the map clip compares the
closest first reconstructed surface. Appearance uses approximately visible
balanced source-camera RGB; unknown samples are gray. Geometry is surface
distance, not independently validated material displacement or strain.

[Validation](validation.json) checks hashes, full video decoding, timing,
recorded model indexes and the actual orbit arc. The `.capture.json` files
record the displayed source samples and camera trajectory. No old desk,
pavilion or yogurt scene was merged into this textile reconstruction.
