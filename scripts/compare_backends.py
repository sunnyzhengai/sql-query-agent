"""Compare Delta vs Fabric Graph backends on real data.

Run this in a Fabric Notebook or locally with explicit tokens.
Iterates all canonical metrics, calls get_metric_subgraph on both
backends, and reports diffs.

Usage in Fabric Notebook:
    %run scripts/compare_backends.py

Usage locally (requires access tokens):
    python scripts/compare_backends.py --workspace-id WID --graph-model-id GID --token TOKEN
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph.delta_backend import DeltaBackend
from src.graph.fabric_graph_backend import FabricGraphBackend
from src.graph.gql_client import GQLClient


def compare_subgraphs(
    result_a: dict, result_b: dict, metric_id: str,
) -> dict:
    """Compare two subgraph results and return a diff report."""
    if not result_a and not result_b:
        return {"metric_id": metric_id, "status": "both_empty"}
    if not result_a:
        return {"metric_id": metric_id, "status": "missing_delta"}
    if not result_b:
        return {"metric_id": metric_id, "status": "missing_graph"}

    diffs = {}

    # Compare transform nodes
    t_ids_a = {t.node_id for t in result_a["transformations"]}
    t_ids_b = {t.node_id for t in result_b["transformations"]}
    if t_ids_a != t_ids_b:
        diffs["transforms_only_delta"] = sorted(t_ids_a - t_ids_b)
        diffs["transforms_only_graph"] = sorted(t_ids_b - t_ids_a)

    # Compare technical nodes
    tech_ids_a = {t.node_id for t in result_a["technical"]}
    tech_ids_b = {t.node_id for t in result_b["technical"]}
    if tech_ids_a != tech_ids_b:
        diffs["technical_only_delta"] = sorted(tech_ids_a - tech_ids_b)
        diffs["technical_only_graph"] = sorted(tech_ids_b - tech_ids_a)

    # Compare dimensions
    dim_ids_a = {t.node_id for t in result_a["dimensions"]}
    dim_ids_b = {t.node_id for t in result_b["dimensions"]}
    if dim_ids_a != dim_ids_b:
        diffs["dimensions_only_delta"] = sorted(dim_ids_a - dim_ids_b)
        diffs["dimensions_only_graph"] = sorted(dim_ids_b - dim_ids_a)

    return {
        "metric_id": metric_id,
        "status": "match" if not diffs else "diff",
        "transforms_delta": len(t_ids_a),
        "transforms_graph": len(t_ids_b),
        "technical_delta": len(tech_ids_a),
        "technical_graph": len(tech_ids_b),
        **diffs,
    }


def run_comparison(delta: DeltaBackend, graph: FabricGraphBackend) -> None:
    """Run full comparison across all metrics and print results."""
    delta_metrics = set(delta.list_canonical_metrics())
    graph_metrics = set(graph.list_canonical_metrics())

    all_metrics = sorted(delta_metrics | graph_metrics)

    print(f"\n{'='*70}")
    print(f"Backend Comparison: {len(all_metrics)} metrics")
    print(f"  Delta only: {sorted(delta_metrics - graph_metrics)}")
    print(f"  Graph only: {sorted(graph_metrics - delta_metrics)}")
    print(f"{'='*70}\n")

    match_count = 0
    diff_count = 0
    results = []

    for metric_id in all_metrics:
        result_delta = delta.get_metric_subgraph(metric_id)
        result_graph = graph.get_metric_subgraph(metric_id)
        report = compare_subgraphs(result_delta, result_graph, metric_id)
        results.append(report)

        status = report["status"]
        if status == "match":
            match_count += 1
            print(f"  MATCH  {metric_id}")
        else:
            diff_count += 1
            diff = {k: v for k, v in report.items() if k not in ("metric_id", "status")}
            print(f"  DIFF   {metric_id}: {json.dumps(diff, indent=2)}")

    print(f"\n{'='*70}")
    print(f"Results: {match_count} match, {diff_count} diff, {len(all_metrics)} total")
    print(f"{'='*70}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Compare Delta vs Fabric Graph backends")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    parser.add_argument("--graph-model-id", required=True, help="Fabric Graph Model ID")
    parser.add_argument("--token", required=True, help="Bearer token for Fabric API")
    parser.add_argument("--sample-data", action="store_true", help="Use sample seed data instead of Delta tables")
    args = parser.parse_args()

    # Build delta backend
    if args.sample_data:
        from scripts.seed_sample_data import SAMPLE_DICT_COLUMNS, SAMPLE_DICT_TABLES, SAMPLE_SQL_SOURCES
        from src.pipeline import build_graph
        builder = build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)
        delta = DeltaBackend(builder.nodes, builder.edges)
    else:
        print("ERROR: Non-sample mode requires Spark context. Run this in a Fabric Notebook.")
        sys.exit(1)

    # Build graph backend
    client = GQLClient(args.workspace_id, args.graph_model_id, access_token=args.token)
    graph = FabricGraphBackend(client)

    run_comparison(delta, graph)


if __name__ == "__main__":
    main()
