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
| F6 | intake reads refuse clean-looking field files: a manifest.json saved by a Windows editor with a byte-order mark fails as a raw JSONDecodeError ("Expecting value: line 1 column 1"), and extract CSVs saved by the SQL client carry the same mark, poisoning the first header name so DictReader raises KeyError. Both reached the operator as bare Python tracebacks, not named refusals | error-contract breach — the first work dry run (Sunny's hand, 2026-09-19); every intake surface that opens a text file is in scope | CLOSED (Brief_Pilot_Build_1, 2026-09-20): every intake text read decodes utf-8-sig — kg1_intake.read_json is now the ONE intake JSON door (inbound estate/pbi/descriptions, console registration + snapshot peek, glossary, fabric_run all re-pointed), CSVs open utf-8-sig; malformed JSON refuses INTAKE-14 naming the path + the parser's words (ruling (4)); pinned RED-first by tests/aisql/test_intake_hardening.py (BOM'd manifest, BOM'd CSV, BOM'd .sql fixtures) |
| F7 | intake never checks CSV headers against the contract: a headerless tables.csv (the SQL client's grid option off) surfaced as KeyError 'schema' deep in validate_extract — the pack pins aliases byte-exact but the intake assumes them | error-contract breach, same dry run | CLOSED (Brief_Pilot_Build_1, 2026-09-20): kg1_intake.CSV_HEADERS = the per-file header contract, checked at load_snapshot; mismatch refuses INTAKE-15 naming the file, expected vs found (ruling (4)); REQUIRED headers only — extras tolerated per the pack law, data_type stays opportunistic (rider (c)); pinned by test_intake_hardening.py (headerless + wrong-header fixtures) |
| F8 | estate_snapshot/ requires its own manifest.json (location · as_of · default_schema) but the pilots runbook's estate step names only the .sql files — the operator hit a raw FileNotFoundError mid-boot | runbook gap + error-contract breach, same dry run | CLOSED (Brief_Pilot_Build_1, 2026-09-20, ruling (5) "i agree with option c"): extract_scripts writes the estate_snapshot/manifest.json TEMPLATE — location from the folder, default_schema from the pack's pack.json (a vendor fact), as_of EMPTY; a present manifest is NEVER overwritten; intake refuses by name — INTAKE-16 missing manifest, INTAKE-17 empty as_of ("fill in the date this estate SQL was captured") — the template's tripwires per the placeholder law; the runbook's step shrank to typing one date |
| F9 | db-qualified three-part table names (`db.schema.table`) NEVER resolve, by construction: the mapper renders the full dotted name (kg2_mapper `_table_name` joins every identifier), and `resolve()` splits at the LAST dot only — so the schema lookup key becomes `db.schema`, which can never appear in the registration's schema_sources. Every table ref in a proc written with db prefixes lands unresolved (counted in the census, so the failure was never silent — but the count does not say WHY). THE CASCADE, seen whole in the second dry-run proc: joins render the zero-target "Join on <raw>" fallback even for single-equality ONs (FL12's real trigger), condition subjects fall to bare name words (no dictionary phrase, no declared value meanings — source comments voice as "(noted …)" where the values map should have spoken), and the owner-possessive can never arm. The db part also never reaches the INTAKE-8/9 opt-in cross-check it was made for | resolution defect — second work dry run (Sunny's hand, 2026-09-19); reproducible by prefixing any sepsis-corpus table ref with a db part | CLOSED (Brief_Pilot_Build_1, 2026-09-20, ruling (8) "i agree with option b"): resolve_scope splits ≥3-part names db · schema · table and binds on schema (db..table falls to default_schema); the db part is COUNTED-NEVER-REFUSED — registered db matches (folded) → binds, the match IS the cross-check passing; foreign db → stays unresolved, census.cross_database_reads names the db; db_name omitted → schema-only binding per the waiver and census.db_names_seen reports the distinct names; pinned RED-first by tests/aisql/test_three_part_resolution.py; the whole F9 cascade (join fallback, bare name words, silent value maps) recovers downstream — FL12's fragment VOICE stays its own open row for build-brief 2. BUILD FIND, same class: the rewrite also recovered ELIDED-SCHEMA refs (`FROM .TABLE` — empty schema part = default schema, legal T-SQL; the sepsis corpus carries five in USP_RPTS_IP_SEPSIS.sql); sepsis pins re-based BY MEASUREMENT, every delta traced (+25 resolved = 5 tables + 20 columns; coverage_gaps 700→680; BED_CONFIG joins the working set) |
| F10 | INTAKE-10 names TWO distinct remedies: kg1_intake.registered_db_name's no-anchor refusal ("name the db, or register exactly one source", MR1a) AND validate_extract's keyless-table refusal (pk integrity, the 2026-09-05 ruling) — the error-contract law says distinct remedies get distinct ids, and per-id firing counts across pilots are product signal; one id firing for two causes muddies both counts | id-collision — found mechanically during ruling (4)'s new-id audit (Brief_Pilot_Build_1, 2026-09-20) | OPEN — Sunny's call: re-number one side (the L1 contract names INTAKE-10 = pk integrity, so the MR1a refusal is the newcomer) or bless the share |
| F11 | the F9 class one arity up: a 4-part linked-server name (`server.db.schema.table`) splits with the SERVER PART DROPPED — never examined, never counted; the ref binds on db/schema/table alone, so a linked-server read could bind to the local table silently. Same failure type F9 named: a legal input part the code does not understand is coerced away instead of counted | found answering Sunny's loud-failure question, 2026-09-20; no 4-part refs in any current corpus (the pin would be RED-ready, not RED) | RULED (Sunny "agree with F11", 2026-09-20) — the ruling-(8) symmetry, counted-never-refused: registration's server named and matching (folded) → binds, the match IS the cross-check; named and DIFFERING → unresolved, counted cross_server_reads with the server named (a linked-server read is another machine's data — binding it locally would be a wrong claim); server not declared (optional, MR1a) → binds on db/schema/table per the waiver and census.server_names_seen reports the names. CLOSED same day via Brief_Closed_Shape slice 5 — the server part is examined, never dropped; pinned RED-first (test_name_grammar: OTHERSRV → cross_server_reads named; waived → server_names_seen) |
| F12 | THE GENERATOR (Echo Law clause): "a shape the code never anticipated is coerced into the nearest known shape and lands in a catch-all count with no cause" has now fired twice — the ABX corpse (2026-09-06: unmapped UNION shape laundered into 'no source records are read') and F9's diagnosis (the result sheet told the DBA "the SQL qualifies it differently" for a ref the ENGINE could not read). Proposed to Sunny (2026-09-20, four rows): (1) THE CLOSED-SHAPE LAW — consumers of estate-authored input declare the vendor-documented input grammar; anything outside counts as shape_unrecognized, tripwire-pinned to 0 on the corpora; (2) unresolved_detail diagnosis becomes a CLOSED enum, shakedown pins per-class counts; (3) diagnosis honesty — customer-blaming sentences only for fully-understood shapes; (4) the grammar-conformance pin over every name arity | generator-level find, 2026-09-20 | RULED (Sunny "i agree with your recommendation, draft the brief", 2026-09-20): proposals 1+2+4 enter as ONE brief, 3 as its wording rule; shape_unrecognized FAILS THE SUITE on the pinned corpora and COUNTS WITH HONEST WORDS ("engine finding — report this to AISQL") on customer runs, never blocking their boot on our defect — CLOSED same day via Brief_Closed_Shape (BUILT 2026-09-20): THE NAME GRAMMAR table lives in Contract_Logic_Layer; the closed enum + unresolved_by_class in resolve; the wording rule in write_intake_result_tables; the arity conformance pin (test_name_grammar) + the shakedown's per-class conservation (127 = 127 reader_writer_drift, sum == total, so nothing fails unclassified) |
| F13 | CI IS RED ON BOTH BRANCHES (lint step, 4 errors) and every error PRE-DATES the 2026-09-20 push — found watching the "push and promote" runs (dev red since c346120 that morning; main inherits at the promotion). THE FOUR: (a) E902 `./*.Notebook/` — ci.yml's lint line still cites the Notebook folders Brief_Retirement removed (a missed consumer of the retirement); (b) E902 `notebooks/` — the folder exists ONLY untracked on Sunny's disk, CI's checkout has none; (c)+(d) I001 devtools/answer_evals.py:40 + devtools/grounding_evals.py:50 — BOTH ARE CORPSES: they import the RETIRED src.orchestrator.* / src.parser (ModuleNotFoundError on import — they cannot run at all); nothing executes them (references are history docs + one suite_map comment; devtools/local_llm.py is consumed only by them). THE MASK: the local ruff cache said "All checks passed" on these exact files — `--no-cache` reproduces CI byte-for-byte, so every recent local "ruff zero new" was cache-blind to these two; the ruff-before-push law needs --no-cache to mean anything | found at the push-and-promote CI watch, 2026-09-20; local repro: `ruff check --no-cache src/ tests/ scripts/ devtools/` | RULED (Sunny "agree with all three, build it", 2026-09-20) + CLOSED same day via Brief_CI_Lint: (1) the ci.yml lint line is `ruff check src/ tests/ scripts/ devtools/`; (2) answer_evals.py + grounding_evals.py + local_llm.py retired in the act; (3) CLAUDE.md's ruff habit is `--no-cache`. Tripwired RED-first (tests/test_ci_lint_paths.py: every lint path tracked + glob-free · the corpses stay gone); CI's exact lint command passes uncached locally |
| F14 | THE SAME CLASS, DEEPER IN src/ (found executing F13's ruling): src/agent_backend.py imports the RETIRED src.parser.identity at line 24 (ModuleNotFoundError on import — a runtime corpse ruff cannot see; its docstring also cites the now-retired devtools/local_llm.py) and src/trace_registry.py:561 names tests/test_grounding_evals.py, a file that does not exist. Brief_Retirement's sweep (src/ 134→15) kept files whose imports died with the ones it removed — lint-green, import-dead | found during Brief_CI_Lint's impact query, 2026-09-20 | OPEN — Sunny's word: a leftover sweep (import every kept src/ module, retire or fix what cannot import) is the mechanical check; NOT in Brief_CI_Lint's ruled scope |
| F15 | CI'S TEST STEP CANNOT BUILD THE WHEEL: the three test_wheel_boot pins ERROR on CI with "Missing dependencies: wheel" — devtools/build_wheel.py:46 runs `python -m build --wheel --no-isolation`, and with --no-isolation the build-system requires (pyproject line 2: setuptools + wheel) must already sit in the running env; the [dev] extras pin `build` (1.5.0/1.4.4) but never `wheel`, so CI's `pip install -e ".[dev]"` env lacks it. Local suites never saw it (wheel is installed on Sunny's machine); CI's Check-packaging step installs `build twine` but runs AFTER tests and never fed them. First seen at commit 2b4a341's run 35663282024 — the FIRST CI test-step run since F13's lint fix let tests execute at all, so whether it ever passed on CI is unverifiable (F13 masked it since at least c346120). Same F13 family: the CI env drifted from the local one, and the green local suite could not say so. The run's OTHER red is not a finding: the known 406-text RecordingGap class awaiting the ruled closing sequence (his AISQL_RECORD run) | found watching commit 2b4a341's CI run (his "commit and push", 2026-09-21); local repro: `pip uninstall wheel` then any test_wheel_boot test | RULED (Sunny "agree, fix it", 2026-09-21) + CLOSED same day: the [dev] extras now carry EVERY [build-system] require, pinned exactly per the F13 rule — `wheel==0.47.0` (single pin, floor >=3.9) and setuptools dual-pinned (83.0.0 on >=3.10 · 80.9.0 on the 3.9 Fabric-floor leg; 81+ dropped 3.9) — setuptools joined because it is the SAME class one require over (present on today's CI image only by accident; enumerate-all-cases). The pin lives where the need lives: test_build_requires_ride_the_dev_extras (test_wheel_boot.py, RED-first) parses pyproject and asserts every [build-system] require has an exact-pinned dev-extras carrier — a future require added without its carrier fails the suite everywhere, not just on CI. No requirements.txt change (the constraints file holds only cross-listed runtime pins; dev tools pin in the extras — the build/pytest/ruff precedent). The dist/ 2.5.0 wheel stands untouched: dev-extras metadata is not shipped behavior, and no pin compares dist bytes; the METADATA delta rides the next wheel cut (the Brief_Anaphor_Clarify precedent). RIDER (same day): the fix's own CI run caught its last loose end — the pin test's imports (packaging · tomli on <3.11) were transitive-only; test_every_thirdparty_import_is_declared went red on CI where the targeted local run had not looked; both now declared exact in the dev extras (packaging==26.3 · tomli==2.4.1;<3.11). The miss is the F13 lesson restated: targeted runs are not the suite |
| F16 | THE 3.9 FABRIC-FLOOR LEG'S FIRST TEST RUN EVER surfaced two version-blind assumptions (fc1ef5b's run: 3.11 fully GREEN — the first all-green CI test job — while 3.9 failed 8): (a) the F15 pin test's `import tomllib` fork — tomllib is stdlib only on 3.11+, and the declaration tripwire scans SOURCE statically, so on 3.9 it demanded a declaration that cannot exist; (b) FIVE console-surface tests (test_ask_console CS1–CS3 + test_click_reroute ×4… 5 of the up-to-7 urlopen callers) died socket.timeout at their 10-second local-server timeout on a runner that needed 30:40 for an 8-minute suite — slow-leg starvation, not a version defect (3.11 passed the same tests on the same commit) | found reading run 35666769593's 3.9 job log, 2026-09-21 | CLOSED in the act (the CI-green continuation Sunny's F15 "agree, fix it" opened): (a) ONE import on every leg — `import tomli as tomllib`, tomli==2.4.1 declared unconditionally (floor >=3.8; the marker fork retired); (b) the three urlopen sites go timeout=60 — patience, zero behavior change. Touched modules 30/30 locally; the 3.9 leg's own green is the closing proof at the next push |
