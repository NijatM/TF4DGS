# Measured short-trial results

Each screening trial uses 600 updates from the same immutable 10k parent and nine validation images. Confirmations use all 45 temporal validation images. Comparisons must use the same evaluation-image count. All fields below come from saved metric JSON.

| Capture | Variant | Validation images | Whole PSNR | Motion PSNR | SSIM | Points | Run seconds | Peak allocated GiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| textile | capacity_900k | 45 | 24.5139 | 22.9060 | 0.84628 | 852061 | 70.5 | 3.14 |
| textile | combination | 45 | 25.4487 | 23.5575 | 0.86267 | 599884 | 68.8 | 2.48 |
| textile | control | 45 | 23.6064 | 22.7745 | 0.83714 | 450000 | 60.6 | 1.92 |
| textile | point_capacity | 45 | 25.4806 | 23.5876 | 0.86276 | 599905 | 66.6 | 2.47 |
| textile | capacity_900k | 9 | 24.7227 | 23.4698 | 0.84675 | 851338 | 67.9 | 3.14 |
| textile | compact_geometry | 9 | 23.6027 | 23.3943 | 0.83326 | 450000 | 63.9 | 3.74 |
| textile | control | 9 | 24.2999 | 23.4285 | 0.84292 | 450000 | 60.2 | 1.92 |
| textile | motion_priority | 9 | 24.8461 | 23.5739 | 0.84915 | 450000 | 65.4 | 1.94 |
| textile | multi_time_support | 9 | 25.4252 | 23.8663 | 0.85751 | 600000 | 65.9 | 2.47 |
| textile | native_detail | 9 | 24.1670 | 23.4532 | 0.84928 | 450000 | 95.6 | 2.03 |
| textile | pattern_detail | 9 | 24.0004 | 23.3608 | 0.83797 | 450000 | 61.2 | 2.28 |
| textile | point_capacity | 9 | 26.1094 | 24.2090 | 0.86791 | 599881 | 64.2 | 2.47 |
| textile | simpler_appearance | 9 | 23.8783 | 22.9658 | 0.83816 | 450000 | 64.2 | 1.91 |
| textile | temporal_support | 9 | 24.3770 | 23.5391 | 0.84433 | 450000 | 58.3 | 1.93 |
| yogurt | capacity_900k | 45 | 30.8732 | 27.0470 | 0.96123 | 566928 | 69.3 | 2.27 |
| yogurt | combination | 45 | 30.9872 | 26.5832 | 0.96153 | 599304 | 72.6 | 2.40 |
| yogurt | control | 45 | 31.1303 | 27.1597 | 0.96270 | 450000 | 70.1 | 1.89 |
| yogurt | point_capacity | 45 | 31.1355 | 27.0921 | 0.96161 | 567237 | 69.6 | 2.27 |

The substantial early gain is point capacity. Smaller temporal-support and motion-weighting improvements require combination confirmation. Raising resolution alone was not a substitute for better geometry/capacity. Loss and SH changes that regress the measured moving region are excluded.

Novel orbit views remain underconstrained by the three same-side cameras, and the cloth still contains streaks/ghosts. No pristine reconstruction or independently validated geometric accuracy is claimed. More iterations and higher resolution are follow-up stages, not measured outcomes yet.

Multi-time seed injection did not improve on the capacity-only trial and is excluded from the selected recipe. Full training starts with a fresh whole-scene action-frame cloud and uniformly initialized temporal centers, retaining the same physical initial temporal sigma as the three-second trials. This is one model with every primitive trainable; no separately trained base is merged. Temporal center learning rates are rescaled to preserve their physical-time step. The longer-duration adaptation is checked for finite forward/backward operations before the full jobs begin.

## Selected full-training recipes

{
  "textile": {
    "variant": "point_capacity",
    "validation_psnr_common_1280": 25.480570983886718,
    "motion_region_psnr_common_1280": 23.587636269463435,
    "confirmation_images": 45,
    "parameters": {
      "max_points": 600000
    },
    "preset": "baseline",
    "selection_scope": "Single-seed short-clip screening plus all-temporal-validation confirmation. Full-duration convergence is not yet measured."
  },
  "yogurt": {
    "variant": "control",
    "validation_psnr_common_1280": 31.13026869032118,
    "motion_region_psnr_common_1280": 27.159680302937826,
    "confirmation_images": 45,
    "parameters": {
      "max_points": 450000
    },
    "preset": "slow_motion",
    "selection_scope": "Single-seed short-clip screening plus all-temporal-validation confirmation. Full-duration convergence is not yet measured."
  }
}
