# Temporal Fields 4D Gaussian Splatting (TF4DGS): Installation approval plan

Prepared on 2026-10-03 (America/New_York).

Status: approved by the user on 2026-10-03. The static installation and
functional validation completed on 2026-10-03, with no restart required.
Approval authorizes the actions below; completed installations are recorded
separately in PROJECT_MEMORY.md.

The starting-state list below is historical. On 2026-10-05, the user authorized
building the dynamic foundation; `tf4dgs` now includes Python 3.11 and the local
CPU capture/analysis package. This did not alter the installed static tools or
authorize a particular GPU research backend. See `docs/DYNAMIC_FOUNDATION.md`.

## Outcome for this installation pass

Set up the free native Windows static workflow: video frame extraction with
FFmpeg, GPU structure from motion with COLMAP, and Gaussian training/viewing
with a locally built LichtFeld Studio. The commands and version pins are in
[INSTALLATION.md](INSTALLATION.md). Progress and restart instructions belong in
[PROJECT_MEMORY.md](PROJECT_MEMORY.md).

The `tf4dgs` Conda environment already exists. LichtFeld manages its bundled
Python independently. Research Python/PyTorch and the dynamic reconstruction
implementation will be selected during the 4D phase; their compatibility
requirements are not established by this static installation.

## Verified starting state

Read-only checks and a temporary developer-shell selection confirmed:

- Project root: `C:\Users\mnijat\Desktop\Git\TF4DGS`; rename is complete.
- Windows 11 Enterprise 25H2, build 26200.9168.
- RTX A4000, 16 GB VRAM, compute capability 8.6; driver 595.95.
- Intel i7-13700; approximately 32 GB RAM and 814 GiB free on C:.
- Visual Studio Community 2026 18.10.3, Desktop C++ tools, MSVC
  14.51.36231 and Windows SDK 10.0.26100.0 are installed and selectable.
- Existing CMake 4.3.1, Ninja 1.13.2 and VS-bundled Git 2.55.0 are usable.
- Miniconda 26.7.1 and the empty `tf4dgs` environment already exist.
- Microsoft x64 VC runtime 14.51.36247 is installed.
- CUDA Toolkit, COLMAP, FFmpeg and the LichtFeld build remain pending.
- R: is free. A temporary project drive alias can shorten build paths.
- The current process is not elevated. Visual Studio, Windows Update and CBS
  do not report a required restart. An existing deletion-only pending-file
  queue is a baseline to compare with installer results, not an instruction
  to restart now.

## Proposed software and locations

| Component | Selected version | Installation action | Administrator access |
| --- | --- | --- | --- |
| CUDA developer toolkit | NVIDIA 13.2.2 Update 2; nvcc 13.2.86 | Download verified installer and install compiler/runtime/development libraries under `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2` | Required |
| COLMAP | 4.2.1 Windows CUDA archive | Verify and extract entire archive under `.local\tools\colmap-4.2.1` | Not normally required |
| FFmpeg / FFprobe | Gyan 9.0.2 essentials build | Verify and extract under `.local\tools\ffmpeg-9.0.2` | Not normally required |
| LichtFeld Studio | v0.5.3, commit `d8c50c6a3e2273cb74130a6e9023de8d068af52d` | Clone recursive source, build Release for the A4000, install complete bundled app under `.local\apps\lichtfeld-v0.5.3` | Not normally required |
| vcpkg and manifest dependencies | Tool/repository commit `930ecc42b512b564571d767f70775d284a6fa307`; manifest baseline `c3867e714dd3a51c272826eea77267876517ed99` | Clone, bootstrap with metrics disabled, download/build the pinned native dependencies | Not normally required |
| Bundled Python and build utilities | Selected by the pinned LichtFeld source/manifest | Fetch and package runtime/build dependencies, including Python 3.12.13 and Astral uv 0.10.2 | Not normally required |

