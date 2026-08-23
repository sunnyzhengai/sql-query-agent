# Handoff — Fabric lineage mitigation: readers_of_table on the Eventhouse surface

**From:** Sunny's ruling via review session, 2026-08-23. **To:** dev
session. **Mode: work order** (bounded; design details yours within
the constraints).

## The ruling (recorded in HANDOFF_REMATCH_ROUND4_GOAL, 2026-08-23)

Ship the Fabric-side mitigation. Round 4 showed the SQL Intelligence
Agent answers readers-of-table questions by name association across
the corpus's name-cousins when it doesn't route to the graph (real
metric names, wrong lineage — see REVIEW_ROUND4_RECORD_AUDIT.md).
Customers get the better artifact; the product wedge rests on what
Fabric cannot copy (typed honesty verdicts, code-enforced routing).

## Scope

1. **readers_of_table Eventhouse stored function** — mirrors the
   homegrown TABLE_USED_BY_QUERY semantics: parsed lineage edges,
   NEVER name mentions; exact table-name scoped; whole-token matching
   on any fallback path (the token-matching law every phrase-taking
   op inherits at birth — 1.56.1 lesson, it lives in the lineage op's
   docstring). Returns distinct metrics (business_name + ref) plus
   the table identity, so a Basis line can say "N certified metrics
   read TABLE, from parsed lineage."
2. **Agent config**: fewshot(s) binding readers-of-table question
   shapes to the function; per-source routing description updated.
   Data-shaped, instruction-light (ADR 0020) — no casebook, no
   hardcoded answers (the function teaches HOW, examples stay
   schema-shaped).
3. **Column variant**: your call whether filters-on-column rides the
   same function or its own (the COMPILED_CONTEXT false-empty was the
   other reach miss) — decide from the exported table shapes, record
   the choice here.
4. **Verification, scripted only** (constitution: never casual chat):
   a small fixed-question check through the API adapter — the two
   Round-4 lineage questions plus one cousin-table trap — run N=3 for
   routing consistency, results recorded in this file. This is config
   verification, NOT a rematch; Round 4 stays closed (one-run
   protocol). A measured before/after would be a Round 5 — Sunny's
   call, not implied here.

## Constraints

- Zero homegrown engine/prompt/tool changes — the pin stands; this is
  entirely Fabric-surface work.
- PHI gate: function returns names/refs/counts only — no expression
  SQL in results.
- Tenant steps Sunny executes by hand get a numbered plain-runbook
  section (function creation, fewshot import, republish) — jargon
  stays here.
- Reachability/registry: if the function's query class is new on the
  export surface, the ADR 0052 contract row applies.

## Also open (from HANDOFF_ROUND4_RECORD_FIXES review verdict)

- The answer_evals INFRA-SKIP finding: implement the promised >20%
  abort, per-family skip counts in board + dump, narrow the except
  (or re-raise unrecognized types). One small patch, not a blocker.

## RUNBOOK (Sunny — everything else is already done via API)

1. Open the workspace → `SQL Intelligence Agent` → hard-refresh the
   tab (stale sessions hide API edits).
2. In the Explorer panel, under the Eventhouse source → Functions:
   **tick the two unticked checkboxes** — `readers_of_table` and
   `column_usage` (leave `semantic_search` ticked). This CANNOT be
   done via API — the service assigns element ids from live schema.
3. Save (toolbar disk icon) if it lights up.
4. Optional 30-second spot check in the test pane: ask "which metrics
   use the IP_SEPSIS table?" — the step expander should show a call
   to `readers_of_table` (not hand-written SQL/GQL).
5. Click **Publish**.
6. Tell dev "published" — dev runs
   `python3.11 devtools/verify_lineage_mitigation.py` (N=3, scripted)
   and appends the results below.

## RESULTS (dev appends)

### 2026-08-23 — shipped; verification pending republish
- **Eventhouse functions LIVE** (created via mgmt API, DDL in
  devtools/eventhouse_setup.kql §4b): `readers_of_table(p_table)` and
  `column_usage(p_column)`. Both: parsed edges only, exact-name match
  first, whole-token `has` fallback ONLY when no exact name exists,
  disclosed in a `matched` column; names/refs only (PHI-safe).
- **Probes (store, all pass):** (a) readers_of_table('IP_SEPSIS') →
  exactly the certified 5, matched=exact; (b)
  readers_of_table('IP_SepsisEncounters') → its OWN 7 readers — and
  they are precisely the "Legacy v1"-family names Fabric mis-attributed
  in Round 4, so the cousin trap now resolves correctly by
  construction; (c) readers_of_table('ED') → token fallback hits only
  real ED-token tables (6), zero AGGREGATED-class substring matches;
  (d) column_usage('COMPILED_CONTEXT') → 5 filters rows, matched=exact.
