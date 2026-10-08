param(
    [string]$Expression = '({ready:!!window.tf4dgsSuperSplat.scene,title:document.title})',
    [string[]]$Files = @(),
    [string]$OutputFile,
    [switch]$DiagnosticOnly,
    [switch]$StaticImport,
    [int]$DebugPort = 8098
)
# Inspect the official editor and import local exports without publishing them.
$ErrorActionPreference = 'Stop'
$TaskRoot = (Get-Location).Path
$ExportRoot = [IO.Path]::GetFullPath((Join-Path $TaskRoot 'outputs/dynamic_textile_001'))
$DocsRoot = [IO.Path]::GetFullPath((Join-Path $TaskRoot 'documentation/dynamic_textile_001'))
foreach ($File in $Files) {
    $Resolved = (Resolve-Path -LiteralPath $File).Path
    if (-not $Resolved.StartsWith($ExportRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or -not $Resolved.EndsWith('.ply')) { throw 'Only local textile Gaussian PLY exports may be imported.' }
}
if ($OutputFile) {
    $OutputFile = [IO.Path]::GetFullPath((Join-Path $TaskRoot $OutputFile))
    if (-not $OutputFile.StartsWith($DocsRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $OutputFile)) { throw 'Use a new documentation screenshot path.' }
}
$Socket = [Net.WebSockets.ClientWebSocket]::new()
$script:MessageId = 0
function Invoke-Cdp([string]$Method, $Parameters) {
    $script:MessageId++
    $CurrentId = $script:MessageId
    $Payload = @{id=$CurrentId;method=$Method;params=$Parameters} | ConvertTo-Json -Depth 20 -Compress
    $Bytes = [Text.Encoding]::UTF8.GetBytes($Payload)
    $Timeout = [Threading.CancellationTokenSource]::new(60000)
    try {
        $Socket.SendAsync([ArraySegment[byte]]::new($Bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,$Timeout.Token).GetAwaiter().GetResult() | Out-Null
        do {
            $Stream = [IO.MemoryStream]::new()
            try {
                do {
                    $Buffer = [byte[]]::new(262144)
                    $Received = $Socket.ReceiveAsync([ArraySegment[byte]]::new($Buffer),$Timeout.Token).GetAwaiter().GetResult()
                    $Stream.Write($Buffer,0,$Received.Count)
                } while (-not $Received.EndOfMessage)
                $Response = [Text.Encoding]::UTF8.GetString($Stream.ToArray()) | ConvertFrom-Json
            } finally { $Stream.Dispose() }
        } while ($Response.id -ne $CurrentId)
        if ($Response.error) { throw ($Response.error | ConvertTo-Json -Compress) }
        return $Response.result
    } finally { $Timeout.Dispose() }
}
function Invoke-Js([string]$Value) {
    $Result = Invoke-Cdp 'Runtime.evaluate' @{expression=$Value;awaitPromise=$true;returnByValue=$true}
    if ($Result.exceptionDetails) { throw ($Result.exceptionDetails | ConvertTo-Json -Depth 10) }
    return $Result.result.value
}
try {
    $Url = 'https://superspl.at/editor/'
    $Pages = Invoke-RestMethod ('http://127.0.0.1:'+$DebugPort+'/json')
    $Page = $Pages | Where-Object { $_.type -eq 'page' -and $_.url.TrimEnd('/') -eq $Url.TrimEnd('/') } | Select-Object -First 1
    if (-not $Page) { $Page = Invoke-RestMethod -Method Put ('http://127.0.0.1:'+$DebugPort+'/json/new?'+[Uri]::EscapeDataString($Url)) }
    $Socket.ConnectAsync([Uri]$Page.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    Invoke-Cdp 'Page.bringToFront' @{} | Out-Null
    if (-not $DiagnosticOnly) {
        for ($ReadyAttempt=0;$ReadyAttempt -lt 3;$ReadyAttempt++) {
            try {
                Invoke-Js '(async()=>{for(let i=0;i<180;i++){const e=document.querySelector("iframe")?.contentWindow||window;if(e.scene&&e.scene.events){window.tf4dgsSuperSplat=e;return true}await new Promise(r=>setTimeout(r,150));}throw Error("SuperSplat editor event interface unavailable");})()' | Out-Null
                break
            } catch {
                if ($ReadyAttempt -eq 2 -or $_.Exception.Message -notmatch 'Execution context was destroyed') { throw }
                Start-Sleep -Milliseconds 200
            }
        }
    } elseif ($Files.Count) { throw 'Diagnostic mode cannot import files.' }
    if ($Files.Count) {
        Invoke-Js '(()=>{document.getElementById("tf4dgs-local-import")?.remove();let e=document.createElement("input");e.type="file";e.multiple=true;e.id="tf4dgs-local-import";e.hidden=true;document.body.append(e);return true})()' | Out-Null
        $Document = Invoke-Cdp 'DOM.getDocument' @{}
        $Node = Invoke-Cdp 'DOM.querySelector' @{nodeId=$Document.root.nodeId;selector='#tf4dgs-local-import'}
        $ResolvedFiles = @($Files | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
        Invoke-Cdp 'DOM.setFileInputFiles' @{nodeId=$Node.nodeId;files=$ResolvedFiles} | Out-Null
        if ($StaticImport) {
            Invoke-Js '(async()=>{const files=Array.from(document.getElementById("tf4dgs-local-import").files);await window.tf4dgsSuperSplat.scene.events.invoke("import",files.map(f=>({filename:f.name,contents:f})));return {static_files_imported:files.length}})()' | ConvertTo-Json -Depth 8
        } else {
            Invoke-Js '(async()=>{const files=Array.from(document.getElementById("tf4dgs-local-import").files),events=window.tf4dgsSuperSplat.scene.events;await events.invoke("import",files.map(f=>({filename:f.name,contents:f})));await events.invoke("plysequence.setFrameAsync",0);events.fire("timeline.setFrameRate",30);return {files:files.length,frames:events.invoke("timeline.frames"),fps:events.invoke("timeline.frameRate")}})()' | ConvertTo-Json -Depth 8
        }
    }
    $State = Invoke-Js $Expression
    $State | ConvertTo-Json -Depth 12
    if ($OutputFile) {
        Invoke-Cdp 'Emulation.setDeviceMetricsOverride' @{width=1500;height=1100;deviceScaleFactor=1;mobile=$false} | Out-Null
        Invoke-Js '(async()=>{await new Promise(r=>setTimeout(r,500));return true})()' | Out-Null
        $Shot = Invoke-Cdp 'Page.captureScreenshot' @{format='png';captureBeyondViewport=$false}
        [IO.File]::WriteAllBytes($OutputFile,[Convert]::FromBase64String($Shot.data))
        $Record = @{url=$Url;captured_utc=[DateTime]::UtcNow.ToString('o');method='Genuine CDP screenshot of official SuperSplat editor';local_files_imported=$Files.Count;state=$State;published=$false}
        [IO.File]::WriteAllText([IO.Path]::ChangeExtension($OutputFile,'.capture.json'),($Record|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
    }
} finally { $Socket.Dispose() }
