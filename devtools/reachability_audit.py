"""Live reachability audit — the drift leg of ADR 0052 under SPEC §3b.

CI enforces the frontier at the ENUM level (a new NodeLayer/EdgeType
without a contract row is a red build before any data exists). This
audit enforces it at the STORE level: run against the live eventhouse,
it fails when reality diverges from the declaration —

  drift        an undeclared node prefix or edge type present in
               graph_nodes/graph_edges (a layer landed without a row)
  conservation the transform equation stops closing:
               transforms = catalog steps ⊎ __final_select__ terminals
               (a REAL step missing from the catalog is a vanished row,
               not an exclusion)

Exit 0 = declaration matches reality; exit 1 = drift, rows named.
Run it after any pipeline rerun or export change.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestrator.tools import CATALOG_KINDS  # noqa: E402
from src.reachability import REACHABILITY  # noqa: E402

# store id-prefix -> NodeLayer value (the graph's short prefixes)
PREFIX_TO_LAYER = {
    "canonical": "canonical",
    "transform": "transformation",
    "tech": "technical",
    "decision": "decision",
    "report": "report",
    "measure": "measure",
}

FINAL_SELECT = "__final_select__"


def undeclared_payloads(node_prefixes: "list[str]",
                        edge_types: "list[str]",
                        catalog_kinds: "list[str]") -> "list[str]":
    """Payloads present in the store with no contract row — each one
    is a layer that landed invisible, the exact accident ADR 0052
    exists to prevent."""
    have = {r["payload"] for r in REACHABILITY}
    node_layers = {p.split(":")[1] for p in have
                   if p.startswith("node:")}
    out = []
    for p in node_prefixes:
        layer = PREFIX_TO_LAYER.get(p)
        if layer is None or layer not in node_layers:
            out.append(f"node prefix {p!r} (layer {layer!r})")
    for et in edge_types:
        if f"edge:{et}" not in have:
            out.append(f"edge type {et!r}")
    for k in catalog_kinds:
        if f"catalog:{k}" not in have:
            out.append(f"catalog kind {k!r}")
    return out


def transform_residual_offenders(uncatalogued_names: "list[str]"
                                 ) -> "list[str]":
    """Uncatalogued transforms that are NOT __final_select__ terminals
    — real steps outside the catalog, i.e. vanished rows."""
    return [n for n in uncatalogued_names if n != FINAL_SELECT]


def main() -> None:
    from devtools.answer_evals import DATABASE, QUERY_URI, _load_dotenv
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    _load_dotenv()
    c = KustoClient(QUERY_URI, DATABASE, az_cli_token_provider(QUERY_URI))

    prefixes = [r["p"] for r in c.run(
        "graph_nodes | extend p = tostring(split(node_id, ':')[0]) "
        "| distinct p", {})]
    edge_types = [r["edge_type"] for r in c.run(
        "graph_edges | distinct edge_type", {})]
    kinds = [r["kind"] for r in c.run(
        "semantic_catalog | distinct ['kind']", {})]

    failures = []
    for u in undeclared_payloads(prefixes, edge_types, kinds):
        failures.append(f"DRIFT: {u} exists in the store with no "
                        "reachability row (ADR 0052)")
    for k in kinds:
        if k not in CATALOG_KINDS:
            failures.append(f"DRIFT: catalog kind {k!r} unknown to "
                            "CATALOG_KINDS")

    n_transforms = c.run(
        "graph_nodes | where node_id startswith 'transform:' | count",
        {})[0]["Count"]
    n_steps = c.run(
        "semantic_catalog | where ['kind'] == 'step' | count",
        {})[0]["Count"]
    residual_names = [r["name"] for r in c.run(
        "graph_nodes | where node_id startswith 'transform:' "
        "| join kind=leftanti (semantic_catalog "
        "| where ['kind'] == 'step' | project node_id) on node_id "
        "| project name", {})]
    offenders = transform_residual_offenders(residual_names)
    print(f"conservation: {n_transforms} transforms = {n_steps} "
          f"catalog steps + {len(residual_names)} {FINAL_SELECT} "
          "terminals")
    if n_transforms != n_steps + len(residual_names):
        failures.append("CONSERVATION: transform equation does not "
                        "close — a third bucket exists")
    for name in offenders:
        failures.append(f"CONSERVATION: transform {name!r} is outside "
                        "the catalog and is not a "
                        f"{FINAL_SELECT} terminal — a vanished step")

    if failures:
        print()
        for f in failures:
            print(f"[X] {f}")
        raise SystemExit(1)
    print("reachability: declaration matches the store — no drift")


if __name__ == "__main__":
    main()
