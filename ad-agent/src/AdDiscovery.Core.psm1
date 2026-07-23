Set-StrictMode -Version Latest

function Get-AiBitSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
}

function ConvertTo-AiBitCanonicalObject {
    [CmdletBinding()]
    param([Parameter(Mandatory, ValueFromPipeline)]$InputObject)
    process {
        if ($null -eq $InputObject) { return $null }
        if ($InputObject -is [string] -or $InputObject.GetType().IsPrimitive -or $InputObject -is [datetime] -or $InputObject -is [guid]) { return $InputObject }
        if ($InputObject -is [System.Collections.IDictionary]) {
            $ordered = [ordered]@{}
            foreach ($key in @($InputObject.Keys | Sort-Object)) { $ordered[$key] = ConvertTo-AiBitCanonicalObject $InputObject[$key] }
            return $ordered
        }
        if ($InputObject -is [System.Collections.IEnumerable]) {
            return @($InputObject | ForEach-Object { ConvertTo-AiBitCanonicalObject $_ })
        }
        $properties = [ordered]@{}
        foreach ($property in @($InputObject.PSObject.Properties.Name | Sort-Object)) { $properties[$property] = ConvertTo-AiBitCanonicalObject $InputObject.$property }
        return $properties
    }
}

function Invoke-AiBitCollector {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Name,[Parameter(Mandatory)][scriptblock]$Action)
    $startedAt = [DateTime]::UtcNow
    try {
        $data = & $Action
        [ordered]@{ name=$Name; status='ok'; started_at_utc=$startedAt.ToString('o'); finished_at_utc=[DateTime]::UtcNow.ToString('o'); error=$null; data=$data }
    } catch {
        [ordered]@{ name=$Name; status='error'; started_at_utc=$startedAt.ToString('o'); finished_at_utc=[DateTime]::UtcNow.ToString('o'); error=[ordered]@{ type=$_.Exception.GetType().FullName; message=$_.Exception.Message }; data=$null }
    }
}

function Test-AiBitPrerequisites {
    [CmdletBinding()]
    param([switch]$RequireGroupPolicy)
    $required = @('ActiveDirectory')
    if ($RequireGroupPolicy) { $required += 'GroupPolicy' }
    $modules = foreach ($name in $required) {
        $found = Get-Module -ListAvailable -Name $name | Select-Object -First 1
        [ordered]@{ name=$name; available=[bool]$found; version=if($found){$found.Version.ToString()}else{$null} }
    }
    $failed = @($modules | Where-Object { -not $_.available })
    [ordered]@{
        status = if($failed.Count -eq 0){'ok'}else{'error'}
        powershell_version = $PSVersionTable.PSVersion.ToString()
        is_windows = [bool]$IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop'
        domain_joined = -not [string]::IsNullOrWhiteSpace($env:USERDNSDOMAIN)
        modules = $modules
        errors = @($failed | ForEach-Object { "Required module '$($_.name)' is not available." })
    }
}

Export-ModuleMember -Function Get-AiBitSha256,ConvertTo-AiBitCanonicalObject,Invoke-AiBitCollector,Test-AiBitPrerequisites
