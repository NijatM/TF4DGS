# Shared verified-download helper; callers supply exact upstream artifact pins.
function Get-VerifiedProjectDownload {
    param(
        [string]$Uri, [string]$Destination,
        [Alias('Sha256')][string]$ExpectedHash,
        [ValidateSet('SHA256','SHA512')][string]$Algorithm = 'SHA256'
    )
    $Destination = [System.IO.Path]::GetFullPath($Destination)
    New-Item -ItemType Directory -Path (Split-Path -Parent $Destination) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $Destination)) {
        $Partial = $Destination + '.partial'
        Invoke-CheckedNative 'curl.exe' @(
            '--fail', '--location', '--retry', '3', '--retry-delay', '2',
            '--connect-timeout', '30', '--continue-at', '-', '--silent',
            '--show-error', '--output', $Partial, $Uri
        )
        Move-Item -LiteralPath $Partial -Destination $Destination
    }
    $ActualHash = (Get-FileHash -LiteralPath $Destination -Algorithm $Algorithm).Hash.ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHash.ToLowerInvariant()) {
        throw "$Algorithm mismatch: $Destination. Do not execute or extract it."
    }
    Write-Output "Verified ${Algorithm}: $Destination"
}
