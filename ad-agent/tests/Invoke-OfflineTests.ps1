Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src\DiscoveryEngine.psm1') -Force

$failures = @()
$passed = 0

function Assert-True {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if ($Condition) {
        $script:passed++
    }
    else {
        $script:failures += $Message
    }
}

$hash = Get-AIBitSha256 -Text 'abc'
Assert-True ($hash -eq 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad') 'SHA-256 mismatch'

$a = [ordered]@{
    z = 1
    a = [ordered]@{
        y = 2
        x = 3
    }
}
$b = [ordered]@{
    a = [ordered]@{
        x = 3
        y = 2
    }
    z = 1
}

$ja = (ConvertTo-AIBitCanonicalObject -InputObject $a) | ConvertTo-Json -Depth 10 -Compress
$jb = (ConvertTo-AIBitCanonicalObject -InputObject $b) | ConvertTo-Json -Depth 10 -Compress
Assert-True ($ja -eq $jb) 'Hashtable canonicalization is not deterministic'

$objectA = New-Object PSObject -Property ([ordered]@{
    z = 1
    a = New-Object PSObject -Property ([ordered]@{ y = 2; x = 3 })
})
$objectB = New-Object PSObject -Property ([ordered]@{
    a = New-Object PSObject -Property ([ordered]@{ x = 3; y = 2 })
    z = 1
})

$joa = (ConvertTo-AIBitCanonicalObject -InputObject $objectA) | ConvertTo-Json -Depth 10 -Compress
$job = (ConvertTo-AIBitCanonicalObject -InputObject $objectB) | ConvertTo-Json -Depth 10 -Compress
Assert-True ($joa -eq $job) 'PSCustomObject canonicalization is not deterministic'

$arrayResult = ConvertTo-AIBitCanonicalObject -InputObject @(
    [ordered]@{ b = 2; a = 1 },
    [ordered]@{ d = 4; c = 3 }
)
Assert-True (($arrayResult | ConvertTo-Json -Depth 10 -Compress) -eq '[{"a":1,"b":2},{"c":3,"d":4}]') 'Array canonicalization failed'

$plugins = Import-AIBitCollectors -Path (Join-Path $root 'collectors')
Assert-True ($plugins.Count -ge 5) 'Expected at least five collector plugins'
Assert-True ((@($plugins.Name | Sort-Object -Unique)).Count -eq $plugins.Count) 'Collector names must be unique'

$snapshot = New-AIBitSnapshot -Results @(
    [ordered]@{
        name = 'test'
        version = '1'
        status = 'ok'
        started_at_utc = 'x'
        finished_at_utc = 'x'
        source = 'test'
        reason = $null
        data = [ordered]@{ value = 1 }
    }
)
Assert-True ($snapshot.fingerprint.Length -eq 64) 'Snapshot fingerprint length invalid'
Assert-True ($snapshot.payload.schema_version -eq '1.1') 'Snapshot schema version invalid'

$result = [ordered]@{
    status = if ($failures.Count -gt 0) { 'failed' } else { 'ok' }
    powershell_version = $PSVersionTable.PSVersion.ToString()
    passed = $passed
    failed = $failures.Count
    failures = $failures
    tests = 8
}

$result | ConvertTo-Json -Depth 5
if ($failures.Count -gt 0) {
    exit 1
}
