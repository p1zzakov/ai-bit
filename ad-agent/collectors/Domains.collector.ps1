@{
    Name='domains'; Version='1.0.0'; RequiredModules=@('ActiveDirectory')
    Collect={
        @(Get-ADForest).Domains | ForEach-Object {
            $domain=Get-ADDomain -Identity $_
            [ordered]@{dns_root=$domain.DNSRoot;netbios_name=$domain.NetBIOSName;domain_mode=$domain.DomainMode.ToString();distinguished_name=$domain.DistinguishedName;domain_sid=$domain.DomainSID.Value;pdc_emulator=$domain.PDCEmulator;rid_master=$domain.RIDMaster;infrastructure_master=$domain.InfrastructureMaster}
        }
    }
}