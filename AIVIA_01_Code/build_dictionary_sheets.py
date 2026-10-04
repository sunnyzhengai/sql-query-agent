# build_dictionary_sheets.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L05)
# Contract: AIVIA_01_Design/02_emr_data_dictionary_data_contract.md
#           (Output File 5 sheets, 02_no_dictionary_match.json,
#            the resolution section of Output File 1)
# Tests:    AIVIA_01_Test/test_02_emr_data_dictionary_data_contract.py
#           (sheets section, written RED first, on tiny synthetic csvs
#            so the paid embedding calls stay pennies; the full corpus
#            run is by hand, once)
#
# PURPOSE. Convert Sunny's five (later six, with values) csv exports
# into the json data sheets with embeddings, write the no-match file,
# and complete the ruled two-step: the resolution section of the
# growing sql-side file binds the unresolved columns.
#
# ---------------------------------------------------------------------
# THE LOADER (every csv passes through it)
# ---------------------------------------------------------------------
#   - encoding utf-8-sig; delimiter SNIFFED from the header line
#     (Sunny's grid pastes are tab-separated; real csv also accepted).
#   - the header row is VALIDATED against the expected field list for
#     that file (from the discovery facts). Wrong or missing header ->
#     loud failure naming the file and the difference.
#   - ragged rows (field count != header count) -> loud failure naming
#     every bad row number. No repair here — Sunny's raw export stays
#     untouched; a repair, if ever needed, is its own ruled step.
#
# ---------------------------------------------------------------------
# THE SHEETS (contract Output File 5 field lists, verbatim)
# ---------------------------------------------------------------------
# table sheet  02_emr_data_dictionary_extraction_table.json
#   table_id, database_name, schema_name, table_name,
#   table_description (= TABLE_INTRODUCTION), deprecated_yn,
#   table_name_embedding, table_description_embedding
#   - database_name / schema_name come from the derived census row for
#     that table name (folded match) — the census carries what the sql
#     wrote + the dbo org fact.
#
# column sheet 02_emr_data_dictionary_extraction_column.json
#   column_id, table_id, database_name, schema_name, table_name,
#   column_name, data_type, is_primary_key, key_ordinal,
#   column_description (= DESCRIPTION), deprecated_yn,
#   column_name_embedding, column_description_embedding
#   - is_primary_key/key_ordinal folded in from the pk csv by
#     PK_COLUMN_ID -> COLUMN_ID (LINE = key_ordinal); absent from the
#     pk csv = false / no ordinal.
#
# join sheet   02_emr_data_dictionary_extraction_join.json
#   join_id, ordinal, source_table_id, source_table_name,
#   source_column_id, source_column_name, destin_table_id,
#   destin_table_name, destin_column_id, destin_column_name,
#   conditional_c, may_be_stale_c, is_current_data_model_yn,
#   is_supplemental_yn, destin_in_scope
#   - REFINEMENT for Sunny's eye: FOREIGN_KEY_NUM alone is only unique
#     WITHIN a table, so join_id = "<TABLE_ID>:<FOREIGN_KEY_NUM>" —
#     globally unique, still verbatim-derived, ordinal unchanged.
#   - REFINEMENT 2: 5,261 join rows point at MANY tables outside our
#     38 (the dictionary knows the whole estate). The contract's
#     FK-integrity law (ids must resolve to sheet rows) would fail on
#     every outside destination. Ruling proposed: keep ALL rows, add
#     destin_in_scope true/false; integrity fails loudly only when a
#     SOURCE id, or an in-scope DESTINATION id, is missing from the
#     sheets. Out-of-scope destinations are tomorrow's expansion
#     frontier, kept visible, never a failure.
#   - no embeddings on the join sheet (contract).
#
# iniitm sheet 02_emr_data_dictionary_extraction_iniitm.json
#   column_id, line, column_ini, column_item — no embeddings (contract).
#
# value sheet  02_emr_data_dictionary_extraction_value.json
#   table_name, code, meaning — no embeddings this phase (contract).
#   Built only when Sunny's values csv exists; its absence is reported,
#   never fatal (move 3 runs after this build's first pass).
#
# ---------------------------------------------------------------------
# THE LOUD RULES (contract, ruled)
# ---------------------------------------------------------------------
#   - NO BLANK DESCRIPTIONS: a table with blank TABLE_INTRODUCTION or
#     a column with blank DESCRIPTION fails the build loudly, naming
#     every offending row (Sunny's ruling: there will be no blanks; a
#     blank means something is wrong).
#   - FK INTEGRITY (as refined above): source ids and in-scope destin
#     ids must exist in the sheets; violations named, build fails.
#   - 02_no_dictionary_match.json: every used table absent from the
#     table csv (CR_STAT_EXECUTION today) and every used column absent
#     from its matched table's columns — rows:
#     {database_name, schema_name, table_name, column_name ("" =
#     table-level miss), sql_file_names[]}. Counted, never silent.
#
# ---------------------------------------------------------------------
# EMBEDDINGS (contract: separate name and description embeddings)
# ---------------------------------------------------------------------
#   - model text-embedding-3-large, 3072 numbers, key from .env —
#     the same real_embedder shape as phase 01; the embedder is passed
#     IN so tests and Fabric reuse the code.
#   - batched calls (chunks of 1000 inputs), never one call per row.
#   - THE REUSE RULE (phase-01 law): if the sheet json already exists,
#     a row whose (id, embedded text) is unchanged KEEPS its stored
#     embedding — re-runs cost only what changed. The census prints
#     embedded-new vs reused counts.
#   - full-corpus first run: ~38 tables x 2 texts + ~1,617 columns x 2
#     texts ~= 3,300 embeddings — a few cents, announced before
#     running.
#
# ---------------------------------------------------------------------
# THE RESOLUTION SECTION (Output File 1, owned by THIS script)
# ---------------------------------------------------------------------
#   Written into 02_sql_extraction.json as "resolution" (the third
#   section; parse re-runs drop it, per the one-file law):
#   - table_source: for every census real table, "emr" (in the table
#     sheet) or "no_dictionary_match" — the census's pending verdicts,
#     delivered. The derived section itself stays untouched (one
#     owner per section).
#   - bindings: each unresolved column from the derived section is
#     checked against the column sheet: exactly ONE candidate table
#     owns the column -> bound (the ruled two-step completes:
#     EFFECTIVE_TIME, REPORT_INFO_ID). Zero -> recorded no_match.
#     Two+ -> recorded ambiguous with the owners listed. Never guessed.
#
# ---------------------------------------------------------------------
# ENTRY POINTS + CLI
# ---------------------------------------------------------------------
# build_sheets(csv_dir, extraction_path, out_dir, embedder) -> census
# CLI (the command Sunny runs):
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/build_dictionary_sheets.py \
#       AIVIA_01_Data/02_emr_data_dictionary \
#       AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json
#   (csv dir doubles as out dir; both are parameters, per the law)
#   Prints the census: rows per sheet, pk columns folded, no-match
#   list by name, bindings made, embeddings new vs reused, value
#   sheet present or awaiting move 3.
#
# CLAUDE'S TESTS (red first, tiny synthetic csvs + the real embedder):
#   - loader: sniffs tab; wrong header fails naming the file; a ragged
#     row fails naming its row number.
#   - sheets: pk folds in (is_primary_key + key_ordinal); join_id =
#     table_id:fk_num with ordinals kept; destin_in_scope flags;
#     blank description fails loudly; embeddings are 3072 numbers on
#     name AND description separately.
#   - reuse: second run with unchanged texts re-embeds nothing.
#   - no-match: a used table absent from the csv lands in the file.
#   - resolution: a one-candidate unresolved column binds; a
#     zero-candidate records no_match; sections ownership holds
#     (files and derived byte-identical before/after).
#   - ON THE REAL DATA (structural only, no embedding cost — embedder
#     that fails if called with unchanged inputs is NOT used here;
#     the real-data run is Sunny's hand): none in the suite; the suite
#     stays synthetic. The real run's census is Sunny's eyeball gate.

