# Handoff — split agent description generation out of 08

> **Status (2026-08-18, dev session): implemented in 1.15.0.**
> New step 07b_generate_agent_descriptions owns ops_agent_descriptions;
> logic lives in src/steps/agent_descriptions.py with 11 tests (plan,
> rejection heuristic, batch saves). Field notes designed in: rejected
> rows persist with status=rejected (queryable, retried next run, final
> summary names them); batch tallies flow through the progress callback
> while the final tally is a separate RunResult block; resume-by-rerun
> preserved via full-row-set saves. 08 is a pure publisher (hard stop
> with remediation if the table is absent); 13 overlays agent
> descriptions when present and falls back to 07 graph descriptions —
> deliberately optional there so the demo path needs no Data Agent
> (verdict recorded here, not just in conversation). Also this pass:
> devops_lineage.py retired (superseded by 12), empty data_loading/
> removed, root-utilities constraint documented, guide-coverage tests
> widened to lettered notebooks (07b/00a-e now enforced).

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
