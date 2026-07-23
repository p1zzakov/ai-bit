# AI-BIT Enterprise 6.2 — Active Directory Discovery Agent

Read-only Windows agent foundation for evidence-based Active Directory discovery.

## Scope of Sprint 1

- collect forest and domain metadata;
- discover domain controllers;
- enumerate organizational units;
- collect Group Policy Object summaries;
- normalize collector output into a versioned snapshot;
- keep collection strictly read-only;
- prepare transport integration with the AI-BIT Evidence Engine.

## Safety model

The agent does not modify Active Directory, Group Policy, DNS, DHCP, SYSVOL, registry policy, users, groups, computers, or domain controllers. PowerShell collectors must use read-only commands and return JSON-compatible objects.

## Planned layout

```text
ad-agent/
├── collectors/
├── config/
├── schemas/
├── src/
└── tests/
```

## Initial snapshot contract

Every snapshot contains:

- `schema_version`;
- `agent_version`;
- `snapshot_id`;
- UTC collection timestamps;
- collector status and errors;
- normalized forest, domain, DC, OU and GPO data;
- SHA-256 fingerprint of the canonical payload.

## Requirements

- Windows Server 2019 or newer;
- PowerShell 5.1 or PowerShell 7;
- ActiveDirectory PowerShell module;
- GroupPolicy PowerShell module for GPO collection;
- domain account with delegated read-only access.

## Status

Version 6.2.0 foundation started. Production service installation and MCP transport are not implemented yet.
