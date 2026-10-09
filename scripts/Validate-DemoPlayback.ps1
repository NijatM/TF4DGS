param(
    [string]$OutputFile = 'documentation\demos\gallery_review_4k.png'
)
$ErrorActionPreference = 'Stop'
$Playback = @'
(async()=>{
 const results=[];
 for(const v of document.querySelectorAll('video')){
  v.pause();v.muted=true;v.scrollIntoView({block:'center'});
  await new Promise(r=>setTimeout(r,300));
  if(document.hidden)throw Error('Keep the dedicated demo browser in the foreground during playback validation.');
  const seek=Math.min(5,v.duration/2);
  await new Promise((resolve,reject)=>{
   const timer=setTimeout(()=>reject(Error('Seek timed out: '+v.id)),4000);
   v.addEventListener('seeked',()=>{clearTimeout(timer);resolve();},{once:true});v.currentTime=seek;
  });
  await new Promise(r=>setTimeout(r,150));
  const q0=v.getVideoPlaybackQuality(), start=v.currentTime;
  let presented=0, callback;
  const paint=()=>{presented++;callback=v.requestVideoFrameCallback(paint);};
  callback=v.requestVideoFrameCallback(paint);
  await v.play();await new Promise(r=>setTimeout(r,1100));v.pause();v.cancelVideoFrameCallback(callback);
  const q=v.getVideoPlaybackQuality();
  results.push({id:v.id,file:v.currentSrc.split('/').at(-1),width:v.videoWidth,height:v.videoHeight,
   duration_s:v.duration,seek_s:seek,played_from_s:start,played_to_s:v.currentTime,
   presented_callbacks:presented,total_frames_during_play:q.totalVideoFrames-q0.totalVideoFrames,
   dropped_frames_during_play:q.droppedVideoFrames-q0.droppedVideoFrames,
   document_hidden:document.hidden,viewport_scroll_y:scrollY,error:v.error?v.error.message:null});
 }
 window.tf4dgsVideoPlaybackCheck=results;window.scrollTo(0,0);
 if(results.some(r=>r.error||r.document_hidden||r.played_to_s-r.played_from_s<.8||r.presented_callbacks<25||r.dropped_frames_during_play>0))throw Error(JSON.stringify(results));
 return results;
})()
'@
& (Join-Path $PSScriptRoot 'Capture-LocalPreview.ps1') -Url 'http://127.0.0.1:8107/' -OutputFile $OutputFile -Expression $Playback
if (-not $?) { throw 'Browser playback validation failed; preserve the failed attempt before retrying.' }
$Metadata = [System.IO.Path]::ChangeExtension($OutputFile,'.capture.json')
$Capture = Get-Content -LiteralPath $Metadata -Raw -Encoding UTF8 | ConvertFrom-Json
$Validation = @{
    status='All four videos sought and played; no browser frame drops in the foreground samples'
    recorded_utc=$Capture.captured_utc
    screenshot=[System.IO.Path]::GetFileName($OutputFile)
    sample_scope='About 1.1 seconds per video after seeking; full-file timestamps and decode checked separately'
    videos=$Capture.page_state.playback_check
}
$ValidationPath = Join-Path ([System.IO.Path]::GetDirectoryName($OutputFile)) 'browser_validation.json'
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($ValidationPath),($Validation | ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
