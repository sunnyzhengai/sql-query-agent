"""Run the full pipeline locally — no Spark, no Fabric, no cloud cost.

Replays recorded ScriptDom fixtures (tests/fixtures/recorded/, produced by
the export_test_fixtures notebook) through the pure step functions:
build_graph -> metric_logic -> export -> validation -> readiness gate,
with contract invariants and relations checked over the in-memory tables.

Usage:
    python scripts/run_pipeline_local.py                # recorded fixtures
    python scripts/run_pipeline_local.py --sample       # bundled sample data

Exit code 0 = DEPLOYMENT READY, 1 = BLOCKED (or fixtures missing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.governance.validation import summarize_validation, validate_pipeline_per_metric  # noqa: E402
from src.invariants import check_all_invariants  # noqa: E402
from src.steps.build_graph import build_graph_step  # noqa: E402
from src.steps.export import export_step  # noqa: E402
from src.steps.metric_logic import metric_logic_step  # noqa: E402
from src.steps.parse import parse_step  # noqa: E402
from src.steps.readiness import (  # noqa: E402
    dictionary_coverage_threshold,
    readiness_gate,
    tech_table_names,
)

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "recorded"


def load_recorded(fixtures_dir: Path = FIXTURES_DIR):
    """Load recorded ScriptDom fixtures. Returns (parse_results, tables, columns)."""
    parse_results = json.loads((fixtures_dir / "parse_results.json").read_text())
    dict_tables = json.loads((fixtures_dir / "dict_tables.json").read_text())
    dict_columns = json.loads((fixtures_dir / "dict_columns.json").read_text())
    return parse_results, dict_tables, dict_columns


def load_sample():
    """Parse the bundled sample corpus with the local fallback parser."""
    from scripts.seed_sample_data import (
        SAMPLE_DICT_COLUMNS,
        SAMPLE_DICT_TABLES,
        SAMPLE_SQL_SOURCES,
    )
    from src.parser.sql_parser import parse_sql

    out = parse_step(SAMPLE_SQL_SOURCES, parse_sql)
    return out.parse_results, list(SAMPLE_DICT_TABLES), list(SAMPLE_DICT_COLUMNS)


def run_pipeline(parse_results, dict_tables, dict_columns) -> "tuple[bool, list[str]]":
    """Run 03->06 on in-memory rows. Returns (blocked, report_lines)."""
    graph = build_graph_step(parse_results, dict_tables, dict_columns)
    metric_rows = metric_logic_step(graph.nodes_rows, graph.edges_rows)
    exported = export_step(graph.nodes_rows, graph.edges_rows)

    # Stub sources so reference invariants and parse-rate hold in replay
    # (the real SQL deliberately never leaves the tenant).
    sources = [
        {"metric_id": r["metric_id"], "name": r["name"], "sql": "[recorded fixture]",
         "steward": None, "developer": None, "source_type": None,
         "source_schema": None}
        for r in parse_results
    ]

    tables: "dict[str, list[dict]]" = {
        "input_sql_sources": sources,
        "input_dict_tables": dict_tables,
        "input_dict_columns": dict_columns,
        "ops_parse_results": parse_results,
        "graph_nodes": graph.nodes_rows,
        "graph_edges": graph.edges_rows,
        "output_metric_logic": metric_rows,
        **exported,
    }
    def fetch(t, cols):
        return [{c: row.get(c) for c in cols} for row in tables[t]]

    def table_exists(t):
        return t in tables

    nodes_by_id = {r["node_id"]: r for r in graph.nodes_rows}
    edges_by_source: "dict[str, list[dict]]" = {}
    for e in graph.edges_rows:
        edges_by_source.setdefault(e["source_id"], []).append(e)

    results = validate_pipeline_per_metric(
        [s["metric_id"] for s in sources],
        {r["metric_id"] for r in parse_results},
        nodes_by_id,
        edges_by_source,
    )
    summary = summarize_validation(results)
    total = max(summary["total"], 1)
    thresholds = {
        "parse_rate": (summary["s2_parsed"] / total, 0.90, True),
        "calculation_logic": (summary["s4_transforms"] / total, 0.80, True),
        "traversal_coverage": (summary["s6_traversal"] / total, 0.70, False),
        "dictionary_coverage": dictionary_coverage_threshold(
            {r["TABLE_NAME"] for r in dict_tables},
            tech_table_names(graph.nodes_rows),
        ),
    }

    violations = check_all_invariants(fetch, table_exists)
    gate = readiness_gate(thresholds, violations, {}, False)

    lines = [
        f"metrics: {total}  nodes: {graph.node_count}  edges: {graph.edge_count}  "
        f"metric_logic rows: {len(metric_rows)}",
        *gate.lines,
    ]
    return gate.blocked, lines


def main() -> None:
    if "--sample" in sys.argv:
        print("Source: bundled sample corpus (fallback parser)")
        data = load_sample()
    else:
        if not (FIXTURES_DIR / "parse_results.json").exists():
            print(f"No recorded fixtures in {FIXTURES_DIR}.")
            print("Run the export_test_fixtures notebook (repo root) on Fabric once,")
            print("download the files there, or use --sample.")
            raise SystemExit(1)
        manifest = json.loads((FIXTURES_DIR / "manifest.json").read_text())
        print(f"Source: recorded ScriptDom fixtures "
              f"({manifest['parse_results']} metrics, exported {manifest['exported_at'][:10]})")
        data = load_recorded()

    blocked, lines = run_pipeline(*data)
    print()
    for line in lines:
        print(f"  {line}")
    print(f"\n  >>> {'DEPLOYMENT BLOCKED' if blocked else 'DEPLOYMENT READY'} <<<")
    raise SystemExit(1 if blocked else 0)


if __name__ == "__main__":
    main()
