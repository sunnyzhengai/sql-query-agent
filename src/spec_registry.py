"""SPEC_REGISTRY — the axiom ledger as data (ADR 0067, turn 1).

The eighth peer registry: one record per SPEC.md axiom. Single-writer
effects: trace_registry derives SPEC_AXIOMS and SPEC_TO_AXM from here
(two hand-maintained structures retired); per-axiom checks are data.

Field discipline (the single-home rule, ADR 0067):
- parents: the framework axioms (docs/AI_VIA_AXIOMS.md) this applies —
  THE home (the crosswalk doc narrates, this decides).
- checks: the file paths SPEC.md's Binding: line names. Where SPEC
  names no file, checks is empty and `reason` quotes the prose binding
  — faithful to the document, never an invented attribution. The count
  of file-less bindings is thereby measurable debt.
- law formulas and per-axiom STATUS stay in SPEC.md, their one home,
  until a later ratchet turn retires that prose into ADRs. Copying
  them here now would mint a second truth.

Grounding ADRs are DERIVED (trace_registry axioms fields), not stored.
Closure checks: tests/test_spec_registry.py (totality both ways
against SPEC.md, check-path existence, parent validity, checks-or-
reason totality).
"""

from __future__ import annotations

GROUPS = {
    "A": "Identity", "B": "Soundness", "C": "Completeness",
    "D": "Derived structure", "E": "Ask-time determinism",
    "F": "The round trip", "G": "Mechanism uniqueness",
    "H": "Escalation", "L": "The ledger", "P": "The one-mind turn",
    "Q": "Graph topology", "R": "Ask-time interpretation + run boundary",
    "T": "The double-sided function",
}

