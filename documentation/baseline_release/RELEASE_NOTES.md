# Yogurt and textile Gaussian reconstruction baseline

This checkpoint preserves the working static COLMAP/LichtFeld workflow and the
current dynamic reconstruction demonstrations. The source includes the native
Windows fitting/rendering tools, chronological screenshots of successes and
failed attempts, realistic RGB and analysis-map orbit videos, and validation.

- **Textile:** 214 compressed RGB Gaussian states and a separate current-session
  static table. Restore the numbered 1,277-frame SuperSplat timeline using
  `scripts/Restore-TextileTimeline.py`. Playback lasts 42.567 seconds; the 30 fps
  presentation holds approximately five newly reconstructed states per second.
  This is not yet a continuous deformation model or material-strain measurement.
- **Yogurt:** full-precision static surroundings and one persistent rigid actor,
  with 53 supported poses, calibration and playback metadata. Open using
  `scripts/Serve-RigidGaussianPreview.py` in the documented CUDA environment.
  RGB is time-constant and unsupported motion gaps remain unsupported.

Extract assets into a fresh checkout root. Both packages exclude source footage,
training checkpoints and rejected trials. See `docs/BASELINE_RELEASE.md` for
checksums, restore instructions and limitations. Hidden geometry and physical
accuracy are unverified. A shared textile deformation backend remains next work.
