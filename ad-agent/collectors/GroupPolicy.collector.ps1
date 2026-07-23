@{
    Name='gpo_summary'; Version='1.0.0'; RequiredModules=@('GroupPolicy')
    Collect={
        Get-GPO -All | ForEach-Object {
            [ordered]@{id=$_.Id.Guid;display_name=$_.DisplayName;domain_name=$_.DomainName;owner=$_.Owner;gpo_status=$_.GpoStatus.ToString();creation_time_utc=$_.CreationTime.ToUniversalTime().ToString('o');modification_time_utc=$_.ModificationTime.ToUniversalTime().ToString('o');user_version=$_.User.DSVersion;computer_version=$_.Computer.DSVersion}
        }
    }
}