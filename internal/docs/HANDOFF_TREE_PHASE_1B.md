# Handoff — tree phase 1b: the ScriptDom port and everything that rides with it

**From:** dev session, 2026-08-19. **Status: EXECUTED (1.28.0 items
1/2/6; 1.30.0 items 3/4/5/7/8 — overnight run 2026-08-20).** Exit
evidence in TREE_PHASE1_ED_SEPSIS.md (488/488, gaps 0) and
RECERT_ANSWER_KEY_1_30.md (awaiting Sunny's morning sign-off: the
depth-cap fix recovered reads corpus-wide, all gains zero losses,
oracles re-pinned). Item 8's surprise: the 13,156 suppressions were
pure indexer noise (zero structural change) — the REAL third bucket
was the depth-15 cap, now raised to 60 and counted.

## Scope (in order)

1. **Extraction moves into the ScriptDom visitor** (200's parse pass —
   same pass that produces fragments; original tokens preserved, no
   CONVERT→CAST rewriting). `src/tree/extract.py` drops its sqlglot
   internals; the DecisionTree model, conservation law, and
   graph_decision_sites contract are unchanged. Expected effect: the
   11 ED-sepsis gaps (6 CTE statements, 2 STUFF/FOR XML, 1
   UNION-INTO, 2 IF blocks) go to ~0 — ScriptDom parses every class
   (the 200 trace was 43/43).
2. **Native-parser law codified**: ADR 0001 amendment (production
   parsing/extraction = dialect-native parser, ScriptDom for T-SQL;
   non-native parsers only in the sanctioned dev-fallback zone, never
   a second implementation of a production capability) + CI plank:
   `import sqlglot` in src/tree/ (or any new production module) fails
   CI with the law named.
3. **Decision nodes enter the graph**: `decision` layer nodes +
   `step → decision` and `decision → column` edges, aliases resolved
   through the same machinery that resolves reads (incl. temp-table
   column lineage where reachable).
4. **The reachability law** (Sunny, 2026-08-19): every decision node
   lies on a path terminating at technical end-nodes OR carries a
   counted reason (`literal_only`, `parameter_only`) — connected or
   counted, no dangling decisions. Enforced as a 500 validation
   invariant.
5. **`parameter_default` site kind** for control-flow decisions
   (the `IF @StartDate IS NULL → fn_parse_date('MB-12')` default
   reporting window). **RULED by Sunny 2026-08-19: model it.** The
   tree captures the default-window decision as a first-class site so
   descriptions can voice it (the omission the deep trace flagged);
   graph_decision_sites' context allowed_values gains
   `parameter_default`; ED sepsis expected 488/488.
6. **Join map regenerates from graph_decision_sites** and
   `scripts/derive_dict_relationships.py` is DELETED — mechanically
   enforced: tests/test_derive_relationships.py fails the moment
   src/tree/extract.py stops importing sqlglot while the script still
   exists (no two paths for one goal). The regenerated map picks up
   the CTE-statement joins the bootstrap undercounted.
7. **Recorded fixtures re-recorded** (after Sunny's full tenant rerun
   on 1.25+): full fragments replace the truncated ones; decision
   trees join the recording so CI replays them.

8. **Port the indexer-reflection fix + property cache into
   `scriptdom_fabric.py`'s walkers** (from the 1.28.0 tree extractor):
   the famous 13,156-suppression counter reproduces locally and is
   overwhelmingly .NET indexer noise; fixing it should collapse the
   counter to ~0 and may recover the trace's 3 missing table reads
   (MED_MIX_COMPONENTS class). CHANGES PARSE OUTPUT: goldens +
   REMATCH answer keys must be re-certified deliberately, together
   with item 7's fixture re-record (now runnable locally).

## Exit evidence

Per the standing protocol: a refreshed TREE_PHASE1_ED_SEPSIS.md-style
artifact from the ScriptDom path — expected: 43/43 statements, ~442+
sites (CTE statements add theirs), gaps ≈ 0 or named, decision→column
edge counts, reachability tally — reviewed by Sunny before 1b is
called done.

**Join-map completeness criterion** (Sunny, 2026-08-19: "we can't miss
joins — later the LLM has gaps when drawing from the joins"): the
sqlglot bootstrap's measured blind spot is **33 unparseable statements
holding 192 JOIN keywords with zero evidence contributed** (the script
prints this tally). The ScriptDom-regenerated map must reconcile:
every JOIN occurrence in the corpus is either an evidenced pair or a
counted skip with a reason — blind spot 0. Until that reconciliation
passes, the join map stays status `planned` and the discovery engine
(ADR 0046) must not consume it.
