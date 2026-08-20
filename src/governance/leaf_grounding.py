"""Leaf grounding — spec:C4, the termination axiom, as a computed verdict.

    ∀f ∈ P.  ∀ℓ ∈ leaves(tree(f)).   ℓ ∈ T_D ∪ T_org   ∨   ℓ ∈ fallout(f)
    completely_parsed(f)  ⟺  fallout(f) = ∅

After internal references resolve (CTEs and temp tables resolve to
their defining steps — the parser already did that), every remaining
PHYSICAL leaf of every parsed file must bottom out on a dictionary
table: vendor (T_D) or org reference (T_org, ORIGIN column). Anything
else is a counted, escalated fallout row — and "completely parsed" is
a computed per-file verdict, never an impression.

Origin: Sunny's blind reconstruction (2026-08-19): "any AST tree branch
that does not end in EMR tables or org's custom reference table is not
a completely parsed sql file."
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from src.parser.identity import fold_identifier

FALLOUT_STAGE = "500_leaf_grounding"
CONTRACT_ID = "contract:input_dict_tables"


@dataclass
class LeafGroundingResult:
    total_files: int = 0
    grounded_files: int = 0
    verdicts: "list[dict]" = field(default_factory=list)   # per metric
    fallout_rows: "list[dict]" = field(default_factory=list)

    @property
    def fraction_grounded(self) -> float:
        return self.grounded_files / self.total_files if self.total_files else 1.0


def _physical_leaves(parse_row: dict) -> "set[str]":
    """Every physical table name a parsed file's tree bottoms out on —
    step-level reads plus final-select reads (temp/CTE references were
    already resolved to steps by the parser and are not leaves)."""
    leaves: "set[str]" = set()
    for cte in json.loads(parse_row.get("ctes_json") or "[]"):
        for ref in cte.get("table_refs") or []:
            leaves.add(ref["table"])
    for ref in json.loads(parse_row.get("final_select_tables") or "[]"):
        leaves.add(ref["table"])
    return leaves


def leaf_grounding(parse_results_rows: "list[dict]",
                   dict_table_rows: "list[dict]",
                   run_at: str = "") -> LeafGroundingResult:
    """The C4 verdict per parsed file. Matching is case-insensitive and
    schema-agnostic (ADR 0016), same as graph binding."""
    known = {fold_identifier(r["TABLE_NAME"]) for r in dict_table_rows}
    result = LeafGroundingResult()
    for row in parse_results_rows:
        metric_id = row["metric_id"]
        ungrounded = sorted({
            leaf for leaf in _physical_leaves(row)
            if fold_identifier(leaf) not in known
        })
        result.total_files += 1
        grounded = not ungrounded
        if grounded:
            result.grounded_files += 1
        result.verdicts.append({
            "metric_id": metric_id,
            "completely_parsed": grounded,
            "ungrounded_leaves": ungrounded,
        })
        if ungrounded:
            result.fallout_rows.append({
                "run_at": run_at,
                "stage": FALLOUT_STAGE,
                "entity_id": metric_id,
                "reason_code": "ungrounded_leaf",
                "reason_text": (
                    "tree branches do not terminate on T_D ∪ T_org: "
                    + ", ".join(ungrounded[:20])
                    + (" …" if len(ungrounded) > 20 else "")
                    + " — add to the dictionary (ORIGIN=org for org "
                      "reference tables) or record why not"),
                "contract_id": CONTRACT_ID,
                "resolution": "escalated",  # novelty always escalates (H2)
            })
    return result


def grounding_lines(result: LeafGroundingResult) -> "list[str]":
    """Human summary for 500's output — the funnel's new honest number."""
    lines = [
        f"Leaf grounding (spec:C4): {result.grounded_files}/"
        f"{result.total_files} files completely parsed "
        f"({result.fraction_grounded:.0%})"
    ]
    for v in result.verdicts:
        if not v["completely_parsed"]:
            heads = ", ".join(v["ungrounded_leaves"][:5])
            more = len(v["ungrounded_leaves"]) - 5
            lines.append(f"  [!] {v['metric_id']}: {heads}"
                         + (f" (+{more} more)" if more > 0 else ""))
    return lines
