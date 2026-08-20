"""EXTRACTION_REGISTRY — the extraction-functor inventory (spec:C1).

The completeness frontier, enumerated. Every kind of source fact either
has a declared extractor (a functor F_k : R_k -> G) or an explicit
exclusion row with a reason. There is no third state — "nobody thought
about it" is exactly the state this registry abolishes.

Motivating incident (spec:C1 origin): the vendor dictionary's join map
J_D had no functor and no exclusion — the technical layer silently
wasn't the complete join map, and only a code-walk found it (recovered
1.27.0/1.28.0). Run against the pre-1.28.0 state, this registry would
have shown `dictionary_joins` as a missing row — the acceptance test
in tests/test_extraction_registry.py pins that forever.

Peer of TABLE_REGISTRY / NOTEBOOK_REGISTRY / SHAPE_REGISTRY /
CAPABILITY_REGISTRY. Adding or excluding a source kind IS the review.

Row contract:
    reference     which reference structure feeds it (spec §4):
                  D = vendor dictionary, P = parsed SQL corpus,
                  M = TMDL/M corpus, O = org declarations,
                  Gov = governance record
    status        "extracted" | "excluded"
    extractor     (extracted) {module, entry} — the functor
    targets       (extracted) node/edge kinds it produces (spec Σ names)
    conservation  (extracted) {home, check} — where |dom| = handled ⊎
                  fallout is accounted, and the file/table that proves it
    exclusion_reason  (excluded) why, with the ruling's provenance
"""

