Set-StrictMode -Version 2.0
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src\DiscoveryEngine.psm1') -Force

$failures=@()
function Assert-True([bool]$Condition,[string]$Message){ if(-not $Condition){$script:failures += $Message} }

$hash=Get-AIBitSha256 'abc'
Assert-True ($hash -eq 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad') 'SHA-256 mismatch'

$a=[ordered]@{z=1;a=[ordered]@{y=2;x=3}}
$b=[ordered]@{a=[ordered]@{x=3;y=2};z=1}
$ja=(ConvertTo-AIBitCanonicalObject $a)|ConvertTo-Json -Depth 10 -Compress
$jb=(ConvertTo-AIBitCanonicalObject $b)|ConvertTo-Json -Depth 10 -Compress
Assert-True ($ja -eq $jb) 'Canonicalization is not deterministic'

$plugins=Import-AIBitCollectors -Path (Join-Path $root 'collectors')
Assert-True ($plugins.Count -ge 5) 'Expected at least five collector plugins'
Assert-True ((@($plugins.Name | Sort-Object -Unique)).Count -eq $plugins.Count) 'Collector names must be unique'

$snapshot=New-AIBitSnapshot -Results @([ordered]@{name='test';version='1';status='ok';started_at_utc='x';finished_at_utc='x';source='test';reason=$null;data=@{value=1}})
Assert-True ($snapshot.fingerprint.Length -eq 64) 'Snapshot fingerprint length invalid'
Assert-True ($snapshot.payload.schema_version -eq '1.1') 'Snapshot schema version invalid'

$result=[ordered]@{status=if($failures.Count){'failed'}else{'ok'};failures=$failures;tests=4}
$result|ConvertTo-Json -Depth 5
if($failures.Count){exit 1}