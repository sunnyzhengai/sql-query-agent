# Handoff — selective re-run + embedding carry-forward (scale economics)

**From:** dev session, 2026-08-18 (Sunny, during the demo rebuild: "each
time if one thing didn't load, we have to re-run the whole pipeline? for
a customer with thousands of procs and hundreds of thousands of
table/column nodes this will take long and cost a lot"). **To:** dev
session, post-demo.

## What is already incremental (state it, defend it)

- 600/610: content-hash caches — LLM spend only on changed SQL. The
  most expensive stage is already protected.
- 030: hash-based change tracking — only new/changed objects load.
- 300/400/800 full rebuilds are a DECISION: deterministic
  rebuild-from-truth beats incremental graph mutation (drift/corruption
  risk) while rebuild cost is minutes of CU. Revisit only when rebuild
  itself is the measured bottleneck.

## Gap 1 — 700 embedding carry-forward (the real cost at scale)

Catalog rebuild currently loses embeddings; every refresh re-embeds
rows whose search_text never changed. Fix = the 600 pattern: hash
search_text per node_id; on refresh, carry forward emb for unchanged
hashes; embed only new/changed rows. At 100k nodes with a one-name
change, the embed bill should be ~1 row, not ~100k.

## Field evidence 2 (same night): the hand-derived list was WRONG

The dev session prescribed 300 -> 400 -> 700 -> 800 after a
metric-names reload and omitted 600 — 300's rebuild wiped 600's
in-place node descriptions, 400 built bare cards, and the demo tenant
served descriptionless answers until a Kusto check caught it (28
canonicals, 432 steps, 0 described). Cache made the repair free, but
the lesson is structural: enrichment dependencies (300 invalidates
600's enrichment; 600 invalidates 700's embeddings) MUST be encoded in
replan, not remembered by anyone — the expert in the loop got it wrong
on the first real try.

## Gap 2 — registry-derived re-run advisor ("replan")

TABLE_REGISTRY already IS the dependency DAG (owners + consumers).
Build a small pure function + utility surface:

    replan(changed_tables) -> ordered minimal notebook list

e.g. replan({"input_metric_names"}) -> [300, 400, 600, 700, 800]
(skip 200: not a consumer; 600 IS required — its node enrichment is
invalidated by 300's rebuild even though its CACHE is hash-keyed;
the run is all cache hits and near-free, but it must run).
Surface it three ways: a src function with tests; a line in 500's
output ("inputs changed since last run: X — minimal re-run: ...");
and the /troubleshoot agent command (admins ask "what do I re-run if I
update the dictionary?" and get the computed answer). This turns the
tribal knowledge I applied by hand today into contract-derived product.

## Non-goals (for the record)

- Incremental graph mutation in 300 (rebuild-from-truth stands).
- Distributed/partitioned parse in 200 — 200 re-parses all sources
  today; acceptable until a measured estate says otherwise (parse is
  CPU-cheap ScriptDom, no external spend). If needed later, the 030
  tracker's hashes already identify unchanged sources to skip.
