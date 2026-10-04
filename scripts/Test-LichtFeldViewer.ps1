# Verify installed Vulkan viewer/model startup with build tools removed from PATH.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$AppBin = Join-Path $ProjectRoot '.local\apps\lichtfeld-v0.5.3\bin'
$LichtFeld = Join-Path $AppBin 'LichtFeld-Studio.exe'
$ValidationPath = Join-Path $ProjectRoot 'lichtfeld-validation.json'
$Validation = Get-Content -LiteralPath $ValidationPath -Raw -Encoding UTF8 | ConvertFrom-Json
$TrainingOutput = $Validation.output_path
if ($TrainingOutput.StartsWith('R:\',[StringComparison]::OrdinalIgnoreCase)) {
    $TrainingOutput = Join-Path $ProjectRoot $TrainingOutput.Substring(3)
}
$Model = Join-Path $TrainingOutput 'splat_20.ply'
foreach ($RequiredFile in @($LichtFeld,$Model)) {
    if (-not (Test-Path -LiteralPath $RequiredFile)) { throw "Viewer check requires: $RequiredFile" }
}
$StdoutLog = Join-Path $ProjectRoot '.local\logs\lichtfeld-viewer-out.log'
$StderrLog = Join-Path $ProjectRoot '.local\logs\lichtfeld-viewer-err.log'
$SavedViewerEnvironment = @{}
foreach ($VariableName in @('PATH','CUDA_PATH','CUDA_HOME','PYTHONHOME','PYTHONPATH')) {
    $SavedViewerEnvironment[$VariableName] = [Environment]::GetEnvironmentVariable($VariableName,'Process')
}
$ViewerProcess = $null
try {
    $env:PATH = "$AppBin;$env:SystemRoot\System32;$env:SystemRoot"
    foreach ($VariableName in @('CUDA_PATH','CUDA_HOME','PYTHONHOME','PYTHONPATH')) {
        [Environment]::SetEnvironmentVariable($VariableName,$null,'Process')
    }
    $ViewerProcess = Start-Process -FilePath $LichtFeld -ArgumentList @('-v',('"' + $Model + '"')) -WorkingDirectory $AppBin -WindowStyle Hidden -RedirectStandardOutput $StdoutLog -RedirectStandardError $StderrLog -PassThru
    $StartupDeadline = [DateTime]::UtcNow.AddMinutes(3)
    $ViewerReady = $false
    do {
        Start-Sleep -Seconds 2
        $ViewerProcess.Refresh()
        if ($ViewerProcess.HasExited) { throw "Viewer exited during startup: $($ViewerProcess.ExitCode). Inspect $StderrLog and $StdoutLog" }
        $ViewerText = (Get-Content -LiteralPath $StdoutLog -Raw -ErrorAction SilentlyContinue) + (Get-Content -LiteralPath $StderrLog -Raw -ErrorAction SilentlyContinue)
        $ViewerReady = $ViewerText -match 'Vulkan device:\s+NVIDIA' -and
            $ViewerText -match 'Vulkan external memory interop enabled' -and
            $ViewerText -match 'Vulkan external timeline semaphore interop enabled' -and
            $ViewerText -match "Loaded '.+' with [1-9][0-9]* gaussians"
    } until ($ViewerReady -or [DateTime]::UtcNow -ge $StartupDeadline)
    if (-not $ViewerReady) { throw 'Viewer startup/model-loading evidence was not found before the timeout.' }
    Start-Sleep -Seconds 5
    $ViewerProcess.Refresh()
    if ($ViewerProcess.HasExited) { throw 'Viewer exited just after loading the test model.' }
    $Validation.viewer_startup_validation = 'passed'
    $Validation | Add-Member -NotePropertyName viewer_cuda_vulkan_interop_passed -NotePropertyValue $true -Force
    $Validation | Add-Member -NotePropertyName viewer_model_loading_passed -NotePropertyValue $true -Force
    $Validation | Add-Member -NotePropertyName viewer_isolated_path_passed -NotePropertyValue $true -Force
    $Validation | Add-Member -NotePropertyName viewer_checked_utc -NotePropertyValue ([DateTime]::UtcNow.ToString('o')) -Force
    $Validation | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ValidationPath -Encoding UTF8
    Write-Output 'Installed Vulkan viewer, CUDA interop and exported-model loading passed with an isolated tool PATH.'
} finally {
    foreach ($VariableName in $SavedViewerEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($VariableName,$SavedViewerEnvironment[$VariableName],'Process')
    }
    if ($ViewerProcess -and -not $ViewerProcess.HasExited) {
        if (-not $ViewerProcess.CloseMainWindow() -or -not $ViewerProcess.WaitForExit(5000)) {
            Stop-Process -Id $ViewerProcess.Id -ErrorAction SilentlyContinue
        }
    }
}
