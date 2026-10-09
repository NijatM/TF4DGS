# Full-recording 4C4D training

Each capture produces one continuous model including the subject, hands, printed
board and visible surroundings. Every Gaussian remains trainable. No separately
trained or frozen background, older desk model or prior actor reconstruction is
merged. Static COLMAP/LichtFeld processing remains available.

## Selected methods

Eight improvement hypotheses were screened using matched 600-update trials.
The leading candidates were confirmed using all 45 temporal validation images.
These scores guide local selection; they do not establish independently measured
novel-view or material geometry accuracy.

| Capture | Selected recipe | Whole / motion PSNR | Confirmation gain over control |
|---|---|---|---|
| Textile | 600k Gaussians; baseline motion rates | 25.4806 / 23.5876 dB | +1.8742 / +0.8132 dB |
| Yogurt | 450k Gaussians; reduced time/rotation rates | 31.1303 / 27.1597 dB | Control was best on motion |

The combination of increased motion weighting and temporal-support penalty did
not beat capacity alone. A 900k budget, image-gradient loss, compactness penalty,
reduced appearance complexity and multi-time seed injection were not selected.
Raising resolution alone gave little motion improvement in the brief screen;
it remains a later detail-refinement stage after geometry training.

The [hypotheses](../documentation/4c4d_hypotheses_001/HYPOTHESES.md),
[actual results](../documentation/4c4d_hypotheses_001/RESULTS.md) and
[chronological screenshots](../documentation/4c4d_hypotheses_001/README.md)
preserve successful and failed attempts. The adapter uses the
[official 4C4D implementation](https://github.com/yangzf-1023/4C4D), pinned to
`ed6a3cb69782c4147151b3898944bc38132bae00`; it is not a reproduction of the
paper's benchmark.

## Complete recordings and stages

| Capture | Frames per camera | Source indices | Export duration |
|---|---:|---|---:|
| Yogurt | 467 | 0–466 | 15.582233 s |
| Textile, including hands | 1277 | 0–1276 | 42.609233 s |

All six streams are `30000/1001` fps. The Premiere alignment is retained; residual
sensor synchronization and calibration away from the marker board remain
provisional. Original footage is unchanged. One continuous model can later be
sampled at exactly 30 fps without independently fitting each frame.

1. Prepare all camera frames at edges 1280, 1920 and native 3840. Fuji/iPhone
   native frames are 3840×2160; DJI is 1536×2304. Keep aspect ratios and calibrated
   principal points.
2. Initialize a fresh whole-scene action-frame cloud at training source 330 for
   yogurt and 588 for textile. Calibrated SIFT/MASt3R and explicitly labelled
   registered inferred depth supply the cloud. Uniform temporal centers cover
   the complete timeline. No old trained splat is used.
3. Check finite forward/backward operations and camera projections, then save
   resumable 100-update checkpoints for both full timelines.
4. Train 60,000 updates at edge 1280, sequentially on the single RTX A4000.
   Save optimizer/RNG checkpoints every 1000 updates and major scored milestones.
5. Refine each model for 8000 updates at 1920 and 8000 at native 3840. If native
   training actually exhausts GPU memory, preserve its failure and screenshot
   and retry at 2560 from the preceding checkpoint.
6. Fit all captured frames for 4000 final updates without densification. Export
   one `continuous_model.pth` per capture and record its SHA-256 in the registry.

Selection uses temporal holdouts; final production fitting includes them and
its scores are fitted references. Full validation evaluation samples distributed
held-out times, including the fixed action preview. Physical initial temporal
sigma and temporal-center learning-rate steps are retained from the short tests
by adjusting their normalized time units for each recording's duration.
The image cache is bounded to 5 GiB. GPU training jobs are sequential.
4K refinement and final quality are pending until their artifacts are verified.

## Paths and resume

- Inputs: ignored `data/4c4d_full_001/<capture>/edge_<size>/`.
- Models/checkpoints: ignored `outputs/4c4d_full_001/<capture>/<attempt>/`.
- Logs: ignored `.local/workflows/4c4d_full_001/`.
- Evidence and current state: `documentation/4c4d_full_001/`.

The live report is `http://127.0.0.1:8109/`. For recovery, first check that another
worker is not already running, then use the repository's VS Code PowerShell:

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
& .local/envs/temporal-base/python.exe scripts/Run-4C4DFullTraining.py --stage train
```

Completed stages are skipped; interrupted stages restore optimizer/RNG state.
Do not launch a second worker against the same output directory. No Windows
restart or Git commit/push is performed automatically.

After `outputs/4c4d_full_001/selected_models.json` exists, launch the continuous
viewer with:

```powershell
& .local/envs/4c4d/Scripts/python.exe scripts/Serve-4C4DScene.py --models outputs/4c4d_full_001/selected_models.json
```

Open `http://127.0.0.1:8110/` for time scrubbing, captured views, free orbit and
native resolution. Browser rendering speed must be measured; offline 30 fps
encoding does not establish a 30 fps interactive viewer. Final review must check
textile patterns, hands, ghosting, missing folds and room floaters at several
times and ±45° views before any pristine reconstruction is claimed.
