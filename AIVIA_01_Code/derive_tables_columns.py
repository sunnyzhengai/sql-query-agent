# derive_tables_columns.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L03 tail)
# Contract: AIVIA_01_Design/02_emr_data_dictionary_data_contract.md
#           (Output File 1 "derived" section; Output File 3)
# Tests:    AIVIA_01_Test/test_02_emr_data_dictionary_data_contract.py
#           (derive section, RED first)
#
# PURPOSE. Open the ONE growing sql-side file (02_sql_extraction.json,
# ruled 2026-09-28), read its "files" trees, and write its "derived"
# section — never touching the other sections, never reading sql
# files. Also write the dictionary discovery query (Output File 3,
# first move).
#
# THE ONE-FILE LAW (ruled 2026-09-28): each script owns its section.
# The parse (step 2) owns "files" and DROPS derived/resolution loudly
# when it re-runs; this script owns "derived"; step 5 owns
# "resolution". This script re-derives deterministically: same trees
# in -> byte-identical derived section out.
#
# ---------------------------------------------------------------------
# THE DERIVED SECTION
# ---------------------------------------------------------------------
#
# "tables": ONE census of EVERY table-like name in the trees (ruled
# 2026-09-28 — Sunny: nothing set aside where a mislabel could hide).
# One row per distinct (file, name), each with:
#   class — structural, decided here:
#     emr_or_enterprise_table  a real database object (a from_ref
#                              table_ref that is none of the below),
#                              INCLUDING refs inside reconstruction
#                              subtrees — the dynamic reads count
#     cte                      name matches a CTE declared in the same
#                              file (folded case-insensitive)
#     temp_table               name starts with "#" (also SELECT INTO
#                              #x targets and DROP #x targets)
#     table_variable           refs flagged variable (@t)
#     table_function           function_ref entries (STRING_SPLIT(...))
#   source — the dictionary's verdict, written by STEP 5, not here:
#     "pending" now; "emr" | "no_dictionary_match" later. Enterprise
#     tables surface as no_dictionary_match by evidence.
#   database_name / schema_name — for real tables: explicit name parts
#     win; a missing database falls back to the file's USE statement;
#     schema per the contract's org-fact line (dbo if Sunny keeps it,
#     else "") — the ruling is read from what the contract says, one
#     place. 4-part (server) names -> "anomalies", counted.
#
# "columns": used columns of real tables only —
#   {sql_file_name, database_name, schema_name, table_name,
#    column_name} — sorted, deduplicated. Binding per scope alias
#   frames (alias, else the table's last name part; nested scopes see
#   enclosing frames):
#     qualified column  -> its frame's table (CTE/temp/derived
#                          qualifiers are not EMR columns — their
#                          interiors already contributed their reads)
#     bare, ONE real source in scope  -> bound to it (the SQL runs,
#                          so the owner is certain)
#     bare, several sources -> "unresolved": {file, column,
#                          candidates}; binds at step 5, never guessed
#     star over a real source -> one row, column_name "*"
#   A table with no resolved columns keeps one row with column_name ""
#   so the census and the column rows never disagree on the table set.
#
# ---------------------------------------------------------------------
# OUTPUT FILE 3, FIRST MOVE — the discovery query
# ---------------------------------------------------------------------
#
# write_discovery_sql(out_dir) -> 02_emr_data_dictionary_discovery.sql
#   (kept for the record; superseded 2026-09-28 — Sunny cannot run
#   INFORMATION_SCHEMA. Discovery was satisfied by her PASTE, recorded
#   in 02_emr_data_dictionary_discovery_facts.md.)
#
# MOVE 2 (RULED 2026-09-28, contract updated) — write_extraction_sql
# generates FIVE standalone queries from the discovery facts + the
# derived table census:
#   _extraction_table.sql   TBL:  TABLE_ID, TABLE_NAME,
#                           TABLE_INTRODUCTION (the ruled description),
#                           DEPRECATED_YN
#   _extraction_column.sql  TBL->COL: COLUMN_ID, TABLE_ID, TABLE_NAME,
#                           COLUMN_NAME, DATA_TYPE, DESCRIPTION,
#                           DEPRECATED_YN
#   _extraction_join.sql    TBL->CLARITY_TBL_FK_ALL: FOREIGN_KEY_NUM
#                           (join_id) + ORDINAL_POSITION + source/dest
#                           ids AND names + the unfiltered reliability
#                           flags (CONDITIONAL_C, MAY_BE_STALE_C,
#                           IS_CURRENT_DATA_MODEL_YN, IS_SUPPLEMENTAL_YN)
#   _extraction_pk.sql      TBL->CLARITY_TBL_PK: TABLE_ID, TABLE_NAME,
#                           LINE (key_ordinal), PK_COLUMN_ID,
#                           COLUMN_DESCRIPTOR
#   _extraction_iniitm.sql  TBL->COL->CLARITY_COL_INIITM: COLUMN_ID,
#                           LINE, COLUMN_INI, COLUMN_ITEM
# Every query: FROM CLARITY.dbo..., Sunny's DE-DUP FILTER
# (TBL.TBL_DESCRIPTOR_OVR IS NOT NULL — 2 rows per table without it),
# and TBL.TABLE_NAME IN (<the used tables — folded UPPER, deduplicated
# across the Clarity/clarity casing split, literal list>). Standalone —
# no parameters to wire; each header says which csv to save.
# The gate: the discovery facts file must exist, else a plain raise —
# the no-guessing law.
#
# MOVE 3 (RULED 2026-09-28, contract) — write_values_sql generates the
# category-values query FROM DATA, never guesses:
#   - the used ZC_* tables come from the derived census;
#   - each ZC table's id column comes from the JOIN CSV: the
#     DEST_COLUMN_NAME rows pointing at that ZC (most common wins,
#     ties alphabetical), verified to exist in the COLUMN CSV;
#   - the meaning column is NAME, verified present in the column csv;
#   - a ZC table whose id column cannot be derived or which lacks
#     NAME is SKIPPED AND COUNTED in the query's header comment —
#     never guessed;
#   - output: 02_emr_data_dictionary_extraction_value.sql — one
#     UNION ALL query, one row shape (TABLE_NAME, CODE cast to
#     varchar, MEANING), saved by Sunny as ..._extraction_value.csv.
#
# ---------------------------------------------------------------------
# ENTRY POINTS + CLI
# ---------------------------------------------------------------------
#
# derive_used(extraction_path) -> the derived dict
#   Opens the growing file, replaces ONLY its "derived" section,
#   writes it back. Raises plainly if the file or its "files" section
#   is missing (the parse must have run).
#
# write_discovery_sql(out_dir) -> the discovery .sql path
#
# CLI (the command Sunny runs):
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/derive_tables_columns.py \
#       AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json \
#       AIVIA_01_Data/02_emr_data_dictionary/
#   Prints the census: tables by class and database, column rows,
#   unresolved count (each named), anomalies. Paths are parameters.
#
# CLAUDE'S TESTS (red first) pin:
#   - the derived section lands INSIDE the growing file; "files" is
#     untouched (byte-identical before/after on that section).
#   - CLARITY_ADT: class emr_or_enterprise_table, database Clarity,
#     schema dbo, source pending — contributed by BOTH a static file
#     and a reconstruction subtree.
#   - month_cte -> class cte; #-names -> class temp_table;
#     STRING_SPLIT -> class table_function. All IN the one census.
#   - EFFECTIVE_TIME bound to CLARITY_ADT; unresolved entries carry
#     candidates and no binding; star rows are "*".
#   - LOTE/Hospitalist unqualified tables carry database CookClarity
#     (the USE fallback).
#   - the discovery .sql names CLARITY_TBL, CLARITY_COL and
#     INFORMATION_SCHEMA; write_extraction_sql without the csv raises
#     with a plain message.
#   - determinism: derive twice, identical bytes.

