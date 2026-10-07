param(
    [int]$DebugPort = 8098,
    [string]$Output = 'documentation/dynamic_capture_001',
    [int[]]$RecaptureStages = @()
)
$ErrorActionPreference = 'Stop'
$Socket = [System.Net.WebSockets.ClientWebSocket]::new()
$script:MessageId = 0
function Invoke-Cdp([string]$Method, $Parameters) {
    $script:MessageId++
    $CurrentId = $script:MessageId
    $Payload = @{id=$CurrentId;method=$Method;params=$Parameters} | ConvertTo-Json -Depth 20 -Compress
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)
    $Timeout = [System.Threading.CancellationTokenSource]::new(15000)
    try {
        $Socket.SendAsync([System.ArraySegment[byte]]::new($Bytes),[System.Net.WebSockets.WebSocketMessageType]::Text,$true,$Timeout.Token).GetAwaiter().GetResult()
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
    $Pages = Invoke-RestMethod ('http://127.0.0.1:' + $DebugPort + '/json')
    $Page = $Pages | Where-Object { $_.type -eq 'page' -and $_.url -like '*127.0.0.1:8097*' } | Select-Object -First 1
    if (-not $Page) {
        $Page = Invoke-RestMethod -Method Put ('http://127.0.0.1:'+$DebugPort+'/json/new?'+[Uri]::EscapeDataString('http://127.0.0.1:8097/'))
    }
    $Socket.ConnectAsync([Uri]$Page.webSocketDebuggerUrl,[System.Threading.CancellationToken]::None).GetAwaiter().GetResult()
    # requestAnimationFrame can remain suspended in a background tab. Show
    # this task-owned report before waiting for the screenshot's paint cycle.
    Invoke-Cdp 'Page.bringToFront' @{} | Out-Null
    Invoke-Cdp 'Emulation.setDeviceMetricsOverride' @{width=1500;height=1100;deviceScaleFactor=1;mobile=$false} | Out-Null
    Invoke-Cdp 'Page.reload' @{ignoreCache=$true} | Out-Null
    Invoke-Js '(async()=>{for(let i=0;i<100;i++){if(document.readyState==="complete"&&window.tf4dgsStages)return true;await new Promise(r=>setTimeout(r,100));}throw Error("Report did not finish loading");})()' | Out-Null
    $Stages = Invoke-Js 'window.tf4dgsStages.map(s=>({number:s.number,title:s.title,status:s.status}))'
    $Records = @()
    $ManifestPath = Join-Path (Resolve-Path -LiteralPath $Output).Path 'screenshot_manifest.json'
    if (Test-Path -LiteralPath $ManifestPath) {
        $Previous = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
        foreach ($Record in $Previous) { $Records += $Record }
    }
    $NewCount = 0
    foreach ($Stage in $Stages) {
        $Existing = @($Records | Where-Object { $_.stage -eq $Stage.number })
        if ($Existing.Count -gt 0 -and $Stage.number -notin $RecaptureStages) { continue }
        $Expression = '(async()=>{const s=document.getElementById("stage");s.value=' + $Stage.number + ';s.dispatchEvent(new Event("change"));await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return document.querySelector("h2").textContent;})()'
        $Heading = Invoke-Js $Expression
        if ($Heading -ne $Stage.title) { throw 'Screenshot page does not match the intended chronological stage.' }
        $Slug = ($Stage.title -replace '^\d+\s*','' -replace '[^A-Za-z0-9]+','_').Trim('_').ToLowerInvariant()
        $Filename = $Stage.number.ToString('D2') + '_' + $Slug + '_report.png'
        $Capture = Invoke-Cdp 'Page.captureScreenshot' @{format='png';captureBeyondViewport=$false}
        [System.IO.File]::WriteAllBytes((Join-Path (Resolve-Path -LiteralPath $Output).Path $Filename),[Convert]::FromBase64String($Capture.data))
        $Record = @{stage=$Stage.number;filename=$Filename;status=$Stage.status;kind='Actual browser screenshot of preserved processing report';retrospective=$true;captured_utc=[DateTime]::UtcNow.ToString('o')}
        if ($Existing.Count -gt 0) {
            $Record.previous_capture_times_utc = @($Existing | ForEach-Object { $_.captured_utc })
            $Record.recapture_reason = 'Corrected current report footer; original outcome/evidence unchanged.'
            $Records = @($Records | Where-Object { $_.stage -ne $Stage.number })
        }
        $Records += $Record
        $NewCount++
        $CheckpointJson = $Records | Sort-Object stage | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($ManifestPath,$CheckpointJson,[System.Text.UTF8Encoding]::new($false))
    }
    Invoke-Js 'document.getElementById("stage").value=window.tf4dgsStages.at(-1).number;document.getElementById("stage").dispatchEvent(new Event("change"));true' | Out-Null
    $Json = $Records | Sort-Object stage | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($ManifestPath,$Json,[System.Text.UTF8Encoding]::new($false))
    Write-Output ('Captured/updated ' + $NewCount + ' screenshots. Total unique chronological stages: ' + $Records.Count + '.')
} finally { $Socket.Dispose() }
