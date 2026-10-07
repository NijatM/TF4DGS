"""Portable session metadata and calibration checks for fixed cameras."""
from pathlib import Path
import re

from .io import number, read_json, relative_path, write_json

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CAMERAS = (("dji", "DJI Osmo Action 6"), ("fuji", "Fujifilm X-T5"), ("iphone", "iPhone 15 Pro / Blackmagic Camera"))


def template(session_id):
    if not ID.fullmatch(session_id):
        raise ValueError("Session ID must contain only letters, digits, underscores or hyphens")
    return {
        "schema_version": 1, "session_id": session_id,
        "world": {"units": "unscaled", "metres_per_unit": None},
        "baseline": {"start_s": 0.0, "end_s": 2.0},
        "timeline": {"reference_camera": "dji", "start_s": 0.0, "end_s": 10.0,
                     "sample_fps": 10.0, "max_skew_s": 0.035},
        "cameras": [{"id": cid, "device": device, "video": f"raw/{cid}/capture.mp4",
                     "fixed_pose": True, "calibration": None,
                     "capture": {"lens_and_zoom_fixed": None, "stabilization": "unknown",
                                 "exposure_locked": None, "white_balance_locked": None},
                     "sync_points": [], "sync_uncertainty_s": None} for cid, device in CAMERAS],
    }


def initialize(path, session_id):
    path = Path(path)
    if path.exists():
        raise ValueError("Session folder already exists; refusing to overwrite it")
    value = template(session_id)
    for cid, _ in CAMERAS:
        (path / "raw" / cid).mkdir(parents=True)
    for name in ("calibration", "manifests", "frames", "baseline"):
        (path / name).mkdir()
    write_json(path / "session.json", value)
    return value


def load(path):
    path = Path(path).resolve()
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1 or not ID.fullmatch(str(value.get("session_id", ""))):
        raise ValueError("Unsupported session schema or invalid session ID")
    cameras = value.get("cameras", [])
    if not isinstance(cameras, list) or len(cameras) < 2:
        raise ValueError("A multi-camera session needs at least two cameras")
    ids = []
    for camera in cameras:
        if not isinstance(camera, dict):
            raise ValueError("Each camera must be a JSON object")
        cid = camera.get("id", "")
        if not isinstance(cid, str) or not ID.fullmatch(cid) or cid in ids:
            raise ValueError("Camera IDs must be unique portable identifiers")
        ids.append(cid)
        relative_path(path.parent, camera["video"])
        if camera.get("fixed_pose") is not True:
            raise ValueError(f"{cid}: this initial pipeline requires a fixed camera pose")
        if camera.get("calibration") is not None:
            relative_path(path.parent, camera["calibration"])
        points = camera.get("sync_points", [])
        if not isinstance(points, list) or any(not isinstance(p, dict) for p in points):
            raise ValueError("Synchronization cues must be a list of objects")
        if points:
            from .sync import fit_clock
            fit_clock(points)
        capture = camera.get("capture", {})
        if not isinstance(capture, dict):
            raise ValueError("Capture settings must be a JSON object")
        for key in ("lens_and_zoom_fixed", "exposure_locked", "white_balance_locked"):
            if capture.get(key) is not None and not isinstance(capture[key], bool):
                raise ValueError(f"{key} must be true, false or null")
        if capture.get("stabilization", "unknown") not in ("on", "off", "unknown"):
            raise ValueError("Stabilization must be on, off or unknown")
        uncertainty = camera.get("sync_uncertainty_s")
        if uncertainty is not None and number(uncertainty, "sync uncertainty") < 0:
            raise ValueError("Sync uncertainty cannot be negative")
    for section in ("timeline", "baseline", "world"):
        if not isinstance(value.get(section), dict):
            raise ValueError(f"{section} must be a JSON object")
    timeline = value["timeline"]
    if timeline["reference_camera"] not in ids:
        raise ValueError("Reference camera does not exist")
    start = number(timeline["start_s"], "timeline start")
    end = number(timeline["end_s"], "timeline end")
    if not start < end:
        raise ValueError("Timeline start must precede end")
    fps = number(timeline["sample_fps"], "sample fps", positive=True)
    number(timeline["max_skew_s"], "max skew", positive=True)
    if "max_sample_offset_s" in timeline:
        number(timeline["max_sample_offset_s"], "max sample offset", positive=True)
    if (end - start) * fps > 100000:
        raise ValueError("Timeline exceeds the foundation's 100,000-sample limit")
    baseline = value["baseline"]
    bs = number(baseline["start_s"], "baseline start")
    be = number(baseline["end_s"], "baseline end")
    if not start <= bs < be <= end:
        raise ValueError("Stable baseline must lie inside the session timeline")
    world = value["world"]
    if world["units"] not in ("unscaled", "metres"):
        raise ValueError("World units must be unscaled or metres")
    if world["units"] == "metres":
        number(world.get("metres_per_unit"), "metres per reconstruction unit", positive=True)
    elif world.get("metres_per_unit") is not None:
        raise ValueError("Set units to metres before supplying a physical scale")
    return value