# ---------------------------------------------------------------------
# UPDATE 2026-09-29 — the L09 amendments. PSEUDO CODE, awaiting Sunny's
# review; the real code lands in this same file after approval.
#
# Design:   AIVIA_01_Design/02_emr_data_dictionary.md (L08 + L09)
# Contract: the L09 contract amendments (column sheet gains
#           column_ini/column_item; value embeddings supersede the
#           "no embeddings on values this phase" line; sidecar file;
#           iniitm stays unembedded)
#
# CHANGE 1 — iniitm folds into the column sheet (L09: line 1 only)
#   - after the pk fold, build ini_map: column_id -> (ini, item) from
#     the iniitm csv rows whose LINE == 1.
#   - every column row gains column_ini, column_item. A column with no
#     iniitm row gets None for both (155 today — legal, counted, never
#     a failure).
#   - THE LEDGER (nothing dropped silently): iniitm rows with LINE > 1
#     are NOT folded (45 rows over 38 columns today — the date+time
#     item pairs and multi-source derived columns). The iniitm sheet
#     json keeps ALL lines unchanged — the record loses nothing; the
#     census reports iniitm_multi_line_columns and
#     iniitm_unfolded_rows, printed at every build.
#   - REUSE LAW UNTOUCHED: the two new fields are not embedded texts,
#     so a re-run over the existing column.json re-embeds ZERO column
#     texts for this change.
#
# CHANGE 2 — value embeddings, sidecar file (L09)
#   - sidecar: 02_emr_data_dictionary_extraction_value_embeddings.json
#     rows: {table_name, code, meaning_embedding} — keyed
#     table_name + code. value.json itself is unchanged and stays
#     readable (1.3 MB, not 1.2 GB).
#   - the MEANING text only is embedded (a code carries no semantics);
#     3072 numbers, same model, same passed-in embedder.
#   - reuse law applies, keyed (table_name, code) + meaning text: a
#     re-run with unchanged meanings re-embeds nothing. The first full
#     run embeds 14,476 meanings — batched, cost announced, Sunny's
#     hand.
#   - built only when the value csv exists (same posture as the value
#     sheet itself); absence reported, never fatal.
#   - integrity, loud: sidecar rows and value sheet rows must match
#     1:1 by (table_name, code) — a mismatch fails the build naming
#     the keys.
#   - census gains value_embeddings_new / value_embeddings_reused.
#
# CLAUDE'S NEW TESTS (red first, synthetic csvs + the real embedder):
#   - a column row carries column_ini/column_item from its LINE 1 row;
#     a column with two iniitm lines folds line 1 only and the census
#     counts the unfolded row; a column with no iniitm row gets None
#     and is counted.
#   - the sidecar exists when values exist; rows match the value sheet
#     1:1 by (table_name, code); embeddings are 3072 numbers over the
#     meaning only.
#   - sidecar reuse: a second run with unchanged meanings re-embeds
#     nothing.
#   - the column sheet re-run after CHANGE 1 re-embeds zero texts.
# ---------------------------------------------------------------------

