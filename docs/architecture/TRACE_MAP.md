# Trace Map — decision → axioms → code → tests (generated)

Generated from `src/trace_registry.py` (ADR 0048).
Regenerate: `python scripts/generate_docs.py`. Closure checks:
`tests/test_trace_registry.py` (totality / existence / single
classification).

## ADR 0001 — Native parsers per SQL dialect

- **Category:** architecture
- **Grounds:** spec:C1, spec:G2
- **Implemented by:**
  - `src/parser/scriptdom_loader.py`
  - `src/parser/scriptdom_fabric.py`
  - `src/parser/sql_parser.py`
  - `src/tree/extract.py`
- **Enforced by:**
  - `tests/test_native_parser_law.py`
  - `tests/parser/test_sql_parser.py`
  - `tests/golden/test_parse_goldens.py`
- **Summarized in:**
  - `docs/architecture/ARCHITECTURE.md`
  - `docs/architecture/SPEC.md`

## ADR 0002 — Delta tables over an external graph database

- **Category:** architecture
- **Implemented by:**
  - `src/graph/backend.py`
  - `src/graph/delta_backend.py`
  - `src/graph/serialization.py`
  - `src/models.py`
  - `src/pipeline.py`
- **Enforced by:**
  - `tests/graph/test_serialization.py`
  - `tests/graph/test_builder.py`
  - `tests/test_pipeline.py`
- **Summarized in:**
  - `docs/architecture/ARCHITECTURE.md`

## ADR 0003 — Store sql_fragments, not full SQL blobs

- **Category:** architecture
- **Implemented by:**
  - `src/graph/builder.py`
  - `src/orchestrator/assemble.py`
- **Enforced by:**
  - `tests/graph/test_serialization.py`
  - `tests/graph/test_builder.py`
- **Summarized in:**
  - `docs/architecture/REFERENCE_ARCHITECTURE.md`

## ADR 0004 — Two-stage human-in-the-loop certification

- **Category:** architecture
- **Implemented by:**
  - `src/governance/steward.py`
- **Enforced by:**
  - `tests/governance/test_steward.py`
- **Summarized in:**
  - `docs/architecture/ARCHITECTURE.md`

## ADR 0005 — Agent refuses when no certified path exists

- **Category:** architecture
- **Grounds:** spec:B1
- **Implemented by:**
  - `src/agent_backend.py`
  - `src/graph/consumption.py`
  - `src/governance/display_names.py`
- **Enforced by:**
  - `tests/test_agent_backend.py`
  - `tests/test_graph_agent_harness.py`
  - `tests/governance/test_display_names.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0006 — Knowledge graph answers questions; Purview discovers reports

- **Category:** architecture
- **Implemented by:**
  - `src/adapters/purview.py`
- **Enforced by:**
  - `tests/adapters/test_adapters.py`
- **Summarized in:**
  - `docs/architecture/INTEGRATION_MAP.md`

## ADR 0007 — BYOT deployment as a Python library (.whl)

- **Category:** architecture
- **Implemented by:**
  - `src/config.py`
  - `src/engine_floor.py`
  - `src/branding.py`
- **Enforced by:**
  - `tests/test_build_deployment_package.py`
  - `tests/test_validate_deployment.py`
  - `tests/test_release_consistency.py`
  - `tests/test_engine_floor.py`
- **Summarized in:**
  - `docs/deployment/INSTALLATION_GUIDE.md`

## ADR 0008 — Ship Tier 1 (core agent) first

- **Category:** product
- **Summarized in:**
  - `docs/product/MARKETPLACE_LISTING.md`

## ADR 0009 — Catalog integrations are optional adapters

- **Category:** architecture
- **Implemented by:**
  - `src/adapters/base.py`
  - `src/adapters/publisher.py`
  - `src/adapters/collibra.py`
  - `src/adapters/collibra_lineage.py`
  - `src/adapters/metadata_generator.py`
  - `src/integration_registry.py`
  - `src/governance/publish_log.py`
- **Enforced by:**
  - `tests/adapters/test_adapters.py`
  - `tests/adapters/test_collibra.py`
  - `tests/governance/test_publish_log.py`
  - `tests/test_docs_consistency.py`
- **Summarized in:**
  - `docs/architecture/INTEGRATION_MAP.md`
  - `docs/architecture/SOURCE_CONNECTORS.md`

## ADR 0010 — Skip Founders Hub Level 3, go direct to Partner Center

- **Category:** product

## ADR 0011 — Static install guide for v1; companion trigger now 'admin graph projected' (amended, ADR 0048)

- **Category:** product
- **Summarized in:**
  - `docs/deployment/INSTALLATION_GUIDE.md`

## ADR 0012 — Build on the existing repo, no rewrite

- **Category:** product
- **Summarized in:**
  - `docs/architecture/ARCHITECTURE.md`

## ADR 0013 — List as transactable SaaS on the commercial marketplace

- **Category:** product
- **Implemented by:**
  - `src/marketplace/fulfillment.py`
- **Enforced by:**
  - `tests/marketplace/test_fulfillment.py`
  - `tests/marketplace/test_host.py`
- **Summarized in:**
  - `docs/product/MARKETPLACE_LISTING.md`
  - `docs/legal/terms-of-service.md`

## ADR 0014 — Ground the agent in metric_logic; dictionary is mandatory

- **Category:** architecture
- **Grounds:** spec:C4
- **Implemented by:**
  - `src/graph/metric_logic.py`
  - `src/steps/metric_logic.py`
  - `src/dictionary.py`
  - `src/steps/readiness.py`
  - `src/governance/validation.py`
- **Enforced by:**
  - `tests/test_dictionary.py`
  - `tests/governance/test_validation.py`
  - `tests/steps/test_steps.py`
- **Summarized in:**
  - `docs/deployment/DATA_DICTIONARY_REQUIREMENTS.md`

## ADR 0015 — metric_id is the universal identity

- **Category:** architecture
- **Grounds:** spec:A2
- **Implemented by:**
  - `src/schemas.py`
  - `src/adapters/fabric_pbi.py`
- **Enforced by:**
  - `tests/test_schemas.py`
  - `tests/adapters/test_fabric_pbi.py`
  - `tests/test_table_contracts.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0016 — Case-insensitive identifier matching, folded uppercase

