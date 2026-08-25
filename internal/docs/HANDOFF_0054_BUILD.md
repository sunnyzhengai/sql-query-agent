# Handoff — ADR 0054 build: the governance red-flag sweep

**From:** review session, 2026-08-23 (sequenced on P0 closure; Sunny's
pre-demo ruling stands). **To:** dev session. **Mode: build order —
the ADR is the spec; this file is sequencing + acceptance.**

## The spec

docs/decisions/0054-governance-red-flags-governed-plurality.md —
ACCEPTED, all four ratifications ruled, §3b answers filled (your
2026-08-23 pass). Build exactly that: the sweep (misnomer /
duplicate / cousin-conflict flags at catalog grain, `_content_key`
imported never re-implemented, conservation partition asserted),
`gov_red_flags` + dispositions (append-only, mandatory reason on
accept/retire), the typed edges (`variant_of`, `supersedes`,
`duplicate_of`), official-for-scope property, reachability rows,
agent named-op access (census kind 'flag' / retrieve), the
official-first + variants-exist stamp, admin tile, Fabric export.

## Sequencing notes

1. **One tenant rerun carries everything:** the W13a resolver edges
   are already waiting on a 300→800 + 700 rerun — land the sweep's
   pipeline artifacts first so Sunny runs ONCE for both payloads.
2. **Echo Law applies from birth:** every new op/stamp/query ships
   with its smoke case (engine_smoke totality will force it), its
   L0 tests, and its live probe before first suite run.
3. **The supersedes-oracle flip:** when the edges ship, the Q4
   legacy fixture's oracle flips from forbidden-phrase to
   required-edge — dev flips it in the same change, never separately.
4. Pin discipline: new named op(s) for flags = CONSCIOUS pin bump,
   recorded, same as lineage/compare precedent.

## Acceptance (project law — before any surface ships)

- Real ED-sepsis-corpus flag output for Sunny's gap-check. Expected
  shapes she will look for: the Base_Pop misnomer (12 catalog steps,
  N distinct logics, INFO grade), the Legacy-v1 cousin conflicts,
  at least one duplicate-hash pair if the corpus holds one.
- Conservation partition sums clean; live-audit leg green; zero
  dispositions referencing absent flags.
- Suite: `flags` family + sameness family reading verdicts; honesty
  1.00 everywhere, standing law.
- The walk gains its flags section; the demo QA gate gains "what
  governance red flags exist?".

## RUNBOOK (Sunny — the ONE combined rerun, both payloads)

1. Workspace → `sql-logic-env` Environment → **Update from git** →
   confirm CustomLibraries shows
   `sql_query_agent-1.57.0-py3-none-any.whl` → **Publish**, wait for
   Published.
2. Workspace → **Update from git** (brings the new
   `320_red_flag_sweep` notebook + everything else).
3. Run, in order (or ask dev to fire the job-API chain):
   **300 → 320 → 400 → 500 → 600 → 610 → 700 → 800.**
   This single pass mints BOTH payloads: the W13a resolver's column
   edges (expect the projection count to jump ~153 → ~2,200) and the
   gov_red_flags table.
4. In the KQL database (aivia semantic catalog): **New → OneLake
   shortcut** → the Lakehouse `gov_red_flags` Delta table (same
   pattern as graph_nodes).
5. SQL Intelligence Agent: dev re-injects the updated instructions
   (governance section + /redflags) via API — just hard-refresh, spot
   check "what governance red flags exist?", and **Publish**.
6. Gap-check: read internal/docs/RED_FLAGS_GAPCHECK.md against your
   expectations (Base_Pop misnomer at INFO, the Legacy-v1 cousins);
   after the rerun the same numbers should come back live from
   "what governance red flags exist?".

## OPS FINDS from the rerun evening (2026-08-24, review session) — next small order

All three are Echo Law first-stage: mechanism named, build-or-defer
to be recorded (review recommends BUILD on all three — each is
small and each class recurs by construction):

