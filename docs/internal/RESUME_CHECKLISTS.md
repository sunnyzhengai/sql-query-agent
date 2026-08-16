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
       5c. [x] **SQL-DB disambiguation — DONE 2026-08-08**: emb absent
           from the mirror (drop confirmed) AND the endpoint's engine
           refuses the function ("not supported", Msg 15871 — modern
           parser, disabled by policy). Three-wall taxonomy recorded in
           ADR 0030. Cleanup now clear: delete probe SQL DB + its
           endpoint twin + both throwaway agents; keep probe-eh.
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

## E. Next session — semantic catalog on-tenant + snapshot (queued 2026-08-08 evening)

1. [ ] **make_golden_snapshot FIRST** (skipped 2026-08-08 — capacity was
       paused before it ran): open the notebook, Run all, ~2 min. It
       backs up the expensive state (description cache, PHI
       dispositions, inputs) to golden_ tables + manifest.
2. [x] **Semantic catalog on-tenant — BUILT + VERIFIED 2026-08-09**
       (ADR 0030 build log): 441 rows embedded, threshold 0.35
       calibrated, semantic_search() live, two-source Graph agent
       verified (KQL resolution -> keyed traversal -> grounded answer
       with report link). Remaining follow-ups: paraphrase test
       (semantic_search on fuzzy phrasing), stepCount/tableCount as
       Metric properties for count questions (future 1.4.4), publish
       agents before demo. Original plan:
       1. Add a small cell to 05 (or run ad hoc): build rows via
          `from src.steps.semantic_catalog import build_semantic_catalog`
          over graph_nodes; write to Delta `output_semantic_catalog` —
          ALWAYS with explicit column order (Spark alphabetizes dict
          rows; positional copies downstream then shift columns):
          `df = spark.createDataFrame(out.rows).select("node_id","kind","ref","name","business_name","search_text","display_text")`
       2. In probe-eh (rename to aivia-eh if you like): run the setup
          script — table, embed (only new rows pay), semantic_search()
          function, verification queries incl. the refusal-floor probe.
       3. Wire as a SECOND source on the Graph agent (script section 5:
          tick semantic_catalog + the function; paste source
          instructions; one example pair = the function call).
       4. Re-run the two questions that failed 2026-08-08: "How is ED
          Sepsis Screening calculated?" (resolution via semantic_search
          -> traversal with the returned ref) and the exact-count
          question (expect 43).
3. [ ] Scale back to F2 after.

---

## F. Next session — orchestrator goes live end to end (queued 2026-08-09)

**STATUS 2026-08-10 (live sessions ran):** shortcuts created; multiple
live CLI sessions done. Shipped from live findings: input cleaning
(escape keys), duplicate-list backstop, empty-pick guard, narrate rule
5 reword (leak fix), the VARIANTS VERB (live-verified:
Base_Pop_Severe_ED_Scores = 6 procs, 5 distinct definitions), and the
verb scorecard game → conversational entry edge REFACTOR GREEN-LIT
(see VERB_SCORECARD.md). UI decided: one backend, two faces (ROADMAP).
Remaining below still valid for further break-it testing.

The answer half is built and offline-tested; it needs two shortcuts and
one live conversation. Plain steps:

1. Resume capacity.
2. **Create the two shortcuts** (full click path — same as the one you
   made for output_semantic_catalog yesterday):
   1. In the workspace item list, open **probe-eh** — the item typed
      **KQL Database** (the child), not the Eventhouse parent.
   2. In the database view, find **New → OneLake shortcut** (either a
      "+ New" button in the toolbar, or right-click the **Shortcuts**
      node in the left tree → New shortcut).
   3. Source: **Microsoft OneLake** → pick your lakehouse
      **sql_query_lh** → expand **Tables**.
   4. Tick **output_metric_logic** AND **graph_nodes** AND
      **graph_edges** (graph_edges added 2026-08-16: the
      list_report_links tool reads consumption-layer edges through it)
      — the picker allows selecting all in one pass (if yours doesn't,
      just run the wizard once per table).
      CHECK FIRST: run `<table> | count` in the query editor — a
      shortcut that already exists fails the wizard with "External
      table ... already exists" (seen live 2026-08-16; that error means
      DONE, not broken).
   5. **Create**. Both appear under the Shortcuts node within a
      minute. A shortcut is a live pointer — no copying, no refresh
      to manage; it always shows the lakehouse table's current rows.
3. Quick checks (query editor, one at a time):
   `output_metric_logic | count` → expect **28**
   `graph_nodes | count` → expect **a few thousand** (28 metrics +
   432 steps + every table and column node)