- **Category:** architecture
- **Grounds:** spec:A1, spec:A3
- **Implemented by:**
  - `src/parser/identity.py`
- **Enforced by:**
  - `tests/parser/test_identity.py`
  - `tests/test_dictionary.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0017 — Resolve-then-traverse agent retrieval

- **Category:** architecture
- **Implemented by:**
  - `src/graph/templates.py`
  - `src/adapters/fabric_agent.py`
- **Enforced by:**
  - `tests/test_graph_templates.py`
  - `tests/adapters/test_fabric_agent.py`
- **Summarized in:**
  - `docs/architecture/QUESTION_MAP.md`

## ADR 0018 — Materialized closure edges (USES_TABLE)

- **Category:** architecture
- **Grounds:** spec:D2
- **Implemented by:**
  - `src/graph/export.py`
  - `src/steps/export.py`
- **Enforced by:**
  - `tests/test_recorded_pipeline.py`
  - `tests/steps/test_steps.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0019 — CTE descriptions bottom-up, before metric descriptions

- **Category:** architecture
- **Implemented by:**
  - `src/descriptions.py`
  - `src/llm_client.py`
  - `src/steps/agent_descriptions.py`
- **Enforced by:**
  - `tests/test_descriptions.py`
  - `tests/test_llm_client.py`
  - `tests/steps/test_agent_descriptions.py`
- **Summarized in:**
  - `docs/development/ANONYMIZATION_STRATEGY.md`

## ADR 0020 — Generator-compatibility LPG export shape

- **Category:** architecture
- **Implemented by:**
  - `src/adapters/collibra_lineage_match.py`
- **Enforced by:**
  - `tests/adapters/test_lineage_match.py`
- **Summarized in:**
  - `docs/architecture/REFERENCE_ARCHITECTURE.md`

## ADR 0021 — Certification discloses, never gates

- **Category:** architecture
- **Enforced by:**
  - `tests/test_schemas.py`
- **Summarized in:**
  - `docs/architecture/REFERENCE_ARCHITECTURE.md`

## ADR 0022 — Definition versioning: certification pins a content hash

- **Category:** architecture
- **Enforced by:**
  - `tests/test_schemas.py`
- **Summarized in:**
  - `docs/architecture/SOURCE_CONNECTORS.md`

## ADR 0023 — Usage-weighted governance flywheel

- **Category:** architecture
- **Implemented by:**
  - `src/orchestrator/events.py`
