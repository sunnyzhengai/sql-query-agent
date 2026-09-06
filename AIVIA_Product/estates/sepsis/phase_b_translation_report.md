# Phase B translation census — the ED-sepsis corpus (Sunny's gap-check)

**Phase B of the twin-graph ruling (ADR 0077), built 2026-09-06.**
The TRANSLATOR — the parser's twin, KG2b's one writer — ran over all
28 procs in the same run as the parse. Every tree now has a stored
meaning twin. This report is the phase gate per the ED-sepsis
acceptance law. Registries at v1.3.0 (one build-time correction,
finding T-1 below).

## The conservation equation, live

`translated + gap == every parsed node` is asserted INSIDE
`translate()` on every file, every run — a mismatch raises, never
warns. Corpus-wide:

| Measure | Count |
|---|---|
| Parsed nodes == twin nodes | 14,865 |
| — translated | 13,993 (94.1%) |
| — gaps (reason-coded) | 872 (5.9%) |
| Degenerate conditions (translated, voiced never) | 24 |
| Coverage gaps (readable-name fallback, counted) | 3,208 |
| Stored twins (`meaning_twin` nodes, file quantum) | 28 |

By kind: 6,961 reference · 3,397 projection · 1,991 condition ·
761 source · 522 statement · 333 selection · 28 file · 872 gap.

## Finding T-1 — the nine-kind library was missing its composites

PB-1's own law ("every meaning node carries a library kind") met the
file root and found the draft library had no kind for it: the nine
kinds covered scope-level-and-below, but the homomorphism law reaches
EVERY grain. **file** and **statement** joined as composite kinds
(registry v1.3.0, correction cited in the converter — the F7
DistinctPredicate pattern: a build-time catch, recorded where it
landed). Your call at gap-check: bless the two composite kinds or
rule a different treatment for the top grains.

## Finding T-2 — the gap census mirrors the mapper exactly

All 872 twin gaps trace 1:1 to what the mapper already counted:
unmapped statement kinds (SET/DECLARE/INSERT/CREATE INDEX/TRUNCATE/
WHILE…, 95 statements), unmapped expressions (19), and their
subtrees. No new loss — the twin is honest about exactly what the
parse is honest about. When a statement kind gets mapped, its twin
starts translating with zero translator changes.

## Finding T-3 — coverage gaps quantify the documentation debt

3,208 references translate by readable name because no dictionary
words exist — the same debt the intake already counts (242
undocumented org-catalog columns + the unresolved-ref classes), now
visible at the reference grain. 1,636 references DO carry dictionary
words. Zero values-map citations corpus-wide — correct, not a miss:
the sepsis KG1 extract carries no values maps at all; the citation
mechanism is proven at unit grain (PB-5: `2 → 'Completed'` with the
map cited in draws_from).

## Finding T-4 — meaning identity is live (the certification law)

Every node carries its content_key. Verified over the corpus build
and pinned as tests: reformatting, alias renames, AND-arm and
join-order swaps, and trailing comments move NO key; changing a
literal (24→48), a column, or a join kind (INNER→LEFT) moves the
key and everything above it. This is the law that will decide when
a certification survives (Phase D) — worth a deliberate look now,
because ruling it later gets expensive.

Sample, the readmit family: `#Base_Pop_ED_Readmit_All`'s selection
twin — `content_key 59b66b65dbc71c7b`, composed of 2 sources + 1
condition + 1 output. Change the 24-hour window and this key, its
statement's, and the file's all move; reformat the whole proc and
none do.

## Acceptance state

- F8 phase-B cases RUNNABLE and green
  (`tests/aivia/test_phase_b_translator.py`, 10 tests)
- Twin conservation pinned in the shakedown
  (`test_twin_conservation`)
- Parse + translate are ONE atomic run (`receive_estate`); the twin
  rebuilds at the file quantum, idempotent when unchanged
- Open for your ruling at gap-check: (1) finding T-1's composite
  kinds; (2) the content_key boundary as exercised (T-4) — does the
  invariance set match your intuition on what a steward's
  certification should survive?