4. On your laptop, run the product:
   `python -m src.orchestrator.cli`
   **This IS the end-to-end test** — see the note below the steps.
   Ask anything — candidates appear ranked with closeness; pick by
   number; the narrated answer ends with a code-stamped Basis. Every
   pick lands in `data/events/pick_events.jsonl` (the flywheel,
   capturing locally until the production sink).
5. Try to break it: rephrase, ask nonsense, decline all candidates.
   Screenshot anything surprising.
6. Pause capacity.

**Why the CLI is the end-to-end test (not a shortcut around Fabric):**
after the runtime pivot (ADR 0032), the orchestrator IS the product —
Fabric's role is the data plane, not the conversation. The CLI run
exercises every real production hop: your Entra identity → Eventhouse
(resolution + embeddings impersonated as you) → OneLake shortcuts →
lakehouse facts → your Azure OpenAI (both LLM edges). The only thing
"CLI" about it is the shell around the loop — a web/Teams surface later
swaps the rendering, not the code underneath. Testing "on Fabric end
to end" in the old sense would mean testing the demoted chat agents —
the secondary surface, not the flagship.

Then the remaining build (no tenant needed): robustness suite reruns
against the FULL loop (assembly+narration graded too), UI beyond the
terminal, Entra sign-in, production event sink.

---

## B. Rematch — SUPERSEDED by ADR 0032 (2026-08-10; was: deferred to Round 3)

The contest's question ("which query language does the generator write
better — NL2SQL over Delta or NL2GQL over the LPG?") was DISSOLVED,
not decided: the orchestrator's flagship loop has no query generator —
resolution is vector search, facts are fixed lookups, closures are
precomputed. The paraphrase-robustness suite is the successor
measurement (baseline 2026-08-09: hit@5 96.7%, replay stable). The
scorecard and Round-1/2 evidence remain as the historical record of
WHY the generator was removed. A Fabric-agent secondary surface, if
ever shipped, would revive a scoped version of this protocol.

Original Round-3 framing kept below for reference:

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

## Fabric gotcha log — 2026-08-12 session

**KQL shortcut schemas FREEZE at creation.** The lakehouse table gained
business_name/report columns Aug 8 (Delta v11), but probe-eh's shortcut
kept serving the 9-column schema it inferred at creation — recreating
the SHORTCUT did not help (the external-table definition persisted),
and after dropping the external table, lazy re-materialization never
came (15+ min). Working fix, fully API/mgmt-scriptable:
  1. `.drop external table <name>` (mgmt endpoint)
  2. `.create external table <name> kind=delta (h@'abfss://<ws-guid>@onelake.dfs.fabric.microsoft.com/<lakehouse-guid>/Tables/dbo/<name>;impersonate')`
     — infers the CURRENT Delta schema; bare-name queries still resolve.
Product consequence: the installer/upgrade path must rebuild external
tables after any schema-evolving release; customer symptom otherwise is
"new columns exist in the lakehouse but the agent can't see them."

**SQL-endpoint metadata sync lag**: new lakehouse tables (gov_*) were
invisible to the Direct Lake semantic-model picker until a forced
refresh — POST /v1/workspaces/{ws}/sqlEndpoints/{id}/refreshMetadata
(works, returns per-table status). The installer's report-deployment
step calls this before creating the model.

**Pipeline ordering gotcha (2026-08-12, caught by the admin dashboard's
first Knowledge Coverage render):** 04 rebuilds output_metric_logic
from the graph; metric DESCRIPTIONS are 07's enrichment INTO that
table — an ad-hoc 04 rerun wipes them until 07 reruns (cache makes
that cheap). Rule: 04 rerun => 07 rerun. Fix candidate for the
product: 04 preserves the description column on rebuild (merge, not
blind overwrite).

**Direct Lake framing note (2026-08-13):** auto-framing catches Delta
changes with variable lag (instant to minutes). The datasets refresh
API ({"type":"automatic"}) forces a reframe in seconds — pipeline
notebooks that write admin tables should end with it so the dashboard
is instantly current. Verified: description restore appeared at 100%
immediately after the forced reframe.

## 1.5.2 rollout — step numbers + customer-facing search rows (2026-08-13)

What changed: search results are now customer-facing (business name,
description, closeness — no CTE names or raw ids). Steps display as
"<metric business name> → step N". Step numbers come from CTE
declaration order, written by 03 into transform node properties
(step_no). No table schema changed (properties is a JSON bag and
graph_nodes.description already existed), so NO shortcut/external-table
rebuild is needed.

Steps for Sunny:
1. Sync DevOps source control (pulls the 1.5.2 wheel in
   sql-logic-env.Environment/Libraries/CustomLibraries).
2. Publish the sql-logic-env environment (picks up 1.5.2).
3. Rerun notebook 03 (writes step_no into graph_nodes properties).
4. Rerun notebook 07 (03's overwrite wiped descriptions — standing
   rule: 03 or 04 rerun => 07 rerun).
