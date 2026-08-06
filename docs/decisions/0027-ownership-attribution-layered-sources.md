# 0027 — Ownership attribution: manual entry is the floor, Entra ID enriches

**Status:** Accepted
**Date:** 2026-08-06

## Context

Customers must see which developer owns the SQL and which business steward
owns the report logic — on the answer, not in a separate portal. The
plumbing already exists end to end (`sql_sources.developer/steward` →
canonical node properties → `output_metric_logic` → agent instructions);
what's undesigned is *population*. The feasibility pass
([OWNERSHIP_ATTRIBUTION.md](../development/OWNERSHIP_ATTRIBUTION.md),
verified against live Microsoft docs 2026-08-06) found: notebooks cannot
get Graph tokens as the notebook user (four fixed audiences only); Graph
lookups need a customer app registration with admin-consented application
permissions; SQL metadata does not record object creators; item ownership
is available via a **preview** admin API (`creatorPrincipal` with UPN) and
GA scanner APIs; commit authorship comes from the git provider's API with a
"committing identity ≈ who synced" caveat. Every automated signal has holes.

## Decision

**Attribution is layered, provenance is stored, and the manual layer is the
product contract.**

1. **Source precedence (highest wins):** (1) manual assignment — the
   steward-assignments pattern, extended to developers; (2) `org_config`
   pattern rules (e.g. schema/name-pattern → team); (3) Entra-derived
   signals via an optional enrichment adapter: admin-items
   `creatorPrincipal`, scanner-API owner, workspace roles, DevOps/GitHub
   per-item commit authorship. Automated signals **prefill and suggest**;
   they never overwrite a manual entry.
2. **Provenance is a column, not a vibe.** Wherever an owner lands
   (`developer`, `steward`), a companion `*_source` value records which
   layer produced it (`manual | config_rule | entra_creator | scanner |
   workspace_role | git_author`). The agent disclosure (ADR 0021) can then
   say "steward: J. Doe (assigned)" vs "developer: R. Roe (from commit
   history)" — attribution honesty mirrors certification honesty.
3. **Identity keys on Entra object id when available**, display name
   otherwise. Manual entries accept a bare name (the minimum bar — works
   with zero Entra permissions, zero admin consent); the enrichment
   adapter backfills object ids by Graph lookup where consented.
4. **Two-identity architecture.** Enrichment runs at pipeline time as an
   admin-consented service principal (MSAL client-credentials, secret in
   Key Vault) — an *optional adapter* in the ADR 0009 sense, with its
   prerequisites (app registration, `User.Read.All`,
   `GroupMember.Read.All`, admin consent) documented as a customer
   checklist. Ask-time identity is never required for attribution display;
   it arrives only implicitly via SQL passthrough and is reserved for the
   personal layer (ADR 0024) and usage events (ADR 0023).
5. **Preview APIs are suggestions-only.** `creatorPrincipal` comes from a
   preview admin API; it may populate the suggestion queue but the product
   must function fully without it (no production dependency on preview
   surfaces — 5-rule gate: supportable at a distance).

## Consequences

- Launch requirement is met with zero customer prerequisites: manual
  assignment through the existing `manage_stewards` path (extended to
  developers), visible in answers immediately.
- The enrichment adapter is a Pro-tier-shaped feature: measurable value
  (prefilled ownership across hundreds of procs), real prerequisites
  (admin consent), cleanly optional.
- `gov_steward_assignments` grows a sibling concept for developers plus
  `*_source` provenance columns — contract evolution to draft alongside
  the certification tables (ADRs 0021-0022) so ownership and certification
  land as one governance schema change.
- Git-authorship attribution inherits the "who synced" caveat; storing the
  source label makes that honesty visible instead of laundering a sync
  identity into an "owner."
