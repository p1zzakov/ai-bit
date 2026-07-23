[CmdletBinding()]
param([switch]$SkipGpo)
$root=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src/AdDiscovery.Core.psm1') -Force
$result=Test-AiBitPrerequisites -RequireGroupPolicy:(-not $SkipGpo)
$result|ConvertTo-Json -Depth 6
if($result.status -ne 'ok'){exit 1}
