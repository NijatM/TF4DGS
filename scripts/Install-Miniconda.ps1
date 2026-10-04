#requires -Version 5.1
# Temporal Fields 4D Gaussian Splatting (TF4DGS): Miniconda manager setup.
[CmdletBinding()]
param(
    [string]$InstallRoot = (Join-Path $env:USERPROFILE 'miniconda3')
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DownloadRoot = Join-Path $ProjectRoot '.local\downloads'
$LogRoot = Join-Path $ProjectRoot '.local\logs'
$InstallerName = 'Miniconda3-py314_26.7.1-1-Windows-x86_64.exe'
$InstallerUrl = 'https://repo.anaconda.com/miniconda/' + $InstallerName
$ExpectedSha256 = '27f1f8ae8c27bc22bbc383b84bf08c63a20a6e190f3975f3502625b1045330b2'
$InstallerPath = Join-Path $DownloadRoot $InstallerName
$ResolvedInstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)
$CondaExe = Join-Path $ResolvedInstallRoot 'Scripts\conda.exe'
$PythonExe = Join-Path $ResolvedInstallRoot 'python.exe'

if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'This installer script requires 64-bit Windows.'
}
if ($ResolvedInstallRoot -match '\s') {
    throw 'Choose a Miniconda installation path without spaces.'
}
if (Test-Path -LiteralPath $ResolvedInstallRoot) {
    throw "Installation target already exists: $ResolvedInstallRoot. Verify it before making changes."
}

foreach ($Folder in @($DownloadRoot, $LogRoot)) {
    New-Item -ItemType Directory -Path $Folder -Force | Out-Null
}

Write-Output "Installer: $InstallerUrl"
if (-not (Test-Path -LiteralPath $InstallerPath)) {
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $InstallerPath -UseBasicParsing
}
$ActualSha256 = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
if ($ActualSha256 -ne $ExpectedSha256) {
    throw "Installer checksum mismatch. Do not run $InstallerPath."
}

$Signature = Get-AuthenticodeSignature -LiteralPath $InstallerPath
Write-Output "SHA-256 verified: $ActualSha256"
Write-Output "Signature status: $($Signature.Status)"
if ($Signature.Status -ne 'Valid') {
    throw 'Installer signature could not be validated. Installation has not started.'
}
if ($Signature.SignerCertificate.Subject -notmatch 'Anaconda') {
    throw 'Installer publisher differs from Anaconda. Installation has not started.'
}
Write-Output "Publisher: $($Signature.SignerCertificate.Subject)"

$InstallerArgs = @(
    '/S'
    '/InstallationType=JustMe'
    '/AddToPath=0'
    '/RegisterPython=0'
    "/D=$ResolvedInstallRoot"
)
Write-Output "Installing for this user at $ResolvedInstallRoot"
$InstallerProcess = Start-Process -FilePath $InstallerPath -ArgumentList $InstallerArgs -WindowStyle Hidden -Wait -PassThru
$ExitRecord = Join-Path $LogRoot 'miniconda-installer-exit.txt'
"Installer exit code: $($InstallerProcess.ExitCode)" |
    Set-Content -LiteralPath $ExitRecord -Encoding ASCII

if ($InstallerProcess.ExitCode -eq 3010) {
    throw 'Installer reports a required restart (3010). Save the project checkpoint before restarting.'
}
if ($InstallerProcess.ExitCode -ne 0) {
    throw "Miniconda installer failed with exit code $($InstallerProcess.ExitCode). Preserve the target and inspect it."
}
if (-not (Test-Path -LiteralPath $CondaExe) -or -not (Test-Path -LiteralPath $PythonExe)) {
    throw 'Installer exited successfully, but expected Conda/Python executables are missing.'
}

$CondaVersion = (& $CondaExe --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Conda version check failed.' }
$PythonVersion = (& $PythonExe --version | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
$CondaBase = (& $CondaExe info --base | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Conda base-path check failed.' }
$ResolvedCondaBase = [System.IO.Path]::GetFullPath($CondaBase)
if ($ResolvedCondaBase.TrimEnd([char]'\') -ne $ResolvedInstallRoot.TrimEnd([char]'\')) {
    throw "Conda returned an unexpected base directory: $CondaBase"
}
& $CondaExe list | Out-File -LiteralPath (Join-Path $LogRoot 'miniconda-base-packages.txt') -Encoding UTF8
if ($LASTEXITCODE -ne 0) { throw 'Conda package-list check failed.' }

$Record = [ordered]@{
    project_full_name = 'Temporal Fields 4D Gaussian Splatting'
    project_short_name = 'TF4DGS'
    project_environment_name = 'tf4dgs'
    installer = $InstallerName
    installer_url = $InstallerUrl
    installer_sha256 = $ActualSha256.ToLowerInvariant()
    installer_publisher = $Signature.SignerCertificate.Subject
    installer_exit_code = $InstallerProcess.ExitCode
    installation_type = 'JustMe'
    installation_root = $ResolvedInstallRoot
    conda_version = $CondaVersion
    base_python_version = $PythonVersion
    path_modified_by_installer = $false
    registered_as_default_python = $false
    shell_initialization_requested = $false
    research_environment_created = $false
}
$Record | ConvertTo-Json |
    Set-Content -LiteralPath (Join-Path $ProjectRoot 'conda-installation.json') -Encoding UTF8
Write-Output $CondaVersion
Write-Output $PythonVersion
Write-Output "Verified Conda base: $CondaBase"
Write-Output 'Installation complete. Research environment dependencies are selected separately.'

