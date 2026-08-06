# 0024 — Layered truth: personal definitions beside enterprise definitions

**Status:** Accepted
**Date:** 2026-08-06

## Context

Real organizations run on two kinds of truth: the enterprise definition
(what Finance certifies "readmission rate" to mean) and the working
definitions individuals actually use ("readmissions, but excluding planned
returns, because that's what my service line reports"). Governance systems
that admit only enterprise truth push personal definitions into
spreadsheets where they are invisible, unversioned, and ungovernable. The
design input for this pass: "Each user may hold their own definition that
is true to them, alongside enterprise-level definitions. A true governance
system supports both."

## Decision

**Two scopes, one lifecycle, explicit disclosure.**

1. **`gov_personal_definitions`** (contract draft, `src/schemas.py`): a
   user-owned definition — owner identity, name, plain-language definition,
   optional SQL fragment, optional `metric_id` link when it forks an
   enterprise metric, timestamps, and a promotion status. Personal
   definitions live beside the graph, not in it: canonical nodes stay
   enterprise-scoped, and the resolution layer consults both sources.
2. **Resolution discloses scope, never silently substitutes.** When the
   asker owns a personal definition matching their question, the agent
   answers from it *labeled as personal* ("your definition") and states
   whether an enterprise definition also exists — and vice versa: if a
   personal fork of an enterprise metric exists, the enterprise answer
   notes "you have a personal variant of this metric." A user's personal
   definitions are visible only to their owner; enterprise remains the
   default scope for everyone else.
3. **Personal definitions never gate and are never gated** (ADR 0021
   applies at both layers): creating one requires no approval, and holding
   one doesn't block the enterprise answer.
4. **Promotion is the flywheel's second gear.** Personal definitions are
   demand signals with logic attached: when several users hold similar
   personal definitions, or one accumulates usage, it surfaces in the
   steward queue (ADR 0023 priority function) as a promotion candidate.
   Promotion runs the standard certification path (ADR 0004) and pins a
   version (ADR 0022); the personal definition records what it was
   promoted into, and its owner gets attribution as the definition's
   originating developer (ownership attribution design).

## Consequences

- The spreadsheet-shadow-IT loop inverts: personal definitions become the
  *intake funnel* for enterprise certification instead of its competitor —
  bottom-up vocabulary building, consistent with how the corpus itself was
  ingested (existing SQL first, certification after).
- Same-name conflicts between personal and enterprise definitions are
  resolved by scope + disclosure, not by uniqueness rules; the
  inconsistency-detection bonus of ADR 0019 (same-name-different-logic)
  extends across layers and feeds the steward queue.
- Resolution (ADR 0017) gains a per-asker input: the asker's identity
  selects which personal layer to consult. This is the same identity
  plumbing ownership attribution and usage events need (one Entra ID
  dependency, three consumers).
- Row-level security posture: personal definitions are the first
  user-private data in the lakehouse; the whitepaper and RLS design must
  cover them.