- **Enforced by:**
  - `tests/orchestrator/test_events.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0024 — Layered truth: personal beside enterprise definitions

- **Category:** architecture
- **Enforced by:**
  - `tests/test_schemas.py`
  - `tests/test_table_contracts.py`

## ADR 0025 — PHI scanning at ingestion; the LLM boundary is the gate

- **Category:** architecture
- **Implemented by:**
  - `src/phi_scan.py`
  - `src/steps/parse.py`
  - `src/anonymization.py`
- **Enforced by:**
  - `tests/test_phi_scan.py`
  - `tests/test_anonymization.py`
  - `tests/test_term_hygiene.py`
- **Summarized in:**
  - `docs/development/ANONYMIZATION_STRATEGY.md`
  - `docs/product/SECURITY_WHITEPAPER.md`

## ADR 0026 — Error-to-data lineage

- **Category:** architecture
- **Implemented by:**
  - `src/governance/error_log.py`
  - `src/governance/installation_errors.py`
  - `src/parser/error_classifier.py`
  - `src/invariants.py`
- **Enforced by:**
  - `tests/governance/test_error_log.py`
  - `tests/governance/test_installation_errors.py`
  - `tests/test_invariants.py`
  - `tests/parser/test_error_classifier.py`

## ADR 0027 — Ownership attribution: manual floor, Entra ID enriches

- **Category:** architecture
- **Enforced by:**
  - `tests/governance/test_steward.py`
- **Summarized in:**
  - `docs/development/OWNERSHIP_ATTRIBUTION.md`

## ADR 0028 — Contact-me first; transactable at first-buyer signal

- **Category:** product
- **Summarized in:**
  - `docs/product/MARKETPLACE_LISTING.md`

## ADR 0029 — Dimension layer activation (design pass, unimplemented)

- **Category:** architecture
- **Summarized in:**
  - `docs/architecture/REFERENCE_ARCHITECTURE.md`

## ADR 0030 — Layered retrieval: search terms first, vectors where allowed

- **Category:** architecture
- **Implemented by:**
  - `src/steps/search_index.py`
  - `src/orchestrator/kusto.py`
- **Enforced by:**
  - `tests/steps/test_search_index.py`
- **Summarized in:**
  - `docs/development/FABRIC_RETRIEVAL_CAPABILITIES.md`

## ADR 0031 — Business terms: weighted plurality

- **Category:** architecture
- **Implemented by:**
  - `src/governance/business_terms.py`
- **Enforced by:**
  - `tests/governance/test_business_terms.py`

## ADR 0032 — Deterministic core, LLM edges

- **Category:** architecture
- **Grounds:** spec:E2
- **Implemented by:**
  - `src/orchestrator/core.py`
  - `src/orchestrator/assemble.py`
- **Enforced by:**
  - `tests/orchestrator/test_core.py`
  - `tests/test_grounding_evals.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0033 — System of record + projections: Delta is the record

- **Category:** architecture
- **Grounds:** spec:D3
- **Implemented by:**
  - `src/graph/fabric_graph_backend.py`
  - `src/graph/gql_client.py`
- **Enforced by:**
  - `tests/graph/test_backend_comparison.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0034 — Conversational entry edge (superseded in part by 0035)

- **Category:** architecture

## ADR 0035 — Agentic conversation over deterministic tools

- **Category:** architecture
- **Grounds:** spec:E3
- **Implemented by:**
  - `src/orchestrator/agent.py`
  - `src/orchestrator/tools.py`
  - `src/orchestrator/cli.py`
  - `src/webapp/app.py`
  - `src/webapp/main.py`
- **Enforced by:**
  - `tests/orchestrator/test_agent.py`
  - `tests/orchestrator/test_tools.py`
  - `tests/webapp/test_app.py`
- **Summarized in:**
  - `docs/architecture/REFERENCE_ARCHITECTURE.md`

## ADR 0036 — Operations are the product: plan, confirm, execute, display

- **Category:** product
- **Grounds:** spec:E6
- **Implemented by:**
  - `src/methodology.py`
  - `src/orchestrator/caption_gate.py`
- **Enforced by:**
  - `tests/test_methodology.py`
  - `tests/orchestrator/test_caption_gate.py`
- **Summarized in:**
  - `docs/METHODOLOGY.md`

## ADR 0037 — The completed algebra: traverse + result-set kernels

- **Category:** architecture
- **Grounds:** spec:D1
- **Implemented by:**
  - `src/graph/traversal.py`
  - `src/orchestrator/ops.py`
- **Enforced by:**
  - `tests/graph/test_traversal.py`
  - `tests/orchestrator/test_ops.py`
- **Summarized in:**
  - `docs/architecture/QUESTION_MAP.md`
  - `docs/METHODOLOGY.md`

## ADR 0038 — The interaction layer: 'no' is input

- **Category:** product
- **Implemented by:**
  - `src/steps/agent_events.py`
- **Enforced by:**
  - `tests/steps/test_agent_events.py`
  - `tests/orchestrator/test_events.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0039 — Every error links to its contract

