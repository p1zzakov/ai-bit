# AI-BIT Enterprise 6.2 — Discovery Engine / Sprint 1

Read-only plugin foundation for evidence-based infrastructure discovery. Active Directory is the first provider.

## Architecture

See `docs/ARCHITECTURE.md`.

```text
Environment → Collector plugin → Raw evidence → Normalizer → Snapshot → SHA-256
```

Compatibility baseline: Windows PowerShell 5.1. The engine does not use `$IsWindows` or PowerShell 7-only syntax.

## Delivered

- universal collector plugin contract;
- automatic collector discovery;
- dependency checks per collector;
- states `ok`, `configuration_required`, `error`, `skipped`;
- Forest, Domains, Domain Controllers, OU and GPO plugins;
- isolated collector failures;
- normalized versioned snapshot `1.1`;
- deterministic canonicalization;
- SHA-256 fingerprint;
- offline engine tests;
- live AD collection runner.

## Requirements

- Windows PowerShell 5.1 or newer;
- domain connectivity for live collection;
- ActiveDirectory module for AD plugins;
- GroupPolicy module for the GPO plugin;
- read-only domain permissions.

The engine does not require `Install-WindowsFeature`. It only checks whether modules are already available.

## Quick start

```powershell
cd C:\AI-BIT\ad-agent
Set-ExecutionPolicy -Scope Process Bypass

.\tests\Invoke-OfflineTests.ps1

.\collectors\Get-AdDiscoverySnapshot.ps1 `
  -OutputPath .\data\snapshots\ad-snapshot.json
```

Run only selected plugins:

```powershell
.\collectors\Get-AdDiscoverySnapshot.ps1 `
  -IncludeCollector forest,domains,domain_controllers
```

Exclude GPO:

```powershell
.\collectors\Get-AdDiscoverySnapshot.ps1 `
  -ExcludeCollector gpo_summary
```

Missing modules do not crash the snapshot. The affected collector returns `configuration_required` with a reason.

## Expected collector result

```json
{
  "name": "forest",
  "version": "1.0.0",
  "status": "ok",
  "source": "Forest.collector.ps1",
  "reason": null,
  "data": {}
}
```

## Out of scope

Windows Service, scheduler, mTLS, MCP transport, DNS, DHCP, replication, SYSVOL, Event Log and server-side ingestion remain outside Sprint 1.