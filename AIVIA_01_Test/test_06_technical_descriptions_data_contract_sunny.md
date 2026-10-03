# test_06_technical_descriptions_data_contract_sunny

Sunny's hand-written cases for phase 06. Claude maintains the
commands; the cases are hers.

## The commands

Run Claude's suite (58 tests, byte-exact):

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/test_06_technical_descriptions_data_contract.py -v

Rebuild the artifacts (deterministic, zero LLM, ~15s):

    /opt/homebrew/bin/python3.11 AIVIA_01_Code/technical_descriptions.py AIVIA_01_Data/05_semantic_graph AIVIA_01_Data/06_technical_descriptions AIVIA_01_Data/02_emr_data_dictionary AIVIA_01_Data/01_subject_sql_files

The eyeball artifacts (tracked, regenerated every build):

    AIVIA_01_Data/06_technical_descriptions/<file_name>.txt
    AIVIA_01_Data/06_technical_descriptions/<file_name>.svg

The ledger queue (what the descriptions chose not to say, by
named reason):

    AIVIA_01_Data/06_technical_descriptions/06_voicing_ledger.json

## Sunny's cases

(awaiting her hand — the gap-check pass over the 8 texts and
SVGs is the acceptance, per the standing ED-sepsis law)
