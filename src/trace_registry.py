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

# Axiom ids and framework parents are DERIVED from the axiom ledger
# (src/spec_registry.py, ADR 0067 turn 1) — the single writer. The two
# hand-maintained structures this replaced had already drifted once
# each (Group P unregistered for 11 days; the crosswalk lived only in
# a doc until 2026-09-01).
from src.spec_registry import SPEC_REGISTRY

SPEC_AXIOMS = frozenset(SPEC_REGISTRY)

CATEGORIES = ("architecture", "product")

# ---------------------------------------------------------------------
# The documentation dependency hierarchy (Sunny's ruling, 2026-09-01)
# ---------------------------------------------------------------------
# Three tiers, one direction — a strict chain, no cycles:
#
#   ROOT       docs/AI_VIA_AXIOMS.md      the constitution (axm:*)
#     ^
#   BLUEPRINT  docs/architecture/*.md     system topology + boundaries
#     ^        docs/product/PRODUCT_TIERS  the OFFER (kept separate:
#     |                                    Sunny's ruling 2026-09-01)
#     |                                   (each declares the axiom
#     |                                    GROUPS it satisfies)
#   EXECUTION  docs/decisions/*.md        one component each; authority
#                                         reaches the axioms THROUGH
#                                         its blueprint file
#
# Why the indirection: an ADR is an engineering choice about a SYSTEM
# COMPONENT. Routing through the blueprint says WHERE the change lives,
# and keeps decision logs free of repeated philosophical preamble. The
# audit trail reads: ADR 0061 changes the run layer -> the run layer is
# specified in SPEC.md -> SPEC.md satisfies axiom groups M and B.
#
# CITATION HANDLES (the two axiom systems are DISTINCT — group letters
# B, D and R collide across them, so a bare id is ambiguous):
#   axm:M5   -> docs/AI_VIA_AXIOMS.md   the framework (root law)
#   spec:C1  -> docs/architecture/SPEC.md  the shadow spec (this system)

# Framework axiom ids defined by docs/AI_VIA_AXIOMS.md.
AXM_AXIOMS = frozenset({
    "D1", "D2", "D3", "D4",          # Data
    "S1", "S2", "S3",                # Specification
    "J1", "J2", "J3", "J4",          # Judgment
    "M1", "M2", "M3", "M4", "M5",    # Mind
    "B1", "B2", "B3", "B4",          # Boundary
    "R1", "R2", "R3", "R4",          # Residue & Ledger
})

AXM_GROUPS = frozenset({"D", "S", "J", "M", "B", "R"})

# The crosswalk mapping, derived per record (prose narrative stays in
# docs/architecture/AXIOM_CROSSWALK.md; the data decides here).
SPEC_TO_AXM = {ax: rec["parents"] for ax, rec in SPEC_REGISTRY.items()}

# Framework axioms with NO spec axiom, each with its recorded reason.
# meta  = a law ABOUT having a spec; implementing it as a spec axiom
#         would be circular. Satisfied by the spec existing/being kept.
# gap   = REAL LAW, enforced in code, but never stated as an axiom —
#         a finding against SPEC's own closure claim (§1), not an
#         artifact of the mapping. Closing these needs an ADR (§16).
# Only meta entries remain: the two `gap` rows (R2, R4) were CLOSED by
# ADR 0064 / SPEC Group L on 2026-09-01. Direction 2 of the crosswalk
# now holds — every non-meta framework axiom reaches a spec axiom.
# J3 LEFT this list on 2026-09-02: spec:G4 (the check contract)
# implements "coverage matches type" for checks themselves — the first
# meta-axiom to become implementable, caught by the closure check when
# G4 landed with parent J3.
AXM_UNMAPPED = {
    "S1": ("meta", "SPEC.md IS the Phi this axiom demands"),
    "S2": ("meta", "amendment authority; SPEC section 16 change discipline"),
}