SPEC_REGISTRY = {
    "A1": {"title": "folding is idempotent", "parents": ["D2"],
           "checks": ["tests/parser/test_identity.py"]},
    "A2": {"title": "metric_id is a key", "parents": ["D3"],
           "checks": ["tests/test_invariants.py",
                      "tests/test_table_contracts.py"]},
    "A3": {"title": "fold-collisions are rejected loudly",
           "parents": ["D2"], "checks": ["tests/test_invariants.py"]},
    "B1": {"title": "witness totality (anti-fabrication)",
           "parents": ["B1"],
           "checks": ["tests/test_invariants.py",
                      "tests/test_tree_contract.py"],
           "reason": "PARTIAL by construction in builders; not yet a "
                     "uniform declared invariant on every edge table"},
    "B2": {"title": "description provenance is total and closed",
           "parents": ["B1", "J4"],
           "checks": ["tests/test_tree_contract.py"]},
    "C1": {"title": "the frontier is enumerated", "parents": ["D1"],
           "checks": ["tests/test_extraction_registry.py"]},
    "C2": {"title": "conservation per extractor", "parents": ["R1"],
           "checks": ["tests/test_tree_contract.py",
                      "tests/mquery/test_mquery.py"]},
    "C3": {"title": "images land in the graph", "parents": ["R1"],
           "checks": ["tests/test_invariants.py"]},
    "C4": {"title": "leaf grounding (termination)",
           "parents": ["R1", "D1"],
           "checks": ["tests/governance/test_leaf_grounding.py"]},
    "D1": {"title": "materialized closures equal the fixpoint",
           "parents": ["D4"],
           "checks": ["tests/test_recorded_pipeline.py"],
           "reason": "oracles ENFORCED; the general closure-vs-live "
                     "diff is UNBOUND (ADR 0037 stated gap)"},
    "D2": {"title": "count oracles", "parents": ["J1"],
           "checks": ["tests/test_recorded_pipeline.py"]},
    "D3": {"title": "projections are functions of the record",
           "parents": ["D3"], "checks": [],
           "reason": "by construction in the builders; no general "
                     "recompute-and-diff check yet (SPEC stated gap)"},
    "E1": {"title": "the path space is finite and enumerable",
           "parents": ["S3"], "checks": ["tests/test_spec_gates.py"]},
    "E2": {"title": "replay determinism for retrieval",
           "parents": ["J2"],
           "checks": ["tests/orchestrator/test_core.py"]},
    "E3": {"title": "the decision typing rule", "parents": ["M5", "J2"],
           "checks": ["tests/test_methodology.py"]},
    "E4": {"title": "pick containment", "parents": ["M5"], "checks": [],
           "reason": "structural pick validation in the orchestrator "
                     "(prose binding, no file named; 0046 re-binds)"},
    "E5": {"title": "filter grounding", "parents": ["B1"],
           "checks": ["tests/test_spec_gates.py"]},
    "E6": {"title": "presentation honesty", "parents": ["B2", "B3"],
           "checks": ["tests/orchestrator/test_core.py",
                      "tests/orchestrator/test_caption_gate.py"]},
    "F": {"title": "the round trip (0044 as equations)",
          "parents": ["J4"], "checks": ["tests/test_tree_contract.py"]},
    "G1": {"title": "one owner per capability", "parents": ["D2"],
           "checks": ["tests/test_capability_registry.py"]},
    "G2": {"title": "sanctioned powers only (Uses \\ S = empty)",
           "parents": ["D2"],
           "checks": ["tests/test_capability_registry.py",
                      "tests/test_native_parser_law.py",
                      "tests/test_notebook_contract.py"]},
    "G3": {"title": "no undeclared power", "parents": ["D2"],
           "checks": ["tests/test_capability_registry.py"]},
    "H1": {"title": "fallout resolution is total and closed",
           "parents": ["R3"],
           "checks": ["tests/test_escalation_contract.py"]},
    "H2": {"title": "novelty always escalates", "parents": ["R3"],
           "checks": ["tests/test_escalation_contract.py"]},
    "L1": {"title": "append-only is declared AND obeyed",
           "parents": ["R4"],
           "checks": ["tests/test_ledger_contract.py",
                      "tests/test_table_contracts.py"]},
    "L2": {"title": "aggregates are derived, never stored",
           "parents": ["R4", "D3"],
           "checks": ["tests/test_ledger_contract.py"]},
    "L3": {"title": "every declaration has a firing mechanism",
           "parents": ["R2"], "checks": ["tests/test_spec_gates.py"],
           "reason": "ENFORCED by citation (0059 Q3 precedent): the "
                     "registry closure checks, funnel, reachability"},
    "P1": {"title": "one conversation decides a turn", "parents": ["M2"],
           "checks": ["tests/orchestrator/test_turn_engine.py"]},
    "P2": {"title": "full tool results persist in one history",
           "parents": ["M2"],
           "checks": ["tests/orchestrator/test_turn_engine.py"]},
    "P3": {"title": "thinking room", "parents": ["M3"],
           "checks": ["tests/orchestrator/test_turn_engine.py"]},
    "P4": {"title": "no question-family casebook", "parents": ["M4"],
           "checks": ["tests/orchestrator/test_turn_engine.py",
                      "tests/test_methodology.py"]},
    "P5": {"title": "honesty at the boundary only", "parents": ["B2"],
           "checks": ["tests/orchestrator/test_turn_engine.py"]},
    "P6": {"title": "failure is observation", "parents": ["M1"],
           "checks": ["tests/orchestrator/test_turn_engine.py"]},
    "Q1": {"title": "accounted connectivity", "parents": ["D1"],
           "checks": ["tests/graph/test_topology.py"]},
    "Q2": {"title": "edge soundness", "parents": ["B1"],
           "checks": ["tests/graph/test_topology.py"]},
    "Q3": {"title": "relative completeness", "parents": ["B3"],
           "checks": [],
           "reason": "ENFORCED by citation — the existing conservation "
                     "asserts predate the axiom (ADR 0059)"},
    "R1": {"title": "parse, never generate", "parents": ["M4", "M5"],
           "checks": ["tests/orchestrator/test_parse_plan.py"]},
    "R2": {"title": "no question types", "parents": ["M4"],
           "checks": ["tests/test_methodology.py"]},
    "R3": {"title": "interpretation confirms before it executes",
           "parents": ["B4"], "checks": ["tests/webapp/test_app.py"]},
    "R4": {"title": "no dead ends", "parents": ["R3"],
           "checks": ["tests/webapp/test_app.py"]},
    "R5": {"title": "certain answers", "parents": ["B3"], "checks": [],
           "reason": "the no-nag boundary in the loop; no general "
                     "multi-reading intersection check (SPEC: PARTIAL)"},
    "R6": {"title": "rows never enter model context", "parents": ["B2"],
           "checks": ["tests/test_run_layer.py"]},
    "R7": {"title": "confirmed SQL only; read-only by construction",
           "parents": ["B4"], "checks": ["tests/test_run_layer.py"]},
    "R8": {"title": "sampling is machine-labelled", "parents": ["B3"],
           "checks": ["tests/test_run_layer.py"]},
    "T0": {"title": "the round-trip law", "parents": ["J4"],
           "checks": [],
           "reason": "instantiated as T1-T3, each with its own judge; "
                     "no single check by design (ADR 0065)"},
    "T1": {"title": "descriptions round-trip (spec:F as family member)",
           "parents": ["J4"], "checks": ["tests/test_tree_contract.py"]},
    "T2": {"title": "SQL stitching round-trips", "parents": ["J4", "B1"],
           "checks": ["tests/test_run_layer.py"],
           "reason": "parseability round-trips; the kappa-equality "
                     "diff is the stated gap, live when stitching ships"},
    "T3": {"title": "definition creation round-trips",
           "parents": ["M5", "J2"], "checks": [],
           "reason": "JUDGED, not tested — the human is the judge by "
                     "construction (SPEC 14d, L3 stratum)"},
}
