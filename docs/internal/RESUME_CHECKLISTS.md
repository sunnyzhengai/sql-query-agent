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
4. [ ] **Purview glossary demo** (short-lived provision — Purview
       bills hard; provision + demo + deprovision same day):
       - provision Purview; service-principal auth as in the Aug 1 test
       - run **09** (asset push — proves the tested path still green)
       - mine term candidates locally:
         `from src.governance.business_terms import mine_term_candidates, candidates_to_records`
         over graph_nodes rows; review top candidates, accept 2–3,
         name siblings distinctly ("X (scheduling)" / "X (cohort)")
       - push via `PurviewAdapter.ensure_glossary()` +
         `publish_glossary_term(...)` — one term per definition,
         assigned to its implementing assets, siblings see-also linked
       - screenshot for the demo/listing; optionally wire ops_sync_log
         audit rows while provisioned
       - deprovision
5. [ ] **L3 retrieval probe** (decides the semantic-retrieval
       architecture — ADR 0030 amendment): Fabric SQL database item;
       DATABASE SCOPED CREDENTIAL (aivia key) + CREATE EXTERNAL MODEL
       → embeddings deployment READY: `text-embedding-3-small` on
       aivia, DataZoneStandard, 1536 dims, live-smoked 2026-08-08;
       table (node_id, text cols, emb VECTOR(1536)); seed rows; embed
       in-database (`UPDATE ... SET emb = AI_GENERATE_EMBEDDINGS(...)`);
       add as Data Agent source + ONE example pair with the shape below;
       ask a PARAPHRASED question (test full-sentence AND distilled
       phrasings); INSPECT RUN STEPS: did generated SQL call
       AI_GENERATE_EMBEDDINGS and execute? Record verdict in ADR 0030.
       Probe query shape (embedding computed ONCE via CROSS JOIN; count
       disclosed; closeness returned; calibrate THRESHOLD empirically
       against ~a dozen known question→answer pairs, start ~0.55):
       ```sql
       WITH q AS (SELECT AI_GENERATE_EMBEDDINGS('cancelled appointments'
                    USE MODEL aivia_embeddings) AS v),
       scored AS (SELECT c.node_id, c.name, c.business_name, c.description,
                    VECTOR_DISTANCE('cosine', c.emb, q.v) AS distance
                  FROM semantic_catalog c CROSS JOIN q)
       SELECT (SELECT COUNT(*) FROM scored WHERE distance < 0.55) AS total_matches,
              TOP 10 *, 1 - distance AS closeness
       FROM scored WHERE distance < 0.55 ORDER BY distance
       ```
       (TOP-with-count syntax may need two statements — part of the
       probe.) Instruction rules to seed alongside: embed the CORE
       CONCEPT, not the full question; always report total_matches
       ("N related, showing top 10"); closeness is relative similarity,
       NEVER a probability; below threshold → refuse ("nothing
       sufficiently related"), per ADR 0005.
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
