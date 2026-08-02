# ADR 0015: metric_id Is the Universal Identity — Consumers Must Propagate It

**Status:** Accepted
**Date:** 2026-08-02

## Context

Metric identity is `metric_id = "<schema>.<object_name>"`, extracted from the
CREATE/ALTER statement (never the filename) and unique by contract in
`input_sql_sources`. But bare object names are NOT unique — the same proc or
view name legitimately exists in multiple schemas. A real-world Purview
catalog showed the failure mode: two assets with the same display name and
no way to tell which schema's object each described.

Our own Purview publisher had the same flaw in miniature: it keyed entities
correctly (`qualifiedName = metric_id`) but displayed the bare
`metric_name`, so same-named metrics looked identical in the browse view.

## Decision

`metric_id` is the only durable identity for a metric, everywhere:

1. Every consumer that projects metrics into another system (Purview,
   Collibra, Power BI descriptions, exports) MUST use `metric_id` as its
   durable key (e.g., Purview `qualifiedName`).
2. Any display name a consumer shows MUST be traceable to `metric_id` at a
   glance. Until business-friendly names exist, the display name IS
   `metric_id` (schema-qualified).
3. Business-friendly display names are a planned feature fed by Power BI
   lineage — which supplies genuinely distinct names — and even then the
   `metric_id` remains the key underneath.

## Consequences

- Same-named objects in different schemas are always distinguishable, in
  every downstream system, without opening asset details
- Catalog re-publishes are idempotent: the durable key never changes when a
  display name does
- Consumers joining data back (e.g., description sync, lineage matching)
  join on `metric_id`, never on names
- The obligation is recorded in the contract preamble (`src/schemas.py`);
  new adapters inherit it as a review checklist item
