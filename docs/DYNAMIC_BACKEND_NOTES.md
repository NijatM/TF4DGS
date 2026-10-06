# Dynamic backend status and integration plan

Research inspected on 2026-10-05. No dynamic trainer has been installed,
forked, pinned or integrated. The working Windows static tools are preserved.

## Candidate evidence

The official [4DGaussians repository](https://github.com/hustvl/4DGaussians)
is a candidate for a shared deformation model. Its published setup uses
Python 3.7, PyTorch 1.13.1/CUDA 11.6 and custom CUDA extensions. That setup is
not validation for this machine's Windows/CUDA 13 toolchain. Its
[arguments](https://github.com/hustvl/4DGaussians/blob/master/arguments/__init__.py)
default `no_dshs=True`; the
[deformation implementation](https://github.com/hustvl/4DGaussians/blob/master/scene/deformation.py)
includes temporal spherical-harmonic features behind that option. Temporal
color therefore needs explicit configuration and testing. The
[renderer](https://github.com/hustvl/4DGaussians/blob/master/gaussian_renderer/__init__.py)
also needs an adapter audit: its Python SH-conversion path accesses canonical
features, whereas the direct rasterizer path accepts deformed SH features.

[Dynamic 3D Gaussians](https://dynamic3dgaussians.github.io/) emphasizes
persistent Gaussian tracking with fixed color, opacity and size while
position/orientation evolve. That is useful tracking research, but its stock
appearance model does not directly provide the requested changing-color
experiment. The official [code](https://github.com/JonathonLuiten/Dynamic3DGaussians)
is a separate research implementation, not a drop-in LichtFeld mode.

The practical inference is to benchmark temporal deformation **and** appearance
together before choosing a backend. We have not established that either stock
repository meets the full TF4DGS requirements or the two-hour training budget.

## Proposed interface

```text
Original fixed-camera videos + measured timing + common calibration
  -> synchronized views with camera IDs, true timestamps and validity
  -> static initialization + temporal geometry/appearance backend [pending]
  -> time query: Gaussian parameters, persistent IDs, validity/provenance
  -> realistic rendering + assigned-point analysis
  -> validated dense fields and trajectories [later]
```

Keep this adapter in TF4DGS initially, separate from the pinned static source
build. A future LichtFeld viewer/trainer extension may use the user's existing
fork, but only after a dynamic backend is validated. Independent static PLY
training per frame is not a substitute for stable temporal identities.

The adapter must carry common-world camera poses, coded image dimensions,
actual frame times, time normalization, masks/visibility and scale. It must
support both temporal positions and temporal appearance while exposing stable
IDs and unsupported regions. Splits, additions and disappearances need an
explicit correspondence policy; dense data will need streaming rather than
the small JSON point-preview format.

Cross-camera appearance correction should be estimated from the unchanged
baseline and kept time-consistent where possible. Per-frame correction could
absorb the real color change we want to visualize. This is a design constraint
to test, not an implemented radiometric calibration method.

## First backend benchmark

Before adding CUDA research dependencies, review the candidate's license and
dependency requirements, choose an isolated compatible environment, then test
a small controlled capture. A WSL/Linux environment is an available future
fallback if native Windows builds cannot be made reliable.

Measure GPU memory, runtime, held-out RGB quality, calibration/timing residuals,
and known geometry/color changes. Compare a color-only case, geometry-only
case and combined case, including hidden/new surfaces. Begin with fewer frames
and an explicit image-size budget; retain native originals and increase
resolution only after memory/quality checks. Training duration alone is not
an accuracy claim.

Export queryable temporal parameters and stable track IDs before connecting
real data to the maps/trails. A CPU synthetic point preview validates the
analysis semantics, not a learned Gaussian trajectory or physical strain.
