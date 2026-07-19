"""Run the full pipeline with real Clarity SQL queries.

Parse SQL files → build graph → generate metadata records → save output.

Usage:
    python3 scripts/run_full_pipeline.py
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.dictionary import DataDictionary
from src.graph.builder import GraphBuilder
from src.graph.traversal import GraphTraverser
from src.parser.sql_parser import parse_sql
from src.adapters.metadata_generator import generate_all_records

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "output"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_lines = []

    def log(msg=""):
        print(msg)
        output_lines.append(msg)

    # Step 1: Load data dictionary
    log("=" * 70)
    log("STEP 1: Load Data Dictionary")
    log("=" * 70)

    with open(SAMPLE_DIR / "clarity_dict_tables.json") as f:
        dict_tables = json.load(f)

    # We don't have column-level dictionary for Clarity yet — use empty
    dict_columns = []

    dictionary = DataDictionary()
    for row in dict_tables:
        dictionary.add_table(row["TABLE_NAME"], row.get("DESCRIPTION", ""))

    log(f"Loaded {len(dict_tables)} table descriptions")
    log()

    # Step 2: Load and parse SQL sources
    log("=" * 70)
    log("STEP 2: Parse SQL Sources")
    log("=" * 70)

    with open(SAMPLE_DIR / "clarity_sql_sources.json") as f:
        sql_sources_meta = json.load(f)

    sql_sources = []
    for meta in sql_sources_meta:
        sql_path = SAMPLE_DIR / meta["sql_file"]
        with open(sql_path) as f:
            sql = f.read()
        sql_sources.append({
            "metric_id": meta["metric_id"],
            "name": meta["name"],
            "sql": sql,
            "steward": meta.get("steward"),
            "developer": meta.get("developer"),
        })
        log(f"Loaded: {meta['metric_id']} ({meta['name']}) from {meta['sql_file']}")

    log()

    # Step 3: Build graph
    log("=" * 70)
    log("STEP 3: Build Graph")
    log("=" * 70)

    builder = GraphBuilder()

    # Create technical nodes from dictionary
    for table_name, table_info in dictionary.tables.items():
        builder.add_technical_node(table_name, description=table_info.description)

    log(f"Created {len(builder.nodes)} technical nodes from dictionary")

    # Process each SQL source
    for source in sql_sources:
        metric_id = source["metric_id"]
        name = source["name"]
        sql = source["sql"]
        steward = source.get("steward")
        developer = source.get("developer")

        log(f"\nProcessing: {metric_id} ({name})")

        # Create canonical node
        builder.add_canonical_node(metric_id, name, steward=steward, developer=developer)

        # Parse SQL and wire transformation + technical edges
        parsed = parse_sql(sql)
        builder.build_from_parsed_sql(metric_id, parsed)

        log(f"  CTEs: {len(parsed.ctes)}")
        for cte in parsed.ctes:
            log(f"    {cte.name} -> {cte.table_refs}")
        log(f"  Final tables: {len(parsed.final_select_tables)}")
        log(f"  Final columns: {len(parsed.final_select_columns)}")

    log()

    # Step 4: Graph summary
    log("=" * 70)
    log("STEP 4: Graph Summary")
    log("=" * 70)

    layer_counts = Counter(n.layer.value for n in builder.nodes.values())
    edge_type_counts = Counter(e.edge_type.value for e in builder.edges)

    log(f"Total nodes: {len(builder.nodes)}")
    log("Nodes by layer:")
    for layer, count in sorted(layer_counts.items()):
        log(f"  {layer}: {count}")
    log(f"Total edges: {len(builder.edges)}")
    log("Edges by type:")
    for etype, count in sorted(edge_type_counts.items()):
        log(f"  {etype}: {count}")
    log()

    # Step 5: Test traversal
    log("=" * 70)
    log("STEP 5: Traversal Test")
    log("=" * 70)

    traverser = GraphTraverser(builder.nodes, builder.edges)

    for source in sql_sources:
        metric_id = source["metric_id"]
        subgraph = traverser.get_metric_subgraph(metric_id)
        if subgraph:
            canonical = subgraph["canonical"]
            log(f"\nMetric: {canonical.name} ({metric_id})")
            log(f"  Steward: {canonical.properties.get('steward', 'N/A')}")
            log(f"  Developer: {canonical.properties.get('developer', 'N/A')}")
            log(f"  Transformation steps: {len(subgraph['transformations'])}")
            for t in subgraph["transformations"]:
                log(f"    - {t.name}")
            log(f"  Technical tables: {len(subgraph['technical'])}")
            for t in subgraph["technical"]:
                if t.properties.get("column") is None:
                    log(f"    - {t.name}: {t.description[:60]}..." if len(t.description) > 60 else f"    - {t.name}: {t.description}")
            log(f"  SQL fragments: {len(subgraph['sql_fragments'])}")
        else:
            log(f"\nMetric: {metric_id} — no graph path found")

    log()

    # Step 6: Generate metadata records
    log("=" * 70)
    log("STEP 6: Metadata Records (for Purview/Collibra)")
    log("=" * 70)

    records = generate_all_records(builder)
    log(f"Total metadata records: {len(records)}")

    record_types = Counter(r.asset_type for r in records)
    for rtype, count in sorted(record_types.items()):
        log(f"  {rtype}: {count}")

    log()
    for r in records:
        log(f"--- Record: {r.asset_id} ---")
        log(f"  Type: {r.asset_type}")
        log(f"  Name: {r.name}")
        log(f"  Owner: {r.owner or '(none)'}")
        log(f"  Description:")
        for line in r.description.split("\n"):
            log(f"    {line}")
        if r.properties.get("source_tables"):
            log(f"  Source tables: {r.properties['source_tables']}")
        if r.properties.get("transform_steps"):
            log(f"  Transform steps: {r.properties['transform_steps']}")
        log()

    # Step 7: Save graph output
    log("=" * 70)
    log("STEP 7: Save Output")
    log("=" * 70)

    nodes_out = [
        {
            "node_id": n.node_id,
            "layer": n.layer.value,
            "name": n.name,
            "description": n.description,
            "properties": n.properties,
        }
        for n in builder.nodes.values()
    ]

    edges_out = [
        {
            "source_id": e.source_id,
            "target_id": e.target_id,
            "edge_type": e.edge_type.value,
            "properties": e.properties,
        }
        for e in builder.edges
    ]

    with open(OUTPUT_DIR / "clarity_graph_nodes.json", "w") as f:
        json.dump(nodes_out, f, indent=2, default=str)
    log(f"Wrote {len(nodes_out)} nodes to clarity_graph_nodes.json")

    with open(OUTPUT_DIR / "clarity_graph_edges.json", "w") as f:
        json.dump(edges_out, f, indent=2, default=str)
    log(f"Wrote {len(edges_out)} edges to clarity_graph_edges.json")

    metadata_out = [
        {
            "asset_id": r.asset_id,
            "asset_type": r.asset_type,
            "name": r.name,
            "description": r.description,
            "owner": r.owner,
            "properties": r.properties,
        }
        for r in records
    ]

    with open(OUTPUT_DIR / "clarity_metadata_records.json", "w") as f:
        json.dump(metadata_out, f, indent=2, default=str)
    log(f"Wrote {len(metadata_out)} metadata records to clarity_metadata_records.json")

    # Save the full log
    with open(OUTPUT_DIR / "full_pipeline_results.txt", "w") as f:
        f.write("\n".join(output_lines))
    log(f"\nFull results saved to data/output/full_pipeline_results.txt")


if __name__ == "__main__":
    main()
