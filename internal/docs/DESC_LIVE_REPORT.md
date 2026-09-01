# P0-c — description generation over our own corpus

**Scale caveat (ruled 2026-08-31, corrected same day):** this corpus spans both ends of the difficulty range — the de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across 21 procs in reporting/, including the 43-step USP_ED_SEPSIS whose invented flowsheet IDs created this gate) AND clean adversarial governance shapes. Difficulty is REAL; what is limited is SCALE: a 28-proc estate, not a multi-thousand-proc enterprise. These rates are MEASURED, not extrapolated, and any place we quote them must carry this sentence.

**60 description(s) generated** (+0 unparsed proc(s) skipped)

**Coverage (DESC-TEMP-1): 413 describable steps across 15 of 28 procs** — CTE steps AND temp-table staged steps (SELECT…INTO #X / INSERT INTO #X), harvested through the parser. Coverage counts the WHOLE corpus and is independent of any --limit on generation. The other 13 procs are single-SELECT report procs with no CTE and no temp staging (verified, not assumed): the step harvester finds nothing in them, so today they get NO description at all. That is a NAMED GAP (DESC-WHOLE-1), not a clean result.

**Dictionary coverage (DESC-VOICE-3.2 fallback ruling):** 156 of 156 referenced columns have NO customer dictionary description — this runner has no graph nodes, so it substitutes the PARSER-DERIVED readable form of each column name (Sunny's fallback ruling: readable wording AND a reported gap). Measured, not assumed: the dictionary fixes ATTRIBUTION but not VOICE on its own — framed as a glossary the model cites the identifiers; framed as SUBSTITUTIONS it writes the meanings (10 column-name violations to 0 across 6 steps). Real customer definitions read better than these readable forms, but the framing — not the dictionary's presence — is what removes the identifiers. The gap itself is the Tier-1 asset ('N columns your catalog never documented').

- clean (passed first try): 50 (83%)
- recovered (corrective retry fixed it): 7 (12%)
- salvaged (surgical fallback kept grounded lines): 1 (2%)
- emptied (absence over fabrication): 2 (3%)

## First-pass violations by class

- ungrounded value: 13
- technical vocabulary in a business description: 6
- misattributed predicate: 2

## Reading these numbers

A HIGH recovered/salvaged rate is a finding about GENERATION quality, not a gate failure — the gate is doing its job either way. An EMPTIED description is the honest floor: absence over fabrication.
