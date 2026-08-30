<!-- GENERATED FILE — do not edit.
     Sources: src/trace_registry.py claims + docstring
     Proves: lines (devtools/suite_map.py grammar).
     Regenerate: python scripts/generate_docs.py
     CI fails if stale or if any module proves nothing
     on record (tests/test_suite_map.py). -->

# Test Map — what every test proves

118 modules, 1319 tests, every module accounted: claimed by an ADR in the trace registry or declaring a law/contract in its docstring (`Proves:` line).

## By ADR

| ADR | Title | Test modules |
|---|---|---|
| 0001 | Native parsers per SQL dialect | `tests/golden/test_parse_goldens.py` (3), `tests/parser/test_sql_parser.py` (10), `tests/test_native_parser_law.py` (3) |
| 0002 | Delta tables over an external graph database | `tests/graph/test_builder.py` (16), `tests/graph/test_serialization.py` (8), `tests/test_pipeline.py` (7) |
| 0003 | Store sql_fragments, not full SQL blobs | `tests/graph/test_builder.py` (16), `tests/graph/test_serialization.py` (8) |
| 0004 | Two-stage human-in-the-loop certification | `tests/governance/test_steward.py` (5) |
| 0005 | Agent refuses when no certified path exists | `tests/governance/test_display_names.py` (7), `tests/test_agent_backend.py` (7), `tests/test_graph_agent_harness.py` (6) |
| 0006 | Knowledge graph answers questions; Purview discovers reports | `tests/adapters/test_adapters.py` (10) |
| 0007 | BYOT deployment as a Python library (.whl) | `tests/test_build_deployment_package.py` (8), `tests/test_engine_floor.py` (4), `tests/test_release_consistency.py` (4), `tests/test_secrets_vault.py` (6), `tests/test_validate_deployment.py` (14) |
| 0009 | Catalog integrations are optional adapters | `tests/adapters/test_adapters.py` (10), `tests/adapters/test_collibra.py` (10), `tests/governance/test_publish_log.py` (3), `tests/test_docs_consistency.py` (10) |
| 0013 | List as transactable SaaS on the commercial marketplace | `tests/marketplace/test_fulfillment.py` (16), `tests/marketplace/test_host.py` (13) |
| 0014 | Ground the agent in metric_logic; dictionary is mandatory | `tests/governance/test_validation.py` (6), `tests/steps/test_steps.py` (41), `tests/test_dictionary.py` (8) |
| 0015 | metric_id is the universal identity | `tests/adapters/test_fabric_pbi.py` (5), `tests/test_schemas.py` (8), `tests/test_table_contracts.py` (10) |
| 0016 | Case-insensitive identifier matching, folded uppercase | `tests/parser/test_identity.py` (12), `tests/test_dictionary.py` (8) |
| 0017 | Resolve-then-traverse agent retrieval | `tests/adapters/test_fabric_agent.py` (4), `tests/test_graph_templates.py` (13) |
| 0018 | Materialized closure edges (USES_TABLE) | `tests/steps/test_steps.py` (41), `tests/test_recorded_pipeline.py` (3) |
| 0019 | CTE descriptions bottom-up, before metric descriptions | `tests/steps/test_agent_descriptions.py` (15), `tests/test_descriptions.py` (23), `tests/test_llm_client.py` (14) |
| 0020 | Generator-compatibility LPG export shape | `tests/adapters/test_lineage_match.py` (26) |
| 0021 | Certification discloses, never gates | `tests/test_schemas.py` (8) |
| 0022 | Definition versioning: certification pins a content hash | `tests/test_schemas.py` (8) |
| 0023 | Usage-weighted governance flywheel | `tests/orchestrator/test_events.py` (7) |
| 0024 | Layered truth: personal beside enterprise definitions | `tests/test_schemas.py` (8), `tests/test_table_contracts.py` (10) |
| 0025 | PHI scanning at ingestion; the LLM boundary is the gate | `tests/test_anonymization.py` (8), `tests/test_phi_scan.py` (25), `tests/test_term_hygiene.py` (2) |
| 0026 | Error-to-data lineage | `tests/governance/test_error_log.py` (8), `tests/governance/test_installation_errors.py` (2), `tests/parser/test_error_classifier.py` (6), `tests/test_invariants.py` (11) |
| 0027 | Ownership attribution: manual floor, Entra ID enriches | `tests/governance/test_steward.py` (5) |
| 0030 | Layered retrieval: search terms first, vectors where allowed | `tests/steps/test_search_index.py` (6) |
| 0031 | Business terms: weighted plurality | `tests/governance/test_business_terms.py` (6) |
| 0032 | Deterministic core, LLM edges | `tests/orchestrator/test_core.py` (10), `tests/test_grounding_evals.py` (6) |
| 0033 | System of record + projections: Delta is the record | `tests/graph/test_backend_comparison.py` (11) |
| 0035 | Agentic conversation over deterministic tools | `tests/orchestrator/test_agent.py` (6), `tests/orchestrator/test_tools.py` (21), `tests/webapp/test_app.py` (74) |
| 0036 | Operations are the product: plan, confirm, execute, display | `tests/orchestrator/test_caption_gate.py` (33), `tests/orchestrator/test_conclusion.py` (23), `tests/test_methodology.py` (8) |
| 0037 | The completed algebra: traverse + result-set kernels | `tests/graph/test_traversal.py` (2), `tests/orchestrator/test_ops.py` (78) |
| 0038 | The interaction layer: 'no' is input | `tests/orchestrator/test_events.py` (7), `tests/steps/test_agent_events.py` (5) |
| 0039 | Every error links to its contract | `tests/governance/test_funnel.py` (8), `tests/governance/test_journey.py` (7), `tests/test_table_contracts.py` (10) |
| 0040 | The consumption layer: reports and measures | `tests/adapters/test_devops_tmdl.py` (26), `tests/extractor/test_workspace_tmdl_source.py` (9), `tests/orchestrator/test_report_links.py` (6), `tests/steps/test_semantic_catalog.py` (9), `tests/steps/test_semantic_models.py` (23) |
| 0041 | M mini-parser, shape registry, fallout capture | `tests/mquery/test_mquery.py` (16) |
| 0042 | The notebook contract: a harness for the driver layer | `tests/test_docs_consistency.py` (10), `tests/test_notebook_contract.py` (12), `tests/test_replan.py` (9) |
| 0043 | The diff kernel: the founding question's shape | `tests/graph/test_decomposition_diff.py` (11), `tests/orchestrator/test_ops.py` (78) |
| 0044 | The tree contract: round-trip verified descriptions | `tests/graph/test_decision_wiring.py` (8), `tests/test_tree_contract.py` (13), `tests/tree/test_extract.py` (18) |
| 0045 | The escalation contract: no silent residue | `tests/governance/test_leaf_grounding.py` (6), `tests/test_escalation_contract.py` (8) |
| 0046 | Anchor, discover, match, rank — the human picks | `tests/test_derive_relationships.py` (7), `tests/test_spec_gates.py` (4) |
| 0047 | The shadow specification (the axiom system) | `tests/test_capability_registry.py` (4), `tests/test_extraction_registry.py` (6), `tests/test_spec_gates.py` (4) |
| 0048 | Declared zones, trace registry, admin graph, companion | `tests/test_admin_graph.py` (9), `tests/test_companion.py` (7), `tests/test_term_hygiene.py` (2), `tests/test_trace_registry.py` (7), `tests/test_zones.py` (4) |
| 0049 | Ingestion routes: filedrop, folders, live extractor | `tests/extractor/test_connection.py` (9), `tests/extractor/test_extractor.py` (15), `tests/extractor/test_proc_parity.py` (8) |
| 0050 | Bounded read-only answer loop: plan to the answer, caption answers, auto-continue (amends 0036) | `tests/orchestrator/test_turn_engine.py` (31) |
| 0051 | The one-mind turn: one conversation decides, the boundary enforces (supersedes 0036/0050's shape) | `tests/orchestrator/test_turn_engine.py` (31) |
| 0052 | The reachability contract: every graph payload reachable by a named op or excluded with a reason | `tests/test_reachability.py` (8), `tests/test_reachability_audit.py` (6) |
| 0053 | Projection-grain column lineage: transform_to_column edges, resolved-only, conservation-counted | `tests/graph/test_builder.py` (16), `tests/orchestrator/test_ops.py` (78) |
| 0054 | Governance red flags and governed plurality: misnomer/duplicate/cousin sweep over content hashes | `tests/governance/test_red_flags.py` (17), `tests/orchestrator/test_flag_ops.py` (11) |
| 0055 | The designed shape corpus: spec-derived test data (category-partition over name x logic x scope) | `tests/shapes/test_shapes.py` (18) |
| 0056 | The decision algebra: every answer ends in a decision (typed deny, usage weights) | `tests/test_flywheel.py` (7) |
| 0059 | The graph topology axioms: connected, sound, complete (measured, then formalized) | `tests/graph/test_topology.py` (14) |
| 0060 | The parse is the plan: parser-only LLM, deterministic traversal, correction flywheel | `tests/orchestrator/test_parse_plan.py` (28) |
| 0061 | The run layer: Pro runs the confirmed definition | `tests/test_run_layer.py` (25) |
| 0062 | The dialogue loop: show, propose, ask, execute | `tests/webapp/test_app.py` (74) |
| 0063 | The product tiers: X-Ray, Bridge, Workbench, Run | `tests/adapters/test_file_export.py` (9), `tests/test_console.py` (15), `tests/test_xray.py` (7) |

## By standing law

### law:live-probe — no ops/tools surface ships without the smoke harness passing against the live store (P0.4)

- `tests/orchestrator/test_engine_smoke_contract.py` (4): CI leg of the live-probe law (P0.4, Sunny's no-whack-a-mole audit

### law:walk-finds — corpses from Sunny's live walks are mechanized same-session (Echo Law)

- `tests/orchestrator/test_gapcheck_finds.py` (10): Gap-check finds (Sunny live, 2026-08-24) — L0: W15 typed compare
- `tests/orchestrator/test_sameness.py` (22): Walk W6/W7 (Sunny live, 2026-08-23): sameness honesty. The corpse:
- `tests/orchestrator/test_walk_continuation.py` (20): Walk 1562 continuation (steps 3–6, 2026-08-23) — L0 for the P0/P1
- `tests/test_console.py` (15): CONSOLE-1 (0063 §3 — the Resolution Console / the Inbox):
- `tests/test_de_typing.py` (4): TESTPLAN_0062 section A — the de-typing proof (the ruling's
- `tests/webapp/test_page_dom.py` (1): RW-19 — the page-JS gate's RUNTIME leg (TESTPLAN_0062 D).

### law:brand-separation — the product name is a seam; the core stays brand-neutral

- `tests/test_brand_neutral_core.py` (1): Brand-neutral core contract (HANDOFF_BRAND_NEUTRAL_CORE, 2026-08-17).
- `tests/test_branding.py` (5): Tests for the product-name seam (src/branding.py).

### law:endpoint-hygiene — no tenant endpoint ever lives in this repo

- `tests/test_endpoint_hygiene.py` (3): Endpoint hygiene — no tenant endpoint ever lives in this repo.

### law:honesty-floor — honesty 1.00 is a build-stopper, never a metric

- `tests/test_grounding_gate.py` (10): The grounding gate — acceptance fixtures are the REAL production

## By executable contract

### contract:toolchain — every third-party dependency is declared and pinned (Sunny's ruling, 2026-08-19)

- `tests/test_dependency_declarations.py` (1): Every third-party import must be declared in pyproject.toml.
- `tests/test_toolchain_contract.py` (2): The toolchain contract (ruled by Sunny 2026-08-19, delivered 1.30.0).

### contract:suite-integrity — answer_evals grades describe the engine or the run aborts (INFRA-SKIP contract)

- `tests/test_infra_skip.py` (6): L0 tests for the answer_evals INFRA-SKIP contract (2026-08-22 outage

### contract:suite-legibility — the suite explains itself to Sunny — the proof ledger and the run transcript (morning orders, 2026-08-27)

- `tests/adapters/test_file_export.py` (9): BRIDGE-1 stage 1 (0063 §2 file-first): native import files from
- `tests/orchestrator/test_conclusion.py` (23): The Answer Format Contract's composer (RW-10): card class is
- `tests/orchestrator/test_parse_plan.py` (28): ADR 0060 prototype L0: closure is structural, grounding is exact,
- `tests/shapes/test_seed.py` (7): The demo-source seed (shape-store tenant load, 2026-08-27):
- `tests/test_flywheel.py` (7): FLYWHEEL-1 (0056 mechanism v1, Sunny-authorized 2026-08-29):
- `tests/test_run_layer.py` (25): ADR 0061 slice 1 — the run layer's cage. THE ACCEPTANCE IS P5:
- `tests/test_secrets_vault.py` (6): KEYVAULT-1 (code-side): "keyvault:<name>" refs resolve through
- `tests/test_suite_map.py` (9): TEST_MAP totality (morning order 1, 2026-08-27): every test module
- `tests/test_suite_transcript.py` (7): Suite transcript emission (morning order 2, 2026-08-27): every
- `tests/test_xray.py` (7): X-RAY-1 (0063 §1, the wedge): the Estate X-Ray report — real

### contract:org-config — org_config referential integrity, LOCAL and TENANT copies together

- `tests/test_org_config_audit.py` (2): L0 for the org_config referential-integrity audit (ops find 2,

### contract:round4-scorecard — the Round-4 record's fact accounting and mitigation verifiers

- `tests/test_rematch_round4.py` (10): L0 tests for the Round-4 runner's fact accounting and scorecard writer.
- `tests/test_verify_lineage_mitigation.py` (6): L0 tests for the lineage-mitigation verifier's answer check

### contract:boundary-echo — every tenant-crossing devtool op pairs with an observable postcondition — an acknowledgment is a claim; only the postcondition is a fact (ordered 2026-08-27)

- `tests/test_boundary_ops.py` (6): The boundary echo contract's teeth (ordered 2026-08-27).

### contract:web-surface — the served page works AS SERVED

- `tests/webapp/test_page_js.py` (2): The served page's JS must parse AS SERVED (live find 2026-08-13:

## By spec axiom (derived: axiom → grounding ADRs → tests)

| Axiom | ADRs | Test modules |
|---|---|---|
| spec:A1 | 0016 | `tests/parser/test_identity.py`, `tests/test_dictionary.py` |
| spec:A2 | 0015 | `tests/adapters/test_fabric_pbi.py`, `tests/test_schemas.py`, `tests/test_table_contracts.py` |
| spec:A3 | 0016 | `tests/parser/test_identity.py`, `tests/test_dictionary.py` |
| spec:B1 | 0005, 0044, 0048 | `tests/governance/test_display_names.py`, `tests/graph/test_decision_wiring.py`, `tests/test_admin_graph.py`, `tests/test_agent_backend.py`, `tests/test_companion.py`, `tests/test_graph_agent_harness.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_tree_contract.py`, `tests/test_zones.py`, `tests/tree/test_extract.py` |
| spec:B2 | 0044 | `tests/graph/test_decision_wiring.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:C1 | 0001, 0048, 0052, 0053, 0054 | `tests/golden/test_parse_goldens.py`, `tests/governance/test_red_flags.py`, `tests/graph/test_builder.py`, `tests/orchestrator/test_flag_ops.py`, `tests/orchestrator/test_ops.py`, `tests/parser/test_sql_parser.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_native_parser_law.py`, `tests/test_reachability.py`, `tests/test_reachability_audit.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:C2 | 0041, 0044, 0045, 0053 | `tests/governance/test_leaf_grounding.py`, `tests/graph/test_builder.py`, `tests/graph/test_decision_wiring.py`, `tests/mquery/test_mquery.py`, `tests/orchestrator/test_ops.py`, `tests/test_escalation_contract.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:C3 | 0039, 0042 | `tests/governance/test_funnel.py`, `tests/governance/test_journey.py`, `tests/test_docs_consistency.py`, `tests/test_notebook_contract.py`, `tests/test_replan.py`, `tests/test_table_contracts.py` |
| spec:C4 | 0014, 0047 | `tests/governance/test_validation.py`, `tests/steps/test_steps.py`, `tests/test_capability_registry.py`, `tests/test_dictionary.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:D1 | 0037 | `tests/graph/test_traversal.py`, `tests/orchestrator/test_ops.py` |
| spec:D2 | 0018 | `tests/steps/test_steps.py`, `tests/test_recorded_pipeline.py` |
| spec:D3 | 0033, 0048 | `tests/graph/test_backend_comparison.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:E1 | 0046 | `tests/test_derive_relationships.py`, `tests/test_spec_gates.py` |
| spec:E2 | 0032, 0054, 0055 | `tests/governance/test_red_flags.py`, `tests/orchestrator/test_core.py`, `tests/orchestrator/test_flag_ops.py`, `tests/shapes/test_shapes.py`, `tests/test_grounding_evals.py` |
| spec:E3 | 0035, 0050, 0051 | `tests/orchestrator/test_agent.py`, `tests/orchestrator/test_tools.py`, `tests/orchestrator/test_turn_engine.py`, `tests/webapp/test_app.py` |
| spec:E4 | 0044, 0046 | `tests/graph/test_decision_wiring.py`, `tests/test_derive_relationships.py`, `tests/test_spec_gates.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:E5 | 0044, 0046 | `tests/graph/test_decision_wiring.py`, `tests/test_derive_relationships.py`, `tests/test_spec_gates.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:E6 | 0036, 0044, 0051 | `tests/graph/test_decision_wiring.py`, `tests/orchestrator/test_caption_gate.py`, `tests/orchestrator/test_conclusion.py`, `tests/orchestrator/test_turn_engine.py`, `tests/test_methodology.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:F | 0044 | `tests/graph/test_decision_wiring.py`, `tests/test_tree_contract.py`, `tests/tree/test_extract.py` |
| spec:G1 | 0047 | `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:G2 | 0001, 0047 | `tests/golden/test_parse_goldens.py`, `tests/parser/test_sql_parser.py`, `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_native_parser_law.py`, `tests/test_spec_gates.py` |
| spec:G3 | 0047 | `tests/test_capability_registry.py`, `tests/test_extraction_registry.py`, `tests/test_spec_gates.py` |
| spec:H1 | 0045 | `tests/governance/test_leaf_grounding.py`, `tests/test_escalation_contract.py` |
| spec:H2 | 0045, 0048 | `tests/governance/test_leaf_grounding.py`, `tests/test_admin_graph.py`, `tests/test_companion.py`, `tests/test_escalation_contract.py`, `tests/test_term_hygiene.py`, `tests/test_trace_registry.py`, `tests/test_zones.py` |
| spec:Q1 | 0059 | `tests/graph/test_topology.py` |
| spec:Q2 | 0059 | `tests/graph/test_topology.py` |
| spec:Q3 | 0059 | `tests/graph/test_topology.py` |
