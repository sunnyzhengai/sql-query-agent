# Phase D anchor census — the ED-sepsis corpus (Sunny's gap-check)

**Phase D of the twin-graph ruling (ADR 0077), built 2026-09-06 —
the LAST phase. The anchor rule is live: governance rides MEANING
identity, never syntax.**

## What Phase D is

Every description now carries an **anchor** — its scope's
`content_key` (the meaning identity your T-4 ruling blessed) at its
scope path. The S1/S2 attachment rules are now **corollaries**, not
machinery, exactly as the ruling predicted:

- **Survives silently (S1):** a developer reformats a proc, renames
  aliases, reorders AND arms — the content_key doesn't move, the
  anchor holds, the steward is never asked to re-bless a change that
  changed nothing. Proven as a test: certify → reformat → rebuild →
  intact, zero new versions anywhere.
- **Orphans visibly (S2):** change `APPT_STATUS_C = 2` to `= 3` —
  the key moves, the certification flags as a **drift orphan** for
  re-review. Never deleted, never silently carried onto changed
  logic.
- **Deletion finds its candidates by MEANING:** rename `#Recent` to
  `#Fresh` — the old anchor's scope is gone, and the census offers
  the renamed scope as the candidate because its content_key
  matches. The rename case resolves itself for the human;
  re-attachment stays a human act.

## The sepsis numbers

| Measure | Count |
|---|---|
| Descriptions produced, anchored at write time | 310 |
| Anchor census: intact | 310 |
| Drift orphans / deleted orphans / unanchored | 0 / 0 / 0 |

(All zeros because this is a fresh produce over the current corpus —
the interesting numbers appear the first time a developer edits a
proc after a steward certifies. The three behaviors above are pinned
as tests, not hoped.)

## The migration (PD-4)

For estates with pre-Phase-D descriptions, `migrate_anchors` appends
anchored versions under the migration basis with the acceptance
equation `migrated + orphaned + human_held == candidates` asserted —
orphans are FINDINGS, human-owned artifacts are never touched by the
pipeline (they surface for the steward instead). Proven over the
fixture estate: 4/4 migrated, equation holds.

## Where the pieces live

- `aivia/graph/kg3_artifacts.py` — `append_description(anchor=…)` +
  `migrate_anchors` (the layer's one writer keeps its census)
- `aivia/lenses/anchors.py` — `lens_anchor_census`: the S1/S2
  corollaries as a READING (derived, writes nothing); this is the
  anchor-mismatch query the lens reclassification promised for
  divergence/concept-drift
- `aivia/flows/produce.py` — anchors stamped at write time

## The twin-graph ruling: FULLY BUILT

All four phases shipped in one day, each gated by a real ED-sepsis
deliverable: A (projection), B (the translator + content_key), C
(the policy walk + your five corpse finds), D (anchors). All 16 F8
answer keys — authored before any phase code — run live and green.

Open engineering ledger going forward (the taxonomy's engine-debt
side): DELETE/GOTO statements (2 each), PIVOT transform semantics
(4), ambiguous/unbound reference classes. Open process item: the
SPEC ledger axioms for phases A-D (ADR 0073 discipline — each needs
its check named; scheduled in ADR 0077, not yet landed).

Your Phase C/D gap-check verdict remains the standing gate on the
regenerated floors.
