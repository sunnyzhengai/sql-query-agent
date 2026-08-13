"""Pipeline validation — checks each metric through every pipeline step.

Verifies that each metric successfully traversed:
1. Loaded into sql_sources
2. Parsed successfully
3. Has a canonical node in the graph
4. Has transformation nodes
5. Has edges connecting layers
6. Is traversable to technical nodes
"""

from __future__ import annotations


def validate_pipeline_per_metric(
    sql_source_ids: list[str],
    parse_ok_ids: set[str],
    nodes: dict[str, dict],
    edges_by_source: dict[str, list[dict]],
) -> list[dict]:
    """Validate each metric through every pipeline step.

    Args:
        sql_source_ids: list of metric_ids from sql_sources
        parse_ok_ids: set of metric_ids from parse_successes
        nodes: dict of node_id -> node row dict (from graph_nodes)
        edges_by_source: dict of source_id -> list of edge row dicts

    Returns:
        List of validation result dicts, one per metric.
    """
    results = []

    for mid in sql_source_ids:
        step1_loaded = True
        step2_parsed = mid in parse_ok_ids

        canonical_id = f"canonical:{mid}"
        step3_canonical = canonical_id in nodes

        transform_nodes = [nid for nid in nodes if nid.startswith(f"transform:{mid}:")]
        step4_transforms = len(transform_nodes) > 0

        c2t_edges = edges_by_source.get(canonical_id, [])
        c2t_count = len([e for e in c2t_edges if e["edge_type"] == "canonical_to_transform"])
        step5_edges = c2t_count > 0

        # Step 6 is a REAL walk (fixed 2026-08-13 — the shallow 2-hop
        # check was ADR 0018's disease in a second location: a metric
        # whose entry transform assembles only from temp tables showed
        # zero direct table edges and false-negatived, while its chain
        # reached dozens. Found by the admin dashboard's first render.)
        tech_reachable = 0
        if step5_edges:
            visited: set = set()
            stack = [canonical_id]
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.add(nid)
                for e in edges_by_source.get(nid, []):
                    if e["edge_type"] == "transform_to_technical":
                        tech_reachable += 1
                    elif e["edge_type"] in ("canonical_to_transform",
                                            "transform_to_transform"):
                        stack.append(e["target_id"])
        step6_traversal = tech_reachable > 0

        results.append({
            "metric_id": mid,
            "step1_loaded": step1_loaded,
            "step2_parsed": step2_parsed,
            "step3_canonical": step3_canonical,
            "step4_transforms": step4_transforms,
            "step5_edges": step5_edges,
            "step6_traversal": step6_traversal,
            "transform_count": len(transform_nodes),
            "edge_count": c2t_count,
            "tech_reachable": tech_reachable,
        })

    return results


def summarize_validation(results: list[dict]) -> dict[str, int]:
    """Summarize validation results into step counts.

    Returns dict with keys: total, s1-s6 counts.
    """
    total = len(results)
    return {
        "total": total,
        "s1_loaded": sum(1 for r in results if r["step1_loaded"]),
        "s2_parsed": sum(1 for r in results if r["step2_parsed"]),
        "s3_canonical": sum(1 for r in results if r["step3_canonical"]),
        "s4_transforms": sum(1 for r in results if r["step4_transforms"]),
        "s5_edges": sum(1 for r in results if r["step5_edges"]),
        "s6_traversal": sum(1 for r in results if r["step6_traversal"]),
    }
