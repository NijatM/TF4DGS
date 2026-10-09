param(
    [ValidateSet('yogurt','textile')][string[]]$Datasets=@('textile','yogurt')
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
foreach($Dataset in $Datasets){
    $Parent="outputs/4c4d_scene_001/$Dataset/baseline_01/checkpoint_010000.pth"
    if(-not (Test-Path -LiteralPath $Parent)){throw "Missing matched parent: $Parent"}
    if(-not (Test-Path -LiteralPath "documentation/4c4d_scene_001/${Dataset}_baseline_01_step_012000_metrics.json")){
        throw "Finish the baseline comparison endpoint before tuning $Dataset."
    }
    foreach($Preset in @('slow_motion','gentle_decay')){
        $Attempt="${Preset}_01"
        $Checkpoint="outputs/4c4d_scene_001/$Dataset/$Attempt/checkpoint.pth"
        $Metrics="documentation/4c4d_scene_001/${Dataset}_${Attempt}_step_012000_metrics.json"
        if(Test-Path -LiteralPath $Metrics){Write-Host "Existing completed tuning evidence preserved: $Dataset / $Attempt";continue}
        if(Test-Path -LiteralPath $Checkpoint){
            & scripts/Run-4C4DScene.ps1 -Dataset $Dataset -Attempt $Attempt -Preset $Preset -Stop 12000 -Resume
        }else{
            & scripts/Run-4C4DScene.ps1 -Dataset $Dataset -Attempt $Attempt -Preset $Preset -Stop 12000 -Parent $Parent
        }
    }
}
exit 0
