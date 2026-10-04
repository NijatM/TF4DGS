# Continue the approved static setup in a standalone hidden Windows worker.
# A file lock prevents duplicate workers; stages stop on the first failure.
[CmdletBinding()]
param([ValidateSet('Configure','Build','Install','Validate')][string]$StartStage = 'Configure')
$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$WorkerLogs = Join-Path $ProjectRoot '.local\logs'
New-Item -ItemType Directory -Path $WorkerLogs -Force | Out-Null
$WorkerLock = [IO.File]::Open((Join-Path $WorkerLogs 'static-installation.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$WorkerRecordPath = Join-Path $ProjectRoot 'installation-worker.json'
$WorkerRunId = [Guid]::NewGuid().ToString('N')
$WorkerTranscript = Join-Path $WorkerLogs ('static-installation-worker-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '.log')
$WorkerRecord = [ordered]@{
    project = 'TF4DGS'; run_id = $WorkerRunId; process_id = $PID;
    started_utc = [DateTime]::UtcNow.ToString('o'); updated_utc = $null;
    state = 'starting'; stage = $StartStage; last_completed_stage = $null;
    transcript_path = $WorkerTranscript; automatic_restart = $false
}
function Save-WorkerState {
    $WorkerRecord.updated_utc = [DateTime]::UtcNow.ToString('o')
    $WorkerRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $WorkerRecordPath -Encoding UTF8
}
function Add-WorkerCheckpoint([string]$Message) {
    Add-Content -LiteralPath (Join-Path $ProjectRoot 'PROJECT_MEMORY.md') -Encoding UTF8 -Value ("`r`n- Static worker " + [DateTime]::UtcNow.ToString('yyyy-MM-dd HH:mm:ss') + ' UTC: ' + $Message)
}
$TranscriptStarted = $false
try {
    Start-Transcript -LiteralPath $WorkerTranscript -Force | Out-Null
    $TranscriptStarted = $true
    Save-WorkerState
    $WorkerStages = @('Configure','Build','Install','Validate')
    $FirstWorkerStage = [Array]::IndexOf($WorkerStages,$StartStage)
    for ($WorkerStageIndex = $FirstWorkerStage; $WorkerStageIndex -lt $WorkerStages.Count; $WorkerStageIndex++) {
        $WorkerStage = $WorkerStages[$WorkerStageIndex]
        $WorkerRecord.stage = $WorkerStage
        $WorkerRecord.state = 'running'
        Save-WorkerState
        Add-WorkerCheckpoint "Starting $WorkerStage; run $WorkerRunId, process $PID."
        if ($WorkerStage -eq 'Validate') {
            & (Join-Path $PSScriptRoot 'Test-LichtFeld.ps1')
        } else {
            & (Join-Path $PSScriptRoot 'Install-LichtFeld.ps1') -Stage $WorkerStage
        }
        $WorkerRecord.last_completed_stage = $WorkerStage
        Save-WorkerState
        Add-WorkerCheckpoint "Completed $WorkerStage."
    }
    $WorkerRecord.state = 'completed'
    Save-WorkerState
    Add-WorkerCheckpoint 'Configure, build, install and synthetic training checks completed; interactive viewer validation remains separate.'
} catch {
    $WorkerRecord.state = 'failed'
    $WorkerRecord.error = $_.Exception.Message
    Save-WorkerState
    Add-WorkerCheckpoint ("Failed at $($WorkerRecord.stage): " + $_.Exception.Message + '. Inspect the transcript and stage log before resuming.')
    throw
} finally {
    if ($TranscriptStarted) { Stop-Transcript | Out-Null }
    $WorkerLock.Dispose()
}
