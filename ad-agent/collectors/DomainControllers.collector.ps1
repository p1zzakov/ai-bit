@{
    Name='domain_controllers'; Version='1.0.0'; RequiredModules=@('ActiveDirectory')
    Collect={
        Get-ADDomainController -Filter * | ForEach-Object {
            [ordered]@{hostname=$_.HostName;name=$_.Name;domain=$_.Domain;forest=$_.Forest;site=$_.Site;ipv4_address=$_.IPv4Address;operating_system=$_.OperatingSystem;operating_system_version=$_.OperatingSystemVersion;is_global_catalog=[bool]$_.IsGlobalCatalog;is_read_only=[bool]$_.IsReadOnly;enabled=[bool]$_.Enabled}
        }
    }
}