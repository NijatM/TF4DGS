# Launch via Windows WMI, independently of VS Code's terminal process tree.
# No scheduled task, service, startup entry or automatic restart is created.
[CmdletBinding()]
param([ValidateSet('Configure','Build','Install','Validate')][string]$StartStage = 'Configure')
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$WorkerScript = Join-Path $PSScriptRoot 'Continue-StaticInstallation.ps1'
$ExistingWorkers = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" | Where-Object { $_.CommandLine -and $_.CommandLine.Contains($WorkerScript) })
if ($ExistingWorkers.Count -gt 0) {
    throw ('An installation worker already exists: ' + ($ExistingWorkers.ProcessId -join ', '))
}
$PowerShellExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$WorkerCommandLine = '"' + $PowerShellExe + '" -NoProfile -NonInteractive -WindowStyle Hidden -File "' + $WorkerScript + '" -StartStage ' + $StartStage
$WorkerStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{
    ShowWindow = [uint16]0
    CreateFlags = [uint32]16777216 # CREATE_BREAKAWAY_FROM_JOB
    PriorityClass = [uint32]16384 # Below Normal, to keep desktop work responsive.
}
$WorkerLaunch = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine = $WorkerCommandLine
    CurrentDirectory = $ProjectRoot
    ProcessStartupInformation = $WorkerStartup
}
if ($WorkerLaunch.ReturnValue -ne 0) { throw "Windows worker launch failed: $($WorkerLaunch.ReturnValue)" }
Write-Output "Started hidden installation worker $($WorkerLaunch.ProcessId), beginning at $StartStage."
Write-Output 'Follow installation-worker.json and .local\logs; check the live process as well as the saved status.'
