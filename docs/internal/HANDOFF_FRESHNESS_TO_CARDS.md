# Handoff — freshness must reach the answer (Trust family, gap 2)

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
