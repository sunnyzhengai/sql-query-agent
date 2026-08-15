# 0039 — Every error links to its contract: error-to-contract lineage

**Status:** Accepted
**Date:** 2026-08-15
**Extends:** 0026 (every error names its data)

## Context

ADR 0026 gave errors *data* lineage: an error row resolves to the metric
and objects it blocks. The 2026-08-15 silent-failure audit (66 findings,
`learning/audit-*.md`) showed the missing hop: most production failures
were not errors at all — they were **contract violations that nothing was
checking**: a blocking threshold silently absent from the readiness gate,
an append that became an overwrite, a required input table read through a
bare `except`. When such a failure did surface, the message described a
symptom, not the promise that was broken.

Sunny's operating philosophy (recorded 2026-08-15): failures have two
audiences. **State problems** (missing/empty/stale tables) must surface as
admin-actionable operational messages so customer admins self-serve. Raw
stack traces are reserved for true product defects, which route to the
vendor. And the same contract failing across multiple customers is a
product signal, not a customer-environment signal — which requires errors
to be *aggregatable by contract*.

## Decision

**Every error is a node linked back to the contract whose failure produced
it. The chain is error → contract → data.**

1. **Contracts have stable ids.** `src/steps/gates.py:contract_id()`
   derives `contract:<table_name>` from TABLE_REGISTRY. The registry entry
   IS the contract; the id is its citation handle. No new state to
   maintain, nothing to drift.

2. **Gates cite contracts.** `precondition_gate` (new, this ADR's
   companion implementation) and `postcondition_gate` failures carry the
   violated contract id, both in the operational message —

       [!] Preconditions failed for 03_build_graph:
           ops_parse_results missing — produced by 02_parse [contract:ops_parse_results]

   — and structurally (`StepPreconditionError.failures` is a list of
   `{table, problem, producer, contract_id}` dicts), so callers can log
   failures as events without re-parsing prose.

3. **Gates are derived, never hand-listed.** Required inputs come from
   each table's `consumers` list (excluding the step's self-reads of
   previous-run state and tables flagged `optional_input`); producers from
   `owner.notebook`; emptiness rules from `must_be_nonempty`. A gate that
   is a projection of the registry cannot drift from the contracts —
   drift was how the 06_validate gate silently shrank.

4. **The two-audience rule.** A gate failure is a STATE problem: its
   message names the fix ("run 02_parse") and the contract, and is safe to
   show a customer admin. Anything that still escapes as a stack trace is
   by definition a product defect and routes to the vendor. Every stack
   trace a gate could have prevented is a misfiled support ticket.

## Consequences

- Support triage becomes a query: group error events by `contract_id`
  across runs (and, at fleet scale, across customers). A contract that
  fails repeatedly everywhere is a product-improvement signal — the
  usage-flywheel applied to failures.
- Follow-up (planned, not yet built): persist gate failures as rows in the
  planned `ops_runtime_error_events` log (ADR 0026 item 2) with a
  `contract_id` column, and project contracts as graph nodes so
  error → contract → data is walkable inside the knowledge graph itself.
- The registry gains two small vocabulary items (`optional_input`,
  `must_be_nonempty`) that make previously-implicit operational knowledge
  declarative.

## Alternatives considered

- **Hand-maintained per-notebook required-table lists** — rejected: that
  list is a second source of truth and would rot exactly like the
  notebooks/README.md pipeline doc did.
- **A separate contracts store with its own ids** — rejected: the
  TABLE_REGISTRY already is the contract store; a parallel one recreates
  the two-implementations disease the audit catalogued.
