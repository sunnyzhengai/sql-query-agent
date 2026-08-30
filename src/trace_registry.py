"""TRACE_REGISTRY — the decision lineage as data (ADR 0048, item 2).

The seventh peer registry (after tables, notebooks, shapes, extraction,
capabilities, integrations): one entry per ADR, recording what the
decision grounds (spec axioms), what implements it (src/ modules), what
enforces it (tests), and what summarizes it (docs). Category separates
architecture decisions from product/business decisions — the latter
legitimately have no code.

Three closure checks make it law (tests/test_trace_registry.py):
- totality: every src/ module is cited by ≥1 decision — the ghost rule
  mechanized; an uncited module is a finding, not a warning;
- existence: every cited path, test, doc, and axiom id exists — the
  failure class the spec audit caught by hand (a cited test that
  didn't exist);
- single classification: governed ⊎ internal covers the repo (with
  src/zones.py).

docs/architecture/TRACE_MAP.md is the generated projection
(scripts/generate_docs.py). Lineages harvested 2026-08-20 from the ADR
texts and in-file citations; evidence lives in each ADR.
"""

from __future__ import annotations

# Axiom ids defined by docs/architecture/SPEC.md (F is the round-trip
# group, stated as one equation block rather than numbered axioms).
SPEC_AXIOMS = frozenset({
    "A1", "A2", "A3", "B1", "B2", "C1", "C2", "C3", "C4",
    "D1", "D2", "D3", "E1", "E2", "E3", "E4", "E5", "E6", "F",
    "G1", "G2", "G3", "H1", "H2",
    # Group Q — graph topology (ADR 0059, ratified 2026-08-26; the
    # ADR's G1-G3, renamed on entry because spec group G was taken)
    "Q1", "Q2", "Q3",
})

CATEGORIES = ("architecture", "product")

