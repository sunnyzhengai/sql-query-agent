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
