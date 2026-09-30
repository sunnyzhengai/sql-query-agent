# Brief_AIVIA_01_Gate_Carveout — the AIVIA_01 estate leaves the hard gate; CLAUDE.md's chat-permission process governs it

**Status: CLOSED** (DRAFT → PRESENTED → APPROVED → BUILT → CLOSED)
Closed 2026-09-26 on Sunny's word, same day as approval and build.
Built 2026-09-26, same sitting as the approval: the early return
in `decide()` + `test_aivia_01_estate_is_not_gated`. Suite:
tests/aisql/test_change_gate.py 13 passed; ruff --no-cache clean
on both declared files.

Sunny's goal, her words (2026-09-26): *"create the mechanical
contract tests first"* — the write of
`AIVIA_01_Test/test_01_subject_sql_files_data_contract.py` was
blocked by THE HARD GATE, because the gate covers every `.py`
path in the repo and knows nothing of the AIVIA_01 estate.

ONE sentence of scope (as ruled, option B): `devtools/change_gate.py`
gains an early return for paths under `AIVIA_01_Code/` and
`AIVIA_01_Test/` — the two folders CLAUDE.md lets Claude author
with Sunny's permission in chat — while `AIVIA_01_Design/` and
`AIVIA_01_Data/` (Sunny-only) stay covered by the gate.

Out of scope, named so it cannot creep: every existing covered
root stays gated exactly as today (`aisql/`, `src/`, `devtools/`,
`tests/`, `AIVIA_Test/`, `services/`, `AIVIA_Product/`, the gate
files, and every other `.py`/`.ipynb` in the repo). No change to
brief well-formedness rules, declared-path rules, or the
fails-closed posture.

Why a carve-out and not a brief per AIVIA_01 change: CLAUDE.md
(checked in, Sunny-authored) already declares AIVIA_01's own
change process. Two live processes claiming the same files is the
conflict; the gate should route each estate to its own law, not
force the old estate's law onto the new one.

The change, exactly: in `decide()`, alongside the existing
"verdicts always land" exemption, add —

    if rel.startswith(("AIVIA_01_Code/", "AIVIA_01_Test/")):
        return 0, None  # AIVIA_01 estate: CLAUDE.md's process governs

plus one new test in `tests/aisql/test_change_gate.py`
(`test_aivia_01_estate_is_not_gated`) asserting a `.py` under
each of the two carved-out roots passes with no brief, that a
`.py` under `AIVIA_01_Design/`/`AIVIA_01_Data/` still blocks, and
that the existing covered roots still block.

## Ambiguities

(1) RULED 2026-09-26, Sunny's words "approve. option B": only
    `AIVIA_01_Code/` and `AIVIA_01_Test/` leave the gate — the
    two folders CLAUDE.md lets Claude author. `AIVIA_01_Design/`
    and `AIVIA_01_Data/` stay covered, so a stray `.py` landing
    in Sunny's folders still blocks.

(2) RULED 2026-09-26, with the approval, as proposed: no
    Sunny-only-authorship hook rides this brief. Claude explained
    what such a hook is in the same sitting; it remains available
    as its own brief whenever Sunny wants it. Option B in (1)
    already blocks code files in her folders.

## Files declared

devtools/change_gate.py
tests/aisql/test_change_gate.py

## Sunny's approval

APPROVED 2026-09-26 — her words: "approve. option B" + "flip the
brief". Status flips to BUILT at the gate edit + green tests.

## Closing check

Both declared files landed and nothing else: the early return in
`devtools/change_gate.py` (option B roots only) and
`test_aivia_01_estate_is_not_gated` in
`tests/aisql/test_change_gate.py`. Suite 13/13 green, ruff
--no-cache clean. First proof in the field: the previously blocked
write of `AIVIA_01_Test/test_01_subject_sql_files_data_contract.py`
passed the gate immediately after the build, and a stray-`.py`
probe under the Sunny-only folders still blocks (pinned in the
test). With CLOSED, this brief no longer unlocks its two declared
paths (H3) — the gate guards them again.
