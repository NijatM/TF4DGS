param(
    [string]$Url = 'http://127.0.0.1:8100/',
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [string]$Expression = 'true',
    [int]$DebugPort = 8098,
    [switch]$Reload
)
$ErrorActionPreference = 'Stop'
if ($Url -notmatch '^http://127\.0\.0\.1:(8096|8097|8100|8101|8102|8103|8104|8105|8107|8108|8109|8110)/') { throw 'Only dedicated local TF4DGS preview pages may be captured.' }
$Socket = [System.Net.WebSockets.ClientWebSocket]::new()
$script:MessageId = 0
function Invoke-Cdp([string]$Method, $Parameters) {
    $script:MessageId++
    $CurrentId = $script:MessageId
    $Payload = @{id=$CurrentId;method=$Method;params=$Parameters} | ConvertTo-Json -Depth 20 -Compress
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)
    $Timeout = [System.Threading.CancellationTokenSource]::new(15000)
    try {
        $Socket.SendAsync([System.ArraySegment[byte]]::new($Bytes),[System.Net.WebSockets.WebSocketMessageType]::Text,$true,$Timeout.Token).GetAwaiter().GetResult() | Out-Null
        do {
            $Stream = [System.IO.MemoryStream]::new()
            try {
                do {
                    $Buffer = [byte[]]::new(65536)
                    $Received = $Socket.ReceiveAsync([System.ArraySegment[byte]]::new($Buffer),$Timeout.Token).GetAwaiter().GetResult()
                    $Stream.Write($Buffer,0,$Received.Count)
                } while (-not $Received.EndOfMessage)
                $Response = [System.Text.Encoding]::UTF8.GetString($Stream.ToArray()) | ConvertFrom-Json
            } finally { $Stream.Dispose() }
        } while ($Response.id -ne $CurrentId)
        if ($Response.error) { throw ($Response.error | ConvertTo-Json -Compress) }
        return $Response.result
    } finally { $Timeout.Dispose() }
}
function Invoke-Js([string]$Expression) {
    $Value = Invoke-Cdp 'Runtime.evaluate' @{expression=$Expression;awaitPromise=$true;returnByValue=$true}
    if ($Value.exceptionDetails) { throw ($Value.exceptionDetails | ConvertTo-Json -Depth 10) }
    return $Value.result.value
}
try {
    # Foreground rendering is needed for reliable animation-frame captures.
    # Restore only a window displaying a TF4DGS task page.
    $TaskWindow = if($DebugPort -eq 8098) { Get-Process msedge -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'TF4DGS' } | Select-Object -First 1 } else { $null }
    if ($TaskWindow) {
        if (-not ('TF4DGSCaptureWindow' -as [type])) {
            Add-Type 'using System; using System.Runtime.InteropServices; public static class TF4DGSCaptureWindow { [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow); [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd); }'
        }
        [TF4DGSCaptureWindow]::ShowWindowAsync($TaskWindow.MainWindowHandle,9) | Out-Null
        [TF4DGSCaptureWindow]::SetForegroundWindow($TaskWindow.MainWindowHandle) | Out-Null
    }
    $Pages = Invoke-RestMethod ('http://127.0.0.1:'+$DebugPort+'/json')
    $Page = $Pages | Where-Object { $_.type -eq 'page' -and $_.url -eq $Url } | Select-Object -First 1
    if (-not $Page) { $Page = Invoke-RestMethod -Method Put ('http://127.0.0.1:'+$DebugPort+'/json/new?'+[Uri]::EscapeDataString($Url)) }
    $Socket.ConnectAsync([Uri]$Page.webSocketDebuggerUrl,[System.Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp 'Page.bringToFront' @{} | Out-Null
    Invoke-Cdp 'Emulation.setDeviceMetricsOverride' @{width=1500;height=1150;deviceScaleFactor=1;mobile=$false} | Out-Null
    if ($Reload) { Invoke-Cdp 'Page.reload' @{ignoreCache=$true} | Out-Null; Start-Sleep -Milliseconds 250 }
    Invoke-Js '(async()=>{for(let i=0;i<120;i++){if(document.readyState==="complete"&&(window.tf4dgsReportReady||window.tf4dgsSceneGalleryReady||(window.tf4dgsMeta&&document.getElementById("render").naturalWidth>0)||(document.getElementById("scrub")&&typeof tracks!=="undefined"&&tracks&&state)||(document.querySelector("video")&&[...document.querySelectorAll("video")].every(v=>v.readyState>=1))))return true;await new Promise(r=>setTimeout(r,100));}throw Error("Preview did not load");})()' | Out-Null
    Invoke-Js $Expression | Out-Null
    Invoke-Js 'window.tf4dgsFreezeReport=true' | Out-Null
    Invoke-Js '(async()=>{for(let n=0;n<15;n++){const imgs=[...document.images].filter(i=>i.getAttribute("src"));const results=await Promise.allSettled(imgs.map(i=>i.decode()));if(results.every(r=>r.status==="fulfilled")){await new Promise(r=>setTimeout(r,400));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true;}await new Promise(r=>setTimeout(r,200));}throw Error("Images failed to decode: "+[...document.images].filter(i=>i.getAttribute("src")&&!i.naturalWidth).map(i=>i.src).join(", "));})()' | Out-Null
    $Capture = Invoke-Cdp 'Page.captureScreenshot' @{format='png';captureBeyondViewport=$false}
    $Absolute = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputFile))
    $Docs = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path 'documentation'))
    if (-not $Absolute.StartsWith($Docs+[System.IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Screenshot output must stay inside project documentation.' }
    [System.IO.File]::WriteAllBytes($Absolute,[Convert]::FromBase64String($Capture.data))
    $State = Invoke-Js '(()=>{if(window.tf4dgsReportReady)return {stage:window.tf4dgsReportStage};if(window.tf4dgsMeta)return {model:window.tf4dgsMeta.source,time:document.getElementById("timeLabel").textContent,mode:document.getElementById("mode").value,trails:document.getElementById("trails").checked};if(window.tf4dgsSceneGalleryReady)return {gallery:true,dataset:document.getElementById("dataset").value,playback_check:window.tf4dgsVideoPlaybackCheck||null,controls_check:window.tf4dgsControlsCheck||null};if(document.querySelector("video"))return {videos:[...document.querySelectorAll("video")].map(v=>({file:v.currentSrc.split("/").at(-1),duration_s:v.duration,width:v.videoWidth,height:v.videoHeight,ready_state:v.readyState,error:v.error?v.error.message:null})),playback_check:window.tf4dgsVideoPlaybackCheck||null,controls_check:window.tf4dgsControlsCheck||null};return {frame_index:state.frame_index,time_s:state.time_s,mode:state.mode,history_s:state.history_s};})()'
    $CaptureKind=if($DebugPort -eq 8099){'Headless local report browser screenshot'}else{'Live local preview browser screenshot'}
    $Record = @{filename=[System.IO.Path]::GetFileName($Absolute);kind=$CaptureKind;url=$Url;captured_utc=[DateTime]::UtcNow.ToString('o');expression=$Expression;page_state=$State}
    [System.IO.File]::WriteAllText([System.IO.Path]::ChangeExtension($Absolute,'.capture.json'),($Record|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
    'Screenshot: '+$Absolute
} finally {
    if ($Socket.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        try { Invoke-Js 'window.tf4dgsFreezeReport=false' | Out-Null } catch { }
    }
    $Socket.Dispose()
}
