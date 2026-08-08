# Resume Checklists — for the next Fabric-capacity session

**Purpose:** on-tenant work queued between capacity sessions, prepped so
each session starts cold in minutes. Sections A (deploy runbook) and B
(rematch) persist; dated sections get executed and marked.

---

## A. Deploy cycle runbook (executed 2026-08-06 with 1.4.1)

Prereqs
- [x] Fabric capacity available; scale to F4 for the run if the F2
      throttles (Azure portal → capacity → Scale; scale BACK to F2 after)
- [x] 07's LLM config in lakehouse `Files/sql-query-agent/`:
      `org_config.yaml` `llm:` block + `llm_api_key.txt` (raw key, one
      line; lives in Files, never in git — llm_api_key.txt is gitignored
      after the 2026-08-08 near-commit that push protection caught)
- [x] `git status` clean on dev; CI green

Steps
1. [x] Build the wheel: `python -m build` → verify metadata version
2. [x] **Ship the wheel via git, not portal upload**: commit into
       `sql-logic-env.Environment/Libraries/CustomLibraries/` (remove the
       old one), push; workspace → Source control → Update; Publish.
       Bare `PbiApiError` on Publish → fresh browser tab first
       (stale-session, 2026-08-06 incident), then
       `devtools/publish_environment.py` for the real error payload
3. [x] Run **07** (first run ~460 calls, then hash-cached); gate green;
       spot-check descriptions for filler
4. [x] Run **05**
5. [x] **Load the Graph Model — there is NO Load/Refresh button.** A load
       fires only when a REAL definition change is saved (new columns →
       update the node type's property mapping via Get data first).
       Saving gives NO feedback — refresh the page to see the "Data load
       is in progress" banner; footer "Last loaded" confirms. Count
       parity can't detect property-value staleness — probe a property.
6. [x] Sanity Q&A (2026-08-06: step-catalog answer verified grounded)
7. [x] Token caveat: restart session before 07 if >1 hr old

Rollback: previous wheel is one git revert away; graph tables are
overwrite snapshots — rerun 03→05 with the old wheel restores.

---

## C. 2026-08-06 evening batch — VALIDATED on tenant 2026-08-08

1. [x] Source control Update (02/07 notebooks + make_golden_snapshot)
2. [x] Azure OpenAI switch: `gpt-5.4-mini` (DataZoneStandard, East US 2)
       live via src.llm_client; lakehouse org_config + key updated
3. [x] 02_parse → ops_phi_findings written
4. [x] 07 → PHI gate live, redacted steps regenerated
5. [x] 05 + graph load
6. [x] Sanity: answers grounded with redacted fragments
7. [x] make_golden_snapshot run (record manifest numbers here when handy)
8. [x] Scaled back to F2

---

## D. Next session — demo prep, L3 probe, business terms (queued 2026-08-07/08)

Order matters: 1–4 change tables/instructions, 5 validates, 6 records.

1. [ ] **Business names + report links CSV** → `input_metric_names`:
       author for the demo metrics — choose names you'd SAY OUT LOUD
       ("ED Sepsis Screening"); include `report_name` + `report_url`
       (the app.powerbi.com link of the demo report Sunny built) on the
       metrics the demo will touch; qualified metric_ids (bare names
       that collide across schemas are skipped by design). Load as
       table, rerun **03→04→05**.
2. [ ] **Re-paste BOTH agents' instructions** (changed 2026-08-07/08:
       business_name in every search clause, report-link rule
       "Used in: <report> (<url>)" + never-invent-a-link, businessName
       in the graph catalog fetch): copy current
       `notebooks/delta_agent_instructions.md` and
       `notebooks/graph_agent_instructions.md` into the agents.
3. [ ] **Graph Model mapping**: Metric type gains `businessName`,
       `reportName`, `reportUrl` columns (Get data → map → Save →
       refresh page → wait for load; runbook step A5 drill).
4. [ ] **Purview glossary demo.** Purview bills hard — create it, demo
       it, and delete it the same day. Concretely:
       1. Create the Purview account in the Azure portal (same
          service-principal setup as the Aug 1 test).
       2. Run notebook **09** — pushes the metric assets, proves the
          tested path still works.
       3. In a notebook cell, mine term candidates from your own SQL:
          `from src.governance.business_terms import mine_term_candidates, candidates_to_records`
          then `mine_term_candidates([r.asDict() for r in spark.table("graph_nodes").collect()])`.
          Look at the top few. Pick 2–3 good ones. If two candidates
          share a name but differ in logic, give each a distinguishing
          name like "X (scheduling)" vs "X (diabetes cohort)".
       4. Push them: `PurviewAdapter.ensure_glossary()` once, then
          `publish_glossary_term(...)` per term (it links each term to
          its metrics automatically).
       5. Open Purview, screenshot the glossary terms for the listing.
       6. Delete the Purview account.