5. Optional: rerun 06 to revalidate; expect 28/28 unchanged.
6. Restart the local web app (`uvicorn`); search rows now show
   descriptions immediately, step numbers after steps 1-5.

Until step 3 runs, step rows show "<business name> → step" without a
number (honest fallback — the number does not exist in the graph yet).

## 1.5.3 rollout — search relevance + concrete descriptions (2026-08-13)

Two live finds from the workbench screenshot (steps outranking metrics
on "ED sepsis"; vague descriptions):

**Root causes:** (1) step search_text contained the parent metric_id —
every step of USP_ED_Sepsis carried the tokens "ED Sepsis", so
transfer-timeline steps outscored the actual sepsis metrics; (2) the
step prompt asked for ONE 40-word sentence with no values, so the LLM
wrote "specific departments"; and the description cache key knew only
the SQL, not the prompt — prompt fixes could never reach cached text.

What 1.5.3 changes: step search_text = step name + own description
only; STEP_PROMPT demands one summary line + '- ' decision lines with
ACTUAL values (codes, statuses, thresholds, time windows); PROMPT_VERSION
is in every cache key (prompt change auto-regenerates everything);
metric descriptions are now cached too (idempotent reruns, zero calls);
vague-filler flags ('specific'/'certain' hiding a value) print in 07's
run report.

Steps for Sunny:
1. Sync DevOps, publish sql-logic-env (1.5.3).
2. Rerun 07. Cache keys are versioned, so ALL ~441 descriptions
   regenerate this run (413 step + 28 metric LLM calls — same cost as
   tonight's run). Watch the "Vague-filler flags" line; a handful is
   tolerable, dozens means the prompt needs another pass.
3. Rebuild the semantic catalog Delta table by running 11_refresh_search_index
   Cell 1 (draft.Notebook is deleted — it lacked the explicit column order fix
   and would resurrect the 2026-08-09 column-shift bug). Must run AFTER 07 so
   the new concrete descriptions land in search_text.
4. In the Eventhouse (aivia-eh/probe-eh): `.drop table semantic_catalog`
   then rerun eventhouse_setup.kql sections 1-2 (recreate + full
   re-embed — search_text changed on every row, and the embed step
   only pays for rows with an empty vector, so a drop is required.
   441 embeddings ≈ cents). semantic_search() function is unchanged.
5. Re-test "ED sepsis" in the workbench: metrics should now lead;
   any step that still ranks does so on its own content.
6. Re-run the robustness suite before trusting the change broadly —
   retrieval inputs changed, so the 12/12 live baseline must be
   re-earned, not assumed.

NOTE the standing gotcha now has a sibling: 03/04 rerun => 07 rerun,
and 07 rerun => catalog rebuild + re-embed (steps 3-4) whenever
descriptions change, or search keeps ranking on stale embeddings.

## 1.5.4 — notebook 11 replaces the manual re-embed ritual (2026-08-13)

The 1.5.3 runbook's manual steps 3-5 (catalog rebuild cell, KQL-editor
.set-or-replace, embed, verify) are now pipeline notebook
**11_refresh_search_index**: rebuild Delta -> Eventhouse copy (mgmt
API, columns by name, emb nulled) -> full re-embed -> coverage check
(raises if any row lacks a vector) -> refusal-floor probe (reported,
never auto-acted). One-time first: KUSTO_URI in cell 0 (KQL database
-> copy Query URI). eventhouse_setup.kql remains the one-time DDL/
function/callout setup only.

Standing rule (final form): 03/04 rerun => 07 rerun => 11 rerun.

## 1.5.6 — description prompt v3: dictionary-grounded translation (2026-08-14)

Live find: v2 descriptions carried actual values (good) AND raw Epic
identifiers (ADT_DEPARTMENT_ID, #SDX, `pd.PatEncCSNID`) — unreadable
for the customer-facing tier. Root cause: the step prompt demanded
literals but had NO translation material. Fix: each step's prompt now
carries the data dictionary for the tables it touches (+ only the
columns its SQL references) from the graph's own technical nodes; raw
identifiers banned in output (use dictionary description or plain
phrase; refer to earlier steps by what they produce); literal VALUES
(codes/thresholds/statuses/hours) still required. New jargon flags in
07's run report (raw-identifier regex, observation only). Cache keys
now include dictionary content — dictionary edits regenerate affected
steps automatically.

Steps: sync + publish env (1.5.6) -> rerun 07 (full regen, ~441 calls,
PROMPT_VERSION=3) -> run notebook 11 (re-embed) -> workbench re-test.
Watch BOTH flag lines in 07's output: vague + jargon counts.
