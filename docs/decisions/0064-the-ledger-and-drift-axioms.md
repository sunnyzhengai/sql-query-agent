# ADR 0064 — Group L: the ledger and drift axioms (closing the crosswalk gaps)

**Status:** ACCEPTED 2026-09-01 — review-authored from the axiom
crosswalk audit; **RATIFIED by Sunny same-day with all three §6 calls
ruled as recommended.** Group L is in SPEC v0.8 §14h; L1 and L2 ship
ENFORCED (`tests/test_ledger_contract.py`, four checks, verified
against injected violations); L3 is ENFORCED by citation. The
crosswalk's Direction 2 now closes: `AXM_UNMAPPED` retains only the
three meta entries.

## 1. Context — how the gap was found

The 2026-09-01 crosswalk audit
([AXIOM_CROSSWALK.md](../architecture/AXIOM_CROSSWALK.md)) mapped every
spec axiom to its framework parent and back. Direction 1 closed: all 41
spec axioms descend from `docs/AI_VIA_AXIOMS.md`. Direction 2 left five
framework axioms unimplemented — three are meta (laws *about* having a
spec; circular to implement) and **two are real:**

- **`axm:R2` — drift fires mechanically.** The funnel, the reachability
  registry, and every CI closure check *are* drift firing. SPEC §3b
  asks the drift question of each new artifact class, but no axiom
  states it, so nothing checks that a new declaration acquired one.
- **`axm:R4` — the ledger.** Events are append-only; aggregates are
  derived, never stored. SPEC §4 lists `Event (append-only)` in the
  signature Σ — the spec *presumes* the law — and `TABLE_REGISTRY`
  carries a `write_mode` field with 10 tables marked `append`. No axiom
  states it.

**Why this is a finding, not bookkeeping.** SPEC §1 claims the spec is
**closed**: "an absence is visible as a gap in a finite list, not as a
surprise found by reading code." A law that code enforces but the spec
never states is exactly the failure that claim promises to prevent.
These two are the live counterexamples, and they were found by a
mechanical audit — which is the system working as designed.

## 2. The measurement (what is already true)

Verified 2026-09-01 before drafting, per the Echo Law's build-first
posture — we state what exists before proposing what doesn't:

- `TABLE_REGISTRY.write_mode` exists: **39 overwrite, 10 append**, 11
  unset (all non-active/planned tables).
- `tests/test_table_contracts.py` asserts every ACTIVE table declares
  `write_mode in ("overwrite", "append")` — **the label is validated.**
- **Nothing checks the label is obeyed.** No test asserts that a table
  declared `append` is never written with overwrite semantics. The
  contract is a declaration with no enforcement behind it.
- **No regression guard exists for R4's founding incident** — the
  purged in-place usage counter (a stored aggregate mutated per query).
  Nothing prevents its return.

## 3. Decision — SPEC Group L (Ledger), three axioms

Group letters D, E, R and others are taken in Φ; **L** is free and
mnemonic.

**L1 — append-only is declared and obeyed.**

    ∀t ∈ Tables. write_mode(t) ∈ {overwrite, append}
    ∧  write_mode(t) = append → no writer of t uses overwrite semantics

*Gloss:* a table that declares itself a ledger may only ever be
appended to. The declaration already exists; this axiom adds the second
half — that code obeys it.
*Binding:* the existing contract check (label legality, ENFORCED) plus
a NEW AST check that no writer of an `append` table calls an
overwriting write. **Status on adoption: PARTIAL** → ENFORCED when the
AST check lands.

**L2 — aggregates are derived, never stored.**

    ∀a ∈ Aggregates. a = f(Events),  f deterministic and recomputable
    no counter is mutated in place

*Gloss:* usage weights, funnel counts, and every governance number are
recomputed from the append-only event log — never incremented in a
row. This is `spec:D3` (projections are functions of the record)
applied to *counts*, and it is the law the purged UsageTracker broke.
*Binding:* a regression test pinning the incident — mutating a stored
count in place fails. **Status on adoption: GATED** (strict-xfail until
the test lands, per the ADR 0044 pattern).

**L3 — every declaration has a firing mechanism.**

    ∀d ∈ Declarations. ∃m. fires(m, divergence(d))

