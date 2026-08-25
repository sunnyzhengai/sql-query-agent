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