import json
import sys
from collections import Counter
from pathlib import Path

# Contract org fact (Sunny kept the line, 2026-09-28): in our EMR
# databases an omitted schema means dbo.
OMITTED_SCHEMA = "dbo"

TABLE_CLASS = "emr_or_enterprise_table"


def _fold(name):
    return name.upper()


def _split_table_ref(name):
    """1-4 dot parts -> (server, database, schema, table); empty parts
    stay empty strings (db..table keeps its emptiness)."""
    parts = name.split(".")
    parts = [""] * (4 - len(parts)) + parts
    return tuple(parts)  # server, db, schema, table


class _FileDerive:
    def __init__(self, entry):
        self.entry = entry
        self.file = entry["name"]
        self.tables = {}       # (name folded, class) -> row
        self.columns = set()   # (db, schema, table, column)
        self.unresolved = {}   # column folded -> set of candidate tables
        self.anomalies = []
        self.cte_names = set()
        self.use_database = ""
        self._collect_context(entry["statements"])

    # -- context: CTE names + USE database, whole file incl. dynamic --
    def _collect_context(self, statements):
        for stmt in statements:
            if stmt.get("statement_kind") == "USE" and not self.use_database:
                self.use_database = stmt["database"]
            for scope in stmt.get("ctes", []):
                self.cte_names.add(_fold(scope["name"]))
            rec = stmt.get("reconstruction")
            if rec and rec.get("reconstructed"):
                self._collect_context(rec["statements"])
            for key in ("then", "else", "body"):
                if key in stmt:
                    self._collect_context(stmt[key])

    # -- census rows ---------------------------------------------------
    def _census(self, written, cls, database="", schema="", table=None):
        """`name` is the BARE object name (census columns hold db and
        schema separately); `written_as` keeps the text as the sql
        wrote it, for the eye."""
        name = table if table is not None else written
        key = (_fold(name), cls)
        if key not in self.tables:
            self.tables[key] = {
                "sql_file_name": self.file, "name": name, "class": cls,
                "database_name": database, "schema_name": schema,
                "source": "pending", "written_as": written,
            }
        return self.tables[key]

    def _classify_table_name(self, name):
        """A table-like NAME -> (class, db, schema, bare table name)."""
        if name.startswith("#"):
            return "temp_table", "", "", name
        server, db, schema, table = _split_table_ref(name)
        if not server and not db and not schema \
                and _fold(table) in self.cte_names:
            return "cte", "", "", table
        if server:
            self.anomalies.append({
                "sql_file_name": self.file, "name": name,
                "reason": "4-part (linked server) name"})
        db = db or self.use_database
        schema = schema or OMITTED_SCHEMA
        return TABLE_CLASS, db, schema, table

    # -- statements ----------------------------------------------------
    def run(self):
        self._statements(self.entry["statements"])
        return self

    def _statements(self, statements):
        for stmt in statements:
            for scope in stmt.get("ctes", []):
                self._census(scope["name"], "cte")
                self._scope(scope, outer=())
            if "scope" in stmt:
                scope = stmt["scope"]
                target = scope.get("name")
                if target:
                    cls, db, sch, table = self._classify_table_name(target)
                    self._census(target, cls, db if cls == TABLE_CLASS else "",
                                 sch if cls == TABLE_CLASS else "",
                                 table=table)
                self._scope(scope, outer=())
            for t in stmt.get("targets", []):  # DROP
                cls, db, sch, table = self._classify_table_name(t)
                self._census(t, cls, db if cls == TABLE_CLASS else "",
                             sch if cls == TABLE_CLASS else "", table=table)
            if "predicate" in stmt:
                self._expressions(stmt["predicate"], frames=())
            rec = stmt.get("reconstruction")
            if rec and rec.get("reconstructed"):
                self._statements(rec["statements"])
            for key in ("then", "else", "body"):
                if key in stmt:
                    self._statements(stmt[key])

    # -- scopes and frames ---------------------------------------------
    def _frame_of(self, scope):
        """alias/name (folded) -> ("table", (db, schema, table)) or
        ("other", None) for cte/temp/derived/variable/function refs."""
        frame = {}
        for ref in scope.get("from_refs", []):
            alias = ref.get("alias")
            if "derived_scope" in ref:
                if alias:
                    frame[_fold(alias)] = ("other", None)
                continue
            if "function_ref" in ref:
                self._census(ref["function_ref"], "table_function")
                if alias:
                    frame[_fold(alias)] = ("other", None)
                continue
            name = ref["table_ref"]
            if ref.get("variable"):
                self._census(name, "table_variable")
                key = alias or name.lstrip("@")
                frame[_fold(key)] = ("other", None)
                continue
            cls, db, sch, table = self._classify_table_name(name)
            self._census(name, cls, db if cls == TABLE_CLASS else "",
                         sch if cls == TABLE_CLASS else "", table=table)
            key = alias or table
            if cls == TABLE_CLASS:
                frame[_fold(key)] = ("table", (db, sch, table))
            else:
                frame[_fold(key)] = ("other", None)
        return frame

    def _scope(self, scope, outer):
        if "set_op" in scope:
            for side in scope["set_op"]["sides"]:
                self._scope(side, outer)
            return
        frame = self._frame_of(scope)
        frames = (frame,) + outer
        for ref in scope.get("from_refs", []):
            if "derived_scope" in ref:
                self._scope(ref["derived_scope"], frames)
        for key in ("where",):
            if key in scope:
                self._expressions(scope[key], frames)
        for pred in scope.get("join_on", []):
            self._expressions(pred, frames)
        for part in ("group_by", "order_by", "projection"):
            for item in scope.get(part, []):
                self._expressions(item, frames)

    def _bind(self, qualifier, column, frames):
        if column.startswith("AIVIA_VAR_") or qualifier.startswith("AIVIA_VAR_"):
            # Our own reconstruction placeholders — already recorded in
            # the reconstruction's "placeholders" list, never columns.
            return
        if qualifier:
            for frame in frames:
                hit = frame.get(_fold(qualifier))
                if hit is None:
                    continue
                kind, target = hit
                if kind == "table":
                    self.columns.add((*target, column))
                return  # cte/temp/derived qualifier: interior already counted
            self.anomalies.append({
                "sql_file_name": self.file, "name": f"{qualifier}.{column}",
                "reason": "qualifier matches no source in scope"})
            return
        own = frames[0] if frames else {}
        tables = {t for kind, t in own.values() if kind == "table" and t}
        if len(tables) == 1:
            self.columns.add((*tables.pop(), column))
        elif len(tables) > 1:
            self.unresolved.setdefault(_fold(column), {
                "sql_file_name": self.file, "column_name": column,
                "candidates": set()})["candidates"].update(
                t[2] for t in tables)
        # zero real sources: the column belongs to a cte/temp/derived
        # source whose interior already contributed its reads

    def _star(self, qualifier, frames):
        own = frames[0] if frames else {}
        if qualifier:
            hit = None
            for frame in frames:
                hit = frame.get(_fold(qualifier))
                if hit is not None:
                    break
            if hit and hit[0] == "table":
                self.columns.add((*hit[1], "*"))
            return
        for kind, target in own.values():
            if kind == "table" and target:
                self.columns.add((*target, "*"))

    def _expressions(self, node, frames):
        if isinstance(node, list):
            for item in node:
                self._expressions(item, frames)
            return
        if not isinstance(node, dict):
            return
        if node.get("node") == "scope":
            self._scope(node, frames)
            return
        if node.get("kind") == "column_ref":
            parts = node["name"].split(".")
            qualifier = ".".join(parts[:-1])
            self._bind(qualifier, parts[-1], frames)
            return
        if node.get("star") or node.get("kind") == "star":
            self._star(node.get("qualifier"), frames)
            return
        for key, v in node.items():
            if key in ("evidence", "comments", "reconstruction"):
                continue
            self._expressions(v, frames)


