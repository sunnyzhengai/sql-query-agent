# Contract_Technical_Layer — the technical graph's data contracts

**Status: RATIFIED (Sunny's gap-check passed, 2026-09-16 — "two
contracts passed"); populated same day from the live system.** First document of the contract
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

## INVARIANTS (the inv.* ids — home of ALL layers' invariant rows, ruled FL6(a) 2026-09-17)

| inv_id | the law, one sentence | enforced by |
|---|---|---|
| inv.no_invented_text | every stored English text is projected from ruled sources (dictionary verbatim or grammar-rendered) — never invented | intake tests · census Q2 |
| inv.one_writer | one writer per field; a new answer to a ruled question lands IN the ruled row, never beside it | contract FIELD rows · the suite locks (joins_to, kind-library) |
| inv.verbatim | stored text == recomputed text, byte-exact | the verbatim suites (F4 fixture + estate) |
| inv.derivable_never_stored | anything computable from stored facts is never stored beside them (the ONE spelling — `derivable_never_authored` retired, FL6) | mapper tests; latest application: the R11 (b) ruling — no fixed phrases restating a kind field |

## DESIGN_SECTIONS (governing this layer)

| ds_id | says (short) | status | home doc |
|---|---|---|---|
| ds.l2_node_vocabulary | technical layer = db · db_schema · table · column | RULED | Design_Graph_Engine L2 |
| ds.naming_gql_reserved | no GQL-reserved words as labels ("schema"→db_schema); vendored-list gate | RULED | Design_Graph_Engine |
| ds.joins_to_dictionary_only | joins_to is DECLARED dictionary truth, never derived from SQL; observed joins live on join nodes (logic layer) | RULED | Design_Graph_Engine (M2 redesign) |
| ds.m1_batch | the technical layer ships as batch M1; census-gated; db/db_schema descriptions none-ruled | RULED, batch CLOSED 2026-09-10 | Design_Graph_Engine L2 — description obligations (re-homed 2026-09-17, CI-A2) + Manifest_Build (the batch record) |
| ds.data_type_temporal_truth | the dictionary's declared type decides temporal; a non-temporal type never vetoes | RULED 2026-09-13 | Grammar_Floor R5.b rider (c) |
| ds.r8_declared_values | a value's DECLARED meaning outranks the SQL author's note; the disagreement is COUNTED (a steward finding, never silent) | RULED | Grammar_Floor R8 |

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
| dc.column | sc.grammar_render (R5 operand words, R8, rider (c)) | description · values · data_type | verbatim suites |
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
| test_graph_export (incl. the reserved-word pin, test_no_name_collides_with_gql_reserved_words) | sc.fabric_export rows · ds.naming_gql_reserved |
| test_metamodel | label/edge vocabulary conformance over the built graph, incl. the reserved-word law (the second enforcement of ds.naming_gql_reserved; test_kg1_intake calls its conformance check) |
| test_speech_parity (stored check) | dc.table/column.description → sc.ask_console words |
| test_ed_sepsis_dev_estate (M1 census) | counts vs the answer key |

## FINDINGS (from populating this contract, 2026-09-16)

| id | finding | kind | status |
|---|---|---|---|
| F1 | db/db_schema descriptions none-ruled — zero is legal by ds.m1_batch | deliberate fact, made visible | CLOSED — the row is the proof |
| F2 | dc.table.pk_columns never reaches Fabric: the export drops LIST-valued fields (counted since the graph-visual build) | consumer gap | RULED (Sunny "yes", 2026-09-16): class FIX — the export carries list fields as joined text; RIDES THE M5 BATCH (its brief + its load, one refresh) |
| F3 | sc.collibra_publish / sc.purview_publish consume this layer with NO governing ds row and NO re-verify test | ungoverned surfaces | RULED (Sunny "yes", 2026-09-16): **DORMANT** — kept as marketplace assets, NOT LIVE, no runs against current estates; revival re-enters via the change process (ruling → contract → tests) |
| F4 | dc.column.values (dict code→meaning) is dropped by the SAME export filter as F2 — export_graph.py:50-53 skips every dict AND list property; graph_column.parquet has no values column. The CONSUMERS row "all fields → graph_* parquets" overclaims. F2's ruled fix ("list fields as joined text") does not decide dict handling; the two existing hand-joins use different separators (" " for scope.structures, "; " for joins_to.onColumns) | consumer gap — same class as F2, found on the first review query of this contract, 2026-09-16 | RULED (Sunny "yes" to all three parts, 2026-09-17): (1) values RIDES the F2 fix — same M5 brief, same load, one refresh; (2) pairs export as `code = meaning` joined by `"; "` (the joins_to house form, e.g. `1 = Emergency; 2 = Urgent`); (3) plain lists join with `"; "` too (pk_columns → `PAT_ID; CONTACT_DATE`) — the ONE separator for all new work; scope.structures stays as served |
| F5 | TESTS table drift: the "reserved-word test" is not a file — it is test_no_name_collides_with_gql_reserved_words INSIDE test_graph_export.py; and test_metamodel.py also enforces ds.naming_gql_reserved (test_kg1_intake calls its conformance check) but has no TESTS row | contract-vs-repo naming drift, review query 2026-09-16 | RULED (Sunny "yes", 2026-09-17) + CLOSED same breath: the row reworded, test_metamodel row added — the TESTS table above is the fix |
