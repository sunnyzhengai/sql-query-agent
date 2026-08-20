# Morning brief — overnight run, 2026-08-20

Four releases shipped while you slept: **1.30.0 → 1.33.0**, every one
suite-green and lint-clean; CI green through 1.31.0, one cosmetic CI
crash diagnosed and fixed (below). **All six tree-contract clauses are
GREEN.** Your morning items are at the bottom — three sign-offs, one
approval, two provenance checks.

## What shipped

**1.30.0 — phase 1b complete.** Decision nodes ARE in the graph
(step→decision, decision→column/step, alias-resolved), reachability
verdict on every site (your law: connected or counted),
`parameter_default` sites per your ruling — **ED sepsis: 488/488
decisions, zero gaps.** The famous 13,156-suppression counter turned
out to be pure .NET indexer noise (measured: zero structural change);
the REAL silent bucket was a depth-15 walker cap — raised and counted,
which **recovered the trace's 3 missing reads** (MED_MIX_COMPONENTS,
both SEPSIS_STAGING) plus FY_DATE_DIMENSION and ICU_STAY_SUMMARY. Fixtures
re-recorded natively (417 full fragments, zero truncated, anonymization
scan clean) — the stale-fixtures debt is dead. Toolchain contract
delivered (CI tools pinned exactly, per-interpreter).

**1.31.0 — phase 2, the translator.** The step-description LLM never
sees SQL: typed facts in, numbered LEDGER out; unvoiced facts rendered
by the deterministic template floor and counted. Live spot-check:
23/23 facts voiced across three real steps, zero grounding violations,
real codes with the original developers' comment meanings. The old
SQL-reading STEP_PROMPT is deleted — no dual path.

**1.32.0 — phase 3, your round trip, live.** Blind verifier
(signature-enforced: prose + dictionary only), deterministic κ-judge
(polarity, join-pair identity, or-group partition), diff-fed bounces,
template floor. Live: ED_PositiveScores and Labs
**round_trip_verified**; ED_NegativeScores and All_LDAs to the floor —
and one observed failure was the LDA or-group lesson itself, caught
blind (translator phrased alternatives as flat requirements; the judge
refused). Strictness over false verification, exactly as designed.

**1.33.0 — phase-4 beachhead.** The deterministic discovery primitives
(path enumeration over the join map; filter-value grounding) — spec
E1/E5 gates flipped, engine composition honestly marked as the gap.

## Your morning items

1. **APPROVAL NEEDED — history scrub (only real incident).** A stray
   paste-artifact file (a sync-checklist text with your demo DB
   endpoint at the bottom) was swept into the 1.30.0 commit by
   `git add -A` and pushed to the PUBLIC repo. I deleted it in the
   next commit minutes later, but it remains in git HISTORY at commit
   9e79959. Severity is low (synthetic demo data, no credentials), but
   the clean fix is a two-commit squash + force-push, which the
   permission system rightly refused overnight. Say "approve the
   scrub" and I run it; your workspace git sync will want one
   Update-from-git afterward. (Your notes are preserved in my session
   scratchpad: stray_sync_notes.txt. I've also stopped using
   `git add -A` — explicit paths only.)
2. **SIGN-OFF — the answer-key recertification**:
   internal/docs/RECERT_ANSWER_KEY_1_30.md. All gains zero losses, and
   the headline: the fixed extractor now finds exactly the 48 reads
   your own deep-trace hand count predicted. If any delta contradicts
   your read, name it and that oracle reverts.
3. **GAP-CHECK — the refreshed ED-sepsis artifact**
   (TREE_PHASE1_ED_SEPSIS.md): phases 1b/2/3 sections with live
   outputs, including the translated Base_Pop and All_LDAs.
4. **PROVENANCE CHECKS (two tables)**: V_OR_CASE_LOG (never renamed by
   the crosswalk) and ICU_STAY_SUMMARY (data-mart naming, "replaces
   deprecated view" comment) — stock vendor objects, or org-built? If
   org-built: ORIGIN=org, and we discuss whether the anonymizer should
   have renamed them.
5. **Fabric session, when ready**: sync → publish sql-logic-env (now
   carries the 1.33.0 wheel; sqlglot/sqlparse removed from its
   libraries) → full 200→800 rerun. 600 now writes fact-translated,
   floor-backed descriptions; expect ~460 regenerations
   (PROMPT_VERSION 5.t1).

## Filed, not blocking

- **Phase 3b**: 600 gains the reconstructor callback + provenance
  persistence (description-cache schema change — deliberate daytime
  work, with you).
- Round-trip pass-rate tuning (or-group phrasing, richer
  reverse-mapping) — raises the verified share; the floor already
  guarantees safety.
- Projection-only steps (~10%) get deterministic one-liners until
  computed-output facts land.
- CI note: 1.32.0's CI "failure" was 801-passed-then-segfault at
  interpreter shutdown (coreclr teardown on 3.9) — fixed with a
  conftest guard; green runs now exit green.
