# 0023 — Usage is governance: the usage-weighted flywheel

**Status:** Accepted
**Date:** 2026-08-06

## Context

ADR 0005 promised that "every refusal feeds the flywheel," and an early
`UsageTracker` implemented query-event tracking before being removed in the
dead-code purge (it bent the graph model — user nodes squatting on the
canonical layer, `queried_by` edges reusing `canonical_to_transform`). The
ROADMAP flags the gap: no usage columns or tables in the registry, no
certify/reject interaction on answers. Meanwhile ADR 0021 removes the
certification gate, which raises the question it answers itself: if
certification doesn't ration availability, what allocates steward
attention? Usage does.

## Decision

**Every interaction is an append-only event; all weights are derived.**

1. **`gov_usage_events`** (contract draft, `src/schemas.py`): one row per
   agent interaction — asker, timestamp, question, resolved `metric_id`
   (null on refusal), outcome (`answered` / `refused`), and answer feedback
   (`confirmed` / `rejected` / `none`). Append-only; the event log is the
   ground truth and every aggregate is recomputable from it.
2. **Usage weight is a derived column, not a counter.** The pipeline (03)
   aggregates events into `usage_weight`, `last_queried`, `asker_count` on
   canonical nodes → `output_metric_logic` → answer disclosure ("asked 214
   times by 31 people" is itself a trust signal, per ADR 0021). No
   in-place increments — the purged `UsageTracker`'s mistake was mutating
   graph state per query; graph writes stay pipeline-owned (single-writer
   contracts).
3. **The steward queue is ordered by demand, never guarded by it.** Queue
   priority = f(usage weight, refusal frequency, feedback rejections,
   stale-certification drift per ADR 0022). Stewards work the top of a
   demand-sorted list; there are no SLAs, no expiry, no auto-gates on
   unworked items (ADR 0021 constitution).
4. **Refusals are demand signals for definitions that don't exist yet.**
   A refused question is an event with `metric_id = null` and the question
   text preserved — clustered by similarity, these become the "most-wanted
   definitions" queue (the Path B promise of ADR 0005, now with a table).
5. **Answer feedback closes the loop.** `confirmed` / `rejected` on an
   answer is the cheapest certification signal in the system: repeated
   confirms raise a draft metric's priority for formal certification;
   rejects on a certified metric flag it for steward re-review. Users
   govern by using; stewards ratify.

Users appear in events (and later, personal definitions per ADR 0024) —
they are **not** graph nodes. The graph stays a knowledge structure; demand
lives beside it.

## Consequences

- The flywheel is now mechanical: usage → weight → queue order → certified
  coverage where it matters → more trust → more usage.
- Event capture needs an ingestion point from the Data Agent conversation
  surface (Fabric-side wiring; the contract defines the shape now so the
  capture mechanism has a fixed target).
- Privacy: events carry user identity (needed for asker_count, ADR 0024
  layers, and ownership attribution). The whitepaper's data-handling
  section must cover interaction logs; deployments can pseudonymize
  `user_id` without breaking the aggregates.
- Aggregation joins the pipeline as a cheap step; recomputability from the
  event log means weights survive graph rebuilds (overwrite-safe).
