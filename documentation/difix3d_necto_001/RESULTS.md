# Difix3D Necto first-pass repair tests

All eight original PLYs preserved. Outputs saved beside originals with `_Difix3D` suffix. The user found little visible improvement in the 2M first pass. Stronger parameter tests are documented separately in [TUNING_RESULTS.md](TUNING_RESULTS.md). Residual novel-view artifacts remain.

| Input | Count | Before / after camera PSNR | Change |
| --- | ---: | --- | ---: |
| MRNF_2m-90k_Night_CleanUp-V1.ply | 1,999,193 | 21.13 / 22.44 | +1.31 dB |
| MRNF_2m-90k_Night_CleanUp-V2_Isolated.ply | 1,539,168 | 11.72 / 11.91 | +0.18 dB |
| splat_90000.ply | 2,000,000 | 21.15 / 22.47 | +1.32 dB |
| MRNF_5m-210k_Night_CleanUp-V1.ply | 4,978,251 | 19.50 / 20.93 | +1.43 dB |
| MRNF_5m-210k_Night_CleanUp-V2.ply | 4,897,316 | 18.48 / 19.71 | +1.22 dB |
| MRNF_5m-210k_Night_CleanUp-V3.ply | 4,564,412 | 14.47 / 15.27 | +0.80 dB |
| MRNF_5m-210k_Night_CleanUp-V4_Isolated.ply | 3,944,031 | 11.52 / 11.80 | +0.28 dB |
| splat_210000.ply | 5,000,000 | 19.55 / 21.04 | +1.50 dB |

Camera scores use images available during original training. They do not establish physical accuracy or recovery of unobserved surfaces. Isolated variants are evaluated with support scores in JSON as well.

[Chronological evidence](index.html) · [Adapter and reproducibility](../../docs/DIFIX3D_NECTO_TEST.md)
