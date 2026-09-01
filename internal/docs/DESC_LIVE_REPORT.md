# P0-c — description generation over our own corpus

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

**60 description(s) generated** (+0 unparsed proc(s) skipped)

**Coverage (DESC-TEMP-1): 413 describable steps across 15 of 28 procs** — CTE steps AND temp-table staged steps (SELECT…INTO #X / INSERT INTO #X), harvested through the parser. Coverage counts the WHOLE corpus and is independent of any --limit on generation. The other 13 procs are single-SELECT report procs with no CTE and no temp staging (verified, not assumed): the step harvester finds nothing in them, so today they get NO description at all. That is a NAMED GAP (DESC-WHOLE-1), not a clean result.

- clean (passed first try): 30 (50%)
- recovered (corrective retry fixed it): 17 (28%)
- salvaged (surgical fallback kept grounded lines): 2 (3%)
- emptied (absence over fabrication): 11 (18%)

## First-pass violations by class

- technical vocabulary in a business description: 23
- ungrounded value: 17
- technical object in a business description: 10
- ungrounded filter claim: 5
- selected-not-filtered: 5
- ungrounded table claim: 2
- purpose speculation: 1

## Reading these numbers

A HIGH recovered/salvaged rate is a finding about GENERATION quality, not a gate failure — the gate is doing its job either way. An EMPTIED description is the honest floor: absence over fabrication.
