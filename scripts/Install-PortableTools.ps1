# Download, verify and install COLMAP/FFmpeg locally; no system installer.
[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Initialize-BuildSession.ps1')
. (Join-Path $PSScriptRoot 'Common-Install.ps1')
$Specifications = @(
    @{
        name = 'COLMAP'; version = '4.2.1'; folder = 'colmap-4.2.1';
        archive = 'colmap-4.2.1-x64-windows-cuda.zip';
        uri = 'https://github.com/colmap/colmap/releases/download/4.2.1/colmap-x64-windows-cuda.zip';
        sha256 = 'e9c5cbd84c2ea986d2e970a2473fc2d2e6b34a2cdcf5d3df2765c319a63af881';
        launcher = 'COLMAP.bat'; arguments = @('-h')
    },
    @{
        name = 'FFmpeg'; version = '9.0.2'; folder = 'ffmpeg-9.0.2';
        archive = 'ffmpeg-9.0.2-essentials_build.zip';
        uri = 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip';
        sha256 = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba';
        launcher = 'ffmpeg.exe'; arguments = @('-version')
    }
)
$Results = @()
foreach ($Specification in $Specifications) {
    $Archive = Join-Path $Downloads $Specification.archive
    $Destination = Join-Path $Tools $Specification.folder
    Get-VerifiedProjectDownload -Uri $Specification.uri -Destination $Archive -Sha256 $Specification.sha256
    if (-not (Test-Path -LiteralPath $Destination)) {
        $Extracting = $Destination + '.extracting'
        if (Test-Path -LiteralPath $Extracting) { throw "Interrupted extraction exists; inspect before resuming: $Extracting" }
        Expand-Archive -LiteralPath $Archive -DestinationPath $Extracting
        Rename-Item -LiteralPath $Extracting -NewName $Specification.folder
    }
    $Candidates = @(Get-ChildItem -LiteralPath $Destination -File -Recurse -Filter $Specification.launcher)
    if ($Candidates.Count -ne 1) { throw "Expected one $($Specification.launcher) under $Destination" }
    $Launcher = $Candidates[0].FullName
    Invoke-CheckedNative $Launcher $Specification.arguments (Join-Path $Logs ($Specification.folder + '-version.log'))
    $Result = [ordered]@{
        name = $Specification.name; version = $Specification.version;
        download_url = $Specification.uri; archive_sha256 = $Specification.sha256;
        installation_root = $Destination; executable_path = $Launcher;
        checked_utc = [DateTime]::UtcNow.ToString('o'); cli_check_passed = $true
    }
    if ($Specification.name -eq 'FFmpeg') {
        $Ffprobe = Join-Path (Split-Path -Parent $Launcher) 'ffprobe.exe'
        Invoke-CheckedNative $Ffprobe @('-version') (Join-Path $Logs 'ffprobe-version.log')
        $Result.ffprobe_path = $Ffprobe
    }
    $Results += [pscustomobject]$Result
    [ordered]@{ project = 'TF4DGS'; portable_tools = $Results } | ConvertTo-Json -Depth 8 |
        Set-Content -LiteralPath (Join-Path $ProjectRoot 'static-tools.json') -Encoding UTF8
}
Write-Output 'COLMAP and FFmpeg installation and command-line checks passed.'
