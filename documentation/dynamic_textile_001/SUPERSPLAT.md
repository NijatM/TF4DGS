# Textile RGB replay in SuperSplat

The tested export is local and excluded from Git:

`outputs/dynamic_textile_001/supersplat_export_03/`

It contains **1,277 numbered compressed PLY files on a 30 fps timeline**, a
separate static board/table layer, and full float32 PLY archives. It plays in
42.567 seconds. There are **214 distinct fitted states**, about five per second;
the timeline holds the latest fitted state at each output timestamp. It does
not interpolate, invent material identities or reconstruct 30 Hz motion.

## Open and play

1. Open [SuperSplat Editor](https://superspl.at/editor/) in current Edge or Chrome.
2. Use **File → Import** to open
   `context/current_table.compressed.ply` inside the export folder.
3. Import **all files inside `rgb_30fps` together**, or drop that specific folder.
   Keep the table layer already in the scene. Do not drop the whole export root:
   it also contains archives and preview copies.
4. Open the Timeline panel. Set **FPS to 30** and length to **1,277 frames**.
   Press Play or scrub. Frame 475 shows the fitted fold at 15.816s;
   frame 798 shows the lifted cloth at 26.593s; frame 1276 shows the last fitted state.
5. Select the cloth/table and press **F** to focus, then orbit and zoom.
   To reproduce the documented view, press **I** for the editable camera overlay:
   set target **T** to `-0.175, 0.045, -0.1` and position **P** to
   `-0.141758, 0.468592, -0.479954`. Set FOV to 55° in the Preferences popup.
   These are editor coordinates, converted from training board coordinates.
   See the [official camera controls](https://developer.playcanvas.com/user-manual/supersplat/editor/camera-controls/).

Loading local files in the editor does not publish a hosted scene. Publishing
is a separate action. This task did not upload or publish the recordings/models.

SuperSplat officially supports numbered PLY sequences and compressed PLY.
A single ordinary PLY or SOG is a static snapshot; it does not store this entire
time-varying reconstruction. See the
[official import/export documentation](https://developer.playcanvas.com/user-manual/supersplat/editor/import-export/).

## Saved quality and measured performance

The selected compressed cloth data occupies 284.41 MB, plus 2.68 MB for the fixed
table. Repeated timeline files are local NTFS hardlinks to the 214 unique
compressed keyframes. Copying them to another filesystem can expand the timeline
to approximately 1.69 GB. The float32 archives are separate and keep the original
Gaussian attributes; there is no Gaussian-count decimation.

Across all 214 compressed cloth files, maximum position quantization error is
0.116 mm and maximum RGB-channel error is 0.00196 in normalized encoded RGB.
Four actual decoded scene renders compared with their full-quality originals
give 64.41–66.29 dB PSNR. These figures describe **file compression error**,
not reconstruction accuracy. The [export validation summary](supersplat_export_summary.json)
records the file checks and measured render differences.

Actual SuperSplat 3.5.2 tests on this machine:

| Export layout | Actual Gaussian data swaps/s in a five-second test |
| --- | ---: |
| Full-quality cloth+table in every PLY |14.16 |
| Compressed cloth+table in every PLY |12.39 |
| Compressed cloth sequence + one static table layer |23.57 |

The timeline advances at the correct real-time speed, while the loader can skip
held duplicate frames. **Sustained 30 Gaussian data swaps/s was not achieved or
verified.** Browser/GPU throughput varies across the sequence and other machines.
The saved 30 fps timeline is distinct from both measured render throughput and
the approximately 5 Hz rate of newly reconstructed states.

Only this textile recording supplies the table and cloth. Occluded folds,
provisional off-plane calibration, source motion blur and temporal jitter remain
limits; no independently validated material strain is included in these RGB PLYs.
The local TF4DGS viewer provides closest-reference surface/color maps separately.

## Recreate the export

With the completed sequence, selected table and dynamic environment available:

```powershell
conda activate tf4dgs-dynamic
python scripts/Export-TextileSuperSplat.py `
  --output outputs/dynamic_textile_001/supersplat_export_new `
  --compressed --separate-context
```

The encoder measures every compressed file's round-trip errors, preserves a
float32 archive, records hashes/source timestamps, and refuses to overwrite an
earlier export. `export_manifest.json` maps every output frame to its fitted
source time. The original combined exports 01/02 remain preserved as trials.
