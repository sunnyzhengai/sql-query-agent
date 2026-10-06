# test_09_business_terms_data_contract_sunny

Sunny's hand-written cases for phase 09. Claude maintains the
commands; the cases are hers.

## The commands

Claude's suite (deterministic, synthetic fixtures, injected
proposer — zero cost, zero network):

    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/test_09_business_terms_data_contract.py -v

The build on the real corpus (PAID LLM calls — the D3 cards
and D5 names, up to 3 repair rounds each; the technical
definitions and the ledger are free and deterministic). The
`only_file=` switch (her ask, 2026-10-05) limits a run to one
file for cheap iteration — drop it for the full-estate run
that ships to Fabric:

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import business_terms as bt; bt.build09('AIVIA_01_Data/05_semantic_graph','AIVIA_01_Data/06_technical_descriptions','AIVIA_01_Data/02_emr_data_dictionary','AIVIA_01_Data/07_business_descriptions','AIVIA_01_Data/08_pbi_lineage','AIVIA_01_Data', only_file='COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS')"

(The 08 lineage folder lives on Fabric today; with no local
08_pbi_reports.json every row lands report-less in the ledger —
counted, honest, nothing exported until the lineage file is
synced down or the blessings happen on Fabric.)

Blessing a name (her hand only — the write is machine-executed
at her explicit ruling, recorded verbatim, per the ratify
clause):

    /opt/homebrew/bin/python3.11 -c "import sys; sys.path.insert(0,'AIVIA_01_Code'); import business_terms as bt; bt.bless('AIVIA_01_Data','AIVIA_01_Data/07_business_descriptions','<node_id>','<report-or-file-name>','RULED <date> (Sunny): <her words>')"

The artifact for her eye (THE CONSOLIDATION RULING, 2026-10-05:
one file; the old sheet/export/ledger are retired and deleted):

    AIVIA_01_Data/ai_delivery.json
    (terms under their report or reportless file; counts.09
     carries the equations + the plumbing skip list)

## Sunny's cases

(awaiting her hand — suggested gap-checks from the stamped
decisions, hers to keep or replace:)

1. The census delivery scope's proposed name: does it say what
   the population IS, in her words, no SQL echo? (D5)
2. The two STRING_SPLIT chooser scopes: flagged plumbing, no
   name, no LLM call, counted in the ledger? (D2)
3. A technical definition read end to end: every bullet true
   against the SQL, negatives all under Exclusions, no table
   names, no @, no codes? (D4)
4. Two similar census reports: the second proposal collides,
   the flag names the first, nothing silently renamed? (D5)
5. The export file before any blessing: empty. After one
   blessing: exactly that one row? (D6)