# The BLUEPRINT tier: one row per architecture map. `satisfies` names
# the framework axiom GROUPS the file translates into topology — the
# upward edge to the root layer. Every ADR must name a component whose
# `doc` is one of these (the downward edge).
ARCHITECTURE_COMPONENTS = {
    "spec": {
        "doc": "docs/architecture/SPEC.md",
        "current_through": "0076",
        "title": "The shadow specification — the formal axiom system",
        "satisfies": ["S", "J", "M", "B", "R"],
        "governs": "The axiom system this codebase is checked against: "
                   "identity, soundness, completeness, derivation, "
                   "ask-time determinism, interpretation, and the "
                   "run-layer boundary.",
    },
    "architecture": {
        # ADR 0066 (2026-09-02): absorbed the former `sphere`
        # component — one system-model file, organized by the Sphere,
        # every section carrying a build status.
        "doc": "docs/architecture/ARCHITECTURE.md",
        "current_through": "0071",
        "title": "The system model — the Sphere",
        # all six groups since ADR 0071 (user_flow absorbed): the one
        # system-model file legitimately spans the constitution.
        "satisfies": ["D", "S", "J", "M", "B", "R"],
        "governs": "What the system is and is becoming, in one file: "
                   "the four shells, radial dynamics, data flow, the "
                   "nervous system, the ownership economy, the "
                   "contracts split — each section build-statused.",
    },
    "pipeline": {
        "doc": "docs/architecture/PIPELINE_MAP.md",
        "current_through": "0025",
        "title": "Pipeline dataflow — stages and contracts",
        "satisfies": ["D", "R"],
        "governs": "The notebook/stage sequence, each stage's inputs "
                   "and outputs, and the conservation of rows across "
                   "them.",
    },
    "integration": {
        # ADR 0069: absorbed the former `connectors` component —
        # SOURCE_CONNECTORS.md retired; its configurations are rows,
        # its change/identity doctrine is registry data.
        "doc": "docs/architecture/INTEGRATION_MAP.md",
        "current_through": "0069",
        "title": "Integrations — acquisition, publication, identity",
        "satisfies": ["D", "B", "R"],
        "governs": "The connector and catalog landscape as data: every "
                   "source configuration and write target, change "
                   "detection, and object identity across re-ingests.",
    },
    "notebook": {
        "doc": "docs/architecture/NOTEBOOK_MAP.md",
        "current_through": "0070",
        "title": "The notebook contract + the question families",
        "satisfies": ["S", "J"],
        "governs": "The layer-0 question families as records (ADR "
                   "0070), every notebook's registry entry with its "
                   "served families, and the AST-enforced planks.",
    },
    "reference": {
        "doc": "docs/architecture/REFERENCE_ARCHITECTURE.md",
        "current_through": "0058",
        "title": "Reference architecture — tiers and deployment",
        "satisfies": ["S", "B"],
        "governs": "The product tiers, source connectors, and the "
                   "customer-tenant deployment footprint.",
    },
    "landing": {
        "doc": "docs/architecture/DECISION_LANDING_MATRIX.md",
        "current_through": "0068",
        "title": "Decision landing — where every action lands",
        "satisfies": ["B", "R"],
        "governs": "Which artifact each governance action produces in "
                   "Purview/Collibra, and the OUTBOX that remembers it.",
    },
    "test": {
        "doc": "docs/architecture/TEST_MAP.md",
        "current_through": "0055",
        "title": "Test map — what every test proves",
        "satisfies": ["J"],
        "governs": "The verification strata: which check carries which "
                   "claim, by ADR, standing law, and contract.",
    },
    "crosswalk": {
        "doc": "docs/architecture/AXIOM_CROSSWALK.md",
        "current_through": "0072",
        "title": "Axiom crosswalk — framework to specification",
        "satisfies": ["S"],
        "governs": "The bridge between the two axiom systems: which "
                   "framework law each spec axiom applies here, and "
                   "which framework laws are meta or unstated gaps.",
    },
    "trace": {
        "doc": "docs/architecture/TRACE_MAP.md",
        "current_through": "0048",
        "title": "Trace map — the lineage projection",
        "satisfies": ["S", "J"],
        "governs": "This registry, projected: decision -> component -> "
                   "axioms -> code -> tests.",
    },
    # Product decisions are choices about the OFFER, not about a system
    # component — so they get their own blueprint, kept OUT of
    # docs/architecture/ (Sunny's ruling, 2026-09-01: separate the
    # product offering into its own folder). PRODUCT_TIERS.md is the
    # blueprint; the marketplace listing is a downstream sales artifact
    # that expresses it for one audience, never the blueprint itself.
    "product": {
        "doc": "docs/product/PRODUCT_TIERS.md",
        "current_through": "0063",
        "title": "Product tiers — the offer structure",
        "satisfies": ["S"],
        "governs": "What is sold, in what tiers, with which claims and "
                   "which gates. Bounded by ADR 0063's tier lock; "
                   "pricing and naming are parked, never invented.",
    },
}