- **Category:** architecture
- **Grounds:** spec:C3
- **Implemented by:**
  - `src/steps/gates.py`
  - `src/governance/funnel.py`
  - `src/governance/journey.py`
- **Enforced by:**
  - `tests/governance/test_funnel.py`
  - `tests/governance/test_journey.py`
  - `tests/test_table_contracts.py`
- **Summarized in:**
  - `docs/deployment/INSTALLATION_GUIDE.md`

## ADR 0040 — The consumption layer: reports and measures

- **Category:** architecture
- **Implemented by:**
  - `src/graph/consumption.py`
  - `src/steps/semantic_models.py`
  - `src/steps/semantic_catalog.py`
  - `src/extractor/devops_tmdl.py`
  - `src/extractor/tmdl_source.py`
- **Enforced by:**
  - `tests/steps/test_semantic_models.py`
  - `tests/steps/test_semantic_catalog.py`
  - `tests/adapters/test_devops_tmdl.py`
  - `tests/extractor/test_workspace_tmdl_source.py`
- **Summarized in:**
  - `docs/architecture/INTEGRATION_MAP.md`

## ADR 0041 — M mini-parser, shape registry, fallout capture

- **Category:** architecture
- **Grounds:** spec:C2
- **Implemented by:**
  - `src/mquery/parser.py`
  - `src/mquery/signature.py`
  - `src/mquery/registry.py`
  - `src/mquery/census.py`
- **Enforced by:**
  - `tests/mquery/test_mquery.py`
- **Summarized in:**
  - `docs/architecture/SOURCE_CONNECTORS.md`

## ADR 0042 — The notebook contract: a harness for the driver layer

- **Category:** architecture
- **Grounds:** spec:C3
- **Implemented by:**
  - `src/notebook_registry.py`
  - `src/replan.py`
- **Enforced by:**
  - `tests/test_notebook_contract.py`
  - `tests/test_replan.py`
  - `tests/test_docs_consistency.py`
- **Summarized in:**
  - `docs/architecture/NOTEBOOK_MAP.md`

## ADR 0043 — The diff kernel: the founding question's shape

- **Category:** architecture
- **Implemented by:**
  - `src/graph/decomposition_diff.py`
- **Enforced by:**
  - `tests/graph/test_decomposition_diff.py`
  - `tests/orchestrator/test_ops.py`
- **Summarized in:**
  - `docs/architecture/QUESTION_MAP.md`

## ADR 0044 — The tree contract: round-trip verified descriptions

- **Category:** architecture
- **Grounds:** spec:B1, spec:B2, spec:C2, spec:E4, spec:E5, spec:E6, spec:F
- **Implemented by:**
  - `src/tree/extract.py`
  - `src/tree/translate.py`
  - `src/tree/verify.py`
  - `src/tree/diff.py`
  - `src/tree/render.py`
  - `src/tree/pipeline.py`
  - `src/steps/build_graph.py`
- **Enforced by:**
  - `tests/test_tree_contract.py`
  - `tests/tree/test_extract.py`
  - `tests/graph/test_decision_wiring.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0045 — The escalation contract: no silent residue

- **Category:** architecture
- **Grounds:** spec:C2, spec:H1, spec:H2
- **Implemented by:**
  - `src/governance/leaf_grounding.py`
- **Enforced by:**
  - `tests/test_escalation_contract.py`
  - `tests/governance/test_leaf_grounding.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0046 — Anchor, discover, match, rank — the human picks

- **Category:** architecture
- **Grounds:** spec:E1, spec:E4, spec:E5
- **Implemented by:**
  - `src/discovery/paths.py`
  - `src/discovery/grounding.py`
- **Enforced by:**
  - `tests/test_spec_gates.py`
  - `tests/test_derive_relationships.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0047 — The shadow specification (the axiom system)

- **Category:** architecture
- **Grounds:** spec:C4, spec:G1, spec:G3, spec:G2
- **Implemented by:**
  - `src/extraction_registry.py`
  - `src/capability_registry.py`
- **Enforced by:**
  - `tests/test_extraction_registry.py`
  - `tests/test_capability_registry.py`
  - `tests/test_spec_gates.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0048 — Declared zones, trace registry, admin graph, companion

- **Category:** architecture
- **Grounds:** spec:B1, spec:C1, spec:D3, spec:H2
- **Implemented by:**
  - `src/zones.py`
  - `src/trace_registry.py`
  - `src/admin_graph.py`
  - `src/companion.py`