1. **Shortcut create-then-verify.** The API shortcut create 201'd,
   REGISTERED the name (list showed it, UI create failed on
   name-conflict) but never MOUNTED (invisible, unqueryable — KQL
   400). Review session deleted the ghost via API; Sunny's UI retry
   then succeeded (count 83). Mechanism: any automated shortcut
   create polls the QUERY path (`table | count`) until green or
   fails loud — the registration list lies; the 201 vouches for
   phase one of a two-phase operation. Belongs in the updater story.
2. **org_config referential integrity.** The 610 failure class:
   tenant config referenced the retired Delta Agent. Mechanism: a
   preflight/live-audit leg resolving every tenant-artifact id in
   org_config against live APIs — dead reference fails loud with
   its error contract BEFORE a chain burns 45 minutes.
3. **Eventhouse rename (cosmetic, pre-capture).** The active
   semantic catalog eventhouse still carries the retired name
   "probe-eh" (the Item-4 correction's "EH rename+ref-edits" step
   was never executed). Rename + reference edits before capture day
   so no screen says "probe".

## LIVE GAP-CHECK FINDS (Sunny on the workbench, 2026-08-24 evening)

Wins confirmed live: compare called FIRST ROUND on the original
corpse question, catalog ids resolved (W12 dead in the field);
hash-partition + diff displayed; 0054 governance stamps firing on
metric retrieve; register fix holding (business voice, no SQL);
resolver edges live (PATIENT_MRN → 8 selects).

- **FIND W15 (pre-capture priority — the recorded known-limit, now
  a live specimen): caption inverted the compare direction.**
  Machine showed 2 distinct hash groups + a 103-line diff (logic
  DIFFERS); commentary said "similar… confirms they are aligned."
  Structural gate passed (compare present) — direction unchecked.
  Remedy (M4-clean, the proven stamp+echo pattern): op_compare's
  headline stamps a TYPED verdict word ("2 groups — logic DIFFERS" /
  "1 group — logic IDENTICAL"); gate duty: a caption over a
  displayed compare must echo the verdict word; fixture: this
  question, graded on direction. This is the demo's drift beat —
  fix before capture.
- **FIND W16 (display, W1 family): governance stamps flood** — 7
  near-identical cousin-conflict sentences on one headline; fold to
  "in 7 cousin-conflict flags (no official designated) — retrieve
  flags for members."

## GAP-CHECK EXECUTED (Sunny live, 2026-08-24 evening) — ACCEPTANCE READS PASSED, pending her word

- census(flag): **83 exact, live**, matching RED_FLAGS_GAPCHECK.md;
  30-row fold; honest verdict. PASS.
- ED_DEPARTURE_TIME column lineage: false empty DEAD — filters: 5
  named metrics, selects: 6, step locations on every row. PASS on
  the machine surface.
- **FIND W17 — ECHO, mandatory by law:** caption said "11 metrics
  filter" — 11 relation ROWS counted as metrics (filters=5). Same
  class as the 1.56.0 pairs-as-metrics corpse; the distinct-count
  stamp mechanism covered the table path, not the column path.
  Extension is mandatory (no deferral): column-lineage notes stamp
  distinct-metric counts PER RELATION ("Filters: 5 metric(s) — …;
  Selects: 6 metric(s) — …"), grader extended.

Dev's next order, consolidated: W15 (compare verdict word — PRE-
CAPTURE), W17 (echo, mandatory), W16 (stamp folding), F1 (error-tile
collapse, DEMO_FEEDBACK_FRIENDS), plus the three ops finds above.

## RESULTS (dev appends)

### 2026-08-23 — BUILT: sweep, surfaces, contracts, acceptance artifact (release 1.57.0)
- **Sweep** (src/governance/red_flags.py): misnomer / duplicate /
  cousin_conflict at catalog grain; `_content_key` imported;
  RATIFIED severity boundaries encoded (step names proc-local INFO;
  shared-scope CONFLICT; duplicates INFO; cousins CONFLICT-on-
  divergence); strict token-containment cousin rule (the Legacy-v1
  shape; no similarity metrics); deterministic flag ids (spec:E2);
  receipts on every row (members+hashes, blast radius WITH basis,
  drill query); conservation partition asserted. Disposition fold
  (append-only; reason MANDATORY on accept/retire enforced — a
  missing reason is a rejected ROW, never silent) mints
  variant_of/supersedes/duplicate_of edges and official-for-scope
  properties; the WRITE surface is the recorded ADR 0050 follow-up.
