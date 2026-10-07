import copy
from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tf4dgs.analysis import analyse, synthetic_tracks, validate_tracks
from tf4dgs.io import relative_path, write_json
from tf4dgs.preview import Handler
from tf4dgs.session import initialize, load, preflight, template, validate_calibration
from tf4dgs.sync import aligned_frames, fit_clock, make_plan


def probe(times):
    return {"frames": [{"index": i, "camera_time_s": t, "media_pts_s": t + 12}
                       for i, t in enumerate(times)]}


def session(end=3, fps=1, tolerance=0.035):
    value = template("test")
    value["cameras"] = value["cameras"][:2]
    value["timeline"].update(end_s=end, sample_fps=fps, max_skew_s=tolerance)
    value["baseline"]["end_s"] = min(0.5, end)
    for camera in value["cameras"]:
        camera["sync_points"] = [{"camera_time_s": 0, "session_time_s": 0}]
    return value


def tracks():
    return {"schema_version": 1, "color_space": "linear_rgb", "identity_kind": "assigned_points",
            "reference_frame": 0, "metres_per_unit": None,
            "frames": [{"time_s": t, "points": [{"id": "p", "position": [x, 0, 0], "rgb": [0, 0, 0]}]}
                       for t, x in ((0, 0), (1, 1), (2, 0))]}


class SynchronizationTests(unittest.TestCase):
    def test_offset_and_clock_drift(self):
        one = fit_clock([{"camera_time_s": 2, "session_time_s": 0}])
        self.assertEqual(one["offset_s"], -2)
        self.assertFalse(one["drift_estimated"])
        two = fit_clock([{"camera_time_s": 1, "session_time_s": 0},
                         {"camera_time_s": 11, "session_time_s": 10.01}])
        self.assertAlmostEqual(two["scale"], 1.001)
        self.assertAlmostEqual(two["offset_s"], -1.001)
        self.assertAlmostEqual(two["drift_ppm"], 1000)

    def test_invalid_cues(self):
        for values in ((1, 1), (1, 0)):
            cues = [{"camera_time_s": values[i], "session_time_s": i} for i in range(2)]
            with self.assertRaises(ValueError):
                fit_clock(cues)

    def test_variable_intervals_use_actual_pts(self):
        data = {"dji": probe([0, .2, .45, .7, .9]), "fuji": probe([.01, .23, .47, .72, .92])}
        result = make_plan(session(1, 2, .06), data)
        self.assertEqual(len(result["bundles"]), 2)
        second = result["bundles"][1]
        self.assertAlmostEqual(second["time_s"], .45)
        self.assertEqual(second["views"]["dji"]["source_index"], 2)
        self.assertAlmostEqual(second["views"]["fuji"]["delta_to_reference_s"], .02)
        self.assertFalse(result["sensor_sync_accuracy_verified"])

    def test_excessive_cross_camera_skew_is_rejected(self):
        result = make_plan(session(), {"dji": probe([0, 1, 2]), "fuji": probe([.1, 1.1, 2.1])})
        self.assertEqual(result["bundles"], [])
        self.assertEqual(len(result["rejected_samples"]), 3)

    def test_oversampling_never_duplicates_frames(self):
        result = make_plan(session(3, 4, .6), {"dji": probe([0, 1, 2]), "fuji": probe([0, 1, 2])})
        self.assertEqual([b["views"]["dji"]["source_index"] for b in result["bundles"]], [0, 1, 2])
        self.assertTrue(any(r["reason"] == "would reuse a source frame" for r in result["rejected_samples"]))

    def test_sampling_rounding_is_separate_from_camera_skew(self):
        times = [i * 1001 / 30000 for i in range(467)]
        value = session(15.55, 10, .001)
        value["timeline"]["max_sample_offset_s"] = .017
        result = make_plan(value, {"dji": probe(times), "fuji": probe(times)})
        self.assertEqual(len(result["bundles"]), 156)
        self.assertEqual(result["rejected_samples"], [])
        self.assertGreater(max(abs(b["time_s"]-b["requested_time_s"]) for b in result["bundles"]), .001)
        self.assertTrue(all(b["views"]["fuji"]["delta_to_reference_s"] == 0 for b in result["bundles"]))

    def test_sampling_tolerance_does_not_relax_camera_pairing(self):
        value = session(1, 10, .001)
        value["timeline"]["max_sample_offset_s"] = .017
        times = [i * 1001 / 30000 for i in range(30)]
        result = make_plan(value, {"dji": probe(times), "fuji": probe([t+.003 for t in times])})
        self.assertEqual(result["bundles"], [])
        self.assertTrue(all(r["reason"] == "cross-camera skew" for r in result["rejected_samples"]))

    def test_nonmonotonic_and_nonfinite_pts(self):
        for times in ([0, 0], [0, -1], [0, float("nan")]):
            with self.assertRaises(ValueError):
                aligned_frames(probe(times), {"scale": 1, "offset_s": 0})

    def test_camera_start_offset(self):
        value = session()
        value["cameras"][1]["sync_points"][0]["camera_time_s"] = 1
        result = make_plan(value, {"dji": probe([0, 1, 2]), "fuji": probe([0, 1, 2, 3])})
        self.assertEqual([b["views"]["fuji"]["source_index"] for b in result["bundles"]], [1, 2, 3])


