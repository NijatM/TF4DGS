"""Create grouped editable SVGs and an Illustrator native-AI creation script.

The Adobe script needs Illustrator; it is not executed by this Python tool.
Existing verified PDF/JSON targets are read and preserved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import pymupdf

PRINT = runpy.run_path(str(Path(__file__).with_name("Create-CalibrationBoards.py")))
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
PT = 72 / 25.4


def add(parent, kind, **attributes):
    return ET.SubElement(parent, f"{{{NS}}}{kind}", {key.replace("_", "-"): str(value) for key, value in attributes.items()})


def number(value):
    return format(value, ".9f").rstrip("0").rstrip(".")


def artwork(spec, dictionary):
    width, height = spec["page_mm"]
    nx, ny = spec["squares"]
    square, marker = spec["square_mm"], spec["marker_mm"]
    left, top = (width - nx * square) / 2, (height - ny * square) / 2
    root = ET.Element(f"{{{NS}}}svg", {"width": f"{width}mm", "height": f"{height}mm",
                                     "viewBox": f"0 0 {width} {height}", "version": "1.1"})
    add(root, "title").text = spec["name"] + " - editable artwork"
    add(root, "desc").text = "Exact-size ChArUco; DICT_5X5_100; legacyPattern=false. Changes to marker geometry require updated calibration and validation."
    layers = []

    def layer(name):
        value = {"name": name, "rectangles": [], "markers": [], "lines": [], "texts": []}
        layers.append(value)
        return add(root, "g", id=name), value

    paper, data = layer("Paper")
    add(paper, "rect", id="Paper_background", x=0, y=0, width=width, height=height, fill="#ffffff")
    data["rectangles"].append(["Paper background", 0, 0, width, height, 0])
    checker, check_data = layer("Checkerboard")
    markers, marker_data = layer("Markers")
    module, margin, next_id = marker / 7, (square - marker) / 2, 0
    for row in range(ny):
        for col in range(nx):
            x, y = left + col * square, top + row * square
            if row % 2 == col % 2:
                name = f"Square_r{row}_c{col}"
                add(checker, "rect", id=name, x=number(x), y=number(y), width=square, height=square, fill="#000000")
                check_data["rectangles"].append([name, x, y, square, square, 100])
                continue
            bits = cv2.aruco.generateImageMarker(dictionary, next_id, 7, borderBits=1)
            paths, rectangles = [], []
            for bit_row in range(7):
                for bit_col in range(7):
                    if bits[bit_row, bit_col] != 0:
                        continue
                    px, py = x + margin + bit_col * module, y + margin + bit_row * module
                    x0, y0, x1, y1 = map(number, (px, py, px + module, py + module))
                    paths.append(f"M{x0},{y0} H{x1} V{y1} H{x0} Z")
                    rectangles.append([px, py, module, module])
            name = f"Marker_ID_{next_id:03d}"
            group = add(markers, "g", id=name)
            add(group, "path", id=name + "_bits", d=" ".join(paths), fill="#000000", fill_rule="nonzero")
            marker_data["markers"].append({"name": name, "id": next_id, "rectangles": rectangles})
            next_id += 1

    measurements, measure_data = layer("Measurements")
    def line(x1, y1, x2, y2, name):
        add(measurements, "line", id=name, x1=number(x1), y1=number(y1), x2=number(x2), y2=number(y2),
            stroke="#000000", stroke_width=number(.35 / PT), fill="none")
        measure_data["lines"].append([name, x1, y1, x2, y2])
    line(left, height - 9, left + 100, height - 9, "Horizontal_100mm")
    for offset in (0, 50, 100):
        line(left + offset, height - 10.5, left + offset, height - 7.5, f"Horizontal_tick_{offset}")
    gx, gy = width - 12, top + (ny * square - 100) / 2
    line(gx, gy, gx, gy + 100, "Vertical_100mm")
    for offset in (0, 50, 100):
        line(gx - 1.5, gy + offset, gx + 1.5, gy + offset, f"Vertical_tick_{offset}")

    labels, label_data = layer("Labels")
    def label(name, x, y, content, size=8, anchor="start", rotation=0):
        attributes = {"id": name, "x": number(x), "y": number(y), "font_family": "Arial, Helvetica, sans-serif",
                      "font_size": number(size / PT), "fill": "#000000", "text_anchor": anchor}
        if rotation:
            attributes["transform"] = f"rotate({rotation} {number(x)} {number(y)})"
        add(labels, "text", **attributes).text = content
        label_data["texts"].append({"name": name, "x": x, "y": y, "content": content,
                                    "size_pt": size, "anchor": anchor, "rotation": rotation})
    label("Title", left, 8, "TF4DGS | ChArUco calibration target", 11)
    inches = "11 x 8.5 in" if spec["paper"] == "US LETTER" else "17 x 11 in"
    label("Paper_size", width - 12, 8, f"{spec['paper']} | {inches} | LANDSCAPE", anchor="end")
    label("Board_definition", left, 13,
          f"DICT_5X5_100 | {nx} x {ny} squares | square {square:g} mm | marker {marker:g} mm | legacyPattern=false")
    label("Horizontal_scale_label", left, height - 12.5, "HORIZONTAL CHECK: endpoint ticks must be 100 mm apart", 7)
    label("Vertical_scale_label", gx + 4, gy + 100, "VERTICAL CHECK: 100 mm", 7, rotation=-90)
    label("Pattern_dimensions", left + 125, height - 12.5, f"Pattern: {nx*square:g} x {ny*square:g} mm | IDs 0-{next_id-1}", 7)
    label("Print_instructions", left, height - 4.8, "PRINT AT 100% / ACTUAL SIZE. Disable Fit/Shrink. Check BOTH rulers; keep the target flat and matte.", 7)
    ET.indent(root, space="  ")
    return root, {"name": spec["name"], "width_mm": width, "height_mm": height, "layers": layers}


def validate_svg(path, spec, board, previews):
    root = ET.parse(path).getroot()
    if root.get("width") != f"{spec['page_mm'][0]}mm" or root.get("height") != f"{spec['page_mm'][1]}mm":
        raise ValueError("SVG physical page dimensions mismatch")
    if root.findall(f".//{{{NS}}}image"):
        raise ValueError("Editable SVG contains a raster image")
    for axis in ("Horizontal", "Vertical"):
        ruler = root.find(f".//{{{NS}}}line[@id='{axis}_100mm']")
        length = float(np.hypot(float(ruler.get("x2"))-float(ruler.get("x1")), float(ruler.get("y2"))-float(ruler.get("y1"))))
        if abs(length - 100) > 1e-6:
            raise ValueError("SVG ruler dimensions mismatch")
    document = pymupdf.open(path)
    page = document[0]
    if any(abs(actual / PT - expected) > .001 for actual, expected in zip((page.rect.width, page.rect.height), spec["page_mm"])):
        raise ValueError("Rendered SVG dimensions mismatch")
    pix = page.get_pixmap(dpi=240, colorspace=pymupdf.csGRAY, alpha=False)
    gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    corners, corner_ids, _, marker_ids = cv2.aruco.CharucoDetector(board).detectBoard(gray)
    if marker_ids is None or sorted(marker_ids.reshape(-1).tolist()) != board.getIds().reshape(-1).tolist():
        raise ValueError("SVG marker detection mismatch")
    if corner_ids is None or len(corner_ids) != (spec["squares"][0]-1)*(spec["squares"][1]-1):
        raise ValueError("SVG ChArUco corners mismatch")
    left, top = ((spec["page_mm"][i]-spec["squares"][i]*spec["square_mm"])/2 for i in (0, 1))
    expected = (board.getChessboardCorners()[corner_ids.reshape(-1), :2]*1000 + [left, top])*240/25.4
    error = float(np.max(np.linalg.norm(corners.reshape(-1, 2)-expected, axis=1)))
    if error > 1.6:
        raise ValueError("SVG corner positions mismatch")
    previews.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(dpi=100, colorspace=pymupdf.csRGB, alpha=False).save(previews / (path.stem + "_editable.png"))
    document.close()
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "status": "passed",
            "markers_detected": len(marker_ids), "charuco_corners_detected": len(corner_ids),
            "max_corner_position_error_px": error, "dpi": 240,
            "groups": [g.get("id") for g in root.findall(f"{{{NS}}}g")]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("documentation/reference_markers"))
    parser.add_argument("--previews", type=Path, default=Path(".local/workflows/calibration_boards"))
    args = parser.parse_args()
    builder = args.output / "Create-Native-Illustrator-Boards.jsx"
    report = args.output / "editable_artwork_validation.json"
    outputs = [args.output / (s["name"] + ".svg") for s in PRINT["BOARDS"]] + [builder, report]
    if any(path.exists() for path in outputs):
        raise ValueError("Editable outputs already exist; preserve them before generating a new set")
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    native_data, validation = [], []
    for spec in PRINT["BOARDS"]:
        manifest = json.loads((args.output / (spec["name"] + ".json")).read_text(encoding="utf-8"))
        pdf = args.output / manifest["pdf"]
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != manifest["pdf_sha256"]:
            raise ValueError("Original PDF differs from the verified target")
        if manifest["squares_x_y"] != spec["squares"] or manifest["square_length_m"]*1000 != spec["square_mm"] or manifest["marker_length_m"]*1000 != spec["marker_mm"]:
            raise ValueError("Original target definition differs from the editable artwork")
        board = PRINT["board_definition"](spec, dictionary)
        root, data = artwork(spec, dictionary)
        svg = args.output / (spec["name"] + ".svg")
        ET.ElementTree(root).write(svg, encoding="utf-8", xml_declaration=True)
        validation.append(validate_svg(svg, spec, board, args.previews))
        native_data.append(data)
    template = Path(__file__).with_name("Illustrator-Boards.template.jsx").read_text(encoding="utf-8")
    if template.count("__BOARD_DATA__") != 1:
        raise ValueError("Invalid Illustrator builder template")
    builder.write_text(template.replace("__BOARD_DATA__", json.dumps(native_data, separators=(",", ":"))), encoding="utf-8")
    value = {"svg_validation": validation, "illustrator_builder": builder.name,
             "illustrator_runtime_tested": False,
             "note": "SVG geometry and rendered detection passed. Native .ai files are created by Illustrator when the JSX is run; Illustrator was not available here."}
    report.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
