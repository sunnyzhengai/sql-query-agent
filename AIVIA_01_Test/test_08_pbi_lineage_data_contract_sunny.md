# test_08_pbi_lineage_data_contract_sunny

Sunny's hand-written cases for phase 08. Claude maintains the
commands; the cases are hers.

## The commands

Claude's suite (deterministic, synthetic TMDL fixtures only —
zero cost, zero network):

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/test_08_pbi_lineage_data_contract.py -v

The build (deterministic, free, re-runnable; the TMDL folder is
the run parameter — point it at a local checkout):

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import pbi_lineage as pl; pl.build08('<path-to-folder-of-SemanticModel-dirs>','AIVIA_01_Data/01_subject_sql_files','AIVIA_01_Data/08_pbi_lineage')"

The artifacts for her eye:

    AIVIA_01_Data/08_pbi_lineage/08_pbi_reports.json
    AIVIA_01_Data/08_pbi_lineage/08_lineage_ledger.json
    (bindings == resolved + unresolved — the printed equation)

## Sunny's cases

(awaiting her hand — her gap-check of the reports json against
a model she knows is the acceptance)
