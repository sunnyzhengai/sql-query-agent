# P0-c — description generation over our own corpus

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

**60 description(s) generated** (+0 unparsed proc(s) skipped)

**Coverage (DESC-TEMP-1): 413 describable steps across 15 of 28 procs** — CTE steps AND temp-table staged steps (SELECT…INTO #X / INSERT INTO #X), harvested through the parser. Coverage counts the WHOLE corpus and is independent of any --limit on generation. The other 13 procs are single-SELECT report procs with no CTE and no temp staging (verified, not assumed): the step harvester finds nothing in them, so today they get NO description at all. That is a NAMED GAP (DESC-WHOLE-1), not a clean result.

**Dictionary coverage (DESC-VOICE-3.2 fallback ruling):** 156 of 156 referenced columns have NO dictionary description in this run — this runner has no graph nodes to draw them from, so EVERY description here was written without dictionary support and falls back to readable column wording. Stated, not hidden: with the dictionary wired these descriptions get materially better, and the gap itself is the Tier-1 asset ('N columns your catalog never documented').

- clean (passed first try): 15 (25%)
- recovered (corrective retry fixed it): 23 (38%)
- salvaged (surgical fallback kept grounded lines): 8 (13%)
- emptied (absence over fabrication): 14 (23%)

## First-pass violations by class

- column name in a business description: 74
- technical vocabulary in a business description: 17
- ungrounded value: 15
- technical object in a business description: 9
- ungrounded filter claim: 5
- ungrounded table claim: 3
- selected-not-filtered: 2
- misattributed predicate: 2

## Reading these numbers

A HIGH recovered/salvaged rate is a finding about GENERATION quality, not a gate failure — the gate is doing its job either way. An EMPTIED description is the honest floor: absence over fabrication.
