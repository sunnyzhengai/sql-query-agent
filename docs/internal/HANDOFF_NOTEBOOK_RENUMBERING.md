# Handoff — full renumbering: century phases, true ordering (SUPERSEDES the minimal verdict)

> **2026-08-18, later same day:** Sunny overruled the minimal proposal —
> "this time really consider the best ordering, don't preserve current
> numbers; 100-intervals for insertion room." Full scheme below replaces
> the 12→00f-only plan. Land in the same release window as the work sync
> (work re-pastes once; the only cheap window pre-Marketplace).

## The scheme (3 digits; century = phase; lexicographic sort = run order)

    0xx ACQUIRE (peer routes): 010 sql_filedrop, 020 sql_folders,
        030 sql_live, 040 dict_clarity, 050 dict_caboodle,
        060 ingest_semantic_models (was 12 — the misfile)
    100 VERIFY (was 01)
    200 PARSE (02) | 300 GRAPH (03) | 400 CARDS (04)
    500 VALIDATE (06) — gate before LLM spend
    600 DESCRIBE (07) | 610 AGENT DESCRIPTIONS (07b)
    700 INDEX (11)
    800 PROJECT/EXPORT (05) — THE ordering fix: export runs AFTER
        descriptions, eliminating the documented "re-run 05 after 07"
        double-run workaround
    900 PUBLISH collibra (08) | 910 purview (09) | 920 pbi_writeback (13)
    950 OPS ingest_agent_events (10)

## Migration notes beyond the original checklist

- Fabric git treats folder rename as delete+create: home workspace items
  get NEW ids — re-point any Data Pipeline activities; work side is free
  (full re-paste in the sync).
- Registry families/serves and generated maps absorb most references;
  gate step-name strings and registry owner/consumer fields need the
  sweep; historical handoffs keep old numbers with a mapping note.
- INSTALLATION_GUIDE run-order sections regenerate; the "re-run 05 after
  07" instruction is DELETED (that's the point).

## Original (superseded) minimal verdict follows for the record


**From:** review session, 2026-08-18 (Sunny, pre-sync: "does our
numbering need revamping?"). **To:** dev session.

## Verdict proposed

1. **12_ingest_semantic_models → 00f_ingest_semantic_models.** It is
   acquisition by the standing principle (number the derivation, letter
   the acquisition — HANDOFF_INGESTION_ROUTES), must run BEFORE 03, and
   its current number actively misleads run order (bit Sunny twice in
   one week; will bite customer admins silently). Sequencing: land in
   the same release window as Sunny's work sync so the work-side
   re-paste happens once.
2. **No further renumbering.** 07b is a legitimate family letter;
   publisher non-contiguity (08/09/13) and the 05/06 order are cosmetic;
   order is enforced by gates on state and documented by the notebook
   registry (families + serves, 1.18) — numbers are documentation only,
   and only the untrue one is worth churn.

## Cascade checklist for item 1 (scope honestly before committing)

- Folder + item rename; notebook registry entry (step_name, family);
  REQUIRES_ENGINE untouched.
- Every string reference: gates step names if any cite "12", registry
  owner/consumers fields for the three input tables, precondition
  producer messages, tests (guide-coverage, notebook contract,
  writers-ground-truth), INSTALLATION_GUIDE, generated
  PIPELINE_MAP/NOTEBOOK_MAP (regen), handoff docs mentioning 12 (leave
  historical mentions — add a rename note at top of the ingestion-routes
  handoff instead).
- Deployed workspaces: home item rename via git sync; WORK gets the new
  item in the upcoming re-paste (old 12 deleted like other stale items).