EXTRACTION_REGISTRY = {
    # ----- D: the vendor dictionary --------------------------------
    "dictionary_tables": {
        "reference": "D",
        "status": "extracted",
        "extractor": {"module": "src/graph/builder.py",
                      "entry": "build_graph_step (dictionary load)"},
        "targets": ["Table"],
        "conservation": {
            "home": "graph_nodes technical layer",
            "check": "postcondition gates + input_dict_tables unique "
                     "invariant (tests/test_table_contracts.py)",
        },
    },
    "dictionary_columns": {
        "reference": "D",
        "status": "extracted",
        "extractor": {"module": "src/graph/builder.py",
                      "entry": "build_graph_step (dictionary load)"},
        "targets": ["Column", "tab2col"],
        "conservation": {
            "home": "graph_nodes technical layer",
            "check": "postcondition gates + input_dict_columns unique "
                     "invariant (tests/test_table_contracts.py)",
        },
    },
    "dictionary_joins": {
        # THE incident row (spec:C1): before 1.27.0 this kind had no
        # functor and no exclusion — the inventory-level violation that
        # motivated this registry. Removing this row fails the
        # acceptance test.
        "reference": "D",
        "status": "extracted",
        "extractor": {"module": "scripts/derive_dict_relationships.py",
                      "entry": "main (native bootstrap; regenerates from "
                               "graph_decision_sites after ADR 0044 1b)"},
        "targets": ["joinable"],
        "conservation": {
            "home": "input_dict_relationships (planned table)",
            "check": "tests/test_derive_relationships.py — committed CSV "
                     "== fresh derivation; blind spot printed (0 native)",
        },
    },
    "org_reference_tables": {
        # T_org (spec §4): org-created value sets / control parameters —
        # declared via the ORIGIN column on input_dict_tables
        # (vendor|org), the T_org vehicle ruled 2026-08-19.
        "reference": "O",
        "status": "extracted",
        "extractor": {"module": "src/graph/builder.py",
                      "entry": "build_graph_step (dictionary load; "
                               "ORIGIN column distinguishes the sort)"},
        "targets": ["Table (T_org)"],
        "conservation": {
            "home": "input_dict_tables (ORIGIN column)",
            "check": "allowed_values invariant on ORIGIN "
                     "(tests/test_table_contracts.py)",
        },
    },
    # ----- P: the parsed SQL corpus --------------------------------
    "sql_procedures": {
        "reference": "P",
        "status": "extracted",
        "extractor": {"module": "src/parser/scriptdom_fabric.py",
                      "entry": "parse_from_fragment (via src/steps/parse.py)"},
        "targets": ["Metric", "Step", "dep", "reads", "calc"],
        "conservation": {
            "home": "ops_parse_results ⊎ ops_parse_errors",
            "check": "loaded = parsed + errored "
                     "(journey reconciliation tests; funnel stage 200)",
        },
    },
    "decision_sites": {
        "reference": "P",
        "status": "extracted",
        "extractor": {"module": "src/tree/extract.py",
                      "entry": "build_decision_tree (ADR 0044 clause 1)"},
        "targets": ["Site", "sites (1b: decision→column edges)"],
        "conservation": {
            "home": "graph_decision_sites + ops_fallout "
                     "stage 300_tree_unextracted",
            "check": "handled + unextracted == total, asserted in the "
                     "extractor; tests/test_tree_contract.py clause 1",
        },
    },
    # ----- M: the TMDL/M corpus ------------------------------------
    "tmdl_partitions": {
        "reference": "M",
        "status": "extracted",
        "extractor": {"module": "src/mquery/",
                      "entry": "shape census + M mini-parser (ADR 0041)"},
        "targets": ["Report", "r2c", "r2t"],
        "conservation": {
            "home": "shape census (recognized ⊎ unknown) + ops_fallout",
            "check": "SHAPE_REGISTRY census tests; unknown shapes counted, "
                     "escalation per ADR 0045 §3",
        },
    },
    "dax_measures": {
        "reference": "M",
        "status": "extracted",
        "extractor": {"module": "src/steps/semantic_models.py",
                      "entry": "060 ingestion → input_dax_expressions"},
        "targets": ["Measure", "r2m", "m2c"],
        "conservation": {
            "home": "input_dax_expressions + consumption wiring counts",
            "check": "wire_consumption_layer skipped-list surfaced in 300 "
                     "output (consumption_skipped, printed per run)",
        },
    },
    # ----- O: org declarations --------------------------------------
    "metric_business_names": {
        "reference": "O",
        "status": "extracted",
        "extractor": {"module": "src/governance/display_names.py",
                      "entry": "apply_business_names (input_metric_names)"},
        "targets": ["Metric.business_name"],
        "conservation": {
            "home": "300 output business_names_applied/skipped",
            "check": "skipped names printed per run; names merge policy "
                     "handoff tracks the residual",
        },
    },
    # ----- Gov: the governance record (projected, ADR 0031/D3) ------
    "business_terms": {
        # Adversarial audit find (2026-08-19): the spec's Σ listed Term
        # nodes + implements edges as projected "each build" — they are
        # NOT: the gov record exists (gov_business_terms/term_links,
        # ADR 0031) and candidate mining exists
        # (src/governance/business_terms.py), but no graph projection is
        # built. Recorded honestly as an exclusion until it lands.
        "reference": "Gov",
        "status": "excluded",
        "exclusion_reason": (
            "Gov record + mining exist; the Term-node/implements-edge "
            "projection (spec:D3) is NOT yet implemented — becomes an "
            "extracted row when the term-projection builder lands "
            "(pre-1.28 audit would also have flagged this row)."
        ),
    },
    "steward_assignments": {
        "reference": "Gov",
        "status": "extracted",
        "extractor": {"module": "src/governance/steward.py",
                      "entry": "StewardManager.apply_to_graph"},
        "targets": ["Metric.steward"],
        "conservation": {
            "home": "300 output stewards_applied",
            "check": "count printed per run; absence recorded in "
                     "ops_setup_completeness",
        },
    },
    # ----- exclusions (ruled by Sunny 2026-08-19): visible roadmap
    # ----- pressure, never silent scope ------------------------------
    "snowflake_views": {
        "reference": "P",
        "status": "excluded",
        "exclusion_reason": (
            "Fabric-native v1 (Marketplace offering). Hospital adoption "
            "of Snowflake is growing — this row IS the roadmap pressure. "
            "When included, Snowflake gets its own native parser "
            "(ADR 0001), never a universal one."
        ),
    },
    "databricks_dbt_models": {
        "reference": "P",
        "status": "excluded",
        "exclusion_reason": (
            "Fabric-native v1. Same ruling and same dialect law as "
            "snowflake_views; dbt-model lineage additionally needs the "
            "dbt manifest as a reference structure when included."
        ),
    },
    "usage_layer_events": {
        "reference": "Gov",
        "status": "excluded",
        "exclusion_reason": (
            "Usage-weighted edges (ADR 0023/0038) are gated on the "
            "access-control ADR; turn/feedback events are captured "
            "(ops event tables) but not yet projected into the graph. "
            "Becomes an extracted row when the 0046 engine lands."
        ),
    },
    "admin_governance_registries": {
        # spec:C1 applied reflexively (ADR 0048 item 3): the admin
        # graph's source kinds are the registries themselves + the
        # error/checklist event tables.
        "reference": "Gov",
        "status": "extracted",
        "extractor": {"module": "src/admin_graph.py",
                      "entry": "build_admin_graph (registry + event "
                               "projection, spec §14b)"},
        "targets": ["contract", "notebook", "module", "adr", "axiom",
                    "error", "checklist"],
        "conservation": {
            "home": "ops_admin_graph_nodes + ops_admin_graph_edges "
                    "(rebuilt each run — a projection, spec:D3)",
            "check": "tests/test_admin_graph.py — every registry entry "
                     "projects to a node; every edge endpoint exists",
        },
    },
}
