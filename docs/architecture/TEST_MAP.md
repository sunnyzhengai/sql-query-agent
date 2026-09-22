<!-- GENERATED FILE — do not edit.
     Sources: src/trace_registry.py claims + docstring
     Proves: lines (devtools/suite_map.py grammar).
     Regenerate: python scripts/generate_docs.py
     CI fails if stale or if any module proves nothing
     on record (tests/test_suite_map.py). -->

# Test Map — what every test proves

100 modules, 873 tests, every module accounted: claimed by an ADR in the trace registry or declaring a law/contract in its docstring (`Proves:` line).

## By ADR

| ADR | Title | Test modules |
|---|---|---|
| 0001 | Native parsers per SQL dialect | `tests/test_native_parser_law.py` (3) |
| 0002 | Delta tables over an external graph database |  |
| 0003 | Store sql_fragments, not full SQL blobs |  |
| 0004 | Two-stage human-in-the-loop certification |  |
| 0005 | Agent refuses when no certified path exists |  |
| 0006 | Knowledge graph answers questions; Purview discovers reports |  |
| 0007 | BYOT deployment as a Python library (.whl) | `tests/test_release_consistency.py` (3), `tests/test_secrets_vault.py` (6) |
| 0009 | Catalog integrations are optional adapters | `tests/test_docs_consistency.py` (6) |
| 0013 | List as transactable SaaS on the commercial marketplace |  |
| 0014 | Ground the agent in metric_logic; dictionary is mandatory |  |
| 0015 | metric_id is the universal identity | `tests/test_schemas.py` (8), `tests/test_table_contracts.py` (10) |
| 0016 | Case-insensitive identifier matching, folded uppercase |  |
| 0017 | Resolve-then-traverse agent retrieval |  |
| 0018 | Materialized closure edges (USES_TABLE) |  |
| 0019 | CTE descriptions bottom-up, before metric descriptions | `tests/test_llm_client.py` (14) |
| 0020 | Generator-compatibility LPG export shape |  |
| 0021 | Certification discloses, never gates | `tests/test_schemas.py` (8) |
| 0022 | Definition versioning: certification pins a content hash | `tests/test_schemas.py` (8) |
| 0023 | Usage-weighted governance flywheel |  |
| 0024 | Layered truth: personal beside enterprise definitions | `tests/test_schemas.py` (8), `tests/test_table_contracts.py` (10) |
| 0025 | PHI scanning at ingestion; the LLM boundary is the gate |  |
| 0026 | Error-to-data lineage |  |
| 0027 | Ownership attribution: manual floor, Entra ID enriches |  |
| 0030 | Layered retrieval: search terms first, vectors where allowed |  |
| 0031 | Business terms: weighted plurality |  |
| 0032 | Deterministic core, LLM edges |  |
| 0033 | System of record + projections: Delta is the record |  |
| 0035 | Agentic conversation over deterministic tools |  |
| 0036 | Operations are the product: plan, confirm, execute, display |  |
| 0037 | The completed algebra: traverse + result-set kernels |  |
| 0038 | The interaction layer: 'no' is input |  |
| 0039 | Every error links to its contract | `tests/test_table_contracts.py` (10) |
| 0040 | The consumption layer: reports and measures |  |
| 0041 | M mini-parser, shape registry, fallout capture |  |
| 0042 | The notebook contract: a harness for the driver layer | `tests/test_docs_consistency.py` (6) |
| 0043 | The diff kernel: the founding question's shape |  |
| 0044 | The tree contract: round-trip verified descriptions |  |
| 0045 | The escalation contract: no silent residue |  |
| 0046 | Anchor, discover, match, rank — the human picks |  |
| 0047 | The shadow specification (the axiom system) | `tests/test_axiom_crosswalk.py` (7) |
| 0048 | Declared zones, trace registry, admin graph, companion | `tests/test_trace_registry.py` (12), `tests/test_zones.py` (4) |
| 0049 | Ingestion routes: filedrop, folders, live extractor |  |
| 0050 | Bounded read-only answer loop: plan to the answer, caption answers, auto-continue (amends 0036) |  |
| 0051 | The one-mind turn: one conversation decides, the boundary enforces (supersedes 0036/0050's shape) |  |
| 0052 | The reachability contract: every graph payload reachable by a named op or excluded with a reason |  |
| 0053 | Projection-grain column lineage: transform_to_column edges, resolved-only, conservation-counted |  |
| 0054 | Governance red flags and governed plurality: misnomer/duplicate/cousin sweep over content hashes |  |
| 0055 | The designed shape corpus: spec-derived test data (category-partition over name x logic x scope) |  |
| 0056 | The decision algebra: every answer ends in a decision (typed deny, usage weights) |  |
| 0059 | The graph topology axioms: connected, sound, complete (measured, then formalized) |  |
| 0060 | The parse is the plan: parser-only LLM, deterministic traversal, correction flywheel |  |
| 0061 | The run layer: Pro runs the confirmed definition |  |
| 0062 | The dialogue loop: show, propose, ask, execute |  |
| 0063 | The product tiers: X-Ray, Bridge, Workbench, Run |  |
| 0064 | Group L: the ledger and drift axioms (closing the crosswalk gaps) | `tests/test_ledger_contract.py` (4) |
| 0065 | Promote section 13 to Group T: the double-sided function as numbered law |  |
| 0067 | Docs are data: the record invariant and the prose ratchet | `tests/test_spec_registry.py` (8) |
| 0068 | The landing matrix as data (ratchet turn 2) | `tests/test_landing_registry.py` (6) |
| 0069 | SOURCE_CONNECTORS retires into the integration registry (ratchet turn 3) | `tests/test_integration_doctrine.py` (4) |
| 0070 | QUESTION_MAP retires into the notebook registry (ratchet turn 4) | `tests/test_question_families.py` (4) |
| 0072 | The crosswalk goes generated (ratchet turn 6) | `tests/test_axiom_crosswalk.py` (7) |
| 0073 | SPEC v1.0: the spec becomes a projection of its own ledger (final ratchet turn) | `tests/test_spec_registry.py` (8) |
| 0074 | The description architecture, ratified: skeleton floor, gate acceptance, metric-level design |  |
| 0075 | The check contract: checks are claims (spec:G4) | `tests/test_check_contract.py` (4) |
| 0076 | Compositional interpretation: capture once, interpret by grammar (spec:G5) |  |
| 0077 | The twin-graph KG: meaning is a stored homomorphic twin | `tests/aisql/test_design_validators.py` (4), `tests/aisql/test_metamodel.py` (7), `tests/aisql/test_phase_a_projection.py` (6) |
| 0078 | The ask-the-graph console: free questions, typed paths, self-answering nodes | `tests/aisql/test_ask_console.py` (21) |
| 0079 | The interpreter and the speaking graph | `tests/aisql/test_ask_console.py` (21) |
| 0080 | The center and the three censuses | `tests/aisql/test_ask_console.py` (21) |
| 0081 | The birth-edge law | `tests/aisql/test_connection_census.py` (9) |

## By standing law

### law:brand-separation — the product name is a seam; the core stays brand-neutral

- `tests/test_brand_neutral_core.py` (1): Brand-neutral core contract (HANDOFF_BRAND_NEUTRAL_CORE, 2026-08-17).
- `tests/test_branding.py` (5): Tests for the product-name seam (src/branding.py).

### law:endpoint-hygiene — no tenant endpoint ever lives in this repo

- `tests/test_endpoint_hygiene.py` (3): Endpoint hygiene — no tenant endpoint ever lives in this repo.

## By executable contract

### contract:toolchain — every third-party dependency is declared and pinned (Sunny's ruling, 2026-08-19)

- `tests/test_dependency_declarations.py` (1): Every third-party import must be declared in pyproject.toml.
- `tests/test_toolchain_contract.py` (2): The toolchain contract (ruled by Sunny 2026-08-19, delivered 1.30.0).

### contract:suite-legibility — the suite explains itself to Sunny — the proof ledger and the run transcript (morning orders, 2026-08-27)

- `tests/test_secrets_vault.py` (6): KEYVAULT-1 (code-side): "keyvault:<name>" refs resolve through
- `tests/test_suite_map.py` (9): TEST_MAP totality (morning order 1, 2026-08-27): every test module

### contract:org-config — org_config referential integrity, LOCAL and TENANT copies together

- `tests/test_org_config_audit.py` (2): L0 for the org_config referential-integrity audit (ops find 2,

### contract:aisql-design-to-code — aisql code and tests consume the ratified registries and fixture answer keys, never the doc's prose (Design-to-Code protocol, slices 0-8; claimed per-module 2026-09-06 when the suite-map gate reached the aisql suite)

- `AIVIA_Test/test_clarity_source_pack.py` (5): Brief_Clarity_Source_Pack (Sunny, 2026-09-19: "we need contracts
- `AIVIA_Test/test_ed_sepsis_dev_estate.py` (30): The one-proc dev estate + THE M-GATE ANSWER KEY (Sunny's
- `AIVIA_Test/test_fabric_wire.py` (15): THE LIVE-WIRE TOGGLE's tests (Design_Chatbot.md rider, ruled
- `AIVIA_Test/test_joins_to_lock.py` (6): THE JOINS_TO LOCK (Sunny's directive 2026-09-10, after the
- `AIVIA_Test/test_meaning_console.py` (60): THE MEANING-TEST CONSOLE's own tests (Design_Chatbot.md ruling,
- `AIVIA_Test/test_speech_parity.py` (5): THE SPEECH PARITY GATE (Sunny's ruling 2026-09-16, from the
- `tests/aisql/test_acronym_enrichment.py` (7): PHASE I — ACRONYM ENRICHMENT (the one-vocabulary law, ruled
- `tests/aisql/test_approve_land.py` (10): Slice 6 exit: the F5 script against the BUILT approve/land flows.
- `tests/aisql/test_ask_console.py` (21): Tier A exit (ADR 0079): the F10 answer keys go RUNNABLE.
- `tests/aisql/test_blessings.py` (36): R5.b THE BLESSED NAME, slice 1 (Grammar_Floor v2.8.0, ratified
- `tests/aisql/test_business_voice.py` (34): BV1–BV6 — Brief_Business_Voice acceptance pins (Grammar_Floor
- `tests/aisql/test_center_censuses.py` (18): ADR 0080 — the center and the three censuses, red-first.
- `tests/aisql/test_change_gate.py` (12): THE HARD GATE — Brief_Hard_Gate_Hook (P2 ruled 2026-09-16).
- `tests/aisql/test_click_reroute.py` (4): STEP A of the search rebuild — CLICKS ARE STEER (gap 12). Suite
- `tests/aisql/test_connection_census.py` (9): STEP 1 of the Connection Ledger build — THE TEST SUITE, shown to
- `tests/aisql/test_derived_column.py` (4): M4 THE DERIVED-COLUMN LAYER — structural pins on the F2 fixture
- `tests/aisql/test_derived_render.py` (22): R12 THE COMPUTED OUTPUT (Grammar v2.10.0, ratified Sunny
- `tests/aisql/test_design_validators.py` (4): Slice 0: the design validators run in CI — every push re-proves the
- `tests/aisql/test_doubles.py` (6): THE SCRIPTED-PROPOSALS CONTRACT (Sunny's ruling, 2026-09-09:
- `tests/aisql/test_extract_autogen.py` (4): Brief_Extract_Autogen (Sunny, 2026-09-19: "this is too manual.
- `tests/aisql/test_fabric_run.py` (7): Brief_Fabric_Resident FR4+FR5 (Sunny's "all eight as proposed,
- `tests/aisql/test_file_layer.py` (5): M6 THE FILE LAYER — structural pins on the F2 fixture estate
- `tests/aisql/test_file_render.py` (7): §R13 v2 — THE THREE LEVELS (Brief_Pilot_Build_3, Sunny
- `tests/aisql/test_flows_change_quanta.py` (6): The flows' change quanta (CONTRACT_DATALOAD §13 + the flows
- `tests/aisql/test_from_structure.py` (4): ERA 3 — THE FROM-STRUCTURE NODE FAMILY (Design_Graph_Engine,
- `tests/aisql/test_full_circle.py` (7): Slice 7: FULL CIRCLE — one run from empty, every family proven.
- `tests/aisql/test_glossary.py` (11): THE GLOSSARY PROCESS (Ruling_Glossary_Process.md, ruled
- `tests/aisql/test_governance_journal.py` (4): PHASE E1 — THE GOVERNANCE JOURNAL (Sunny's ruling: all user
- `tests/aisql/test_grain_capture.py` (7): SLICE E — THE GRAIN-SOURCE CAPTURE (Brief_Pilot_Build_3,
- `tests/aisql/test_graph_export.py` (13): M1 — THE FABRIC GRAPH EXPORT READING (the materialization plan,
- `tests/aisql/test_intake_hardening.py` (10): Brief_Pilot_Build_1 slices A + B (Brief_Pilot_Findings_R1 F6/F7/F8,
- `tests/aisql/test_kg1_intake.py` (12): Slice 1: KG1 intake vs the F1 answer key — the graph, node by node.
- `tests/aisql/test_kg2_mapper.py` (13): Slice 2 exit: the F2 answer key against the BUILT trees.
- `tests/aisql/test_kg3_artifacts.py` (18): Slice 4: the ledger — KG3 artifact layer lifecycle + derived states.
- `tests/aisql/test_kind_library.py` (4): Slice 2: the kind-library case families (F7) — construct,
- `tests/aisql/test_label_rename.py` (5): STEP D (promoted) — LABEL, not kind. The industry-standard term
- `tests/aisql/test_ledger_close.py` (5): The ledger close (Sunny's order, 2026-09-06): the last engine-debt
- `tests/aisql/test_lenses.py` (11): Slice 3 exit: the F3 answer key against the BUILT lenses.
- `tests/aisql/test_literal_census.py` (1): E3 LOCK 1 — THE LITERAL CENSUS (the literal law, ratified
- `tests/aisql/test_meaning_smells.py` (18): THE MEANING-SMELL CENSUS + THE PHRASE-CORPUS SWEEP (Sunny's go,
- `tests/aisql/test_metamodel.py` (7): Slice 0: the registry loader — code consumes ratified registries only.
- `tests/aisql/test_minimal_registration.py` (6): Brief_Minimal_Registration (Sunny, 2026-09-19: "keep db name and
- `tests/aisql/test_name_grammar.py` (9): Brief_Closed_Shape (Sunny 2026-09-20: F12 "i agree with your
- `tests/aisql/test_part_edges.py` (4): STEP 4 of the Connection Ledger build — PART EDGES. The test
- `tests/aisql/test_pbi_layer.py` (5): PHASE H — THE PBI LAYER (Sunny's ruling 2026-09-08: every proc
- `tests/aisql/test_person_nodes.py` (7): STEP 3 of the Connection Ledger build — PERSON NODES. The test
- `tests/aisql/test_phase_a_projection.py` (6): Phase A exit (ADR 0077): the F8 phase-A answer keys go RUNNABLE.
- `tests/aisql/test_phase_b_translator.py` (10): Phase B exit (ADR 0077): the F8 phase-B answer keys go RUNNABLE.
- `tests/aisql/test_phase_c_voicing.py` (5): Phase C exit (ADR 0077): the F8 phase-C answer keys go RUNNABLE.
- `tests/aisql/test_phase_d_anchors.py` (5): Phase D exit (ADR 0077): the F8 phase-D answer keys go RUNNABLE.
- `tests/aisql/test_phi_gate.py` (8): Slice 2: the PHI boundary — both doors, fixture-driven.
- `tests/aisql/test_planks.py` (6): Slice 0: the planks — the import law and banned constructs as physics.
- `tests/aisql/test_produce.py` (10): Slice 5 exit: produce vs the RATIFIED floor grammar — F4 upgraded
- `tests/aisql/test_refusals.py` (9): Slice 1: the F6 refusal set — every refusal NAMES its rule.
- `tests/aisql/test_registry_mirrors.py` (11): E3 LOCK 2 — THE MIRROR-CHECKS (the literal law; the
- `tests/aisql/test_report_layer.py` (6): M7 THE REPORT LAYER — pins authored FAILING (test-first;
- `tests/aisql/test_root_edges.py` (4): STEP 5 of the Connection Ledger build — ROOT EDGES. The test
- `tests/aisql/test_scope_layer.py` (3): M2 (bottom-up re-ruling, 2026-09-10) — THE SCOPE LAYER.
- `tests/aisql/test_scope_sentence.py` (43): R14 — THE BUSINESS TERM SENTENCE (Brief_Pilot_Build_3, Sunny
- `tests/aisql/test_scribe_draft.py` (2): Brief_Work_Dryrun (Sunny's "approved, both proposals stand",
- `tests/aisql/test_search_is_the_answer.py` (13): STEP B — THE SEARCH IS THE ANSWER (Sunny's pipeline, ruled
- `tests/aisql/test_seat_prompts.py` (4): STEP C of the search rebuild — THE PROMPT IS REGISTRY DATA.
- `tests/aisql/test_sepsis_shakedown.py` (11): The sepsis shakedown (round 2) — conservation counters pinned;
- `tests/aisql/test_shape_census.py` (4): THE SHAPE CENSUS — integrity battery #13 (THE SHAPE CONTRACT,
- `tests/aisql/test_shapes_shakedown.py` (5): The shapes shakedown — the engine over the 38-file ADR 0055 corpus,
- `tests/aisql/test_ship_surface.py` (5): Brief_Packaging slice 1 (Sunny's "all four as proposed, build
- `tests/aisql/test_speech_contract.py` (8): E1 — THE SPEECH CONTRACT build (ruled 2026-09-09, Scribe route).
- `tests/aisql/test_statement_layer.py` (5): M5 THE STATEMENT LAYER — structural pins on the F2 fixture
- `tests/aisql/test_statement_render.py` (15): §R11 THE STATEMENT STEP — byte-exact render pins (authored
- `tests/aisql/test_store.py` (6): Slice 1: the append-only substrate — LC-F2/F3 as structure.
- `tests/aisql/test_term_origins.py` (6): STEP 2 of the Connection Ledger build — TERM ORIGINS. The test
- `tests/aisql/test_three_part_resolution.py` (5): Brief_Pilot_Build_1 slice A2 (Brief_Pilot_Findings_R1 F9, ruling
- `tests/aisql/test_verbatim_census.py` (3): E2 — THE VERBATIM CENSUS (integrity battery #8, ratified in
- `tests/aisql/test_visual_counts.py` (1): FS1 — the graph visual's counts-vs-key re-verify (ruled by
- `tests/aisql/test_wheel_boot.py` (4): Brief_Fabric_Resident FR7 (Sunny's "all eight as proposed,
- `tests/live/test_live_seats.py` (4): THE LIVE TIER — the live-seat rule (Sunny's ruling, 2026-09-09):
- `tests/test_ci_lint_paths.py` (2): THE CI-LINT PATH TRIPWIRE (Brief_CI_Lint, ruled 2026-09-20

## By spec axiom

Two evidence grades, direct always preferred (2026-09-02):
**direct** = the module's docstring declares `Proves: spec:<id>`
— a named, per-axiom claim. **Inferred** = the coarse join
axiom → grounding ADRs → everything those ADRs claim; it says
the axiom's decisions are tested, not that this module tests
this axiom. Precision migrates left as `Proves:` lines are
added; SPEC.md's own `Binding:` citations stay the per-axiom
source of truth (checked to resolve by
tests/test_docs_consistency.py).

| Axiom | ADRs | Direct proof | Inferred via ADR claims |
|---|---|---|---|
| spec:A1 | 0016 | — | `tests/parser/test_identity.py`, `tests/test_dictionary.py` |
| spec:A2 | 0015 | — | `tests/adapters/test_fabric_pbi.py`, `tests/test_schemas.py`, `tests/test_table_contracts.py` |
| spec:A3 | 0016 | — | `tests/parser/test_identity.py`, `tests/test_dictionary.py` |
| spec:B1 | 0005, 0044, 0048 | — | `tests/governance/test_display_names.py`, `tests/graph/test_decision_wiring.py`, `tests/test_admin_graph.py`, `tests/test_agent_backend.py`, `tests/test_companion.py`, `tests/test_graph_agent_harness.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_tree_contract.py`, `tests/test_zones.py`, `tests/tree/test_extract.py` |
| spec:B2 | 0044, 0074 | — | `tests/graph/test_decision_wiring.py`, `tests/test_desc_0074.py`, `tests/test_gate_recut.py`, `tests/test_skeleton_composer.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:C1 | 0001, 0048, 0052, 0053, 0054 | — | `tests/golden/test_parse_goldens.py`, `tests/governance/test_red_flags.py`, `tests/graph/test_builder.py`, `tests/orchestrator/test_flag_ops.py`, `tests/orchestrator/test_ops.py`, `tests/parser/test_sql_parser.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_native_parser_law.py`, `tests/test_reachability.py`, `tests/test_reachability_audit.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:C2 | 0041, 0044, 0045, 0053 | — | `tests/governance/test_leaf_grounding.py`, `tests/graph/test_builder.py`, `tests/graph/test_decision_wiring.py`, `tests/mquery/test_mquery.py`, `tests/orchestrator/test_ops.py`, `tests/test_escalation_contract.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:C3 | 0039, 0042 | — | `tests/governance/test_funnel.py`, `tests/governance/test_journey.py`, `tests/test_docs_consistency.py`, `tests/test_notebook_contract.py`, `tests/test_replan.py`, `tests/test_table_contracts.py` |
| spec:C4 | 0014, 0047 | — | `tests/governance/test_validation.py`, `tests/steps/test_steps.py`, `tests/test_axiom_crosswalk.py`, `tests/test_capability_registry.py`, `tests/test_dictionary.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:D1 | 0037 | `tests/test_question_families.py` | `tests/graph/test_traversal.py`, `tests/orchestrator/test_ops.py` |
| spec:D2 | 0018 | — | `tests/steps/test_steps.py`, `tests/test_recorded_pipeline.py` |
| spec:D3 | 0033, 0048 | — | `tests/graph/test_backend_comparison.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:E1 | 0046 | — | `tests/test_derive_relationships.py`, `tests/test_spec_gates.py` |
| spec:E2 | 0032, 0054, 0055 | — | `tests/governance/test_red_flags.py`, `tests/orchestrator/test_core.py`, `tests/orchestrator/test_flag_ops.py`, `tests/shapes/test_shapes.py`, `tests/test_grounding_evals.py` |
| spec:E3 | 0035, 0050, 0051 | `tests/test_integration_doctrine.py` | `tests/orchestrator/test_agent.py`, `tests/orchestrator/test_tools.py`, `tests/orchestrator/test_turn_engine.py`, `tests/webapp/test_app.py` |
| spec:E4 | 0044, 0046 | — | `tests/graph/test_decision_wiring.py`, `tests/test_derive_relationships.py`, `tests/test_spec_gates.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:E5 | 0044, 0046 | — | `tests/graph/test_decision_wiring.py`, `tests/test_derive_relationships.py`, `tests/test_spec_gates.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:E6 | 0036, 0044, 0051 | — | `tests/graph/test_decision_wiring.py`, `tests/orchestrator/test_caption_gate.py`, `tests/orchestrator/test_conclusion.py`, `tests/orchestrator/test_turn_engine.py`, `tests/test_methodology.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:F | 0044, 0074 | — | `tests/graph/test_decision_wiring.py`, `tests/test_desc_0074.py`, `tests/test_gate_recut.py`, `tests/test_skeleton_composer.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:G1 | 0047 | — | `tests/test_axiom_crosswalk.py`, `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:G2 | 0001, 0047 | — | `tests/golden/test_parse_goldens.py`, `tests/parser/test_sql_parser.py`, `tests/test_axiom_crosswalk.py`, `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_native_parser_law.py`, `tests/test_spec_gates.py` |
| spec:G3 | 0047 | — | `tests/test_axiom_crosswalk.py`, `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:G4 | 0075 | `tests/test_check_contract.py` | — |
| spec:G5 | 0076 | — | `tests/test_op_frontier.py`, `tests/test_skeleton_composer.py` |
| spec:H1 | 0045 | — | `tests/governance/test_leaf_grounding.py`, `tests/test_escalation_contract.py` |
| spec:H2 | 0045, 0048 | — | `tests/governance/test_leaf_grounding.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_escalation_contract.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:L1 | 0064 | `tests/test_ledger_contract.py` | — |
| spec:L2 | 0064 | `tests/test_ledger_contract.py` | — |
| spec:L3 | 0064 | `tests/test_integration_doctrine.py`, `tests/test_landing_registry.py`, `tests/test_spec_registry.py` | `tests/test_ledger_contract.py` |
| spec:P1 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:P2 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:P3 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:P4 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:P5 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:P6 | 0051 | — | `tests/orchestrator/test_turn_engine.py` |
| spec:Q1 | 0059 | — | `tests/graph/test_topology.py` |
| spec:Q2 | 0059 | — | `tests/graph/test_topology.py` |
| spec:Q3 | 0059 | — | `tests/graph/test_topology.py` |
| spec:R1 | 0060 | — | `tests/orchestrator/test_parse_plan.py` |
| spec:R2 | 0062 | — | `tests/webapp/test_app.py` |
| spec:R3 | 0060, 0062 | — | `tests/orchestrator/test_parse_plan.py`, `tests/webapp/test_app.py` |
| spec:R4 | 0062 | — | `tests/webapp/test_app.py` |
| spec:R5 | 0062 | — | `tests/webapp/test_app.py` |
| spec:R6 | 0061 | — | `tests/test_run_layer.py` |
| spec:R7 | 0061 | — | `tests/test_run_layer.py` |
| spec:R8 | 0061 | — | `tests/test_run_layer.py` |
| spec:T0 | 0065 | — | `tests/test_tree_contract.py` |
| spec:T1 | 0065, 0074 | — | `tests/test_desc_0074.py`, `tests/test_gate_recut.py`, `tests/test_skeleton_composer.py`, `tests/test_tree_contract.py` |
| spec:T2 | 0065 | — | `tests/test_tree_contract.py` |
| spec:T3 | 0065 | — | `tests/test_tree_contract.py` |
| spec:W1 | — | — | **(no recorded proof)** |
| spec:W2 | — | — | **(no recorded proof)** |
| spec:W3 | — | — | **(no recorded proof)** |
| spec:W4 | — | — | **(no recorded proof)** |
| spec:W5 | — | — | **(no recorded proof)** |
