# Reproducible staged LichtFeld source setup/build. Restore the R: alias on
# every invocation, and resume the next unfinished stage after interruptions.
[CmdletBinding()]
param([ValidateSet('Prepare','Configure','Build','Install','All')][string]$Stage = 'All')
. (Join-Path $PSScriptRoot 'Initialize-BuildSession.ps1') -UseDriveAlias
. (Join-Path $PSScriptRoot 'Common-Install.ps1')
. (Join-Path $PSScriptRoot 'Get-ProjectSubmoduleCommit.ps1')
$LfsModulePath = '.local/src/LichtFeld-Studio'
$VcpkgModulePath = '.local/src/vcpkg'
$LfsCommit = Get-ProjectSubmoduleCommit -ProjectRoot $ProjectRoot -RelativePath $LfsModulePath
$VcpkgCommit = Get-ProjectSubmoduleCommit -ProjectRoot $ProjectRoot -RelativePath $VcpkgModulePath
$VcpkgBaseline = 'c3867e714dd3a51c272826eea77267876517ed99'
$LfsSource = Join-Path $Sources 'LichtFeld-Studio'
$VcpkgRoot = Join-Path $Sources 'vcpkg'
$LfsBuild = Join-Path $Builds 'lichtfeld-v0.5.3-release'
$LfsInstall = Join-Path $Apps 'lichtfeld-v0.5.3'
$env:VCPKG_ROOT = $VcpkgRoot
$RuntimePatch = Join-Path $ProjectRoot 'patches\lichtfeld-v0.5.3-cuda13-runtime-search.patch'
$RecordPath = Join-Path $ProjectRoot 'lichtfeld-installation.json'
$Record = [ordered]@{
    project = 'TF4DGS'; version = 'v0.5.3'; source_commit = $LfsCommit;
    vcpkg_tool_commit = $VcpkgCommit; vcpkg_manifest_baseline = $VcpkgBaseline;
    source_root = $LfsSource; build_root = $LfsBuild; installation_root = $LfsInstall;
    cuda_root = $CudaRoot; compiler_toolset = $env:VCToolsVersion;
    windows_sdk = $env:WindowsSDKVersion; stage = $Stage;
    source_patch = $RuntimePatch;
    source_patch_sha256 = (Get-FileHash -LiteralPath $RuntimePatch -Algorithm SHA256).Hash.ToLowerInvariant();
    state = 'starting'; updated_utc = [DateTime]::UtcNow.ToString('o')
}
function Save-LichtFeldRecord {
    $Record.updated_utc = [DateTime]::UtcNow.ToString('o')
    $Record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RecordPath -Encoding UTF8
}
function Assert-SourcePins {
    foreach ($Pin in @(@{path=$LfsSource;commit=$LfsCommit}, @{path=$VcpkgRoot;commit=$VcpkgCommit})) {
        $Head = (& git.exe -C $Pin.path rev-parse HEAD | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or $Head -ne $Pin.commit) { throw "Source revision mismatch: $($Pin.path)" }
    }
    $Manifest = Get-Content -LiteralPath (Join-Path $LfsSource 'vcpkg.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Manifest.'builtin-baseline' -ne $VcpkgBaseline) { throw 'LichtFeld dependency baseline changed.' }
}
function Apply-LichtFeldRuntimePatch {
    $SavedPatchPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & git.exe -C $LfsSource apply --reverse --check $RuntimePatch 2>&1 | Out-Null
        $PatchAlreadyApplied = $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $SavedPatchPreference
    }
    if ($PatchAlreadyApplied) {
        Write-Output 'CUDA 13 runtime DLL search patch is already applied.'
    } else {
        Invoke-CheckedNative 'git.exe' @('-C',$LfsSource,'apply','--check',$RuntimePatch)
        Invoke-CheckedNative 'git.exe' @('-C',$LfsSource,'apply',$RuntimePatch)
        Write-Output 'Applied the recorded CUDA 13 runtime DLL search patch.'
    }
}
Save-LichtFeldRecord
try {
    if ($Stage -in @('Prepare','All')) {
        # Refuse to replace a checkout containing unrecorded commits. Stage
        # intentional fork revisions in TF4DGS before building them.
        foreach ($ExistingPin in @(@{path=$LfsSource;commit=$LfsCommit}, @{path=$VcpkgRoot;commit=$VcpkgCommit})) {
            if (Test-Path -LiteralPath (Join-Path $ExistingPin.path '.git')) {
                $ExistingHead = (& git.exe -C $ExistingPin.path rev-parse HEAD | Out-String).Trim()
                if ($LASTEXITCODE -ne 0 -or $ExistingHead -ne $ExistingPin.commit) {
                    throw "Unrecorded source revision at $($ExistingPin.path). Stage the intended submodule reference in TF4DGS before running Prepare."
                }
            }
        }
        Invoke-CheckedNative 'git.exe' @('-C',$ProjectRoot,'-c','core.longpaths=true','submodule','update','--init','--recursive','--',$LfsModulePath,$VcpkgModulePath) (Join-Path $Logs 'source-submodules.log')
        Assert-SourcePins
        Invoke-CheckedNative (Join-Path $VcpkgRoot 'bootstrap-vcpkg.bat') @('-disableMetrics') (Join-Path $Logs 'vcpkg-bootstrap.log')
        $Record.state = 'prepared'
        Save-LichtFeldRecord
    }
    if ($Stage -in @('Configure','All')) {
        Assert-SourcePins
        Apply-LichtFeldRuntimePatch
        # vcpkg's x264 port uses a double-slash URL that returned an HTML bot
        # check. The canonical VideoLAN URL returns the exact pinned archive.
        Get-VerifiedProjectDownload -Algorithm SHA512 -ExpectedHash '707ff486677a1b5502d6d8faa588e7a03b0dee45491c5cba89341be4be23d3f2e48272c3b11d54cfc7be1b8bf4a3dfc3c3bb6d9643a6b5a2ed77539c85ecf294' -Uri 'https://code.videolan.org/videolan/x264/-/archive/31e19f92f00c7003fa115047ce50978bc98c3a0d/x264-31e19f92f00c7003fa115047ce50978bc98c3a0d.tar.gz' -Destination (Join-Path $VcpkgRoot 'downloads\videolan-x264-31e19f92f00c7003fa115047ce50978bc98c3a0d.tar.gz')
        $ConfigureArgs = @(
            '-S',$LfsSource, '-B',$LfsBuild, '-G','Ninja', '-DCMAKE_BUILD_TYPE=Release',
            "-DCMAKE_TOOLCHAIN_FILE=$VcpkgRoot/scripts/buildsystems/vcpkg.cmake",
            '-DVCPKG_TARGET_TRIPLET=x64-windows', '-DVCPKG_HOST_TRIPLET=x64-windows',
            "-DCUDAToolkit_ROOT=$CudaRoot", "-DCMAKE_CUDA_COMPILER=$Nvcc",
            '-DBUILD_PORTABLE=ON', '-DBUILD_CUDA_MIN_SM=86', '-DBUILD_TESTS=OFF',
            '-DBUILD_PYTHON_STUBS=OFF', '-DLFS_DEV_IMPORT_SOURCE_PYTHON=OFF',
            '-DLFS_DEV_IMPORT_SOURCE_RESOURCES=OFF', '-DCUDA_DEVICE_DEBUG=OFF',
            '-DLFS_FAST_COMPILE=OFF'
        )
        $Record.state = 'configuring'
        $Record.configure_arguments = $ConfigureArgs
        $Record.source_download_workaround = 'Prefetch canonical VideoLAN x264 URL with the original pinned SHA-512; source version unchanged.'
        Save-LichtFeldRecord
        Invoke-CheckedNative 'cmake.exe' $ConfigureArgs (Join-Path $Logs 'lichtfeld-configure.log')
        $Record.state = 'configured'
        Save-LichtFeldRecord
    }
    if ($Stage -in @('Build','All')) {
        Assert-SourcePins
        $Record.state = 'building'
        Save-LichtFeldRecord
        Invoke-CheckedNative 'cmake.exe' @('--build',$LfsBuild,'--parallel','4') (Join-Path $Logs 'lichtfeld-build.log')
        $Record.state = 'built'
        Save-LichtFeldRecord
    }
    if ($Stage -in @('Install','All')) {
        Assert-SourcePins
        $Record.state = 'installing'
        Save-LichtFeldRecord
        Invoke-CheckedNative 'cmake.exe' @('--install',$LfsBuild,'--prefix',$LfsInstall) (Join-Path $Logs 'lichtfeld-install.log')
        $LichtFeld = Join-Path $LfsInstall 'bin\LichtFeld-Studio.exe'
        if (-not (Test-Path -LiteralPath $LichtFeld)) { throw 'Installed LichtFeld executable is missing.' }
        Invoke-CheckedNative $LichtFeld @('--help') (Join-Path $Logs 'lichtfeld-help.log')
        $Record.state = 'installed-cli-verified'
        $Record.executable_path = $LichtFeld
        $Record.dataset_training_validation = 'pending-user-footage'
        Save-LichtFeldRecord
    }
} catch {
    $Record.state = 'failed'
    $Record.error = $_.Exception.Message
    Save-LichtFeldRecord
    throw
}
Write-Output "LichtFeld stage completed: $Stage"
