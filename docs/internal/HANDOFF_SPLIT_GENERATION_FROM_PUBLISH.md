# Handoff — split agent description generation out of 08

**From:** review session, 2026-08-18 (Sunny, mid-work-deployment: "if 08
is about Collibra, why is generation in this notebook? shouldn't it be
independent?"). **To:** dev session. Confirms audit finding #37
(notebooks with real untested logic — 08 is the worst offender).

## Wanted

1. New numbered step in the descriptions family (e.g. 07b or renumber —
   see naming principle in HANDOFF_INGESTION_ROUTES): Data-Agent
   description generation. Owns ops_agent_descriptions. Logic moves to
   src/steps (reject-phrases heuristic, hash-based needs_generation,
   incremental save batching) with tests; notebook becomes a thin driver.
   Precondition gate derives from the registry as usual.
2. 08 (Collibra), 13 (PBI) become pure publishers consuming
   ops_agent_descriptions — no generation capability at all. A customer
   wanting only PBI write-back never touches a Collibra notebook.
3. Field notes from the 2026-08-18 work run to preserve in the design:
   - the cumulative failed-counter confused a real operator — per-batch
     AND final tallies should be visually distinct;
   - REJECTED (agent non-answer) rows should persist somewhere queryable
     (they currently exist only in stdout — same stdout-state disease);
     suggested: ops_agent_descriptions row with status=rejected, so
     retry/inspection is a query, and the generation step can report
     "N rejected, here are the metric_ids" at the end.
   - session died overnight after the 1h run; resume-by-rerun worked
     exactly as designed (cache skipped 626/627) — keep that property.
