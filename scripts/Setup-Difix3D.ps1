param(
    [string]$BasePython = "$env:USERPROFILE\miniconda3\envs\tf4dgs-dynamic\python.exe"
)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$SourceDirectory=Join-Path $ProjectRoot '.local\src\Difix3D'
$ExpectedCommit='c76edc595586e16732c91ddee82f3a6d83a8a9cc'
if (-not (Test-Path -LiteralPath $BasePython)) { throw 'Install the documented tf4dgs-dynamic renderer environment first, or supply -BasePython.' }
& $BasePython -c "import torch,gsplat; assert torch.__version__=='2.4.0+cu124'; assert gsplat.__version__=='1.5.3+pt24cu124'; print('Renderer dependencies verified')"
if ($LASTEXITCODE -ne 0) { throw 'Renderer environment does not match tested versions' }
if (-not (Test-Path -LiteralPath (Join-Path $SourceDirectory '.git'))) {
    & git clone 'https://github.com/nv-tlabs/Difix3D.git' $SourceDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Source download failed' }
    & git -C $SourceDirectory checkout --detach $ExpectedCommit
    if ($LASTEXITCODE -ne 0) { throw 'Pinned source checkout failed' }
}
$ActualCommit=(& git -C $SourceDirectory rev-parse HEAD).Trim()
if ($ActualCommit -ne $ExpectedCommit) { throw 'Existing Difix3D checkout differs from tested revision; preserve it and inspect before changing.' }
$EnvironmentDirectory=Join-Path $ProjectRoot '.local\envs\difix3d'
$PythonExecutable=Join-Path $EnvironmentDirectory 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    & $BasePython -m venv --system-site-packages $EnvironmentDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Isolated overlay creation failed' }
}
& $PythonExecutable -m pip install -r (Join-Path $ProjectRoot 'environments\difix3d-requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $PythonExecutable -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
Write-Output 'Difix3D setup complete. Original static and dynamic environments are preserved.'
