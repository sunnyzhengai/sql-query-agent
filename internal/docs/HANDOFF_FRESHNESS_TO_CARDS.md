# Handoff — freshness must reach the answer (Trust family, gap 2)

> **Status (2026-08-18, dev session): implemented in 1.19.0.**
> output_metric_logic carries logic_last_changed_at (hash-change vs the previous card table — the previous run IS the memory, no new state) and source_extracted_at (from ops_extraction_tracking; null on file-drop routes and the agent SAYS so). Agent instructions gained a trust-questions section (cite both dates; volunteer them when currency is questioned) — SUNNY: re-paste notebooks/delta_agent_instructions.md into the Data Agent. 09's Purview description gains a Freshness trailer. Staleness: config freshness.stale_after_days (default 30) checked in 06 — WARNING + ops_fallout rows (stage 06_freshness, reason stale_source), never a gate. 06's precondition now requires output_metric_logic (consistent with its run-02-04-first contract). 08/13 trailers deferred: their descriptions come from 07b text; add if wanted after field look.

**From:** review session, 2026-08-18 (Question Map, gap 2). **To:** dev
session. See docs/architecture/QUESTION_MAP.md.

## Finding

"When did this metric's logic last change? Is it stale?" is a Trust
question users will ask. The raw signal exists (extraction tracking
hashes; parse history; 12's extracted_at) but no card carries it —
output_metric_logic has no logic_last_changed / source_extracted_at, so
neither the agent nor publishers can answer or qualify trust.

## Wanted

1. Card columns on output_metric_logic: logic_last_changed_at (from
   hash-change detection across runs), source_extracted_at; contract +
   descriptions as usual.
2. Surfaced: agent instructions teach citing freshness; publishers
   (08/09/13) may include it in the description trailer where the
   catalog supports it.
3. Staleness policy hook: a config threshold (e.g. warn if source
   extraction older than N days) feeding the funnel/health family, not a
   hard gate.