*Gloss:* SPEC §3b's third question, promoted from a review ritual to a
checkable axiom: when reality diverges from a declaration, something
mechanical fires — a red build, a checklist row, a funnel bar.
"Someone would notice" is the definition of a missing feedback loop.
*Binding:* by CITATION of what already exists and passes — the registry
closure checks (extraction, capability, notebook, trace, integration,
shape, table), `src/governance/funnel.py`, `src/reachability.py`. Each
registry's closure test IS the firing mechanism for its declaration.
**Status on adoption: ENFORCED (by citation)** — the ADR 0059 Q3
precedent, where the equations predated the axiom.

## 4. What this is NOT

- **NOT new machinery for L3.** The mechanisms exist; the axiom names
  them so a FUTURE declaration without one is a visible gap rather
  than an omission nobody was asked about.
- **NOT a rewrite of D3.** D3 governs projections; L2 governs counts
  specifically, because the incident was a count.
- **NOT a claim that the ledger is fully enforced.** L1 ships PARTIAL
  and L2 GATED, stated honestly per SPEC §3's status vocabulary.

## 5. Consequences

- Direction 2 of the crosswalk closes: every non-meta framework axiom
  reaches a spec axiom. `AXM_UNMAPPED` retains only the three meta
  entries, and `tests/test_axiom_crosswalk.py` keeps it that way.
- SPEC's §1 closure claim becomes true again.
- One new check to build (L1's AST pass) and one gated test to flip
  (L2's regression pin). L3 costs nothing but the citation.
- The crosswalk audit becomes a repeatable instrument: run it after any
  axiom change in either document.

## 6. Calls — ALL RULED 2026-09-01 (Sunny, as recommended)

1. **Scope of L1's check — RULED: targeted.** Writers of `append`-
   declared tables only. The capability registry's `Uses ∖ S = ∅`
   pattern generalizes it later if an undeclared-table class appears.
   **Implementation note (field find during the build):** the check
   could NOT be an AST pass over `src/` as the draft assumed —
   **`src/` contains no Delta writes at all.** Writes live in the
   `*.Notebook/notebook-content.py` sources, so the check scans those,
   the same surface `tests/test_notebook_contract.py` already governs.
   The draft's "AST check over src/" would have scanned an empty set
   and reported green forever — a false-assurance check, worse than
   none. Recorded because the generator clause applies: the lesson is
   that a check must be proven against an injected violation before it
   is trusted.
2. **L2's schedule — RULED: pin immediately.** Not strict-xfail —
   the guard passes today, so it ships ENFORCED rather than GATED. The
   corpse (the purged in-place usage counter) is now a permanent
   fixture (`axm:J3`, corpse-to-fixture).
3. **The group letter — RULED: L.** "Ledger" is distinct from residue
   (H) and derivation (D); the letter was free in Φ.

## 6b. Verification (how we know the checks work)

Both new checks were proven against injected violations, not merely
observed green:

- **L1:** flipping `ops_funnel`'s write from `mode("append")` to
  `mode("overwrite")` in `500_validate` produced
  `500_validate:397: ops_funnel is declared append in TABLE_REGISTRY
  but written with mode('overwrite')`. Notebook restored; `git diff`
  clean.
- **L1 regex hardening:** the first draft was line-bounded and missed
  `gov_feedback_events`, whose write wraps across three lines with
  backslash continuations. Fixed to span newlines while refusing to
  splice across a second `.write`.
- **L1 false-positive guard:** `500_validate:191` writes
  `ops_build_summary` with NO `.mode()` — legal, because it is the
  first-creation branch behind `spark.catalog.tableExists()`. The
  check accepts a no-mode write only when that guard is nearby, so
  correct code is not flagged.
- **L2:** `usage_count += 1`, `usage_count = usage_count + 1`, and
  `weight += 1` are all flagged; `weights = derive_from(events)` is
  not.

## 7. Relations

- **ADR 0047** — the shadow spec; §16's amendment rule is why this ADR
  exists at all (axiom changes require a recorded decision).
- **ADR 0059** — the precedent for ENFORCED-by-citation (Q3).
- **ADR 0023** — the usage-weighted flywheel, whose weights L2 governs.
- **ADR 0044** — the strict-xfail gate pattern L2 uses.
- **`axm:R2`, `axm:R4`** — the framework laws this closes.
