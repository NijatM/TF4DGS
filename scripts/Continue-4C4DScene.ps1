param([ValidateSet('yogurt','textile')][string[]]$Datasets=@('textile','yogurt'))
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
$Selection=Get-Content -LiteralPath 'documentation/4c4d_scene_001/selection.json' -Raw | ConvertFrom-Json
foreach($Dataset in $Datasets){
    $Choice=$Selection.datasets.$Dataset
    if(-not $Choice -or -not $Choice.continuation_attempt){throw "No reviewed continuation settings for $Dataset"}
    $Attempt=$Choice.continuation_attempt
    $Metric="documentation/4c4d_scene_001/${Dataset}_${Attempt}_step_030000_metrics.json"
    if(Test-Path -LiteralPath $Metric){Write-Host "Existing 30k evidence preserved: $Dataset / $Attempt";continue}
    if(-not (Test-Path -LiteralPath "outputs/4c4d_scene_001/$Dataset/$Attempt/checkpoint.pth")){throw 'Selected checkpoint is missing.'}
    & scripts/Run-4C4DScene.ps1 -Dataset $Dataset -Attempt $Attempt -Preset $Choice.preset -Stop 30000 -Resume
}
exit 0
