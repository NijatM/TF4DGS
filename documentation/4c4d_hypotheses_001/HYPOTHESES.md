# Eight 4C4D improvement hypotheses

These are local hypotheses based on our observed errors and the [official 4C4D implementation](https://github.com/yangzf-1023/4C4D). They are not guaranteed improvements.

| Test | Reason and prediction |
|---|---|
| temporal_support | Very short temporal support leaves gaps between captured frames. A soft 40 ms minimum marginal standard deviation may improve interpolation without forcing all Gaussians to be persistent. |
| compact_geometry | Long conditional spatial ellipsoids produce cloth streaks and floaters. A mild aspect-ratio penalty may recover compact geometry rather than view-specific streaks. |
| pattern_detail | Global RGB/SSIM objectives dilute small textile patterns. A motion-weighted image-gradient loss may recover weave, printed detail and hand boundaries. |
| motion_priority | The surrounding room competes with the changing subject. Raising motion-region weight from 4 to 8 may improve the subject while retaining supervision on every room pixel. |
| point_capacity | The early 450k cap limits births and fine detail. Allowing 600k Gaussians may reduce missing folds and preserve newly visible surfaces. |
| native_detail | 1280-edge supervision loses source detail. A matched 1920-edge continuation may improve detail at a common 1280 evaluation resolution, justifying later native 4K refinement. |
| simpler_appearance | High-degree space/time color coefficients can fit appearance before geometry. Limiting active SH to spatial 1 / temporal 1 may reduce view-specific overfitting. |
| multi_time_support | First-frame-only geometry misses later folds and hand positions. Timestamped calibrated seeds at three training times may improve coverage within the same joint model. |

All trials start at the same immutable 10k checkpoint and RNG state and run 600 updates. Nine held-out camera images (three times × three cameras) screen whole-frame and motion appearance. Positive results are candidates for confirmation, not proof of final quality. The higher-resolution trial has more pixel work; initialization-plus-capacity is compared against capacity alone.

Existing long experiments: textile reached 20k (25.95 dB whole-frame / 24.05 dB motion PSNR), but visible cloth streaks remain. Yogurt favored reduced time/rotation learning rates at 12k. Prior opacity/learning-rate branches did not fix cloth geometry.

The previous 30k continuation ended at 20,500 because Windows denied replacement of the browser-read live-progress JSON. The last saved and evaluated checkpoint is 20,000. Atomic writes now use unique temporary names and bounded retries; failed-run logs and screenshots are preserved.

## Full recordings

- yogurt: 467 frames/camera, 15.5822 seconds, three cameras.
- textile: 1277 frames/camera, 42.6092 seconds, three cameras.
