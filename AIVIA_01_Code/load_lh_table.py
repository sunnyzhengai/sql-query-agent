# load_lh_table.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/01_subject_sql_files.md — F11: Notebook loads
#           the data sheet json from Files into lakehouse table
#           01_subject_sql_files_lh_table.
# Contract: AIVIA_01_Design/01_subject_sql_files_data_contract.md
# Tests:    AIVIA_01_Test/test_01_load_lh_table.py (red first)
#
# SHAPE — the standing pattern (design doc last line): the notebook is a
# THIN CALLER; the logic lives here, in the wheel, tested locally. Spark
# exists only in Fabric, so the split is:
#     this module  = everything testable without Spark
#                    (read the sheet, validate it, shape the rows)
#     the notebook = three lines (below): call this module, make the
#                    dataframe, save the table
#
# ONE public function:
#
#     to_table_rows(sheet_path)
#         Read the data sheet json at sheet_path (locally a repo path;
#         in Fabric the /lakehouse/.../Files path — a PARAMETER, never
#         written in here).
#         VALIDATE before anything ships to a table — fail loudly,
#         naming the offending file, if any row has:
#           - missing/extra columns (the contract's four, in order)
#           - blank database_name or schema_name
#           - an embedding that is not exactly 3072 numbers
#         (The gate the local tests enforce, enforced AGAIN at the
#         door of production — a hand-edited sheet can't sneak in.)
#         RETURN the rows renamed to camelCase column names:
#             fileName, databaseName, schemaName, fileNameEmbedding
#
# THE camelCase DECISION (Sunny to confirm): this table's whole purpose
# is feeding the graph model (next design step: names + embeddings as
# node properties). The earlier sql-query-agent work found that Fabric
# Graph's natural-language querying REQUIRES camelCase column names in
# the tables it loads from — snake_case broke it. Renaming at this door
# costs nothing now and spares a rebuild later. The data sheet itself
# stays snake_case — the contract's names don't change; only the
# lakehouse table speaks camelCase.
#
# THE NOTEBOOK (F11) — Sunny creates a notebook in the AIVIA_01
# workspace, attaches the AIVIA_01_ENV environment (that's what makes
# `import load_lh_table` work — the aivia01 wheel is in it), attaches
# the AIVIA_01_LH lakehouse as default, and pastes exactly this one cell:
#
#     from load_lh_table import to_table_rows
#
#     rows = to_table_rows(
#         "/lakehouse/default/Files/Data/01_subject_sql_files/"
#         "01_subject_sql_files_data_sheet.json"
#     )
#     df = spark.createDataFrame(rows)
#     df.write.mode("overwrite").saveAsTable("f01_subject_sql_files_lh_table")
#     df.drop("fileNameEmbedding").write.mode("overwrite") \
#         .saveAsTable("f01_subject_sql_files_graph")
#
#     Overwrite mode: the sheet is the truth; rerunning the notebook
#     replaces the tables wholesale, never appends duplicates.
#
#     THE GRAPH EXPORT TABLE, RULED 2026-09-27 (found live at F12/F13):
#     the graph model cannot hold the 3072-number embedding array as a
#     node property — the mapping UI shows the column typed "?", and
#     loads of the full table died (SystemError1009). RULED: the graph
#     reads its OWN embedding-free table, f01_subject_sql_files_graph
#     (fileName/databaseName/schemaName only) — the drop line above —
#     and embeddings STAY in f01_subject_sql_files_lh_table; a chat
#     embeds the question and reads embeddings from the lakehouse table,
#     the graph serves structure. (The old project's graph_* export-table
#     pattern and Delta-for-search / graph-for-traversal verdict, met
#     again.) NOTE: at ruling time even the clean 3-column load still
#     failed with the service's transient 1009 on trial capacity — a
#     Fabric-side fault under support/retry, not a mapping error.
#     THE NAME, RULED 2026-09-27: the leading-digit risk called out here
#     BIT in T-SQL, not Spark — "select * from 01_..." dies with
#     "Incorrect syntax near '01'", and every SQL consumer would need
#     [brackets] forever. Sunny renamed the table f01_... (letter first,
#     keeps the step numbering) and reran; design doc F11 carries it.
#
# THE WHEEL RIDES AGAIN: pyproject.toml gains this module in py-modules
# and bumps version 0.1.0 -> 0.2.0. After Sunny approves and tests are
# green, shipping = her F10 command again (sync_wheel), then she runs
# the notebook — her eye on the table is F11's acceptance test.
#
# TESTS (test_01_load_lh_table.py, red first) — locally pinned:
#   - to_table_rows on the REAL sheet returns 8 rows, camelCase keys,
#     embeddings intact (3072 numbers, same first values as the sheet)
#   - a sheet with a blank schema_name -> loud ValueError naming the file
#   - a sheet with a short embedding -> loud ValueError naming the file
#   - a sheet with wrong columns -> loud ValueError naming the file
#   - the built wheel contains load_lh_table.py (extends the existing
#     wheel test) and pyproject says 0.2.0
#   The Spark lines are NOT pytest-able locally (no Spark here); their
#   acceptance test is Sunny's notebook run and her eye on the table.

import json
from pathlib import Path

EMBEDDING_LENGTH = 3072
SHEET_COLUMNS = ["file_name", "database_name", "schema_name", "file_name_embedding"]


def to_table_rows(sheet_path):
    sheet_path = Path(sheet_path)
    with open(sheet_path, encoding="utf-8") as f:
        rows = json.load(f)

    problems = []
    for i, row in enumerate(rows):
        name = row.get("file_name") or f"<row {i} without file_name>"
        if list(row.keys()) != SHEET_COLUMNS:
            problems.append(
                f"{name}: columns {list(row.keys())}, contract requires {SHEET_COLUMNS}"
            )
            continue
        if not str(row["database_name"]).strip():
            problems.append(f"{name}: blank database_name")
        if not str(row["schema_name"]).strip():
            problems.append(f"{name}: blank schema_name")
        emb = row["file_name_embedding"]
        if (
            not isinstance(emb, list)
            or len(emb) != EMBEDDING_LENGTH
            or not all(isinstance(x, (int, float)) for x in emb)
        ):
            problems.append(
                f"{name}: embedding is not {EMBEDDING_LENGTH} numbers"
            )
    if problems:
        raise ValueError(
            f"data sheet {sheet_path} is not fit for the lakehouse table:\n  "
            + "\n  ".join(problems)
        )

    return [
        {
            "fileName": row["file_name"],
            "databaseName": row["database_name"],
            "schemaName": row["schema_name"],
            "fileNameEmbedding": row["file_name_embedding"],
        }
        for row in rows
    ]
