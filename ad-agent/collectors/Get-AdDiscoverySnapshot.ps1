[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "./data/snapshots/ad-snapshot.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Collector {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    $startedAt = [DateTime]::UtcNow
    try {
        $data = & $Action
        return [ordered]@{
            name = $Name
            status = "ok"
            started_at_utc = $startedAt.ToString("o")
            finished_at_utc = [DateTime]::UtcNow.ToString("o")
            error = $null
            data = $data
        }
    }
    catch {
        return [ordered]@{
            name = $Name
            status = "error"
            started_at_utc = $startedAt.ToString("o")
            finished_at_utc = [DateTime]::UtcNow.ToString("o")
            error = $_.Exception.Message
            data = $null
        }
    }
}

Import-Module ActiveDirectory -ErrorAction Stop

$collectors = @()

$collectors += Invoke-Collector -Name "forest" -Action {
    $forest = Get-ADForest
    [ordered]@{
        name = $forest.Name
        root_domain = $forest.RootDomain
        forest_mode = $forest.ForestMode.ToString()
        domains = @($forest.Domains)
        global_catalogs = @($forest.GlobalCatalogs)
        sites = @($forest.Sites)
        schema_master = $forest.SchemaMaster
        domain_naming_master = $forest.DomainNamingMaster
    }
}

$collectors += Invoke-Collector -Name "domains" -Action {
    Get-ADForest | Select-Object -ExpandProperty Domains | ForEach-Object {
        $domain = Get-ADDomain -Identity $_
        [ordered]@{
            dns_root = $domain.DNSRoot
            netbios_name = $domain.NetBIOSName
            domain_mode = $domain.DomainMode.ToString()
            distinguished_name = $domain.DistinguishedName
            domain_sid = $domain.DomainSID.Value
            pdc_emulator = $domain.PDCEmulator
            rid_master = $domain.RIDMaster
            infrastructure_master = $domain.InfrastructureMaster
        }
    }
}

$collectors += Invoke-Collector -Name "domain_controllers" -Action {
    Get-ADDomainController -Filter * | ForEach-Object {
        [ordered]@{
            hostname = $_.HostName
            name = $_.Name
            domain = $_.Domain
            forest = $_.Forest
            site = $_.Site
            ipv4_address = $_.IPv4Address
            operating_system = $_.OperatingSystem
            operating_system_version = $_.OperatingSystemVersion
            is_global_catalog = [bool]$_.IsGlobalCatalog
            is_read_only = [bool]$_.IsReadOnly
            enabled = [bool]$_.Enabled
        }
    }
}

$collectors += Invoke-Collector -Name "organizational_units" -Action {
    Get-ADOrganizationalUnit -Filter * -Properties ProtectedFromAccidentalDeletion | ForEach-Object {
        [ordered]@{
            name = $_.Name
            distinguished_name = $_.DistinguishedName
            canonical_name = $_.CanonicalName
            protected_from_accidental_deletion = [bool]$_.ProtectedFromAccidentalDeletion
        }
    }
}

$collectors += Invoke-Collector -Name "gpo_summary" -Action {
    Import-Module GroupPolicy -ErrorAction Stop
    Get-GPO -All | ForEach-Object {
        [ordered]@{
            id = $_.Id.Guid
            display_name = $_.DisplayName
            domain_name = $_.DomainName
            owner = $_.Owner
            gpo_status = $_.GpoStatus.ToString()
            creation_time_utc = $_.CreationTime.ToUniversalTime().ToString("o")
            modification_time_utc = $_.ModificationTime.ToUniversalTime().ToString("o")
            user_version = $_.User.DSVersion
            computer_version = $_.Computer.DSVersion
        }
    }
}

$snapshot = [ordered]@{
    schema_version = "1.0"
    agent_version = "6.2.0"
    snapshot_id = [Guid]::NewGuid().Guid
    collected_at_utc = [DateTime]::UtcNow.ToString("o")
    host = [ordered]@{
        computer_name = $env:COMPUTERNAME
        user_domain = $env:USERDOMAIN
        user_name = $env:USERNAME
        powershell_version = $PSVersionTable.PSVersion.ToString()
    }
    collectors = $collectors
}

$json = $snapshot | ConvertTo-Json -Depth 12
$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) $OutputPath),
    $json,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Output $json
