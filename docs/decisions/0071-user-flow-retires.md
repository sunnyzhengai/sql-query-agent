# ADR 0071 — USER_FLOW retires (ratchet turn 5)

**Status:** ACCEPTED 2026-09-02 — Sunny's "proceed" on the ratchet
sequence (ADR 0067). The third retirement, and the purest: nothing
converts, because nothing in the file was agent-obeyable law.

## What the file was

Born 2026-07-18 — the oldest document in the folder — and never
substantively updated: the 2026-09-01 audit had to cap it with a
three-point correction header (no question types; execution gated;
Purview is a write target) just to make it safe to read. Under the
0067 invariant its content sorts cleanly:

- **Law that survived** was already law elsewhere: refusal-over-guess
  is ADR 0005; the flywheel is ADR 0023/0056 with `spec:L2` making
  its weights derived-never-stored; the loop is ADR 0062 / SPEC
  Group R; the journey per tier is PRODUCT_TIERS.
- **The two-path branch, the month-by-month adoption projection, and
  the superseded execute-and-answer steps** — archaeology; git and
  the ADRs are the record.
- **The FCOTS row-level-security story** (same question, per-user
  answers) — verified UNBUILT: no RLS/personalized filtering exists
  in code, and the run layer is TOP-N read-only. It was a product
  aspiration living in an architecture file. Recorded here as
  roadmap material: if wanted, it re-enters through the design
  protocol (INDEX) with an ADR and a component — not by prose.

## What survives, and where

A compact **flywheel section in ARCHITECTURE.md** (`BUILT`): refusal
is intake, weights are derived from the append-only events, the
escalation door captures demand, and weight patterns are promotion
signals. ~15 lines replacing a 285-line file, because the other 270
were duplication, supersession, or story.

## Consequences

- `docs/architecture/`: **10 files (4 authored + 6 generated)**.
- The `user_flow` component retires; its 6 ADRs (0034, 0035, 0036,
  0038, 0050, 0062 — the conversation-shape lineage) re-route to
  `architecture`, which now satisfies all six framework groups — the
  one system-model file legitimately spans the constitution.
  Architecture stamp → 0071.
- docs/README's tour pointer updates.

## Relations

0067 (the ratchet) · 0066 (the merge that made ARCHITECTURE the one
system-model file this content folds into) · 0005/0023/0056/0062
(the law the file used to paraphrase).
