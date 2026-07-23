# AI-BIT Enterprise 6.2 — AD Discovery Agent / Sprint 1

Read-only foundation for evidence-based Active Directory discovery.

## Sprint 1 delivered

- prerequisite validation for ActiveDirectory and GroupPolicy modules;
- read-only collection of Forest, Domains, Domain Controllers, OU and GPO summaries;
- isolated collector failures;
- versioned JSON snapshot contract;
- deterministic canonicalization and SHA-256 fingerprint;
- JSON Schema 2020-12;
- offline validation script;
- live validation script for a domain-connected Windows host.

## Requirements

Windows Server 2019+ or Windows 10/11 with RSAT, Windows PowerShell 5.1 or PowerShell 7, and a domain account with read permissions. No write cmdlets are used.

## Quick start

```powershell
cd C:\AI-BIT\ad-agent
Copy-Item .\config\agent.example.json .\config\agent.json
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\Invoke-Preflight.ps1
.\collectors\Get-AdDiscoverySnapshot.ps1 -OutputPath .\data\snapshots\ad-snapshot.json
.\scripts\Invoke-Sprint1Validation.ps1
```

Without Group Policy tools:

```powershell
.\scripts\Invoke-Preflight.ps1 -SkipGpo
.\collectors\Get-AdDiscoverySnapshot.ps1 -SkipGpo
```

Offline validation on a non-domain machine:

```powershell
.\scripts\Invoke-Sprint1Validation.ps1 -SkipLiveCollection
```

## Expected output

The snapshot contains `payload` and `fingerprint`. Each collector returns `ok` or `error`; one failed collector does not erase evidence from successful collectors.

## Out of scope for Sprint 1

Windows Service, scheduler, mTLS transport, MCP upload, DNS/DHCP/replication/SYSVOL/Event Log collectors and server-side Evidence Engine ingestion.
