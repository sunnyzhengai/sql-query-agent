"""The lens registry — catalog-to-implementation closure as data.

CHECK-LENS-D1: the ratified catalog's v1 rows and the implemented
lens set must be the SAME set, both directions — a catalog row with
no implementation is a hope; an implementation off-catalog is an
undeclared reader. Deferred rows stay deferred (the import law keeps
their modules structurally absent).
"""
from typing import Callable, Dict, List

from aivia.graph.metamodel import load as load_registry
from aivia.lenses import census, compliance, decisions, derivation, families

# literal: schema-mirror lenses (readings)
V1_LENSES: Dict[str, Callable] = {
    "ownership": derivation.lens_ownership,
    "authorship": derivation.lens_authorship,
    "version": derivation.lens_version,
    "standing": derivation.lens_standing,
    "current": derivation.lens_current,
    "current-outcome": derivation.lens_current_outcome,
    "staleness": derivation.lens_staleness,
    "decisions(class)": decisions.lens_decisions,
    "degenerate": decisions.lens_degenerate,
    "join-compliance": compliance.lens_join_compliance,
    "relatedness": families.lens_relatedness,
    "working-set": census.lens_working_set,
    "gap-census": census.lens_gap_census,
    "referenced-keys": census.lens_referenced_keys,
}


def d1_closure() -> List[str]:
    catalog = load_registry("lenses").sheets["Catalog_v1"]
    v1_rows = {r["Lens"] for r in catalog if r["v1"] == "yes"}
    implemented = set(V1_LENSES)
    problems = []
    for name in sorted(v1_rows - implemented):
        problems.append(f"catalog v1 row '{name}' has no implementation "
                        "— a rule with no check is a hope")
    for name in sorted(implemented - v1_rows):
        problems.append(f"implemented lens '{name}' is not a catalog v1 "
                        "row — undeclared reader")
    return problems
