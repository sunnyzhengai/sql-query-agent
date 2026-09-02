# ADR 0070 — QUESTION_MAP retires into the notebook registry (ratchet turn 4)

**Status:** ACCEPTED 2026-09-02 — Sunny's order, executing ADR 0067.
The second file the ratchet retires.

## Why the notebook registry, and why retirement

QUESTION_MAP was already half-data: the `serves` field and the
coverage projection lived in `notebook_registry` since ADR 0042, and
even the family TITLES were duplicated in the doc generator. What
remained prose was layer 0 (Sunny-approved 2026-08-18: archetype
question + asked-by per family) and the shape/storage/status audit —
both record-shaped. They became **`FAMILY_RECORDS`**; NOTEBOOK_MAP now
renders the full family table; `QUESTION_FAMILIES` derives from the
records (the generator's duplicate title dict deleted — one writer).

What did NOT convert, because it was rationale or supersession
history: the July governing model's superseded clause 2 (LLM-planned
routing — ADR 0062 abolished it; `spec:R2` is the law), and the
closed-gaps chronicle (ADRs 0043/0022/0039 are the record). The two
STANDING doctrine clauses travel in the records' preamble: shape
classes shape the STORAGE, and precomputation is only verifiable
cache (`spec:D1`).

## The checks the prose never had

- **Storage is cross-checked:** every family's `storage_tables` must
  exist in TABLE_REGISTRY — a family grounded in a table no contract
  declares is a fabricated grounding, now a red build.
- **Coverage runs both ways:** ADR 0042 enforced every notebook
  serves ≥1 family; this turn adds the reverse — every family must be
  served by ≥1 notebook. An unserved family is dead doctrine or a
  missing notebook; both deserve red.
- **One writer for the letters:** `QUESTION_FAMILIES == tuple(FAMILY_RECORDS)`.

## Consequences

- `docs/architecture/`: **11 files (5 authored + 6 generated)** — the
  generated half now outnumbers the authored half.
- The `question` component retires; its 5 ADRs (0017, 0030, 0037,
  0043, 0046 — the ask-time machinery) re-route to `architecture`,
  the system model. Notebook stamp → 0070.
- The families remain a storage-coverage audit, never a routing
  table — stated in the data itself, where an agent reads it.

## Relations

0067 (the ratchet) · 0042 (the contract extended) · 0062/`spec:R2`
(why no routing table) · the 2026-08-18 layer-0 approval (content
unchanged, re-homed).
