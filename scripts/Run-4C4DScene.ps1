param(
    [ValidateSet('yogurt','textile')][string]$Dataset,
    [Parameter(Mandatory=$true)][string]$Attempt,
    [int]$Edge=1280,
    [int]$Stop=30000,
    [ValidateSet('baseline','slow_motion','gentle_decay','fast_time')][string]$Preset='baseline',
    [string]$Parent,
    [switch]$Resume,
    [switch]$Refine,
    [switch]$FitAll
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Root
$Docs='documentation/4c4d_scene_001'
$Python=Join-Path $Root '.local/envs/4c4d/Scripts/python.exe'
$DocPython=Join-Path $Root '.local/envs/temporal-base/python.exe'
$Tag="${Dataset}_${Attempt}"
$RunArgs=@('-u','scripts/Train-4C4DScene.py','--dataset',$Dataset,'--attempt',$Attempt,'--edge',"$Edge",'--preset',$Preset,'--stop',"$Stop")
if($Parent){$RunArgs+=@('--parent',$Parent)}
if($Resume){$RunArgs+='--resume'}
if($Refine){$RunArgs+='--refine'}
if($FitAll){$RunArgs+='--fit-all'}
& $DocPython scripts/Temporal-BenchmarkReport.py --docs $Docs --title "$Tag started" --status training --detail "Full camera frames at edge $Edge. One joint model including hands/subject/visible surroundings. Preset $Preset, stop $Stop, parent $Parent, resolution-refinement $Refine, production fit of all recorded frames $FitAll. Checkpoints, RNG and input provenance are preserved."
$Log=".local/workflows/4c4d_scene_001/${Tag}_$([DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')).log"
$OldPreference=$ErrorActionPreference
try{
    $ErrorActionPreference='Continue'
    & $Python @RunArgs *>&1 | ForEach-Object{$_.ToString()} | Tee-Object -FilePath $Log
    $Exit=$LASTEXITCODE
}finally{$ErrorActionPreference=$OldPreference}
if($Exit -ne 0){
    & $DocPython scripts/Temporal-BenchmarkReport.py --docs $Docs --title "$Tag failed" --status 'failed; checkpoints retained' --detail "Training returned $Exit. Full log: $Log. Earlier successful runs are preserved; no restart or silent overwrite."
    try{& scripts/Capture-LocalPreview.ps1 -Url 'http://127.0.0.1:8109/' -DebugPort 8099 -OutputFile "$Docs/${Tag}_failed.png" -Reload}catch{Write-Warning $_.Exception.Message}
    throw "$Tag failed; inspect saved log before continuing."
}
$Metric=Get-Content "$Docs/${Tag}_step_$($Stop.ToString('000000'))_metrics.json" -Raw | ConvertFrom-Json
& $DocPython scripts/Build-4C4DSceneReport.py
$Role=if($FitAll){'fitted-reference'}else{'validation'}
& $DocPython scripts/Temporal-BenchmarkReport.py --docs $Docs --title "$Tag completed $Stop updates" --status 'trained; visual review pending' --detail ("Full-frame $Role PSNR $([Math]::Round($Metric.validation_psnr_db,2)) dB; motion-region PSNR $([Math]::Round($Metric.motion_region_psnr_db,2)) dB; SSIM at edge1280 $([Math]::Round($Metric.validation_ssim_at_1280,3)). $($Metric.point_count) Gaussians, peak allocated $([Math]::Round($Metric.peak_cuda_allocated_gib,2)) GiB. Whole-frame scores do not certify new-view geometry or material correspondence. Production scores use fitted images, not held-out tests.") --images "${Tag}_step_$($Stop.ToString('000000'))_preview.png" "${Tag}_step_$($Stop.ToString('000000'))_orbit.png"
try{
    & scripts/Capture-LocalPreview.ps1 -Url 'http://127.0.0.1:8109/' -DebugPort 8099 -OutputFile "$Docs/${Tag}_step_$($Stop.ToString('000000'))_completed.png" -Reload
    & scripts/Capture-LocalPreview.ps1 -Url 'http://127.0.0.1:8109/' -DebugPort 8098 -OutputFile "$Docs/${Tag}_step_$($Stop.ToString('000000'))_completed_visible.png" -Reload
}catch{
    Write-Warning $_.Exception.Message
    & $DocPython scripts/Temporal-BenchmarkReport.py --docs $Docs --title "$Tag documentation screenshot failed" --status 'documentation failure; model retained' --detail $_.Exception.Message
}
