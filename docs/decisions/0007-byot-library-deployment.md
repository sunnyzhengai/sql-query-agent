# ADR 0007: BYOT Deployment as a Python Library (.whl)

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

The product could be a hosted SaaS (customer data flows to AIVIA infrastructure)
or run entirely inside the customer's environment. Target buyers (healthcare,
finance) have hard data-sovereignty requirements.

## Decision

Ship a Python wheel installed into the customer's own Microsoft Fabric tenant
(Bring Your Own Tenant). No AIVIA-hosted servers, databases, or APIs touch
customer data. Identity is the customer's Entra ID; secrets live in their Key
Vault; RBAC is inherited from Fabric workspace roles.

## Consequences

- The security story is delegation: SOC 2 via Fabric, HIPAA via "we process SQL
  logic, not data" — no BAA required (customer's Microsoft BAA covers Fabric)
- Customer pays for Fabric compute; AIVIA charges for the library license
- Updates are customer-managed (.whl upgrades) — no forced rollout channel
- An Azure Managed Application (ARM/Bicep one-click deploy) remains a future
  packaging option once the customer base outgrows notebook-based install
