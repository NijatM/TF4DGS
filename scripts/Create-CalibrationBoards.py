"""Generate exact-size vector ChArUco PDFs and verify their rendered detection.

Uses the optional isolated tools in configs/board_print_requirements.txt;
the CPU capture/analysis environment does not need these dependencies.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


BOARDS = (
    {"name": "TF4DGS_ChArUco_US_Letter_8x6_30mm", "paper": "US LETTER",
     "page_mm": [279.4, 215.9], "squares": [8, 6], "square_mm": 30.0, "marker_mm": 22.0},
    {"name": "TF4DGS_ChArUco_US_Tabloid_10x6_35mm", "paper": "US TABLOID / LEDGER",
     "page_mm": [431.8, 279.4], "squares": [10, 6], "square_mm": 35.0, "marker_mm": 25.0},
)


def text(pdf, x, y, content, size=8, right=False):
    pdf.setFont("Helvetica", size)
    method = pdf.drawRightString if right else pdf.drawString
    method(x * mm, y * mm, content)


def board_definition(spec, dictionary):
    board = cv2.aruco.CharucoBoard(tuple(spec["squares"]), spec["square_mm"] / 1000,
                                   spec["marker_mm"] / 1000, dictionary)
    board.setLegacyPattern(False)
    return board


def make_pdf(path, spec, board, dictionary):
    width, height = spec["page_mm"]
    nx, ny = spec["squares"]
    square, marker = spec["square_mm"], spec["marker_mm"]
    board_width, board_height = nx * square, ny * square
    left, bottom = (width - board_width) / 2, (height - board_height) / 2
    if min(left, bottom) < 15:
        raise ValueError("Insufficient printing margin")
    pdf = canvas.Canvas(str(path), pagesize=(width * mm, height * mm),
                        pageCompression=1, invariant=1)
    pdf.setTitle(spec["name"])
    pdf.setAuthor("Temporal Fields 4D Gaussian Splatting (TF4DGS)")
    pdf.setSubject("Exact-size vector ChArUco target; DICT_5X5_100; OpenCV legacyPattern=false")
    pdf.setViewerPreference("PrintScaling", "None")
    pdf.setFillColorRGB(0, 0, 0)
    pdf.setStrokeColorRGB(0, 0, 0)

    text(pdf, left, height - 8, "TF4DGS | ChArUco calibration target", 11)
    paper_inches = "11 x 8.5 in" if spec["paper"] == "US LETTER" else "17 x 11 in"
    text(pdf, width - 12, height - 8, f"{spec['paper']} | {paper_inches} | LANDSCAPE", 8, right=True)
    text(pdf, left, height - 13,
         f"DICT_5X5_100 | {nx} x {ny} squares | square {square:g} mm | marker {marker:g} mm | legacyPattern=false", 8)

    marker_id, cells = 0, []
    margin = (square - marker) / 2
    module = marker / 7  # 5 data bits plus one black-border module on each side.
    for row in range(ny):
        for col in range(nx):
            x, top = left + col * square, bottom + board_height - row * square
            if row % 2 == col % 2:
                pdf.rect(x * mm, (top - square) * mm, square * mm, square * mm, stroke=0, fill=1)
                continue
            bits = cv2.aruco.generateImageMarker(dictionary, marker_id, 7, borderBits=1)
            # Fill every black module in one path, avoiding rasterizer seams
            # between neighboring modules when viewing or printing the PDF.
            marker_path = pdf.beginPath()
            for bit_row in range(7):
                for bit_col in range(7):
                    if bits[bit_row, bit_col] == 0:
                        marker_path.rect((x + margin + bit_col * module) * mm,
                                         (top - margin - (bit_row + 1) * module) * mm,
                                         module * mm, module * mm)
            pdf.drawPath(marker_path, stroke=0, fill=1, fillMode=1)
            cells.append({"id": marker_id, "column": col, "row": row,
                          "corners_m": board.getObjPoints()[marker_id].tolist()})
            marker_id += 1
    if marker_id != len(board.getIds()):
        raise ValueError("PDF marker count differs from OpenCV's board")

    # Independent horizontal and vertical 100 mm rulers outside the target.
    pdf.setLineWidth(0.35)
    pdf.line(left * mm, 9 * mm, (left + 100) * mm, 9 * mm)
    for offset in (0, 50, 100):
        pdf.line((left + offset) * mm, 7.5 * mm, (left + offset) * mm, 10.5 * mm)
    text(pdf, left, 12.5, "HORIZONTAL CHECK: endpoint ticks must be 100 mm apart", 7)
    gx, gy = width - 12, bottom + (board_height - 100) / 2
    pdf.line(gx * mm, gy * mm, gx * mm, (gy + 100) * mm)
    for offset in (0, 50, 100):
        pdf.line((gx - 1.5) * mm, (gy + offset) * mm, (gx + 1.5) * mm, (gy + offset) * mm)
    pdf.saveState()
    pdf.translate((gx + 4) * mm, gy * mm)
    pdf.rotate(90)
    text(pdf, 0, 0, "VERTICAL CHECK: 100 mm", 7)
    pdf.restoreState()
    text(pdf, left + 125, 12.5, f"Pattern: {board_width:g} x {board_height:g} mm | IDs 0-{marker_id - 1}", 7)
    text(pdf, left, 4.8, "PRINT AT 100% / ACTUAL SIZE. Disable Fit/Shrink. Check BOTH rulers; keep the target flat and matte.", 7)
    pdf.showPage()
    pdf.save()
    return {"origin_on_page_mm_from_bottom_left": [left, bottom],
            "pattern_mm": [board_width, board_height], "markers": cells}


def validate_pdf(path, spec, board, dictionary, preview_root):
    # This verifies the delivered PDF, not merely the generator's source image.
    document = pymupdf.open(path)
    if len(document) != 1:
        raise ValueError("Calibration PDF must contain exactly one page")
    page = document[0]
    actual_mm = [page.rect.width / mm, page.rect.height / mm]
    if any(abs(a - b) > 0.001 for a, b in zip(actual_mm, spec["page_mm"])):
        raise ValueError("PDF page size differs from the selected paper")
    if page.get_images():
        raise ValueError("Calibration PDF should contain vector geometry, not raster images")
    dpi = 240
    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    gray = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width)
    detector = cv2.aruco.CharucoDetector(board)
    corners, corner_ids, marker_corners, ids = detector.detectBoard(gray)
    expected_ids = board.getIds().reshape(-1).tolist()
    actual_ids = sorted(ids.reshape(-1).tolist()) if ids is not None else []
    if actual_ids != expected_ids:
        raise ValueError(f"PDF marker detection mismatch: {actual_ids} vs {expected_ids}")
    expected_corners = (spec["squares"][0] - 1) * (spec["squares"][1] - 1)
    if corner_ids is None or len(corner_ids) != expected_corners:
        raise ValueError("Not all ChArUco chessboard corners were detected")
    # Check measured PDF vector geometry as well as the rasterized target.
    drawings = page.get_drawings()
    vector_black_rectangles = [item[1] for drawing in drawings for item in drawing["items"]
                              if item[0] == "re" and drawing.get("fill") == (0.0, 0.0, 0.0)]
    square_points = spec["square_mm"] * mm
    solid_squares = [r for r in vector_black_rectangles
                     if abs(r.width - square_points) < .002 and abs(r.height - square_points) < .002]
    if len(solid_squares) != spec["squares"][0] * spec["squares"][1] // 2:
        raise ValueError("PDF chessboard-square dimensions/count do not match")
    if preview_root:
        preview_root.mkdir(parents=True, exist_ok=True)
        page.get_pixmap(dpi=100, colorspace=pymupdf.csRGB, alpha=False).save(preview_root / (path.stem + ".png"))
    # Use the board's known geometry to independently compare all corner positions.
    left = (spec["page_mm"][0] - spec["squares"][0] * spec["square_mm"]) / 2
    top = (spec["page_mm"][1] - spec["squares"][1] * spec["square_mm"]) / 2
    expected_xy = board.getChessboardCorners()[corner_ids.reshape(-1), :2] * 1000
    expected_xy += np.array([left, top], dtype=np.float32)
    expected_px = expected_xy * dpi / 25.4
    # PDF raster pixel centers are displaced by at most roughly half a pixel.
    errors = np.linalg.norm(corners.reshape(-1, 2) - expected_px, axis=1)
    if float(np.max(errors)) > 1.6:
        raise ValueError("Detected corners do not match the nominal physical layout")
    document.close()
    return {"page_count": 1, "page_size_mm": actual_mm, "vector_only": True,
            "raster_validation_dpi": dpi, "markers_detected": len(actual_ids),
            "charuco_corners_detected": len(corner_ids),
            "max_corner_position_error_px": float(np.max(errors)),
            "nominal_square_side_mm": spec["square_mm"], "status": "passed",
            "note": "Validates PDF geometry and rendered detection; physical printer scale must still be measured."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("documentation/reference_markers"))
    parser.add_argument("--previews", type=Path, default=Path(".local/workflows/calibration_boards"))
    args = parser.parse_args()
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    args.output.mkdir(parents=True, exist_ok=True)
    names = [spec["name"] + suffix for spec in BOARDS for suffix in (".pdf", ".json")]
    if any((args.output / name).exists() for name in names):
        raise ValueError("An output board already exists; choose a new folder to preserve previous print targets")
    tools = {name: version(name) for name in ("opencv-python-headless", "numpy", "reportlab", "PyMuPDF", "pillow", "charset-normalizer")}
    for spec in BOARDS:
        board = board_definition(spec, dictionary)
        pdf = args.output / (spec["name"] + ".pdf")
        layout = make_pdf(pdf, spec, board, dictionary)
        validation = validate_pdf(pdf, spec, board, dictionary, args.previews)
        manifest = {"schema_version": 1, "target_type": "charuco_print_target", "board_id": spec["name"],
                    "paper": spec["paper"], "page_size_mm": spec["page_mm"], "squares_x_y": spec["squares"],
                    "square_length_m": spec["square_mm"] / 1000, "marker_length_m": spec["marker_mm"] / 1000,
                    "dictionary": "DICT_5X5_100", "dictionary_bytes_sha256": hashlib.sha256(dictionary.bytesList.tobytes()).hexdigest(),
                    "border_bits": 1, "legacy_pattern": False, "opencv_version": cv2.__version__,
                    "board_coordinates": "Origin at top-left of printed pattern; x right, y down, z into the page; all board points have z=0.",
                    "physical_dimensions_verified": False, "layout": layout, "generator_packages": tools,
                    "pdf": pdf.name, "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    "validation": validation,
                    "references": ["https://docs.opencv.org/4.13.0/df/d4a/tutorial_charuco_detection.html",
                                   "https://doi.org/10.1016/j.patcog.2014.01.005"]}
        (args.output / (spec["name"] + ".json")).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"pdf": str(pdf), "validation": validation}))


if __name__ == "__main__":
    main()
