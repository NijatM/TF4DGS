# First real TF4DGS recordings: chronological processing record

Started 2026-10-07. Two fixed-camera tests share a user-measured 35 mm ChArUco
board: a translated yogurt container and a manipulated knitted textile.
Original recordings remain on D:. Verified copies, extracted frames, complete
logs and calibration experiments remain under ignored `data/` and `.local/`.

**Status: native extraction and provisional shared-camera calibration completed;
real rigid yogurt Gaussian pilots and current-capture Gaussian surroundings
trained, exported and visually verified together. Textile stereo tracking
is partial; full non-rigid reconstruction is not completed.** Original uncropped files and independent calibration captures
are unavailable. Physical accuracy remains unverified despite measured scale.

The local browser report is [index.html](index.html). Numbered screenshots
show actual browser views of the processing evidence. Early stages completed
before screenshots were requested: their screenshots are retrospective views
of preserved results/errors, not original live terminal captures. Recording
contact sheets and marker overlays are labeled diagnostic images. Stages that
ran concurrently are recorded in their start order.

| Stage | Outcome | Evidence / next action |
| --- | --- | --- |
| 01 Copy recordings | Passed | Six copies verified with SHA-256. Separate `data/dynamic_yogurt_001/raw` and matching textile folder, each organized by camera. |
| 02 Inspect yogurt | Passed | 467 frames, 15.582 s, 29.97 FPS; empty board, container placement, pause and translation. |
| 03 Inspect textile | Passed | 1,277 frames, 42.609 s, 29.97 FPS; initial textile, in-plane manipulation, lifts/folds and return. |
| 04 First-frame markers | Passed | Yogurt: all 30 IDs in every native view. Textile: 13/13/14 IDs; material hides the others. |
| 05 Decoded timestamps | Passed | Actual PTS/fingerprints recorded for all six videos. Matching exported timestamps are distinct from sensor synchronization. |
| 06 Visibility/stability audit | Completed | 78 samples/camera for yogurt, 213 for textile. Sparse visible markers during textile manipulation make homography extrapolation unreliable. |
| 07 Dynamic environment attempt 1 | Failed | Conda scanned unaccepted Anaconda default-channel terms despite environment recipe. No terms accepted; used explicit conda-forge channels instead. |
| 08 Isolated environment retry | Passed | Python 3.10.22, torch 2.4.0+cu124, official gsplat 1.5.3+pt24cu124 Windows wheel. Main CPU/static setup preserved. |
| 09 Calibration preparation | Completed | Native matched frame 360 from three cameras. Centered focal estimates consistent for Fuji/iPhone; inconsistent for cropped DJI. Initial values are not solved calibration. |
| 10 Calibration command attempt 1 | Failed | PowerShell round-trip formatting on integer parameters caused invalid camera arguments. Corrected by casting numbers to double; retained error logs. |
| 11 GPU render/backward | Passed | Real one-Gaussian CUDA rasterization and position/color gradients; 0.612 s on RTX A4000. Package consistency check passed. |
| 12 Automatic COLMAP initialization | Failed | Three verified pairs (195/163/81 matches), all classified planar. Repeated unsuitable initial pair; no sparse model created. Reused feature DB for board-based attempts. |
| 13 First extraction pilot | Rejected as undersampled | 1 ms limit also restricted sampling rounding: only 11 yogurt / 31 textile bundles. Valid sparse images retained as `frames_sampling_attempt_01`. |
| 14 Timing correction | Passed | Separate sampling offset 17 ms from cross-camera skew 1 ms; 156/426 bundles, zero rejections. 25 tests passed. |
| 15 Full-size selection attempt | Failed | Long left-associated FFmpeg selection expression exceeded parser depth; reported Cannot allocate memory before output. This was a filter-parser failure, not GPU OOM. |
| 16 Extraction scalability correction | Passed | Balanced expression tree; 26 tests pass, including real 200-frame sparse selection and independently decoded first/middle/last frame hashes. |
| 17 Board bootstrap attempt 1 | Failed | Only 3 accepted triangulated matches and 0 off-plane triple matches under provisional uncropped-view assumptions. Cropped-DJI solve refused insufficient support. |
| 18 Visual-report encoding attempt | Failed then corrected | Windows PowerShell redirected the Conda JSON as UTF-16; initial UTF-8 reader failed. Added BOM-aware decoding for retained logs. |
| 19 Corrected native extraction | Passed | 156 yogurt and 426 textile bundles, three native PNGs each (468/1278 images); no rejected samples, no resize or relighting. |
| 20 Marker-aware match diagnostic | Completed | COLMAP's verified Fuji/iPhone matches disagreed with known board mapping by hundreds of pixels. Repeated-pattern aliases rejected. First read-only SQLite diagnostic required a sandbox-safe retry. |
| 21 Rectified lid matching | Completed | Real lid texture matched after provisional plane rectification: 22-30 Fuji/iPhone and 20-45 Fuji/DJI homography inliers across tested heights. Initial native reprojection residual around 12 pixels failed the strict 3-pixel gate. |
| 22 Joint board/lid refinement | Provisional success | Fitted all three square-pixel pinhole cameras, 46 material tracks and a flat lid plane; 7 tracks seen in all three views. Held-out board RMS 1.67/1.15/1.14 px (Fuji/iPhone/DJI). Held-out lid predictions 7.45/3.85 px (iPhone/DJI). Estimated lid height 56.7 mm; not independently verified. |
| 23 Shared-calibration transfer | Failed for DJI | Unchanged physical rig did not mean unchanged exported framing. Textile DJI board error was 90.34 px; Fuji 2.65 px and iPhone 0.98 px. Original transfer retained. |
| 24 Export-crop correction | Provisional success | Principal-point-only corrections preserve physical poses. DJI shift +90.13/-4.77 px reduces board RMS to 1.00 px; Fuji/iPhone corrected RMS 1.51/0.92 px. Textile uses separate corrected calibration files. |
| 25 Rigid material tracking | Partial success | Native-image optical flow of 46 observed lid features, with forward/backward checks and no bridging of failures. 46/156 frames support multi-view poses, 9.3093-14.014 s, median fit residual 2.89 px. Earlier/later unsupported frames are retained as missing, not invented. |
| 26 Screenshot manifest correction | Failed then corrected | PowerShell wrapped the previous JSON array as one entry when adding stages. Flattened the manifest and corrected the reader; original screenshot files and capture timestamps preserved, sorted by stage number. |
| 27 Gaussian pilot preparation attempt 1 | Failed | Native crop/mask preparation completed, but NumPy int32 crop dimensions could not be serialized to JSON. Converted dimensions to ordinary integers. Failed output folder and traceback retained as gaussian_pilot_01. |
| 28 First moving Gaussian training | Trained, quality limited | gaussian_pilot_02: 15,077 persistent Gaussians, 3,000 steps, best step 2,000, 117 training/21 held-out-time views. Full held-out foreground PSNR 20.83 dB from 16.05 dB initial. Label text remains blurred and edge streaks visible; not accepted as a finished crisp model. |
| 29 Evaluation scope correction | Failed then corrected | Run-02 summary accidentally reported the three screenshot views (19.90 dB) instead of all 21 held-out views (20.83 dB in history). Corrected evaluation to keep the full split when saving panels; the original summary/log remain preserved. |
| 30 Denser constrained yogurt pilot | Trained, quality limited | gaussian_pilot_03: 51,469 persistent Gaussians, fixed surface orientations, bounded scales, 10,000 steps; held-out foreground PSNR 21.37 dB from 15.74 dB initialization. Native crop pixels retained. Edges/text still imperfect; metric accuracy and unseen geometry unverified. |
| 31 Textile stereo initialization attempt 1 | Failed | Raw-perspective SIFT yielded 7 Fuji/DJI and 20 Fuji/iPhone accepted pairs, but 0 consistent triple-view points. Tracking refused insufficient support. Native masks, initialization and traceback retained; mask also included some board content. Retry uses plane rectification and visible-marker exclusion. |
| 32 Rectified textile initialization attempt 2 | Failed after matching | Rectification produced observed material correspondences, including two-view points. Saving the native observations failed because NumPy arrays were not JSON serializable. Converted only the observation arrays to lists; preserved the failed folder, rectifications and diagnostic. |
| 33 Rectified textile material tracks | Partial success | 39 two-view material candidates initialized; 18/426 frames retain at least 12 triangulated tracks, 0-1.7017 s. Occlusion and knit ambiguity prevent dense deformation during later manipulation. This is observed point analysis, not a completed non-rigid Gaussian model. |
| 34 Native-rate textile tracking retry | No substantial improvement | Used consecutive original 29.97 Hz frames until tracks were lost, then sampled the native 10 Hz plan. Same 18 well-supported bundles; some isolated features survive longer, but do not support a dense field. Native PNG training frames preserved. |
| 35 Live-preview screenshot attempt 1 | Failed then corrected | Capture readiness used image.complete, which is also true before an image source is loaded. Browser image decoding raised EncodingError. Readiness now waits for actual rendered image pixels (naturalWidth > 0). |
| 36 Live rigid Gaussian viewer | Passed | Actual CUDA-rendered yogurt model in a browser with time selection, orbit and zoom. RGB capture uses run 03; later cleaner preview uses run 04. This is a Gaussian renderer, separate from the selected-point viewer. |
| 37 Tighter final quality comparison | Trained, cleaner edges | gaussian_pilot_04: 51,469 Gaussians, 30,000 steps, 1.5 mm bounded position offsets, 0.9 mm maximum scale. Held-out foreground PSNR 20.82 dB; lower than run 03's 21.37 dB, but visibly fewer loose edge splats. Retain both; select run 04 for the cleaner preview. |
| 38 Gaussian displacement and trails | Passed | All persistent Gaussian centers receive reference displacement or fading motion activity; 35 representative IDs show trails. Uses observed valid poses and true sample times; gaps are not interpolated. Rigid displacement is not material strain. |
| 39 Independent native-pixel verification | Passed | Independently decoded one middle frame per original copied stream: all six match the extracted PNG RGB bytes exactly. Fuji/iPhone stay 3840 x 2160; DJI 1536 x 2304. All extraction counts/dimensions separately checked. |
| 40 Selected-feature preview capture | Captured, timing correction needed | Both geometry and observed appearance maps displayed for real yogurt features. Initial screenshot requested frame 130 before the data set the slider maximum, so it captured frame 100 instead. Screenshot preserves its actual 10.01 s label; readiness corrected to wait for loaded tracks/state. |
| 41 Selected-feature preview correction | Passed | Capture waits for loaded tracks, selects frame 130 (13.013 s) and a 3-second activity window. Actual frame/time stored in screenshot metadata. No Gaussian temporal color or pigment change is claimed from this selected-feature video appearance. |
| 42 Cleaner Gaussian preview | Passed | Run 04 loaded in the real Gaussian viewer. RGB and scalar fields remain available with the same persistent IDs. Recent activity is gray when no contiguous history exists; unsupported poses return an error rather than an invented time sample. |
| 43 Processing/checkpoint verification | Passed | Native-pixel checks, Gaussian parameter/export checks, live RGB/displacement/activity rendering and missing-history/unsupported-frame checks passed. CPU foundation: 26 tests pass. Static source pins preserved; footage/models remain ignored. |
| 44 Yogurt visibility-mask retry | Failed to improve coverage | Filled-rim masking increased DJI observations from 247 to 2,438 but selected a disconnected blue component in iPhone views, dropping other valid blue features. Only 34 valid poses, 11.011-14.5145 s; original 46-frame result retained. |
| 45 Visibility union correction | Failed to improve reliable poses | Union mask retains original blue pixels and expands DJI observations to 2,683; iPhone retains 4,131. Only 28 frames pass the unchanged full-observation pose thresholds, median residual 4.92 px. Additional observations include inconsistent tracks; keep the original stronger 46-frame result. |
| 46 Report-tab recovery | Failed then corrected | The dedicated report tab was no longer present during capture. Screenshot helper now reopens only the local 8097 report in the existing dedicated browser. No user browser windows were closed. |
| 47 Explicit motion-inlier refinement | Partial, not selected | Single-view planar hypotheses initialize a joint fit; accepted poses retain at least four features in each of two cameras and twelve total after 8 px rejection. 40 supported frames, 10.6106-15.2152 s, median inlier residual 2.94 px. Later reach improved, total coverage did not; original 46-frame trajectory remains selected. Raw and retained counts preserved; gaps remain missing. |
| 48 Measured container dimensions | Recorded | User measured table-to-lid height 58 mm and outer lid diameter 95 mm. Measurement uncertainty was not supplied. Earlier estimates were 56.7 mm high and 95.5 mm across. Portable measurement record saved; earlier calibration and models retained. |
| 49 Measured-height camera refinement | Converged, provisional | Joint fit fixes lid height at 58 mm. The 95 mm diameter is excluded from camera fitting and checked against blue-rim contours: Fuji 96.64 mm, iPhone 96.98 mm, DJI 94.70 mm. Held-out lid prediction RMS iPhone/DJI 6.80/3.96 px; held-out board RMS Fuji/iPhone/DJI 1.79/1.17/1.37 px. Measurement improves the constraint; residuals do not establish millimetre accuracy. |
| 50 Measured calibration crop-transfer check | Passed, candidate only | Reused physical camera poses and fitted export principal-point translations for the textile clips. Candidate cameras saved separately; existing textile calibration and tracking remain unchanged pending review. |
| 51 Documentation capture timeout | Failed, recovery attempted | Browser screenshot capture timed out before saving the new report stages. The helper now brings its report tab to the foreground before waiting for animation frames and checkpoints the manifest after every screenshot. This failed capture is retained in the chronology; calibration and motion processing were unaffected. |
| 52 Measured unconstrained motion comparison | Partial; implausible fit rejected | Original blue-feature observations give 45 supported frames, median retained error 2.11 px, but one fitted lid orientation flips about 126 degrees. The expanded observed set gives 53 frames, 7.2072-15.5155 s, median 2.84 px and at most 7.87 degrees tilt. Low pixel residual alone is insufficient for accepting physical motion. Neither result silently replaces the original preview. |
| 53 Upright tabletop constraint trial | Failed to improve coverage | Fixing motion to yaw and XY sliding removes tilt/lift ambiguity but only 43/156 frames pass the same pixel thresholds, 9.4094-15.015 s, median inlier error 3.21 px. This assumption does not resolve the remaining calibration/tracking inconsistencies. Retain the trial; use the non-flipped measured 53-frame fit for a separate appearance-model comparison, with its physical limits explicit. |
| 54 Measured-dimension Gaussian pilot | Trained, comparison retained | Run 05: 51,913 persistent Gaussians, 30,000 steps, initialized at measured height 58 mm and lid radius 47.5 mm. 53 supported poses, 135 training and 24 held-out native crops; foreground PSNR 20.82 dB. This split differs from run 04, so their rounded scores are not a controlled quality comparison. Earlier models remain intact. |
| 55 Opacity quality diagnosis | Quality issue identified | Real held-out renders show unwanted partial transparency and fine loose structure in the lid/body. Training's low silhouette weight allows alpha to compensate for mismatched appearance. A separate trial raises silhouette weight from 0.035 to 0.2 and reduces bounded position offsets from 1.5 mm to 0.65 mm; compare on identical crops/masks and pose samples before selection. |
| 56 Stronger opacity trial | Trained, cleaner opaque surface | Measured run 06: 51,913 Gaussians, 30,000 steps, 0.65 mm position bounds, 0.9 mm maximum scale and silhouette weight 0.2. Uses the same 53 poses and native view split as measured run 05. Full RGB/detail and hidden geometry remain imperfect; do not label the result pristine or metrically certified. |
| 57 Shared-crop quality comparison | Passed; run 06 selected | Identical 24 held-out crops and masks: alpha MAE improves 0.06395 to 0.04421 (about 31% lower), mean foreground alpha increases 0.9435 to 0.9654. Foreground RGB PSNR decreases 20.82 to 20.20 dB. Select the more solid measured run 06 for demonstration, retain run 05 and original run 04. This is a selection split, not an untouched test. |
| 58 Measured actor live RGB | Passed | Genuine visible browser screenshot at 12.012 s shows run 06 with 51,913 persistent IDs. Viewer reads its matching pose file from motion.json and rejects an explicit incompatible trajectory. Previous run 04 remains available on local port 8101. |
| 59 Measured actor activity and trails | Passed | Genuine browser screenshot at 13.013 s, 3-second fading window, all-Gaussian activity field and 35 representative trails. Reference is the first supported time, not an invented frame-zero pose; gaps remain unsupported. This field includes rigid motion, not material strain or calibrated pigment change. |
| 60 Measured checkpoint verification | Passed | Height/diameter initialization and canonical camera/pose provenance agree; Gaussian export, persistent IDs, six live renders, invalid/missing-history behavior, native pixel checks, 26 foundation tests and static pins pass. Raw footage/models/logs remain ignored. All chronological evidence is retained. |
| 61 Earlier-scene registration experiment | Failed; abandoned | Three current empty views produced no verified registrations to the earlier static model. No scenes were merged and old inputs were untouched. The user then explicitly excluded all earlier scenes from this workflow; the attempt and helper were moved into the ignored abandoned archive. It will not supply the current surroundings. |
| 62 Current-capture background source | Selected | Surroundings must be actual static Gaussians from the current recordings, in the measured marker coordinate system. The current empty frames show the tabletop, board, monitor stand, cables, divider, outlets and chairs. Three fixed views provide limited off-table stereo; unobserved surfaces remain unsupported. Finish and visually verify yogurt before resuming textile. |
| 63 Current-background depth tool | Installed and verified | Official Depth Anything V2 Small indoor checkpoint downloaded with its published SHA-256 checked. Matching torchvision 0.19.0+cu124 added to the isolated dynamic environment. Depth is an initialization prior for weakly observed surrounding geometry; the measured board supplies tabletop scale. Old static reconstruction and installations remain separate. |
| 64 Background empty-interval diagnosis | Failed visual check | First-eight-frame median retained a transient cue hand in the Fuji view and rejected many changing pixels. It is not an acceptable static background. Run 01 and its depth/mask diagnostic are preserved; no trained background selected. Retry uses the individually inspected clean frame zero in each current stream. |
| 65 Clean current-background initialization | Provisional success | Run 02 uses the clean first frame in each current stream. 370,081 static Gaussians, including 239,770 on the measured tabletop plane. No earlier scene or photographic backdrop is imported. Off-table depth remains a monocular prior, with limited three-camera support. |
| 66 Unconstrained background fitting | Failed to improve | 3,000 native-patch iterations worsened input-view fit; selection retained step zero. The export arrays correctly contain 370,081 points, but the first summary counter was also inconsistent and was corrected in the helper for later runs. This trial is preserved and rejected as the final background. |
| 67 Conservative background appearance fit | Improved slightly | Run 02/trained_02 fixes geometry and opacity and refines colors. Selected step 500 of 3,000; mean three-input-view MSE improves 0.007083 to 0.006946. These are training-camera scores, not independent validation. All 370,081 static points remain separate from the 51,913 moving actor IDs. |
| 68 Combined scene visual check | Rendered; cleanup needed | Genuine browser screenshot at 12.012 s shows current-capture surroundings and yogurt in one depth-ordered Gaussian rasterization. World-fixed iPhone view, room toggle, camera presets and actor-only fields work. Conflicting off-table depth priors cause ghosting at the monitor/stand; this preview is not accepted as the final cleanup. |
| 69 Conflicting depth-layer cleanup | Improved | Run 03 preserves the measured plane and removes unverified Fuji/DJI off-table seeds inside the wide iPhone view. Current native pixel stride reduced to four and initial opacity raised to 0.97. 498,531 static Gaussians remain, including 250,261 tabletop points. This reduces ghosting without importing another scene or claiming hidden-room accuracy. |
| 70 Cleaned background appearance fit | Selected | Conservative 3,000-step native-patch fit selects step 500. Wide iPhone input-fit PSNR 24.13 dB, Fuji 24.68 dB, DJI 17.36 dB. The widest view improves visually; reduced conflicting geometry sacrifices some side-view fit. These are training-view scores. Current static layer is run03/trained_01; actor run06 and all earlier trials remain separate. |
| 71 Whole-scene motion start | Visually checked | Genuine GUI capture at the first supported sample, 7.2072 s. Yogurt and current table/room are rendered as Gaussians in one world. Camera stays fixed, so movement is visible against the board and surroundings. No static desk or Necto scene is used. |
| 72 Whole-scene motion end | Visually checked | Genuine GUI capture at 15.5155 s confirms the container moves across the same fixed background. Hidden surfaces, lid/body detail and physical calibration remain provisional. Supported motion is accepted as a demonstration; missing samples are not filled. |
| 73 Whole-scene fading activity | Passed | Genuine GUI capture at 13.013 s shows all-actor activity and representative trails over unchanged static Gaussian surroundings. Static RGB is not remapped by actor displacement/activity colors. |
| 74 Scene-validation mask diagnosis | Failed then corrected | Initial automated field check inferred actor coverage from RGB differences. White actor pixels can equal white tabletop RGB while occupying geometry, so that mask incorrectly treated some actor pixels as static. Corrected verification to use calibrated projected Gaussian bounds; renderer geometry and images were unchanged. |
| 75 Current-scene motion verification | Passed | All 53 supported renders pass. Static-only first/last images are byte-identical under the fixed camera; measured plane z remains exactly zero, model/export counts and calibration provenance agree, actor movement is visible, static RGB stays outside actor fields, all camera presets render, and unsupported time/camera/mode requests are rejected. Yogurt visual/motion gate completed before resuming textile work. |
| 76 Textile measured retry launch | Failed then corrected | First launcher selected the CPU capture environment, where OpenCV is unavailable. No dataset/model output was created; traceback retained. Relaunched with existing tf4dgs-dynamic OpenCV installation. No package or static-tool changes were needed. |
| 77 Measured textile material tracking | Partial improvement | Separate measured crop-transfer session gives 45 observed two-view IDs (0 triple-view IDs). Native-rate LK tracking supports 28 samples, 0-2.9029 s, compared with the earlier 18 samples through 1.7017 s. Later hand occlusion/folding remains unsupported; this is not a completed non-rigid Gaussian replay. |
| 78 Textile RAFT coverage comparison | No improvement; retained | Official RAFT Large weights verified by SHA-256. Same 45 observed initial IDs, consecutive native-rate frames, 1280-pixel flow previews, forward/backward and unchanged stereo rejection checks. Supports 24 samples through 2.5025 s; measured LK run05 remains selected. LK used 1920-pixel flow, so this is not an equal-resolution benchmark. Missing tracks are not bridged or reidentified. The first documentation update hit an approval-review usage limit; evidence is now recorded. |