import csv
import json
import sys
from pathlib import Path

EMBED_BATCH = 1000

EXPECTED_HEADERS = {
    "table": ["TABLE_ID", "TABLE_NAME", "TABLE_INTRODUCTION",
              "DEPRECATED_YN"],
    "column": ["COLUMN_ID", "TABLE_ID", "TABLE_NAME", "COLUMN_NAME",
               "DATA_TYPE", "DESCRIPTION", "DEPRECATED_YN"],
    "join": ["TABLE_ID", "FOREIGN_KEY_NUM", "ORDINAL_POSITION",
             "SOURCE_TABLE_NAME", "SOURCE_COLUMN_ID", "SOURCE_COLUMN_NAME",
             "DEST_TABLE_ID", "DEST_TABLE_NAME", "DEST_COLUMN_ID",
             "DEST_COLUMN_NAME", "CONDITIONAL_C", "MAY_BE_STALE_C",
             "IS_CURRENT_DATA_MODEL_YN", "IS_SUPPLEMENTAL_YN"],
    "pk": ["TABLE_ID", "TABLE_NAME", "LINE", "PK_COLUMN_ID",
           "COLUMN_DESCRIPTOR"],
    "iniitm": ["COLUMN_ID", "LINE", "COLUMN_INI", "COLUMN_ITEM"],
    "value": ["TABLE_NAME", "CODE", "MEANING"],
}


def _fold(name):
    return name.upper()


