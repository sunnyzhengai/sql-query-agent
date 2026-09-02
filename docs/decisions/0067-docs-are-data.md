# ADR 0067 — Docs are data: the record invariant and the prose ratchet

**Status:** ACCEPTED 2026-09-02 — Sunny's ruling on the inflated docs
folder (~82k words of prose over 4.3k lines of registries; every drift
the 2026-09-01 audit fixed was in prose, every catch was made by data).

## The invariant

> If an agent must **obey** it → it is a record with a check.
> If a human must **understand why** → it is an ADR.
> Nothing else exists.

Agents cite ADRs; they never take instruction from them. Prose is for
rationale and history only.

## The ratchet (no big-bang)

1. **No new checkable claim may be born as prose.** New law enters as
   a record; its rationale enters as ADR text.
2. **When prose is touched, its checkable content moves to a record
   and the prose dies.** Each conversion moves one step of the design
   protocol from interpretive to CI-forced.
3. **Every record names its goal, its data, and its check** — fields
   grow toward: inputs, outputs, check, status, parent, adr.

Target end-state: `docs/` = AXIOMS + PROTOCOL + one architecture page
+ decisions/ + generated projections. Everything else is registry.

## Turn 1 (ships with this ADR)

`src/spec_registry.py` — the 48 axioms as records: id, group, title,
framework parents, declared checks, grounding ADRs. Single-writer
effects:

- `SPEC_AXIOMS` and `SPEC_TO_AXM` in trace_registry become
  **derived** from the records — two hand-maintained structures die.
- Per-axiom checks become data: every axiom names its check files
  (existence-verified) or carries an explicit unbound reason — the
  "design TEST around SPEC" spine.
- Totality both ways: every record id appears in SPEC.md; every
  axiom id in SPEC.md has a record. A new axiom cannot exist in only
  one place (the Group-P failure class, closed at the id level).

**Deliberately NOT in turn 1** (single-home rule — a field moves only
when its prose home dies): the law formulas and per-axiom statuses
stay in SPEC.md, their one home. Copying them into records now would
create the dual-truth drift trap this ADR exists to kill. They migrate
in a later turn, when the per-axiom prose is retired into ADRs.

## Relations

0047 (SPEC), 0048 (registries as law), 0066 (the merge that showed
prose is where drift lives), the 2026-09-02 seam-tightening (the
Proves: migration — the same ratchet pattern, already running).