- **Enforced by:**
  - `tests/test_zones.py`
  - `tests/test_trace_registry.py`
  - `tests/test_term_hygiene.py`
  - `tests/test_admin_graph.py`
  - `tests/test_companion.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`
  - `docs/architecture/TRACE_MAP.md`

## ADR 0049 — Ingestion routes: filedrop, folders, live extractor

- **Category:** architecture
- **Implemented by:**
  - `src/extractor/connection.py`
  - `src/extractor/discovery.py`
  - `src/extractor/extractor.py`
  - `src/extractor/tracker.py`
- **Enforced by:**
  - `tests/extractor/test_connection.py`
  - `tests/extractor/test_extractor.py`
  - `tests/extractor/test_proc_parity.py`
- **Summarized in:**
  - `docs/architecture/SOURCE_CONNECTORS.md`

## ADR 0050 — Bounded read-only answer loop: plan to the answer, caption answers, auto-continue (amends 0036)

- **Category:** architecture
- **Grounds:** spec:E3
- **Implemented by:**
  - `src/orchestrator/turn_engine.py`
- **Enforced by:**
  - `tests/orchestrator/test_turn_engine.py`

## ADR 0051 — The one-mind turn: one conversation decides, the boundary enforces (supersedes 0036/0050's shape)

- **Category:** architecture
- **Grounds:** spec:E3, spec:E6
- **Implemented by:**
  - `src/orchestrator/turn_engine.py`
- **Enforced by:**
  - `tests/orchestrator/test_turn_engine.py`
- **Summarized in:**
  - `docs/architecture/SPEC.md`

## ADR 0052 — The reachability contract: every graph payload reachable by a named op or excluded with a reason

- **Category:** architecture
- **Grounds:** spec:C1
- **Implemented by:**
  - `src/reachability.py`
  - `devtools/reachability_audit.py`
- **Enforced by:**
  - `tests/test_reachability.py`
  - `tests/test_reachability_audit.py`
- **Summarized in:**
  - `docs/decisions/0052-reachability-contract.md`
  - `docs/architecture/SPEC.md`

## ADR 0053 — Projection-grain column lineage: transform_to_column edges, resolved-only, conservation-counted

- **Category:** architecture
- **Grounds:** spec:C1, spec:C2
- **Implemented by:**
  - `src/graph/builder.py`
  - `src/steps/build_graph.py`
- **Enforced by:**
  - `tests/graph/test_builder.py`
  - `tests/orchestrator/test_ops.py`
- **Summarized in:**
  - `docs/decisions/0053-projection-column-lineage.md`

## ADR 0054 — Governance red flags and governed plurality: misnomer/duplicate/cousin sweep over content hashes

- **Category:** architecture
- **Grounds:** spec:C1, spec:E2
- **Implemented by:**
  - `src/governance/red_flags.py`
  - `src/steps/red_flag_sweep.py`
- **Enforced by:**
  - `tests/governance/test_red_flags.py`
  - `tests/orchestrator/test_flag_ops.py`
- **Summarized in:**
  - `docs/decisions/0054-governance-red-flags-governed-plurality.md`

## ADR 0055 — The designed shape corpus: spec-derived test data (category-partition over name x logic x scope)

- **Category:** architecture
- **Grounds:** spec:E2
- **Implemented by:**
  - `src/shapes/generator.py`
  - `src/shapes/matrix.py`
  - `src/shapes/checker.py`
- **Enforced by:**
  - `tests/shapes/test_shapes.py`
- **Summarized in:**
  - `docs/decisions/0055-designed-shape-corpus.md`

## ADR 0056 — The decision algebra: every answer ends in a decision (typed deny, usage weights)

- **Category:** architecture
- **Summarized in:**
  - `docs/decisions/0056-decision-algebra.md`

## ADR 0057 — The Sphere: architecture model, ownership economy, contracts split

- **Category:** architecture
- **Summarized in:**
  - `docs/decisions/0057-the-sphere.md`
  - `docs/architecture/SPHERE.md`

## ADR 0058 — The self-service contracts: contracts-first for the Pro pillar (provenance rungs, execution floors)

- **Category:** architecture
- **Summarized in:**
  - `docs/decisions/0058-self-service-contracts.md`

## ADR 0059 — The graph topology axioms: connected, sound, complete (measured, then formalized)

- **Category:** architecture
- **Grounds:** spec:Q1, spec:Q2, spec:Q3
- **Implemented by:**
  - `src/graph/topology.py`
- **Enforced by:**
  - `tests/graph/test_topology.py`
- **Summarized in:**
  - `docs/decisions/0059-graph-topology-axioms.md`
  - `docs/architecture/SPEC.md`