TRACE_REGISTRY = {
    "0001": {
        "title": "Native parsers per SQL dialect",
        "category": "architecture",
        "component": "architecture",
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
        "component": "architecture",
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
        "component": "architecture",
        "axioms": [],
        "modules": ["src/graph/builder.py", "src/orchestrator/assemble.py"],
        "tests": ["tests/graph/test_serialization.py", "tests/graph/test_builder.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0004": {
        "title": "Two-stage human-in-the-loop certification",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/governance/steward.py"],
        "tests": ["tests/governance/test_steward.py"],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0005": {
        "title": "Agent refuses when no certified path exists",
        "category": "architecture",
        "component": "spec",
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
        "component": "integration",
        "axioms": [],
        "modules": ["src/adapters/purview.py"],
        "tests": ["tests/adapters/test_adapters.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0007": {
        "title": "BYOT deployment as a Python library (.whl)",
        "category": "architecture",
        "component": "reference",
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
        "component": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/product/MARKETPLACE_LISTING.md"],
    },
    "0009": {
        "title": "Catalog integrations are optional adapters",
        "category": "architecture",
        "component": "integration",
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
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0010": {
        "title": "Skip Founders Hub Level 3, go direct to Partner Center",
        "category": "product",
        "component": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": [],
    },
    "0011": {
        "title": "Static install guide for v1; companion trigger now "
                 "'admin graph projected' (amended, ADR 0048)",
        "category": "product",
        "component": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/deployment/INSTALLATION_GUIDE.md"],
    },
    "0012": {
        "title": "Build on the existing repo, no rewrite",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0013": {
        "title": "List as transactable SaaS on the commercial marketplace",
        "category": "product",
        "component": "product",
        "axioms": [],
        "modules": ["src/marketplace/fulfillment.py"],
        "tests": ["tests/marketplace/test_fulfillment.py",
                  "tests/marketplace/test_host.py"],
        "docs": ["docs/product/MARKETPLACE_LISTING.md",
                 "docs/legal/terms-of-service.md",
                 "docs/product/REVIEWER_GUIDE.md"],
    },
    "0014": {
        "title": "Ground the agent in metric_logic; dictionary is mandatory",
        "category": "architecture",
        "component": "architecture",
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
        "component": "spec",
        "axioms": ["A2"],
        "modules": ["src/schemas.py", "src/adapters/fabric_pbi.py"],
        "tests": ["tests/test_schemas.py", "tests/adapters/test_fabric_pbi.py",
                  "tests/test_table_contracts.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0016": {
        "title": "Case-insensitive identifier matching, folded uppercase",
        "category": "architecture",
        "component": "spec",
        "axioms": ["A1", "A3"],
        "modules": ["src/parser/identity.py"],
        "tests": ["tests/parser/test_identity.py", "tests/test_dictionary.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0017": {
        "title": "Resolve-then-traverse agent retrieval",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/graph/templates.py", "src/adapters/fabric_agent.py"],
        "tests": ["tests/test_graph_templates.py",
                  "tests/adapters/test_fabric_agent.py"],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0018": {
        "title": "Materialized closure edges (USES_TABLE)",
        "category": "architecture",
        "component": "spec",
        "axioms": ["D2"],
        "modules": ["src/graph/export.py", "src/steps/export.py"],
        "tests": ["tests/test_recorded_pipeline.py", "tests/steps/test_steps.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0019": {
        "title": "CTE descriptions bottom-up, before metric descriptions",
        "category": "architecture",
        "component": "pipeline",
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
        "component": "reference",
        "axioms": [],
        "modules": ["src/adapters/collibra_lineage_match.py"],
        "tests": ["tests/adapters/test_lineage_match.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0021": {
        "title": "Certification discloses, never gates",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py"],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0022": {
        "title": "Definition versioning: certification pins a content hash",
        "category": "architecture",
        "component": "integration",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0023": {
        "title": "Usage-weighted governance flywheel",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/orchestrator/events.py"],
        "tests": ["tests/orchestrator/test_events.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0024": {
        "title": "Layered truth: personal beside enterprise definitions",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/test_schemas.py", "tests/test_table_contracts.py"],
        "docs": [],
    },
    "0025": {
        "title": "PHI scanning at ingestion; the LLM boundary is the gate",
        "category": "architecture",
        "component": "pipeline",
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
        "component": "landing",
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
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": ["tests/governance/test_steward.py"],
        "docs": ["docs/development/OWNERSHIP_ATTRIBUTION.md"],
    },
    "0028": {
        "title": "Contact-me first; transactable at first-buyer signal",
        "category": "product",
        "component": "product",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/product/MARKETPLACE_LISTING.md"],
    },
    "0029": {
        "title": "Dimension layer activation (design pass, unimplemented)",
        "category": "architecture",
        "component": "reference",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/architecture/REFERENCE_ARCHITECTURE.md"],
    },
    "0030": {
        "title": "Layered retrieval: search terms first, vectors where allowed",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/steps/search_index.py", "src/orchestrator/kusto.py"],
        "tests": ["tests/steps/test_search_index.py"],
        "docs": ["docs/development/FABRIC_RETRIEVAL_CAPABILITIES.md"],
    },
    "0031": {
        "title": "Business terms: weighted plurality",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/governance/business_terms.py"],
        "tests": ["tests/governance/test_business_terms.py"],
        "docs": [],
    },
    "0032": {
        "title": "Deterministic core, LLM edges",
        "category": "architecture",
        "component": "spec",
        "axioms": ["E2"],
        "modules": ["src/orchestrator/core.py", "src/orchestrator/assemble.py"],
        "tests": ["tests/orchestrator/test_core.py", "tests/test_grounding_evals.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0033": {
        "title": "System of record + projections: Delta is the record",
        "category": "architecture",
        "component": "spec",
        "axioms": ["D3"],
        "modules": ["src/graph/fabric_graph_backend.py", "src/graph/gql_client.py"],
        "tests": ["tests/graph/test_backend_comparison.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0034": {
        "title": "Conversational entry edge (superseded in part by 0035)",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": [],
    },
    "0035": {
        "title": "Agentic conversation over deterministic tools",
        "category": "architecture",
        "component": "architecture",
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
        "category": "architecture",
        "component": "architecture",
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
        "component": "architecture",
        "axioms": ["D1"],
        "modules": ["src/graph/traversal.py", "src/orchestrator/ops.py"],
        "tests": ["tests/graph/test_traversal.py", "tests/orchestrator/test_ops.py"],
        "docs": ["docs/architecture/ARCHITECTURE.md", "docs/METHODOLOGY.md"],
    },
    "0038": {
        "title": "The interaction layer: 'no' is input",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/steps/agent_events.py"],
        "tests": ["tests/steps/test_agent_events.py",
                  "tests/orchestrator/test_events.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0039": {
        "title": "Every error links to its contract",
        "category": "architecture",
        "component": "landing",
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
        "component": "integration",
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
        "component": "integration",
        "axioms": ["C2"],
        "modules": ["src/mquery/parser.py", "src/mquery/signature.py",
                    "src/mquery/registry.py", "src/mquery/census.py"],
        "tests": ["tests/mquery/test_mquery.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
    "0042": {
        "title": "The notebook contract: a harness for the driver layer",
        "category": "architecture",
        "component": "notebook",
        "axioms": ["C3"],
        "modules": ["src/notebook_registry.py", "src/replan.py"],
        "tests": ["tests/test_notebook_contract.py", "tests/test_replan.py",
                  "tests/test_docs_consistency.py"],
        "docs": ["docs/architecture/NOTEBOOK_MAP.md"],
    },
    "0043": {
        "title": "The diff kernel: the founding question's shape",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": ["src/graph/decomposition_diff.py"],
        "tests": ["tests/graph/test_decomposition_diff.py",
                  "tests/orchestrator/test_ops.py"],
        "docs": ["docs/architecture/ARCHITECTURE.md"],
    },
    "0044": {
        "title": "The tree contract: round-trip verified descriptions",
        "category": "architecture",
        "component": "spec",
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
        "component": "spec",
        "axioms": ["C2", "H1", "H2"],
        "modules": ["src/governance/leaf_grounding.py"],
        "tests": ["tests/test_escalation_contract.py",
                  "tests/governance/test_leaf_grounding.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0046": {
        "title": "Anchor, discover, match, rank — the human picks",
        "category": "architecture",
        "component": "architecture",
        "axioms": ["E1", "E4", "E5"],
        "modules": ["src/discovery/paths.py", "src/discovery/grounding.py"],
        "tests": ["tests/test_spec_gates.py", "tests/test_derive_relationships.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0047": {
        "title": "The shadow specification (the axiom system)",
        "category": "architecture",
        "component": "crosswalk",
        "axioms": ["C4", "G1", "G3", "G2"],
        "modules": ["src/extraction_registry.py", "src/capability_registry.py"],
        "tests": ["tests/test_extraction_registry.py",
                  "tests/test_capability_registry.py",
                  "tests/test_spec_gates.py",
                  "tests/test_axiom_crosswalk.py"],
        "docs": ["docs/architecture/SPEC.md",
                 "docs/architecture/AXIOM_CROSSWALK.md",
                 "docs/AI_VIA_AXIOMS.md"],
    },
    "0048": {
        "title": "Declared zones, trace registry, admin graph, companion",
        "category": "architecture",
        "component": "trace",
        "axioms": ["B1", "C1", "D3", "H2"],
        "modules": ["src/zones.py", "src/trace_registry.py",
                    "src/admin_graph.py", "src/companion.py"],
        "tests": ["tests/test_zones.py", "tests/test_trace_registry.py",
                  "tests/test_term_hygiene.py", "tests/test_admin_graph.py",
                  "tests/test_companion.py"],
        "docs": ["docs/architecture/SPEC.md", "docs/architecture/TRACE_MAP.md"],
    },
    "0076": {
        # ACCEPTED 2026-09-03: compositional interpretation (spec:G5)
        # — capture the scalar subtree once in the existing walk
        # (ExprNode IR), interpret by structural recursion (one rule
        # per grammar kind), checkers read the same meanings truth.
        # Carries the ordered post-mortem: conservation was quantified
        # at site grain; G2 governed the entry point, not the path;
        # the composer's input was never a named component.
        "title": "Compositional interpretation: capture once, "
                 "interpret by grammar (spec:G5)",
        "category": "architecture",
        "component": "spec",
        "axioms": ["G5"],
        "modules": ["src/tree/extract.py", "src/descriptions.py"],
        "tests": ["tests/test_skeleton_composer.py",
                  "tests/test_op_frontier.py"],
        "docs": ["docs/decisions/0076-compositional-interpretation.md",
                 "docs/architecture/SPEC.md"],
    },
    "0075": {
        # ACCEPTED 2026-09-02: the check contract (spec:G4) — fire and
        # cover are distinct claims; frontiers as data deny-by-default;
        # injected-violation proofs pinned as meta-tests; pattern
        # ancestry on the record. Born from the sloppy-ban incident.
        "title": "The check contract: checks are claims (spec:G4)",
        "category": "architecture",
        "component": "spec",
        "axioms": ["G4"],
        "modules": [],
        "tests": ["tests/test_check_contract.py"],
        "docs": ["docs/decisions/0075-the-check-contract.md",
                 "docs/architecture/SPEC.md"],
    },
    "0074": {
        # ACCEPTED 2026-09-02 (four calls ruled same day): the
        # field-evolved description
        # architecture (skeleton floor + gate acceptance) as 0044's
        # phase-3 amendment; fix 0019's metric premise (terminal steps,
        # not root CTEs; per-FILE deliverable); reopen the provenance
        # vocabulary; state the wedge description contract. Four calls
        # await Sunny; spec amendments land on ratification.
        "title": "The description architecture, ratified: skeleton "
                 "floor, gate acceptance, metric-level design",
        "category": "architecture",
        "component": "spec",
        "axioms": ["B2", "F", "T1"],
        "modules": ["src/descriptions.py"],
        "tests": ["tests/test_desc_0074.py",
                  "tests/test_skeleton_composer.py",
                  "tests/test_gate_recut.py"],
        "docs": ["docs/decisions/0074-description-architecture-ratified.md"],
    },
    "0073": {
        # ACCEPTED 2026-09-02 (the final ratchet turn): SPEC v1.0 —
        # laws, glosses, origins and STATUSES join the ledger; SPEC.md
        # is generated from scripts/spec_frame.md + the records. The
        # changelog freezes ("the ADRs are the changelog", now
        # literal). Status vocabulary closed at four incl. JUDGED.
        "title": "SPEC v1.0: the spec becomes a projection of its "
                 "own ledger (final ratchet turn)",
        "category": "architecture",
        "component": "spec",
        "axioms": [],
        "modules": ["src/spec_registry.py"],
        "tests": ["tests/test_spec_registry.py"],
        "docs": ["docs/decisions/0073-spec-goes-generated.md",
                 "docs/architecture/SPEC.md"],
    },
    "0072": {
        # ACCEPTED 2026-09-02 (ratchet turn 6): the crosswalk doc goes
        # GENERATED — Direction 1 derives from spec_registry (parents
        # + parent_note per record), Direction 2 from AXM_UNMAPPED.
        # The hand prose's history (gaps found/closed) lives in
        # 0064/0065; the doc now cannot disagree with the data.
        "title": "The crosswalk goes generated (ratchet turn 6)",
        "category": "architecture",
        "component": "crosswalk",
        "axioms": [],
        "modules": ["src/spec_registry.py"],
        "tests": ["tests/test_axiom_crosswalk.py"],
        "docs": ["docs/decisions/0072-crosswalk-goes-generated.md",
                 "docs/architecture/AXIOM_CROSSWALK.md"],
    },
    "0071": {
        # ACCEPTED 2026-09-02 (ratchet turn 5): USER_FLOW retires —
        # nothing converts because nothing was agent-obeyable law;
        # the flywheel's ~15 lines fold into ARCHITECTURE, the rest
        # was duplication/story (FCOTS RLS verified unbuilt, recorded
        # as roadmap in the ADR).
        "title": "USER_FLOW retires (ratchet turn 5)",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/decisions/0071-user-flow-retires.md",
                 "docs/architecture/ARCHITECTURE.md"],
    },
    "0070": {
        # ACCEPTED 2026-09-02 (ratchet turn 4): QUESTION_MAP.md
        # retires — the families were already half-data (serves,
        # coverage); layer 0 + shapes/storage/status become
        # FAMILY_RECORDS in notebook_registry, rendered into
        # NOTEBOOK_MAP. Storage names cross-checked against
        # TABLE_REGISTRY; runtime-routing abolition (spec:R2) stated
        # in the data, not just prose.
        "title": "QUESTION_MAP retires into the notebook registry "
                 "(ratchet turn 4)",
        "category": "architecture",
        "component": "notebook",
        "axioms": [],
        "modules": ["src/notebook_registry.py"],
        "tests": ["tests/test_question_families.py"],
        "docs": ["docs/decisions/0070-question-map-retires.md",
                 "docs/architecture/NOTEBOOK_MAP.md"],
    },
    "0069": {
        # ACCEPTED 2026-09-02 (ratchet turn 3): SOURCE_CONNECTORS.md
        # RETIRES into the integration registry — a parallel
        # connector_registry would have minted a rival truth (D2, one
        # owner). 8 configuration rows added, change/identity doctrine
        # as data, the stale sqlglot mechanism notes fixed at source.
        "title": "SOURCE_CONNECTORS retires into the integration "
                 "registry (ratchet turn 3)",
        "category": "architecture",
        "component": "integration",
        "axioms": [],
        "modules": ["src/integration_registry.py"],
        "tests": ["tests/test_integration_doctrine.py"],
        "docs": ["docs/decisions/0069-source-connectors-retire.md",
                 "docs/architecture/INTEGRATION_MAP.md"],
    },
    "0068": {
        # ACCEPTED 2026-09-02 (ratchet turn 2): the landing matrix as
        # data — landing_registry (ninth peer), the doc now generated.
        # 0063's two invariants (no action without a landing, no
        # landing without a grade) mechanized. Content keeps its DRAFT
        # v3 status; the four 2026-08-31 rulings stay RULED.
        "title": "The landing matrix as data (ratchet turn 2)",
        "category": "architecture",
        "component": "landing",
        "axioms": [],
        "modules": ["src/landing_registry.py"],
        "tests": ["tests/test_landing_registry.py"],
        "docs": ["docs/decisions/0068-landing-matrix-as-data.md",
                 "docs/architecture/DECISION_LANDING_MATRIX.md"],
    },
    "0067": {
        # ACCEPTED 2026-09-02 (Sunny: docs are data): the record
        # invariant + the prose ratchet. Turn 1 = the axiom ledger
        # (spec_registry, eighth peer): SPEC_AXIOMS and SPEC_TO_AXM
        # now DERIVED from it; per-axiom checks are data; totality
        # locked both ways to SPEC.md at the id level.
        "title": "Docs are data: the record invariant and the "
                 "prose ratchet",
        "category": "architecture",
        "component": "spec",
        "axioms": [],
        "modules": ["src/spec_registry.py"],
        "tests": ["tests/test_spec_registry.py"],
        "docs": ["docs/decisions/0067-docs-are-data.md",
                 "docs/architecture/SPEC.md"],
    },
    "0066": {
        # ACCEPTED 2026-09-02 (Sunny: "we only need one"): SPHERE.md
        # merged into ARCHITECTURE.md — one system-model blueprint,
        # organized by the Sphere, build status per section. Kills the
        # three-rival-layer-models drift (3 layers / 4 shells / SPEC
        # section-4 sorts). ADR 0057's model unchanged, re-homed.
        "title": "One system-model file: SPHERE merges into "
                 "ARCHITECTURE",
        "category": "architecture",
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/decisions/0066-merge-sphere-into-architecture.md",
                 "docs/architecture/ARCHITECTURE.md"],
    },
    "0065": {
        # ACCEPTED 2026-09-01 (Sunny: "we should promote 13"): SPEC
        # section 13 becomes Group T. Zero new mechanisms — T1 and T3
        # cite what exists, T2 states the kappa-diff gap that goes live
        # when fragment stitching ships. The value is that three
        # previously-unnumbered laws are citable and statused.
        "title": "Promote section 13 to Group T: the double-sided "
                 "function as numbered law",
        "category": "architecture",
        "component": "crosswalk",
        "axioms": ["T0", "T1", "T2", "T3"],
        "modules": [],
        "tests": ["tests/test_tree_contract.py"],
        "docs": ["docs/decisions/0065-promote-the-double-sided-function.md",
                 "docs/architecture/SPEC.md",
                 "docs/architecture/AXIOM_CROSSWALK.md"],
    },
    "0064": {
        # ACCEPTED 2026-09-01, all three calls ruled same-day (targeted
        # L1 scan · pin L2 immediately · letter L): SPEC Group L — the
        # ledger (append-only OBEYED, derived aggregates) and
        # drift-fires. Closes the two real axm gaps (R2, R4). L1/L2
        # ENFORCED via test_ledger_contract (proven against injected
        # violations); L3 by citation (0059 Q3 precedent). No modules
        # by design — the axioms bind existing machinery.
        "title": "Group L: the ledger and drift axioms "
                 "(closing the crosswalk gaps)",
        "category": "architecture",
        "component": "crosswalk",
        "axioms": ["L1", "L2", "L3"],
        "modules": [],
        "tests": ["tests/test_ledger_contract.py"],
        "docs": ["docs/decisions/0064-the-ledger-and-drift-axioms.md",
                 "docs/architecture/AXIOM_CROSSWALK.md"],
    },
    "0063": {
        # ACCEPTED 2026-08-30 (Resolution Console v1, file-first,
        # the Inbox, the total landing map). Build began on the
        # lift: X-RAY-1 (src/xray.py — the wedge report) first;
        # BRIDGE-1 exporters and CONSOLE-1 follow in the
        # tier-locked queue.
        "title": "The product tiers: X-Ray, Bridge, Workbench, Run",
        "category": "product",
        "component": "product",
        "axioms": [],
        "modules": ["src/xray.py", "src/adapters/file_export.py",
                    "src/console.py"],
        "tests": ["tests/test_xray.py",
                  "tests/adapters/test_file_export.py",
                  "tests/test_console.py"],
        "docs": ["docs/decisions/0063-product-tiers.md",
                 "docs/product/XRAY_ENGAGEMENT.md"],
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
        "component": "architecture",
        "axioms": ["R2", "R3", "R4", "R5"],
        "modules": ["src/webapp/app.py"],
        "tests": ["tests/webapp/test_app.py"],
        "docs": ["docs/decisions/0062-the-dialogue-loop.md",
                 "docs/architecture/SPEC.md"],
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
        "component": "spec",
        "axioms": ["R6", "R7", "R8"],
        "modules": ["src/run_layer.py"],
        "tests": ["tests/test_run_layer.py"],
        "docs": ["docs/decisions/0061-the-run-layer.md",
                 "docs/architecture/SPEC.md"],
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
        "component": "spec",
        "axioms": ["R1", "R3"],
        "modules": ["src/orchestrator/parse_plan.py"],
        "tests": ["tests/orchestrator/test_parse_plan.py"],
        "docs": ["docs/decisions/0060-parse-is-the-plan.md",
                 "docs/architecture/SPEC.md"],
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
        "component": "spec",
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
        "component": "reference",
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
        "component": "architecture",
        "axioms": [],
        "modules": [],
        "tests": [],
        "docs": ["docs/decisions/0057-the-sphere.md",
                 "docs/architecture/ARCHITECTURE.md"],
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
        "component": "architecture",
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
        "component": "test",
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
        "component": "architecture",
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
        "component": "architecture",
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
        "component": "spec",
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
        "component": "spec",
        "axioms": ["E3", "E6", "P1", "P2", "P3", "P4", "P5", "P6"],
        "modules": ["src/orchestrator/turn_engine.py"],
        "tests": ["tests/orchestrator/test_turn_engine.py"],
        "docs": ["docs/architecture/SPEC.md"],
    },
    "0050": {
        "title": "Bounded read-only answer loop: plan to the answer, "
                 "caption answers, auto-continue (amends 0036)",
        "category": "architecture",
        "component": "architecture",
        "axioms": ["E3"],
        "modules": ["src/orchestrator/turn_engine.py"],
        "tests": ["tests/orchestrator/test_turn_engine.py"],
        "docs": [],
    },
    "0049": {
        "title": "Ingestion routes: filedrop, folders, live extractor",
        "category": "architecture",
        "component": "integration",
        "axioms": [],
        "modules": ["src/extractor/connection.py", "src/extractor/discovery.py",
                    "src/extractor/extractor.py", "src/extractor/tracker.py"],
        "tests": ["tests/extractor/test_connection.py",
                  "tests/extractor/test_extractor.py",
                  "tests/extractor/test_proc_parity.py"],
        "docs": ["docs/architecture/INTEGRATION_MAP.md"],
    },
}


def modules_cited() -> "set[str]":
    return {m for e in TRACE_REGISTRY.values() for m in e["modules"]}


def decisions_for_module(module: str) -> "list[str]":
    return sorted(adr for adr, e in TRACE_REGISTRY.items()
                  if module in e["modules"])
