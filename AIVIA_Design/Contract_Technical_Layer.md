# Contract_Technical_Layer — the technical graph's data contracts

**Status: DRAFT — populated 2026-09-16 from the live system;
awaiting Sunny's gap-check.** First document of the contract
system (Sunny's ruling 2026-09-16: model the INTERACTIONS of
design, data, and registries as keyed joinable tables; one
document per graph layer, modular and independent; contracts are
ROWS, a per-type contract is a filter). Layer docs to follow:
Contract_Logic_Layer · Contract_Consumption_Layer ·
Contract_Governance_Layer · Contract_Surfaces.

Conventions: IDs join across tables (dc. data type · sc. surface
· ds. design section · inv. invariant · R-n grammar rule). An
edge's rows live in the layer of the code that WRITES them.
Findings from populating a contract land in its FINDINGS table —
never silently.

## DESIGN_SECTIONS (governing this layer)

| ds_id | says (short) | status | home doc |
|---|---|---|---|
| ds.l2_node_vocabulary | technical layer = db · db_schema · table · column | RULED | Design_Graph_Engine L2 |
| ds.naming_gql_reserved | no GQL-reserved words as labels ("schema"→db_schema); vendored-list gate | RULED | Design_Graph_Engine |
| ds.joins_to_dictionary_only | joins_to is DECLARED dictionary truth, never derived from SQL; observed joins live on join nodes (logic layer) | RULED | Design_Graph_Engine (M2 redesign) |
| ds.m1_batch | the technical layer ships as batch M1; census-gated; db/db_schema descriptions none-ruled | RULED, batch CLOSED 2026-09-10 | Manifest_Build |
| ds.data_type_temporal_truth | the dictionary's declared type decides temporal; a non-temporal type never vetoes | RULED 2026-09-13 | Grammar_Floor R5.b rider (c) |
| ds.r8_declared_values | a value's DECLARED meaning outranks the SQL author's note | RULED | Grammar_Floor R8 |

## DATA_CONTRACTS

| dc_id | kind | what it is | writer | count (ed_sepsis_dev) |
|---|---|---|---|---|
| dc.db | node | the database | KG1 intake | 1 |
| dc.db_schema | node | a schema in the db | KG1 intake | 3 |
| dc.table | node | a dictionary table | KG1 intake | 90 |
| dc.column | node | a column of a table | KG1 intake | 4,554 |
| dc.has_part (technical rows) | edge | containment db→schema→table→column | KG1 intake | 4,647 |
| dc.joins_to | edge | declared table↔table join with key columns | KG1 intake (joins.csv) | 65 (conservation 68 = 65 + 2 pending + 1 collapsed) |

## CONTRACT_FIELDS

| dc_id | field | writer | rules | checks |
|---|---|---|---|---|
| dc.db | name | registration | inv.no_invented_text | intake tests |
| dc.db | description | NONE-RULED — zero is legal | ds.m1_batch | census Q2 |
| dc.db_schema | name | registration (label law: db_schema) | ds.naming_gql_reserved | reserved-word gate |
| dc.db_schema | description | NONE-RULED — zero is legal | ds.m1_batch | census Q2 |
| dc.table | name | EMR dictionary, verbatim | inv.no_invented_text | census |
| dc.table | description | EMR dictionary, verbatim | inv.no_invented_text | census Q2 (90/90) |
| dc.table | pk_columns | EMR dictionary (LIST-valued) | inv.no_invented_text | FINDING F2 |
| dc.column | name | EMR dictionary, verbatim | inv.no_invented_text | census |
| dc.column | description | EMR dictionary, verbatim | inv.no_invented_text | census Q2 (4554/4554) |
| dc.column | data_type | EMR dictionary | ds.data_type_temporal_truth | rider-(c) tests |
| dc.column | values (code→meaning) | EMR dictionary | ds.r8_declared_values | R8 voicing tests |
| dc.joins_to | onColumns | joins.csv, declared | ds.joins_to_dictionary_only | test_joins_to_lock (6 pins) |

## CONSUMERS

| dc_id | consumer | reads | re-verify |
|---|---|---|---|
| dc.table · dc.column | sc.ask_console | description → searchable text (lowercased) | speech parity gate |
| dc.column | sc.meaning_console | description · data_type · values | console battery |
| dc.table · dc.column · edges | sc.fabric_export | all fields → graph_* parquets | export census tests |
| dc.table | sc.fabric_export | pk_columns | NONE — FINDING F2 |
| dc.joins_to | sc.fabric_export | endpoints + onColumns | export test (65 ride) |
| dc.* (all) | sc.graph_visual | name · description · pk cards · join cards | visual counts vs key |
| dc.column | grammar renderers (R5 operand words, R8, rider (c)) | description · values · data_type | verbatim suites |
| dc.table · dc.column | sc.collibra_publish · sc.purview_publish | names + descriptions | NONE — FINDING F3 |

## GOVERNS

| ds_id | governs |
|---|---|
| ds.l2_node_vocabulary | dc.db · dc.db_schema · dc.table · dc.column |
| ds.naming_gql_reserved | every label above (db_schema is its enforcement scar) |
| ds.joins_to_dictionary_only | dc.joins_to — writer and every field |
| ds.m1_batch | counts + description obligations of all six dc rows |
| ds.data_type_temporal_truth | dc.column.data_type |
| ds.r8_declared_values | dc.column.values |
| inv.no_invented_text · inv.one_writer | every field row above |

## TESTS

| test_id | proves |
|---|---|
| test_kg1_intake | dc.* writers and shapes |
| test_shape_census Q1/Q2/Q3 | counts + description obligations, both directions |
| test_joins_to_lock | ds.joins_to_dictionary_only conservation |
| test_graph_export + reserved-word test | sc.fabric_export rows · ds.naming_gql_reserved |
| test_speech_parity (stored check) | dc.table/column.description → sc.ask_console words |
| test_ed_sepsis_dev_estate (M1 census) | counts vs the answer key |

## FINDINGS (from populating this contract, 2026-09-16)

| id | finding | kind | status |
|---|---|---|---|
| F1 | db/db_schema descriptions none-ruled — zero is legal by ds.m1_batch | deliberate fact, made visible | CLOSED — the row is the proof |
| F2 | dc.table.pk_columns never reaches Fabric: the export drops LIST-valued fields (counted since the graph-visual build) | consumer gap | OPEN — Sunny rules when the export fix lands |
| F3 | sc.collibra_publish / sc.purview_publish consume this layer with NO governing ds row and NO re-verify test | ungoverned surfaces | OPEN — contract them or mark dormant |
