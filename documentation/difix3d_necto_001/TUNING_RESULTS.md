# Stronger 2M repair results

**User review,2026-10-12:** no noticeable improvement; repair work stopped at
the user's request. The stronger outputs do not meet the requested visual
quality. The earlier selection and scores below remain as experiment evidence.

Selected moderate Difix3D refinement followed by opacity-only source-guided recovery: fewer window-side ghosts in matched actual 3D views, retained knit detail, and better source-camera fit. Aggressive rates, hard pruning and depth/SSIM recovery were rejected. This improves the tested views but does not fully repair glass/window streaks or unseen surfaces.

Original camera audit:21.147dB. These scores measure fit to existing photographs, not independent geometry accuracy.

| Candidate | Updates | Training edge | Camera PSNR | Decision |
| --- | ---: | ---: | ---: | --- |
| first_pass | 750 | 768 | 22.466 | user found little visible repair |
| wide_official | 3000 | 768 | 23.084 | not selected |
| wide_strong | 3000 | 768 | 22.833 | not selected |
| wide_strong_pruned_balanced | filter only | 1024 audit | 22.063 | rejected: damaged source reconstruction |
| wide_official_pruned_conservative | filter only | 1024 audit | 22.462 | rejected: damaged source reconstruction |
| geometry_recovery | 6000 | 1024 | 14.282 | rejected: damaged source reconstruction |
| opacity_recovery | 3000 | 1024 | 24.715 | selected |

Final stronger copies are saved in the original `MRNF_2m-90k` folder with `_Refined_Difix3D.ply` suffix. Previous repairs remain available. Crops, rotations and Gaussian counts are preserved. All eight original SHA256 hashes were rechecked.

| Export | Gaussian count | Support camera PSNR: original / first pass / selected |
| --- | ---: | --- |
| MRNF_2m-90k_Night_CleanUp-V1_Refined_Difix3D.ply | 1,999,193 | 21.130 / 22.438 / 24.632 |
| MRNF_2m-90k_Night_CleanUp-V2_Isolated_Refined_Difix3D.ply | 1,539,168 | 17.943 / 18.879 / 19.298 |
| splat_90000_Refined_Difix3D.ply | 2,000,000 | 21.147 / 22.466 / 24.715 |

Residual window/glass streaks remain. Missing surfaces outside the photographs are not established as recovered. Rejected attempts are retained in ignored work folders and chronological evidence.

[Actual rendered comparison](tuning_comparison.html) · [Chronological report](index.html)
