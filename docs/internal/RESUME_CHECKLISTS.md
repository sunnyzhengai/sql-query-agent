# Resume Checklists — for the next Fabric-capacity session

**Purpose:** the two queued work items deliberately out of scope for the
2026-08-06 autonomous run, prepped so they can start cold in minutes.
Delete each section when done; delete the file when both are done.

---

## A. 1.4.x deploy cycle — RUN 2026-08-06 (1.4.1); kept as the runbook

Executed 2026-08-06 with 1.4.1. Lessons learned are folded in below —
this section is now the reusable deploy runbook.

Prereqs
- [x] Fabric capacity available; scale to F4 for the run if the F2
      throttles (Azure portal → capacity → Scale; scale BACK to F2 after)
- [x] 07's LLM config in lakehouse `Files/sql-query-agent/`:
      `org_config.yaml` gets an `llm:` block (endpoint, model,
      api_key_file) + `llm_api_key.txt` (raw key only, one line; lives in
      Files, never in git). Dev tenant: api.openai.com + gpt-4o-mini,
      matching the local fixtures' vocabulary
- [x] `git status` clean on dev; CI green

Steps
1. [x] Build the wheel: `python -m build` → verify metadata version
2. [x] **Ship the wheel via git, not portal upload**: commit it into
       `sql-logic-env.Environment/Libraries/CustomLibraries/` (remove the
       old one), push; workspace → Source control → Update; then Publish
       the environment. Portal upload is the fallback, not the path.
       If Publish fails with a bare `PbiApiError`: fresh browser tab
       first (stale-session is the common cause; 2026-08-06 incident),
       then `devtools/publish_environment.py` for the real error payload
3. [x] Run **07_generate_descriptions**: first run ~460 calls, then
       hash-cached (`ops_description_cache` — separate from the committed
       local fixtures cache). Postcondition gate green; spot-check 3 step
       + 2 metric descriptions (no benefit-filler)
4. [x] Run **05_export_graph_tables**
5. [x] **Load the Graph Model — there is NO Load/Refresh button**
       (verified 2026-08-06: neither the model editor toolbar nor the
       item's ⋯ menu has one). A load fires only when a REAL definition
       change is saved:
       - 05 added/changed columns → update the node type's property
         mapping (Get data first if the new column isn't listed) → Save
       - content-only refresh → re-apply a mapping via Get data → Save
       Footer "Last loaded" confirms. Count parity CANNOT detect a stale
       load when only property values changed — probe a property:
       `MATCH (t:Transformation) RETURN t.name AS name, t.description AS d LIMIT 5`
6. [ ] Sanity Q&A (2 questions max, save burst budget): one metric-detail
       question (expects step catalog in the answer), one refusal probe
7. [x] mssparkutils token caveat: if the session runs >1 hr, restart the
       session before 07 — `getToken()` caches and won't refresh mid-batch

Rollback: previous wheel is one git revert away (environment is
git-integrated); graph tables are overwrite-mode snapshots — rerunning
03→05 with the old wheel restores.

---

## B. Remaining rematch questions (Round 2 completion)

Goal: finish the 9-question scorecard on the post-1.3.1 graph, then the
Delta head-to-head. Full protocol: [REMATCH_SCORECARD.md](REMATCH_SCORECARD.md).

Prereqs
- [ ] Deploy cycle A done (descriptions live make Q1-style answers richer;
      at minimum 1.3.1 shim must be Loaded — it already is per 2026-08-05)
- [ ] Pre-flight: pipeline green, Graph Model re-Loaded, count parity
      queryset passes, both agents draft-published with current instructions

Session plan (respect ~6 Q&A per F2 burst; pause/resume resets)
- Burst 1 — Graph agent remaining: Q2 (19 tables), Q4b (7 metrics),
  Q5 (14 sharers), Q6 (133 columns), Q7 (top = reporting.USP_ED_Sepsis, 38)
- Burst 2 — Graph agent: Q8, Q9 (refusals) + truncation diagnostic probe;
  re-ask anything that hit throttling mid-answer
- Bursts 3–4 — Delta agent: full Q1–Q9 in scorecard order, same wording
- [ ] Score 0/1 per axis (Correct / Grounded / Honest) into the /27 table;
      verbatim transcripts for surprises; note friction + latency
- [ ] Watch for the footer tic (Basis describing a query never run) — log
      it per occurrence; footer-honesty rule is in instructions but the
      generator is stochastic
- [ ] Feed results into REMATCH_WRITEUP.md (draft exists, thesis
      pre-written: "the data contract, not the prompt, is where correctness
      gets enforced") and decide the publishing venue
