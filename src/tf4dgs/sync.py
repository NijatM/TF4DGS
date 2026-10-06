"""Clock fitting and nearest-frame pairing from measured presentation times."""
from bisect import bisect_left
import math

from .io import number


def fit_clock(points):
    if not points:
        raise ValueError("Enter at least one shared cue for every camera")
    pairs = [(number(p["camera_time_s"], "camera cue time"), number(p["session_time_s"], "session cue time")) for p in points]
    if len({x for x, _ in pairs}) != len(pairs):
        raise ValueError("Camera cue times must be distinct")
    if len(pairs) == 1:
        scale, offset = 1.0, pairs[0][1] - pairs[0][0]
    else:
        mx = sum(x for x, _ in pairs) / len(pairs)
        my = sum(y for _, y in pairs) / len(pairs)
        denominator = sum((x-mx)**2 for x, _ in pairs)
        scale = sum((x-mx)*(y-my) for x, y in pairs) / denominator
        offset = my - scale * mx
    if not math.isfinite(scale) or not math.isfinite(offset) or scale <= 0:
        raise ValueError("Synchronization cues produce an invalid clock transform")
    residual = max(abs(scale*x + offset-y) for x, y in pairs)
    return {"scale": scale, "offset_s": offset, "drift_estimated": len(pairs) >= 2,
            "cue_count": len(pairs), "fit_residual_max_s": residual,
            "drift_ppm": (scale-1)*1e6,
            "uncertainty_note": "Cue residual is not sensor synchronization accuracy; two cues fit exactly by construction."}


def aligned_frames(probe, clock):
    frames = probe["frames"]
    if not frames:
        raise ValueError("Video has no decoded frame timestamps")
    result = []
    for expected, frame in enumerate(frames):
        if frame["index"] != expected:
            raise ValueError("Frame indices must enumerate every decoded source frame from zero")
        local = number(frame["camera_time_s"], "frame camera time")
        time = local * clock["scale"] + clock["offset_s"]
        if result and time <= result[-1]["time_s"]:
            raise ValueError("Frame presentation times must increase strictly")
        result.append({"index": expected, "time_s": time, "camera_time_s": local,
                       "media_pts_s": number(frame["media_pts_s"], "media PTS")})
    return result


def nearest(frames, times, target):
    i = bisect_left(times, target)
    choices = [j for j in (i-1, i) if 0 <= j < len(frames)]
    return min(choices, key=lambda j: (abs(times[j]-target), j))


def make_plan(session, probes):
    timeline = session["timeline"]
    reference = timeline["reference_camera"]
    clocks, frames, times, warnings = {}, {}, {}, []
    for camera in session["cameras"]:
        cid = camera["id"]
        clocks[cid] = fit_clock(camera["sync_points"])
        frames[cid] = aligned_frames(probes[cid], clocks[cid])
        times[cid] = [f["time_s"] for f in frames[cid]]
        if len(camera["sync_points"]) < 2:
            warnings.append(f"{cid}: clock drift not measured")
        if abs(clocks[cid]["drift_ppm"]) > 5000:
            warnings.append(f"{cid}: fitted drift exceeds 5000 ppm; check cue times and recording modes")
        if clocks[cid]["fit_residual_max_s"] > timeline["max_skew_s"]:
            raise ValueError(f"{cid}: sync-cue residual exceeds allowed frame skew")
    start, end, fps, tolerance = (timeline[k] for k in ("start_s", "end_s", "sample_fps", "max_skew_s"))
    used = {cid: set() for cid in frames}
    bundles, rejected = [], []
    for step in range(math.ceil((end-start)*fps)):
        target = start + step / fps
        if target >= end:
            break
        ri = nearest(frames[reference], times[reference], target)
        rt = times[reference][ri]
        if abs(rt-target) > tolerance or not start <= rt < end:
            rejected.append({"requested_time_s": target, "reason": "reference coverage/skew"})
            continue
        selected = {cid: nearest(frames[cid], times[cid], rt) for cid in frames}
        view_times = [times[cid][i] for cid, i in selected.items()]
        if max(view_times)-min(view_times) > tolerance:
            rejected.append({"requested_time_s": target, "reason": "cross-camera skew"})
            continue
        if any(i in used[cid] for cid, i in selected.items()):
            rejected.append({"requested_time_s": target, "reason": "would reuse a source frame"})
            continue
        views = {}
        for cid, i in selected.items():
            used[cid].add(i)
            f = frames[cid][i]
            views[cid] = {"source_index": f["index"], "camera_time_s": f["camera_time_s"],
                          "media_pts_s": f["media_pts_s"], "aligned_time_s": f["time_s"],
                          "delta_to_reference_s": f["time_s"]-rt,
                          "image": f"frames/{cid}/frame_{len(used[cid])-1:06d}.png"}
        bundles.append({"time_s": rt, "normalized_time": (rt-start)/(end-start),
                        "requested_time_s": target, "views": views})
    return {"schema_version": 1, "session_id": session["session_id"], "clocks": clocks,
            "timeline": timeline, "warnings": warnings, "bundles": bundles,
            "rejected_samples": rejected,
            "timestamp_convention": "camera_time_s is media PTS minus first decoded video PTS; affine transform gives session seconds",
            "sensor_sync_accuracy_verified": False}
