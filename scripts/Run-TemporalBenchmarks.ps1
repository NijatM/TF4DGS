param([switch]$SmokeOnly,[string]$Attempt='pilot_01',[string[]]$Methods=@('4dgaussians','4c4d'),[string[]]$Datasets=@('yogurt','textile'),[int]$CaptureDebugPort=8099)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$Config=Get-Content -LiteralPath 'configs/temporal_benchmark_001.json' -Raw | ConvertFrom-Json
$Updates=if($SmokeOnly){625}else{$Config.training.total_image_updates}
$DocsPython=Join-Path $ProjectRoot '.local\envs\temporal-base\python.exe'
$LogRoot=Join-Path $ProjectRoot '.local\workflows\temporal_benchmark_001'
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$env:PYTHONHASHSEED='42'
foreach($Dataset in $Datasets) {
    foreach($Method in $Methods) {
        $Python=Join-Path $ProjectRoot ('.local\envs\'+$Method+'\Scripts\python.exe')
        $Coarse=if($Method -eq '4dgaussians'){if($SmokeOnly){125}else{$Config.training.'4dgaussians_coarse_updates'}}else{0}
        $Tag=$Method+'_'+$Dataset+'_'+$Attempt
        & $DocsPython 'scripts/Temporal-BenchmarkReport.py' --title ($Tag+' started') --detail ("$Updates image updates; batch size 1; pinned action interval, common seed/cameras/losses, held-out timestamps and a 180000-point cap. Live progress appears at http://127.0.0.1:8108/.") --status 'training'
        $PreviousPreference=$ErrorActionPreference
        try {
            $ErrorActionPreference='Continue'
            & $Python -u 'scripts/Train-TemporalBenchmark.py' --method $Method --dataset $Dataset --updates $Updates --coarse $Coarse --attempt $Attempt *>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath (Join-Path $LogRoot ($Tag+'.log'))
            $NativeExit=$LASTEXITCODE
        } finally { $ErrorActionPreference=$PreviousPreference }
        if($NativeExit -ne 0) {
            & $DocsPython 'scripts/Temporal-BenchmarkReport.py' --title ($Tag+' failed') --status 'failed' --detail ('Training exited with code '+$NativeExit+'. Complete log retained at .local/workflows/temporal_benchmark_001/'+$Tag+'.log. Earlier outputs and checkpoints are retained.')
            try { & (Join-Path $PSScriptRoot 'Capture-LocalPreview.ps1') -DebugPort $CaptureDebugPort -Url 'http://127.0.0.1:8108/' -OutputFile ('documentation/temporal_benchmark_001/'+$Tag+'_failed.png') -Reload } catch { Write-Warning $_.Exception.Message }
            throw ($Tag+' failed; do not silently skip this benchmark.')
        }
        $Metric=Get-Content -LiteralPath ('documentation/temporal_benchmark_001/'+$Tag+'_metrics.json') -Raw | ConvertFrom-Json
        $Detail=('Completed '+$Updates+' updates in '+[Math]::Round($Metric.elapsed_s,1)+' seconds; '+$Metric.point_count+' Gaussians; peak allocated GPU memory '+[Math]::Round($Metric.peak_cuda_allocated_gib,2)+' GiB. Held-out timestamp image PSNR '+[Math]::Round($Metric.heldout_psnr_db,2)+' dB, full-crop SSIM '+[Math]::Round($Metric.heldout_ssim,3)+'. These photometric metrics do not establish novel-view geometry or material-point accuracy.')
        & $DocsPython 'scripts/Temporal-BenchmarkReport.py' --title ($Tag+' completed') --status 'trained; awaiting visual review' --detail $Detail --images ($Tag+'_iphone_heldout.png') ($Tag+'_fuji_heldout.png') ($Tag+'_dji_heldout.png')
        try {
            & (Join-Path $PSScriptRoot 'Capture-LocalPreview.ps1') -DebugPort $CaptureDebugPort -Url 'http://127.0.0.1:8108/' -OutputFile ('documentation/temporal_benchmark_001/'+$Tag+'_completed.png') -Reload
        } catch {
            & $DocsPython 'scripts/Temporal-BenchmarkReport.py' --title ($Tag+' screenshot attempt failed') --status 'capture failed; training retained' --detail ($_.Exception.Message+' The successful model and metrics are retained. Screenshot capture will be retried independently.')
        }
    }
}
