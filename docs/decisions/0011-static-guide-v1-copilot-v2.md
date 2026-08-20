# ADR 0011: Static Install Guide for v1; AI Co-Pilot Deferred to v2

**Status:** Accepted — amended 2026-08-20 (trigger changed, see Amendment)
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

## Amendment (2026-08-20, Sunny's verdict — HANDOFF_TRACE_AND_ADMIN_GRAPH)

**The co-pilot no longer waits for customers.** The original reasoning —
"no data on what breaks until 3+ customers" — predates the contract
regime. The contracts now DEFINE what a working system is: every step's
required inputs, outputs, gates, and escalations are enumerated and
mechanically checked (ADR 0039, 0042, 0045; the notebook and table
registries). That is the data the co-pilot needed.

**Trigger changes from "3+ customers" to "admin graph projected"** (see
ADR 0048): once the registries, contracts, trace lineages, and error
events are projected as one walkable graph, the companion is built on
it. Field data from real customers still enriches the residue OUTSIDE
the contract frontier — environment and tenant quirks — through the
existing installation-error signature-census channel; it stops being
the gate for building the companion at all.

The filter test above stands unchanged, and the decision corpus it
produced is now literally the companion's grounding material — the
dogfood consequence, realized.
