# Functional local smoke checks, separate from reconstruction quality testing.
[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'Initialize-BuildSession.ps1')
$Installed = Get-Content -LiteralPath (Join-Path $ProjectRoot 'static-tools.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Colmap = ($Installed.portable_tools | Where-Object name -eq 'COLMAP').executable_path
$Ffmpeg = ($Installed.portable_tools | Where-Object name -eq 'FFmpeg').executable_path
$Ffprobe = ($Installed.portable_tools | Where-Object name -eq 'FFmpeg').ffprobe_path
$Scratch = Join-Path $Builds ('static-smoke-' + [Guid]::NewGuid().ToString('N'))
$VideoFrames = Join-Path $Scratch 'video-frames'
$Images = Join-Path $Scratch 'feature-images'
foreach ($Folder in @($Scratch,$VideoFrames,$Images)) { New-Item -ItemType Directory -Path $Folder -Force | Out-Null }
$Clip = Join-Path $Scratch 'synthetic.mp4'
Invoke-CheckedNative $Ffmpeg @('-hide_banner','-loglevel','error','-n','-f','lavfi','-i','testsrc2=size=640x480:rate=10','-t','1','-c:v','libx264','-pix_fmt','yuv420p',$Clip) (Join-Path $Logs 'ffmpeg-encode-smoke.log')
$ProbeText = (Invoke-CheckedNative $Ffprobe @('-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height','-of','json',$Clip) | Out-String)
$Probe = $ProbeText | ConvertFrom-Json
if ($Probe.streams[0].width -ne 640 -or $Probe.streams[0].height -ne 480) { throw 'Video dimensions differ from the generated test clip.' }
Invoke-CheckedNative $Ffmpeg @('-hide_banner','-loglevel','error','-n','-i',$Clip,'-vf','fps=5',(Join-Path $VideoFrames 'frame_%03d.png')) (Join-Path $Logs 'ffmpeg-extract-smoke.log')
$FrameCount = @(Get-ChildItem -LiteralPath $VideoFrames -File -Filter '*.png').Count
if ($FrameCount -ne 5) { throw "Expected five decoded/extracted frames, received $FrameCount." }

# A deterministic textured surface and translated view exercise real SIFT.
Add-Type -AssemblyName System.Drawing
$Bitmap = New-Object System.Drawing.Bitmap(640,480)
$Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
$Random = New-Object System.Random(73142)
try {
    $Graphics.Clear([System.Drawing.Color]::White)
    for ($Index=0; $Index -lt 1000; $Index++) {
        $Brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb($Random.Next(256),$Random.Next(256),$Random.Next(256)))
        try { $Graphics.FillRectangle($Brush,$Random.Next(620),$Random.Next(460),$Random.Next(3,22),$Random.Next(3,22)) }
        finally { $Brush.Dispose() }
    }
    $Bitmap.Save((Join-Path $Images 'view_0.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    $Shifted = New-Object System.Drawing.Bitmap(640,480)
    $ShiftedGraphics = [System.Drawing.Graphics]::FromImage($Shifted)
    try {
        $ShiftedGraphics.Clear([System.Drawing.Color]::White)
        $ShiftedGraphics.DrawImage($Bitmap,18,10)
        $Shifted.Save((Join-Path $Images 'view_1.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $ShiftedGraphics.Dispose(); $Shifted.Dispose() }
} finally { $Graphics.Dispose(); $Bitmap.Dispose() }
$Database = Join-Path $Scratch 'features.db'
Invoke-CheckedNative $Colmap @('feature_extractor','--database_path',$Database,'--image_path',$Images,'--ImageReader.single_camera','1','--ImageReader.camera_model','PINHOLE','--FeatureExtraction.use_gpu','1','--FeatureExtraction.gpu_index','0') (Join-Path $Logs 'colmap-gpu-extraction-smoke.log')
Invoke-CheckedNative $Colmap @('exhaustive_matcher','--database_path',$Database,'--FeatureMatching.type','SIFT_BRUTEFORCE','--FeatureMatching.use_gpu','1','--FeatureMatching.gpu_index','0') (Join-Path $Logs 'colmap-gpu-matching-smoke.log')
$BasePython = Join-Path $env:USERPROFILE 'miniconda3\python.exe'
$SqlCheck = Join-Path $Scratch 'check_database.py'
@'
import json
import sqlite3
import sys
with sqlite3.connect(sys.argv[1]) as connection:
    keypoints = connection.execute('select coalesce(sum(rows),0) from keypoints').fetchone()[0]
    matches = connection.execute('select coalesce(sum(rows),0) from matches').fetchone()[0]
print(json.dumps({'keypoints': keypoints, 'matches': matches}))
assert keypoints > 0 and matches > 0
'@ | Set-Content -LiteralPath $SqlCheck -Encoding ASCII
$SqlText = (Invoke-CheckedNative $BasePython @($SqlCheck,$Database) (Join-Path $Logs 'colmap-database-smoke.log') | Out-String)
$Counts = $SqlText | ConvertFrom-Json
[ordered]@{
    project = 'TF4DGS'; checked_utc = [DateTime]::UtcNow.ToString('o');
    video_encode_decode_passed = $true; extracted_frames = $FrameCount;
    colmap_gpu_extraction_passed = $true; colmap_gpu_matching_passed = $true;
    keypoints = $Counts.keypoints; matches = $Counts.matches;
    fixture_path = $Scratch; reconstruction_quality_validation = 'pending-user-footage'
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ProjectRoot 'static-tools-validation.json') -Encoding UTF8
Write-Output 'Video encode/decode/extraction and COLMAP GPU SIFT extraction/matching passed.'
