# Dot-source this file to restore TF4DGS's native build environment.
[CmdletBinding()]
param(
    [switch]$UseDriveAlias,
    [string]$VsRoot = 'C:\Program Files\Microsoft Visual Studio\18\Community',
    [string]$Toolset = '14.51',
    [string]$WindowsSdk = '10.0.26100.0',
    [string]$CudaRoot = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2'
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$RunRoot = $ProjectRoot
if ($UseDriveAlias) {
    $Mappings = @(& subst.exe)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect temporary drive mappings.' }
    if (Test-Path -LiteralPath 'R:\') {
        if ($Mappings -notcontains ('R:\: => ' + $ProjectRoot)) {
            throw 'R: belongs to another location. Do not replace it.'
        }
    } else {
        & subst.exe R: $ProjectRoot
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the project drive alias.' }
    }
    $RunRoot = 'R:\'
}
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
$GitBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd'
$CmakeBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin'
$NinjaBin = Join-Path $VsRoot 'Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja'
$VsInstallerBin = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer'
$env:Path = "$VsInstallerBin;$GitBin;$CmakeBin;$NinjaBin;" + $env:Path
Import-Module (Join-Path $VsRoot 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VsRoot -SkipAutomaticLocation -DevCmdArguments "-arch=x64 -host_arch=x64 -vcvars_ver=$Toolset -winsdk=$WindowsSdk"
if (-not $env:VCToolsVersion.StartsWith($Toolset + '.')) {
    throw "Unexpected compiler selection: $env:VCToolsVersion"
}
$Nvcc = Join-Path $CudaRoot 'bin\nvcc.exe'
$env:CUDA_PATH = $CudaRoot
$env:Path = (Join-Path $CudaRoot 'bin') + ";$GitBin;$CmakeBin;$NinjaBin;" + $env:Path
$env:VCPKG_VISUAL_STUDIO_PATH = $VsRoot
$VcpkgCache = Join-Path $LocalRoot 'cache\vcpkg'
New-Item -ItemType Directory -Path $VcpkgCache -Force | Out-Null
$env:VCPKG_DEFAULT_BINARY_CACHE = $VcpkgCache
$env:VCPKG_MAX_CONCURRENCY = '4'
$env:CMAKE_BUILD_PARALLEL_LEVEL = '4'
Set-Location -LiteralPath $RunRoot

function Invoke-CheckedNative {
    param([string]$FilePath, [string[]]$Arguments = @(), [string]$LogPath)
    if (-not (Get-Command $FilePath -ErrorAction SilentlyContinue)) { throw "Executable not found: $FilePath" }
    $PreviousPreference = $ErrorActionPreference
    try {
        # Windows PowerShell wraps native stderr as error records. Preserve
        # warnings while judging the program by its actual process exit code.
        $ErrorActionPreference = 'Continue'
        if ($LogPath) {
            & $FilePath @Arguments 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $LogPath -ErrorAction Stop
        } else {
            & $FilePath @Arguments 2>&1 | ForEach-Object { $_.ToString() }
        }
        $NativeExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $PreviousPreference
    }
    if ($NativeExitCode -ne 0) { throw "$FilePath failed with exit code $NativeExitCode. Log: $LogPath" }
}
