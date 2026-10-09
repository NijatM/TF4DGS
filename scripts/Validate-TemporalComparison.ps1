param(
    [ValidateSet('yogurt','textile')][string]$Dataset='yogurt',
    [int]$DebugPort=8099
)
$ErrorActionPreference='Stop'
$Expression=@'
(async()=>{
 const dataset=document.getElementById('dataset'),mode=document.getElementById('mode');
 dataset.value='__DATASET__';const results=[];
 for(const selected of ['fixed','comparison','orbit30']){
  mode.value=selected;await window.tf4dgsLoadComparison();
  const videos=[...document.querySelectorAll('video')];
  for(let i=0;i<videos.length;i++){
   const v=videos[i];videos.forEach(other=>other.pause());
   await window.tf4dgsSeekComparison(.7);v.scrollIntoView({block:'center'});
   await v.play();await new Promise(r=>setTimeout(r,250));
   const start={time:v.currentTime,quality:v.getVideoPlaybackQuality()};let presented=0,callback;
   const paint=()=>{presented++;callback=v.requestVideoFrameCallback(paint);};callback=v.requestVideoFrameCallback(paint);
   await new Promise(r=>setTimeout(r,1100));v.pause();v.cancelVideoFrameCallback(callback);
   const quality=v.getVideoPlaybackQuality();
   results.push({dataset:dataset.value,mode:selected,method:i===0?'4dgaussians':'4c4d',
    file:v.currentSrc.split('/').at(-1),width:v.videoWidth,height:v.videoHeight,duration_s:v.duration,
    played_from_s:start.time,played_to_s:v.currentTime,presented_callbacks:presented,
    decoded_frames:quality.totalVideoFrames-start.quality.totalVideoFrames,
    dropped_frames:quality.droppedVideoFrames-start.quality.droppedVideoFrames,
    document_hidden:document.hidden,error:v.error?v.error.message:null});
  }
 }
 window.tf4dgsVideoPlaybackCheck=results;
 if(results.some(r=>r.error||r.document_hidden||r.played_to_s-r.played_from_s<.8||r.presented_callbacks<25||r.dropped_frames>0))throw Error(JSON.stringify(results));
 mode.value='fixed';await window.tf4dgsLoadComparison();await window.tf4dgsSeekComparison(1.57);window.scrollTo(0,0);
 return results;
})()
'@
$Expression=$Expression.Replace('__DATASET__',$Dataset)
$OutputFile="documentation/temporal_benchmark_001/${Dataset}_comparison_browser.png"
& (Join-Path $PSScriptRoot 'Capture-LocalPreview.ps1') -Url 'http://127.0.0.1:8108/comparison.html' -OutputFile $OutputFile -DebugPort $DebugPort -Reload -Expression $Expression
$Capture=Get-Content -LiteralPath ([IO.Path]::ChangeExtension($OutputFile,'.capture.json')) -Raw -Encoding UTF8 | ConvertFrom-Json
$Validation=@{status='Passed native source comparisons and continuous model videos';dataset=$Dataset;captured_utc=$Capture.captured_utc;screenshot=[IO.Path]::GetFileName($OutputFile);sample_scope='Each video individually in view for 1.1 seconds after 250 ms startup warmup; full-file decode/timestamps checked separately';videos=$Capture.page_state.playback_check}
[IO.File]::WriteAllText([IO.Path]::GetFullPath("documentation/temporal_benchmark_001/${Dataset}_browser_validation.json"),($Validation|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