- **Pipeline**: 320_red_flag_sweep notebook (contract-registered,
  REQUIRES_ENGINE 1.57, precondition-gated) after 300; gov_red_flags
  (active) + gov_flag_dispositions (planned/optional) schema
  contracts; installation guide + scheduled-pipeline order updated.
- **Agent surface**: census kind `flag` (exact count, "flags
  disclose, never gate" in the stamped universe, named remediation
  on pre-sweep stores), flag retrieve (members surfaced for next
  hops), step-name stamp carries the recorded flag verdict beside
  the sameness caveat (W6 closed systematically — single-row machine
  reads), metric retrieval stamps variants-exist + official
  designation state. CONSCIOUS pin bump (census enum + one
  tool-property sentence): new pin d9f8df5c…, updated in
  answer_evals + test_turn_engine with dated comments.
- **Echo Law from birth**: reachability row catalog:flag (marker-
  verified); engine-smoke case (flag surface or named remediation);
  offline dispatch case unchanged-by-construction (census); 14 L0
  sweep tests + 7 L0 flag-ops tests; suite `flags` family with a
  DISCLOSED requires-table skip (never silent) and a store-derived
  count+classes oracle.
- **Q4 supersedes-oracle flip**: nothing to flip in this change —
  the relationship_claim oracle derives from the store's edge count,
  so it flips ITSELF the moment a retire disposition mints the first
  supersedes edge (design accepted by review as exactly right;
  sequencing note 3 satisfied by construction).
- **Acceptance artifact**: internal/docs/RED_FLAGS_GAPCHECK.md from
  the recorded corpus — 83 flags: Base_Pop misnomer 12 steps / 12
  distinct logics at INFO (the shape named in the order), 9 cousin
  conflicts incl. every Legacy-v1 pair, 0 duplicates (the corpus
  holds none — stated, class L0-proven), 74 step misnomers
  inventoried, conservation clean (460 swept = 292 + 162 + 6
  no_fragment).
- **Release 1.57.0**: version bumped, wheel built, environment item
  updated, CHANGELOG entry, release-consistency tests green; walk
  gains section I (flags, with count oracles + the demo QA
  question); TRACE_MAP/NOTEBOOK_MAP regenerated; ADR 0054 registry
  entry filled (un-sanctioned — modules and tests now exist).
- Full gates + live smoke to run at close (recorded below).

