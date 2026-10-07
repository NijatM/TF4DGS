import copy
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tf4dgs.io import write_json
from tf4dgs.media import executable, extract_session, png_size, probe_session
from tf4dgs.session import initialize
from tf4dgs.sync import make_plan


class MediaIntegrationTests(unittest.TestCase):
    def test_long_sparse_selection_extracts_the_correct_source_frames(self):
        try:
            ffmpeg, ffprobe = executable("ffmpeg"), executable("ffprobe")
        except ValueError as exc:
            self.skipTest(str(exc))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "long_capture"
            value = initialize(root, "long_capture")
            value["cameras"] = value["cameras"][:2]
            value["timeline"].update(end_s=10, sample_fps=20, max_skew_s=.001, max_sample_offset_s=.017)
            for camera in value["cameras"]:
                camera["sync_points"] = [{"camera_time_s": 0, "session_time_s": 0}]
                subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-f", "lavfi",
                                "-i", "testsrc2=size=64x48:rate=30:duration=10", "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", str(root / camera["video"])], check=True)
            session_path = root / "session.json"
            write_json(session_path, value, overwrite=True)
            probes = probe_session(session_path, ffprobe)
            plan = make_plan(value, probes)
            self.assertEqual(len(plan["bundles"]), 200)
            plan_path = root / "manifests/sync-plan.json"
            write_json(plan_path, plan)
            result = extract_session(session_path, plan_path, ffmpeg)
            self.assertEqual(result["status"], "complete")
            for camera in value["cameras"]:
                files = sorted((root / "frames" / camera["id"]).glob("*.png"))
                self.assertEqual(len(files), 200)
                for sample in (0, 100, 199):
                    index = plan["bundles"][sample]["views"][camera["id"]]["source_index"]
                    check = root / f"{camera['id']}_{sample}_verification.png"
                    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-noautorotate",
                                    "-i", str(root / camera["video"]), "-vf", f"select=eq(n\\,{index})",
                                    "-frames:v", "1", "-pix_fmt", "rgb24", "-update", "1", str(check)], check=True)
                    self.assertEqual(hashlib.sha256(files[sample].read_bytes()).digest(),
                                     hashlib.sha256(check.read_bytes()).digest())

    def test_three_different_frame_rates_extract_native_frames(self):
        try:
            ffmpeg, ffprobe = executable("ffmpeg"), executable("ffprobe")
        except ValueError as exc:
            self.skipTest(str(exc))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "synthetic_capture"
            value = initialize(root, "synthetic_capture")
            value["timeline"].update(end_s=1, sample_fps=4, max_skew_s=.07)
            value["baseline"]["end_s"] = .25
            for camera, fps in zip(value["cameras"], (12, 8, 16)):
                camera["sync_points"] = [{"camera_time_s": 0, "session_time_s": 0}]
                subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-f", "lavfi",
                                "-i", f"testsrc2=size=160x96:rate={fps}:duration=1", "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", str(root / camera["video"])], check=True)
            session_path = root / "session.json"
            write_json(session_path, value, overwrite=True)
            probes = probe_session(session_path, ffprobe)
            self.assertEqual([len(probes[c["id"]]["frames"]) for c in value["cameras"]], [12, 8, 16])
            plan = make_plan(value, probes)
            self.assertEqual(len(plan["bundles"]), 4)
            plan_path = root / "manifests/sync-plan.json"
            stale = copy.deepcopy(plan)
            stale["bundles"][0]["views"]["dji"]["source_index"] = 1
            write_json(plan_path, stale)
            with self.assertRaisesRegex(ValueError, "stale or edited"):
                extract_session(session_path, plan_path, ffmpeg)
            self.assertFalse((root / "manifests/extraction.json").exists())
            write_json(plan_path, plan, overwrite=True)
            video = root / value["cameras"][0]["video"]
            original = video.read_bytes()
            video.write_bytes(original + b"changed source")
            with self.assertRaisesRegex(ValueError, "differs from the probed file"):
                extract_session(session_path, plan_path, ffmpeg)
            video.write_bytes(original)
            manifest = root / "manifests/dji.frames.json"
            hdr = copy.deepcopy(probes["dji"])
            hdr["stream"]["color_transfer"] = "smpte2084"
            write_json(manifest, hdr, overwrite=True)
            with self.assertRaisesRegex(ValueError, "HDR color normalization"):
                extract_session(session_path, plan_path, ffmpeg)
            write_json(manifest, probes["dji"], overwrite=True)
            result = extract_session(session_path, plan_path, ffmpeg)
            self.assertEqual(result["status"], "complete")
            self.assertEqual([c["frames"] for c in result["cameras"]], [4, 4, 4])
            for camera in value["cameras"]:
                files = sorted((root / "frames" / camera["id"]).glob("*.png"))
                self.assertEqual(len(files), 4)
                self.assertTrue(all(png_size(path) == (160, 96) for path in files))
                # Independently decode one selected source index and compare
                # bytes: correct counts alone would miss a wrong-frame bug.
                index = plan["bundles"][2]["views"][camera["id"]]["source_index"]
                check = root / (camera["id"] + "_verification.png")
                subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-n", "-noautorotate",
                                "-i", str(root / camera["video"]), "-vf", f"select=eq(n\\,{index})",
                                "-frames:v", "1", "-pix_fmt", "rgb24", "-update", "1", str(check)], check=True)
                self.assertEqual(hashlib.sha256(files[2].read_bytes()).digest(),
                                 hashlib.sha256(check.read_bytes()).digest())
            with self.assertRaises(ValueError):
                extract_session(session_path, plan_path, ffmpeg)


if __name__ == "__main__":
    unittest.main()
