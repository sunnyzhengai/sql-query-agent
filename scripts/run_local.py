"""Run the full pipeline locally using seed sample data.

Usage:
    python scripts/seed_sample_data.py   # generate seed data first
    python scripts/run_local.py          # build graph from seed data
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph.traversal import GraphTraverser
from src.pipeline import build_graph

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"


def main() -> None:
    # Load seed data
    for name in ["dict_tables", "dict_columns", "sql_sources"]:
        path = SAMPLE_DIR / f"{name}.json"
        if not path.exists():
            print(f"ERROR: {path} not found. Run 'python scripts/seed_sample_data.py' first.", file=sys.stderr)
            sys.exit(1)

    with open(SAMPLE_DIR / "dict_tables.json") as f:
        dict_tables = json.load(f)
    with open(SAMPLE_DIR / "dict_columns.json") as f:
        dict_columns = json.load(f)
    with open(SAMPLE_DIR / "sql_sources.json") as f:
        sql_sources = json.load(f)

    # Build graph
    builder = build_graph(dict_tables, dict_columns, sql_sources)

    # Summary
    layer_counts = Counter(n.layer.value for n in builder.nodes.values())
    edge_type_counts = Counter(e.edge_type.value for e in builder.edges)

    print("=== Graph Build Complete ===")
    print(f"Total nodes: {len(builder.nodes)}")
    for layer, count in sorted(layer_counts.items()):
        print(f"  {layer}: {count}")
    print(f"Total edges: {len(builder.edges)}")
    for etype, count in sorted(edge_type_counts.items()):
        print(f"  {etype}: {count}")

    # Test traversal
    print("\n=== Traversal Test ===")
    traverser = GraphTraverser(builder.nodes, builder.edges)
    for source in sql_sources:
        metric_id = source["metric_id"]
        result = traverser.get_metric_subgraph(metric_id)
        if result:
            print(f"\nMetric: {result['canonical'].name} ({metric_id})")
            print(f"  Transformations: {[t.name for t in result['transformations']]}")
            print(f"  Technical tables: {[t.name for t in result['technical']]}")
            print(f"  SQL fragments: {len(result['sql_fragments'])}")
        else:
            print(f"\nMetric: {metric_id} — no graph path found")

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nodes_out = [n.model_dump(mode="json") for n in builder.nodes.values()]
    edges_out = [e.model_dump(mode="json") for e in builder.edges]

    with open(OUTPUT_DIR / "graph_nodes.json", "w") as f:
        json.dump(nodes_out, f, indent=2)
    with open(OUTPUT_DIR / "graph_edges.json", "w") as f:
        json.dump(edges_out, f, indent=2)

    print(f"\nGraph written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