### 2026-08-24 — close-out gates (run by review session; dev's session ended before recording)
Full suite **1,052 passed** + 5 xfailed, ruff clean. Live
engine_smoke pending capacity — runs with the combined rerun (it
must, per the Echo Law: the flag surface's live case executes then).
Gap-check artifact verified present and well-formed; review notes:
the sweep independently re-derived walk finding Q6 (the "Sepsis
Encounters" family, 4 logics) and surfaced Severe-vs-Non-Severe as a
cousin pair — a textbook first DISPOSITION candidate (intentional
variants; accept or label, never merge). Awaiting Sunny's gap-check
verdict, then the combined rerun.

### 2026-08-24 — LIVE SMOKE GREEN (dev): the pending leg closed
The graph_nodes/graph_edges shortcut outage self-resolved (transient
Fabric incident — no pipeline was running; native KQL tables were
unaffected throughout; a background watch confirmed recovery).
devtools/engine_smoke.py then ran green end to end through the real
dispatch: all 9 cases including the W12 permanent reproduction and
the NEW census(kind=flag) case, which verified the NAMED remediation
on the pre-sweep store ("run 320_red_flag_sweep…" — exactly the
honest state until Sunny's combined rerun). Echo Law fully
satisfied at birth; the same case flips to enumerating live flags
after the rerun. BUILD ORDER COMPLETE — open items are Sunny's:
gap-check verdict, then the combined rerun (runbook above).

### 2026-08-24 — THE COMBINED RERUN (fired by dev on Sunny's "go")
Preflight found Sunny had already done runbook steps 1–2 (workspace
synced — Fabric committed back 320's .platform re-stamp — and the
1.57.0 wheel PUBLISHED on the environment). Chain fired via job API:
300 (2:36) → 320 (1:44, first tenant run clean) → 400 → 500 → 600
all Completed; **610 FAILED** (Spark session cancelled).
FIELD CORPSE — retirement completion gap: 610 reads
fabric_graph.data_agent_id from the LAKEHOUSE org_config.yaml, which
still pointed at the Delta Agent DELETED on 2026-08-22 (the local
copy was repointed for Round 4; the tenant copy has one pipeline
consumer — 610 — and nobody repointed it; the retirement runbook
never said to). Fix: one-line OneLake patch → SQL Intelligence Agent
id; 610 then completed in 79s. Runbook step 7 gains REPOINT FIRST as
step 0. (OneLake write lesson: the DFS flush needs an explicit
Content-Length: 0 — the first flush 400'd after the truncating
create; re-flush recovered, file verified whole, 3,924 bytes.)
Resume chain 610 → 700 → 800 running at time of writing.
PAYLOAD VERIFICATION (live store): projection edges **153 → 2,295**,
decision→column **2,744** — the W13a resolver's tenant numbers,
richer than the local build's 2,251. gov_red_flags shortcut created
VIA API (POST items/{kqlDb}/shortcuts → 201; runbook step 4 needs no
UI) — count verification pending shortcut hydration.

### 2026-08-24 — CORRECTION + CLOSE-OUT (dev): the shortcut claim above was WRONG
**Correction (per the review's ops find 1): "runbook step 4 needs no
UI" is FALSE.** The API create was a GHOST — registered (201, listed)
but never mounted; the review session deleted the ghost and SUNNY'S
UI RETRY is the shortcut that works. The 201 vouches for phase one of
a two-phase operation.
**Final state — everything green:**
- gov_red_flags LIVE and queryable: **83 flags (74 misnomer/INFO, 9
  cousin_conflict/CONFLICT)** — matching the local gap-check
  number-for-number.
- engine_smoke fully green INCLUDING the flag surface in live mode
  ("flag surface live: 83 flag(s)") — the case's second acceptance
  state, reached.
- SQL endpoint metadata refreshed (dbo.gov_red_flags: Success); agent
  draft carries the governance instructions + /redflags (verified
  landed, 15,430 chars). Remaining for Sunny: tick gov_red_flags in
  the agent's Lakehouse source elements (UI-only), spot-check, Publish.
**Ops finds 1+2 BUILT (Echo Law, review's recommendation):**
- devtools/create_kql_shortcut.py — create-then-VERIFY: polls the
  QUERY path until green or deletes the ghost and fails loud with the
  remediation; all future shortcut automation goes through it.
- devtools/org_config_audit.py (+L0, tests/test_org_config_audit.py)
  — resolves every tenant-artifact id in org_config (local or
  --tenant Lakehouse copy) against live APIs; dead reference fails
  loud with its remediation BEFORE a chain fires. First live run:
  repointed agent resolves; graph_model_id flagged 404-stale
  (WARN-only, no reader; fix rides the rename work).
**Ops find 3 (eventhouse rename) staged, not executed** — tenant UI
rename is Sunny's; the ref-edit list (git grep probe-eh, excluding
the retired-agent folders): devtools/{agent_live_eval,
agent_robustness_suite, answer_evals, robustness_suite}.py,
devtools/eventhouse_{setup,probe}.kql, src/orchestrator/cli.py,
src/webapp/main.py, plus the SQL Intelligence Agent's
kusto-probe-eh datasource folder name (re-syncs on rename) and
org_config search.kusto_db — rename + edits + org_config move
together, then org_config_audit --tenant proves the store leg.
Suite 1,054 passed + 5 xfailed, ruff clean.
