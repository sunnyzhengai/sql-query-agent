"""ADR 0055 — the shape matrix registry (the ADR 0052 pattern).

Every ratified dimension VALUE must be covered by at least one cell —
instantiated or excluded-with-reason — and CI asserts that totality:
a dimension value can no longer sit silently uncovered, and a new
value added here without a cell fails the build.

The cells themselves live in the generator's manifest (one source of
truth for files + expectations); this module declares the RATIFIED
dimension space (Sunny, 2026-08-24) the manifest must cover.
"""

from __future__ import annotations

# Sunny's ratified dimension set (ADR 0055, D1–D6). Values are the
# coverage obligations; the manifest's `dims` strings must mention
# every one of them somewhere.
DIMENSIONS = {
    "D1_name_relation": ("identical", "cousin", "disjoint"),
    "D2_logic_relation": ("hash_identical", "ws_case_only",
                          "sem_same_syn_diff", "genuinely_different"),
    "D3_scope": ("cte", "temp", "schema_view", "business"),
    "D4_reference_form": ("direct_qualified", "aliased",
                          "via_temp_projection", "unqualified_unique",
                          "unqualified_ambiguous", "wrong_kind"),
    "D5_chain_shape": ("linear", "diamond", "self_reference",
                       "cross_schema_twin"),
    "D6_hygiene": ("dynamic_sql", "multi_statement", "crlf",
                   "phi_literal"),
}


def coverage(manifest: dict) -> "dict[str, list[str]]":
    """dimension value -> cell ids whose dims string mentions it."""
    out: "dict[str, list[str]]" = {}
    for _dim, values in DIMENSIONS.items():
        for v in values:
            out[v] = [c["cell_id"] for c in manifest["cells"]
                      if v in c["dims"] or v.replace("_", ".") in c["dims"]]
    return out


def uncovered(manifest: dict) -> "list[str]":
    return sorted(v for v, cells in coverage(manifest).items()
                  if not cells)
