[CmdletBinding()]
param(
    [string]$OutputPath = '.\data\snapshots\ad-snapshot.json',
    [string[]]$IncludeCollector = @(),
    [string[]]$ExcludeCollector = @(),
    [switch]$PassThru
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src\DiscoveryEngine.psm1') -Force

$plugins = Import-AIBitCollectors -Path $PSScriptRoot
if ($IncludeCollector.Count -gt 0) { $plugins = @($plugins | Where-Object { $IncludeCollector -contains $_.Name }) }
if ($ExcludeCollector.Count -gt 0) { $plugins = @($plugins | Where-Object { $ExcludeCollector -notcontains $_.Name }) }

$results = @()
foreach ($plugin in $plugins) { $results += ,(Invoke-AIBitCollector -Collector $plugin) }
$snapshot = New-AIBitSnapshot -Results $results -AgentVersion '6.2.0'
$path = Export-AIBitSnapshot -Snapshot $snapshot -Path $OutputPath

if ($PassThru) { return $snapshot }
[ordered]@{
    status='ok'
    path=$path
    snapshot_id=$snapshot.payload.snapshot_id
    fingerprint=$snapshot.fingerprint
    collectors=@($results | Select-Object name,status,reason)
} | ConvertTo-Json -Depth 8