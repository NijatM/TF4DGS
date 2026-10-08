# Shareable Gaussian baseline packages

The 2026-10-08 checkpoint includes the measured rigid yogurt replay and the
revised textile RGB keyframe replay. A continuous textile deformation model is
still pending; backend selection follows this checkpoint.

Keep the source, chronological screenshots, compressed demonstration videos and
package summary in Git. Upload the two ZIPs as **GitHub Release assets**. Do not
force-add `outputs/`, enable a broad LFS rule or commit the full model folders.
GitHub Release assets do not use Git LFS storage or download bandwidth, and the
models do not enlarge every source checkout. See GitHub's
[large-file distribution guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github#distributing-large-binaries).

## Prepared assets

Local folder: `outputs/release_assets/baseline_2026-10-08/`.

| File | ZIP size (decimal MB) | Contents |
| --- | ---: | --- |
| TF4DGS-textile-baseline.zip | 283.09 | All 214 selected compressed cloth keyframes, one static table, timing/export manifest. |
| TF4DGS-yogurt-baseline.zip | 25.84 | Full-precision actor/background NPZ and PLY files, 53 supported poses, current-session camera calibration and metadata. |

Total upload: **308.93 MB**. `SHA256SUMS.txt` records both ZIP checksums.
[package_summary.json](../documentation/baseline_release/package_summary.json)
records actual sizes, SHA-256 hashes and completed CRC/content validation.
Source footage, extracted images, pretrained weights, optimizer checkpoints,
failed trials and temporary caches are not included.

A fresh extraction check restored all 1,277 textile aliases and confirmed that
both ZIPs coexist without path collisions. The exact yogurt models loaded and
rendered their first/last supported poses through the real CUDA viewer without
footage. Portable evidence is in
[restore_validation.json](../documentation/baseline_release/restore_validation.json)
and [yogurt_playback_validation.json](../documentation/baseline_release/yogurt_playback_validation.json).

The textile package preserves every selected Gaussian; it uses the previously
validated quantized viewer export. Native float32 textile archives remain local.
Repeated 30 fps timeline PLYs are not bundled 1,277 times. Restoring aliases uses
hardlinks when supported, or verified copies; copies can expand to about 1.69 GB.
The bundle retains the full 42.567-second presentation with roughly five newly
reconstructed states per second. It is not a continuous deformation model,
material-strain measurement or independently reconstructed 30 Hz motion.

The yogurt package contains one persistent rigid actor, fixed RGB and static
current-session surroundings. Unsupported motion gaps remain unsupported. Its
static PLYs alone do not contain the animation; the NPZ/poses provide playback.
No earlier desk or Necto scan is merged. Both reconstructions have provisional
geometry and calibration outside the observed measured board.

## Upload after the user commits and pushes

Only the user executes these publishing commands. From the project root, after
`git push origin main` succeeds:

```powershell
$Gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
& $Gh release create baseline-2026-10-08 `
  'outputs/release_assets/baseline_2026-10-08/TF4DGS-textile-baseline.zip' `
  'outputs/release_assets/baseline_2026-10-08/TF4DGS-yogurt-baseline.zip' `
  'outputs/release_assets/baseline_2026-10-08/SHA256SUMS.txt' `
  --repo NijatM/TF4DGS --target main `
  --title 'Yogurt and textile Gaussian reconstruction baseline' `
  --notes-file 'documentation/baseline_release/RELEASE_NOTES.md'
```

This creates a release/tag at remote `main` and uploads the selected assets.
It does not use Git LFS. No publishing command has been executed by Codex.

## Restore on a fresh checkout

Download both assets from the release. Check their SHA-256 hashes against the
published `SHA256SUMS.txt`. Extract the ZIPs into the TF4DGS checkout root,
preserving their `outputs/` and `data/` directories. Use a fresh checkout, or
review existing files before extracting; do not overwrite a newer reconstruction.

For textile, the `tf4dgs` Python environment is sufficient to restore aliases:

```powershell
conda run -n tf4dgs python scripts/Restore-TextileTimeline.py
```

Then follow [the SuperSplat opening guide](../documentation/dynamic_textile_001/SUPERSPLAT.md):
import the static `context/current_table.compressed.ply` first, then all restored
`rgb_30fps/` files together; set 30 FPS and 1,277 frames. The original training
data and neural models are not required for this export playback.

For yogurt, install the documented `tf4dgs-dynamic` CUDA environment and run:

```powershell
conda run --no-capture-output -n tf4dgs-dynamic python scripts/Serve-RigidGaussianPreview.py
```

Open <http://127.0.0.1:8100/>. Original footage is not required for replay.
The release is model playback data, not a complete dataset for retraining.

## Repackage from the selected local outputs

Both helpers use only Python's standard library. Packaging refuses existing
output/summary paths and validates every archived file before reporting success.
Use new paths to retain earlier checkpoints:

```powershell
conda run -n tf4dgs python scripts/Package-GaussianBaselines.py `
  --output outputs/release_assets/baseline_new `
  --summary documentation/baseline_release/package_summary_new.json
```