def validate_calibration(calibration, cid):
    if not isinstance(calibration, dict) or calibration.get("schema_version") != 1 or calibration.get("camera_id") != cid:
        raise ValueError(f"{cid}: calibration schema/camera ID mismatch")
    w, h = calibration["image_size"]
    if any(isinstance(x, bool) or not isinstance(x, int) or x <= 0 for x in (w, h)):
        raise ValueError("Calibration dimensions must be positive integers")
    models = {"PINHOLE": 4, "OPENCV": 8}
    model = calibration["model"]
    params = calibration["params"]
    if model not in models or len(params) != models[model]:
        raise ValueError("Calibration supports PINHOLE (4 params) or OPENCV (8 params)")
    params = [number(x, "intrinsic parameter") for x in params]
    fx, fy, cx, cy = params[:4]
    if fx <= 0 or fy <= 0 or not (0 <= cx <= w and 0 <= cy <= h):
        raise ValueError("Invalid calibration focal length or principal point")
    pose = calibration["world_to_camera"]
    r, t = pose["R"], pose["t"]
    if len(r) != 3 or any(len(row) != 3 for row in r) or len(t) != 3:
        raise ValueError("world_to_camera requires a 3x3 R and 3-vector t")
    r = [[number(x, "rotation") for x in row] for row in r]
    [number(x, "translation") for x in t]
    for i in range(3):
        for j in range(3):
            if abs(sum(r[i][k] * r[j][k] for k in range(3)) - (1 if i == j else 0)) > 1e-4:
                raise ValueError("Rotation is not orthonormal")
    det = (r[0][0] * (r[1][1]*r[2][2]-r[1][2]*r[2][1])
           - r[0][1] * (r[1][0]*r[2][2]-r[1][2]*r[2][0])
           + r[0][2] * (r[1][0]*r[2][1]-r[1][1]*r[2][0]))
    if abs(det - 1) > 1e-4:
        raise ValueError("Rotation must have determinant +1")
    return calibration


def preflight(path):
    session = load(path)
    root = Path(path).resolve().parent
    missing, warnings, calibration_errors = [], [], []
    for camera in session["cameras"]:
        cid = camera["id"]
        if not relative_path(root, camera["video"]).is_file():
            missing.append(camera["video"])
        if not camera.get("sync_points"):
            warnings.append(f"{cid}: synchronization cues not entered")
        elif len(camera["sync_points"]) == 1:
            warnings.append(f"{cid}: offset only; end-to-end clock drift is unmeasured")
        capture = camera.get("capture", {})
        for field in ("lens_and_zoom_fixed", "exposure_locked", "white_balance_locked"):
            if capture.get(field) is not True:
                warnings.append(f"{cid}: {field} not confirmed")
        if capture.get("stabilization") != "off":
            warnings.append(f"{cid}: stabilization off is not confirmed; fixed intrinsics may be unsuitable")
        if camera.get("sync_uncertainty_s") is None:
            warnings.append(f"{cid}: sensor/timing uncertainty is not quantified")
        if camera.get("calibration") is None:
            calibration_errors.append(f"{cid}: calibration pending")
        else:
            try:
                calibration = validate_calibration(read_json(relative_path(root, camera["calibration"])), cid)
                if calibration.get("synthetic_only"):
                    calibration_errors.append(f"{cid}: synthetic calibration cannot establish real training readiness")
            except (ValueError, OSError, KeyError, TypeError) as exc:
                calibration_errors.append(f"{cid}: {exc}")
    return {"session_id": session["session_id"], "missing_videos": missing,
            "warnings": warnings, "calibration_errors": calibration_errors,
            "ready_to_probe": not missing,
            "ready_to_plan": not missing and all(c.get("sync_points") for c in session["cameras"]),
            "ready_for_training": False,
            "training_status": "Trainer integration and calibrated real-data validation are pending"}
