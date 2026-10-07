# Temporal Fields 4D Gaussian Splatting (TF4DGS): Installation

Prepared for this computer on **2026-10-02**.

Installation prerequisites and authorization scope rechecked on **2026-10-03**;
see [INSTALLATION_APPROVALS.md](INSTALLATION_APPROVALS.md).

Project folder: `TF4DGS`. Conda environment: `tf4dgs`.

This guide establishes the first static workflow:

**DJI Osmo Action 6 capture → FFmpeg frames → COLMAP SfM → LichtFeld Studio → saved splat.**

The project scope is in [PROJECT_SCOPE.md](PROJECT_SCOPE.md). Setup progress and
restart checkpoints belong in [PROJECT_MEMORY.md](PROJECT_MEMORY.md).

**Status (updated 2026-10-05):** Miniconda and the Python 3.11 `tf4dgs` CPU
capture/analysis environment are installed. CUDA
13.2.2 is installed and its ordinary/forced-PTX GPU checks passed on 2026-10-03.
COLMAP 4.2.1 and FFmpeg 9.0.2 are installed and their GPU/media smoke checks
passed. LichtFeld v0.5.3 is built and installed with the recorded CUDA 13
packaging patch. Synthetic GPU training, checkpoint resume, PLY export and
Vulkan viewer/model loading passed on 2026-10-03. No restart is required.
Actual stage results are recorded in PROJECT_MEMORY.md and the validation JSON
files. Continue with Section 7 for your first real capture; Sections 2-6 provide
the reproducible setup procedure for another machine.

The resolved native package inventory for this build is saved in
[`native-dependencies.json`](native-dependencies.json). The source manifest,
registry revisions and local patch define the reproducible inputs; package
ABIs and paths in the records describe this machine's build.

## 1. Selected setup

| Component | Version / choice | Action |
| --- | --- | --- |
| Windows | Windows 11 Enterprise 25H2, build 26200.9168 | Reuse |
| GPU | NVIDIA RTX A4000, 16 GB VRAM, compute capability 8.6 | Reuse |
| NVIDIA driver | 596.71 (595.95 at initial inspection) | Reuse; post-restart CUDA checks passed |
| Visual Studio Community | 2026, 18.10.3 | Reuse |
| MSVC x64 | Toolset 14.51.36231 | Select explicitly |
| Windows SDK | 10.0.26100.0 | Select existing SDK |
| CMake / Ninja / Git | 4.3.1-msvc1 / 1.13.2 / 2.55.0.windows.5 | Reuse Visual Studio copies |
| CUDA Toolkit | **13.2.2 Update 2**, nvcc 13.2.86 | Installed and GPU-verified |
| COLMAP | **4.2.1**, Windows x64 CUDA archive | Installed; GPU feature/matching checks passed |
| FFmpeg | **9.0.2**, Gyan essentials Windows build | Installed; encode/decode/extraction passed |
| LichtFeld Studio | **v0.5.3**, source build with recorded CUDA 13 packaging patch | Installed; synthetic training/resume/export and viewer loading passed |
| vcpkg | Tool/repository commit `930ecc42b512b564571d767f70775d284a6fa307`; retain manifest baseline | Bootstrapped; all 92 dependency ports installed |
| Conda manager | Miniconda 26.7.1, base Python 3.14.7 | Installed; `tf4dgs` now uses Python 3.11.16 for the CPU foundation |

The machine has an i7-13700, approximately 32 GB RAM and approximately 819 GB free
on C: at inspection. Build parallelism starts at four jobs.

