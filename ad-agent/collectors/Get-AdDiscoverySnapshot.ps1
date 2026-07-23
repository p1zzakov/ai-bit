[CmdletBinding()]
param(
    [string]$OutputPath = './data/snapshots/ad-snapshot.json',
    [string]$ConfigPath = './config/agent.json',
    [switch]$SkipGpo,
    [switch]$PassThru
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $root 'src/AdDiscovery.Core.psm1') -Force

$config = if(Test-Path $ConfigPath){ Get-Content $ConfigPath -Raw | ConvertFrom-Json } else { $null }
$gpoEnabled = -not $SkipGpo
if($config -and $null -ne $config.collectors.gpo_summary){ $gpoEnabled = [bool]$config.collectors.gpo_summary -and -not $SkipGpo }
$preflight = Test-AiBitPrerequisites -RequireGroupPolicy:$gpoEnabled
if($preflight.status -ne 'ok'){ throw ($preflight.errors -join ' ') }
Import-Module ActiveDirectory -ErrorAction Stop

$collectors = @()
$collectors += Invoke-AiBitCollector -Name 'forest' -Action {
    $f=Get-ADForest
    [ordered]@{ name=$f.Name; root_domain=$f.RootDomain; forest_mode=$f.ForestMode.ToString(); domains=@($f.Domains|Sort-Object); global_catalogs=@($f.GlobalCatalogs|Sort-Object); sites=@($f.Sites|Sort-Object); schema_master=$f.SchemaMaster; domain_naming_master=$f.DomainNamingMaster }
}
$collectors += Invoke-AiBitCollector -Name 'domains' -Action {
    @(Get-ADForest).Domains | Sort-Object | ForEach-Object { $d=Get-ADDomain -Identity $_; [ordered]@{ dns_root=$d.DNSRoot; netbios_name=$d.NetBIOSName; domain_mode=$d.DomainMode.ToString(); distinguished_name=$d.DistinguishedName; domain_sid=$d.DomainSID.Value; pdc_emulator=$d.PDCEmulator; rid_master=$d.RIDMaster; infrastructure_master=$d.InfrastructureMaster } }
}
$collectors += Invoke-AiBitCollector -Name 'domain_controllers' -Action {
    Get-ADDomainController -Filter * | Sort-Object HostName | ForEach-Object { [ordered]@{ hostname=$_.HostName; name=$_.Name; domain=$_.Domain; forest=$_.Forest; site=$_.Site; ipv4_address=$_.IPv4Address; operating_system=$_.OperatingSystem; operating_system_version=$_.OperatingSystemVersion; is_global_catalog=[bool]$_.IsGlobalCatalog; is_read_only=[bool]$_.IsReadOnly; enabled=[bool]$_.Enabled } }
}
$collectors += Invoke-AiBitCollector -Name 'organizational_units' -Action {
    Get-ADOrganizationalUnit -Filter * -Properties CanonicalName,ProtectedFromAccidentalDeletion | Sort-Object DistinguishedName | ForEach-Object { [ordered]@{ name=$_.Name; distinguished_name=$_.DistinguishedName; canonical_name=$_.CanonicalName; protected_from_accidental_deletion=[bool]$_.ProtectedFromAccidentalDeletion } }
}
if($gpoEnabled){
    $collectors += Invoke-AiBitCollector -Name 'gpo_summary' -Action {
        Import-Module GroupPolicy -ErrorAction Stop
        Get-GPO -All | Sort-Object DisplayName | ForEach-Object { [ordered]@{ id=$_.Id.Guid; display_name=$_.DisplayName; domain_name=$_.DomainName; owner=$_.Owner; gpo_status=$_.GpoStatus.ToString(); creation_time_utc=$_.CreationTime.ToUniversalTime().ToString('o'); modification_time_utc=$_.ModificationTime.ToUniversalTime().ToString('o'); user_version=$_.User.DSVersion; computer_version=$_.Computer.DSVersion } }
    }
}

$payload=[ordered]@{
    schema_version='1.0.0'; agent_version='6.2.0'; snapshot_id=[Guid]::NewGuid().Guid; collected_at_utc=[DateTime]::UtcNow.ToString('o')
    host=[ordered]@{ computer_name=$env:COMPUTERNAME; user_dns_domain=$env:USERDNSDOMAIN; user_domain=$env:USERDOMAIN; user_name=$env:USERNAME; powershell_version=$PSVersionTable.PSVersion.ToString() }
    preflight=$preflight; collectors=$collectors
}
$canonical = ConvertTo-AiBitCanonicalObject $payload
$canonicalJson = $canonical | ConvertTo-Json -Depth 20 -Compress
$snapshot=[ordered]@{ payload=$payload; fingerprint=[ordered]@{ algorithm='sha256'; value=(Get-AiBitSha256 $canonicalJson); canonicalization='sorted-properties-json-utf8-v1' } }
$json=$snapshot | ConvertTo-Json -Depth 20
$resolved=[System.IO.Path]::GetFullPath((Join-Path (Get-Location) $OutputPath))
$dir=Split-Path -Parent $resolved
if(-not(Test-Path $dir)){New-Item -ItemType Directory -Path $dir -Force|Out-Null}
[System.IO.File]::WriteAllText($resolved,$json,[System.Text.UTF8Encoding]::new($false))
if($PassThru){$snapshot}else{[ordered]@{status='ok';path=$resolved;snapshot_id=$payload.snapshot_id;fingerprint=$snapshot.fingerprint.value}|ConvertTo-Json}
