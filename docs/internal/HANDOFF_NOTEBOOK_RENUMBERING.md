# Handoff — renumbering: fix the one lie (12 → 00f), decline the beauty pass

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