def _load_csv(csv_dir, kind):
    """The loader: sniff the delimiter, validate the header, fail
    loudly on ragged rows. Sunny's raw export is never modified."""
    path = Path(csv_dir) / f"02_emr_data_dictionary_extraction_{kind}.csv"
    with open(path, encoding="utf-8-sig", newline="") as f:
        first = f.readline()
        delim = "\t" if "\t" in first else ","
        f.seek(0)
        rows = list(csv.reader(f, delimiter=delim))
    header = rows[0] if rows else []
    expected = EXPECTED_HEADERS[kind]
    if header != expected:
        raise ValueError(
            f"{kind} csv header mismatch in {path.name}: expected "
            f"{expected}, found {header}")
    ragged = [i + 1 for i, r in enumerate(rows[1:], start=1)
              if len(r) != len(expected) and r]
    if ragged:
        raise ValueError(
            f"{kind} csv has ragged rows (field count != "
            f"{len(expected)}) at line(s) {ragged[:20]} in {path.name}")
    return [dict(zip(expected, r)) for r in rows[1:] if r]


def _census_maps(extraction_path):
    with open(extraction_path, encoding="utf-8") as f:
        doc = json.load(f)
    derived = doc.get("derived")
    if not derived:
        raise ValueError(
            f"{extraction_path} has no 'derived' section — run "
            "derive_tables_columns first")
    loc, files, display = {}, {}, {}
    for r in derived["tables"]:
        if r["class"] != "emr_or_enterprise_table":
            continue
        key = _fold(r["name"])
        if key not in loc:
            loc[key] = (r["database_name"], r["schema_name"])
            display[key] = r["name"]
        files.setdefault(key, set()).add(r["sql_file_name"])
    return doc, derived, loc, files, display


def _embed_with_reuse(rows, plans, out_path, embedder, census):
    """plans: (row, field, text). Reuse a stored embedding when the
    same id kept the same text (the phase-01 economy law)."""
    old = {}
    out_path = Path(out_path)
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for row in json.load(f):
                rid = row.get("table_id"), row.get("column_id")
                for field in row:
                    if field.endswith("_embedding"):
                        text_field = field[:-len("_embedding")]
                        key_text = row.get(
                            text_field,
                            row.get(text_field.replace("_name", ""), None))
                        old[(rid, field)] = (key_text, row[field])
    to_embed = []
    for row, field, text in plans:
        rid = row.get("table_id"), row.get("column_id")
        prior = old.get((rid, field))
        if prior is not None and prior[1] is not None \
                and prior[0] == _plan_text(row, field):
            # prior[1] check (2026-10-03): a stored None never
            # satisfies reuse — vectors are reused, holes are not
            row[field] = prior[1]
            census["embeddings_reused"] += 1
        else:
            to_embed.append((row, field, text))
    for start in range(0, len(to_embed), EMBED_BATCH):
        chunk = to_embed[start:start + EMBED_BATCH]
        vectors = embedder([text for _, _, text in chunk])
        for (row, field, _), vec in zip(chunk, vectors):
            row[field] = vec
            census["embeddings_new"] += 1


def _plan_text(row, field):
    """The text a stored embedding was computed over, derived from the
    row itself so reuse checks are self-contained."""
    base = field[:-len("_embedding")]
    if base in row:
        return row[base]
    return row.get(base.replace("_name", ""))


def _embed_values_sidecar(value_sheet, out_path, embedder, census):
    """The L09 sidecar: one meaning embedding per value row, built
    fresh from the CURRENT value sheet (stale keys cannot survive).
    meaning rides along so the reuse check is self-contained, same law
    as _plan_text."""
    old = {}
    out_path = Path(out_path)
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for row in json.load(f):
                old[(row["table_name"], row["code"])] = (
                    row.get("meaning"), row["meaning_embedding"])
    sidecar = [{"table_name": r["table_name"], "code": r["code"],
                "meaning": r["meaning"]} for r in value_sheet]
    to_embed = []
    for row in sidecar:
        prior = old.get((row["table_name"], row["code"]))
        if prior is not None and prior[0] == row["meaning"]:
            row["meaning_embedding"] = prior[1]
            census["value_embeddings_reused"] += 1
        else:
            to_embed.append(row)
    for start in range(0, len(to_embed), EMBED_BATCH):
        chunk = to_embed[start:start + EMBED_BATCH]
        vectors = embedder([r["meaning"] for r in chunk])
        for row, vec in zip(chunk, vectors):
            row["meaning_embedding"] = vec
            census["value_embeddings_new"] += 1
    return sidecar


