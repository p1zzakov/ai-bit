[CmdletBinding()]
param([switch]$SkipLiveCollection)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src/AdDiscovery.Core.psm1') -Force
$checks=@()
$hash=Get-AiBitSha256 'abc'
$checks += [ordered]@{name='sha256';status=if($hash -eq 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'){'ok'}else{'error'};actual=$hash}
$a=[ordered]@{z=1;a=2};$b=[ordered]@{a=2;z=1}
$ca=(ConvertTo-AiBitCanonicalObject $a|ConvertTo-Json -Compress);$cb=(ConvertTo-AiBitCanonicalObject $b|ConvertTo-Json -Compress)
$checks += [ordered]@{name='canonicalization';status=if($ca -eq $cb){'ok'}else{'error'};actual=$ca}
$schema=Get-Content (Join-Path $root 'schemas/ad-snapshot.schema.json') -Raw|ConvertFrom-Json
$checks += [ordered]@{name='schema_parse';status=if($schema.'$schema'){'ok'}else{'error'};actual=$schema.title}
if(-not $SkipLiveCollection){
    $out=Join-Path $env:TEMP 'ai-bit-ad-snapshot-test.json'
    & (Join-Path $root 'collectors/Get-AdDiscoverySnapshot.ps1') -OutputPath $out -PassThru | Out-Null
    $doc=Get-Content $out -Raw|ConvertFrom-Json
    $checks += [ordered]@{name='live_collection';status=if($doc.fingerprint.value -and $doc.payload.collectors.Count -ge 4){'ok'}else{'error'};actual=$out}
}
$result=[ordered]@{status=if(@($checks|Where-Object status -eq 'error').Count -eq 0){'ok'}else{'error'};checks=$checks}
$result|ConvertTo-Json -Depth 8
if($result.status -ne 'ok'){exit 1}
