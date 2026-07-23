@{
    Name='forest'; Version='1.0.0'; RequiredModules=@('ActiveDirectory')
    Collect={
        $forest=Get-ADForest
        [ordered]@{name=$forest.Name;root_domain=$forest.RootDomain;forest_mode=$forest.ForestMode.ToString();domains=@($forest.Domains);global_catalogs=@($forest.GlobalCatalogs);sites=@($forest.Sites);schema_master=$forest.SchemaMaster;domain_naming_master=$forest.DomainNamingMaster}
    }
}