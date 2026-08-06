# Resume Checklists — for the next Fabric-capacity session

**Purpose:** the two queued work items deliberately out of scope for the
2026-08-06 autonomous run, prepped so they can start cold in minutes.
Delete each section when done; delete the file when both are done.

---

## A. 1.4.0 deploy cycle (wheel → 07 → 05 → re-Load)

Goal: get bottom-up descriptions (ADR 0019) + the generator-compatibility
export (ADR 0020) live on the Fabric tenant in one sitting.

Prereqs
- [ ] Fabric capacity available (F2 burst budget in mind: no agent Q&A
      needed for the deploy itself)
- [ ] `OPENAI` endpoint decision for 07 on-tenant: customer-pattern Azure
      OpenAI vs. dev key in notebook env (dev tenant only — never ship the key)
- [ ] `git status` clean on dev; CI green

Steps
1. [ ] Build the wheel: `python -m build` → verify `twine check dist/*`
       and version says **1.4.0** (`pyproject.toml` already bumped)
2. [ ] Upload wheel to the Fabric Environment (replace 1.3.1); publish
       environment; wait for propagation (~10 min)
3. [ ] Run **07_generate_descriptions** (now the ADR 0019 bottom-up path):
       - watch call volume — first run is ~460 calls, then hash-cached
         (`ops_description_cache`)
       - postcondition gate green; spot-check 3 step + 2 metric
         descriptions for grounding (no invented purposes — the tuned
         METRIC_PROMPT from 2026-08-06 bans benefit-filler)
4. [ ] Run **05_export_graph_tables** so the LPG export carries
       descriptions + the 1.3.1 shim shapes (qualified `name`, closure
       `CALCULATED_BY`)
5. [ ] **Re-Load the Graph Model** (the LPG is a snapshot — this is the
       step that always gets forgotten; count parity queryset from
       REMATCH_SCORECARD pre-flight is the check)
6. [ ] Sanity Q&A (2 questions max, save burst budget): one metric-detail
       question (expects step catalog in the answer), one refusal probe
7. [ ] mssparkutils token caveat: if the session runs >1 hr, restart the
       session before 07 — `getToken()` caches and won't refresh mid-batch

Rollback: previous wheel stays in the Environment history; graph tables are
overwrite-mode snapshots — rerunning 03→05 with the old wheel restores.

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
