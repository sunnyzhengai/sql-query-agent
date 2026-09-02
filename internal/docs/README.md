# internal/ — AIVIA-only

Never shipped to customers. The governed ⊎ internal partition is ADR
0048; `src/zones.py` classifies it and `tests/test_zones.py` enforces it.

## What lives here (policy, set 2026-09-01)

This folder was cleared of 41 HANDOFF_* documents and ~50 point-in-time
session artifacts (walk transcripts, nightly batteries, demo scripts,
morning briefs, round-by-round results). They had served their purpose
and had become a liability: **superseded working notes are the most
dangerous thing an agent can read**, because they are written in the
same confident voice as standing decisions but record states of the
world that no longer hold. They also risked being ingested.

**The rule going forward: this folder holds durable evidence, not
working notes.**

- **Belongs here** — evidence a standing ADR, spec axiom, or test cites
  as its proof; anything whose deletion would leave a decision
  unsupported.
- **Does not belong here** — handoffs, session logs, transcripts,
  briefs, checklists, and anything whose title contains a date or a
  round number. Those live in the conversation and die with it. If a
  handoff produces a durable conclusion, the conclusion goes to its ADR
  or to BOARD.md; the handoff itself is not kept.

Before adding a file, ask: *will something cite this a month from now?*
If not, it does not go here.

## What survived the 2026-09-01 clearing, and why

Each of these is load-bearing — a standing document or a passing test
points at it as evidence:

| File | Cited by |
|---|---|
| `PARSE_EXPERIMENT.md` | ADR 0060 (the measurement that closed its build gate), `src/trace_registry.py` |
| `TRACE_USP_ED_SEPSIS.md` | ADR 0044, `src/tree/extract.py`, `tests/test_grounding_gate.py` |
| `REMATCH_SCORECARD.md` | `docs/README.md`, `tests/test_graph_templates.py` (certified numbers) |
| `RECERT_ANSWER_KEY_1_30.md` | `tests/test_recorded_pipeline.py` |
| `SMARTNESS_WALK.md` | SPEC.md §14d — the L3 acceptance protocol |
| `VERB_SCORECARD.md` | ADR 0034 |
| `MARKETPLACE_TRANSACTABLE_PLAN.md` | ADR 0028, `src/marketplace/fulfillment.py` |
| `ROADMAP.md` | `docs/README.md` — project status |

Everything else remains recoverable from git history if a specific
document is ever needed again; nothing was destroyed, only removed from
the working tree.
