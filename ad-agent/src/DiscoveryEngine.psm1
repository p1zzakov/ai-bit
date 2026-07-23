Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Test-AIBitModule {
    param([Parameter(Mandatory=$true)][string]$Name)
    return [bool](Get-Module -ListAvailable -Name $Name | Select-Object -First 1)
}

function ConvertTo-AIBitCanonicalObject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false, ValueFromPipeline=$true)]
        [AllowNull()]
        $InputObject
    )

    process {
        if ($null -eq $InputObject) {
            return $null
        }

        if ($InputObject -is [System.Collections.IDictionary]) {
            $result = New-Object System.Collections.Specialized.OrderedDictionary
            $keys = @($InputObject.Keys | ForEach-Object { [string]$_ } | Sort-Object)
            foreach ($key in $keys) {
                $value = $InputObject.Item($key)
                $result.Add($key, (ConvertTo-AIBitCanonicalObject -InputObject $value))
            }
            return $result
        }

        if (($InputObject -is [System.Collections.IEnumerable]) -and -not ($InputObject -is [string])) {
            $items = New-Object System.Collections.ArrayList
            foreach ($item in $InputObject) {
                [void]$items.Add((ConvertTo-AIBitCanonicalObject -InputObject $item))
            }
            return @($items.ToArray())
        }

        if (($InputObject -is [System.Management.Automation.PSCustomObject]) -or
            ($InputObject.GetType().FullName -eq 'System.Management.Automation.PSCustomObject')) {
            $result = New-Object System.Collections.Specialized.OrderedDictionary
            $properties = @($InputObject.PSObject.Properties | Sort-Object Name)
            foreach ($property in $properties) {
                $result.Add($property.Name, (ConvertTo-AIBitCanonicalObject -InputObject $property.Value))
            }
            return $result
        }

        return $InputObject
    }
}

function Get-AIBitSha256 {
    param([Parameter(Mandatory=$true)][string]$Text)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join '')
    }
    finally {
        $sha.Dispose()
    }
}

function Import-AIBitCollectors {
    param([Parameter(Mandatory=$true)][string]$Path)
    $collectors = @()
    $files = Get-ChildItem -Path $Path -Filter '*.collector.ps1' | Where-Object { -not $_.PSIsContainer } | Sort-Object Name
    foreach ($file in @($files)) {
        $descriptor = & $file.FullName
        if (($null -eq $descriptor.Name) -or ($null -eq $descriptor.Collect)) {
            throw "Invalid collector descriptor: $($file.FullName)"
        }
        $descriptor.Source = $file.Name
        $collectors += ,$descriptor
    }
    return $collectors
}

function Invoke-AIBitCollector {
    param([Parameter(Mandatory=$true)]$Collector)
    $started = [DateTime]::UtcNow
    $requiredModules = @($Collector.RequiredModules)
    $missing = @($requiredModules | Where-Object { -not (Test-AIBitModule -Name $_) })

    if ($missing.Count -gt 0) {
        return [ordered]@{
            name = $Collector.Name
            version = $Collector.Version
            status = 'configuration_required'
            started_at_utc = $started.ToString('o')
            finished_at_utc = [DateTime]::UtcNow.ToString('o')
            source = $Collector.Source
            reason = ('Missing PowerShell module(s): ' + ($missing -join ', '))
            data = $null
        }
    }

    try {
        foreach ($module in $requiredModules) {
            Import-Module $module -ErrorAction Stop
        }
        $data = & $Collector.Collect
        return [ordered]@{
            name = $Collector.Name
            version = $Collector.Version
            status = 'ok'
            started_at_utc = $started.ToString('o')
            finished_at_utc = [DateTime]::UtcNow.ToString('o')
            source = $Collector.Source
            reason = $null
            data = $data
        }
    }
    catch {
        return [ordered]@{
            name = $Collector.Name
            version = $Collector.Version
            status = 'error'
            started_at_utc = $started.ToString('o')
            finished_at_utc = [DateTime]::UtcNow.ToString('o')
            source = $Collector.Source
            reason = $_.Exception.Message
            data = $null
        }
    }
}

function New-AIBitSnapshot {
    param(
        [Parameter(Mandatory=$true)][array]$Results,
        [string]$AgentVersion = '6.2.0'
    )

    $payload = [ordered]@{
        schema_version = '1.1'
        agent_version = $AgentVersion
        snapshot_id = [Guid]::NewGuid().Guid
        collected_at_utc = [DateTime]::UtcNow.ToString('o')
        host = [ordered]@{
            computer_name = $env:COMPUTERNAME
            user_domain = $env:USERDOMAIN
            user_name = $env:USERNAME
            powershell_version = $PSVersionTable.PSVersion.ToString()
            powershell_edition = if ($PSVersionTable.PSObject.Properties.Name -contains 'PSEdition') { $PSVersionTable.PSEdition } else { 'Desktop' }
            os = $env:OS
        }
        collectors = $Results
    }

    $canonical = ConvertTo-AIBitCanonicalObject -InputObject $payload
    $canonicalJson = $canonical | ConvertTo-Json -Depth 20 -Compress
    return [ordered]@{
        fingerprint_algorithm = 'sha256'
        fingerprint = Get-AIBitSha256 -Text $canonicalJson
        payload = $payload
    }
}

function Export-AIBitSnapshot {
    param(
        [Parameter(Mandatory=$true)]$Snapshot,
        [Parameter(Mandatory=$true)][string]$Path
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $directory = Split-Path -Parent $fullPath
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText(
        $fullPath,
        ($Snapshot | ConvertTo-Json -Depth 20),
        $utf8WithoutBom
    )
    return $fullPath
}

Export-ModuleMember -Function @(
    'Test-AIBitModule',
    'ConvertTo-AIBitCanonicalObject',
    'Get-AIBitSha256',
    'Import-AIBitCollectors',
    'Invoke-AIBitCollector',
    'New-AIBitSnapshot',
    'Export-AIBitSnapshot'
)
