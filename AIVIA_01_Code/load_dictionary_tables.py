# load_dictionary_tables.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/04_fabric_move.md (M02; decisions 1, 2, 6)
# Contract: AIVIA_01_Design/04_fabric_move_data_contract.md
#           (Output Files 1 and 2)
# Tests:    AIVIA_01_Test/test_04_fabric_move_data_contract.py (born
#           with this build, RED first)
#
# PURPOSE. The Delta loader: turn the local sheets (the truth) into
# lakehouse-table rows — validated, counted to the digit, camelCase at
# the door — plus the derived graph tables. The F11 pattern extended:
# this module is everything testable WITHOUT Spark; the notebook is a
# thin caller (one cell, below); the wheel ships it; Sunny runs the
# notebook; her eye on the tables is the acceptance.
#
# TWO F11-ERA RULINGS CARRY FORWARD (both from live Fabric failures,
# both need their lines added to the 04 contract — Sunny's hand):
#   1. camelCase AT THE DOOR (ruled 2026-09-27; the standing finding:
#      Fabric Graph's natural-language layer requires camelCase column
#      names). ALL nine lakehouse tables speak camelCase — one law, no
#      per-table exceptions. The local sheets stay snake_case; only
#      the lakehouse renames: table_id -> tableId, column_name ->
#      columnName, and so on mechanically.
#   2. THE GRAPH READS EMBEDDING-FREE TABLES (ruled 2026-09-27, found
#      live at F12/F13: a 3,072-number array as a node property broke
#      the graph mapping and the load). The graph model must NOT be
#      declared over dict_tables/dict_columns (they carry embeddings).
#      The loader therefore derives TWO MORE tables the contract
#      should add:
#        graph_table_nodes:  tableId, tableName, databaseName,
#                            schemaName, deprecatedYn
#        graph_column_nodes: columnId, tableId, tableName, columnName,
#                            dataType, deprecatedYn
#      Embeddings stay in dict_tables/dict_columns for the chat; the
#      graph model reads graph_* only (the old export-table pattern,
#      met again).
#
# ---------------------------------------------------------------------
# ONE public function (testable locally, no Spark):
#
#   build_table_rows(dir02, dir03) -> (tables, census)
#     tables: {lakehouse_table_name: [row dicts, camelCase keys]}
#     for ALL ELEVEN tables:
#       dict_tables, dict_columns, dict_joins, dict_values,
#       dict_value_embeddings, dict_no_match, chat_abstract_names,
#       chat_technical_terms (parsed from the md via
#       chat_bot.parse_terms — the one terms door),
#       graph_join_edges, graph_table_nodes, graph_column_nodes
#     - graph_join_edges derives through dictionary_graph.build_graph
#       (the one graph door — fk edges grouped by join_id + the L08
#       rule edges, kind column carrying provenance). column_pairs
#       serialize to a json STRING column (Spark-friendly; the graph
#       model doesn't read pairs; any consumer parses).
#     - VALIDATION BEFORE ANYTHING SHIPS, loud, naming offenders (the
#       local gates enforced AGAIN at the door of production):
#         field sets exactly per contract; no blank descriptions;
#         embeddings exactly 3,072 numbers; value sidecar 1:1 with
#         values; every column's tableId resolves.
#     - THE COUNTS TO THE DIGIT (contract law) — census asserts the
#       golden numbers before returning, build fails loudly otherwise:
#         dict_tables 38, dict_columns 1,618, dict_joins 5,262,
#         dict_values 14,476, dict_value_embeddings 14,476,
#         dict_no_match 1, chat_abstract_names 1,656,
#         chat_technical_terms 9, graph_join_edges 391 (210
#         joinsByFk + 181 joinsByRule), graph_table_nodes 38,
#         graph_column_nodes 1,618.
#       (The golden numbers live as a module constant the 04 tests
#       also pin; a corpus change updates BOTH by hand — never
#       silently.)
#
# ---------------------------------------------------------------------
# THE NOTEBOOK (M02) — Sunny creates it in the AIVIA_01 workspace,
# attaches AIVIA_01_ENV (the wheel) + AIVIA_01_LH, pastes ONE cell:
#
#     from load_dictionary_tables import build_table_rows
#
#     tables, census = build_table_rows(
#         "/lakehouse/default/Files/Data/02_emr_data_dictionary",
#         "/lakehouse/default/Files/Data/03_chat_bot")
#     for name, rows in tables.items():
#         spark.createDataFrame(rows).write.mode("overwrite") \
#             .saveAsTable(name)
#         print(name, spark.table(name).count())
#     print(census)
#
#     Overwrite mode: the local sheets are the truth; a rerun replaces
#     wholesale, never appends (the no-lakehouse-hand-edits drift rule
#     enforced by mechanism).
#     NOTE: build_table_rows reads the json sheets from Files — so the
#     sync step that copies the local sheets to Files precedes the
#     notebook run (the existing Files paths from the 02/03 contracts;
#     they are the TRANSPORT, not the archive — Delta-only ruling
#     stands, Sunny may clear Files after a load or leave them as the
#     next load's input).
#
# ---------------------------------------------------------------------
# THE WHEEL RIDES AGAIN: pyproject py-modules gains
# load_dictionary_tables + its import closure (dictionary_graph,
# chat_bot, build_abstract_names — already local modules), version
# 0.2.0 -> 0.3.0. Shipping = Sunny's sync_wheel command, then the
# notebook; capacity ops (the run, the later graph-model declare) on
# her go, one refresh per batch.
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (test_04_fabric_move_data_contract.py, red first;
# real sheets, zero API cost — this module embeds nothing):
#   - build_table_rows on the REAL local assets returns all eleven
#     tables with the golden counts to the digit.
#   - every key in every row is camelCase (no underscores survive).
#   - dict_tables/dict_columns embeddings intact: 3,072 numbers, first
#     values equal to the sheet's.
#   - graph_table_nodes/graph_column_nodes carry NO embedding fields.
#   - graph_join_edges: 391 rows, kind split 210/181, column_pairs a
#     parseable json string, every edge's endpoints resolve.
#   - a sheet with a blank description / short embedding / missing
#     field -> loud ValueError naming the offender (synthetic copies).
#   - chat_technical_terms rows == the terms md rows (the one door).
#   - the built wheel contains the module and pyproject says 0.3.0
#     (extends the standing wheel test).
#   The Spark lines are not locally pytest-able; their acceptance is
#   Sunny's notebook run, the printed counts, and her eye.

import json
from pathlib import Path

import dictionary_graph
from chat_bot import parse_terms

EMBEDDING_LENGTH = 3072

# The golden numbers — a law, pinned here AND in the 04 tests; a corpus
# change updates both by hand, never silently.
GOLDEN_COUNTS = {
    "dict_tables": 38, "dict_columns": 1618, "dict_joins": 5262,
    "dict_values": 14476, "dict_value_embeddings": 14476,
    "dict_no_match": 1, "chat_abstract_names": 1656,
    "chat_technical_terms": 9, "graph_join_edges": 391,
    "graph_table_nodes": 38, "graph_column_nodes": 1618,
}

ABSTRACT_FIELDS = {"object_kind", "object_id", "object_name",
                   "abstract", "synonyms", "sunny_abstract",
                   "sunny_synonyms"}


def _camel(name):
    head, *rest = name.split("_")
    return head + "".join(part.title() for part in rest)


def _camel_rows(rows):
    return [{_camel(k): v for k, v in row.items()} for row in rows]


def _check_embedding(row, field, label, problems):
    emb = row.get(field)
    if (not isinstance(emb, list) or len(emb) != EMBEDDING_LENGTH
            or not all(isinstance(x, (int, float)) for x in emb)):
        problems.append(f"{label}: {field} is not "
                        f"{EMBEDDING_LENGTH} numbers")


def build_table_rows(dir02, dir03, expected_counts=GOLDEN_COUNTS):
    dir03 = Path(dir03)
    sheets = dictionary_graph.load_sheets(dir02)
    graph = dictionary_graph.build_graph(sheets)
    terms = parse_terms(
        (dir03 / "03_chat_technical_terms.md").read_text(encoding="utf-8"))
    abstracts = json.loads(
        (dir03 / "03_chat_abstract_names.json").read_text(encoding="utf-8"))

    # The local gates, enforced AGAIN at the door of production — loud.
    problems = []
    table_ids = {r["table_id"] for r in sheets["tables"]}
    for r in sheets["tables"]:
        if not str(r["table_description"]).strip():
            problems.append(f"{r['table_name']}: blank table_description")
        _check_embedding(r, "table_name_embedding", r["table_name"],
                         problems)
        _check_embedding(r, "table_description_embedding",
                         r["table_name"], problems)
    for r in sheets["columns"]:
        label = f"{r['table_name']}.{r['column_name']}"
        if not str(r["column_description"]).strip():
            problems.append(f"{label}: blank column_description")
        if r["table_id"] not in table_ids:
            problems.append(f"{label}: table_id does not resolve")
        _check_embedding(r, "column_name_embedding", label, problems)
        _check_embedding(r, "column_description_embedding", label,
                         problems)
    values = sheets["values"] or []
    sidecar = sheets["value_embeddings"] or []
    if ({(v["table_name"], v["code"]) for v in values}
            != {(v["table_name"], v["code"]) for v in sidecar}):
        problems.append("value sidecar is not 1:1 with the value sheet")
    for v in sidecar:
        _check_embedding(v, "meaning_embedding",
                         f"{v['table_name']}:{v['code']}", problems)
    for row in abstracts:
        if set(row) != ABSTRACT_FIELDS:
            problems.append(
                f"abstract row {row.get('object_name')}: fields "
                f"{sorted(row)}")
    if problems:
        raise ValueError(
            "the assets are not fit for the lakehouse (door gate):\n  "
            + "\n  ".join(problems[:20]))

    edge_rows = []
    for e in graph["edges"].values():
        edge_rows.append({
            "edgeKey": e["edge_key"], "kind": e["kind"],
            "sourceTableId": e["source_table_id"],
            "destinTableId": e["destin_table_id"],
            "columnPairs": json.dumps(e["column_pairs"]),
            "rule": e.get("rule"),
            "conditionalC": e.get("conditional_c"),
            "mayBeStaleC": e.get("may_be_stale_c"),
            "isCurrentDataModelYn": e.get("is_current_data_model_yn"),
            "isSupplementalYn": e.get("is_supplemental_yn")})

    tables = {
        "dict_tables": _camel_rows(sheets["tables"]),
        "dict_columns": _camel_rows(sheets["columns"]),
        "dict_joins": _camel_rows(sheets["joins"]),
        "dict_values": _camel_rows(values),
        "dict_value_embeddings": _camel_rows(sidecar),
        "dict_no_match": _camel_rows(sheets["no_match"]),
        "chat_abstract_names": _camel_rows(abstracts),
        "chat_technical_terms": _camel_rows(terms),
        "graph_join_edges": edge_rows,
        "graph_table_nodes": [
            {"tableId": r["table_id"], "tableName": r["table_name"],
             "databaseName": r["database_name"],
             "schemaName": r["schema_name"],
             "deprecatedYn": r["deprecated_yn"]}
            for r in sheets["tables"]],
        "graph_column_nodes": [
            {"columnId": r["column_id"], "tableId": r["table_id"],
             "tableName": r["table_name"],
             "columnName": r["column_name"],
             "dataType": r["data_type"],
             "deprecatedYn": r["deprecated_yn"]}
            for r in sheets["columns"]],
    }

    census = {name: len(rows) for name, rows in tables.items()}
    census["joinsByFk"] = sum(1 for e in edge_rows
                              if e["kind"] == "joins_by_fk")
    census["joinsByRule"] = sum(1 for e in edge_rows
                                if e["kind"] == "joins_by_rule")

    if expected_counts:
        drift = [f"{name}: expected {expected}, found "
                 f"{census.get(name)}"
                 for name, expected in expected_counts.items()
                 if census.get(name) != expected]
        if drift:
            raise ValueError(
                "counts drifted from the golden numbers (update the "
                "law by hand if the corpus changed):\n  "
                + "\n  ".join(drift))
    return tables, census
