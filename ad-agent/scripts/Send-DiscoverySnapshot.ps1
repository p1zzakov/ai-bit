[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$SnapshotPath,

    [Parameter(Mandatory=$true)]
    [string]$ServerUrl,

    [string]$ApiToken = '',
    [string]$AgentId = '',
    [int]$TimeoutSeconds = 120
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$resolvedPath = (Resolve-Path -LiteralPath $SnapshotPath).Path
$json = [System.IO.File]::ReadAllText($resolvedPath, [System.Text.Encoding]::UTF8)

try {
    $snapshot = $json | ConvertFrom-Json
}
catch {
    throw "Snapshot is not valid JSON: $($_.Exception.Message)"
}

if (-not $snapshot.fingerprint -or -not $snapshot.payload.snapshot_id) {
    throw 'Snapshot must contain fingerprint and payload.snapshot_id.'
}

$endpoint = $ServerUrl.TrimEnd('/') + '/api/v1/discovery/snapshots'
$headers = @{}
if ($ApiToken) {
    $headers['X-AIBIT-Token'] = $ApiToken
}
if ($AgentId) {
    $headers['X-AIBIT-Agent-ID'] = $AgentId
}

$response = Invoke-RestMethod `
    -Method Post `
    -Uri $endpoint `
    -Headers $headers `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($json)) `
    -TimeoutSec $TimeoutSeconds

$response | ConvertTo-Json -Depth 10
