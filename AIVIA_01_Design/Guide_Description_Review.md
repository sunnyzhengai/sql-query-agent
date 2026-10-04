# Guide_Description_Review

Status: LIVING GUIDE (authored by Claude at Sunny's word,
2026-10-03: "can you document these files"). Updated whenever a
build changes what lands where. Plain words throughout.

## The one-line map

Descriptions live in TWO data folders — 06 holds the TECHNICAL
truth (deterministic, zero LLM), 07 holds the BUSINESS voice
(proposed by the model, verified by the gate, blessed by Sunny).
In both: the .txt files are for your eye; the .json sheets are
the machine truth the .txt files are printed from.

## Phase 06 — the technical descriptions
Folder: AIVIA_01_Data/06_technical_descriptions/

| File | What it is | How to read it |
|---|---|---|
| <file_name>.txt (8 files) | THE PRIMARY READ — one per SQL file: THE SELECTIONS (every scope's central sentence), THE STEPS (every statement, silent ones loud in [brackets]), THE FILE (the three-level floor: headline, pipeline, Presents/Population/Inner joins, parameters, census close) | top to bottom; every sentence traces to stored rows; nothing is ever invented here |
| <file_name>.svg (8 files) | the same file as a PICTURE: statements down the spine, scopes as boxes with their predicates, lineage edges across the margin colored by kind (member / star_member / behind_star), the dynamic-SQL gap in red | open in any browser; sentence and shape side by side is the gap-check posture |
| 06_description_sheet.json | the machine truth: 362 rows, five grains, byte-exact sentences with evidence refs | query it; don't read it raw |
| 06_voicing_ledger.json | everything 06 chose NOT to say, each with its named reason (93 rows) — the conservation equation's other half | the words-gap rows double as the dictionary-growth queue |

## Phase 07 — the business descriptions
Folder: AIVIA_01_Data/07_business_descriptions/

| File | What it is | How to read it |
|---|---|---|
| <file_name>.txt | THE PRIMARY READ — one line per described thing, each marked: [gate_passed] = business text that survived every gate check, AWAITING YOUR BLESSING; [floor] = the technical sentence shipped instead, with the named reasons on the sheet row | CURRENT STATE: only the Totals_SSRS file is live (the single-file probe, 16 passed / 5 floors); the other 7 .txt are floor-only placeholders until the full corpus run |
| 07_business_sheet.json | the machine truth: per-node business text, status (proposed / gate_passed / blessed / floor), the gate findings, rounds used, model | currently holds the probe's 21 rows; the corpus run replaces it whole |
| 07_blessing_registry.json | YOUR HAND ONLY — blessed names and sentences, one dated ruling per row; machines read it, never write it | empty today |
| 07_blessing_seed_candidates.json | 3 candidates staged from 03's sunny_synonyms — no force until you move one into the registry | |
| 07_code_sightings.json | codes the proposer wanted to speak but your dictionary gives no meaning — value-growth ore | 3 sightings today |

## What reviewing looks like

1. Open a 06 .txt — is every sentence TRUE to the SQL? (Your
   gap-check; still the open acceptance for phase 06.)
2. Open the 07 Totals .txt — do the [gate_passed] lines read
   right for a business user? Those are the blessing candidates.
3. For any [floor] line, the sheet row's gate_findings say
   exactly which words failed and why.
4. The full story of how the gate and voice converged:
   AIVIA_01_Design/dryruns/phase_II_uses_phase_I.md.

## The commands (also in the per-phase sunny-md files)

Rebuild 06 (deterministic, ~15s):
    /opt/homebrew/bin/python3.11 AIVIA_01_Code/technical_descriptions.py AIVIA_01_Data/05_semantic_graph AIVIA_01_Data/06_technical_descriptions AIVIA_01_Data/02_emr_data_dictionary AIVIA_01_Data/01_subject_sql_files

Rebuild 07 floor-only (deterministic, zero cost): see
    AIVIA_01_Test/test_07_business_descriptions_data_contract_sunny.md

The 07 LIVE run (paid calls): Claude runs it at your word.