def derive_used(extraction_path):
    extraction_path = Path(extraction_path)
    with open(extraction_path, encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict) or "files" not in doc:
        raise ValueError(
            f"{extraction_path} has no 'files' section — run "
            "parse_sql_tree.py first (the parse owns that section)")
    tables, columns, unresolved, anomalies = [], [], [], []
    for entry in doc["files"]:
        d = _FileDerive(entry).run()
        tables.extend(d.tables.values())
        emr_tables = {(r["database_name"], r["schema_name"], r["name"])
                      for r in d.tables.values()
                      if r["class"] == TABLE_CLASS}
        covered = {(db, sch, t) for db, sch, t, _ in d.columns}
        for db, sch, t in emr_tables - covered:
            d.columns.add((db, sch, t, ""))
        columns.extend(
            {"sql_file_name": d.file, "database_name": db,
             "schema_name": sch, "table_name": t, "column_name": c}
            for db, sch, t, c in d.columns)
        unresolved.extend(
            {**u, "candidates": sorted(u["candidates"])}
            for u in d.unresolved.values())
        anomalies.extend(d.anomalies)
    derived = {
        "tables": sorted(tables, key=lambda r: (
            r["sql_file_name"], r["class"], _fold(r["name"]))),
        "columns": sorted(columns, key=lambda r: (
            r["sql_file_name"], r["database_name"], r["schema_name"],
            r["table_name"], r["column_name"])),
        "unresolved": sorted(unresolved, key=lambda u: (
            u["sql_file_name"], u["column_name"])),
        "anomalies": anomalies,
    }
    doc["derived"] = derived
    with open(extraction_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    return derived


DISCOVERY_SQL = """\
-- 02_emr_data_dictionary_discovery.sql (contract Output File 3, first
-- move). Run ONCE in the EMR's Clarity database by Sunny's hand.
-- Save the full result as 02_emr_data_dictionary_discovery.csv in
-- AIVIA_01_Data/02_emr_data_dictionary/.
-- Also answer (from knowledge or the inventory rows below): which
-- dictionary table holds the JOIN relationships between tables?
--
-- ONE result set, two kinds of rows:
--   COLUMN_NAME filled -> the columns of CLARITY_TBL / CLARITY_COL
--   COLUMN_NAME blank  -> inventory: every table named CLARITY_...
--     (to spot where joins, keys, and category values live)
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME,
       DATA_TYPE, ORDINAL_POSITION
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('CLARITY_TBL', 'CLARITY_COL')
UNION ALL
SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, '', '', 0
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE 'CLARITY\\_%' ESCAPE '\\'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
"""


def write_discovery_sql(out_dir):
    out = Path(out_dir) / "02_emr_data_dictionary_discovery.sql"
    out.write_text(DISCOVERY_SQL, encoding="utf-8")
    return out


_QUERY_HEADER = """\
-- {name} (contract Output File 3, move 2; generated {stamp}).
-- Run in the EMR by Sunny's hand. Save the FULL result as
-- {csv} in AIVIA_01_Data/02_emr_data_dictionary/.
-- The TBL_DESCRIPTOR_OVR filter is Sunny's de-dup ruling
-- (2 rows per table without it). Table list: the {n} used tables
-- from the derived census, casing folded.
"""

_EXTRACTION_QUERIES = {
    "table": """\
SELECT TBL.TABLE_ID, TBL.TABLE_NAME, TBL.TABLE_INTRODUCTION,
       TBL.DEPRECATED_YN
FROM CLARITY.dbo.CLARITY_TBL TBL
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
{in_list}
  )
ORDER BY TBL.TABLE_NAME;
""",
    "column": """\
SELECT COL.COLUMN_ID, COL.TABLE_ID, TBL.TABLE_NAME, COL.COLUMN_NAME,
       COL.DATA_TYPE, COL.DESCRIPTION, COL.DEPRECATED_YN
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_COL COL ON TBL.TABLE_ID = COL.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
{in_list}
  )
ORDER BY TBL.TABLE_NAME, COL.COLUMN_NAME;
""",
    "join": """\
SELECT TFA.TABLE_ID, TFA.FOREIGN_KEY_NUM, TFA.ORDINAL_POSITION,
       TFA.SOURCE_TABLE_NAME, TFA.SOURCE_COLUMN_ID,
       TFA.SOURCE_COLUMN_NAME, TFA.DEST_TABLE_ID, TFA.DEST_TABLE_NAME,
       TFA.DEST_COLUMN_ID, TFA.DEST_COLUMN_NAME, TFA.CONDITIONAL_C,
       TFA.MAY_BE_STALE_C, TFA.IS_CURRENT_DATA_MODEL_YN,
       TFA.IS_SUPPLEMENTAL_YN
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_TBL_FK_ALL TFA
        ON TBL.TABLE_ID = TFA.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
{in_list}
  )
ORDER BY TFA.TABLE_ID, TFA.FOREIGN_KEY_NUM, TFA.ORDINAL_POSITION;
""",
    "pk": """\
SELECT PK.TABLE_ID, TBL.TABLE_NAME, PK.LINE, PK.PK_COLUMN_ID,
       PK.COLUMN_DESCRIPTOR
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_TBL_PK PK ON TBL.TABLE_ID = PK.TABLE_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
{in_list}
  )
ORDER BY TBL.TABLE_NAME, PK.LINE;
""",
    "iniitm": """\
SELECT INI.COLUMN_ID, INI.LINE, INI.COLUMN_INI, INI.COLUMN_ITEM
FROM CLARITY.dbo.CLARITY_TBL TBL
    JOIN CLARITY.dbo.CLARITY_COL COL ON TBL.TABLE_ID = COL.TABLE_ID
    JOIN CLARITY.dbo.CLARITY_COL_INIITM INI
        ON COL.COLUMN_ID = INI.COLUMN_ID
WHERE TBL.TBL_DESCRIPTOR_OVR IS NOT NULL
  AND TBL.TABLE_NAME IN (
{in_list}
  )
ORDER BY INI.COLUMN_ID, INI.LINE;
""",
}


def used_table_names(extraction_path):
    """The census's real tables, folded UPPER and deduplicated (the
    Clarity/clarity casing split folds to one list), sorted."""
    with open(extraction_path, encoding="utf-8") as f:
        doc = json.load(f)
    derived = doc.get("derived")
    if not derived:
        raise ValueError(
            f"{extraction_path} has no 'derived' section — run "
            "derive_used first")
    return sorted({_fold(r["name"]) for r in derived["tables"]
                   if r["class"] == TABLE_CLASS})


def write_extraction_sql(extraction_path, facts_path, out_dir):
    facts_path = Path(facts_path)
    if not facts_path.exists():
        raise FileNotFoundError(
            f"discovery facts not found at {facts_path} — the "
            "extraction queries are generated from the recorded "
            "discovery facts (Sunny's paste, "
            "02_emr_data_dictionary_discovery_facts.md), never from "
            "guesses")
    names = used_table_names(extraction_path)
    in_list = ",\n".join(f"    '{n}'" for n in names)
    out_dir = Path(out_dir)
    written = []
    for kind, body in _EXTRACTION_QUERIES.items():
        fname = f"02_emr_data_dictionary_extraction_{kind}.sql"
        header = _QUERY_HEADER.format(
            name=fname, stamp="from the discovery facts",
            csv=fname.replace(".sql", ".csv"), n=len(names))
        path = out_dir / fname
        path.write_text(header + body.format(in_list=in_list),
                        encoding="utf-8")
        written.append(path)
    return written


def _read_tsv(path):
    """Sunny's exports: tab-separated (grid paste) or comma. Sniff by
    the header line; return (header list, row dicts)."""
    import csv as _csv
    with open(path, encoding="utf-8-sig", newline="") as f:
        first = f.readline()
        delim = "\t" if "\t" in first else ","
        f.seek(0)
        reader = _csv.DictReader(f, delimiter=delim)
        return reader.fieldnames, list(reader)


# Category values, CLARITY_* tables — Sunny's ruled list (contract,
# 2026-09-28): not ZC-structured, so each table is ruled one by one.
# The generator obeys this list VERBATIM; CLARITY_ADT is ruled NOT a
# category table (the event data table) and is absent on purpose.
CATEGORY_RULINGS = {
    "CLARITY_BED": ("BED_CSN_ID", "BED_LABEL"),
    "CLARITY_DEP": ("DEPARTMENT_ID", "DEPARTMENT_NAME"),
    "CLARITY_EPM": ("PAYOR_ID", "PAYOR_NAME"),
    "CLARITY_LOC": ("LOC_ID", "LOC_NAME"),
    "CLARITY_ROM": ("ROOM_CSN_ID", "ROOM_NAME"),
    "CLARITY_SA": ("SERV_AREA_ID", "SERV_AREA_NAME"),
}


def write_values_sql(extraction_path, join_csv, column_csv, out_dir):
    join_csv, column_csv = Path(join_csv), Path(column_csv)
    if not join_csv.exists():
        raise FileNotFoundError(
            f"join csv not found at {join_csv} — the values queries "
            "derive each ZC table's id column from the join csv "
            "(DEST_COLUMN_NAME), never from guesses")
    if not column_csv.exists():
        raise FileNotFoundError(f"column csv not found at {column_csv}")
    used_zc = [n for n in used_table_names(extraction_path)
               if n.startswith("ZC_")]
    _, join_rows = _read_tsv(join_csv)
    _, col_rows = _read_tsv(column_csv)
    dest_cols = {}
    for r in join_rows:
        dest_cols.setdefault(r["DEST_TABLE_NAME"].upper(), []).append(
            r["DEST_COLUMN_NAME"].upper())
    table_cols = {}
    for r in col_rows:
        table_cols.setdefault(r["TABLE_NAME"].upper(), set()).add(
            r["COLUMN_NAME"].upper())
    plan, skipped = [], []
    for zc in used_zc:
        cols = table_cols.get(zc, set())
        if "NAME" not in cols:
            skipped.append(f"{zc}: no NAME column in the column csv")
            continue
        candidates = [c for c in dest_cols.get(zc, []) if c in cols]
        if not candidates:
            skipped.append(f"{zc}: no id column derivable from the join csv")
            continue
        counts = Counter(candidates)
        top = max(counts.values())
        id_col = sorted(c for c, n in counts.items() if n == top)[0]
        plan.append((zc, id_col, "NAME"))
    used = set(used_table_names(extraction_path))
    for table, (id_col, meaning_col) in sorted(CATEGORY_RULINGS.items()):
        if table not in used:
            continue
        cols = table_cols.get(table, set())
        missing = [c for c in (id_col, meaning_col) if c not in cols]
        if missing:
            raise ValueError(
                f"ruled category table {table}: column(s) "
                f"{', '.join(missing)} not in the column csv — the "
                "contract ruling and the dictionary disagree; re-rule")
        plan.append((table, id_col, meaning_col))
    selects = [
        f"SELECT '{table}' AS TABLE_NAME,\n"
        f"       CAST({id_col} AS VARCHAR(50)) AS CODE,\n"
        f"       {meaning_col} AS MEANING\n"
        f"FROM CLARITY.dbo.{table}"
        for table, id_col, meaning_col in sorted(plan)]
    header = (
        "-- 02_emr_data_dictionary_extraction_value.sql (contract Output "
        "File 3, move 3;\n"
        "-- generated FROM the join and column csvs — id columns derived, "
        "never guessed).\n"
        "-- Run in the EMR by Sunny's hand. Save the FULL result as\n"
        "-- 02_emr_data_dictionary_extraction_value.csv in "
        "AIVIA_01_Data/02_emr_data_dictionary/.\n"
        f"-- {len(selects)} ZC tables included.\n")
    for s in skipped:
        header += f"-- SKIPPED (counted, needs a ruling if wanted): {s}\n"
    sql = header + "\nUNION ALL\n".join(selects) + "\nORDER BY 1, 2;\n"
    out = Path(out_dir) / "02_emr_data_dictionary_extraction_value.sql"
    out.write_text(sql, encoding="utf-8")
    return out, skipped


def main(argv):
    if len(argv) < 3:
        print("usage: python3.11 AIVIA_01_Code/derive_tables_columns.py "
              "<02_sql_extraction.json> <output dir for the .sql>",
              file=sys.stderr)
        return 2
    derived = derive_used(argv[1])
    sql_path = write_discovery_sql(argv[2])
    by_class = {}
    for r in derived["tables"]:
        by_class.setdefault(r["class"], set()).add(_fold(r["name"]))
    print("derived census:")
    for cls in sorted(by_class):
        print(f"  {cls}: {len(by_class[cls])} distinct names")
    real = {(r['database_name'], _fold(r['name']))
            for r in derived["tables"] if r["class"] == TABLE_CLASS}
    for db in sorted({d for d, _ in real}):
        names = sorted(n for d, n in real if d == db)
        print(f"  database {db or '(blank)'}: {len(names)} tables")
    print(f"  column rows: {len(derived['columns'])}")
    for u in derived["unresolved"]:
        print(f"  UNRESOLVED {u['sql_file_name']}: {u['column_name']} "
              f"~ {u['candidates']}")
    for a in derived["anomalies"]:
        print(f"  ANOMALY {a['sql_file_name']}: {a['name']} — {a['reason']}")
    print(f"discovery query written: {sql_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
