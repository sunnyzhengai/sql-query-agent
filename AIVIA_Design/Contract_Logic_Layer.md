# Contract_Logic_Layer — the logic graph's data contracts

**Status: RATIFIED (Sunny's gap-check passed, 2026-09-16 — "two
contracts passed"); populated same day from the live system.** Second document of the contract
system (conventions in Contract_Technical_Layer.md; process in
Ruling_Change_Process.md). This layer is what the SQL MEANS: the
structures born from parsing the estate's files.

## DESIGN_SECTIONS (governing this layer)

| ds_id | says (short) | status | home doc |
|---|---|---|---|
| ds.scope_identity | scope name keys = file::name / file::name#i; delivery emitters mint file::delivery (plural: delivery_1..n + the DBA list) | RULED | Design_Graph_Engine — SCOPE IDENTITY (re-homed 2026-09-17, CI-A1; the registry sheet transcribes it) |
| ds.m2_join_redesign | a scope reaches its tables THROUGH its join nodes; joins and conditions are separate batches; sides = the ON-resolved pair, syntactic order | RULED 09-10, batch CLOSED | Design_Graph_Engine |
| ds.kind_vs_label | condition is ONE label; the predicate kind is a PROPERTY from the closed registry set; a new kind is a registry row, never a label | RULED | Design_Graph_Engine |
| ds.m3_condition_layer | condition trees materialize (parentage carries clause; clauseProvenance retired); resolves_to role-tagged | RULED 09-10, batch CLOSED | Design_Graph_Engine (the retirement sentence + role vocabulary; pointer fixed 2026-09-17, CI-A4) |
| ds.era3_from_structure | every FROM walks scope—has_part→(join \| direct_read)—sides; the reads EDGE retired; ONE invariant: side-targets == read-set | RULED 09-14, CLOSED 09-15 | Design_Graph_Engine era-3 |
| ds.m4_stay_flat | one derived_column node per computed output; expression trees stay at L1 | RULED 09-16, batch CLOSED | Design_Graph_Engine registries stamp 1.45.0 (pointer fixed 2026-09-17, CI-A4) |
| ds.cites_store_grain | cites = distinct (scope, dictionary column) its outputs draw on | RULED 09-16 (measured re-base) | Design_Graph_Engine edge vocabulary — cites (the tuple definition landed 2026-09-17, CI-A4) |
| ds.birth_edge_law | a node ships only in the batch where its birth edge points DOWN at verified nodes | RULED | Design_Graph_Engine — Migration, THE BATCH LAW (re-homed 2026-09-17, CI-A3) |
| ds.ruled_silent_index | joins, direct_reads, statements stay OUT of the ask index (connective structure / until §D); scopes are IN | RULED | Design_Chatbot riders — THE RULED-SILENT LIST (consolidated 2026-09-17, CI-A5) |
| R1–R7 · R10 · R12 · (R11 reserved) | the voicing grammar per grain (R10 = the file/report floor) | RULED (R11 unwritten — M5) | Grammar_Floor |

## DATA_CONTRACTS

| dc_id | kind | what it is | writer | count (ed_sepsis_dev) | status |
|---|---|---|---|---|---|
| dc.file | node | one SQL file of the estate | estate intake | 1 | LIVE |
| dc.statement | node | one statement of a file (id file::stmt/N) | (M5 builder) | 0 | **TARGET — M5, planned** |
| dc.scope | node | one named selection (CTE / #temp / delivery) | scope builder | 44 | LIVE |
| dc.join | node | one observed join: which pair combines, how, on what | join layer builder | 95 | LIVE |
| dc.direct_read | node | the single-table FROM's sided node (no ON, no type — absence in the KIND) | era-3 builder | 6 | LIVE |
| dc.condition | node | one predicate, leaf or composite (kind = property) | condition layer builder | 1,141 | LIVE |
| dc.param | node | a procedure parameter consulted by scopes | condition layer builder | 2 (+2 at M5) | LIVE |
| dc.derived_column | node | one computed output of a scope (STAY FLAT) | M4 builder | 156 | LIVE |
| dc.meaning_twin | node (internal) | the translated twin blob of a file | translator | 1 | LIVE — retires at M9 (parse records) |
| dc.has_part (logic rows) | edge | scope→join · scope→direct_read · join/scope/condition→condition · scope→derived_column (+ file→statement at M6) | the respective builders | 1,398 | LIVE |
| dc.left_side / dc.right_side | edge | a join's or direct_read's resolved pair (side order syntactic) | join + era-3 builders | 101 / 87 | LIVE |
| dc.resolves_to | edge | condition → dictionary column or param, ROLE-tagged | condition layer builder | 165 | LIVE |
| dc.uses_param | edge | scope → param it consults | condition layer builder | 2 | LIVE |
| dc.cites | edge | scope → dictionary column its outputs draw on | M4 builder | 97 | LIVE |

## CONTRACT_FIELDS (per type; name fields omitted where verbatim-from-source)

| dc_id | field | writer | rules | checks |
|---|---|---|---|---|
| dc.file | description (speech) | kg3 description artifact via the Scribe, gated drafted→approved — NOT a node property | R10 file floor · LLM cage | produce gates + F4 |
| dc.scope | description | grammar renderer (scope lead) | inv.verbatim | test_scope_layer |
| dc.scope | structures | parse, machine fact | inv.derivable_never_stored | mapper tests |
| dc.join | description · onPredicate · joinType | join renderer + tree | inv.verbatim; joinType from tree | estate M2 battery |
| dc.direct_read | description | read_render | inv.verbatim | era-3 battery |
| dc.condition | description | grammar renderer (R1–R7 + annotations R8) | inv.verbatim · library words | verbatim suite |
| dc.condition | kind · degenerate · fragment | parse; kind from CLOSED registry set | ds.kind_vs_label | kind-library lock |
| dc.param | description | builder (fixed phrase) | — | estate battery |
| dc.derived_column | description | R12 renderer + function library | inv.verbatim · library words | verbatim + parity gate |
| dc.derived_column | derivation · operation · position · fragment | parse, machine facts | ds.m4_stay_flat | estate M4 battery |
| dc.resolves_to | role | parse (closed role vocabulary) | ds.kind_vs_label (roles) | role census |
| dc.statement | (planned) description | R11 renderer — **R11 UNWRITTEN** | operational subkind voiced NEVER — **RULED (b) (Sunny "b", 2026-09-17): the 36 data-producing statements get R11 descriptions; the 31 operational store NOTHING (none-ruled, zero is legal — the db/db_schema precedent), the emptiness COUNTED never silent; a fixed phrase would restate the node's own kind field (derivable is never stored). Gate check re-pins 67→36 nonempty + 31 empty-by-rule** | (M5 tests) |

## CONSUMERS

| dc_id | consumer | reads | re-verify |
|---|---|---|---|
| dc.scope · dc.condition · dc.param · dc.derived_column · dc.file | sc.ask_console | description as searchable text | speech parity gate |
| dc.join · dc.direct_read | sc.ask_console | **NOTHING — ruled-silent (ds.ruled_silent_index)** | parity gate (absent check) |
| all LIVE types | sc.meaning_console | descriptions + structure walks | console battery (18 blessed) |
| all LIVE types + edges | sc.fabric_export | per-type graph_* parquets | export census tests |
| all LIVE types | sc.graph_visual | name · description · edges | visual counts vs key |
| dc.condition trees | sc.grammar_render (floors) | predicates for scope/file floors | verbatim suites |
| dc.meaning_twin | sc.translator | the twin blob | homomorphism law tests |

## GOVERNS

| ds_id | governs |
|---|---|
| ds.scope_identity | dc.scope (identity), dc.statement (planned identity) |
| ds.m2_join_redesign | dc.join · dc.left_side/right_side · the read-set walk |
| ds.kind_vs_label | dc.condition.kind · dc.resolves_to.role (closed sets) |
| ds.m3_condition_layer | dc.condition · dc.param · dc.resolves_to · dc.uses_param |
| ds.era3_from_structure | dc.direct_read · the reads retirement · the ONE invariant |
| ds.m4_stay_flat + ds.cites_store_grain | dc.derived_column · dc.cites |
| ds.birth_edge_law | every dc row's shipping batch |
| ds.ruled_silent_index | dc.join/direct_read/statement × sc.ask_console |
| R1–R7 / R10 / R12 | the description fields per grain |
| inv.verbatim · inv.derivable_never_stored · inv.one_writer | every field above |

## TESTS

| test_id | proves |
|---|---|
| test_from_structure (4 pins) | ds.era3_from_structure incl. the ONE invariant |
| test_ed_sepsis_dev_estate (M2/M3/M4 batteries) | counts vs key · conservation · verbatim · parentage |
| test_derived_render (19) + test_derived_column | R12 · ds.m4_stay_flat · F2-fixture negatives |
| test_speech_parity | consumers' speech == contract (incl. the absent checks) |
| test_joins_to_lock · kind-library locks | closed sets, one-authority |
| test_part_edges · test_shape_census | birth edges · ledger both directions |
| verbatim/floor suites (F4 + estate) | stored == recomputed everywhere |

## FINDINGS (from populating this contract, 2026-09-16)

| id | finding | kind | status |
|---|---|---|---|
| FL1 | a reference to a COMPUTED or temp-table column carries NO store edge (dc.resolves_to reaches dictionary columns only) → "which scope reads derived_column X" is not graph-walkable; meaning resolves through the defining projection (Gap B) but no edge lands | missing edge class — surfaced in the AGE_IN_DAYS "correct behavior" discussion | RULED (Sunny "yes", 2026-09-16): a declared OPEN SLOT — **THE COMPUTED-READ EDGE**, sequenced AFTER M5; enters via its own brief carrying its design questions (edge name · extend resolves_to with a role vs a new edge · exact grain — Sunny's rulings, never builder picks); pairs with the ask-console convergence decision |
| FL2 | dc.statement is TARGET: M5 planned (67; operational 31 = counted-missing debt until M6); R11 unwritten | planned OPEN slot | OPEN by design — the M5 entry gate |
| FL3 | dc.meaning_twin duplicates meaning beside the graph (one-home tension) with retirement PLANNED at M9 (parse records) | declared, dated tension | OPEN — rides the Phase-2 ladder |
| FL4 | joins/direct_reads/statements are ruled-silent in the ask index — deliberate, now visible as consumer rows reading NOTHING | deliberate fact made visible | CLOSED — the rows are the proof |
| FL5 | description quality: unblessed vendor words produce dangling phrases ("the date and time when") across condition AND derived_column descriptions — the R5 steward class | steward queue, not a code defect | OPEN — rides Sunny's blessing pace |
| FL6 | invariant id split: line 49 said inv.derivable_never_authored, line 85 says inv.derivable_never_stored — two names for one law breaks the join; and inv.* ids had NO home table in any contract doc (referenced, never defined) | contract-integrity, review query 2026-09-16 | RULED (Sunny "a", 2026-09-17) + CLOSED same breath: the ONE name is inv.derivable_never_stored (the CLAUDE.md wording); the INVARIANTS table lives in Contract_Technical_Layer beside the conventions (home of all layers' inv rows); the stray spelling corrected above |
| FL7 | the M5 gate disagrees with itself: expected_m_gates.json census_after.M5.condition = 1147 (store truth, the 1141 re-base) but description_coverage says "754/754 at M5" (the old twin count 748+6); same split inside GQL_Gates.md (line 549 "total→754" vs line 105 "condition→1147") — the M3 measurement re-base never reached the coverage strings | gate-sheet drift, review query 2026-09-16 | RULED (Sunny "yes", 2026-09-17): the two stale lines correct to the MEASURED numbers — coverage "1141/1141 at M3, 1147/1147 at M5", GQL_Gates "total→1147" — finishing the M3 re-base; via Brief_Gate_Number_Rebase |
| FL8 | inbound.py:557 declares "held_statement_rooted": 0 and nothing ever increments it — the condition walker (decisions.named_scopes) never visits a statement's own predicate subtree, so the counter reads 0 for the wrong reason; the 6 IF predicates + @StartDate/@EndDate are not "held", they are out of reach. Also: the estate test asserts twin subkind == "operational" but kg2_mapper writes no subkind field — the writer must be located before the M5 build | placeholder-law class (a counter that cannot fire), review query 2026-09-16 | OPEN — the M5 brief carries both: give the counter a real value or retire it; name subkind's one writer |
