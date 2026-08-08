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
       Saving gives NO feedback that a load started — the "Data load is
       in progress" banner only appears after a page refresh. Refresh to
       see it; footer "Last loaded" flipping confirms completion. Count
       parity CANNOT detect a stale load when only property values
       changed — probe a property:
       `MATCH (t:Transformation) RETURN t.name AS name, t.description AS d LIMIT 5`
6. [x] Sanity Q&A passed (2026-08-06): property probe returned described
       transformations; "How is USP_ED_Sepsis calculated" returned a
       step-catalog answer whose distinctive claims (24h readmits, HemOnc
       transfers, boarders, BPA overrides) all trace to certified step
       descriptions — the ADR 0019 chain verified end to end in production
7. [x] mssparkutils token caveat: if the session runs >1 hr, restart the
       session before 07 — `getToken()` caches and won't refresh mid-batch

Rollback: previous wheel is one git revert away (environment is
git-integrated); graph tables are overwrite-mode snapshots — rerunning
03→05 with the old wheel restores.

---

## C. Next Fabric session — validate the 2026-08-06 evening batch

Built offline, needs one on-tenant validation pass (order matters):

1. [ ] Source control → Update (pulls updated 02/07 notebooks + the new
       make_golden_snapshot notebook item)
2. [x] **Azure OpenAI live smoke — DONE 2026-08-06 from local**: resource
       `aivia` (rg-fabric-prod, East US 2), deployment `gpt-5.4-mini`
       v2026-03-17, DataZoneStandard sku (gpt-4o-mini is deprecated;
       regional Standard sku no longer offered on new models).
       src.llm_client verified live: api-key header + api-version URL,
       model replied "OK". Remaining on-tenant: update lakehouse
       org_config to
       `endpoint: https://aivia.openai.azure.com/openai/deployments/gpt-5.4-mini`
       + `model: gpt-5.4-mini`, replace llm_api_key.txt with aivia Key 1
       (was copied to clipboard). Note: next 07 run regenerates changed
       steps with the new model (hash cache limits the blast radius).
3. [ ] Run **02_parse** — expect "Saved ~278 PHI findings to
       ops_phi_findings (~218 redact, ~60 open for steward review)"
4. [ ] Run **07_generate_descriptions** — expect "PHI gate: ... fragments
       redacted", ~102 steps regenerate (redaction changed their hashes),
       metrics recompose, rest from cache
5. [ ] Rerun **05** + trigger the graph load (runbook step 5 — mapping
       unchanged, so make a real definition change or re-apply Get data)
6. [ ] Sanity: one metric-detail question still grounded; spot-check a
       redacted step's description reads fine with `<ID>`/`<DATE>` gone
7. [ ] Run **make_golden_snapshot** — golden_ tables + Files/golden/
       manifest.json; record the manifest numbers here
8. [ ] Scale back to F2 if you scaled up
9. [ ] **L3 retrieval probe** (added 2026-08-08, ADR 0030 amendment —
       decides the semantic-retrieval architecture): create a Fabric SQL
       database item; DATABASE SCOPED CREDENTIAL with the aivia Azure
       OpenAI key + CREATE EXTERNAL MODEL (embeddings deployment) +
       one table (id, text, emb VECTOR(1536)); seed a few rows, embed
       in-database (UPDATE ... SET emb = AI_GENERATE_EMBEDDINGS(...));
       add as a Data Agent source with ONE example pair using the
       count-then-top-k shape below; ask a paraphrased question and
       INSPECT RUN STEPS: did the generated SQL call
       AI_GENERATE_EMBEDDINGS and execute? Record verdict in ADR 0030.
       Embeddings deployment READY (2026-08-08): text-embedding-3-small
       on aivia, DataZoneStandard, 1536 dims, live-smoked.
       Probe query shape (embedding computed ONCE via CROSS JOIN, count
       disclosed, similarity returned — calibrate THRESHOLD empirically,
       start ~0.55 cosine distance):
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
       (exact TOP-with-count syntax may need splitting into two
       statements — part of the probe). Instruction rules to seed with
       it: embed the CORE CONCEPT not the full question; always report
       total_matches ("N related, showing top 10"); closeness is
       relative similarity, never a probability; below threshold =>
       refuse ("nothing sufficiently related"), per ADR 0005.
10. [ ] Business-friendly names (added 2026-08-07): author the dev-corpus
       mapping as input_metric_names (CSV → table; e.g.
       reporting.USP_ED_Sepsis → "ED Sepsis Screening" for the demo
       metrics), rerun 03→04→05, trigger the graph load (mapping gains
       businessName column → update the Metric type mapping first, same
       drill as the description column), then ask an agent by the
       business name to verify resolution

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