CUDA 13.2.2 documents support for Visual Studio 2026 / MSVC 195x and Windows 11
25H2. The existing driver meets CUDA 13.x's Windows minor-compatibility minimum
of 580. Local compiler, native GPU and forced-PTX execution checks passed before
the LichtFeld build. Repeat these checks on another machine.
[NVIDIA Windows installation guide](https://docs.nvidia.com/cuda/archive/13.2.2/cuda-installation-guide-microsoft-windows/index.html),
[NVIDIA compatibility documentation](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html).

Keep MSVC 14.51 selected: Microsoft's STL compatibility table associates it
with CUDA 13.2. A future compiler update needs another compatibility check.
[Microsoft compiler/STL mapping](https://github.com/microsoft/STL/wiki/Macro-_MSVC_STL_UPDATE).

LichtFeld v0.5.3 requires CUDA 12.8+ and CMake 3.30+. Its Windows CI uses Visual
Studio 2022 and CUDA 12.8; this guide reuses this machine's newer compiler with a
compatible CUDA release. The release includes a Windows CUDA 13.2 build fix.
This machine's complete combination passed compilation and functional checks
after the runtime packaging patch described in Section 6. Another machine
still needs its own validation.
[LichtFeld release](https://github.com/MrNeRF/LichtFeld-Studio/releases/tag/v0.5.3),
[pinned build documentation](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/docs/building_and_distribution.md),
[pinned Windows CI](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/.github/workflows/windows.yml).

This is a free source-build route. The static setup uses LichtFeld's bundled
Python dependencies. The Conda environment supports the CPU capture and
point-analysis foundation; see Section 10 for reproducibility and Git handling.
The later 4D backend and its dependencies will be chosen in a separate phase.

## 2. Start a setup PowerShell session

Run the numbered sections in order in one **ordinary, non-administrator
PowerShell** session. CUDA's installer can request elevation separately.
Reopen and restore the session after any required restart.

Project-local tools, source, builds and logs will live under `.local`:

```text
TF4DGS/
  README.md
  INSTALLATION.md
  PROJECT_SCOPE.md
  PROJECT_MEMORY.md
  environment.yml
  .local/
    downloads/
    tools/
    src/
    build/
    apps/
    logs/
  data/
  outputs/
```

Use a temporary `R:` drive alias to keep Windows dependency-build paths short.
It points to this project folder; files remain in the folder on C:. The alias is
session/machine state to recreate after restarting. Stop if R: belongs elsewhere.

```powershell
$ErrorActionPreference = 'Stop'
$ProjectRoot = 'C:\Users\mnijat\Desktop\Git\TF4DGS'

function Assert-NativeSuccess {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE. Check its log."
    }
}

if (-not (Test-Path -LiteralPath $ProjectRoot -PathType Container)) {
    throw "Project folder does not exist: $ProjectRoot"
}

$ExpectedMapping = 'R:\: => ' + $ProjectRoot
$CurrentMappings = @(& subst.exe)
Assert-NativeSuccess 'Read drive aliases'

if (Test-Path -LiteralPath 'R:\') {
    if ($CurrentMappings -notcontains $ExpectedMapping) {
        throw 'R: already belongs to another location. Choose another free drive letter.'
    }
} else {
    & subst.exe R: $ProjectRoot
    Assert-NativeSuccess 'Create project drive alias'
}

$RunRoot = 'R:\'
$LocalRoot = Join-Path $RunRoot '.local'
$Downloads = Join-Path $LocalRoot 'downloads'
$Tools = Join-Path $LocalRoot 'tools'
$Sources = Join-Path $LocalRoot 'src'
$Builds = Join-Path $LocalRoot 'build'
$Apps = Join-Path $LocalRoot 'apps'
$Logs = Join-Path $LocalRoot 'logs'

foreach ($Folder in @($Downloads, $Tools, $Sources, $Builds, $Apps, $Logs)) {
    New-Item -ItemType Directory -Path $Folder -Force | Out-Null
}
Set-Location -LiteralPath $RunRoot
```

PowerShell does not reliably stop when a native program returns an error.
`Assert-NativeSuccess` supplies that check for the commands below.

### Load the existing compiler and tools

These paths were checked on this computer. This changes the current shell's
environment only.

```powershell
$VsRoot = 'C:\Program Files\Microsoft Visual Studio\18\Community'
$GitBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd'
$CmakeBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin'
$NinjaBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
$VsInstallerBin = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer'
$env:Path = "$VsInstallerBin;$GitBin;$CmakeBin;$NinjaBin;$env:Path"

Import-Module (Join-Path $VsRoot 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VsRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.51 -winsdk=10.0.26100.0'

$env:Path = "$GitBin;$CmakeBin;$NinjaBin;$env:Path"
$env:VCPKG_VISUAL_STUDIO_PATH = $VsRoot

if (-not $env:VCToolsVersion.StartsWith('14.51.')) {
    throw "Unexpected MSVC toolset: $env:VCToolsVersion"
}
Get-Command cl.exe
$env:VCToolsVersion
$env:WindowsSDKVersion

& git.exe --version
Assert-NativeSuccess 'Git version'
& cmake.exe --version
Assert-NativeSuccess 'CMake version'
& ninja.exe --version
Assert-NativeSuccess 'Ninja version'
& nvidia-smi.exe
Assert-NativeSuccess 'NVIDIA driver check'
```

Expected: MSVC 14.51, SDK 10.0.26100.0, the versions in Section 1, and an RTX
A4000 with the current installed driver. Driver 596.71 passed the checks after
the machine restarted; the CUDA toolkit installation did not replace it.
Record the actual output in the memory file.

## 3. Install CUDA 13.2.2 and verify compilation

On this computer, this stage is complete; do not rerun the installer.
The reusable `scripts\Install-Cuda.ps1` verifies the downloaded installer and
runs the selected toolkit components with elevation and reboot suppressed.
`scripts\Test-Cuda.ps1` runs both GPU checks below. These instructions remain
for installation on another machine.

Open the [CUDA 13.2.2 download archive](https://developer.nvidia.com/cuda-13-2-2-download-archive).
Select Windows → x86_64 → Windows 11 → an EXE installer. Save it in the physical
folder `C:\Users\mnijat\Desktop\Git\TF4DGS\.local\downloads`.

Run the signed NVIDIA installer. Use Custom installation and include the CUDA
development tools and runtime libraries. The default complete CUDA toolkit
selection is suitable; profiling tools are optional. Avoid removing CUDA
libraries to minimize the install. Separate Visual Studio integration is not
required for the Ninja build.

Keep the default toolkit location:

```text
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2
```

CUDA 13.1+ Windows toolkits no longer bundle the display driver. Keep the
existing driver for this first check.
[NVIDIA release notes](https://docs.nvidia.com/cuda/archive/13.2.2/cuda-toolkit-release-notes/index.html).

If the installer requires a restart, follow Section 9 before continuing.
An elevated installer may not see the ordinary shell's R: alias; use the physical
C: path when selecting downloads.

After installation, restore Section 2 if the shell was closed, then run:

```powershell
$CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2'
$Nvcc = Join-Path $CudaRoot 'bin\nvcc.exe'
if (-not (Test-Path -LiteralPath $Nvcc)) {
    throw 'CUDA compiler was not found at the expected location.'
}
$env:CUDA_PATH = $CudaRoot
$env:Path = (Join-Path $CudaRoot 'bin') + ';' + $env:Path
& $Nvcc --version
Assert-NativeSuccess 'CUDA compiler version'
```

Expected: CUDA 13.2, nvcc build 13.2.86. Confirm Update 2 in the installer/version
record; the directory name alone does not identify the update.

### Compile and run a small GPU check

This verifies the selected compiler, CUDA runtime and a real GPU kernel before
the larger dependency build.

```powershell
$Preflight = Join-Path $Builds 'cuda-preflight'
New-Item -ItemType Directory -Path $Preflight -Force | Out-Null
$CudaCheckSource = Join-Path $Preflight 'cuda_check.cu'
$CudaCheckExe = Join-Path $Preflight 'cuda_check.exe'

@'
#include <cuda_runtime.h>
#include <cstdio>

static bool ok(cudaError_t result, const char* step) {
    if (result == cudaSuccess) return true;
    std::fprintf(stderr, "%s: %s\n", step, cudaGetErrorString(result));
    return false;
}
__global__ void write_value(int* value) { *value = 42; }

int main() {
    int count = 0;
    if (!ok(cudaGetDeviceCount(&count), "Device count") || count < 1) return 1;
    cudaDeviceProp properties{};
    if (!ok(cudaGetDeviceProperties(&properties, 0), "Device properties")) return 1;
    std::printf("GPU: %s; compute capability %d.%d\n",
                properties.name, properties.major, properties.minor);
    int* device_value = nullptr;
    if (!ok(cudaMalloc(reinterpret_cast<void**>(&device_value), sizeof(int)), "Allocate")) return 1;
    write_value<<<1, 1>>>(device_value);
    if (!ok(cudaGetLastError(), "Launch") ||
        !ok(cudaDeviceSynchronize(), "Synchronize")) return 1;
    int value = 0;
    if (!ok(cudaMemcpy(&value, device_value, sizeof(int), cudaMemcpyDeviceToHost), "Read back")) return 1;
    if (!ok(cudaFree(device_value), "Free")) return 1;
    std::printf("Kernel result: %d\n", value);
    return value == 42 ? 0 : 1;
}
'@ | Set-Content -LiteralPath $CudaCheckSource -Encoding ASCII

& $Nvcc -std=c++20 -arch=sm_86 $CudaCheckSource -o $CudaCheckExe 2>&1 |
    Tee-Object -FilePath (Join-Path $Logs 'cuda-preflight-build.log')
Assert-NativeSuccess 'Compile CUDA check'
& $CudaCheckExe
Assert-NativeSuccess 'Run CUDA check'

# LichtFeld portable mode also requires working driver PTX compilation.
$PreviousPtxSetting = $env:CUDA_FORCE_PTX_JIT
try {
    $env:CUDA_FORCE_PTX_JIT = '1'
    & $CudaCheckExe
    Assert-NativeSuccess 'Run CUDA PTX compilation check'
} finally {
    $env:CUDA_FORCE_PTX_JIT = $PreviousPtxSetting
}
```

Expected: RTX A4000, compute capability 8.6, `Kernel result: 42` and exit code 0.
Require both the ordinary kernel run and the forced PTX run to pass: satisfying
the CUDA minor-compatibility driver minimum alone does not prove PTX support.
[NVIDIA PTX compatibility limits](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html),
[forced PTX check](https://docs.nvidia.com/cuda/archive/13.1.1/cuda-programming-guide/05-appendices/environment-variables.html).
Stop and investigate a failure before installing LichtFeld dependencies.
Do not bypass a compiler rejection with `-allow-unsupported-compiler`.

## 4. Install COLMAP and FFmpeg

On this computer, this stage and functional smoke checks are complete.
Reusable helpers: `scripts\Install-PortableTools.ps1` and
`scripts\Test-PortableTools.ps1`. See `static-tools.json` for executable paths
and `static-tools-validation.json` for actual smoke-check results.

Both tools use extracted archives. Keep the complete extracted directory,
including DLLs and support files.

Define a download helper that verifies SHA-256 and can reuse a verified file:

```powershell
function Get-VerifiedArchive {
    param(
        [string]$Uri,
        [string]$Destination,
        [string]$ExpectedSha256
    )
    if (-not (Test-Path -LiteralPath $Destination)) {
        Invoke-WebRequest -Uri $Uri -OutFile $Destination -UseBasicParsing
    }
    $Actual = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
    if ($Actual -ne $ExpectedSha256) {
        throw "SHA-256 mismatch: $Destination. Do not extract this download."
    }
}
```

### COLMAP 4.2.1

Use the CUDA-enabled asset from the
[official COLMAP release](https://github.com/colmap/colmap/releases/tag/4.2.1).

```powershell
$ColmapZip = Join-Path $Downloads 'colmap-4.2.1-x64-windows-cuda.zip'
$ColmapRoot = Join-Path $Tools 'colmap-4.2.1'
$ColmapUri = 'https://github.com/colmap/colmap/releases/download/4.2.1/colmap-x64-windows-cuda.zip'
$ColmapSha256 = 'e9c5cbd84c2ea986d2e970a2473fc2d2e6b34a2cdcf5d3df2765c319a63af881'

Get-VerifiedArchive -Uri $ColmapUri -Destination $ColmapZip -ExpectedSha256 $ColmapSha256
if (-not (Test-Path -LiteralPath $ColmapRoot)) {
    Expand-Archive -LiteralPath $ColmapZip -DestinationPath $ColmapRoot
}
$ColmapLaunchers = @(Get-ChildItem -LiteralPath $ColmapRoot -Recurse -File -Filter 'COLMAP.bat')
if ($ColmapLaunchers.Count -ne 1) {
    throw 'Expected one COLMAP.bat in the extracted package.'
}
$Colmap = $ColmapLaunchers[0].FullName
& $Colmap -h
Assert-NativeSuccess 'COLMAP command-line check'
```

Use the supplied batch launcher so its bundled DLL/plugin paths are set.
GUI startup and GPU feature extraction are checked with the first dataset.
[COLMAP Windows command-line instructions](https://colmap.github.io/cli.html).

### FFmpeg 9.0.2

FFmpeg's own site distributes source and links external Windows build providers.
Use the pinned Gyan essentials build, which includes `ffmpeg` and `ffprobe`.
[FFmpeg downloads](https://ffmpeg.org/download.html),
[Gyan build provider](https://www.gyan.dev/ffmpeg/builds/),
[pinned archive checksum](https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip.sha256).

```powershell
$FfmpegUri = 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip'
$FfmpegZip = Join-Path $Downloads 'ffmpeg-9.0.2-essentials_build.zip'
$FfmpegRoot = Join-Path $Tools 'ffmpeg-9.0.2'
$FfmpegSha256 = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'
Get-VerifiedArchive -Uri $FfmpegUri -Destination $FfmpegZip -ExpectedSha256 $FfmpegSha256

if (-not (Test-Path -LiteralPath $FfmpegRoot)) {
    Expand-Archive -LiteralPath $FfmpegZip -DestinationPath $FfmpegRoot
}
$FfmpegCandidates = @(Get-ChildItem -LiteralPath $FfmpegRoot -Recurse -File -Filter 'ffmpeg.exe')
if ($FfmpegCandidates.Count -ne 1) {
    throw 'Expected one ffmpeg.exe in the extracted package.'
}
$Ffmpeg = $FfmpegCandidates[0].FullName
$Ffprobe = Join-Path (Split-Path -Parent $Ffmpeg) 'ffprobe.exe'
& $Ffmpeg -version
Assert-NativeSuccess 'FFmpeg version'
& $Ffprobe -version
Assert-NativeSuccess 'FFprobe version'
```

Expected: COLMAP 4.2.1 and FFmpeg/FFprobe 9.0.2. Save the actual checksum results
and executable paths in `PROJECT_MEMORY.md`. If an interrupted extraction
left a partial directory, inspect it before replacing it; do not treat its
presence as proof of a completed install.

## 5. Get the pinned LichtFeld source and vcpkg

LichtFeld source pin:

```text
Tag:    v0.5.3
Commit: d8c50c6a3e2273cb74130a6e9023de8d068af52d
```

This is the original upstream baseline. The user has published the recorded
CUDA packaging fix to their LichtFeld fork at
`b4e26dc929d23ad8c4cc266e61eb8bf7334ede36` on `tf4dgs`. TF4DGS records the
selected fork revision through its submodule reference; source and dependency
validation below use that reference.

Dependency registry pin from its
[vcpkg manifest](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/vcpkg.json):

```text
c3867e714dd3a51c272826eea77267876517ed99
```

The vcpkg **repository/tool checkout** is a separate pin:

```text
930ecc42b512b564571d767f70775d284a6fa307
```

Keep the manifest baseline unchanged. Checking out vcpkg itself at that older
baseline cannot resolve the release's glslang 16.2.0 and shader-slang 2026.5
overrides. The newer repository commit contains every exact overridden version
and port version. [Pinned vcpkg commit](https://github.com/microsoft/vcpkg/commit/930ecc42b512b564571d767f70775d284a6fa307),
[glslang versions](https://github.com/microsoft/vcpkg/blob/930ecc42b512b564571d767f70775d284a6fa307/versions/g-/glslang.json),
[Slang versions](https://github.com/microsoft/vcpkg/blob/930ecc42b512b564571d767f70775d284a6fa307/versions/s-/shader-slang.json).

LichtFeld and vcpkg are project submodules under `.local/src`. Clone TF4DGS
with `--recurse-submodules`, or initialize them with the commands below. Their
exact selected commits are recorded by TF4DGS; the values above identify the
initial validated baseline. Future LichtFeld fork commits are selected by
updating the submodule reference. See [GIT_SETUP.md](GIT_SETUP.md).

Do not overwrite unrecorded source commits or local edits. Before building an
intentional fork revision, commit it in the fork and stage its new submodule
reference in TF4DGS. Keep full vcpkg Git history for versioned port resolution.

```powershell
$LfsSource = Join-Path $Sources 'LichtFeld-Studio'
$VcpkgRoot = Join-Path $Sources 'vcpkg'
. (Join-Path $ProjectRoot 'scripts\Get-ProjectSubmoduleCommit.ps1')
$LfsCommit = Get-ProjectSubmoduleCommit -ProjectRoot $ProjectRoot -RelativePath '.local/src/LichtFeld-Studio'
$VcpkgCommit = Get-ProjectSubmoduleCommit -ProjectRoot $ProjectRoot -RelativePath '.local/src/vcpkg'

& git.exe -C $ProjectRoot submodule update --init --recursive
Assert-NativeSuccess 'Initialize source submodules'
$ActualLfsCommit = (& git.exe -C $LfsSource rev-parse HEAD).Trim()
Assert-NativeSuccess 'Read LichtFeld commit'
if ($ActualLfsCommit -ne $LfsCommit) { throw 'LichtFeld commit differs from the recorded submodule reference.' }

$ActualVcpkgCommit = (& git.exe -C $VcpkgRoot rev-parse HEAD).Trim()
Assert-NativeSuccess 'Read vcpkg commit'
if ($ActualVcpkgCommit -ne $VcpkgCommit) { throw 'vcpkg commit differs from the recorded submodule reference.' }

& (Join-Path $VcpkgRoot 'bootstrap-vcpkg.bat') -disableMetrics
Assert-NativeSuccess 'Bootstrap vcpkg'

$env:VCPKG_ROOT = $VcpkgRoot
$VcpkgCache = Join-Path $LocalRoot 'cache\vcpkg'
New-Item -ItemType Directory -Path $VcpkgCache -Force | Out-Null
$env:VCPKG_DEFAULT_BINARY_CACHE = $VcpkgCache
$env:VCPKG_MAX_CONCURRENCY = '4'
$env:CMAKE_BUILD_PARALLEL_LEVEL = '4'
& (Join-Path $VcpkgRoot 'vcpkg.exe') version
Assert-NativeSuccess 'vcpkg executable check'
```

CMake will install dependencies from LichtFeld's manifest. This includes its
Python 3.12.13 runtime and graphics/media libraries. Portable builds also fetch
and bundle Astral uv 0.10.2. Vulkan headers/loader, glslang tools and Slang come
from the manifest; a separate Vulkan SDK or Clang installation is not a default
requirement of this pinned release. Its internal FFmpeg dependency is separate
from the command-line FFmpeg in Section 4.
[Bundled uv setup](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/cmake/FetchUV.cmake),
[vcpkg concurrency setting](https://learn.microsoft.com/en-us/vcpkg/users/config-environment#vcpkg_max_concurrency).

## 6. Build and install LichtFeld

The resumable project helper restores the compiler session and R: alias on
each invocation. Run one stage at a time and check that it completes:

```powershell
& .\scripts\Install-LichtFeld.ps1 -Stage Prepare
& .\scripts\Install-LichtFeld.ps1 -Stage Configure
& .\scripts\Install-LichtFeld.ps1 -Stage Build
& .\scripts\Install-LichtFeld.ps1 -Stage Install
```

After an interruption, resume the first unfinished stage recorded in
`lichtfeld-installation.json` and `PROJECT_MEMORY.md`. Existing sources and
dependency caches are reused. Configure prefetches x264's exact pinned archive
from VideoLAN's canonical URL and verifies its original SHA-512: the port's
double-slash URL returned an HTML bot-check page on this machine. No source
revision or expected checksum is changed. The manual CMake commands below
assume that this verified download is already cached.

Configure also applies the recorded
[`CUDA 13 runtime search patch`](patches/lichtfeld-v0.5.3-cuda13-runtime-search.patch).
The original source omits CUDA's Windows `bin/x64` directory when packaging
runtime DLLs, causing installation to fail resolving `nvjpeg64_13.dll` on this
machine. The patch adds that existing directory to the search list; the source
revision and dependency pins stay unchanged. Its SHA-256 is recorded in
`lichtfeld-installation.json`. Run the Configure helper before the manual
commands below so this patch and verified downloads are prepared.

For a long build that can survive closing VS Code, start the hidden worker:

```powershell
& .\scripts\Start-StaticInstallationWorker.ps1 -StartStage Configure
Get-Content -LiteralPath .\installation-worker.json
```

It runs the remaining stages and synthetic training validation in order, writes
stage checkpoints to `PROJECT_MEMORY.md`, and stops on the first error. Check
the recorded process ID is still alive before launching a second worker. Resume
at the first unfinished stage, using `-StartStage Build`, `Install` or `Validate`
when earlier stages are complete. Completed vcpkg ports are cached; an
interrupted port can be rebuilt from the beginning by vcpkg.

The worker uses Windows WMI process creation with a hidden window and
`CREATE_BREAKAWAY_FROM_JOB`, independently of the editor terminal. No scheduled
task or startup service is installed. Windows restart still stops the worker;
restore it from the saved checkpoint afterward.
[Microsoft process creation documentation](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/create-method-in-class-win32-process),
[startup flags](https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-processstartup).

Use direct CMake + Ninja. **There are no CMake presets at v0.5.3.**
The older `build_lichtfeld.ps1` is not the selected route: its CUDA-version
restriction and LibTorch download do not match this release's main build.

This builds an optimized Release application with a bundled runtime.
`BUILD_CUDA_MIN_SM=86` targets this A4000 and newer compatible GPUs.
Portable mode uses PTX, so the driver may take extra time compiling kernels at
first use. The first dependency/source build can take substantially longer than
a training run.

Flags and packaging are based on the
[pinned CMake source](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/CMakeLists.txt)
and [Python packaging source](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/src/python/CMakeLists.txt).

```powershell
. (Join-Path $ProjectRoot 'scripts\Initialize-BuildSession.ps1') -UseDriveAlias
$LfsBuild = Join-Path $Builds 'lichtfeld-v0.5.3-release'
$LfsInstall = Join-Path $Apps 'lichtfeld-v0.5.3'

$ConfigureArgs = @(
    '-S', $LfsSource
    '-B', $LfsBuild
    '-G', 'Ninja'
    '-DCMAKE_BUILD_TYPE=Release'
    "-DCMAKE_TOOLCHAIN_FILE=$VcpkgRoot/scripts/buildsystems/vcpkg.cmake"
    '-DVCPKG_TARGET_TRIPLET=x64-windows'
    '-DVCPKG_HOST_TRIPLET=x64-windows'
    "-DCUDAToolkit_ROOT=$CudaRoot"
    "-DCMAKE_CUDA_COMPILER=$Nvcc"
    '-DBUILD_PORTABLE=ON'
    '-DBUILD_CUDA_MIN_SM=86'
    '-DBUILD_TESTS=OFF'
    '-DBUILD_PYTHON_STUBS=OFF'
    '-DLFS_DEV_IMPORT_SOURCE_PYTHON=OFF'
    '-DLFS_DEV_IMPORT_SOURCE_RESOURCES=OFF'
    '-DCUDA_DEVICE_DEBUG=OFF'
    '-DLFS_FAST_COMPILE=OFF'
)

Invoke-CheckedNative 'cmake.exe' $ConfigureArgs (Join-Path $Logs 'lichtfeld-configure.log')

Invoke-CheckedNative 'cmake.exe' @('--build', $LfsBuild, '--parallel', '4') (Join-Path $Logs 'lichtfeld-build.log')

Invoke-CheckedNative 'cmake.exe' @('--install', $LfsBuild, '--prefix', $LfsInstall) (Join-Path $Logs 'lichtfeld-install.log')

$Lichtfeld = Join-Path $LfsInstall 'bin\LichtFeld-Studio.exe'
if (-not (Test-Path -LiteralPath $Lichtfeld)) {
    throw 'Installed LichtFeld executable was not found.'
}
& $Lichtfeld --help
Assert-NativeSuccess 'LichtFeld command-line check'
```

Keep the entire `lichtfeld-v0.5.3` install directory. Its `bin`, `Lib`, `DLLs`
and resources work together; moving only the EXE will break the runtime.

The worker runs the synthetic application check automatically. When using the
manual stages, run it once after installation:

```powershell
& .\scripts\Test-LichtFeld.ps1
```

It checks bundled Python startup, prepares a tiny known-pose scene, trains for
20 iterations, preserves a genuine iteration-10 checkpoint through a Python
callback, and resumes that checkpoint to iteration 20 with PLY export. This
release restores the training limit stored in the checkpoint, so supplying a
larger `--iter` during resume is not sufficient to extend that limit. The
synthetic check verifies software operation; capture quality is tested below.

Verify viewer startup and exported-model loading after the synthetic check:

```powershell
& .\scripts\Test-LichtFeldViewer.ps1
```

This starts and closes only its own verification process, checking Vulkan
device initialization, CUDA memory/semaphore sharing and loading the exported
405-Gaussian fixture. It isolates the child process from the build-tool and
Python PATH settings. Results are saved in `lichtfeld-validation.json`; logs
are under `.local\logs\lichtfeld-viewer-*.log`. This is a startup check, not a
visual-quality assessment.

For normal use, open PowerShell in the project folder and launch the installed
viewer directly. No build session or R: alias is needed for this command:

```powershell
& .\.local\apps\lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe
```

Keep the complete install directory together. The application reports
`v0.5.3-dirty (d8c50c6a)` because of the documented packaging patch. Inspect the
window and UI, then close the viewer before subsequent command-line training.

If build failures are demonstrably compiler-specific, assess the upstream CI
combination, Visual Studio 2022 + CUDA 12.8, as a fallback. Diagnose and record
the error before changing the compiler/toolkit pins or build directory.

## 7. First static dataset and training check

This section needs your own footage. The software installation can finish
before footage is ready; reconstruction quality remains unvalidated until this
check is completed.

### Capture and extract frames

Use an unchanged, textured scene with steady light and strong view overlap.
Move the DJI camera around the scene slowly. Keep recording resolution, field
of view, exposure and white balance fixed. Turn off electronic stabilization
and other changing image warps where the selected camera mode permits it.
Start with normal SDR video; Log/HDR footage needs a deliberate color transform
before its colors can be treated consistently.

Copy the original video to `data\static_desk_001\capture.mp4`. The following
starting settings extract two frames per second with maximum width 2048 px.
Adjust frame selection/resolution after inspecting sharpness, overlap and
registration; two fps is not a reconstruction-quality guarantee.

```powershell
$DatasetRoot = Join-Path $RunRoot 'data\static_desk_001'
$Capture = Join-Path $DatasetRoot 'capture.mp4'
$Images = Join-Path $DatasetRoot 'images'
$Sparse = Join-Path $DatasetRoot 'sparse\0'
$Undistorted = Join-Path $DatasetRoot 'undistorted'
$TrainingOutput = Join-Path $RunRoot 'outputs\static_desk_001'

foreach ($Folder in @($Images, $Sparse)) {
    New-Item -ItemType Directory -Path $Folder -Force | Out-Null
}
& $Ffprobe -v error -show_streams -show_format $Capture
Assert-NativeSuccess 'Inspect capture'
& $Ffmpeg -n -i $Capture -vf "fps=2,scale='min(2048,iw)':-2" -q:v 2 (Join-Path $Images 'frame_%06d.jpg')
Assert-NativeSuccess 'Extract frames'
```

Remove blurred or redundant frames from the selected dataset while preserving
the original recording. Finish frame selection before COLMAP extraction.

### Reconstruct with COLMAP

Launch its GUI:

```powershell
& $Colmap gui
```

1. Create a project with database `data\static_desk_001\database.db` and the
   extracted `images` directory.
2. Extract SIFT features with GPU enabled. Share intrinsics for frames from the
   same unchanged recording mode. Select a camera model appropriate to the
   actual DJI footage: a wide distorted view and a camera-dewarped view may
   need different models.
3. Use sequential matching for the orbital video. Reconstruct the sparse scene.
4. Inspect registered cameras, sparse points and coverage. If registration is
   fragmented or visibly wrong, fix frame/capture/calibration choices first.
5. Export the intended reconstruction as a **binary model** to
   `data\static_desk_001\sparse\0`.

COLMAP models contain `cameras.bin`, `images.bin` and `points3D.bin`; newer
versions can also include rig/frame metadata. Dense MVS is unnecessary for
this Gaussian initialization.
[COLMAP tutorial](https://colmap.github.io/tutorial.html),
[model format](https://colmap.github.io/format.html).

Create an undistorted COLMAP dataset with pinhole cameras:

```powershell
& $Colmap image_undistorter --image_path $Images --input_path $Sparse --output_path $Undistorted --output_type COLMAP --max_image_size 2048
Assert-NativeSuccess 'Undistort COLMAP dataset'

# Normalize the model layout for the Gaussian dataset loader.
# Keep any original flat sparse files for COLMAP's own workspace.
$UndistortedSparse = Join-Path $Undistorted 'sparse'
$UndistortedModel = Join-Path $UndistortedSparse '0'
New-Item -ItemType Directory -Path $UndistortedModel -Force | Out-Null
foreach ($ModelFile in @('cameras.bin', 'images.bin', 'points3D.bin', 'rigs.bin', 'frames.bin')) {
    $FlatFile = Join-Path $UndistortedSparse $ModelFile
    $TargetFile = Join-Path $UndistortedModel $ModelFile
    if (Test-Path -LiteralPath $FlatFile) {
        Copy-Item -LiteralPath $FlatFile -Destination $TargetFile -Force
    }
}
foreach ($RequiredFile in @('cameras.bin', 'images.bin', 'points3D.bin')) {
    if (-not (Test-Path -LiteralPath (Join-Path $UndistortedModel $RequiredFile))) {
        throw "Undistorted model is missing $RequiredFile."
    }
}
```

The loader dataset now has `undistorted\images` and `undistorted\sparse\0`
containing the binary camera/image/point model. Load the **undistorted dataset
root** in LichtFeld. Preserve the original model and images.
The undistortion flags were checked against
[COLMAP 4.2.1 source](https://github.com/colmap/colmap/blob/4.2.1/src/colmap/exe/image.cc).

### Train, save and reopen

Use LichtFeld's GUI to load the dataset, start training and save a checkpoint.
Inspect the result from new viewpoints and export a PLY.

The pinned release also documents this dataset/output invocation:

```powershell
& $Lichtfeld -d $Undistorted -o $TrainingOutput
Assert-NativeSuccess 'Static training run'
```

Check `--help` before adding iteration, resolution or Gaussian-count options.
Start with a small run that proves training, checkpoint loading and export;
then tune image resolution and model size for the 16 GB GPU and the approximate
two-hour training budget.
[LichtFeld dataset/training documentation](https://github.com/MrNeRF/LichtFeld-Studio/blob/v0.5.3/README.md).

Installation acceptance:

- CUDA check compiles and returns 42.
- FFmpeg/FFprobe and COLMAP report the pinned versions.
- LichtFeld starts and loads the undistorted model.
- GPU feature extraction and a small GPU training run complete.
- A saved checkpoint reopens and a PLY export is viewable.

Record training settings, wall time, VRAM use and visible quality. Installation
success establishes a working static baseline; physical deformation accuracy
will need separate calibration and validation during the 4D phase.

## 8. Resume and troubleshoot

| Symptom | Action |
| --- | --- |
| Git, CMake, Ninja or compiler not found | Restore Section 2 in the current shell. |
| `python` opens the Microsoft Store | Use the bundled runtime; this setup does not depend on the Store alias. |
| Unsupported compiler / CUDA host error | Confirm MSVC 14.51 and nvcc 13.2.86, inspect the first error, then assess the fallback. |
| Long-path build errors | Confirm all source/build/tool paths use the workspace's R: alias. |
| Download or dependency failure | Keep caches and logs; correct the failure and rerun the failed configure/build step. |
| CPU build runs out of RAM | Reduce both vcpkg concurrency and CMake build jobs to two. |
| GPU training runs out of VRAM | Reduce dataset image resolution or Gaussian count after checking the actual error. |
| Missing Python/DLL/shader resource | Check the complete install tree and install log; launch its installed EXE. |
| Instructions mention other flags/dependencies | Compare with v0.5.3 source; current master documentation may differ. |

Once a stage passes, resume from the next unfinished stage. Build commands reuse
their existing build tree. Restore the same compiler, CUDA and R: environment
before resuming; do not silently change those paths inside a configured tree.

## 9. Restart checkpoint and Git handling

A Windows restart is needed only if an installer or confirmed system state
requires one. Before asking you to restart, update `PROJECT_MEMORY.md` with:

```markdown
## Installation checkpoint
- Date/time:
- Completed installation-guide sections:
- Installed versions and physical executable paths:
- Validations passed:
- Logs and exact failing/unfinished step:
- Restart reason:
- Next command/action:
- Expected result:
- Session to restore: Section 2, then CUDA paths and relevant stage variables.
```

After restart, verify the installed state, recreate R:, load the developer
shell, restore variables from the relevant sections and continue at the saved
step. Do not rerun completed installers merely to restore shell variables.

Keep project documents, scripts, environment definitions, patches and source
submodule references in Git. The root `.gitignore` excludes generated files
while allowing the two source submodules:

```gitignore
/.local/*
!/.local/src/
/.local/src/*
!/.local/src/LichtFeld-Studio/
!/.local/src/vcpkg/
/data/
/outputs/
/*-installation.json
/*-validation.json
/installation-worker.json
/static-tools.json
```

The local Git repository is initialized on `main`, with the source submodules
registered. The user published the LichtFeld fix and the main project;
`main` tracks `origin/main`. [GIT_SETUP.md](GIT_SETUP.md)
contains the commands for publishing the existing patch to your fork and making
the first TF4DGS commit/push. Later clone with `--recurse-submodules`.

The CPU dynamic foundation now supplies session/calibration checks,
timestamp synchronization, extraction and selected-point maps/trails. See
[the foundation guide](docs/DYNAMIC_FOUNDATION.md). A calibrated real-data
pipeline and GPU 4D reconstruction backend remain pending; their research
dependencies will be selected separately.

## 10. tf4dgs Conda environment and setup on another machine

The project environment is named **`tf4dgs`**, defined in
[environment.yml](environment.yml). It supplies Python 3.11, pip and setuptools
from conda-forge for the CPU foundation. Research GPU dependencies are pending
backend selection. The tested Windows builds are saved in
[environments/tf4dgs-win-64.explicit.txt](environments/tf4dgs-win-64.explicit.txt).
Between Miniconda and Anaconda Distribution, **Miniconda for Windows x86_64**
is the recommended starting point: it supplies Conda and Python with a minimal
initial package set, allowing this project to select its own dependencies.
[Official comparison](https://www.anaconda.com/docs/getting-started/concepts/anaconda-or-miniconda).

Miniconda was installed and verified on **2026-10-02**:

| Item | Verified value |
| --- | --- |
| Install directory | `C:\Users\mnijat\miniconda3` |
| Conda version | 26.7.1 |
| Base Python version | 3.14.7 |
| Installer exit code | 0 |
| Installer signature | Valid, Anaconda, Inc. |
| PATH/default Python registration | Disabled by installer flags |
| Restart | None requested |

The bundled base Python version does not set the Python version for future
project environments. Use the project's dedicated environment for research
packages. LichtFeld's bundled Python remains managed by its source build.

The reusable [Install-Miniconda.ps1](scripts/Install-Miniconda.ps1) downloads
the pinned installer, checks its SHA-256 and publisher signature, installs for
the current user and verifies Conda/Python. It stops if the target directory
already exists. Its version record is saved in
local `conda-installation.json` file, excluded from Git.

Pinned installer:
`Miniconda3-py314_26.7.1-1-Windows-x86_64.exe`. SHA-256:
`27f1f8ae8c27bc22bbc383b84bf08c63a20a6e190f3975f3502625b1045330b2`.
[Official installer index](https://repo.anaconda.com/miniconda/),
[Windows installation flags](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html).

On a new compatible Windows machine, from the project folder:

```powershell
& '.\scripts\Install-Miniconda.ps1'
```

On this computer, the installed manager can be checked directly:

```powershell
& 'C:\Users\mnijat\miniconda3\Scripts\conda.exe' --version
```

Files to keep in Git:

- `environment.yml`: environment name, channels, Python version and direct
  CPU-foundation dependencies.
- `environments/tf4dgs-win-64.explicit.txt`: resolved Conda package builds
  for this tested Windows CPU environment.
- `pyproject.toml`, `src/` and `scripts/TF4DGS.py`: the local project package;
  install it separately with the command below.
- Pinned pip dependency records where applicable; a Conda explicit file alone
  does not capture pip-installed packages.
- Installer version, download URL and checksum in the setup documentation.
- The native tool versions and checks already recorded in this guide.

Keep machine-specific absolute `prefix:` entries out of a shared YAML recipe.
Review exported dependencies: a history-only export is useful for portable
direct requirements, but pip dependencies must be checked separately.
Windows package locks require separate resolution/validation for Linux or WSL.
[Conda environment and export documentation](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html).

On a new machine with Conda available, create the named environment:

```powershell
conda env create --file environment.yml --no-default-packages
conda activate tf4dgs
python -m pip install -e . --no-deps --no-build-isolation
python -m unittest discover -s tests -v
```

Alternatively, replace the environment-create command with
`conda create -n tf4dgs --file environments/tf4dgs-win-64.explicit.txt` for the
exact tested Windows package builds. Package downloads are needed unless they
are already cached. The explicit file does not include the editable project
or native GUI tools. The first isolated GPU prototype is now documented below.

Use the developer-shell setup in Section 2 for the native LichtFeld build.
Activate `tf4dgs` for the project's capture and point-analysis tools.

If keeping the installer EXE locally, save it under `.local\downloads`, which
the root Git exclusions already cover. Commit the small environment
recipe, version records and lockfiles; keep installed environment directories
and package caches outside tracked files.

Conda environments can include native libraries and CUDA toolkit components.
Recreating an environment still requires a compatible NVIDIA driver and, for
this source-build workflow, the documented MSVC/native build setup. A YAML
file does not replace the full machine preparation in Sections 1-6.

## 11. Isolated dynamic Gaussian pilot (2026-10-07)

Keep the working `tf4dgs` CPU environment and LichtFeld static build. The first
real rigid-container prototype uses a separate **`tf4dgs-dynamic`** environment,
Python 3.10.22, torch 2.4.0+cu124 and the official precompiled
gsplat 1.5.3+pt24cu124 Windows wheel. Its packaged CUDA runtime does not replace
system CUDA 13.2.2. No compiler change or restart was needed on this machine.

The tested installation commands, wheel URL/checksum and portable locks are
in [DYNAMIC_BACKEND_NOTES.md](docs/DYNAMIC_BACKEND_NOTES.md). Actual renderer
forward/backward and real-model checks passed on the RTX A4000. This is a
provisional rigid Gaussian prototype; full textile deformation and temporal
Gaussian appearance are not yet implemented. See the
[real processing report](documentation/dynamic_capture_001/README.md) for
datasets, outputs, GUI previews, failures and remaining limits.