- **Column-variant decision (scope item 3): SEPARATE function.**
  `column_usage` carries both relations in one result
  (relation='filters'|'selects') mirroring the homegrown _column_usage
  pairing, but it is its own function, not a mode of
  readers_of_table — one question shape per docstring is what steers
  the Fabric source router (the per-source-description finding), and
  table-grain vs column-grain are different question shapes.
- **Root-cause find while editing instructions:** our OWN instructions
  prescribed the disease — the "Lakehouse alternative" for lineage
  taught `LIKE '%table_name%'` (substring name-match). Round 4's
  name-association answers followed our fallback, not free
  improvisation. Section rewritten: KQL functions PRIMARY, Graph
  Model for multi-hop shapes only, LIKE-lineage banned in text.
- **Agent config updated via updateDefinition (Succeeded, draft):**
  aiInstructions regenerated from the repo md (13,205 chars); KQL
  source userDescription gained the lineage-routing paragraph; the two
  functions added to the KQL source's selected elements; KQL fewshots
  replaced from NEW repo file notebooks/kql_agent_fewshots.json (4
  pairs — lineage fewshots use ED_ENCOUNTERS_FACT / BASE_GROUPER_ID /
  PATIENTMRN, deliberately DIFFERENT from the verification questions
  so N=3 tests generalization, not fewshot recall; the KQL-source
  config now lives in git, closing the never-synced gap that made the
  Graph Agent's config unique).
- **Verifier ready:** devtools/verify_lineage_mitigation.py — 3 fixed
  questions (IP_SEPSIS readers / IP_SepsisEncounters cousin trap /
  COMPILED_CONTEXT filters), N=3 each, oracles derived live from the
  store functions, cousin-leak detection with the also-expected
  carve-out. L0-tested (tests/test_verify_lineage_mitigation.py).
- **INFRA-SKIP finding closed** (also-open item):
  devtools/answer_evals.py — except narrowed to
  requests.RequestException (anything else re-raises as an engine
  bug), >20%-of-attempted abort implemented (exit 3, min 10 attempts
  floor), per-family skip counts in the board, skip rows in the dump,
  all-skipped families surface explicitly and fail the run.
  L0-tested (tests/test_infra_skip.py). Suite + ruff green.
- **Awaiting:** Sunny's Publish (runbook above) → N=3 run → results
  appended here.

### 2026-08-23 — walk corpse: the token law's THIRD birth + element-id lesson
Sunny's post-refresh walk, "how many metrics contain ED logic": the
draft agent free-wrote `LIKE '%ed%'` over four catalog columns → "21
of 28 metrics" (substring matches COMPILED and every past-tense
word). True token count: 2. Honest Basis (method disclosed), wrong
result — same question was a false-EMPTY in Round 4; over-match and
false-empty are the two faces of the missing token law (census
1.50.4 → lineage op 1.56.1 → Fabric catalog-search 2026-08-23).
Source found in OUR OWN config again: the Lakehouse fewshots still
taught `LIKE '%table_name%'` lineage and `LIKE '%keyword%'` metric
lookup. Fixed (updateDefinition Succeeded, verified): all substring
fewshots replaced (exact-id lookup after semantic_search; token-exact
'%.table' lineage form; NEW token-bounded bracket-class count
fewshot), token-matching rule added to instructions ("Token matching
in EVERY text search", Basis must state token vs exact), repo files
notebooks/delta_agent_fewshots.json + instructions md updated first
(config-as-code, then injected).
ELEMENT-ID LESSON: API-added element leaves with minted GUIDs are
DROPPED — the service re-derives the element tree from live schema
with its own ids (semantic_search's id changed on refresh). Function
selection must be ticked in the UI; runbook amended below.

### 2026-08-23 — VERIFIED: N=3 scripted verification, 9/9 PASS
Sunny ticked the two functions and published; dev ran
devtools/verify_lineage_mitigation.py against the PUBLISHED agent via
the MCP adapter. Result — every run, every question, full carry, zero
cousin leakage:
- exact_table ("which metrics use the IP_SEPSIS table?"): 3/3 PASS,
  5/5 certified readers carried each run.
- cousin_trap ("which metrics use the IP_SepsisEncounters table?"):
  3/3 PASS, 7/7 of ITS OWN readers carried, zero IP_SEPSIS-family
  names leaked — the Round-4 name-association disease does not
  reproduce against the trap corpus.
- column_filters ("which metrics filter on the COMPILED_CONTEXT
  column?"): 3/3 PASS, 5/5 filtering metrics carried — the Round-4
  false-empty is closed.
Routing consistency was the point of N=3: 9/9 identical-quality
answers. The mitigation closes BOTH Round-4 reach misses (lineage
false-empty, name-cousin association) and the routing inconsistency
on the shipped artifact. Round 4 itself stays closed (one-run
protocol); any measured before/after is a Round 5 — Sunny's call.
WORK ORDER COMPLETE.