class AnalysisTests(unittest.TestCase):
    def test_out_and_return_retains_recent_motion(self):
        value = validate_tracks(tracks())
        self.assertEqual(analyse(value, 2)["points"][0]["geometry"], 0)
        recent = analyse(value, 2, "recent", 5)["points"][0]
        self.assertAlmostEqual(recent["geometry"], 1.8)
        self.assertEqual(len(recent["trail"]), 2)

    def test_old_color_change_remains_in_reference_view(self):
        value = tracks()
        for frame in value["frames"][1:]:
            frame["points"][0]["rgb"] = [1, 0, 0]
        value["frames"].append({"time_s": 8, "points": copy.deepcopy(value["frames"][-1]["points"])})
        self.assertEqual(analyse(value, 3)["points"][0]["appearance"], 1)
        self.assertIsNone(analyse(value, 3, "recent", 5)["points"][0]["appearance"])

    def test_missing_observation_does_not_create_a_trail(self):
        value = tracks()
        value["frames"][1]["points"] = []
        recent = analyse(value, 2, "recent")["points"][0]
        self.assertIsNone(recent["geometry"])
        self.assertEqual(recent["trail"], [])

    def test_new_surface_has_no_original_reference(self):
        value = tracks()
        value["frames"][2]["points"][0]["id"] = "new_surface"
        point = analyse(value, 2)["points"][0]
        self.assertIsNone(point["geometry"])
        self.assertEqual(point["reason"], "no stable reference correspondence")

    def test_appearance_and_geometry_are_independent(self):
        value = tracks()
        value["frames"][1]["points"][0].update(position=[0, 0, 0], rgb=[1, 0, 0])
        point = analyse(value, 1)["points"][0]
        self.assertEqual(point["geometry"], 0)
        self.assertEqual(point["appearance"], 1)

    def test_metric_scale_is_explicit(self):
        value = tracks()
        value["metres_per_unit"] = .1
        result = analyse(value, 1)
        self.assertEqual(result["geometry_units"], "m")
        self.assertAlmostEqual(result["points"][0]["geometry"], .1)

    def test_duplicate_ids_and_undeclared_color_space(self):
        value = tracks()
        value["frames"][0]["points"] *= 2
        with self.assertRaises(ValueError):
            validate_tracks(value)
        value = tracks()
        value["color_space"] = "camera_log"
        with self.assertRaises(ValueError):
            validate_tracks(value)

    def test_reference_cannot_leak_into_earlier_frame(self):
        value = tracks()
        value["reference_frame"] = 1
        point = analyse(value, 0)["points"][0]
        self.assertIsNone(point["geometry"])
        self.assertEqual(point["trail"], [])

    def test_invalid_history_and_frame_index(self):
        for history in (0, -1, float("nan"), True):
            with self.assertRaises(ValueError):
                analyse(tracks(), 1, "recent", history)
        for frame in (True, 1.5, -1, 3):
            with self.assertRaises(ValueError):
                analyse(tracks(), frame)


class SessionTests(unittest.TestCase):
    def test_pending_session_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capture"
            initialize(path, "capture")
            report = preflight(path / "session.json")
            self.assertEqual(len(report["missing_videos"]), 3)
            self.assertFalse(report["ready_for_training"])
            self.assertFalse(report["ready_to_probe"])
            with self.assertRaises(ValueError):
                initialize(path, "capture")

    def test_paths_are_portable_and_contained(self):
        for path in ("../escape.mp4", "C:/movie.mp4", "https://example.com/movie", "raw\\camera.mp4"):
            with self.assertRaises(ValueError):
                relative_path(Path.cwd(), path)

    def test_calibration_requires_a_proper_rotation(self):
        value = {"schema_version": 1, "camera_id": "dji", "image_size": [3840, 2160],
                 "model": "PINHOLE", "params": [2000, 2000, 1920, 1080],
                 "world_to_camera": {"R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "t": [0, 0, 0]}}
        validate_calibration(value, "dji")
        value["world_to_camera"]["R"][2][2] = -1
        with self.assertRaises(ValueError):
            validate_calibration(value, "dji")

    def test_invalid_baseline_and_moving_camera(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session.json"
            for change in ("baseline", "pose"):
                value = session()
                if change == "baseline":
                    value["baseline"]["end_s"] = 50
                else:
                    value["cameras"][0]["fixed_pose"] = False
                write_json(path, value, overwrite=True)
                with self.assertRaises(ValueError):
                    load(path)

    def test_malformed_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "session.json"
            for value in ([], {**session(), "cameras": [None, None]}, {**session(), "timeline": []}):
                write_json(path, value, overwrite=True)
                with self.assertRaises(ValueError):
                    load(path)


class PreviewTests(unittest.TestCase):
    def test_read_only_preview_serves_analysis_and_handles_bad_input(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, tracks=validate_tracks(synthetic_tracks())))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(url + "/api/health", timeout=5) as response:
                self.assertTrue(json.load(response)["synthetic"])
            with urlopen(url + "/api/analysis?frame=16&mode=recent&history=5", timeout=5) as response:
                points = {p["id"]: p for p in json.load(response)["points"]}
                self.assertGreater(points["out_and_return"]["geometry"], 0)
            with urlopen(url, timeout=5) as response:
                self.assertIn(b"Synthetic", response.read())
            for endpoint in ("/api/analysis?frame=-1", "/api/analysis?history=nan", "/api/analysis?mode=invalid"):
                with self.assertRaises(HTTPError) as result:
                    urlopen(url + endpoint, timeout=5)
                self.assertEqual(result.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
