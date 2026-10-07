param(
    [Parameter(Mandatory=$true)][string]$Url,
    [Parameter(Mandatory=$true)][string]$CacheDirectory,
    [Parameter(Mandatory=$true)][string]$SetupExpressionFile,
    [Parameter(Mandatory=$true)][string]$PlaybackExpressionFile,
    [int]$DebugPort = 8098,
    [int]$Width = 1500,
    [int]$Height = 1000
)
# Stream actual browser paint frames. Do not capture the desktop or other tabs.
# Raw lossless frames remain in an ignored cache; encode only final small clips.
$ErrorActionPreference = 'Stop'
if ($Url -notmatch '^http://127\.0\.0\.1:(8096|8100|8101|8102)/$') { throw 'Only dedicated TF4DGS local viewers may be recorded.' }
$TaskRoot = (Get-Location).Path
$CacheRoot = [IO.Path]::GetFullPath((Join-Path $TaskRoot '.local/workflows/dynamic_setup'))
$TaskCache = [IO.Path]::GetFullPath((Join-Path $TaskRoot $CacheDirectory))
if (-not $TaskCache.StartsWith($CacheRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Raw video capture must stay in the ignored dynamic cache.' }
if (Test-Path -LiteralPath $TaskCache) { throw 'Preserve previous capture attempts; choose a new cache directory.' }
New-Item -ItemType Directory -Path $TaskCache | Out-Null
$Socket = [Net.WebSockets.ClientWebSocket]::new()
$script:MessageId = 0
$script:CaptureActive = $false
$script:Frames = [Collections.Generic.List[object]]::new()
function Send-Cdp([string]$Method,$Parameters) {
    $script:MessageId++
    $Payload = @{id=$script:MessageId;method=$Method;params=$Parameters} | ConvertTo-Json -Depth 15 -Compress
    $Bytes = [Text.Encoding]::UTF8.GetBytes($Payload)
    $Timeout = [Threading.CancellationTokenSource]::new(15000)
    try { $Socket.SendAsync([ArraySegment[byte]]::new($Bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,$Timeout.Token).GetAwaiter().GetResult() | Out-Null }
    finally { $Timeout.Dispose() }
    return $script:MessageId
}
function Receive-Cdp {
    $Stream = [IO.MemoryStream]::new()
    $Timeout = [Threading.CancellationTokenSource]::new(45000)
    try {
        do {
            $Buffer = [byte[]]::new(262144)
            $Received = $Socket.ReceiveAsync([ArraySegment[byte]]::new($Buffer),$Timeout.Token).GetAwaiter().GetResult()
            if ($Received.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close) { throw 'Browser capture socket closed.' }
            $Stream.Write($Buffer,0,$Received.Count)
        } while (-not $Received.EndOfMessage)
        $Response = [Text.Encoding]::UTF8.GetString($Stream.ToArray()) | ConvertFrom-Json
        return $Response
    } finally { $Stream.Dispose();$Timeout.Dispose() }
}
function Receive-Response([int]$CurrentId) {
    while ($true) {
        $Response = Receive-Cdp
        if ($Response.method -eq 'Page.screencastFrame') {
            if ($script:CaptureActive) {
                $Number = $script:Frames.Count
                $Filename = 'frame_'+$Number.ToString('D6')+'.png'
                [IO.File]::WriteAllBytes((Join-Path $TaskCache $Filename),[Convert]::FromBase64String($Response.params.data))
                $script:Frames.Add(@{filename=$Filename;timestamp_s=[double]$Response.params.metadata.timestamp;received_utc=[DateTime]::UtcNow.ToString('o')})
            }
            Send-Cdp 'Page.screencastFrameAck' @{sessionId=$Response.params.sessionId} | Out-Null
        }
        if ($Response.id -eq $CurrentId) {
            if ($Response.error) { throw ($Response.error | ConvertTo-Json -Compress) }
            return $Response.result
        }
    }
}
function Invoke-Cdp([string]$Method,$Parameters) { $Id=Send-Cdp $Method $Parameters;return Receive-Response $Id }
function Invoke-Js([string]$Expression) {
    $Value=Invoke-Cdp 'Runtime.evaluate' @{expression=$Expression;awaitPromise=$true;returnByValue=$true}
    if ($Value.exceptionDetails) { throw ($Value.exceptionDetails | ConvertTo-Json -Depth 8) }
    return $Value.result.value
}
try {
    $Pages=Invoke-RestMethod ('http://127.0.0.1:'+$DebugPort+'/json')
    $Page=$Pages | Where-Object { $_.type -eq 'page' -and $_.url -eq $Url } | Select-Object -First 1
    if (-not $Page) { $Page=Invoke-RestMethod -Method Put ('http://127.0.0.1:'+$DebugPort+'/json/new?'+[Uri]::EscapeDataString($Url)) }
    $Socket.ConnectAsync([Uri]$Page.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp 'Page.bringToFront' @{} | Out-Null
    Invoke-Cdp 'Emulation.setDeviceMetricsOverride' @{width=$Width;height=$Height;deviceScaleFactor=1;mobile=$false} | Out-Null
    Invoke-Cdp 'Page.reload' @{ignoreCache=$true} | Out-Null
    Invoke-Js '(async()=>{for(let i=0;i<120;i++){if(document.readyState==="complete"&&((window.tf4dgsMeta&&document.getElementById("render").naturalWidth>0)||(typeof tracks!=="undefined"&&tracks&&state)))return true;await new Promise(r=>setTimeout(r,100));}throw Error("Viewer did not load");})()' | Out-Null
    $Setup=Get-Content -LiteralPath $SetupExpressionFile -Raw
    $Playback=Get-Content -LiteralPath $PlaybackExpressionFile -Raw
    $InitialState=Invoke-Js $Setup
    $script:CaptureActive=$true
    Invoke-Cdp 'Page.startScreencast' @{format='png';maxWidth=$Width;maxHeight=$Height;everyNthFrame=1} | Out-Null
    $PlaybackState=Invoke-Js $Playback
    # Let the last fully painted frame remain visible in the actual capture.
    Invoke-Js '(async()=>{await new Promise(r=>setTimeout(r,800));return true})()' | Out-Null
    Invoke-Cdp 'Page.stopScreencast' @{} | Out-Null
    $script:CaptureActive=$false
    if ($script:Frames.Count -lt 10) { throw 'Too few actual browser frames were captured.' }
    $Record=@{status='captured';method='CDP Page.startScreencast actual browser PNG paint frames';url=$Url;width=$Width;height=$Height;initial_state=$InitialState;playback_state=$PlaybackState;frames=@($script:Frames);finished_utc=[DateTime]::UtcNow.ToString('o')}
    [IO.File]::WriteAllText((Join-Path $TaskCache 'capture.json'),($Record|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    'Recorded '+$script:Frames.Count+' actual browser frames to '+$CacheDirectory
} catch {
    $Failure=@{status='failed';message=$_.Exception.Message;frames=@($script:Frames);url=$Url;finished_utc=[DateTime]::UtcNow.ToString('o')}
    [IO.File]::WriteAllText((Join-Path $TaskCache 'failure.json'),($Failure|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    throw
} finally { $Socket.Dispose() }
