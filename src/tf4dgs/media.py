"""Probe real PTS and extract synchronized native-size PNGs without shell commands."""
import hashlib
from pathlib import Path
import shutil
import struct
import subprocess

from .io import read_json, relative_path, write_json
from .session import load
from .sync import make_plan

PROJECT = Path(__file__).resolve().parents[2]


def select_expression(indices):
    """Balance membership tests to avoid FFmpeg's expression depth limit."""
    terms = [f"eq(n,{index})" for index in indices]
    if not terms:
        raise ValueError("Frame selection must not be empty")
    while len(terms) > 1:
        terms = [f"({terms[i]}+{terms[i+1]})" if i+1 < len(terms) else terms[i]
                 for i in range(0, len(terms), 2)]
    return terms[0]


def executable(name, explicit=None):
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_file():
            raise ValueError(f"Executable not found: {path}")
        return str(path)
    for path in sorted((PROJECT / ".local/tools/ffmpeg-9.0.2").glob(f"**/{name}.exe")):
        return str(path)
    path = shutil.which(name)
    if not path:
        raise ValueError(f"{name} not found; provide its executable path")
    return path


def fingerprint(path):
    with Path(path).open("rb") as stream:
        return {"bytes": Path(path).stat().st_size, "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}


def probe_video(path, ffprobe=None):
    import json
    command = [executable("ffprobe", ffprobe), "-v", "error", "-select_streams", "v:0",
               "-show_frames", "-show_streams", "-show_format", "-show_entries",
               "frame=best_effort_timestamp_time,pts_time,width,height:stream=index,codec_name,width,height,avg_frame_rate,r_frame_rate,time_base,color_space,color_transfer,color_primaries:stream_side_data=rotation:format=duration",
               "-of", "json", str(Path(path).resolve())]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if len(data.get("streams", [])) != 1:
        raise ValueError("Expected one selected video stream")
    stream = data["streams"][0]
    raw = data.get("frames", [])
    if not raw:
        raise ValueError("No decoded video frames found")
    frames = []
    for i, frame in enumerate(raw):
        stamp = frame.get("best_effort_timestamp_time", frame.get("pts_time"))
        if stamp is None:
            raise ValueError("Missing decoded frame PTS; nominal FPS is not an acceptable substitute")
        pts = float(stamp)
        if not frames:
            first = pts
        if (frame.get("width"), frame.get("height")) != (stream["width"], stream["height"]):
            raise ValueError("Video dimensions change during capture; fixed calibration is unsuitable")
        frames.append({"index": i, "media_pts_s": pts, "camera_time_s": pts-first})
    # Check finiteness and ordering even before a sync plan is created.
    from .sync import aligned_frames
    aligned_frames({"frames": frames}, {"scale": 1.0, "offset_s": 0.0})
    deltas = [frames[i]["camera_time_s"]-frames[i-1]["camera_time_s"] for i in range(1, len(frames))]
    return {"schema_version": 1, "stream": stream, "frames": frames,
            "first_media_pts_s": first, "fingerprint": fingerprint(path),
            "frame_interval_min_s": min(deltas) if deltas else None,
            "frame_interval_max_s": max(deltas) if deltas else None,
            "decoded_coordinates": "coded pixels; extraction disables autorotation; no resize"}


def probe_session(path, ffprobe=None):
    session = load(path)
    root = Path(path).resolve().parent
    destinations = [root / f"manifests/{camera['id']}.frames.json" for camera in session["cameras"]]
    if any(p.exists() for p in destinations):
        raise ValueError("Probe manifests already exist; archive them before reprobe")
    results = {}
    for camera, destination in zip(session["cameras"], destinations):
        result = probe_video(relative_path(root, camera["video"]), ffprobe)
        result["video"] = camera["video"]
        write_json(destination, result)
        results[camera["id"]] = result
    return results


def png_size(path):
    with Path(path).open("rb") as stream:
        head = stream.read(24)
    if len(head) != 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG output")
    return struct.unpack(">II", head[16:24])


def extract_session(path, plan_path, ffmpeg=None):
    session = load(path)
    root = Path(path).resolve().parent
    plan = read_json(plan_path)
    if plan.get("session_id") != session["session_id"] or not plan.get("bundles"):
        raise ValueError("A nonempty synchronization plan for this session is required")
    marker = root / "manifests/extraction.json"
    if marker.exists():
        raise ValueError("An extraction record already exists; refusing to overwrite it")
    probes = {c["id"]: read_json(root / f"manifests/{c['id']}.frames.json") for c in session["cameras"]}
    if plan != make_plan(session, probes):
        raise ValueError("Synchronization plan is stale or edited; regenerate it from the current session and probes")
    prepared = []
    for camera in session["cameras"]:
        cid = camera["id"]
        probe = probes[cid]
        video = relative_path(root, camera["video"])
        if fingerprint(video) != probe["fingerprint"]:
            raise ValueError(f"{cid}: source video differs from the probed file")
        if probe["stream"].get("color_transfer") in ("smpte2084", "arib-std-b67"):
            raise ValueError(f"{cid}: HDR color normalization must be selected before 8-bit PNG extraction")
        frames_dir = root / "frames" / cid
        if frames_dir.exists() and any(frames_dir.iterdir()):
            raise ValueError(f"{cid}: output frames already exist")
        indices = [b["views"][cid]["source_index"] for b in plan["bundles"]]
        if indices != sorted(set(indices)):
            raise ValueError("Source indices must increase without reuse")
        for bundle in plan["bundles"]:
            index = bundle["views"][cid]["source_index"]
            if not 0 <= index < len(probe["frames"]):
                raise ValueError("Source index lies outside the probed video")
        prepared.append((cid, video, frames_dir, indices, probe))
    record = {"schema_version": 1, "status": "in_progress", "cameras": [],
              "format": "8-bit RGB PNG", "autorotation": False, "resize": False,
              "color_note": "No exposure, gamut or cross-camera color calibration is applied. Unknown/log transfer requires review before appearance analysis."}
    write_json(marker, record)
    for cid, video, destination, indices, probe in prepared:
        destination.mkdir(parents=True, exist_ok=True)
        filter_path = root / f"manifests/{cid}.select-filter.txt"
        # FFmpeg 9 reads the filter argument from a file with -/filter:v.
        filter_path.write_text("select='" + select_expression(indices) + "'", encoding="utf-8")
        command = [executable("ffmpeg", ffmpeg), "-hide_banner", "-loglevel", "error", "-n",
                   "-noautorotate", "-i", str(video), "-map", "0:v:0", "-/filter:v", str(filter_path),
                   "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-start_number", "0",
                   str(destination / "frame_%06d.png")]
        subprocess.run(command, check=True)
        files = sorted(destination.glob("frame_*.png"))
        expected_size = (probe["stream"]["width"], probe["stream"]["height"])
        if len(files) != len(indices) or any(png_size(p) != expected_size for p in files):
            raise ValueError(f"{cid}: extracted frame count/dimensions mismatch")
        record["cameras"].append({"id": cid, "frames": len(files), "image_size": list(expected_size),
                                  "source_fingerprint": probe["fingerprint"]})
        write_json(marker, record, overwrite=True)
    record["status"] = "complete"
    write_json(marker, record, overwrite=True)
    return record