TRACE_REGISTRY = {
    "0001": {
        "title": "Native parsers per SQL dialect",
        "category": "architecture",
        "axioms": ["C1", "G2"],
        "modules": [
            "src/parser/scriptdom_loader.py", "src/parser/scriptdom_fabric.py",
            "src/parser/sql_parser.py", "src/tree/extract.py",
        ],
        "tests": [
            "tests/test_native_parser_law.py", "tests/parser/test_sql_parser.py",
            "tests/golden/test_parse_goldens.py",
        ],
        "docs": ["docs/architecture/ARCHITECTURE.md", "docs/architecture/SPEC.md"],
    },
    "0002": {
        "title": "Delta tables over an external graph database",
        "category": "architecture",
        "axioms": [],
        "modules": [
            "src/graph/backend.py", "src/graph/delta_backend.py",
            "src/graph/serialization.py", "src/models.py", "src/pipeline.py",
        ],
        "tests": [
            "tests/graph/test_serialization.py", "tests/graph/test_builder.py",
            "tests/test_pipeline.py",
        ],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0003": {
        "title": "Store sql_fragments, not full SQL blobs",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/graph/builder.py", "src/orchestrator/assemble.py"],
        "tests": ["tests/graph/test_serialization.py", "tests/graph/test_builder.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0004": {
        "title": "Two-stage human-in-the-loop certification",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/governance/steward.py"],
        "tests": ["tests/governance/test_steward.py"],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0005": {
        "title": "Agent refuses when no certified path exists",
        "category": "architecture",
        "axioms": ["B1"],
        "modules": [
            "src/agent_backend.py", "src/graph/consumption.py",
            "src/governance/display_names.py",
        ],
        "tests": [
            "tests/test_agent_backend.py", "tests/test_graph_agent_harness.py",
            "tests/governance/test_display_names.py",
        ],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0006": {
        "title": "Knowledge graph answers questions; Purview discovers reports",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/adapters/purview.py"],
        "tests": ["tests/adapters/test_adapters.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0007": {
        "title": "BYOT deployment as a Python library (.whl)",
        "category": "architecture",
        "axioms": [],
        # secrets_vault joined 2026-08-29 (KEYVAULT-1 code-side):
        # config-load secret resolution is a deployment concern —
        # the enterprise end state the board recorded, code half
        "modules": ["src/config.py", "src/engine_floor.py", "src/branding.py",
                    "src/secrets_vault.py"],
        "tests": [
            "tests/test_build_deployment_package.py",
            "tests/test_validate_deployment.py",
            "tests/test_release_consistency.py", "tests/test_engine_floor.py",
            "tests/test_secrets_vault.py",
        ],
        "docs": ["docs/deployment/INSTALLATION_GUIDE.md"],
    },
    "0008": {
        "title": "Ship Tier 1 (core agent) first",
        "category": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/product/MARKETPLACE_LISTING.md"],
    },
    "0009": {
        "title": "Catalog integrations are optional adapters",
        "category": "architecture",
        "axioms": [],
        "modules": [
            "src/adapters/base.py", "src/adapters/publisher.py",
            "src/adapters/collibra.py", "src/adapters/collibra_lineage.py",
            "src/adapters/metadata_generator.py", "src/integration_registry.py",
            "src/governance/publish_log.py",
        ],
        "tests": [
            "tests/adapters/test_adapters.py", "tests/adapters/test_collibra.py",
            "tests/governance/test_publish_log.py",
            "tests/test_docs_consistency.py",
        ],
        "docs": ["docs/architecture/INTEGRATION_MAP.md",
                 "docs/architecture/SOURCE_CONNECTORS.md"],
    },
    "0010": {
        "title": "Skip Founders Hub Level 3, go direct to Partner Center",
        "category": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": [],
    },
    "0011": {
        "title": "Static install guide for v1; companion trigger now "
                 "'admin graph projected' (amended, ADR 0048)",
        "category": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/deployment/INSTALLATION_GUIDE.md"],
    },
    "0012": {
        "title": "Build on the existing repo, no rewrite",
        "category": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0013": {
        "title": "List as transactable SaaS on the commercial marketplace",
        "category": "product",
        "axioms": [],
        "modules": ["src/marketplace/fulfillment.py"],
        "tests": ["tests/marketplace/test_fulfillment.py",
                  "tests/marketplace/test_host.py"],
        "docs": ["docs/product/MARKETPLACE_LISTING.md",
                 "docs/legal/terms-of-service.md"],
    },
    "0014": {
        "title": "Ground the agent in metric_logic; dictionary is mandatory",
        "category": "architecture",
        "axioms": ["C4"],
        "modules": [
            "src/graph/metric_logic.py", "src/steps/metric_logic.py",
            "src/dictionary.py", "src/steps/readiness.py",
            "src/governance/validation.py",
        ],
        "tests": [
            "tests/test_dictionary.py", "tests/governance/test_validation.py",
            "tests/steps/test_steps.py",
        ],
        "docs": ["docs/deployment/DATA_DICTIONARY_REQUIREMENTS.md"],
    },
    "0015": {
        "title": "metric_id is the universal identity",
        "category": "architecture",
        "axioms": ["A2"],
        "modules": ["src/schemas.py", "src/adapters/fabric_pbi.py"],
        "tests": ["tests/test_schemas.py", "tests/adapters/test_fabric_pbi.py",
                  "tests/test_table_contracts.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0016": {
        "title": "Case-insensitive identifier matching, folded uppercase",
        "category": "architecture",
        "axioms": ["A1", "A3"],
        "modules": ["src/parser/identity.py"],
        "tests": ["tests/parser/test_identity.py", "tests/test_dictionary.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0017": {
        "title": "Resolve-then-traverse agent retrieval",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/graph/templates.py", "src/adapters/fabric_agent.py"],
        "tests": ["tests/test_graph_templates.py",
                  "tests/adapters/test_fabric_agent.py"],
        "docs": ["docs/architecture/QUESTION_MAP.md"],
    },
    "0018": {
        "title": "Materialized closure edges (USES_TABLE)",
        "category": "architecture",
        "axioms": ["D2"],
        "modules": ["src/graph/export.py", "src/steps/export.py"],
        "tests": ["tests/test_recorded_pipeline.py", "tests/steps/test_steps.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0019": {
        "title": "CTE descriptions bottom-up, before metric descriptions",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/descriptions.py", "src/llm_client.py",
                    "src/steps/agent_descriptions.py"],
        "tests": ["tests/test_descriptions.py", "tests/test_llm_client.py",
                  "tests/steps/test_agent_descriptions.py"],
        "docs": ["docs/development/ANONYMIZATION_STRATEGY.md"],
    },
    "0020": {
        "title": "Generator-compatibility LPG export shape",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/adapters/collibra_lineage_match.py"],
        "tests": ["tests/adapters/test_lineage_match.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0021": {
        "title": "Certification discloses, never gates",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0022": {
        "title": "Definition versioning: certification pins a content hash",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py"],
        "docs": ["docs/architecture/SOURCE_CONNECTORS.md"],
    },
    "0023": {
        "title": "Usage-weighted governance flywheel",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/orchestrator/events.py"],
        "tests": ["tests/orchestrator/test_events.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0024": {
        "title": "Layered truth: personal beside enterprise definitions",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py", "tests/test_table_contracts.py"],
        "docs": [],
    },
    "0025": {
        "title": "PHI scanning at ingestion; the LLM boundary is the gate",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/phi_scan.py", "src/steps/parse.py",
                    "src/anonymization.py"],
        "tests": ["tests/test_phi_scan.py", "tests/test_anonymization.py",
                  "tests/test_term_hygiene.py"],
        "docs": ["docs/development/ANONYMIZATION_STRATEGY.md",
                 "docs/product/SECURITY_WHITEPAPER.md"],
    },
    "0026": {
        "title": "Error-to-data lineage",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/governance/error_log.py",
                    "src/governance/installation_errors.py",
                    "src/parser/error_classifier.py", "src/invariants.py"],
        "tests": ["tests/governance/test_error_log.py",
                  "tests/governance/test_installation_errors.py",
                  "tests/test_invariants.py",
                  "tests/parser/test_error_classifier.py"],
        "docs": [],
    },
    "0027": {
        "title": "Ownership attribution: manual floor, Entra ID enriches",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/governance/test_steward.py"],
        "docs": ["docs/development/OWNERSHIP_ATTRIBUTION.md"],
    },
    "0028": {
        "title": "Contact-me first; transactable at first-buyer signal",
        "category": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/product/MARKETPLACE_LISTING.md"],
    },
    "0029": {
        "title": "Dimension layer activation (design pass, unimplemented)",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0030": {
        "title": "Layered retrieval: search terms first, vectors where allowed",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/steps/search_index.py", "src/orchestrator/kusto.py"],
        "tests": ["tests/steps/test_search_index.py"],
        "docs": ["docs/development/FABRIC_RETRIEVAL_CAPABILITIES.md"],
    },
    "0031": {
        "title": "Business terms: weighted plurality",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/governance/business_terms.py"],
        "tests": ["tests/governance/test_business_terms.py"],
        "docs": [],
    },
    "0032": {
        "title": "Deterministic core, LLM edges",
        "category": "architecture",
        "axioms": ["E2"],
        "modules": ["src/orchestrator/core.py", "src/orchestrator/assemble.py"],
        "tests": ["tests/orchestrator/test_core.py", "tests/test_grounding_evals.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0033": {
        "title": "System of record + projections: Delta is the record",
        "category": "architecture",
        "axioms": ["D3"],
        "modules": ["src/graph/fabric_graph_backend.py", "src/graph/gql_client.py"],
        "tests": ["tests/graph/test_backend_comparison.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0034": {
        "title": "Conversational entry edge (superseded in part by 0035)",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": [],
    },
    "0035": {
        "title": "Agentic conversation over deterministic tools",
        "category": "architecture",
        "axioms": ["E3"],
        "modules": ["src/orchestrator/agent.py", "src/orchestrator/tools.py",
                    "src/orchestrator/cli.py", "src/webapp/app.py",
                    "src/webapp/main.py"],
        "tests": ["tests/orchestrator/test_agent.py",
                  "tests/orchestrator/test_tools.py", "tests/webapp/test_app.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0036": {
        "title": "Operations are the product: plan, confirm, execute, display",
        "category": "product",
        "axioms": ["E6"],
        "modules": ["src/methodology.py",
                    "src/orchestrator/caption_gate.py",
                    # RW-10 (2026-08-28): the answer format
                    # contract — the ADR's presentation half
                    "src/orchestrator/conclusion.py"],
        "tests": ["tests/test_methodology.py",
                  "tests/orchestrator/test_caption_gate.py",
                  "tests/orchestrator/test_conclusion.py"],
        "docs": ["docs/METHODOLOGY.md"],
    },
    "0037": {
        "title": "The completed algebra: traverse + result-set kernels",
        "category": "architecture",
        "axioms": ["D1"],
        "modules": ["src/graph/traversal.py", "src/orchestrator/ops.py"],
        "tests": ["tests/graph/test_traversal.py", "tests/orchestrator/test_ops.py"],
        "docs": ["docs/architecture/QUESTION_MAP.md", "docs/METHODOLOGY.md"],
    },
    "0038": {
        "title": "The interaction layer: 'no' is input",
        "category": "product",
        "axioms": [],
        "modules": ["src/steps/agent_events.py"],
        "tests": ["tests/steps/test_agent_events.py",
                  "tests/orchestrator/test_events.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0039": {
        "title": "Every error links to its contract",
        "category": "architecture",
        "axioms": ["C3"],
        "modules": ["src/steps/gates.py", "src/governance/funnel.py",
                    "src/governance/journey.py"],
        "tests": ["tests/governance/test_funnel.py",
                  "tests/governance/test_journey.py",
                  "tests/test_table_contracts.py"],
        "docs": ["docs/deployment/INSTALLATION_GUIDE.md"],
    },
    "0040": {
        "title": "The consumption layer: reports and measures",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/graph/consumption.py", "src/steps/semantic_models.py",
                    "src/steps/semantic_catalog.py", "src/extractor/devops_tmdl.py",
                    "src/extractor/tmdl_source.py"],
        "tests": ["tests/steps/test_semantic_models.py",
                  "tests/steps/test_semantic_catalog.py",
                  "tests/adapters/test_devops_tmdl.py",
                  "tests/extractor/test_workspace_tmdl_source.py",
                  "tests/orchestrator/test_report_links.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0041": {
        "title": "M mini-parser, shape registry, fallout capture",
        "category": "architecture",
        "axioms": ["C2"],
        "modules": ["src/mquery/parser.py", "src/mquery/signature.py",
                    "src/mquery/registry.py", "src/mquery/census.py"],
        "tests": ["tests/mquery/test_mquery.py"],
        "docs": ["docs/architecture/SOURCE_CONNECTORS.md"],
    },
    "0042": {
        "title": "The notebook contract: a harness for the driver layer",
        "category": "architecture",
        "axioms": ["C3"],
        "modules": ["src/notebook_registry.py", "src/replan.py"],
        "tests": ["tests/test_notebook_contract.py", "tests/test_replan.py",
                  "tests/test_docs_consistency.py"],
        "docs": ["docs/architecture/NOTEBOOK_MAP.md"],
    },
    "0043": {
        "title": "The diff kernel: the founding question's shape",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/graph/decomposition_diff.py"],
        "tests": ["tests/graph/test_decomposition_diff.py",
                  "tests/orchestrator/test_ops.py"],
        "docs": ["docs/architecture/QUESTION_MAP.md"],
    },
    "0044": {
        "title": "The tree contract: round-trip verified descriptions",
        "category": "architecture",
        "axioms": ["B1", "B2", "C2", "E4", "E5", "E6", "F"],
        "modules": ["src/tree/extract.py", "src/tree/translate.py",
                    "src/tree/verify.py", "src/tree/diff.py",
                    "src/tree/render.py", "src/tree/pipeline.py",
                    "src/steps/build_graph.py"],
        "tests": ["tests/test_tree_contract.py", "tests/tree/test_extract.py",
                  "tests/graph/test_decision_wiring.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0045": {
        "title": "The escalation contract: no silent residue",
        "category": "architecture",
        "axioms": ["C2", "H1", "H2"],
        "modules": ["src/governance/leaf_grounding.py"],
        "tests": ["tests/test_escalation_contract.py",
                  "tests/governance/test_leaf_grounding.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0046": {
        "title": "Anchor, discover, match, rank — the human picks",
        "category": "architecture",
        "axioms": ["E1", "E4", "E5"],
        "modules": ["src/discovery/paths.py", "src/discovery/grounding.py"],
        "tests": ["tests/test_spec_gates.py", "tests/test_derive_relationships.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0047": {
        "title": "The shadow specification (the axiom system)",
        "category": "architecture",
        "axioms": ["C4", "G1", "G3", "G2"],
        "modules": ["src/extraction_registry.py", "src/capability_registry.py"],
        "tests": ["tests/test_extraction_registry.py",
                  "tests/test_capability_registry.py", "tests/test_spec_gates.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0048": {
        "title": "Declared zones, trace registry, admin graph, companion",
        "category": "architecture",
        "axioms": ["B1", "C1", "D3", "H2"],
        "modules": ["src/zones.py", "src/trace_registry.py",
                    "src/admin_graph.py", "src/companion.py"],
        "tests": ["tests/test_zones.py", "tests/test_trace_registry.py",
                  "tests/test_term_hygiene.py", "tests/test_admin_graph.py",
                  "tests/test_companion.py"],
        "docs": ["docs/architecture/SPEC.md", "docs/architecture/TRACE_MAP.md"],
    },
    "0063": {
        # ACCEPTED 2026-08-30 (Resolution Console v1, file-first,
        # the Inbox, the total landing map). Build began on the
        # lift: X-RAY-1 (src/xray.py — the wedge report) first;
        # BRIDGE-1 exporters and CONSOLE-1 follow in the
        # tier-locked queue.
        "title": "The product tiers: X-Ray, Bridge, Workbench, Run",
        "category": "product",
        "axioms": [],
        "modules": ["src/xray.py", "src/adapters/file_export.py"],
        "tests": ["tests/test_xray.py",
                  "tests/adapters/test_file_export.py"],
        "docs": ["docs/decisions/0063-product-tiers.md"],
    },
    "0062": {
        # ACCEPTED 2026-08-29, all calls ruled same-day (developer
        # door every round; convert the parse card FIRST on
        # hold-lift; axiom register 0062:A1-A6 standing). First
        # build landed the same day the hold lifted: the ITERATION
        # card (show grounded matches → propose → ask w/ prune +
        # the standing developer door; /api/escalate captures
        # demand as a 0056 deny event).
        "title": "The dialogue loop: show, propose, ask, execute",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/webapp/app.py"],
        "tests": ["tests/webapp/test_app.py"],
        "docs": ["docs/decisions/0062-the-dialogue-loop.md"],
    },
    "0061": {
        # DRAFT 2026-08-28 (overnight, review-authored): the run
        # layer — Pro runs the confirmed definition. Slice 1 built
        # same night (PHASE2-SLICE-1, overnight-authorized against
        # the draft): ScriptDom single-SELECT gate, TOP-cap-as-fact,
        # P5 stamps-only capture, /api/run + run button. Three §6
        # open calls await Sunny; defaults stand until relaxed.
        "title": "The run layer: Pro runs the confirmed definition",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/run_layer.py"],
        "tests": ["tests/test_run_layer.py"],
        "docs": ["docs/decisions/0061-the-run-layer.md"],
    },
    "0060": {
        # ACCEPTED 2026-08-28 (all three calls ruled same-day:
        # confirm-all, usage-promotion w/ steward veto, frontier
        # pilot parser). PROTOTYPE built + the gating experiment
        # measured (PARSE_EXPERIMENT.md: PROPOSED 7/7 oracles vs
        # CURRENT 6/7); the ENGINE change stays gated on the full
        # measurement incl. Sunny's walk paraphrases.
        "title": "The parse is the plan: parser-only LLM, "
                 "deterministic traversal, correction flywheel",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/orchestrator/parse_plan.py"],
        "tests": ["tests/orchestrator/test_parse_plan.py"],
        "docs": ["docs/decisions/0060-parse-is-the-plan.md"],
    },
    "0059": {
        # ACCEPTED + MECHANIZED 2026-08-26: union-find analyzer
        # (foundation exception + receipt exclusion), EDGE_PROVENANCE
        # totality, 300 postcondition, recorded-corpus baseline as
        # permanent CI, live-audit topology leg; spec Group Q (the
        # ADR's G1-G3 renamed on entry — G was taken).
        "title": "The graph topology axioms: connected, sound, "
                 "complete (measured, then formalized)",
        "category": "architecture",
        "axioms": ["Q1", "Q2", "Q3"],
        "modules": ["src/graph/topology.py"],
        "tests": ["tests/graph/test_topology.py"],
        "docs": ["docs/decisions/0059-graph-topology-axioms.md",
                 "docs/architecture/SPEC.md"],
    },
    "0058": {
        # DRAFT 2026-08-25 (review): the self-service contracts —
        # contracts-first for the Pro pillar; Sunny ratifies; build
        # lands WITH Pro, nothing in the current queue.
        "title": "The self-service contracts: contracts-first for "
                 "the Pro pillar (provenance rungs, execution floors)",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/decisions/0058-self-service-contracts.md"],
    },
    "0057": {
        # ACCEPTED 2026-08-25 — DESIGN RECORD (five Sunny+review
        # rounds): the four-shell sphere, change-propagation nervous
        # system, ownership economy, static/dynamic contracts split.
        # Binds future design; enters the build queue only by future
        # orders — no modules by construction.
        "title": "The Sphere: architecture model, ownership economy, "
                 "contracts split",
        "category": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/decisions/0057-the-sphere.md",
                 "docs/architecture/SPHERE.md"],
    },
    "0056": {
        # ACCEPTED 2026-08-25; FLYWHEEL-1 (Sunny-authorized
        # 2026-08-29) pulled the v1 MECHANISM forward: usage weights
        # from captured decision events, card provenance disclosure,
        # the Ground-Truth Shelf (my definitions/reports/questions,
        # replay). The full typed-deny algebra + promotion ladder
        # still land with the post-capture build order.
        "title": "The decision algebra: every answer ends in a "
                 "decision (typed deny, usage weights)",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/flywheel.py"],
        "tests": ["tests/test_flywheel.py"],
        "docs": ["docs/decisions/0056-decision-algebra.md"],
    },
    "0055": {
        # ACCEPTED + BUILT 2026-08-25 (dimensions ratified by Sunny;
        # both phases in one overnight run): generator + matrix
        # registry + checker + the `shapes` CI family; corpus of
        # record under data/shapes/generated/ (regen byte-identical).
        "title": "The designed shape corpus: spec-derived test data "
                 "(category-partition over name x logic x scope)",
        "category": "architecture",
        "axioms": ["E2"],
        "modules": ["src/shapes/generator.py", "src/shapes/matrix.py",
                    "src/shapes/checker.py"],
        "tests": ["tests/shapes/test_shapes.py"],
        "docs": ["docs/decisions/0055-designed-shape-corpus.md"],
    },
    "0054": {
        # ACCEPTED + BUILT 2026-08-23 (all four ratifications ruled;
        # build order HANDOFF_0054_BUILD): sweep + flag surface live;
        # the disposition WRITE surface (plan-confirm, ADR 0050) is
        # the recorded follow-up.
        "title": "Governance red flags and governed plurality: "
                 "misnomer/duplicate/cousin sweep over content hashes",
        "category": "architecture",
        "axioms": ["C1", "E2"],
        "modules": ["src/governance/red_flags.py",
                    "src/steps/red_flag_sweep.py"],
        "tests": ["tests/governance/test_red_flags.py",
                  "tests/orchestrator/test_flag_ops.py"],
        "docs": ["docs/decisions/"
                 "0054-governance-red-flags-governed-plurality.md"],
    },
    "0053": {
        "title": "Projection-grain column lineage: transform_to_column "
                 "edges, resolved-only, conservation-counted",
        "category": "architecture",
        "axioms": ["C1", "C2"],
        "modules": ["src/graph/builder.py", "src/steps/build_graph.py"],
        "tests": ["tests/graph/test_builder.py",
                  "tests/orchestrator/test_ops.py"],
        "docs": ["docs/decisions/0053-projection-column-lineage.md"],
    },
    "0052": {
        "title": "The reachability contract: every graph payload "
                 "reachable by a named op or excluded with a reason",
        "category": "architecture",
        "axioms": ["C1"],
        "modules": ["src/reachability.py",
                    "devtools/reachability_audit.py"],
        "tests": ["tests/test_reachability.py",
                  "tests/test_reachability_audit.py"],
        "docs": ["docs/decisions/0052-reachability-contract.md",
                 "docs/architecture/SPEC.md"],
    },
    "0051": {
        "title": "The one-mind turn: one conversation decides, the "
                 "boundary enforces (supersedes 0036/0050's shape)",
        "category": "architecture",
        "axioms": ["E3", "E6"],
        "modules": ["src/orchestrator/turn_engine.py"],
        "tests": ["tests/orchestrator/test_turn_engine.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0050": {
        "title": "Bounded read-only answer loop: plan to the answer, "
                 "caption answers, auto-continue (amends 0036)",
        "category": "architecture",
        "axioms": ["E3"],
        "modules": ["src/orchestrator/turn_engine.py"],
        "tests": ["tests/orchestrator/test_turn_engine.py"],
        "docs": [],
    },
    "0049": {
        "title": "Ingestion routes: filedrop, folders, live extractor",
        "category": "architecture",
        "axioms": [],
        "modules": ["src/extractor/connection.py", "src/extractor/discovery.py",
                    "src/extractor/extractor.py", "src/extractor/tracker.py"],
        "tests": ["tests/extractor/test_connection.py",
                  "tests/extractor/test_extractor.py",
                  "tests/extractor/test_proc_parity.py"],
        "docs": ["docs/architecture/SOURCE_CONNECTORS.md"],
    },
}


def modules_cited() -> "set[str]":
    return {m for e in TRACE_REGISTRY.values() for m in e["modules"]}


def decisions_for_module(module: str) -> "list[str]":
    return sorted(adr for adr, e in TRACE_REGISTRY.items()
                  if module in e["modules"])
