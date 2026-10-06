"""Selected-point metrics with stable IDs and explicit missing correspondence.

RGB distance is Euclidean distance in declared normalized linear RGB, not DeltaE,
wetness, pigment change, physical strain or speed. Recent activity is a fading
sum of observed increments, retaining out-and-return motion.
"""
import math

from .io import number


def vector(value, label, *, rgb=False):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{label} must contain three numbers")
    values = [number(x, label) for x in value]
    if rgb and any(not 0 <= x <= 1 for x in values):
        raise ValueError("RGB must be normalized to [0,1]")
    return values


def validate_tracks(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("color_space") != "linear_rgb":
        raise ValueError("Tracks require schema 1 and declared linear_rgb colors")
    if data.get("identity_kind") not in ("assigned_points", "persistent_gaussian_ids"):
        raise ValueError("Declare assigned_points or persistent_gaussian_ids; row order is not identity")
    frames = data.get("frames", [])
    if not isinstance(frames, list) or not frames:
        raise ValueError("Tracks contain no frames")
    previous = -math.inf
    for frame in frames:
        if not isinstance(frame, dict) or not isinstance(frame.get("points"), list):
            raise ValueError("Each track frame must be an object with a points list")
        time = number(frame["time_s"], "track time")
        if time <= previous:
            raise ValueError("Track times must increase strictly")
        previous = time
        ids = set()
        for point in frame["points"]:
            if not isinstance(point, dict):
                raise ValueError("Each point must be a JSON object")
            pid = point["id"]
            if not isinstance(pid, str) or not pid or pid in ids:
                raise ValueError("Point IDs must be nonempty strings, unique in each frame")
            ids.add(pid)
            if point.get("status", "tracked") not in ("tracked", "new", "occluded", "unsupported"):
                raise ValueError("Invalid point validity status")
            if point.get("position") is not None:
                vector(point["position"], "position")
            if point.get("rgb") is not None:
                vector(point["rgb"], "rgb", rgb=True)
    baseline = data.get("reference_frame", 0)
    if isinstance(baseline, bool) or not isinstance(baseline, int) or not 0 <= baseline < len(frames):
        raise ValueError("Reference frame index is invalid")
    scale = data.get("metres_per_unit")
    if scale is not None:
        number(scale, "metres per unit", positive=True)
    return data


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def supported(point):
    return point is not None and point.get("status", "tracked") == "tracked"


def analyse(data, frame_index, mode="since_start", history_s=5.0):
    if mode not in ("since_start", "recent"):
        raise ValueError("Analysis mode must be since_start or recent")
    history_s = number(history_s, "history duration", positive=True)
    frames = data["frames"]
    if isinstance(frame_index, bool) or not isinstance(frame_index, int) or not 0 <= frame_index < len(frames):
        raise ValueError("Frame index is out of range")
    reference_index = data.get("reference_frame", 0)
    maps = [{p["id"]: p for p in f["points"]} for f in frames[:frame_index+1]]
    reference = {p["id"]: p for p in frames[reference_index]["points"]}
    current = frames[frame_index]
    now = current["time_s"]
    scale = data.get("metres_per_unit") or 1.0
    output = []
    for point in current["points"]:
        pid = point["id"]
        base = reference.get(pid)
        geometry, appearance, segments, reason = None, None, [], None
        if not supported(point):
            reason = point.get("status", "unsupported")
        elif frame_index < reference_index:
            reason = "before reference frame"
        elif mode == "since_start":
            if not supported(base):
                reason = "no stable reference correspondence"
            else:
                if point.get("position") is not None and base.get("position") is not None:
                    geometry = distance(point["position"], base["position"]) * scale
                if point.get("rgb") is not None and base.get("rgb") is not None:
                    appearance = distance(point["rgb"], base["rgb"])
        else:
            # Zero is valid only if at least one contiguous supported observation
            # pair exists in the history window. Gaps never become fake zeroes.
            motion_values, color_values = [], []
            for i in range(max(1, reference_index+1), frame_index+1):
                older, newer = maps[i-1].get(pid), maps[i].get(pid)
                if not supported(older) or not supported(newer):
                    continue
                t0, t1 = frames[i-1]["time_s"], frames[i]["time_s"]
                if t0 < now-history_s or t1 > now:
                    continue
                weight = max(0.0, 1.0-(now-t1)/history_s)
                if older.get("position") is not None and newer.get("position") is not None:
                    motion_values.append(distance(older["position"], newer["position"])*scale*weight)
                if older.get("rgb") is not None and newer.get("rgb") is not None:
                    color_values.append(distance(older["rgb"], newer["rgb"])*weight)
            if motion_values:
                geometry = sum(motion_values)
            if color_values:
                appearance = sum(color_values)
            if geometry is None and appearance is None:
                reason = "no contiguous recent correspondence"
        # Trails use the recent window in both comparison modes and cannot
        # bridge missing/occluded/new identities or the reference boundary.
        if supported(point) and frame_index >= reference_index:
            for i in range(max(1, reference_index+1), frame_index+1):
                older, newer = maps[i-1].get(pid), maps[i].get(pid)
                t0, t1 = frames[i-1]["time_s"], frames[i]["time_s"]
                if t0 < now-history_s or not supported(older) or not supported(newer):
                    continue
                if older.get("position") is None or newer.get("position") is None:
                    continue
                segments.append({"from": older["position"], "to": newer["position"],
                                 "alpha": max(0.0, 1.0-(now-t1)/history_s)})
        output.append({"id": pid, "position": point.get("position"), "rgb": point.get("rgb"),
                       "status": point.get("status", "tracked"), "geometry": geometry,
                       "appearance": appearance, "reason": reason, "trail": segments})
    return {"time_s": now, "frame_index": frame_index, "mode": mode, "history_s": history_s,
            "geometry_units": "m" if data.get("metres_per_unit") is not None else "reconstruction units",
            "geometry_quantity": "reference displacement" if mode == "since_start" else "fading motion activity",
            "appearance_quantity": "linear RGB distance" if mode == "since_start" else "fading linear RGB activity",
            "points": output}


def synthetic_tracks():
    frames = []
    for i in range(33):
        time = i / 4
        out_return = 0.7 * math.sin(math.pi*time/4)**2
        color = min(1.0, max(0.0, (time-2)/2))
        points = [
            {"id": "color_only", "position": [-0.9, 0, 0], "rgb": [0.15+0.65*color, 0.55-0.4*color, 0.2]},
            {"id": "out_and_return", "position": [0, out_return, 0], "rgb": [0.2, 0.45, 0.8]},
            {"id": "combined", "position": [0.9, out_return*0.7, 0.2*math.sin(time)], "rgb": [0.2+0.5*color, 0.5, 0.1]},
            {"id": "static", "position": [0, -0.5, -0.4], "rgb": [0.45, 0.45, 0.45]},
        ]
        if not 3 <= time <= 4:
            points.append({"id": "occlusion_demo", "position": [-0.5, 0.35, 0.3], "rgb": [0.4, 0.2, 0.7]})
        if time >= 5:
            points.append({"id": "new_surface", "position": [0.5, 0.4, -0.3], "rgb": [0.7, 0.3, 0.2],
                           "status": "new" if time == 5 else "tracked"})
        frames.append({"time_s": time, "points": points})
    return {"schema_version": 1, "synthetic": True, "identity_kind": "assigned_points",
            "color_space": "linear_rgb", "reference_frame": 0, "metres_per_unit": None,
            "title": "Synthetic selected-point analysis", "frames": frames}
