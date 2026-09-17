# Brief_Hard_Gate_Hook — the pre-code hook that refuses code edits not covered by an APPROVED brief

**Status: CLOSED** (built + full suite green 2173/0, 2026-09-17 just past midnight; per H3 this brief no longer unlocks its files)

The first change under the ratified process (P2, Sunny 2026-09-16:
"hard gate"). The hook is Claude Code's PreToolUse mechanism: before
every Edit/Write/NotebookEdit, a script receives the target file
path and either allows the edit or blocks it with a message. Ours
blocks any code-file edit whose path is not declared in a brief
with an unlocking status, and says which step of the process is
missing.

| field | content |
|---|---|
| class | planned addition — fills the slot declared by the P2 ruling (Ruling_Change_Process.md, decisions table + the mechanical-enforcement row; ledger stamp 2026-09-16 late) |
| claims | Ruling_Change_Process.md P2 ("hard gate") · P3 (the FIX lane the hook must not break) · the closing check (files declared == files changed — the hook makes "declared" machine-readable) |
| impacts (computed, step-2 query) | **no dc row touched · no registry · no served data · no export · no Sunny's load.** New files: `.claude/settings.json` (checked in — becomes the one home of hook wiring; settings.local.json stays personal permissions) · the hook script (home = ambiguity H6) · a test file (test-first). Changed docs: `briefs/Brief_TEMPLATE.md` gains a machine-readable "files declared" row (the hook reads it; the closing check reads the same row — one home). Consumers: every future Edit/Write/NotebookEdit in this repo |
| ambiguities | H1–H6 below — ALL OPEN; an OPEN ambiguity blocks code |
| debt declared | none — no placeholder; the hook ships whole with its tests |
| Sunny's approval | **"approve"** — 2026-09-16 late, after ruling all six ambiguities one at a time (H2 "c" · H1 "covered" · H3–H6 "yes") |
| closing check | **BALANCED** — files changed == the six declared (settings.json + change_gate.py + test_change_gate.py new; TEMPLATE + this brief + TEST_MAP.md modified). Build: 9 pins authored FAILING (the allow-pins red, the block-pins trivially 2 — a missing script also fails closed), hook built, 9 green; live-fired: inbound.py BLOCKED with the process message, the declared hook file ALLOWED; ruff clean; full suite 2173 passed / 0 failed. Known limit, recorded: the hook matches Edit/Write/NotebookEdit — a shell write bypasses it; the discipline law + this closing check remain the net for that path |

## The ambiguities — Sunny rules each

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| H1 | which paths does the gate COVER? | **RULED (Sunny, 2026-09-16 late: "covered" on the AIVIA_Product question)** — covered: `aivia/` · `src/` · `devtools/` · `tests/` · `AIVIA_Test/` · `services/` · **`AIVIA_Product/`** (estate data + answer keys — the FL7 drift class now gated) · any `*.py` / `*.ipynb` anywhere else. EXEMPT: `AIVIA_Design/` (verdicts-land must never be blocked — rulings, contracts, briefs, the ledger land the moment they're made; registries/*.json stay tripwired by the determinism test) · `*.md` everywhere |
| H2 | **the FIX lane vs the hard gate** — P3 keeps the brief-SKIP for a fix with zero ambiguities + zero contract changes, but the gate only unlocks on a brief. How does a lane-fix edit pass? | **RULED (Sunny, 2026-09-16 late: "c")** — lane-fixes need APPROVED briefs like everything else; **the P3 skip is RETIRED** (P3 row in Ruling_Change_Process.md amended same breath — the supersession is recorded IN the ruled row). Every change of every class now takes an APPROVED brief; the hook has ONE rule, no fix lane |
| H3 | which brief statuses UNLOCK the gate? | **RULED (Sunny, 2026-09-16 late: "yes")** — APPROVED and BUILT only. DRAFT/PRESENTED do not (approval is the point); CLOSED does not (a closed brief stops authorizing edits the moment it closes — no permanent keys) |
| H4 | does the gate guard ITSELF — `.claude/settings.json` + the hook script? | **RULED (Sunny, 2026-09-16 late: "yes")** — covered; changing the gate takes a brief like everything else. `.claude/settings.local.json` (personal permissions, no gate wiring) stays exempt |
| H5 | the machine-readable declared-files form in a brief | **RULED (Sunny, 2026-09-16 late: "yes")** — a `## Files declared` section, one EXACT repo-relative path per line, NO wildcards (a glob could claim the whole engine in one line); the hook greps the section, the closing check diffs the same list. Amending the list of an APPROVED brief needs Sunny's word — his approval covered the list as it stood |
| H6 | the hook script's home + interpreter | **RULED (Sunny, 2026-09-16 late: "yes")** — `devtools/change_gate.py` (a covered directory, per H4's spirit), run with `/opt/homebrew/bin/python3.11` absolute (hooks run in a bare shell — never the .venv), stdlib only (json/os/re/pathlib — the gate must never break on environment); on any internal error the hook BLOCKS and says why (fails closed, never silently open) |

## Files declared

    .claude/settings.json
    devtools/change_gate.py
    tests/aivia/test_change_gate.py
    AIVIA_Design/briefs/Brief_TEMPLATE.md
    AIVIA_Design/briefs/Brief_Hard_Gate_Hook.md
    docs/architecture/TEST_MAP.md

(TEST_MAP.md added post-approval with Sunny's word — "yes",
2026-09-16 late, per H5: the suite-map tripwire forced its
regeneration when the new test file joined the map.)

## Build order (after APPROVED, per the process)

1. tests first — `tests/aivia/test_change_gate.py` feeds the hook
   sample stdin JSON and pins: covered-path + no brief → BLOCK with
   the process message · covered-path + APPROVED brief declaring it
   → ALLOW · exempt path → ALLOW · class-fix brief per the H2
   ruling · CLOSED brief → BLOCK (per H3) · the gate's own files →
   per H4. Authored failing (no hook exists), then green.
2. the hook script + `.claude/settings.json` wiring
   (PreToolUse on Edit|Write|NotebookEdit).
3. Brief_TEMPLATE.md gains the "Files declared" section (H5 form).
4. full suite + ruff; no export, no load.
5. close: files changed == the Files declared list above.
