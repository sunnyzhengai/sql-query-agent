# Ruling_Change_Process — how any change moves from idea to build

**Status: RATIFIED (Sunny, 2026-09-16 late: P1 "yes" · P2 "hard
gate" · P3 "keep the step 3 skip"); drafted the same night at his
"do we need to solidify a process document".** Born
from the AGE_IN_DAYS dig: placeholders without tripwires, a
ruling that never faced the surface it bypassed, and patches
proposed before the design was consulted. This document is the
one process; the contract tables (Contract_*.md) are what it
queries.

## The five steps

| # | step | who | output | may skip? |
|---|---|---|---|---|
| 1 | CLASSIFY the change | builder | one of the four classes below | never |
| 2 | QUERY the contract tables | builder (mechanical) | the computed impact list | never |
| 3 | BRIEF presented to Sunny | builder → Sunny | class + claims + impacts + ambiguities | never (the FIX skip was retired by H2(c), same night — see the decisions table) |
| 4 | SUNNY RULES every ambiguity | Sunny | his words, quoted in the brief → APPROVED | never — an OPEN ambiguity blocks code |
| 5 | BUILD in the fixed order | builder | registry/contract rows → tests first → code → full suite + integrity → export regen → Sunny's load if served data changed → close | never |

## Step 1 — the four change classes

| class | means | extra requirement |
|---|---|---|
| planned addition | fills a declared OPEN slot | check it matches the slot as declared |
| unplanned addition | the architecture never anticipated it | a ruling extends the design BEFORE the brief |
| update | changes something DECIDED | comply with every invariant; the governing ds rows amend in the same act |
| fix | build drifted from design; design does not move | cite the ds/contract row the code returns to |

Fits none cleanly → that IS an ambiguity → step 4 before anything.

## Step 2 — the impact query (run against the Contract_* tables)

| ask | from |
|---|---|
| who governs the thing I'm changing? | GOVERNS |
| who writes it? (must stay ONE writer) | CONTRACT_FIELDS / DATA_CONTRACTS |
| who consumes it? | CONSUMERS |
| which surfaces do those consumers feed? | SURFACE_CONTRACTS |
| which tests re-verify each consumer? | TESTS |
| does served data change? (→ Sunny's load) | CONSUMERS rows naming sc.fabric_export |
| is any real source not ready yet? | → THE PLACEHOLDER LAW: tripwire test in the same commit |

## Step 3 — the brief (one table, presented before code)

| field | content |
|---|---|
| class | from step 1 |
| claims | the ds rows this implements or amends |
| impacts | the step-2 query output, verbatim |
| ambiguities | every question the design does not answer — each OPEN or carrying Sunny's quoted ruling |
| debt declared | any deferral, with its recorded reason (Echo Law) and landing step |

## The standing laws this process binds together

| law | clause |
|---|---|
| the pause rule | code may only cite RULED design; a question the design doesn't answer stops the build until Sunny rules |
| the placeholder law | a placeholder ships WITH a test that fails when its real source arrives — never naked |
| one home of meaning | one writer per field; a second answer to a ruled question must land in the ruled row, never beside it |
| same breath | contract/registry rows, INDEX lines, and design stamps move in the same commit as the change they describe |
| the closing check | at close, files actually changed == files declared in the brief; mismatch fails the close |
| verdicts land | Sunny's rulings are quoted in the brief and stamped in the ledger the moment they're made |

## Where things live

| artifact | home |
|---|---|
| this process | AIVIA_Design/Ruling_Change_Process.md (this file) |
| the contract tables | AIVIA_Design/Contract_<Layer>.md + Contract_Surfaces.md |
| briefs | AIVIA_Design/briefs/ (one file per change; status DRAFT → PRESENTED → APPROVED → BUILT → CLOSED) |
| the chronological record | Manifest_Build.md (the ledger — history, never current law) |
| mechanical enforcement | integrity checks in the test suite + THE HARD GATE (ruled P2): a pre-code hook (.claude/settings.json) refuses code edits not covered by an APPROVED brief; the hook's own build enters via its own brief — the first change under this ratified process |

## Decisions (all ruled by Sunny, 2026-09-16)

| # | decision | ruling |
|---|---|---|
| P1 | ratify this process document | **RATIFIED** — "yes" |
| P2 | the pre-code hook: hard gate or discipline + closing check? | **HARD GATE** — "hard gate"; the hook refuses code edits not covered by an APPROVED brief; its build enters via its own brief |
| P3 | the lightweight FIX lane (step 3 skip) — keep or remove? | **KEEP** — "keep the step 3 skip" — **SUPERSEDED the same night by H2(c) ("c", Brief_Hard_Gate_Hook): with the hard gate live, every class including FIX needs an APPROVED brief; the skip is retired** |
