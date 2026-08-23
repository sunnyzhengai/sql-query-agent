# Runbook — configure SQL Intelligence Agent, one tenant pass

Staged by dev, 2026-08-22, per the item-4 CORRECTION in
HANDOFF_TRACE_AND_ADMIN_GRAPH.md. Everything below is ONE sitting, in
this order — the order matters (rename before agent config; fewshots
copied before any retirement; Round 4 before retirement).

**THE ONE WARNING: do not delete Delta Agent or Graph Agent until
step 7 has copied the Eventhouse example queries out of the Graph
Agent — they exist nowhere else.**

## 0. Prerequisites (5 min)

1. Resume the capacity (aiviafabric) if paused.
2. Pull the repo on the machine you'll edit org_config from
   (`git pull` on dev).

## 1. Publish the environment (10 min, mostly waiting)

1. Workspace → `sql-logic-env` → confirm CustomLibraries shows
   `sql_query_agent-1.56.0-py3-none-any.whl` (Update from git if not).
2. Publish. Wait for "Published".

## 2. Rename the Eventhouse (10 min)

1. Workspace → `probe-eh.Eventhouse` → rename to
   `aivia_semantic_catalog`.
2. On dev, update every reference, then verify:
   - `git grep -ln "probe-eh"` — expect: src/webapp/main.py,
     src/orchestrator/cli.py, devtools/answer_evals.py,
     devtools/eventhouse_setup.kql, devtools/eventhouse_probe.kql,
     devtools/robustness_suite.py (re-grep; the list may have grown)
   - In each, replace the database name `probe-eh` with the KQL
     DATABASE name as shown on the renamed item (check the item —
     the DB may keep its own name; update to what the portal shows).
   - Update `org_config.yaml` → `search.kusto_db` (and `kusto_uri` if
     the Query URI changed — the portal shows it on the DB page).
3. Verify before moving on:
   - `python3.11 devtools/answer_evals.py --smoke` reaches the store
     (any grade output = connected; "store unreachable" = wrong name).
4. Commit the reference edits (explicit file paths).

## 3. The single pipeline run (the big one)

Run notebooks 400 → 800 in order (as in the standard rerun), then
`700_refresh_search_index`. This one run carries THREE payloads:
1. v6 descriptions — the metric-grain scope rule (poisoned "without
   applying any filtering decisions" text regenerates everywhere).
2. Decision expressions redacted at rest (export-side PHI gate).
3. `transform_to_column` projection edges (ADR 0053) — after this,
   "who selects PATIENTMRN" has a real answer.
Post-run checks (dev can run these for you if you ping):
- `python3.11 devtools/reachability_audit.py` → "no drift" + both
  conservation lines.
- Load the Graph Model (Load operation on the Graph item) so the
  traversal source is fresh.

## 4. Configure SQL Intelligence Agent (20 min)

FIELD CORRECTION (2026-08-22): the empty shell no longer exists in
the workspace — CREATE the item fresh: + New item → Data agent →
name it exactly `SQL Intelligence Agent`.
1. Create/open `SQL Intelligence Agent` (Data Agent).
2. Add data source 1 — **Lakehouse** (the pipeline lakehouse), select:
   `output_metric_logic`, `output_metric_twins`, `ops_parse_errors`,
   `ops_pipeline_validation`, `ops_installation_errors`, `ops_funnel`,
   `ops_fallout`, `graph_nodes`, `graph_edges`,
   `graph_edge_uses_table`, `graph_canonical`.
3. Add data source 2 — **KQL database** on `aivia_semantic_catalog`
   (the renamed Eventhouse): the semantic catalog DB with the
   `semantic_search()` function.
4. Add data source 3 — **Graph Model** (the LPG item the Graph Agent
   uses today).
5. Instructions panel → paste ALL of
   `notebooks/sql_intelligence_agent_instructions.md` (below its
   `---` line).
6. Lakehouse source → Example queries → Import from JSON →
   `notebooks/delta_agent_fewshots.json`.
7. **Copy THREE things from Graph Agent before ANY retirement**
   (they exist nowhere else — never synced to git):
   a. Its KQL source → Example queries → copy each pair into the
      same place on the new agent's KQL source.
   b. Its KQL source → the per-source DESCRIPTION/routing text
      (starts "To resolve a user's topic or metric reference,
      call semantic_search(...) FIRST…") → paste verbatim into
      the new agent's KQL source description box (review-session
      find, 2026-08-22: per-source descriptions steer the
      agent's source router; agent-level instructions alone do
      not reach it).
   c. Its Graph Model source → per-source description, if one is
      set → same copy.
8. Publish the agent.

## 5. Verify (10 min)

Ask the published agent; every answer must end with a Basis line:
1. "What metrics are available?" → the certified list, exact count.
2. "How is Severe Sepsis Episodes calculated?" → curated description
   + criteria from decision_summary (REJECT if it claims "no
   filtering decisions" — that's the poisoned-description corpse and
   means step 3's run didn't regenerate descriptions).
3. "Which metrics use IP_SEPSIS?" → reader list via lineage, not
   name mentions.
4. "/coverage" → the counts table.
5. "How many severe sepsis patients last month?" → refusal naming
   what it CAN answer.

## 6. Point Round 4 at it and run

1. `org_config.yaml` → `fabric_graph.data_agent_id:` → the SQL
   Intelligence Agent's id (item settings → copy the agent/artifact
   id from the URL or details pane); confirm `workspace_id` is set.
2. `python3.11 devtools/rematch_round4.py` — it writes
   internal/docs/REMATCH_ROUND4_SCORECARD.md and appends to the goal
   file. Round 4 tests THIS agent — the artifact-as-shipped.
3. Reporting rule (Round-4 record audit, 2026-08-22): any prose about
   the result ANNOTATES the scorecard's machine-emitted miss/partial
   lines — never free-write a miss list from the truncated answers,
   and any "X is not in the catalog" claim carries its grep receipt
   against data/demo/input_metric_names.csv. Full untruncated
   answers: REMATCH_ROUND4_RAW.jsonl beside the scorecard.

## 7. Retire (only after 5 passes and 6 has run)

Workspace-first deletion protocol, one at a time:
1. Delta Agent (Data Agent) — delete in workspace; on next git sync
   remove `Delta Agent.DataAgent/` from the repo.
2. Graph Agent (Data Agent) — same (fewshots were copied in 4.7).
3. eh_probe (Data Agent) — same.
4. Move `export_test_fixtures` and `make_golden_snapshot` notebooks
   into a workspace folder (notebooks-location rule); verify the
   folder lands in git on next sync.

## 8. Close out

1. Ping dev with the Round 4 scorecard + any verification failures
   (each becomes a fixture per the walk protocol).
2. Pause the capacity if you're done for the day.
