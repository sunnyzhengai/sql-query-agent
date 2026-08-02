# ADR 0011: Static Install Guide for v1; AI Co-Pilot Deferred to v2

**Status:** Accepted
**Date:** 2026-07-25 (extracted from MARKETPLACE_PIVOT.md D4 + D5)

## Context

An AI-powered installation/troubleshooting co-pilot is effectively a second
product — months of work — and with zero customers there is no data on what
actually breaks during installation.

## Decision

Ship v1 with a written step-by-step guide (`docs/deployment/INSTALLATION_GUIDE.md`).
Build the co-pilot after 3+ customers reveal real support patterns.

Meanwhile, capture customer-facing operational decisions now, in structured
markdown (this `docs/decisions/` directory), so they become the co-pilot's raw
material later.

**Filter test for what to record:** "If a system admin encounters an error, does
knowing this decision help resolve it?" If yes → document. Internal engineering
choices that don't affect operators are summarized in ARCHITECTURE.md instead.

## Consequences

- A static guide is what every enterprise product ships with at v1
- Decisions are freshest when made — recording them now makes future graph
  ingestion trivial (the co-pilot will eat AIVIA's own dogfood)
