# build_data_sheet.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Contract: AIVIA_01_Design/01_subject_sql_files_data_contract.md
# Tests:    AIVIA_01_Test/test_01_subject_sql_files_data_contract.py
#
# One public function:
#
#     build_data_sheet(sql_dir, sheet_path, embedder)
#
#     sql_dir    — folder holding the subject sql files
#                  (local: AIVIA_01_Data/01_subject_sql_files/,
#                   production: the lakehouse Files path — passed in, never
#                   written inside this file, per the design doc)
#     sheet_path — where the JSON data sheet is written
#     embedder   — a function: list of names -> list of embeddings.
#                  The real one calls OpenAI text-embedding-3-large
#                  (3072 numbers per embedding, key from .env).
#                  It is passed IN so the same code runs locally and in
#                  Fabric; this file never reads the key itself.
#
# PSEUDO CODE
#
# Step 1 — list the sql files in sql_dir.
#     Keep every visible file. Skip hidden files (names starting with ".")
#     and skip .json files, so the data sheet sitting in the same folder
#     is never counted as a subject file. (Same rule the tests use.)
#
# Step 2 — read the existing sheet at sheet_path, if there is one.
#     Parse the JSON list and index the rows by file_name.
#     If the file does not exist, start with no existing rows.
#
# Step 3 — decide each row of the new sheet, one per file from Step 1.
#     For a file that already has a row:
#         keep its database_name and schema_name exactly as stored
#         (contract line 45: never overwrite Sunny's hand-filled values).
#         Keep its stored embedding too, IF it is a valid list of 3072
#         numbers — the file name did not change, so the embedding is
#         still correct, and we do not spend a paid API call re-embedding
#         the same name. Otherwise treat the embedding as missing.
#     For a file with no row (new file):
#         database_name = ""   (blank, for Sunny to fill)
#         schema_name  = ""    (blank, for Sunny to fill)
#         embedding    = missing (computed in Step 4)
#     A row whose file no longer exists in the folder is dropped —
#     the sheet mirrors the folder exactly, both directions.
#
# Step 4 — embed the names that are missing an embedding.
#     Collect all file names from Step 3 with a missing embedding.
#     If there are any, make ONE call: embedder(those names) — a single
#     batch, not one call per name. Put each returned embedding into
#     its row. If there are none, no API call happens at all.
#
# Step 5 — write the sheet to sheet_path.
#     A JSON list of rows, each row with exactly these keys in this
#     order (contract lines 27-31):
#         file_name, database_name, schema_name, file_name_embedding
#     Rows sorted by file_name so rebuilds are deterministic.
#     Written with indent=2, utf-8 — readable when Sunny opens it.
#
# Step 6 — fail loudly on blanks, AFTER writing.
#     Look through the rows just written. If any row has a blank
#     database_name or schema_name, raise ValueError with a message
#     naming EVERY unfilled file (contract lines 42-43, 45).
#     The order matters: the sheet is written first so that on a first
#     build Sunny has the file on disk to fill in, and the error tells
#     her exactly which rows need her hand.
#
# No command-line part in this step. The tests (and later the Fabric
# notebook) call build_data_sheet directly with their own paths and
# their own embedder.

import json
from pathlib import Path

# Contract lines 60-62: text-embedding-3-large, 3072 numbers per embedding.
EMBEDDING_LENGTH = 3072

COLUMNS = ["file_name", "database_name", "schema_name", "file_name_embedding"]


def _is_valid_embedding(value):
    return (
        isinstance(value, list)
        and len(value) == EMBEDDING_LENGTH
        and all(isinstance(x, (int, float)) for x in value)
    )


def build_data_sheet(sql_dir, sheet_path, embedder):
    sql_dir = Path(sql_dir)
    sheet_path = Path(sheet_path)

    # Step 1 — list the sql files.
    file_names = sorted(
        p.name
        for p in sql_dir.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix != ".json"
    )

    # Step 2 — read the existing sheet, if there is one.
    existing = {}
    if sheet_path.exists():
        with open(sheet_path, encoding="utf-8") as f:
            existing = {row["file_name"]: row for row in json.load(f)}

    # Step 3 — decide each row; rows for deleted files are dropped by
    # building only from file_names.
    rows = []
    names_to_embed = []
    for name in file_names:
        old = existing.get(name, {})
        embedding = old.get("file_name_embedding")
        if not _is_valid_embedding(embedding):
            embedding = None
            names_to_embed.append(name)
        rows.append(
            {
                "file_name": name,
                "database_name": old.get("database_name", ""),
                "schema_name": old.get("schema_name", ""),
                "file_name_embedding": embedding,
            }
        )

    # Step 4 — one batched call for every name missing an embedding.
    if names_to_embed:
        embeddings = embedder(names_to_embed)
        by_name = dict(zip(names_to_embed, embeddings))
        for row in rows:
            if row["file_name_embedding"] is None:
                row["file_name_embedding"] = by_name[row["file_name"]]

    # Step 5 — write the sheet (rows already sorted by file_name).
    with open(sheet_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    # Step 6 — fail loudly on blanks, AFTER writing.
    unfilled = [
        row["file_name"]
        for row in rows
        if not str(row["database_name"]).strip() or not str(row["schema_name"]).strip()
    ]
    if unfilled:
        raise ValueError(
            "database_name/schema_name blank — Sunny must fill these rows in "
            f"{sheet_path}: {', '.join(unfilled)}"
        )
