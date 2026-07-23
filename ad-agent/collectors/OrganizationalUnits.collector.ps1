@{
    Name='organizational_units'; Version='1.0.0'; RequiredModules=@('ActiveDirectory')
    Collect={
        Get-ADOrganizationalUnit -Filter * -Properties ProtectedFromAccidentalDeletion | ForEach-Object {
            [ordered]@{name=$_.Name;distinguished_name=$_.DistinguishedName;canonical_name=$_.CanonicalName;protected_from_accidental_deletion=[bool]$_.ProtectedFromAccidentalDeletion}
        }
    }
}