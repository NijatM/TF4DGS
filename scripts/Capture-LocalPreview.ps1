param(
    [string]$Url = 'http://127.0.0.1:8100/',
    [Parameter(Mandatory=$true)][string]$OutputFile,
    [string]$Expression = 'true',
    [int]$DebugPort = 8098,
    [switch]$Reload
)
$ErrorActionPreference = 'Stop'
if ($Url -notmatch '^http://127\.0\.0\.1:(8096|8097|8100|8101)/') { throw 'Only dedicated local TF4DGS preview pages may be captured.' }
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
    $Pages = Invoke-RestMethod ('http://127.0.0.1:'+$DebugPort+'/json')
    $Page = $Pages | Where-Object { $_.type -eq 'page' -and $_.url -eq $Url } | Select-Object -First 1
    if (-not $Page) { $Page = Invoke-RestMethod -Method Put ('http://127.0.0.1:'+$DebugPort+'/json/new?'+[Uri]::EscapeDataString($Url)) }
    $Socket.ConnectAsync([Uri]$Page.webSocketDebuggerUrl,[System.Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp 'Page.bringToFront' @{} | Out-Null
    Invoke-Cdp 'Emulation.setDeviceMetricsOverride' @{width=1500;height=1150;deviceScaleFactor=1;mobile=$false} | Out-Null
    if ($Reload) { Invoke-Cdp 'Page.reload' @{ignoreCache=$true} | Out-Null; Start-Sleep -Milliseconds 250 }
    Invoke-Js '(async()=>{for(let i=0;i<120;i++){if(document.readyState==="complete"&&((window.tf4dgsMeta&&document.getElementById("render").naturalWidth>0)||(document.getElementById("scrub")&&typeof tracks!=="undefined"&&tracks&&state)))return true;await new Promise(r=>setTimeout(r,100));}throw Error("Preview did not load");})()' | Out-Null
    Invoke-Js $Expression | Out-Null
    Invoke-Js '(async()=>{await Promise.all([...document.images].map(i=>i.decode()));await new Promise(r=>setTimeout(r,400));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true;})()' | Out-Null
    $Capture = Invoke-Cdp 'Page.captureScreenshot' @{format='png';captureBeyondViewport=$false}
    $Absolute = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputFile))
    $Docs = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path 'documentation'))
    if (-not $Absolute.StartsWith($Docs+[System.IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Screenshot output must stay inside project documentation.' }
    [System.IO.File]::WriteAllBytes($Absolute,[Convert]::FromBase64String($Capture.data))
    $State = Invoke-Js '(()=>{if(window.tf4dgsMeta)return {model:window.tf4dgsMeta.source,time:document.getElementById("timeLabel").textContent,mode:document.getElementById("mode").value,trails:document.getElementById("trails").checked};return {frame_index:state.frame_index,time_s:state.time_s,mode:state.mode,history_s:state.history_s};})()'
    $Record = @{filename=[System.IO.Path]::GetFileName($Absolute);kind='Live local preview browser screenshot';url=$Url;captured_utc=[DateTime]::UtcNow.ToString('o');expression=$Expression;page_state=$State}
    [System.IO.File]::WriteAllText([System.IO.Path]::ChangeExtension($Absolute,'.capture.json'),($Record|ConvertTo-Json -Depth 8),[System.Text.UTF8Encoding]::new($false))
    'Screenshot: '+$Absolute
} finally { $Socket.Dispose() }