Manual capture information: user aligned a dropped-box impact in Premiere,
then trimmed/exported all views on one timeline. Fixed Fuji XF33 mm lens;
DJI Natural view additionally cropped. Exposure and white balance were manual.
Stabilization reported probably off, not independently verified. User confirmed
measured board and unchanged camera/board positions between tests. Retain
approximately one native-frame timing uncertainty (33.37 ms); equal export
frame counts do not prove simultaneous exposure or rule out duplicated frames.

The copied Fuji/iPhone streams are 3840 x 2160, DJI 1536 x 2304 portrait. All
are H.264 High, 8-bit SDR BT.709 at 30000/1001 FPS, about 80 Mb/s. MainConcept
export metadata matches the user-declared Premiere workflow. Training frames
preserve coded dimensions and orientation without exposure/color adjustment.

Scientific limits: a single flat-board pose does not independently determine
unrestricted camera intrinsics. Cropping can put the principal point outside
the coded image. Board-fit residual is not independent 3D accuracy. Hands and
folds occlude the textile; hidden fabric cannot be treated as observed. The
yogurt's lid-plane projections in the audit are 2D diagnostics, not measured
contact positions or material deformation. No image rows or independent PLY
indices are being declared persistent Gaussian identities.

Current review files (all models and full logs are local, ignored by Git):

