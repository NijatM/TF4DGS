param([ValidateSet('4dgaussians','4c4d','base')][string]$Method='base',[switch]$Build)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$VsRoot='C:\Program Files\Microsoft Visual Studio\18\Community'
$VcVars=Join-Path $VsRoot 'VC\Auxiliary\Build\vcvarsall.bat'
if (-not (Test-Path -LiteralPath $VcVars)) { throw 'The required Visual Studio native build tools were not found.' }
Import-Module (Join-Path $VsRoot 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
Enter-VsDevShell -VsInstallPath $VsRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.44 -winsdk=10.0.26100.0'
if (-not $env:VCToolsVersion.StartsWith('14.44.')) { throw 'Unexpected compiler selection.' }
$env:CUDA_HOME='C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2'
$env:TORCH_CUDA_ARCH_LIST='8.6'
$env:MAX_JOBS='2'
$env:DISTUTILS_USE_SDK='1'
$env:MSSdk='1'
$Base=Join-Path $ProjectRoot '.local\envs\temporal-base'
$env:PATH=(Join-Path $Base 'Scripts')+';'+(Join-Path $env:CUDA_HOME 'bin')+';'+$env:PATH
$script:TemporalPython=if($Method -eq 'base'){Join-Path $Base 'python.exe'}else{Join-Path $ProjectRoot ('.local\envs\'+$Method+'\Scripts\python.exe')}
if($Build) {
    $LogRoot=Join-Path $ProjectRoot '.local\workflows\temporal_benchmark_001\build'
    New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
    $Packages=if($Method -eq 'base'){@('.local/research/4DGaussians/submodules/simple-knn')}elseif($Method -eq '4dgaussians'){@('.local/research/4DGaussians/submodules/depth-diff-gaussian-rasterization')}else{@('.local/research/4C4D/diff-gaussian-rasterization')}
    foreach($Package in $Packages) {
        $Log=Join-Path $LogRoot ($Method+'-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')+'.log')
        $PreviousPreference=$ErrorActionPreference
        try {
            $ErrorActionPreference='Continue'
            & $script:TemporalPython -m pip install (Join-Path $ProjectRoot $Package) --no-build-isolation --no-deps *>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $Log
            $NativeExit=$LASTEXITCODE
        } finally { $ErrorActionPreference=$PreviousPreference }
        if($NativeExit -ne 0){throw ('Native build failed. Preserved log: '+$Log)}
    }
}
