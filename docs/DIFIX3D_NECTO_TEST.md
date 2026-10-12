# Difix3D Necto static repair test

This test uses only `Desktop/Necto/NightV1/colmap`, not the earlier project
Necto capture. It processes the three original SH3 PLYs in `MRNF_2m-90k`
and five in `MRNF_5m-210k`, including the user's cleaned/isolated variants.
Each output is saved in its original folder as `<original_stem>_Difix3D.ply`,
with a same-stem `.difix3d.json` record. Originals are hashed and never overwritten.

## Implementation and scope

- Official source: [nv-tlabs/Difix3D](https://github.com/nv-tlabs/Difix3D),
  revision `c76edc595586e16732c91ddee82f3a6d83a8a9cc`.
- Model: [nvidia/difix_ref](https://huggingface.co/nvidia/difix_ref), revision
  `d4830559772a5795c9d136302c5b197d6418d3fb`. Single-step inference, timestep199,
  guidance0, reference images from the matching capture.
- Python3.10/PyTorch2.4.0 CUDA12.4/gsplat1.5.3 Windows renderer reused read-only
  in a separate venv overlay. Diffusion dependencies remain in that overlay.
  No static LichtFeld source or environment was modified.
- The standard PLY SH3 layout is imported without changing coordinates,
  count or ordering. Undistorted COLMAP PINHOLE cameras are required; original
  image dimensions are checked. RGB-render checks establish alignment.
- Cleaned variants were rotated after export. Similarity transforms are
  recovered from3000 preserved DC-color/opacity correspondences per file;
  matched positions verify every fit. Cameras are transformed into each edited
  model's coordinate frame. Failed unaligned outputs are archived, not retained
  as the final repair outputs. User edits and original PLYs stay intact.
- Deterministic sampling of48 original source views and24 near-camera
  interpolated novel poses. Nine camera views provide an audit only: they were
  present during original training, so these are not independent held-out scores.
- Difix targets are generated at1024 maximum edge. The adapter refines the same
  Gaussian primitives for750updates at768edge, using approximately70% original
  source views and30% pseudo-target views, with additional.3 pseudo-loss weight.
  Actual GPU OOM triggers a documented512edge retry from saved optimizer state.
- Support masking protects empty regions of already isolated variants. No
  largest-cluster deletion, global outlier pruning, geometry normalization,
  densification, downsampling or old-scene merge is applied.
- No neural image enhancer is applied when verifying the exported PLY. Reopened
  camera renders must match the in-memory scores. Comparisons also show actual
  novel-view renders separately from generative target images.

This is a bounded PLY refinement adapter using the official Difix diffusion
model, not a reproduction of the paper's complete progressive pipeline.
It is not guaranteed to remove every floater or recover unobserved geometry.
Existing high-resolution Gaussian attributes remain in the export, but this
repair test is not native7K optimization.

PPISP is not applied by gsplat here. The output is canonical SH appearance; an
unchanged PPISP companion is not attached to newly optimized parameters.
Compare originals and outputs with the same viewer exposure and appearance
settings. Preserve the original `.ppisp` and checkpoints.

## Setup and rerun

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
.\scripts\Setup-Difix3D.ps1
& '.local/envs/difix3d/Scripts/python.exe' scripts/Repair-Difix3DSplats.py --stage audit
& '.local/envs/difix3d/Scripts/python.exe' scripts/Align-Difix3DVariants.py
& '.local/envs/difix3d/Scripts/python.exe' scripts/Run-Difix3DBatch.py
```

The batch runs one model per child process; CUDA memory is released between
models. Completed output/provenance pairs skip refinement and are reverified.
Existing files without matching provenance are refused. Logs, snapshots,
models and machine-specific manifest remain under ignored `.local/` and `outputs/`.

## Documentation

[Chronological report](../documentation/difix3d_necto_001/index.html) contains
baseline renders, diffusion targets, actual exported/reopened comparisons and
failures. Browser screenshots are real local-page captures, clearly labelled
when headless. No files are staged, committed, pushed or uploaded.

Initial failure: diffusers0.27.2 lacked PositionNet required by the released
custom UNet. Switching the isolated overlay to official diffusers0.25.1 resolved
it. A first audit console-formatting error and a visible-browser capture timeout
were also encountered; headless documentation capture succeeded. Preserve
failure records rather than representing the first attempt as successful.
A pinned model load also required its explicit custom-code permission flag;
the inspected official model code is enabled with `trust_remote_code=True`.

## Stronger repair tests after first-pass review

The user found little visible repair in the first 2M outputs. Source-camera
PSNR improvements did not establish removal of novel-view floaters. The next
tests explicitly inspect matched window-side views and close-up knit detail.

- `wide_official`: 3000 updates, 40 pseudo-target views (24 local interpolations
  and 16 wider orbit views). Published gsplat example geometry learning rates;
  60% source sampling, 40% novel sampling, novel loss weight0.5.
- `wide_strong`: doubled position/scale/opacity rates, plus opacity/scale
  regularization. Same image targets as the moderate test, so the comparison
  isolates optimization changes. It scored lower than the moderate test.
- Sparse SfM support pruning: retained the original files and exported only
  ignored prototypes. Balanced and conservative variants removed useful room
  detail and failed the camera-fit tolerance. They are rejected, not final.
- `geometry_recovery`: attenuates suspicious primitives instead of deleting
  them, then refines with all275 original photographs, L1/SSIM, sparse accurate
  SfM depths and locally supported Difix targets. Two inspected wide poses
  retained; wall-colliding wide poses excluded. 6000 updates at1024 edge.
  This is an experimental adapter extension, not the official full pipeline.
- The depth/SSIM recovery combination failed: camera PSNR dropped23.084 to
  14.282dB and actual renders showed exaggerated fabric edges and room damage.
  That candidate is rejected. `opacity_recovery` retries source-guided recovery
  with ordinary L1 image loss, keeping depth and SSIM weights at zero.

`Create-Difix3DVariantMaps.py` checks every cleaned Gaussian against the raw
model using invariant attributes and transformed positions. Both 2M subsets
have unique identities, covariance agreement and correctly rotated SH
coefficients. A reviewed raw repair can therefore be transferred without
reintroducing deleted Gaussians or undoing crops/rotations. The transfer script
applies repair deltas, independently renders each saved result and refuses
publication of failed camera audits or unverified copies.

`Review-Difix3DTuning.py` produces matched1536-edge renders of every candidate,
without final diffusion enhancement. Open
[detailed comparison](../documentation/difix3d_necto_001/tuning_comparison.html)
for native-size images. Rejected prototypes stay under ignored `outputs/`;
chronological failures, parameter metadata and browser screenshots remain in
the documentation. Initial repairs remain available for comparison.

The selected stronger2M recipe is `wide_official` followed by
`opacity_recovery`:3000updates at768edge, then3000at1024edge. The second stage
uses all275 source photos and26 repaired poses, with70% source sampling and
30% novel sampling, novel loss weight0.6. Suspicious opacity is capped at5%
only at initialization and can recover during optimization. Neither depth nor
SSIM constraints nor hard pruning are used in the selected result.

Three `_Refined_Difix3D.ply` copies now reside in the external `MRNF_2m-90k`
input folder. Each has independently rendered provenance and a verified copy
hash. All eight originals remain unchanged. The5M first-pass files remain
available; stronger tuning in this pass focused on the user-reviewed2M family.
See [final results](../documentation/difix3d_necto_001/TUNING_RESULTS.md) and
[before/after images](../documentation/difix3d_necto_001/final_comparison.html).

Residual window/glass streaks remain. Source-camera fit and visual improvement
at tested poses do not prove reconstruction of missing or unseen surfaces.
