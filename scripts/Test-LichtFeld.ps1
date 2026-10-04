# Meaningful GPU training/checkpoint smoke check on a generated known-pose
# scene. Real reconstruction quality remains a separate capture-based test.
[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Initialize-BuildSession.ps1') -UseDriveAlias
$LichtFeld = Join-Path $Apps 'lichtfeld-v0.5.3\bin\LichtFeld-Studio.exe'
if (-not (Test-Path -LiteralPath $LichtFeld)) { throw 'Complete the LichtFeld Install stage first.' }
$BundledPython = Join-Path $Apps 'lichtfeld-v0.5.3\bin\python.exe'
Invoke-CheckedNative $BundledPython @('--version') (Join-Path $Logs 'lichtfeld-python-version.log')
$Fixture = Join-Path $Builds 'lichtfeld-smoke-dataset'
if (-not (Test-Path -LiteralPath (Join-Path $Fixture 'sparse\0\cameras.bin'))) {
    if (-not (Test-Path -LiteralPath $Fixture)) {
        Invoke-CheckedNative $BundledPython @((Join-Path $PSScriptRoot 'Create-SmokeDataset.py'),$Fixture) (Join-Path $Logs 'lichtfeld-fixture-create.log')
    }
    $Sparse = Join-Path $Fixture 'sparse\0'
    foreach ($TextModel in @('cameras.txt','images.txt','points3D.txt')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Sparse $TextModel))) {
            throw "Synthetic fixture is incomplete: $TextModel. Preserve it for inspection."
        }
    }
    $Colmap = Join-Path $Tools 'colmap-4.2.1\COLMAP.bat'
    Invoke-CheckedNative $Colmap @('model_converter','--input_path',$Sparse,'--output_path',$Sparse,'--output_type','BIN') (Join-Path $Logs 'lichtfeld-fixture-convert.log')
    Invoke-CheckedNative $Colmap @('model_analyzer','--path',$Sparse) (Join-Path $Logs 'lichtfeld-fixture-analyze.log')
}
$Output = Join-Path $Builds ('lichtfeld-smoke-training-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Output | Out-Null
$SmokeConfig = Join-Path $Output 'smoke-config.json'
$SmokeParameters = Get-Content -LiteralPath (Join-Path $Sources 'LichtFeld-Studio\eval\mcmc_optimization_params.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$SmokeParameters.iterations = 20
$SmokeParameters.save_steps = @(10)
$SmokeParameters.eval_steps = @()
$SmokeParameters | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $SmokeConfig -Encoding ASCII
Invoke-CheckedNative $LichtFeld @('--version') (Join-Path $Logs 'lichtfeld-version.log')
$PreviousSmokeOutput = $env:TF4DGS_SMOKE_OUTPUT
try {
    $env:TF4DGS_SMOKE_OUTPUT = $Output
    Invoke-CheckedNative $LichtFeld @('-d',$Fixture,'-o',$Output,'--config',$SmokeConfig,'--python-script',(Join-Path $PSScriptRoot 'Capture-SmokeCheckpoint.py'),'--headless','--iter','20','--max-cap','1000','--sh-degree','0','--resize_factor','1','--test-every','8') (Join-Path $Logs 'lichtfeld-training-smoke.log')
} finally {
    $env:TF4DGS_SMOKE_OUTPUT = $PreviousSmokeOutput
}
$Checkpoint = Join-Path $Output 'checkpoints\checkpoint.resume'
$IntermediateCheckpoint = Join-Path $Output 'checkpoints\intermediate_10.resume'
$Ply = Join-Path $Output 'splat_20.ply'
foreach ($Artifact in @($Checkpoint,$IntermediateCheckpoint,$Ply)) {
    if (-not (Test-Path -LiteralPath $Artifact) -or (Get-Item -LiteralPath $Artifact).Length -eq 0) {
        throw "Training output is missing/empty: $Artifact"
    }
}
$ResumedOutput = Join-Path $Output 'resumed'
$ResumeLog = Join-Path $Logs 'lichtfeld-resume-smoke.log'
# This release restores the checkpoint's saved iteration limit. Resume the
# genuine iteration-10 snapshot to its original target of 20 iterations.
Invoke-CheckedNative $LichtFeld @('--resume',$IntermediateCheckpoint,'-d',$Fixture,'-o',$ResumedOutput,'--headless','--resize_factor','1','--test-every','8') $ResumeLog
if (-not (Select-String -LiteralPath $ResumeLog -Pattern 'Restored training state from checkpoint at iteration 10' -Quiet)) {
    throw 'The expected intermediate training state was not restored.'
}
if (-not (Test-Path -LiteralPath (Join-Path $ResumedOutput 'splat_20.ply'))) { throw 'Checkpoint resume did not produce the expected PLY.' }
[ordered]@{
    project = 'TF4DGS'; checked_utc = [DateTime]::UtcNow.ToString('o');
    executable_path = $LichtFeld; fixture_path = $Fixture; output_path = $Output;
    cli_version_passed = $true; dataset_loading_passed = $true;
    bundled_python_startup_passed = $true;
    gpu_training_passed = $true; checkpoint_save_resume_passed = $true;
    ply_export_passed = $true; training_iterations = 20;
    python_training_callback_passed = $true; resume_start_iteration = 10;
    resumed_iterations = 20;
    viewer_startup_validation = 'pending';
    real_reconstruction_quality_validation = 'pending-user-footage'
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ProjectRoot 'lichtfeld-validation.json') -Encoding UTF8
Write-Output 'Synthetic dataset GPU training, checkpoint save/resume and PLY export passed.'
