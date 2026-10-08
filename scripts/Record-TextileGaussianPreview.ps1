param(
    [Parameter(Mandatory=$true)][string]$Attempt,
    [ValidateSet('rgb','geometry','color','combined')][string]$Mode = 'rgb',
    [int]$DebugPort = 8098
)
# Record real browser paints at source wall-clock speed; never synthesize frames.
$ErrorActionPreference = 'Stop'
if ($Attempt -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Use a simple unique attempt name.' }
$TaskRoot = (Get-Location).Path
if (-not (Test-Path -LiteralPath 'scripts/Serve-TextileGaussianPreview.py')) { throw 'Run from the TF4DGS repository root.' }
$ControlDirectory = Join-Path $TaskRoot ('.local/workflows/dynamic_setup/textile_reconstruction_02/recording_controls/'+$Attempt)
if (Test-Path -LiteralPath $ControlDirectory) { throw 'Preserve previous attempts; choose a new name.' }
New-Item -ItemType Directory -Path $ControlDirectory | Out-Null
$Setup = @'
(async()=>{
  stop(); await refresh();
  if(meta.status!=='complete'||frames.length!==meta.requested)throw Error('Finish and validate the full sequence before recording');
  document.getElementById('camera').value='orbit';
  document.getElementById('mode').value='__MODE__';
  document.getElementById('table').checked=true;
  document.getElementById('trails').checked=false;
  document.getElementById('reference').value='first';
  document.getElementById('time').value=0;
  azimuth=95; elevation=48; distance=.57; panX=0; panY=0;
  await window.tf4dgsUpdate();
  return {model:meta.source,representation:meta.representation,keyframes:frames.length,
    mode:document.getElementById('mode').value,source_duration_s:frames.at(-1).time_s,
    orbit:'Elevated iPhone-side view; azimuth 95 +/-45 degrees, back and forth',
    time_interpolation:false,persistent_material_ids:false};
})()
'@
$Setup = $Setup.Replace('__MODE__',$Mode)
$Playback = @'
(async()=>{
  stop(); const start=performance.now(), duration=frames.at(-1).time_s;
  const shown=[],sourceSamples=[];
  while(true){
    const t=Math.min(duration,(performance.now()-start)/1000);
    let index=0;
    while(index<frames.length-1&&frames[index+1].time_s<=t)index++;
    document.getElementById('time').value=index;
    azimuth=95+45*Math.sin(2*Math.PI*t/duration);
    await window.tf4dgsUpdate();
    if(shown.at(-1)!==frames[index].index){shown.push(frames[index].index);sourceSamples.push({index:frames[index].index,time_s:frames[index].time_s,azimuth_deg:azimuth,elevation_deg:elevation,distance_m:distance});}
    if(t>=duration)break;
    await new Promise(r=>setTimeout(r,Math.max(0,80-(performance.now()-start-t*1000))));
  }
  return {source_first_s:frames[0].time_s,source_last_s:frames.at(-1).time_s,
    wall_elapsed_s:(performance.now()-start)/1000,keyframes_displayed:shown,
    source_samples:sourceSamples,
    timing:'Actual source wall-clock replay; slow renders may skip discrete keyframes',
    orbit:'One elevated +/-45 degree arc back and forth',
    mode:document.getElementById('mode').value};
})()
'@
$SetupPath = Join-Path $ControlDirectory 'setup.js'
$PlaybackPath = Join-Path $ControlDirectory 'playback.js'
[IO.File]::WriteAllText($SetupPath,$Setup,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($PlaybackPath,$Playback,[Text.UTF8Encoding]::new($false))
$CaptureDirectory = '.local/workflows/dynamic_setup/textile_reconstruction_02/browser_captures/'+$Attempt
& (Join-Path $TaskRoot 'scripts/Record-LocalWebViewer.ps1') -Url 'http://127.0.0.1:8104/' `
    -CacheDirectory $CaptureDirectory -SetupExpressionFile $SetupPath `
    -PlaybackExpressionFile $PlaybackPath -DebugPort $DebugPort -Width 1500 -Height 1150
if (-not $?) { throw 'Browser capture failed; keep its failure record.' }
Write-Output ('Capture ready for Encode-WebViewerRecording.py: '+$CaptureDirectory+'/capture.json')