5. [x] **L3 probe — RUN 2026-08-08, verdict: FAIL** (recorded in ADR
       0030). Direct SQL worked (right match first, 0.49 vs 0.62 gap,
       1.1 s); the Data Agent could not use it — its validator sees the
       read-only mirror where AI functions don't exist and the VECTOR
       column is dropped ("Invalid column name 'emb'"). Bonus capture:
       unscoped agent FABRICATED an appointments dataset + chart —
       before/after screenshots saved for the demo/whitepaper.
       Cleanup: [ ] delete the L3_Probe agent; keep the `probe` SQL
       database (needed for the disambiguation check below).
       5b. [x] **Eventhouse probe — RUN 2026-08-08 same day, verdict:
           PASS** (ADR 0030). Agent generated + executed ai_embeddings
           KQL under user impersonation; correct row returned. Eventhouse
           is the semantic-retrieval engine. Productization notes in ADR
           0030 (stored KQL function; per-user role prereq). Cleanup:
           [ ] delete EH Probe + L3_Probe throwaway agents; KEEP probe-eh
           (seed of the real build); delete probe SQL DB after 5c.
           Original steps for reference:
           **`devtools/eventhouse_probe.kql`**; follow top to bottom.
           In plain steps:
           1. Portal prereqs first (section 0): create an Eventhouse
              item; give YOUR account the "Cognitive Services OpenAI
              User" role on aivia (this probe uses your identity, no
              key anywhere); run the callout-policy command — the step
              most likely to fight back; screenshot any error.
           2. Run sections 1–3 in the KQL query editor: make the
              table, embed the rows, then run the search yourself.
              Readmission row first at ~0.5 similarity = setup good.
           3. Throwaway agent "EH Probe", only this KQL database as
              source; paste instructions + the example pair from
              section 4. If the validator rejects the example pair —
              screenshot; that alone is a verdict.
           4. Ask the newborn-sepsis question; open run steps; check:
              KQL contains ai_embeddings? Executed? Right row first?
           5. Tell Claude the outcome (PASS / validator-reject /
              execution error) — ADR 0030 gets the verdict.
       5c. [ ] **SQL-DB disambiguation, 2 min** (architect follow-up,
           script section 5): open the probe database's SQL analytics
           endpoint (its read-only twin) and run the two queries —
           does `emb` exist there? does AI_GENERATE_EMBEDDINGS parse?
           Settles which wall(s) the SQL probe hit; record in ADR 0030.
       Original SQL-probe steps kept below for reference:
       1. In the workspace: **+ New item → SQL database** (a third kind
          of item — not the lakehouse, not a warehouse). Any name; it's
          disposable.
       2. Open its query editor. Paste the script's sections 1–3 one at
          a time. Where the script says `<AIVIA-KEY-1>`, paste the aivia
          key — into the editor only, never into the file.
       3. Section 3 is a search you run yourself. If the readmission
          row comes back first, setup is good. Note the distance
          numbers — they tell us where to set the match threshold.
       4. Create a throwaway Data Agent named "L3 Probe" with ONLY this
          database as its source. Copy the instruction paragraph and
          the one example pair from section 4 of the script.
       5. Ask it: "anything about newborns screened for sepsis in the
          ER?" Open the answer's **run steps** panel and check two
          things: does the generated SQL contain
          AI_GENERATE_EMBEDDINGS, and did it execute and return rows?
       6. Both yes → **PASS**. Query errored → **FAIL** (we switch to
          the backup plan). Agent never wrote that SQL shape at all →
          not a verdict; reword and ask again before concluding.
          Either way, tell Claude the result — ADR 0030 gets its
          verdict recorded.
       7. Delete the throwaway agent. Keep the database if PASS.
6. [ ] **Demo QA subset** (before recording; ~6 Q&A per F2 burst):
       Q1 (metric detail with step catalog), Q4 (13 readers), Q8
       (refusal), one business-name resolution ("how is ED Sepsis
       Screening calculated?" → resolves + shows both names + report
       link), and one cross-grain probe (concept defined both as a
       metric AND inside another metric's CTE — the
       cancelled-appointments pattern; candidate: pick from miner
       output). The cross-grain answer is demo-script material.
7. [ ] **Golden snapshot refresh** after all table changes; record
       manifest numbers
8. [ ] Scale back to F2

---

## B. Rematch — DEFERRED to Round 3 (decided 2026-08-08)

Round 2 completion is superseded: the full head-to-head waits until the
resolution surface stops moving — dimension layer (ADR 0029), retrieval
architecture (ADR 0030 probe verdict + implementation), report/measure
nodes (semantic-model lane). Benchmarking a moving target twice buys
nothing. The demo-QA subset (section D.6) covers pre-video acceptance.

Round 3 additions to the answer key when it runs:
- business-name resolution questions (vocabulary → metricId)
- report-link questions ("which report shows X?")
- business-term questions incl. the cross-grain cancelled-appointments
  pattern (both definitions surfaced, weights disclosed)
- retrieval A/B: same set with and without the L3 semantic catalog —
  quantifies what the semantic layer buys (evidence for defaulting it)
- filter/parameter questions once the dimension layer ships

Protocol, scoring axes (Correct/Grounded/Honest), burst budgeting, and
the footer-honesty watch all carry over from
[REMATCH_SCORECARD.md](REMATCH_SCORECARD.md). Feed results into
REMATCH_WRITEUP.md (thesis pre-written) and decide the publishing venue.