- Current static Gaussian surroundings:
  `outputs/dynamic_yogurt_001/static_background_03/trained_01/`.
  498,531 Gaussians from the current recordings; 250,261 stay on the measured
  tabletop. Actor and surroundings share the measured world and a single
  depth-ordered rasterization. No earlier desk/Necto scene is used.
- Current measured, more solid rigid actor:
  `outputs/dynamic_yogurt_001/gaussian_pilot_06_measured_solid/`.
  `canonical_actor.ply` is a classic static 3DGS snapshot; `canonical_actor.npz`
  plus `motion.json`/the referenced rigid poses provide the time queries.
  The PLY alone does not store animation. All 51,913 IDs persist across the
  supported 53 time samples (7.2072-15.5155 s, with gaps). Initialization uses
  the user-measured 58 mm height and 95 mm lid diameter. The assumed hidden
  frustum surface is not measured; trained positions can move within 0.65 mm.
- Earlier cleaner actor: `outputs/dynamic_yogurt_001/gaussian_pilot_04/`,
  51,469 Gaussians and 46 supported poses. Retained for comparison on port 8101.
- Measured actor with lower opacity loss:
  `outputs/dynamic_yogurt_001/gaussian_pilot_05_measured/`. Shared-crop
  comparison against run 06 is in `outputs/dynamic_yogurt_001/measured_comparison_01/`.
