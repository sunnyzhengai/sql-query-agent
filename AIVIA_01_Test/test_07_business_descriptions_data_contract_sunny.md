# test_07_business_descriptions_data_contract_sunny

Sunny's hand-written cases for phase 07. Claude maintains the
commands; the cases are hers.

## The commands

Run Claude's suite (11 tests, deterministic — the fixtures are
the dry run's recorded real model outputs; zero API cost):

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/test_07_business_descriptions_data_contract.py -v

The floor-only build (deterministic, zero cost — the sheet and
texts exist with every row status=floor):

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import business_descriptions as bd; bd.build07('AIVIA_01_Data/05_semantic_graph','AIVIA_01_Data/06_technical_descriptions','AIVIA_01_Data/07_business_descriptions','AIVIA_01_Data/02_emr_data_dictionary', no_llm=True)"

THE LIVE RUN (paid gpt-5-mini calls — 151 nodes x up to 3
repair rounds; Sunny's explicit go required before each run):

    (same command with no_llm=False — Claude runs it at her word)

The artifacts:

    AIVIA_01_Data/07_business_descriptions/07_business_sheet.json
    AIVIA_01_Data/07_business_descriptions/<file_name>.txt
    AIVIA_01_Data/07_business_descriptions/07_blessing_registry.json  (HER HAND ONLY)
    AIVIA_01_Data/07_business_descriptions/07_blessing_seed_candidates.json (3 staged, awaiting her rulings)
    AIVIA_01_Data/07_business_descriptions/07_code_sightings.json

## Sunny's cases

(awaiting her hand — her blessing pass over the live run's
sheet and texts is the acceptance)

## THE WALK REOPEN (ruled 2026-10-04 — Brief_07_Graph_Grounded_
## Proposer.md Q1–Q9; contract stamped same day)

Build order, standing law: pseudo code (her approval) -> the
seven G-locks land RED (verbatim pytest shown) -> code -> green
-> the proving-file regeneration.

Her commands at the walk build (the placeholders in CAPS are
filled by Claude at pseudo approval, before the red tests):

1. The suite (the seven new locks ride in this same file):

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/test_07_business_descriptions_data_contract.py -v

2. The naming coverage pass (zero-cost report BEFORE any live
   call — lists every column/table the walk will speak that has
   no short name in the 03 asset; gaps stage for her eye in
   07_naming_gaps.json; the build refuses live calls while gaps
   exist):

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import business_walk as bw; bw.naming_coverage('AIVIA_01_Data/05_semantic_graph','AIVIA_01_Data/02_emr_data_dictionary','AIVIA_01_Data/03_chat_bot', only_file='COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS')"

3. The proving-file live build under the walk (paid; her
   explicit go before each run, as always; census totals only —
   the corpus runs only after section-H acceptance):

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import business_walk as bw; bw.build07_walk('AIVIA_01_Data/05_semantic_graph','AIVIA_01_Data/06_technical_descriptions','AIVIA_01_Data/07_business_descriptions','AIVIA_01_Data/02_emr_data_dictionary','AIVIA_01_Data/03_chat_bot', no_llm=False, only_file='COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS')"

4. Her acceptance, two halves (contract section H):
   a. Read AIVIA_01_Data/07_business_descriptions/
      COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.txt
      clean — no new leak classes.
   b. Confirm the seeded-invention catch is the CHECKER's, not
      her eye's: the G.1–G.7 tests green in the suite run.

CUTOVER EXECUTED 2026-10-04 (her acceptance): the walk commands
in THIS section are the live pipeline; the build07 one-liners in
the sections above are LEGACY (kept for history, not for runs).
Two more doors since the build:
  - bless (the ratify clause — her ruling, machine write):
    stated in chat to Claude, who runs business_walk.bless() with
    her ruling recorded verbatim; kind="name" for name rows.
  - zero-call rerender (lands blessings without rerolling):
    same build command with rerender=True and no no_llm flag.