def build_sheets(csv_dir, extraction_path, out_dir, embedder):
    csv_dir, out_dir = Path(csv_dir), Path(out_dir)
    doc, derived, loc, file_map, display = _census_maps(extraction_path)
    census = {"embeddings_new": 0, "embeddings_reused": 0,
              "value_embeddings_new": 0, "value_embeddings_reused": 0}

    t_rows = _load_csv(csv_dir, "table")
    c_rows = _load_csv(csv_dir, "column")
    j_rows = _load_csv(csv_dir, "join")
    p_rows = _load_csv(csv_dir, "pk")
    i_rows = _load_csv(csv_dir, "iniitm")
    value_path = csv_dir / "02_emr_data_dictionary_extraction_value.csv"
    v_rows = _load_csv(csv_dir, "value") if value_path.exists() else None

    # -- the table sheet ---------------------------------------------
    blanks = [r["TABLE_NAME"] for r in t_rows
              if not r["TABLE_INTRODUCTION"].strip()]
    if blanks:
        raise ValueError(
            "blank TABLE_INTRODUCTION (the contract says no blanks): "
            + ", ".join(blanks))
    table_sheet = []
    for r in sorted(t_rows, key=lambda r: r["TABLE_NAME"]):
        db, sch = loc.get(_fold(r["TABLE_NAME"]), ("", ""))
        table_sheet.append({
            "table_id": r["TABLE_ID"],
            "database_name": db, "schema_name": sch,
            "table_name": r["TABLE_NAME"],
            "table_description": r["TABLE_INTRODUCTION"],
            "deprecated_yn": r["DEPRECATED_YN"],
        })
    sheet_tables = {_fold(r["table_name"]) for r in table_sheet}
    table_ids = {r["table_id"] for r in table_sheet}

    # -- the column sheet (pk folded in) -----------------------------
    blanks = [f"{r['TABLE_NAME']}.{r['COLUMN_NAME']}" for r in c_rows
              if not r["DESCRIPTION"].strip()]
    if blanks:
        raise ValueError(
            "blank column DESCRIPTION (the contract says no blanks): "
            + ", ".join(blanks[:20]))
    pk_map = {r["PK_COLUMN_ID"]: int(r["LINE"]) for r in p_rows}
    # L09 iniitm fold: LINE 1 becomes the column properties; more lines
    # stay in the iniitm sheet and are COUNTED, never silently dropped.
    ini_map, ini_extra = {}, {}
    for r in i_rows:
        if int(r["LINE"]) == 1:
            ini_map[r["COLUMN_ID"]] = (r["COLUMN_INI"], r["COLUMN_ITEM"])
        else:
            ini_extra[r["COLUMN_ID"]] = ini_extra.get(r["COLUMN_ID"], 0) + 1
    column_sheet = []
    for r in sorted(c_rows, key=lambda r: (r["TABLE_NAME"],
                                           r["COLUMN_NAME"])):
        db, sch = loc.get(_fold(r["TABLE_NAME"]), ("", ""))
        ini, item = ini_map.get(r["COLUMN_ID"], (None, None))
        column_sheet.append({
            "column_id": r["COLUMN_ID"], "table_id": r["TABLE_ID"],
            "database_name": db, "schema_name": sch,
            "table_name": r["TABLE_NAME"],
            "column_name": r["COLUMN_NAME"],
            "data_type": r["DATA_TYPE"],
            "is_primary_key": r["COLUMN_ID"] in pk_map,
            "key_ordinal": pk_map.get(r["COLUMN_ID"]),
            "column_ini": ini, "column_item": item,
            "column_description": r["DESCRIPTION"],
            "deprecated_yn": r["DEPRECATED_YN"],
        })
    column_ids = {r["column_id"] for r in column_sheet}
    table_columns = {}
    for r in column_sheet:
        table_columns.setdefault(_fold(r["table_name"]), set()).add(
            _fold(r["column_name"]))

    # -- the join sheet (join_id = TABLE_ID:FK_NUM; destin_in_scope) --
    join_sheet = []
    violations = []
    for r in sorted(j_rows, key=lambda r: (r["SOURCE_TABLE_NAME"],
                                           r["TABLE_ID"],
                                           int(r["FOREIGN_KEY_NUM"]),
                                           int(r["ORDINAL_POSITION"]))):
        in_scope = _fold(r["DEST_TABLE_NAME"]) in sheet_tables
        row = {
            "join_id": f"{r['TABLE_ID']}:{r['FOREIGN_KEY_NUM']}",
            "ordinal": int(r["ORDINAL_POSITION"]),
            "source_table_id": r["TABLE_ID"],
            "source_table_name": r["SOURCE_TABLE_NAME"],
            "source_column_id": r["SOURCE_COLUMN_ID"],
            "source_column_name": r["SOURCE_COLUMN_NAME"],
            "destin_table_id": r["DEST_TABLE_ID"],
            "destin_table_name": r["DEST_TABLE_NAME"],
            "destin_column_id": r["DEST_COLUMN_ID"],
            "destin_column_name": r["DEST_COLUMN_NAME"],
            "conditional_c": r["CONDITIONAL_C"],
            "may_be_stale_c": r["MAY_BE_STALE_C"],
            "is_current_data_model_yn": r["IS_CURRENT_DATA_MODEL_YN"],
            "is_supplemental_yn": r["IS_SUPPLEMENTAL_YN"],
            "destin_in_scope": in_scope,
        }
        if row["source_table_id"] not in table_ids:
            violations.append(f"{row['join_id']}: source table id unknown")
        if row["source_column_id"] not in column_ids:
            violations.append(f"{row['join_id']}: source column id unknown")
        if in_scope and row["destin_table_id"] not in table_ids:
            violations.append(
                f"{row['join_id']}: in-scope destin table id unknown")
        if in_scope and row["destin_column_id"] not in column_ids:
            violations.append(
                f"{row['join_id']}: in-scope destin column id unknown")
        join_sheet.append(row)
    if violations:
        raise ValueError("join sheet FK integrity (contract loud rule): "
                         + "; ".join(violations[:20]))

    # -- iniitm and value sheets --------------------------------------
    iniitm_sheet = [
        {"column_id": r["COLUMN_ID"], "line": int(r["LINE"]),
         "column_ini": r["COLUMN_INI"], "column_item": r["COLUMN_ITEM"]}
        for r in sorted(i_rows, key=lambda r: (r["COLUMN_ID"],
                                               int(r["LINE"])))]
    value_sheet = None
    if v_rows is not None:
        value_sheet = [
            {"table_name": r["TABLE_NAME"], "code": r["CODE"],
             "meaning": r["MEANING"]}
            for r in sorted(v_rows, key=lambda r: (r["TABLE_NAME"],
                                                   r["CODE"]))]

    # -- no_dictionary_match ------------------------------------------
    no_match = []
    for key in sorted(loc):
        if key not in sheet_tables:
            db, sch = loc[key]
            no_match.append({
                "database_name": db, "schema_name": sch,
                "table_name": display[key], "column_name": "",
                "sql_file_names": sorted(file_map[key])})
    col_misses = {}
    for r in derived["columns"]:
        cname = r["column_name"]
        if cname in ("", "*"):
            continue
        tkey = _fold(r["table_name"])
        if tkey in sheet_tables and _fold(cname) not in table_columns.get(
                tkey, set()):
            col_misses.setdefault(
                (r["database_name"], r["schema_name"], r["table_name"],
                 cname), set()).add(r["sql_file_name"])
    for (db, sch, tname, cname), fnames in sorted(col_misses.items()):
        no_match.append({
            "database_name": db, "schema_name": sch, "table_name": tname,
            "column_name": cname, "sql_file_names": sorted(fnames)})

    # -- the resolution section (this script's OWN section) -----------
    table_source = {display[k]: ("emr" if k in sheet_tables
                                 else "no_dictionary_match")
                    for k in sorted(loc)}
    bindings = []
    for u in derived["unresolved"]:
        owners = sorted(t for t in u["candidates"]
                        if _fold(u["column_name"]) in table_columns.get(
                            _fold(t), set()))
        entry = {"sql_file_name": u["sql_file_name"],
                 "column_name": u["column_name"]}
        if len(owners) == 1:
            entry.update(outcome="bound", table_name=owners[0])
        elif not owners:
            entry["outcome"] = "no_match"
        else:
            entry.update(outcome="ambiguous", owners=owners)
        bindings.append(entry)
    doc["resolution"] = {"table_source": table_source,
                         "bindings": bindings}

    # -- embeddings (reuse law), then write everything ----------------
    plans = []
    t_out = out_dir / "02_emr_data_dictionary_extraction_table.json"
    for row in table_sheet:
        plans.append((row, "table_name_embedding", row["table_name"]))
        plans.append((row, "table_description_embedding",
                      row["table_description"]))
    _embed_with_reuse(table_sheet, plans, t_out, embedder, census)
    plans = []
    c_out = out_dir / "02_emr_data_dictionary_extraction_column.json"
    for row in column_sheet:
        plans.append((row, "column_name_embedding", row["column_name"]))
        plans.append((row, "column_description_embedding",
                      row["column_description"]))
    _embed_with_reuse(column_sheet, plans, c_out, embedder, census)

    with open(t_out, "w", encoding="utf-8") as f:
        json.dump(table_sheet, f, indent=2)
    with open(c_out, "w", encoding="utf-8") as f:
        json.dump(column_sheet, f, indent=2)
    with open(out_dir / "02_emr_data_dictionary_extraction_join.json",
              "w", encoding="utf-8") as f:
        json.dump(join_sheet, f, indent=2)
    with open(out_dir / "02_emr_data_dictionary_extraction_iniitm.json",
              "w", encoding="utf-8") as f:
        json.dump(iniitm_sheet, f, indent=2)
    if value_sheet is not None:
        with open(out_dir / "02_emr_data_dictionary_extraction_value.json",
                  "w", encoding="utf-8") as f:
            json.dump(value_sheet, f, indent=2)
        v_emb_out = (out_dir
                     / "02_emr_data_dictionary_extraction_value_embeddings"
                       ".json")
        sidecar = _embed_values_sidecar(
            value_sheet, v_emb_out, embedder, census)
        if ({(r["table_name"], r["code"]) for r in sidecar}
                != {(r["table_name"], r["code"]) for r in value_sheet}):
            raise ValueError(
                "value sidecar out of step with the value sheet "
                "(L09 1:1 integrity)")
        with open(v_emb_out, "w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2)
    with open(out_dir / "02_no_dictionary_match.json", "w",
              encoding="utf-8") as f:
        json.dump(no_match, f, indent=2)
    with open(extraction_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

    census.update({
        "tables": len(table_sheet), "columns": len(column_sheet),
        "joins": len(join_sheet),
        "joins_in_scope": sum(1 for j in join_sheet
                              if j["destin_in_scope"]),
        "pk_columns": sum(1 for c in column_sheet if c["is_primary_key"]),
        "iniitm": len(iniitm_sheet),
        "iniitm_multi_line_columns": len(ini_extra),
        "iniitm_unfolded_rows": sum(ini_extra.values()),
        "iniitm_no_row_columns": sum(
            1 for c in column_sheet if c["column_ini"] is None),
        "values": len(value_sheet) if value_sheet is not None else None,
        "no_match": [f"{r['table_name']}.{r['column_name']}".rstrip(".")
                     for r in no_match],
        "bindings": bindings,
    })
    return census


def main(argv):
    if len(argv) < 3:
        print("usage: python3.11 AIVIA_01_Code/build_dictionary_sheets.py "
              "<csv dir (also out dir)> <02_sql_extraction.json>",
              file=sys.stderr)
        return 2
    from local_chat import real_embedder
    census = build_sheets(argv[1], argv[2], argv[1], real_embedder)
    print("dictionary sheets census:")
    for k in ("tables", "columns", "pk_columns", "joins",
              "joins_in_scope", "iniitm", "iniitm_multi_line_columns",
              "iniitm_unfolded_rows", "iniitm_no_row_columns", "values"):
        print(f"  {k}: {census[k]}")
    print(f"  embeddings: {census['embeddings_new']} new, "
          f"{census['embeddings_reused']} reused")
    print(f"  value embeddings: {census['value_embeddings_new']} new, "
          f"{census['value_embeddings_reused']} reused")
    for m in census["no_match"]:
        print(f"  NO DICTIONARY MATCH: {m}")
    for b in census["bindings"]:
        extra = b.get("table_name") or ",".join(b.get("owners", []))
        print(f"  binding {b['column_name']} ({b['sql_file_name']}): "
              f"{b['outcome']} {extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
