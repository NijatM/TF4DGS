import argparse
import json
from pathlib import Path
import subprocess
import sys

from .analysis import analyse, synthetic_tracks, validate_tracks
from .io import read_json, write_json
from .media import extract_session, probe_session
from .session import initialize, load, preflight
from .sync import make_plan


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tf4dgs", description="TF4DGS capture and analysis foundation (GPU trainer pending)")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init-session", help="Create ignored capture folders and an incomplete session template")
    init.add_argument("path", type=Path)
    init.add_argument("--id", default="dynamic_001")
    for name in ("validate", "probe", "plan", "extract"):
        p = sub.add_parser(name)
        p.add_argument("session", type=Path, help="Path to session.json")
        if name == "probe":
            p.add_argument("--ffprobe")
        elif name == "extract":
            p.add_argument("--ffmpeg")
    analysis = sub.add_parser("analyse", help="Export selected-point scalar fields and trails for a sampled time")
    analysis.add_argument("tracks", type=Path)
    analysis.add_argument("--frame", type=int, required=True)
    analysis.add_argument("--mode", choices=("since_start", "recent"), default="since_start")
    analysis.add_argument("--history", type=float, default=5)
    analysis.add_argument("--output", type=Path)
    demo = sub.add_parser("serve-preview", help="Interactive point demo; no Gaussian reconstruction")
    demo.add_argument("--tracks", type=Path, help="Optional assigned-point/persistent-ID track JSON; defaults to synthetic data")
    demo.add_argument("--port", type=int, default=8094)
    args = parser.parse_args(argv)
    try:
        if args.command == "init-session":
            initialize(args.path, args.id)
            result = {"session": str(args.path / "session.json"), "status": "awaiting_recordings_and_calibration"}
        elif args.command == "validate":
            result = preflight(args.session)
        elif args.command == "probe":
            probes = probe_session(args.session, args.ffprobe)
            result = {cid: {"frame_count": len(p["frames"]), "image_size": [p["stream"]["width"], p["stream"]["height"]]} for cid, p in probes.items()}
        elif args.command == "plan":
            session = load(args.session)
            root = args.session.resolve().parent
            probes = {c["id"]: read_json(root / f"manifests/{c['id']}.frames.json") for c in session["cameras"]}
            plan = make_plan(session, probes)
            write_json(root / "manifests/sync-plan.json", plan)
            result = {"paired_samples": len(plan["bundles"]), "rejected_samples": len(plan["rejected_samples"]), "warnings": plan["warnings"]}
        elif args.command == "extract":
            result = extract_session(args.session, args.session.resolve().parent / "manifests/sync-plan.json", args.ffmpeg)
        elif args.command == "analyse":
            result = analyse(validate_tracks(read_json(args.tracks)), args.frame, args.mode, args.history)
            if args.output:
                write_json(args.output, result)
        else:
            from .preview import serve
            tracks = read_json(args.tracks) if args.tracks else synthetic_tracks()
            serve(tracks, args.port)
            return 0
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"TF4DGS: {exc}", file=sys.stderr)
        return 2
