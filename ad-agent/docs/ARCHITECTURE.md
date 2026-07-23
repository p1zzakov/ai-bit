# AI-BIT Discovery Engine 6.2 — Architecture

## Purpose

AI-BIT Discovery Engine is a read-only plugin platform for collecting reproducible infrastructure evidence. Active Directory is the first provider, not a hard-coded product boundary.

## Pipeline

```text
Environment check
      ↓
Collector plugin
      ↓
Raw evidence
      ↓
Normalizer
      ↓
Snapshot builder
      ↓
Canonical JSON
      ↓
SHA-256 fingerprint
      ↓
File output / future transport
```

## Principles

1. Windows PowerShell 5.1 is the compatibility baseline.
2. Collectors must not mutate managed systems.
3. Missing capability is `configuration_required`, not a fabricated defect.
4. One collector failure must not destroy other evidence.
5. Every collector result is independently timestamped and traceable.
6. Fingerprints cover normalized payload only.
7. Transport is outside collector responsibility.

## Collector contract

Each collector is a `.ps1` plugin returning a descriptor:

```powershell
@{
    Name = 'forest'
    Version = '1.0.0'
    RequiredModules = @('ActiveDirectory')
    Collect = { ... }
}
```

The `Collect` scriptblock returns JSON-compatible read-only evidence.

## Result states

- `ok` — evidence collected;
- `configuration_required` — required module, permission or endpoint unavailable;
- `error` — collector executed but failed;
- `skipped` — explicitly disabled.

Unknown is never treated as missing.

## Sprint 1 boundary

Sprint 1 includes:

- plugin discovery;
- environment and dependency checks;
- Forest, Domains, Domain Controllers, Organizational Units and GPO plugins;
- evidence normalization;
- snapshot construction;
- SHA-256 fingerprint;
- PowerShell 5.1-compatible runner;
- offline and live validation.

Windows Service, scheduler, mTLS, MCP transport, DNS, DHCP, replication, SYSVOL and Event Log remain outside Sprint 1.