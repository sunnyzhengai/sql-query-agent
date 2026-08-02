# ADR 0008: Ship Tier 1 (Core Agent) First

**Status:** Accepted
**Date:** 2026-07-25 (extracted from MARKETPLACE_PIVOT.md D1)

## Context

Three product tiers exist: Core Agent (metadata Q&A), Governance Sync
(Collibra/Purview push), and Active Data Agent (dynamic SQL execution). Waiting
for all three delays listing.

## Decision

List the Core Metadata & Semantic Q&A agent on Marketplace as Tier 1. Build
Governance Sync (Tier 2) and Dynamic SQL Execution (Tier 3) as add-on modules
after listing.

## Consequences

- Fastest path to revenue and market validation; Tier 1 has the widest market
  (any org with SQL sources in Fabric)
- Tier 2 requires per-tool integration work that would block the broad product
- Tier 3 introduces security/compliance complexity that could delay certification
- Marketplace listing describes Tier 1; roadmap mentions Tiers 2–3 as upcoming
