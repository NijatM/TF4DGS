# Reference marker files

`documentation/reference_markers` holds printable and Illustrator-editable
ChArUco targets, matching target definitions, validation results and the native
Illustrator export script.

Created and verified on 2026-10-06 for the first controlled multi-camera motion
test on the white desk. Both PDFs are one-page landscape vector documents.
Choose the paper your printer supports; **Tabloid is recommended if available**.

| PDF | Paper, landscape | Pattern | Square / marker side |
| --- | --- | --- | --- |
| [US Letter](TF4DGS_ChArUco_US_Letter_8x6_30mm.pdf) | 11 x 8.5 inches (279.4 x 215.9 mm) | 8 x 6 squares; 240 x 180 mm | 30 / 22 mm |
| [US Tabloid / Ledger](TF4DGS_ChArUco_US_Tabloid_10x6_35mm.pdf) | 17 x 11 inches (431.8 x 279.4 mm) | 10 x 6 squares; 350 x 210 mm | 35 / 25 mm |

Print one of these PDFs directly, rather than a screenshot or browser preview.
Select the matching paper, landscape orientation and **100% / Actual Size**.
Disable Fit, Shrink, borderless expansion and multiple pages per sheet. Use
black-and-white printing on matte paper, then mount it flat and secure it.

Measure the printed horizontal and vertical endpoint ticks: each pair must
be **100 mm apart**. Also check several square intervals in both directions.
If the printer changes scale, correct its settings and reprint, or record the
actual dimensions for calibration. Keep the pattern exposed around the target.
The PDF requests no print scaling, but printer/viewer settings still need review.

Both boards use `DICT_5X5_100`, one black-border module, and OpenCV's modern
ChArUco layout (`legacyPattern=false`). The top-left square is black. Letter
uses marker IDs 0-23; Tabloid uses 0-29. **Use one board at a time**: they share
marker IDs but have different geometry. These are custom print layouts using
the standard OpenCV marker dictionary.

The corresponding `.json` files preserve board dimensions, individual marker
corners, dictionary checksum, layout version and PDF SHA-256. Keep the JSON
matching the PDF actually printed. These describe a target, not a solved
camera calibration. `physical_dimensions_verified` stays false until the
physical print is measured; no camera poses or accuracy have been established.

## Editable artwork and native Illustrator files

Open either vector file in Illustrator with **File > Open**, make your edits,
then use **File > Save As > Adobe Illustrator (.ai)**:

- [US Letter editable SVG](TF4DGS_ChArUco_US_Letter_8x6_30mm.svg)
- [US Tabloid / Ledger editable SVG](TF4DGS_ChArUco_US_Tabloid_10x6_35mm.svg)

Both SVGs preserve the exact paper and pattern dimensions. They contain
separate Paper, Checkerboard, Markers, Measurements and Labels groups, with
each marker named by ID and editable text. No raster images are embedded.

Alternatively, use **File > Scripts > Other Script** in Illustrator and select
[Create-Native-Illustrator-Boards.jsx](Create-Native-Illustrator-Boards.jsx).
It creates both original boards as native `.ai` documents beside the script,
with five named Illustrator layers, per-ID marker groups, live text and
CMYK black fills. The paper layer is locked. Existing `.ai` files are never
overwritten; move or rename them before rerunning the script. The script
recreates the original geometry; it does not import changes made to an SVG.
See [Adobe's script instructions](https://helpx.adobe.com/illustrator/desktop/automate-visualize-data/automate-actions/install-and-run-scripts.html).

Illustrator was unavailable on this machine, so native `.ai` creation has
**not been executed or tested**. The delivered SVGs were rendered and verified;
the builder remains an optional Illustrator export route. Inspect the native
documents before printing, including label placement and both 100 mm rulers.

Labels can be edited without changing the target geometry. Keep the marker
bit patterns intact. Changing square or marker size, IDs, spacing or placement
requires an updated target JSON and detection checks before calibration.
The original JSON definitions apply to the unmodified boards. Keep using
the verified PDFs for printing until any modified artwork is revalidated.

## Verification

The delivered PDFs were rendered at 240 DPI and detected with OpenCV 4.13.0.
Letter: all 24 markers and 35 internal chessboard corners; Tabloid: all 30
markers and 45 corners. Maximum corner-coordinate disagreement with nominal
page geometry was approximately 0.17 raster pixels. Both have exact paper
dimensions within 0.001 mm, vector-only content and the correct square sizes.
This validates the digital targets, not printer accuracy or real camera data.

The editable SVGs also passed the same 240 DPI detection and page-dimension
checks: all 24/30 markers and 35/45 corners, with approximately 0.17 pixels
maximum disagreement. Results and SVG hashes are recorded in
[editable_artwork_validation.json](editable_artwork_validation.json).

## Recreating the targets

`scripts/Create-CalibrationBoards.py` generates the vectors from OpenCV's
dictionary and validates the rendered PDFs. Optional printing dependencies
are pinned in `configs/board_print_requirements.txt`. They are isolated from
the main `tf4dgs` environment and static native tools.

From the repository root in PowerShell, to create a separate tool environment
and regenerate into a new directory:

```powershell
conda activate tf4dgs
python -m venv .local/tools/board-print-env-new
& .local/tools/board-print-env-new/Scripts/python.exe -m pip install -r configs/board_print_requirements.txt
& .local/tools/board-print-env-new/Scripts/python.exe scripts/Create-CalibrationBoards.py --output .local/workflows/calibration_boards/recreated
& .local/tools/board-print-env-new/Scripts/python.exe scripts/Create-EditableCalibrationBoards.py --output .local/workflows/calibration_boards/recreated
```

The generators refuse existing outputs to protect printed-target definitions
and artwork edits. The editable generator reads the matching PDFs/JSON first
and embeds the original geometry in the JSX using
`scripts/Illustrator-Boards.template.jsx`. Previews, installed packages and
intermediate files remain under ignored `.local`. Final PDFs, SVGs, JSON
definitions, the JSX builder, source and instructions are suitable for Git.

## References

- OpenCV contributors. *Detection of ChArUco Boards*, OpenCV 4.13.0 documentation,
  accessed 2026-10-06. [Documentation](https://docs.opencv.org/4.13.0/df/d4a/tutorial_charuco_detection.html).
- Garrido-Jurado, S., Muñoz-Salinas, R., Madrid-Cuevas, F. J., and Marín-Jiménez,
  M. J. (2014). *Automatic generation and detection of highly reliable fiducial
  markers under occlusion*. Pattern Recognition, 47(6), 2280-2292.
  [DOI: 10.1016/j.patcog.2014.01.005](https://doi.org/10.1016/j.patcog.2014.01.005).

The paper describes the underlying ArUco system; the OpenCV documentation
describes this ChArUco implementation. Report the chosen dimensions and
dictionary separately when writing the experiment's methods.

## User's commit commands

No commit or push was performed. From the repository in VS Code PowerShell:

```powershell
Set-Location -LiteralPath 'C:\Users\mnijat\Desktop\Git\TF4DGS'
git add -- README.md PROJECT_MEMORY.md docs/CAPTURE_CHECKLIST.md
git add -- configs/board_print_requirements.txt scripts/Create-CalibrationBoards.py scripts/Create-EditableCalibrationBoards.py scripts/Illustrator-Boards.template.jsx
git add -- documentation/reference_markers
git --no-pager diff --cached --stat
git commit -m "Add verified ChArUco reference markers and editable artwork"
git push origin main
```