- Higher numerical validation score, looser edges:
  `outputs/dynamic_yogurt_001/gaussian_pilot_03/`. Keep this comparison.
- Yogurt observed material features:
  `outputs/dynamic_yogurt_001/rigid_tracking_01/point_tracks.json`.
- Textile observed material features and coverage:
  `outputs/dynamic_textile_001/material_tracking_05_measured/`: 45 initial IDs,
  28 supported samples through 2.9029 s. Earlier run04 and RAFT run06 are kept.
  Later folding/lifting
  lacks enough validated material correspondence for dense deformation. No
  complete textile 4D Gaussian reconstruction is claimed.
- Full experiment logs: `.local/workflows/dynamic_setup/`; calibration attempts
  remain under each dataset's `calibration/`. Raw recordings were not modified.

Open the currently running [measured Gaussian viewer](http://127.0.0.1:8100/),
[earlier run 04 comparison](http://127.0.0.1:8101/),
[real selected-feature maps](http://127.0.0.1:8096/) or
[chronological report](http://127.0.0.1:8097/). Local previews require their
servers; `index.html` and numbered screenshots can also be viewed offline.

From this project folder, reopen the two analysis tools after closing them:

```powershell
conda run -n tf4dgs-dynamic python scripts/Serve-RigidGaussianPreview.py
# Use a second terminal for the selected-feature appearance/geometry viewer:
conda run -n tf4dgs python scripts/TF4DGS.py serve-preview --tracks outputs/dynamic_yogurt_001/rigid_tracking_01/point_tracks.json --port 8096
```

Validation PSNR uses the automatic foreground masks and 24 held-out **views at 8 times
from the same cameras**. That split was used to select checkpoints; it is not
an untouched independent test, novel-camera validation or metric certificate.
The current measured run trades 0.62 dB against measured run 05 for more solid
opacity on identical masks/crops. Earlier runs 03/04 used 21 views at 7 times;
their scores cannot establish improvement over the different measured split.
Gaussian training uses encoded video RGB and a time-constant appearance model.
Selected-feature appearance uses inverse BT.709 transfer and a fixed camera
per feature, with small tracking previews/patch medians. Neither is calibrated
pigment change. Unknown sensor timing, approximate camera intrinsics, shadows
and unseen surfaces limit the result more than adding training iterations.

Measurement provenance is in [container_measurements.json](container_measurements.json).
The original `data/dynamic_yogurt_001/session.json` stays unchanged for earlier
experiments. Current measured runs use `session_measured_candidate.json` and
`calibration/board_lid_refinement_02_measured/`; motion uses
`outputs/dynamic_yogurt_001/rigid_tracking_06_measured/rigid_poses.json`.
New textile run05 and RAFT run06 use `session_measured_candidate.json` with
`calibration/cameras_crop_adjusted_02_measured/`. Earlier run04 keeps its original
calibration and tracks. Do not mix the two
sets of canonical coordinates, cameras and transforms.

Next development: improve subject masks and material correspondence through
the textile's hand occlusion/folds before fitting a dense non-rigid model;
benchmark temporal Gaussian appearance separately. A future capture with
uncropped originals, multi-angle calibration and unique material features
would allow stronger geometric validation. The existing files remain useful
for testing the rigid renderer and analysis interface.

An initial documentation-directory write failed because the tool's workspace
root still names the old project folder. Creating the requested directory
through the approved actual workspace path resolved it without data changes.

No commits or pushes were performed. Raw data, training outputs, package
caches and full logs remain ignored; this report and numbered screenshots
are intended for the user's Git history.