The initial combination reuses the installed Visual Studio 2026 compiler.
NVIDIA documents VS 2026 support, and Microsoft's STL table pairs MSVC 14.51
with CUDA 13.2. A real CUDA compilation/kernel check is required before the
larger LichtFeld build. Upstream's Windows CI uses VS 2022 and CUDA 12.8;
the selected newer combination is still subject to local build validation.
[NVIDIA compiler support](https://docs.nvidia.com/cuda/archive/13.2.2/cuda-installation-guide-microsoft-windows/index.html),
[Microsoft STL compatibility](https://github.com/microsoft/STL/wiki/Macro-_MSVC_STL_UPDATE),
[pinned LichtFeld Windows CI](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/.github/workflows/windows.yml).

The vcpkg tool checkout is intentionally newer than the manifest baseline: the
old repository checkout lacks the required glslang 16.2.0 and shader-slang
2026.5 versions. All exact overrides, including port versions, are available
at the selected tool checkout. The manifest baseline itself stays unchanged.
[Selected vcpkg commit](https://github.com/microsoft/vcpkg/commit/930ecc42b512b564571d767f70775d284a6fa307).

Vulkan libraries and shader tools are provided by the manifest. No separate
Vulkan SDK, Clang, Perl, LibTorch developer-test setup or nvJPEG2000 SDK is
currently required. CUDA's nvJPEG development/runtime library is needed for
the image codec. Portable builds fetch uv from its pinned Astral GitHub release.
[LichtFeld manifest](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/vcpkg.json),
[bundled uv setup](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/cmake/FetchUV.cmake),
[image-codec setup](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/external/CMakeLists.txt).

## Download verification

Use upstream/publisher downloads and the exact pins rather than moving `latest`
links. Build-system dependency downloads are included in the approval.

| Artifact | Verified integrity record |
| --- | --- |
| `cuda_13.2.2_windows.exe` | Official size 2,499,003,640 bytes; MD5 `9e4bcad21f296561fa834a4eeda079d2`; require a valid NVIDIA Authenticode signature before execution and record the local SHA-256 |
| COLMAP CUDA ZIP | SHA-256 `e9c5cbd84c2ea986d2e970a2473fc2d2e6b34a2cdcf5d3df2765c319a63af881` |
| FFmpeg essentials ZIP | SHA-256 `60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba` |

CUDA MD5 is the vendor's published file-integrity check; Authenticode is the
publisher check. COLMAP's Windows package is an unsigned GitHub Actions build,
so verify the release asset checksum instead of requiring a signature it lacks.
Transitive vcpkg ports use the source references/hashes from the pinned manifest
and registry. Record resolved package versions and source revisions.

Sources: [CUDA installer](https://developer.download.nvidia.com/compute/cuda/13.2.2/local_installers/cuda_13.2.2_windows.exe),
[NVIDIA checksums](https://developer.download.nvidia.com/compute/cuda/13.2.2/docs/sidebar/md5sum.txt),
[COLMAP release asset checksums](https://github.com/colmap/colmap/releases/expanded_assets/4.2.1),
[Gyan checksum](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip.sha256).

## Consolidated authorization requested

Approve the following actions for this static installation:

1. Download the listed software, recursive Git submodules, and dependencies
   referenced by the pinned LichtFeld/vcpkg build from their upstream publishers,
   public repositories, release CDNs and package hosts. Run the verified
   installers, upstream bootstrap/build scripts and resulting local programs.
2. Create/update project setup scripts, documentation and checkpoint records.
   Store downloads, source, builds, caches, tools and logs under `.local`, with
   ordinary user cache/temporary files where dependencies need them.
3. Install NVIDIA CUDA into the standard system location, allowing its normal
   toolkit files, installer registry entries and CUDA environment variables.
   Use unattended options where supported and suppress automatic reboot.
4. Create a temporary R: alias for this project and set compiler/CUDA/tool PATH
   variables in build sessions. Restore these session settings after a restart.
5. Build locally, run CPU/GPU checks and launch the installed viewer when needed
   to verify startup. Diagnose failures, retry interrupted downloads/stages,
   and make documented local compatibility fixes necessary for the selected
   source build, preserving the original revision and recording the changes.
6. Use the conditional fallbacks below only when a specific failure establishes
   the need. Record the reason before installing additional software.

This authorization covers standard software license acceptance needed for
these free installations. All project-local installed/generated files remain
ignored by Git; setup documentation and reproducibility scripts remain suitable
to commit later.

## Conditional fallbacks covered by the requested approval

| Trigger | Authorized response | Possible interaction |
| --- | --- | --- |
| An executable requires a newer Microsoft VC runtime | Install/update only the official Microsoft x64 redistributable, with reboot suppressed | Windows UAC |
| A native dependency reports a missing compatible compiler/SDK tool | Add the specific necessary Microsoft C++/Clang/SDK component or an upstream portable build utility; record its version and source | Windows UAC for Visual Studio components |
| A reproducible compiler/toolkit incompatibility prevents the selected LichtFeld build | Install a compatible VS 2022 C++ Build Tools/compiler and CUDA 12.8 toolkit alongside the existing tools; use a separate build directory | Windows UAC; possibly a required restart |

Fallbacks do not remove or replace the working VS 2026 installation. CUDA 12.8
installation must omit its bundled display driver; retain the working display
driver. It was 595.95 at approval and is 596.71 after the later machine restart,
changed outside this toolkit installation; post-restart GPU checks passed.
Do not use `-allow-unsupported-compiler` to evade a compiler rejection.
[Microsoft runtime download](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist),
[Microsoft installer parameters](https://learn.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio).

The scope remains free native Windows setup. A paid purchase, a display-driver
replacement, switching to WSL/Linux or an unrelated machine configuration
change would need a separate decision.

## Resources and completion checks

The CUDA installer is approximately 2.5 GB, COLMAP's ZIP approximately 395 MB
and FFmpeg's ZIP approximately 109 MB. Source/dependency downloads add to this.
Allow a conservative working budget of 100 GiB for downloads/builds/caches;
this is a planning allowance, not a measured final size. The first source build
may take several hours. Start with four build jobs and reduce to two if memory
pressure requires it.

Proceed in order: restore developer shell and paths; install CUDA; compile/run
the GPU kernel check both normally and with forced PTX compilation, matching
the portable LichtFeld build's needs; install and verify FFmpeg/COLMAP; build/install LichtFeld;
verify the bundled app and save actual versions/paths and results.

Without capture footage, verify video encode/decode/frame extraction with a
tiny generated clip, and actual COLMAP GPU SIFT extraction/matching on locally
generated textured images. These are installation smoke checks. Verify
LichtFeld command-line startup and its installed runtime/resources. Where a
minimal synthetic training fixture is practical, label its result separately.
Good-quality SfM reconstruction, training and deformation accuracy still need
the user's capture and calibration data.

## User interaction that advance approval cannot remove

Windows may display an administrator/UAC consent or credentials dialog because
the current process is not elevated. The user may need to approve that OS
dialog even after authorizing the work here. An installer-specific unavoidable
interactive choice will be explained if one occurs.

Do not restart automatically. If an installer requires it, first save completed
stages, executable locations, versions, logs and the exact resume command in
`PROJECT_MEMORY.md`, then ask the user to restart. Resume from that checkpoint
after the user returns.

## Approval record

User approval received on 2026-10-03, recorded at 04:33:58 UTC:

> I approve the static installation plan, including conditional fallbacks.

The user asked to start with CUDA and show its administrator prompt early if
possible. Download and verify the installer before launching it with elevation.
No automatic restart is authorized. Retain this approval across turns/restarts;
do not request approval again for actions already included in this plan.
