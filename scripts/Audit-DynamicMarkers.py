"""Audit visible board geometry, camera stability and coarse motion in real video.

Board homographies are image diagnostics, not full camera calibration. Blue-lid
coordinates are perspective projections onto the board plane, not physical 3D
container positions. Intrinsics, physical print scale and sensor timing must
be verified separately before metric reconstruction.
"""
import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def scalar_stats(values):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    return None if not len(values) else {"min": float(values.min()), "median": float(np.median(values)),
                                        "p95": float(np.quantile(values, .95)), "max": float(values.max())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--stride", type=int, default=6, help="Sample every N decoded frames")
    args = parser.parse_args()
    cv2.setNumThreads(2)
    session = json.loads(args.session.read_text(encoding="utf-8-sig"))
    root = args.session.parent
    output = root/"calibration"/"marker_audit"
    if output.exists():
        raise ValueError("Marker audit already exists; preserve it before a new audit")
    output.mkdir(parents=True)
    definition_path = Path("documentation/reference_markers/TF4DGS_ChArUco_US_Tabloid_10x6_35mm.json")
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    object_corners = {m["id"]: np.array(m["corners_m"], dtype=np.float64)[:, :2] for m in definition["layout"]["markers"]}
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_100)
    parameters = cv2.aruco.DetectorParameters()
    parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    summaries = []
    for camera in session["cameras"]:
        cid = camera["id"]
        probe = json.loads((root/f"manifests/{cid}.frames.json").read_text(encoding="utf-8"))
        capture = cv2.VideoCapture(str(root/camera["video"]))
        if not capture.isOpened():
            raise ValueError("Video decode failed")
        width, height = probe["stream"]["width"], probe["stream"]["height"]
        scale = min(1., 1600/max(width, height))
        sample_size = (round(width*scale), round(height*scale))
        sx, sy = sample_size[0]/width, sample_size[1]/height
        records, reference_h, previous_gray, native_reference = [], None, None, None
        checkpoints = np.array([[0,0],[.35,0],[.35,.21],[0,.21],[.175,.105]],dtype=float).reshape(-1,1,2)
        for index, stamp in enumerate(probe["frames"]):
            ok, image = capture.read()
            if not ok:
                raise ValueError(f"{cid}: decode ended at {index} before probed frame count")
            if index % args.stride:
                continue
            sample = cv2.resize(image, sample_size, interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = detector.detectMarkers(gray)
            known = [] if ids is None else [(int(marker), corner.reshape(4,2)/[sx,sy]) for marker,corner in zip(ids.reshape(-1),corners) if int(marker) in object_corners]
            if known:
                points = np.vstack([item[1] for item in known]).astype(np.float32).reshape(-1,1,2)
                native_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                cv2.cornerSubPix(native_gray, points, (5,5), (-1,-1), (cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_MAX_ITER,30,.01))
                pixels = points.reshape(-1,2).astype(float)
                world = np.vstack([object_corners[item[0]] for item in known])
            else:
                pixels, world = None, None
            h, residual, drift = None, None, None
            if len(known) >= 4:
                h, inliers = cv2.findHomography(world,pixels,cv2.RANSAC,2.)
                if h is not None:
                    projected = cv2.perspectiveTransform(world.reshape(-1,1,2),h).reshape(-1,2)
                    residual = float(np.sqrt(np.mean(np.sum((projected-pixels)**2,axis=1))))
                    projected_checks = cv2.perspectiveTransform(checkpoints,h).reshape(-1,2)
                    if reference_h is None:
                        reference_h = h.copy()
                        native_reference = {"decoded_index":index, "homography_board_m_to_native_px":h.tolist(),
                                            "markers":[{"id":item[0],"pixels":pixels[i*4:(i+1)*4].tolist()} for i,item in enumerate(known)]}
                    reference_checks = cv2.perspectiveTransform(checkpoints,reference_h).reshape(-1,2)
                    drift = float(np.median(np.linalg.norm(projected_checks-reference_checks,axis=1)))
            blue_center, plane_xy, area = None, None, None
            if "yogurt" in session["session_id"] and reference_h is not None:
                hsv = cv2.cvtColor(sample,cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv,np.array([85,65,45]),np.array([135,255,255]))
                plane = np.array([[[-.15,-.15],[.5,-.15],[.5,.36],[-.15,.36]]],dtype=float)
                polygon = cv2.perspectiveTransform(plane,reference_h)[0]*[sx,sy]
                roi = np.zeros_like(mask)
                cv2.fillPoly(roi,[np.round(polygon).astype(np.int32)],255)
                mask &= roi
                mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((17,17),np.uint8))
                contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    contour = max(contours,key=cv2.contourArea)
                    area = cv2.contourArea(contour)
                    if area > 80:
                        moments=cv2.moments(contour)
                        blue_center=np.array([moments['m10']/moments['m00']/sx,moments['m01']/moments['m00']/sy])
                        plane_xy=cv2.perspectiveTransform(blue_center.reshape(1,1,2),np.linalg.inv(reference_h))[0,0].tolist()
            record={"index":index,"time_s":stamp['camera_time_s'],"marker_count":len(known),
                    "marker_ids":[x[0] for x in known],"homography_rms_px":residual,"board_drift_px":drift,
                    "mean_luma":float(gray.mean()),"dark_fraction":float(np.mean(gray<12)),
                    "bright_fraction":float(np.mean(gray>245)),"laplacian_variance":float(cv2.Laplacian(gray,cv2.CV_32F).var()),
                    "mean_frame_difference":None if previous_gray is None else float(cv2.absdiff(previous_gray,gray).mean()),
                    "blue_lid_center_px":None if blue_center is None else blue_center.tolist(),
                    "blue_lid_projected_board_xy_m":plane_xy,"blue_area_preview_px":area}
            records.append(record)
            previous_gray=gray
            if len(records)%30==0:
                print(f"{session['session_id']} {cid}: {index}/{len(probe['frames'])} frames; {len(known)} markers",flush=True)
        capture.release()
        result={"camera_id":cid,"image_size":[width,height],"stride":args.stride,"samples":records,
                "reference":native_reference,"full_calibration_solved":False,
                "nominal_board_dimensions_only":True,"lid_plane_projection_is_not_3d_position":True}
        (output/f"{cid}.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        with (output/f"{cid}.csv").open('w',newline='',encoding='utf-8') as stream:
            keys=['index','time_s','marker_count','homography_rms_px','board_drift_px','mean_luma','dark_fraction','bright_fraction','laplacian_variance','mean_frame_difference']
            writer=csv.DictWriter(stream,keys,extrasaction='ignore');writer.writeheader();writer.writerows(records)
        summary={"camera_id":cid,"samples":len(records),"marker_counts":scalar_stats([x['marker_count'] for x in records]),
                 "homography_rms_px":scalar_stats([x['homography_rms_px'] or np.nan for x in records]),
                 "board_drift_px":scalar_stats([np.nan if x['board_drift_px'] is None else x['board_drift_px'] for x in records]),
                 "blue_track_samples":sum(x['blue_lid_center_px'] is not None for x in records)}
        summaries.append(summary)
        print(json.dumps(summary),flush=True)
    result={"session_id":session['session_id'],"board_definition":definition_path.name,
            "physical_print_verified":False,"full_calibration_solved":False,"summaries":summaries}
    (output/'summary.json').write_text(json.dumps(result,indent=2)+"\n",encoding='utf-8')


if __name__=='__main__':
    main()
