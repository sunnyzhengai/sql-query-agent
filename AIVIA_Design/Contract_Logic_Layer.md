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
| R1–R7 · R10 · R11 · R12 | the voicing grammar per grain (R10 = the file floor; R11 = the statement step, ratified v2.11.0 at M5) | RULED | Grammar_Floor |

## DATA_CONTRACTS

| dc_id | kind | what it is | writer | count (ed_sepsis_dev) | status |
|---|---|---|---|---|---|
| dc.file | node | one SQL file of the estate — SERVED at M6 with THE TWO GOVERNANCE FIELDS | estate intake; fields: file layer (technical_definition) + receive_descriptions (description, approved-only) | 1 | LIVE (M6 BUILT 2026-09-17) |
| dc.statement | node | one statement of a file (id file::stmt/N) | M5 builder (_store_statement_layer, after scopes before conditions — M5-1) | 67 | LIVE (M5 BUILT 2026-09-17) |
| dc.scope | node | one named selection (CTE / #temp / delivery) | scope builder | 44 | LIVE |
| dc.join | node | one observed join: which pair combines, how, on what | join layer builder | 95 | LIVE |
| dc.direct_read | node | the single-table FROM's sided node (no ON, no type — absence in the KIND) | era-3 builder | 6 | LIVE |
| dc.condition | node | one predicate, leaf or composite (kind = property) | condition layer builder | 1,147 (+6 statement-rooted at M5) | LIVE |
| dc.param | node | a procedure parameter consulted by scopes or statements | condition layer builder | 4 (+2 at M5: @StartDate/@EndDate) | LIVE |
| dc.derived_column | node | one computed output of a scope (STAY FLAT) | M4 builder | 156 | LIVE |
| dc.meaning_twin | node (internal) | the translated twin blob of a file | translator | 1 | LIVE — retires at M9 (parse records) |
| dc.has_part (logic rows) | edge | scope→join · scope→direct_read · join/scope/statement/condition→condition · scope→derived_column · statement→scope · file→statement · file→param | the respective builders | 1,519 (+71 at M6 — THE 31-STATEMENT DEBT RETIRED at its named landing step) | LIVE |
| dc.left_side / dc.right_side | edge | a join's or direct_read's resolved pair (side order syntactic) | join + era-3 builders | 101 / 87 | LIVE |
| dc.resolves_to | edge | condition → dictionary column or param, ROLE-tagged | condition layer builder | 169 (+4 at M5) | LIVE |
| dc.uses_param | edge | scope or statement → param it consults | condition layer builder | 4 (+2 statement→param at M5) | LIVE |
| dc.cites | edge | scope → dictionary column its outputs draw on | M4 builder | 97 | LIVE |

## CONTRACT_FIELDS (per type; name fields omitted where verbatim-from-source)

| dc_id | field | writer | rules | checks |
|---|---|---|---|---|
| dc.file | description (report description, Collibra-named) | receive_descriptions — the ONE writer; lands ONLY approved artifact text (the Scribe summary OF the technical definition; Sunny "APPROVED" 2026-09-17); empty-until-approved COUNTED | the LLM cage vs the R13 catch-all · meaning-key anchor | test_m6_two_governance_fields · speech parity (aboutness) |
| dc.file | technical_definition (Collibra-named) | file layer (R13 THE CATCH-ALL, RATIFIED v2.12.0) | inv.verbatim — stored == recomputed byte-exact | test_file_render (hash pin) · estate M6 battery |
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
| dc.statement | description | R11 renderer (**RATIFIED v2.11.0, Sunny "ratified" 2026-09-17** — the 36 gap-checked at the mid-build checkpoint) | operational subkind voiced NEVER — **RULED (b) (Sunny "b", 2026-09-17): the 36 data-producing statements get R11 descriptions; the 31 operational store NOTHING (none-ruled, zero is legal — the db/db_schema precedent), the emptiness COUNTED never silent; a fixed phrase would restate the node's own kind field (derivable is never stored). Gate check re-pins 67→36 nonempty + 31 empty-by-rule** | test_statement_render (11 incl. the 2 byte-exact estate IFs) · test_statement_layer · estate M5 battery · parity absent-check |

## CONSUMERS

| dc_id | consumer | reads | re-verify |
|---|---|---|---|
| dc.scope · dc.condition · dc.param · dc.derived_column · dc.file | sc.ask_console | description as searchable text | speech parity gate |
| dc.join · dc.direct_read · dc.statement | sc.ask_console | **NOTHING — ruled-silent (ds.ruled_silent_index; statement re-affirmed at M5: "leave as is")** | parity gate (absent check) |
| all LIVE types | sc.meaning_console | descriptions + structure walks | console battery (18 blessed) |
| all LIVE types + edges | sc.fabric_export | per-type graph_* parquets | export census tests |
| all LIVE types | sc.graph_visual | name · description · edges | visual counts vs key |
| dc.condition trees | sc.grammar_render (floors) | predicates for scope/file floors | verbatim suites |
| dc.meaning_twin | sc.translator | the twin blob | homomorphism law tests |

## GOVERNS

| ds_id | governs |
|---|---|
| ds.scope_identity | dc.scope (identity); dc.statement identity (file::stmt/N, landed M5) |
| ds.m2_join_redesign | dc.join · dc.left_side/right_side · the read-set walk |
| ds.kind_vs_label | dc.condition.kind · dc.resolves_to.role (closed sets) |
| ds.m3_condition_layer | dc.condition · dc.param · dc.resolves_to · dc.uses_param |
| ds.era3_from_structure | dc.direct_read · the reads retirement · the ONE invariant |
| ds.m4_stay_flat + ds.cites_store_grain | dc.derived_column · dc.cites |
| ds.birth_edge_law | every dc row's shipping batch |
| ds.ruled_silent_index | dc.join/direct_read/statement × sc.ask_console |
| R1–R7 / R10 / R12 | the description fields per grain |
| inv.verbatim · inv.derivable_never_stored · inv.one_writer | every field above |

## THE NAME GRAMMAR (Brief_Closed_Shape; F12 ruled "i agree with your recommendation" + F11 "agree with F11", 2026-09-20)

Microsoft's documented T-SQL object-name grammar — 1 to 4
dot-separated parts, `server.database.schema.table`, inner parts
may be EMPTY — is finite, so this table is exhaustive by
construction. The customer defines NOTHING; ScriptDom refuses
arity ≥5 at parse time. Consumer: kg2_mapper.resolve (this
layer's one resolution writer). THE LAW: every written form lands
in its RULED bucket below; a shape outside the grammar counts as
`shape_unrecognized` — NEVER coerced into the nearest known shape
(the generator find, F12: the ABX corpse and F9's diagnosis were
this one defect class). Enforcement: test_name_grammar.py (the
generated arity table) + the shakedown's per-class conservation
(classes sum to unresolved_refs; shape_unrecognized on a pinned
corpus FAILS THE SUITE — the internal lane; on a customer run it
COUNTS with the engine-finding sentence, never blocking their
boot — the ruled split).

| written form | ruled bucket |
|---|---|
| `T` (1 part) | binds via the estate's declared default_schema; none declared → unresolved, class `no_default_schema` (never a guess) |
| `S.T` (2 parts) | binds via schema_sources; schema unmapped → `schema_not_mapped`; table absent → `table_not_in_dictionary` |
| `D.S.T` (3 parts) | ruling (8), counted-never-refused: db matches registration (folded) → binds; differs → unresolved, class `cross_database`, census.cross_database_reads names the db; db_name waived → binds + census.db_names_seen |
| `D..T` / `.T` (empty schema part) | the empty part falls to default_schema (legal T-SQL); then as above |
| `V.D.S.T` (4 parts) | F11 ruled — the ruling-(8) symmetry one level up: server matches → binds (the match IS the cross-check); differs → unresolved, class `cross_server`, census.cross_server_reads names the server (a linked-server read is another machine's data, never bound locally); server waived (optional, MR1a) → binds + census.server_names_seen |
| anything else (arity ≥5 · empty table part) | class `shape_unrecognized` — the reserved bucket; the sheet prints the engine-finding sentence verbatim |

THE CLOSED DIAGNOSIS ENUM (one class per unresolved ref; the ONE
literal lives with the writer): `schema_not_mapped` ·
`table_not_in_dictionary` · `cross_database` · `cross_server` ·
`no_default_schema` · `reader_writer_drift` (column refs — the
silently-failing-report class) · `shape_unrecognized`. THE
WORDING RULE (proposal 3): the DBA sheet may blame the customer's
data only for fully-understood classes; the reserved class prints
"AISQL COULD NOT READ THIS REFERENCE SHAPE — an engine finding …
report this to AISQL" — a code defect can never again print as
the customer's problem.

## TESTS

| test_id | proves |
|---|---|
| test_name_grammar (the generated arity table + the wording rule) | THE NAME GRAMMAR — every written form in its ruled bucket; diagnoses honest |
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
| FL2 | dc.statement was TARGET: M5 planned (67; operational 31 = counted-missing debt until M6); R11 unwritten | planned OPEN slot | CLOSED (M5 BUILT 2026-09-17, Brief_M5_Statement_Layer): 67 LIVE, R11 RATIFIED v2.11.0, the 31 counted-missing stand declared until M6 |
| FL3 | dc.meaning_twin duplicates meaning beside the graph (one-home tension) with retirement PLANNED at M9 (parse records) | declared, dated tension | OPEN — rides the Phase-2 ladder |
| FL4 | joins/direct_reads/statements are ruled-silent in the ask index — deliberate, now visible as consumer rows reading NOTHING | deliberate fact made visible | CLOSED — the rows are the proof |
| FL5 | description quality: unblessed vendor words produce dangling phrases ("the date and time when") across condition AND derived_column descriptions — the R5 steward class | steward queue, not a code defect | OPEN — rides Sunny's blessing pace |
| FL6 | invariant id split: line 49 said inv.derivable_never_authored, line 85 says inv.derivable_never_stored — two names for one law breaks the join; and inv.* ids had NO home table in any contract doc (referenced, never defined) | contract-integrity, review query 2026-09-16 | RULED (Sunny "a", 2026-09-17) + CLOSED same breath: the ONE name is inv.derivable_never_stored (the CLAUDE.md wording); the INVARIANTS table lives in Contract_Technical_Layer beside the conventions (home of all layers' inv rows); the stray spelling corrected above |
| FL7 | the M5 gate disagrees with itself: expected_m_gates.json census_after.M5.condition = 1147 (store truth, the 1141 re-base) but description_coverage says "754/754 at M5" (the old twin count 748+6); same split inside GQL_Gates.md (line 549 "total→754" vs line 105 "condition→1147") — the M3 measurement re-base never reached the coverage strings | gate-sheet drift, review query 2026-09-16 | RULED (Sunny "yes", 2026-09-17): the two stale lines correct to the MEASURED numbers — coverage "1141/1141 at M3, 1147/1147 at M5", GQL_Gates "total→1147" — finishing the M3 re-base; via Brief_Gate_Number_Rebase |
| FL8 | inbound.py:557 declares "held_statement_rooted": 0 and nothing ever increments it — the condition walker (decisions.named_scopes) never visits a statement's own predicate subtree, so the counter reads 0 for the wrong reason; the 6 IF predicates + @StartDate/@EndDate are not "held", they are out of reach. Also: the estate test asserts twin subkind == "operational" but kg2_mapper writes no subkind field — the writer must be located before the M5 build | placeholder-law class (a counter that cannot fire), review query 2026-09-16 | OPEN — the M5 brief carries both: give the counter a real value or retire it; name subkind's one writer |
| FL9 | condition prose drops both sides' scopes: `T1.X = T2.X` voices as "The x is the x" (reads as a tautology) and `T1.X = T2.Y` with near-identical names reads the same; the join nodes prove both scopes are KNOWN — the renderer owns the information and does not speak it. CONSEQUENCE, caught live: a second join to the same line-numbered lookup whose ON clause mistakenly filters on the FIRST join's alias (never-matching by construction — a real defect in the operator's estate) shows plainly in the raw join text but the scope-less condition prose "The line is 2" hides it — the rendering masked a defect | voicing gap, work dry run 2026-09-19; reproduces on the sepsis corpus | OPEN — slice C, Brief_Pilot_Findings_R1 |
| FL10 | scalar/temporal functions leak verbatim into prose: "is on or after dateadd(year,-1,convert(date,getdate()))", "the isnull(convert(date,…),'2999-12-31') is on or before …" — the floor needs phrases for the recurring shapes: DATEADD relative to GETDATE → "within the last N units"; ISNULL(date, far-future sentinel) → "treating a missing date as open-ended"; IIF/DATEDIFF likewise | grammar gap (Grammar_Floor amendment, after ruling), same dry run | OPEN — slice C. MECHANISM (second sample, same day): two entry points, both verified — (1) condition subjects voice through value()→_fill_overlay, which carries ONLY the four absorbed overlays (COALESCE/LEFT/RIGHT/DATEADD); the FN_SKELETONS library rows (ISNULL, DATEDIFF, …) fill only on the derived-column path (_fill_library) — so ISNULL in a WHERE can never fill today; (2) the DATEADD overlay's guard reads args[1].value — a NEGATIVE offset parses as a unary expression whose value is None, the guard fails, the whole call renders raw. CONVERT and GETDATE have no rows at all (R12 remainder) |
| FL11 | vendor category columns suffixed _C voice the suffix as a stray word (a column `X_C` speaks as "The x c is 2"); the suffix is the vendor's category-code convention, and with values.csv absent the code stays bare. Two parts: suffix-aware naming at voicing (where does per-vendor naming knowledge live — the source pack?), and the values map filling the meaning when present | voicing gap + pack-knowledge question, same dry run | OPEN — slice C; the naming-home question is Sunny's |
| FL12 | joins have two renderings and the fallback is raw: simple ON clauses voice as prose naming both sides ("Joins A with B on …"); complex ON clauses fall back to "Join on" + the verbatim multi-line SQL, comments and indentation included, naming NEITHER table. The fallback must name both sides and normalize whitespace; inline comments should surface as "(noted …)" as condition prose already does | voicing gap, same dry run | OPEN — slice C. REFINED (second sample, same day): the real fallback trigger is UNRESOLVED SIDES, not ON complexity — four single-equality joins all fell to "Join on <raw>" under F9's resolution failure (join_render names only sides that resolves_to reached); the raw fragment tail is common to BOTH renderings. The fix rides F9 for resolution plus this row for the fragment's voice |
| FL13 | the four WHEN branches of ONE searched CASE landed TWICE as byte-identical condition rows — a double visit in extraction. Generator clause applies: locate the double-walk one level up before any patch; reproduce with a searched CASE on the sepsis corpus | extraction defect, same dry run | OPEN — slice C, investigation first |
| FL14 | LAG collapses to "a value computed from the x" — the prior-row meaning vanishes — while ROW_NUMBER carries its ruled phrase ("the record's position in its ordered sequence"); LAG/LEAD need their own: "the previous/next record's x in its ordered sequence" | grammar gap, same dry run | OPEN — slice C |
| FL15 | THE HEADLINE: scope/CTE descriptions voice only the FROM-shape ("Drawn from A, combined with B, …"), flattening population-defining inner joins together with decorating lookups and omitting grain and payload — unusable as a Business Term definition, the operator's declared consumer ("i'll want to use the CTE descriptions as Business Terms definitions. but right now it's not accurate", Sunny, 2026-09-19). All three ingredients already exist in the graph: grain (the window partition), population (inner-join + WHERE conditions), payload (the selected/derived columns). Proposed composition: "One record per <grain>: <population restrictions>, carrying <payload>." | design change — the pilot's target sentence, same dry run | OPEN — slice D, the design centerpiece; Sunny's design questions in the brief. CORRECTED (second sample, same day): the ingredient claim overclaimed — grain is NOT graph-held (the mapper stores over=True as a flag, never the PARTITION BY/ORDER BY contents — FL17), and payload is only PARTLY held (derived columns are nodes; aliased pass-through columns are counted, never minted, per the sealed M4 census law — a rename like an author's business alias for a plain column is exactly the payload's best words and lives only in the tree). D depends on the over-capture build (FL17) and needs a ruled payload source |
| FL16 | a NOT predicate lands as TWO condition rows speaking OPPOSITE sentences: the NOT node voices folded per Grammar 2.5.0 ("The x is none of the values …") AND the condition walker (inbound emit, which recurses into every predicate child unconditionally) mints the NOT's child as its own row voicing the positive ("The x is one of the values …"). Any flat listing of a scope's conditions shows the contradiction side by side — a long exclusion list appears twice, once as "none of", once as "one of"; same for NOT LIKE ("does not contain" beside "contains"). The graph holds them as parent→child, but the child's stored description reads as an active filter with reversed meaning | double-voicing vs tree-structure tension — second work dry run, 2026-09-19; reproduces on any NOT in the sepsis corpus | OPEN — slice C, after Sunny rules ambiguity (9): is the NOT child a real structural row (keep, perhaps marked), or does 2.5.0's "one meaning, one phrase" fold it entirely? |
| FL17 | the window's PARTITION BY / ORDER BY never enter the tree — the mapper stores over=True as a FLAG (kg2_mapper line 105), and the ROW_NUMBER phrase compensates with the contentless skeleton "the record's position in its ordered sequence": a ranking column whose meaning is "position within each patient, ordered by filing order" loses both the per-what and the by-what. The deferral was recorded with its reason (produce.py, the R12 build: "capture is a twin-structure act") — THIS SIGHTING IS THE DEFERRAL'S ECHO, and per the Echo Law the capture becomes a mandatory build with this echo as its acceptance test. Slice D's grain ingredient ALSO stands on it (the FL15 correction) | echo of a recorded deferral — second work dry run, 2026-09-19 | OPEN — slice E (echo-mandated), sequenced by Sunny; the acceptance test: a partitioned ROW_NUMBER dcol whose stored phrase names its partition and its ordering |
| FL18 | the AND-group sentence counts two as "All 2 of its parts hold." — English says "Both of its parts hold."; the n==2 case deserves its own word | grammar polish, second work dry run, 2026-09-19 | OPEN — slice C, one line in the group renderer + its pin |
