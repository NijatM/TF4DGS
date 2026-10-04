# Temporal Fields 4D Gaussian Splatting (TF4DGS)
# Run after downloading the pinned NVIDIA full installer. This script requests
# Windows elevation for the verified installer, not for the subsequent build.
[CmdletBinding()]
param([string]$InstallerPath)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogRoot = Join-Path $ProjectRoot '.local\logs'
$CudaRoot = Join-Path $env:ProgramFiles 'NVIDIA GPU Computing Toolkit\CUDA\v13.2'
$NvccPath = Join-Path $CudaRoot 'bin\nvcc.exe'
$RecordPath = Join-Path $LogRoot 'cuda-installation.json'
if (-not $InstallerPath) {
    $InstallerPath = Join-Path $ProjectRoot '.local\downloads\cuda_13.2.2_windows.exe'
}
$InstallerPath = [System.IO.Path]::GetFullPath($InstallerPath)
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null

# Full toolkit compiler, development/runtime libraries and diagnostic tools.
# Omit optional Nsight packages, VS integration and all display-driver packages.
$Components = @(
    'crt_13.2', 'nvcc_13.2', 'nvvm_13.2', 'thrust_13.2', 'cudart_13.2',
    'cublas_13.2', 'cublas_dev_13.2', 'cufft_13.2', 'cufft_dev_13.2',
    'curand_13.2', 'curand_dev_13.2', 'cusolver_13.2', 'cusolver_dev_13.2',
    'cusparse_13.2', 'cusparse_dev_13.2', 'npp_13.2', 'npp_dev_13.2',
    'nvjpeg_13.2', 'nvjpeg_dev_13.2', 'nvrtc_13.2', 'nvrtc_dev_13.2',
    'nvjitlink_13.2', 'nvfatbin_13.2', 'nvptxcompiler_13.2',
    'nvml_dev_13.2', 'cuda_profiler_api_13.2', 'cupti_13.2', 'nvtx_13.2',
    'cuobjdump_13.2', 'nvdisasm_13.2', 'nvprune_13.2', 'cuxxfilt_13.2',
    'sanitizer_13.2'
)

if (Test-Path -LiteralPath $NvccPath) {
    throw "CUDA already exists at $CudaRoot. Verify/resume that installation before rerunning an installer."
}
if (-not (Test-Path -LiteralPath $InstallerPath -PathType Leaf)) {
    throw "Download the official CUDA 13.2.2 installer first: $InstallerPath"
}
if ((Get-Item -LiteralPath $InstallerPath).Length -ne 2499003640) {
    throw 'CUDA installer size differs from the official NVIDIA metadata.'
}
$Md5 = (Get-FileHash -LiteralPath $InstallerPath -Algorithm MD5).Hash.ToLowerInvariant()
if ($Md5 -ne '9e4bcad21f296561fa834a4eeda079d2') {
    throw 'CUDA installer checksum does not match the official NVIDIA checksum.'
}
$Signature = Get-AuthenticodeSignature -LiteralPath $InstallerPath
if ($Signature.Status -ne 'Valid' -or $Signature.SignerCertificate.Subject -notmatch 'NVIDIA Corporation') {
    throw 'CUDA installer must have a valid NVIDIA publisher signature.'
}
$Sha256 = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()
$SessionManagerKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager'
$PendingBefore = (Get-ItemProperty -LiteralPath $SessionManagerKey -Name PendingFileRenameOperations -ErrorAction SilentlyContinue).PendingFileRenameOperations
$InstallerArguments = (@('-s', '-n') + $Components + @('-log:' + $LogRoot, '-loglevel:6')) -join ' '
$Record = [ordered]@{
    project = 'TF4DGS'
    toolkit_version = '13.2.2'
    expected_nvcc_build = '13.2.86'
    installer_path = $InstallerPath
    installer_url = 'https://developer.download.nvidia.com/compute/cuda/13.2.2/local_installers/cuda_13.2.2_windows.exe'
    installer_md5 = $Md5
    installer_sha256 = $Sha256
    installer_signature = [string]$Signature.Status
    installer_publisher = $Signature.SignerCertificate.Subject
    installation_root = $CudaRoot
    components = $Components
    installer_arguments = $InstallerArguments
    automatic_reboot_suppressed = $true
    pending_file_entries_before = @($PendingBefore).Count
    state = 'awaiting-uac'
    started_utc = [DateTime]::UtcNow.ToString('o')
}
function Save-Record {
    $Record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $RecordPath -Encoding UTF8
}
Save-Record
Write-Output 'Verified NVIDIA installer. Windows may now ask for administrator consent.'
try {
    $InstallerProcess = Start-Process -FilePath $InstallerPath -ArgumentList $InstallerArguments -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    $Record.installer_exit_code = $InstallerProcess.ExitCode
    $Record.finished_utc = [DateTime]::UtcNow.ToString('o')
    $PendingAfter = (Get-ItemProperty -LiteralPath $SessionManagerKey -Name PendingFileRenameOperations -ErrorAction SilentlyContinue).PendingFileRenameOperations
    $Record.pending_file_entries_after = @($PendingAfter).Count
    $Record.nvcc_present = Test-Path -LiteralPath $NvccPath
    if ($InstallerProcess.ExitCode -in @(3010, 1641)) {
        $Record.state = 'installer-requires-restart'
        Save-Record
        Write-Output "Installer requested a restart (exit $($InstallerProcess.ExitCode)). Save the project checkpoint before restarting."
        exit 3010
    }
    if ($InstallerProcess.ExitCode -ne 0) {
        $Record.state = 'installer-result-needs-inspection'
        Save-Record
        throw "CUDA installer returned $($InstallerProcess.ExitCode). Inspect NVIDIA logs and installed components before proceeding."
    }
    if (-not $Record.nvcc_present) { throw 'Installer returned success, but nvcc was not found.' }
    $VersionOutput = (& $NvccPath --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $VersionOutput -notmatch 'V13\.2\.86') {
        throw "CUDA compiler version does not match the selected pin: $VersionOutput"
    }
    $Record.nvcc_version_output = $VersionOutput
    $Record.state = 'installed-awaiting-gpu-checks'
    Save-Record
    Write-Output $VersionOutput
    Write-Output "Installer exit code: 0. Record: $RecordPath"
} catch {
    $Record.error = $_.Exception.Message
    if ($Record.state -eq 'awaiting-uac') { $Record.state = 'installer-launch-failed' }
    elseif ($Record.state -ne 'installer-result-needs-inspection') { $Record.state = 'verification-failed' }
    Save-Record
    throw
}
