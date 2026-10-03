"""Phase 02 contract tests (AIVIA_01_Design/02_emr_data_dictionary_data_contract.md).

This file grows with each phase-02 code file. Current section: the one
parse door (AIVIA_01_Code/scriptdom_loader.py, design L03/L07).

Written test-first: RED until scriptdom_loader.py exposes
    ensure_scriptdom(), parse_tsql(sql) -> (fragment, messages),
    ScriptDomUnavailable.

No API calls in this section — ScriptDom is a local native parser; the
paid-call law touches the embedding sections that come later.

One test is a standing lock, green from birth: the single-parse-door law
(ADR 0001) — no file in AIVIA_01_Code other than the loader may
instantiate the parser. It guards the law, not new behavior.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
SQL_DIR = REPO_ROOT / "AIVIA_01_Data" / "01_subject_sql_files"

sys.path.insert(0, str(CODE_DIR))
import scriptdom_loader  # noqa: E402


def subject_sql_files():
    """The 8 subject files — same rule as phase 01: every visible
    non-json file in the folder."""
    return sorted(
        p for p in SQL_DIR.iterdir()
        if p.is_file() and not p.name.startswith(".") and p.suffix != ".json"
    )


def test_the_parse_door_opens():
    # Proves pythonnet + coreclr + the libs/ DLL on this machine.
    scriptdom_loader.ensure_scriptdom()


def test_one_real_subject_file_parses_clean():
    sql = (SQL_DIR / "COOK_RPT_usp_SF_CensusDashboard").read_text(
        encoding="utf-8-sig")
    fragment, messages = scriptdom_loader.parse_tsql(sql)
    assert fragment is not None
    assert messages == []


def test_all_8_subject_files_parse_clean():
    # The phase gate: ScriptDom must clear the whole corpus before the
    # tree mapper is built on top of it.
    files = subject_sql_files()
    assert len(files) == 8, f"expected the 8 subject files, found {len(files)}"
    failures = {}
    for path in files:
        sql = path.read_text(encoding="utf-8-sig")
        fragment, messages = scriptdom_loader.parse_tsql(sql)
        if fragment is None or messages:
            failures[path.name] = messages or ["no fragment returned"]
    assert not failures, f"parse errors: {failures}"


def test_parse_errors_are_reported_never_raised():
    # An errorful parse is the CALLER's decision to reject — the door
    # reports messages, it does not raise and does not hide.
    fragment, messages = scriptdom_loader.parse_tsql("SELEC 1 FRM nowhere")
    assert messages, "broken SQL must yield error messages"
    assert all(m.startswith("L") and "C" in m.split(":")[0] for m in messages), (
        f"messages must carry L<line>C<col> positions: {messages}")


def test_single_parse_door_law():
    # ADR 0001 lock: only the loader instantiates the parser. Comment
    # lines don't count — the law is about executable code.
    offenders = []
    for path in sorted(CODE_DIR.glob("*.py")):
        if path.name == "scriptdom_loader.py":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            code = line.split("#", 1)[0]
            if "TSql160Parser(" in code:
                offenders.append(path.name)
                break
    assert not offenders, (
        f"only scriptdom_loader.py may instantiate the parser: {offenders}")


def test_unavailable_failure_is_loud_and_typed():
    # The one failure type exists and is a RuntimeError, so callers can
    # catch exactly it and surface the remediation.
    if not hasattr(scriptdom_loader, "ScriptDomUnavailable"):
        pytest.fail("ScriptDomUnavailable not defined yet (RED expected)")
    assert issubclass(scriptdom_loader.ScriptDomUnavailable, RuntimeError)


# ---------------------------------------------------------------------------
# Section 2 — the full mapped tree (AIVIA_01_Code/parse_sql_tree.py,
# design L03, contract Output File 1). RED until parse_sql_tree.py
# exposes map_tree(file_name, text) and build_extraction(sql_dir, out_path).
# Tests write only to tmp_path — the real 02_sql_extraction.json run is
# by hand, per the contract's authorship rules.
# ---------------------------------------------------------------------------

import json  # noqa: E402

import parse_sql_tree  # noqa: E402


@pytest.fixture(scope="module")
def extraction(tmp_path_factory):
    out = tmp_path_factory.mktemp("tree") / "02_sql_extraction.json"
    entries = parse_sql_tree.build_extraction(SQL_DIR, out)
    return entries, out


def _walk_nodes(obj, skip=()):
    """Yield every dict node in the tree, depth-first. Keys in `skip`
    are not descended into."""
    if isinstance(obj, dict):
        yield obj
        for k, v in obj.items():
            if k in skip:
                continue
            yield from _walk_nodes(v, skip)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_nodes(item, skip)


def test_tree_covers_all_8_files_sorted(extraction):
    entries, out = extraction
    assert out.exists(), "the json must land where the parameter says"
    names = [e["name"] for e in entries]
    assert names == sorted(names)
    assert len(entries) == 8
    for e in entries:
        assert e["node"] == "file"
        assert e["dialect"] == "tsql"
        assert e["tree_version"] == parse_sql_tree.TREE_VERSION
        assert e["statements"], f"{e['name']}: no statements mapped"


def _assert_evidence_against(container, text, label):
    checked = 0
    for node in _walk_nodes(container, skip=("reconstruction",)):
        ev = node.get("evidence")
        if not isinstance(ev, dict) or "offset" not in ev:
            continue
        start = ev["offset"]
        assert text[start:start + len(ev["fragment"])] == ev["fragment"], (
            f"{label}: evidence mismatch at offset {start}")
        checked += 1
    return checked


def test_the_evidence_law_holds_everywhere(extraction):
    # Every fragment must be the verbatim slice of the NORMALIZED text
    # at its recorded offset — the whole tree, mechanically. A
    # reconstruction's inner nodes index the reconstruction's own
    # "text", never the file — checked against that text here.
    entries, _ = extraction
    checked = 0
    for entry in entries:
        text = (SQL_DIR / entry["name"]).read_text(encoding="utf-8-sig")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        checked += _assert_evidence_against(entry, text, entry["name"])
        for node in _walk_nodes(entry):
            rec = node.get("reconstruction")
            if rec and rec.get("reconstructed"):
                checked += _assert_evidence_against(
                    {"statements": rec["statements"],
                     "remainder": rec["remainder"]},
                    rec["text"], f"{entry['name']} (reconstruction)")
    assert checked > 0, "no evidence nodes found — the tree is hollow"


def test_ground_truth_month_cte_and_clarity_adt(extraction):
    # Pinned from Sunny's file COOK_RPT_usp_SF_CensusDashboard: a CTE
    # named month_cte, and the real EMR table Clarity.dbo.CLARITY_ADT
    # read under alias adt.
    entries, _ = extraction
    [entry] = [e for e in entries
               if e["name"] == "COOK_RPT_usp_SF_CensusDashboard"]
    cte_names = [s.get("name") for stmt in entry["statements"]
                 for s in stmt.get("ctes", [])]
    assert "month_cte" in cte_names, f"CTEs found: {cte_names}"
    adt_refs = [n for n in _walk_nodes(entry)
                if n.get("table_ref") == "Clarity.dbo.CLARITY_ADT"]
    assert adt_refs, "Clarity.dbo.CLARITY_ADT not found as a table_ref"
    assert any(r.get("alias") == "adt" for r in adt_refs)


def test_joins_carry_their_type(extraction):
    entries, _ = extraction
    join_types = {j.get("join_type")
                  for entry in entries
                  for node in _walk_nodes(entry)
                  for j in node.get("join_on", [])}
    assert join_types, "no join predicates mapped across 8 census procs"
    assert None not in join_types, "a join predicate lost its join_type"


def test_remainder_is_counted_never_bare(extraction):
    entries, _ = extraction
    for entry in entries:
        for item in entry["remainder"]:
            assert item.get("type"), f"{entry['name']}: remainder without type"
            assert item.get("reason"), f"{entry['name']}: remainder without reason"
            assert "fragment" in item.get("evidence", {}), (
                f"{entry['name']}: remainder without evidence")


def test_build_is_deterministic(extraction, tmp_path):
    _, first_out = extraction
    second_out = tmp_path / "again.json"
    parse_sql_tree.build_extraction(SQL_DIR, second_out)
    assert first_out.read_bytes() == second_out.read_bytes()


def test_tree_is_json_clean(extraction):
    # The artifact must survive a round trip — no .NET objects leaking.
    # RULED 2026-09-28: the file is the growing sections dict; the
    # parse writes exactly its own section.
    entries, out = extraction
    assert json.loads(out.read_text(encoding="utf-8")) == {"files": entries}


def test_comments_banner_lands_at_file_level(extraction):
    # RULED 2026-09-28: comments before the first statement attach to
    # the file entry itself, verbatim.
    entries, _ = extraction
    [entry] = [e for e in entries
               if e["name"] == "COOK_RPT_usp_SF_CensusDashboard"]
    file_comments = entry.get("comments", [])
    assert file_comments, "header banner missing from file-level comments"
    assert any("This procedure pulls Census data from ADT" in c["text"]
               for c in file_comments)


def test_comments_trail_their_comparisons(extraction):
    # RULED 2026-09-28, the trailing/leading convention: --Census rides
    # trailing on the EVENT_TYPE_C comparison, --Canceled on the
    # EVENT_SUBTYPE_C comparison — not on a parent chain or scope.
    entries, _ = extraction
    [entry] = [e for e in entries
               if e["name"] == "COOK_RPT_usp_SF_CensusDashboard"]
    trailing = {}
    for node in _walk_nodes(entry):
        for c in node.get("comments", []):
            if c.get("position") == "trailing":
                trailing[c["text"].strip()] = node
    assert "--Census" in trailing, f"trailing comments: {list(trailing)}"
    assert "EVENT_TYPE_C" in trailing["--Census"]["evidence"]["fragment"]
    assert "--Canceled" in trailing
    assert "EVENT_SUBTYPE_C" in trailing["--Canceled"]["evidence"]["fragment"]


def test_dynamic_sql_files_are_stamped(extraction):
    # FOUND 2026-09-28: the two SSRS files run EXEC (@SQL); the tree
    # must say so — the derive step reports them as under-extracted.
    entries, _ = extraction
    flagged = {e["name"] for e in entries if e.get("dynamic_sql")}
    assert flagged == {
        "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS",
        "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Totals_SSRS",
    }, f"dynamic_sql stamps: {flagged}"


def test_order_by_is_mapped_not_remainder(extraction):
    # RULED 2026-09-28: ORDER BY joins the scope shape (5 corpus files
    # use it); it must not appear in any remainder.
    entries, _ = extraction
    assert any(node.get("order_by")
               for entry in entries for node in _walk_nodes(entry)), (
        "no order_by mapped anywhere, but 5 corpus files use it")
    for entry in entries:
        for item in entry["remainder"]:
            assert "order by" not in item["evidence"]["fragment"].lower()[:20], (
                f"{entry['name']}: an ORDER BY fell into remainder")


def test_dynamic_sql_reconstruction_reads_clarity(extraction):
    # RULED 2026-09-28: the approved reconstruction — both SSRS files'
    # EXEC (@SQL) must yield a parsed inner tree whose from_refs reach
    # Clarity.dbo.CLARITY_ADT (the read that was invisible before).
    entries, _ = extraction
    for name in ("Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS",
                 "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Totals_SSRS"):
        [entry] = [e for e in entries if e["name"] == name]
        recs = [node["reconstruction"] for node in _walk_nodes(entry)
                if node.get("statement_kind") == "EXECUTE"
                and "reconstruction" in node]
        assert recs, f"{name}: EXEC statement has no reconstruction"
        ok = [r for r in recs if r.get("reconstructed")]
        assert ok, (f"{name}: reconstruction failed: "
                    f"{[r.get('errors') for r in recs]}")
        tables = {n.get("table_ref") for r in ok
                  for n in _walk_nodes(r["statements"])}
        assert "Clarity.dbo.CLARITY_ADT" in tables, (
            f"{name}: inner tables found: {sorted(t for t in tables if t)}")


# ---------------------------------------------------------------------------
# Section 3 — the construct master (contract Output File 6,
# 02_tsql_construct_master.json).
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def master(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("master")
    out = out_dir / "02_sql_extraction.json"
    master_path = out_dir / "02_tsql_construct_master.json"
    entries = parse_sql_tree.build_extraction(SQL_DIR, out, master_path)
    rows = json.loads(master_path.read_text(encoding="utf-8"))
    return entries, master_path, rows


def test_master_inventory_is_complete_by_construction(master):
    # The inventory comes from the parser DLL by reflection — the whole
    # t-sql grammar, present before any file arrives.
    _, _, rows = master
    assert len(rows) > 500, f"only {len(rows)} constructs — reflection failed?"
    names = [r["construct"] for r in rows]
    assert names == sorted(names)
    assert len(names) == len(set(names))
    for r in rows:
        assert r["status"] in ("mapped", "remainder", "unseen")


def test_master_statuses_agree_with_the_trees(master):
    # Every construct type that landed in a tree remainder must carry
    # master status "remainder" — the master cannot claim it mapped.
    entries, _, rows = master
    by_name = {r["construct"]: r for r in rows}
    tree_remainder_types = {item["type"] for entry in entries
                            for item in entry["remainder"]}
    for t in tree_remainder_types:
        assert by_name[t]["status"] == "remainder", (
            f"{t} is in tree remainder but master says "
            f"{by_name[t]['status']}")
        assert by_name[t]["count_in_corpus"] > 0


def test_master_preserves_sunny_rulings(master, tmp_path):
    # The phase-01 sheet law: script columns regenerate, Sunny's ruling
    # column survives every rebuild.
    _, master_path, rows = master
    target = next(r for r in rows if r["status"] == "unseen")
    for r in rows:
        if r["construct"] == target["construct"]:
            r["ruling"] = "test ruling — must survive"
    master_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    out = tmp_path / "again.json"
    parse_sql_tree.build_extraction(SQL_DIR, out, master_path)
    rebuilt = json.loads(master_path.read_text(encoding="utf-8"))
    kept = next(r for r in rebuilt if r["construct"] == target["construct"])
    assert kept["ruling"] == "test ruling — must survive"


def test_the_construct_lock_every_observed_remainder_is_ruled():
    # THE LOCK (contract loud rule 1): a construct that appears in our
    # sql files without a ruling turns this red, naming it. It reads
    # the REAL landed master — rulings live there and only there.
    real_master = (REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
                   / "02_tsql_construct_master.json")
    assert real_master.exists(), (
        "the construct master has not been landed yet — run "
        "parse_sql_tree.py with the master path")
    rows = json.loads(real_master.read_text(encoding="utf-8"))
    unruled = [f"{r['construct']} (count {r['count_in_corpus']})"
               for r in rows
               if r["status"] == "remainder" and not r["ruling"].strip()]
    assert not unruled, (
        "constructs observed in the corpus, awaiting Sunny's ruling: "
        + "; ".join(unruled))


# ---------------------------------------------------------------------------
# Section 4 — the "derived" section of the ONE growing sql-side file +
# the discovery query (AIVIA_01_Code/derive_tables_columns.py; contract
# Output File 1 "derived" + Output File 3 first move). RED until
# derive_tables_columns.py exposes derive_used, write_discovery_sql,
# write_extraction_sql. The derive step reads the growing file, never
# sql files; tests work on a tmp COPY of the landed artifact.
# ---------------------------------------------------------------------------

import shutil  # noqa: E402

import derive_tables_columns  # noqa: E402

TREE_PATH = (REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
             / "02_sql_extraction.json")


@pytest.fixture(scope="module")
def derived(tmp_path_factory):
    work = tmp_path_factory.mktemp("derived") / "02_sql_extraction.json"
    shutil.copy(TREE_PATH, work)
    result = derive_tables_columns.derive_used(work)
    doc = json.loads(work.read_text(encoding="utf-8"))
    return result, doc, work


def test_derived_lands_inside_the_growing_file(derived):
    result, doc, _ = derived
    assert doc["derived"] == result
    original = json.loads(TREE_PATH.read_text(encoding="utf-8"))
    assert doc["files"] == original["files"], (
        "derive touched the files section — section ownership violated")


def test_census_is_one_list_with_classes(derived):
    # RULED 2026-09-28 (Sunny): every table-like name in ONE census —
    # nothing set aside where a mislabel could hide.
    result, _, _ = derived
    by_name = {}
    for row in result["tables"]:
        by_name.setdefault(row["name"].lower(), set()).add(row["class"])
    assert by_name["month_cte"] == {"cte"}
    assert any(n.startswith("#") and cls == {"temp_table"}
               for n, cls in by_name.items())
    assert by_name["string_split"] == {"table_function"}
    assert "emr_or_enterprise_table" in by_name["clarity_adt"]
    for row in result["tables"]:
        assert row["source"] == "pending", "source is step 5's verdict"


def test_clarity_adt_from_static_and_dynamic(derived):
    result, _, _ = derived
    adt = [r for r in result["tables"]
           if r["name"] == "CLARITY_ADT"
           and r["class"] == "emr_or_enterprise_table"]
    assert adt, "CLARITY_ADT missing from the census"
    # T-SQL identifiers are case-insensitive; one corpus file writes
    # "clarity" lowercase — the census keeps the written casing, the
    # comparison folds.
    assert all(r["database_name"].upper() == "CLARITY"
               and r["schema_name"] == "dbo" for r in adt)
    files = {r["sql_file_name"] for r in adt}
    assert "COOK_RPT_usp_SF_CensusDashboard" in files
    assert "Reporting_USP_CCHCS_CC_ADT_Monthly_IP_Census_Days_SSRS" in files, (
        "the dynamic-SQL file did not contribute its reconstructed reads")


def test_used_columns_bind_via_alias(derived):
    result, _, _ = derived
    assert any(r["table_name"] == "CLARITY_ADT"
               and r["column_name"] == "EFFECTIVE_TIME"
               for r in result["columns"])


def test_no_real_table_lacks_a_database(derived):
    # Corpus fact (checked 2026-09-28): every real-table ref in the 8
    # files is explicitly qualified — so no census row may carry a
    # blank database. If a future file breaks this, the USE fallback
    # (pinned below) is what fills it.
    result, _, _ = derived
    real = [r for r in result["tables"]
            if r["class"] == "emr_or_enterprise_table"]
    assert real
    assert all(r["database_name"] for r in real), (
        sorted({r["written_as"] for r in real if not r["database_name"]}))


def test_use_fallback_mechanism(tmp_path):
    # The mechanism itself, on a minimal synthetic tree: an unqualified
    # table in a file with USE gets the USE database + the org-fact
    # dbo schema.
    doc = {"files": [{
        "node": "file", "name": "synthetic", "dialect": "tsql",
        "tree_version": "1.0.0", "comments": [], "remainder": [],
        "statements": [
            {"statement_kind": "USE", "position": 1, "database": "CookClarity",
             "evidence": {"fragment": "USE CookClarity", "offset": 0,
                          "line": 1, "column": 1}},
            {"statement_kind": "SELECT", "position": 2,
             "evidence": {"fragment": "select A from PATIENT", "offset": 16,
                          "line": 2, "column": 1},
             "scope": {"node": "scope",
                       "from_refs": [{"table_ref": "PATIENT", "alias": None,
                                      "evidence": {"fragment": "PATIENT",
                                                   "offset": 30, "line": 2,
                                                   "column": 15}}],
                       "join_on": [], "projection": [],
                       "evidence": {"fragment": "select A from PATIENT",
                                    "offset": 16, "line": 2, "column": 1}}},
        ]}]}
    work = tmp_path / "02_sql_extraction.json"
    work.write_text(json.dumps(doc), encoding="utf-8")
    result = derive_tables_columns.derive_used(work)
    [row] = [r for r in result["tables"]
             if r["class"] == "emr_or_enterprise_table"]
    assert row["name"] == "PATIENT"
    assert row["database_name"] == "CookClarity"
    assert row["schema_name"] == "dbo"  # the contract's org-fact line


def test_unresolved_carry_candidates_never_bindings(derived):
    result, _, _ = derived
    for u in result["unresolved"]:
        assert u["candidates"], f"unresolved without candidates: {u}"
        assert "table_name" not in u, "an unresolved column got a binding"


def test_derive_is_deterministic(derived, tmp_path):
    _, _, work = derived
    again = tmp_path / "02_sql_extraction.json"
    shutil.copy(TREE_PATH, again)
    derive_tables_columns.derive_used(again)
    derive_tables_columns.derive_used(again)  # twice on purpose
    assert (json.loads(again.read_text(encoding="utf-8"))["derived"]
            == json.loads(work.read_text(encoding="utf-8"))["derived"])


def test_discovery_sql_names_the_dictionary_tables(tmp_path):
    derive_tables_columns.write_discovery_sql(tmp_path)
    sql = (tmp_path / "02_emr_data_dictionary_discovery.sql").read_text(
        encoding="utf-8")
    assert "CLARITY_TBL" in sql
    assert "CLARITY_COL" in sql
    assert "INFORMATION_SCHEMA" in sql.upper()


FACTS_PATH = (REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
              / "02_emr_data_dictionary_discovery_facts.md")


def test_extraction_sql_refuses_without_discovery_facts(tmp_path):
    # The no-guessing law: the queries generate only from the recorded
    # discovery facts.
    with pytest.raises(Exception, match="discovery"):
        derive_tables_columns.write_extraction_sql(
            TREE_PATH, tmp_path / "missing_facts.md", tmp_path)


@pytest.fixture(scope="module")
def extraction_sql(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("move2")
    paths = derive_tables_columns.write_extraction_sql(
        TREE_PATH, FACTS_PATH, out_dir)
    return {p.name: p.read_text(encoding="utf-8") for p in paths}


def test_move2_writes_the_five_queries(extraction_sql):
    assert sorted(extraction_sql) == [
        "02_emr_data_dictionary_extraction_column.sql",
        "02_emr_data_dictionary_extraction_iniitm.sql",
        "02_emr_data_dictionary_extraction_join.sql",
        "02_emr_data_dictionary_extraction_pk.sql",
        "02_emr_data_dictionary_extraction_table.sql",
    ]


def test_move2_queries_carry_the_rulings(extraction_sql):
    for name, sql in extraction_sql.items():
        # Sunny's de-dup filter on every query.
        assert "TBL_DESCRIPTOR_OVR IS NOT NULL" in sql, name
        # Standalone literal IN list with the used tables, casing
        # folded to ONE entry per table.
        assert sql.count("'CLARITY_ADT'") == 1, name
        assert "'V_REPORT_RUN_FACT'" in sql, name
    join_sql = extraction_sql["02_emr_data_dictionary_extraction_join.sql"]
    assert "CLARITY_TBL_FK_ALL" in join_sql
    assert "FOREIGN_KEY_NUM" in join_sql and "ORDINAL_POSITION" in join_sql
    assert "CONDITIONAL_C" in join_sql  # flags ride along, unfiltered
    table_sql = extraction_sql["02_emr_data_dictionary_extraction_table.sql"]
    assert "TABLE_INTRODUCTION" in table_sql  # the ruled description
    assert "DEPRECATED_YN" in table_sql  # rides, never filters
    pk_sql = extraction_sql["02_emr_data_dictionary_extraction_pk.sql"]
    assert "CLARITY_TBL_PK" in pk_sql and "PK_COLUMN_ID" in pk_sql
    ini_sql = extraction_sql["02_emr_data_dictionary_extraction_iniitm.sql"]
    assert "CLARITY_COL_INIITM" in ini_sql


# ---------------------------------------------------------------------------
# Section 5 — move 3: the values query, derived from Sunny's csvs.
# ---------------------------------------------------------------------------

CSV_DIR = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"


def test_values_sql_refuses_without_join_csv(tmp_path):
    with pytest.raises(Exception, match="join csv"):
        derive_tables_columns.write_values_sql(
            TREE_PATH, tmp_path / "missing_join.csv",
            CSV_DIR / "02_emr_data_dictionary_extraction_column.csv",
            tmp_path)


def test_values_sql_derives_id_columns_from_data(tmp_path):
    out, skipped = derive_tables_columns.write_values_sql(
        TREE_PATH,
        CSV_DIR / "02_emr_data_dictionary_extraction_join.csv",
        CSV_DIR / "02_emr_data_dictionary_extraction_column.csv",
        tmp_path)
    sql = out.read_text(encoding="utf-8")
    assert "'ZC_PAT_CLASS'" in sql, "used ZC table missing from values query"
    assert "UNION ALL" in sql and "AS MEANING" in sql
    # every skip is counted in the header, never silent
    for s in skipped:
        assert s in sql
    # Sunny's ruled CLARITY_* category tables (contract 2026-09-28)
    assert "'CLARITY_DEP'" in sql and "DEPARTMENT_NAME AS MEANING" in sql
    assert "'CLARITY_BED'" in sql and "BED_LABEL AS MEANING" in sql
    # CLARITY_ADT is ruled NOT a category table
    assert "'CLARITY_ADT'" not in sql


# ---------------------------------------------------------------------------
# Section 6 — the dictionary sheets (AIVIA_01_Code/build_dictionary_sheets.py,
# contract Output File 5 + no_dictionary_match + the resolution section).
# RED until the real code lands. Tiny synthetic csvs keep the paid
# embedding calls at pennies; the full-corpus run is Sunny's hand.
# ---------------------------------------------------------------------------

import build_dictionary_sheets  # noqa: E402
from test_01_subject_sql_files_data_contract import real_embedder  # noqa: E402


def _mini_csvs(root):
    """A 2-table synthetic dictionary matching the discovery shapes."""
    (root / "02_emr_data_dictionary_extraction_table.csv").write_text(
        "TABLE_ID\tTABLE_NAME\tTABLE_INTRODUCTION\tDEPRECATED_YN\n"
        "T1\tPATIENT\tThe patient table.\tN\n"
        "T2\tZC_SEX\tSex categories.\tN\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_column.csv").write_text(
        "COLUMN_ID\tTABLE_ID\tTABLE_NAME\tCOLUMN_NAME\tDATA_TYPE\t"
        "DESCRIPTION\tDEPRECATED_YN\n"
        "C1\tT1\tPATIENT\tPAT_ID\tVARCHAR\tThe patient id.\tN\n"
        "C2\tT1\tPATIENT\tSEX_C\tINTEGER\tThe sex category.\tN\n"
        "C3\tT2\tZC_SEX\tSEX_C\tINTEGER\tCategory value.\tN\n"
        "C4\tT2\tZC_SEX\tNAME\tVARCHAR\tCategory name.\tN\n",
        encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_join.csv").write_text(
        "TABLE_ID\tFOREIGN_KEY_NUM\tORDINAL_POSITION\tSOURCE_TABLE_NAME\t"
        "SOURCE_COLUMN_ID\tSOURCE_COLUMN_NAME\tDEST_TABLE_ID\t"
        "DEST_TABLE_NAME\tDEST_COLUMN_ID\tDEST_COLUMN_NAME\tCONDITIONAL_C\t"
        "MAY_BE_STALE_C\tIS_CURRENT_DATA_MODEL_YN\tIS_SUPPLEMENTAL_YN\n"
        "T1\t1\t1\tPATIENT\tC2\tSEX_C\tT2\tZC_SEX\tC3\tSEX_C\t3\t2\tY\tN\n"
        "T1\t2\t1\tPATIENT\tC1\tPAT_ID\tT9\tOUTSIDE_TBL\tC9\tPAT_ID\t3\t2\tY\tN\n",
        encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_pk.csv").write_text(
        "TABLE_ID\tTABLE_NAME\tLINE\tPK_COLUMN_ID\tCOLUMN_DESCRIPTOR\n"
        "T1\tPATIENT\t1\tC1\tPATIENT__PAT_ID\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_iniitm.csv").write_text(
        "COLUMN_ID\tLINE\tCOLUMN_INI\tCOLUMN_ITEM\n"
        "C1\t1\tEPT\t.1\n", encoding="utf-8")
    doc = {"files": [], "derived": {
        "tables": [
            {"sql_file_name": "f1", "name": "PATIENT",
             "class": "emr_or_enterprise_table", "database_name": "Clarity",
             "schema_name": "dbo", "source": "pending",
             "written_as": "Clarity.dbo.PATIENT"},
            {"sql_file_name": "f1", "name": "ZC_SEX",
             "class": "emr_or_enterprise_table", "database_name": "Clarity",
             "schema_name": "dbo", "source": "pending",
             "written_as": "Clarity.dbo.ZC_SEX"},
            {"sql_file_name": "f1", "name": "GHOST_TBL",
             "class": "emr_or_enterprise_table", "database_name": "Clarity",
             "schema_name": "dbo", "source": "pending",
             "written_as": "Clarity.dbo.GHOST_TBL"},
        ],
        "columns": [], "anomalies": [],
        "unresolved": [
            {"sql_file_name": "f1", "column_name": "SEX_C",
             "candidates": ["PATIENT", "ZC_SEX"]},
            {"sql_file_name": "f1", "column_name": "PAT_ID",
             "candidates": ["PATIENT", "GHOST_TBL"]},
        ]}}
    tree = root / "02_sql_extraction.json"
    tree.write_text(json.dumps(doc), encoding="utf-8")
    return tree


@pytest.fixture(scope="module")
def sheets(tmp_path_factory):
    root = tmp_path_factory.mktemp("sheets")
    tree = _mini_csvs(root)
    census = build_dictionary_sheets.build_sheets(
        root, tree, root, real_embedder)
    def load(kind):
        return json.loads(
            (root / f"02_emr_data_dictionary_extraction_{kind}.json")
            .read_text(encoding="utf-8"))
    return census, load, root, tree


def test_sheets_table_and_column_shapes(sheets):
    _, load, _, _ = sheets
    [pat, zc] = load("table")
    assert pat["table_name"] == "PATIENT"
    assert pat["database_name"] == "Clarity" and pat["schema_name"] == "dbo"
    assert pat["table_description"] == "The patient table."
    assert len(pat["table_name_embedding"]) == 3072
    assert len(pat["table_description_embedding"]) == 3072
    cols = load("column")
    pat_id = next(c for c in cols if c["column_name"] == "PAT_ID")
    assert pat_id["is_primary_key"] is True and pat_id["key_ordinal"] == 1
    assert pat_id["data_type"] == "VARCHAR"
    assert len(pat_id["column_name_embedding"]) == 3072
    sex = next(c for c in cols
               if c["column_name"] == "SEX_C" and c["table_name"] == "PATIENT")
    assert sex["is_primary_key"] is False


def test_sheets_join_ids_and_scope_flags(sheets):
    _, load, _, _ = sheets
    joins = load("join")
    in_scope = next(j for j in joins if j["destin_table_name"] == "ZC_SEX")
    assert in_scope["join_id"] == "T1:1" and in_scope["ordinal"] == 1
    assert in_scope["destin_in_scope"] is True
    outside = next(j for j in joins if j["destin_table_name"] == "OUTSIDE_TBL")
    assert outside["destin_in_scope"] is False


def test_no_dictionary_match_is_counted(sheets):
    _, _, root, _ = sheets
    rows = json.loads((root / "02_no_dictionary_match.json")
                      .read_text(encoding="utf-8"))
    assert any(r["table_name"] == "GHOST_TBL" and r["column_name"] == ""
               for r in rows)


def test_resolution_binds_the_two_step(sheets):
    _, _, _, tree = sheets
    doc = json.loads(tree.read_text(encoding="utf-8"))
    res = doc["resolution"]
    assert res["table_source"]["PATIENT"] == "emr"
    assert res["table_source"]["GHOST_TBL"] == "no_dictionary_match"
    # SEX_C exists in BOTH candidates -> ambiguous, owners listed
    sex = next(b for b in res["bindings"] if b["column_name"] == "SEX_C")
    assert sex["outcome"] == "ambiguous"
    assert sorted(sex["owners"]) == ["PATIENT", "ZC_SEX"]
    # PAT_ID exists only in PATIENT (GHOST has no columns) -> bound
    pat = next(b for b in res["bindings"] if b["column_name"] == "PAT_ID")
    assert pat["outcome"] == "bound" and pat["table_name"] == "PATIENT"


def test_blank_description_fails_loudly(tmp_path):
    tree = _mini_csvs(tmp_path)
    bad = tmp_path / "02_emr_data_dictionary_extraction_table.csv"
    bad.write_text(
        "TABLE_ID\tTABLE_NAME\tTABLE_INTRODUCTION\tDEPRECATED_YN\n"
        "T1\tPATIENT\t\tN\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PATIENT"):
        build_dictionary_sheets.build_sheets(
            tmp_path, tree, tmp_path, real_embedder)


def test_wrong_header_fails_naming_the_file(tmp_path):
    tree = _mini_csvs(tmp_path)
    bad = tmp_path / "02_emr_data_dictionary_extraction_pk.csv"
    bad.write_text("WRONG\tHEADER\nx\ty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pk"):
        build_dictionary_sheets.build_sheets(
            tmp_path, tree, tmp_path, real_embedder)


def test_embeddings_reused_on_unchanged_rerun(sheets, tmp_path):
    _, _, root, tree = sheets
    def forbidden_embedder(texts):
        raise AssertionError(f"re-embedded unchanged texts: {texts[:2]}")
    census = build_dictionary_sheets.build_sheets(
        root, tree, root, forbidden_embedder)
    assert census["embeddings_new"] == 0
    assert census["embeddings_reused"] > 0


# ---------------------------------------------------------------------------
# Section 6b — the L09 amendments (ruled 2026-09-29, design L08 + L09):
# iniitm LINE 1 folds into the column sheet as column_ini/column_item
# (more lines counted, never silently dropped — the iniitm sheet keeps
# every line), and the value-embeddings SIDECAR file (meaning text only,
# 1:1 with the value sheet, reuse law keyed table_name + code + meaning).
# RED until the amendment code lands in build_dictionary_sheets.py.
# ---------------------------------------------------------------------------


def _mini_csvs_l09(root):
    """The mini dictionary plus a multi-line iniitm and a values csv."""
    tree = _mini_csvs(root)
    (root / "02_emr_data_dictionary_extraction_iniitm.csv").write_text(
        "COLUMN_ID\tLINE\tCOLUMN_INI\tCOLUMN_ITEM\n"
        "C1\t1\tEPT\t.1\n"
        "C1\t2\tEPT\t111.00\n"  # the date+time pair shape — NOT folded
        "C2\t1\tEPT\t130.00\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_value.csv").write_text(
        "TABLE_NAME\tCODE\tMEANING\n"
        "ZC_SEX\t1\tFemale\n"
        "ZC_SEX\t2\tMale\n", encoding="utf-8")
    return tree


@pytest.fixture(scope="module")
def sheets_l09(tmp_path_factory):
    root = tmp_path_factory.mktemp("sheets_l09")
    tree = _mini_csvs_l09(root)
    census = build_dictionary_sheets.build_sheets(
        root, tree, root, real_embedder)

    def load(name):
        return json.loads(
            (root / f"02_emr_data_dictionary_extraction_{name}.json")
            .read_text(encoding="utf-8"))
    return census, load, root, tree


def test_column_sheet_folds_iniitm_line1_only(sheets_l09):
    census, load, _, _ = sheets_l09
    cols = {c["column_id"]: c for c in load("column")}
    # C1 has two lines: line 1 folds, line 2 does not.
    assert cols["C1"]["column_ini"] == "EPT"
    assert cols["C1"]["column_item"] == ".1"
    # C2 has one line: it folds.
    assert cols["C2"]["column_ini"] == "EPT"
    assert cols["C2"]["column_item"] == "130.00"
    # C3/C4 have no iniitm row: None for both, legal, counted.
    assert cols["C3"]["column_ini"] is None
    assert cols["C3"]["column_item"] is None
    # The ledger counts (nothing dropped silently).
    assert census["iniitm_multi_line_columns"] == 1
    assert census["iniitm_unfolded_rows"] == 1
    assert census["iniitm_no_row_columns"] == 2
    # The iniitm sheet keeps EVERY line — the record loses nothing.
    assert len(load("iniitm")) == 3


def test_value_sidecar_is_1to1_with_the_value_sheet(sheets_l09):
    _, load, _, _ = sheets_l09
    values = load("value")
    sidecar = load("value_embeddings")
    assert len(sidecar) == len(values) == 2
    assert ({(r["table_name"], r["code"]) for r in sidecar}
            == {(r["table_name"], r["code"]) for r in values})
    for row in sidecar:
        # meaning rides along so reuse checks are self-contained
        assert set(row) == {"table_name", "code", "meaning",
                            "meaning_embedding"}
        assert len(row["meaning_embedding"]) == 3072


def test_value_sidecar_reuse_on_unchanged_rerun(sheets_l09):
    _, _, root, tree = sheets_l09

    def forbidden_embedder(texts):
        raise AssertionError(f"re-embedded unchanged texts: {texts[:2]}")
    census = build_dictionary_sheets.build_sheets(
        root, tree, root, forbidden_embedder)
    assert census["value_embeddings_new"] == 0
    assert census["value_embeddings_reused"] == 2
    # the iniitm fold added no embedded texts either
    assert census["embeddings_new"] == 0


def test_sidecar_tracks_the_value_sheet_exactly(tmp_path):
    tree = _mini_csvs_l09(tmp_path)
    build_dictionary_sheets.build_sheets(
        tmp_path, tree, tmp_path, real_embedder)
    # Sunny re-exports: one row gone, one meaning changed.
    (tmp_path / "02_emr_data_dictionary_extraction_value.csv").write_text(
        "TABLE_NAME\tCODE\tMEANING\n"
        "ZC_SEX\t1\tFemale patient\n", encoding="utf-8")
    census = build_dictionary_sheets.build_sheets(
        tmp_path, tree, tmp_path, real_embedder)
    sidecar = json.loads(
        (tmp_path / "02_emr_data_dictionary_extraction_value_embeddings"
         ".json").read_text(encoding="utf-8"))
    # exactly the current value sheet — the dropped code 2 is gone
    assert [(r["table_name"], r["code"]) for r in sidecar] == [("ZC_SEX", "1")]
    # the changed meaning was re-embedded, nothing else
    assert census["value_embeddings_new"] == 1
    assert census["value_embeddings_reused"] == 0


# ---------------------------------------------------------------------------
# Section 7 — the phase 02 graph ENGINE (AIVIA_01_Code/dictionary_graph.py,
# design L08 + L09; split out of the retired L06 chat per 03_chat_bot.md
# L04). Synthetic sheets keep the paid calls at pennies; the real-sheet
# tests are structural only (zero embedding cost). The L06 answer/page
# tests retired with the page — the 03 build brings its own, red first.
# ---------------------------------------------------------------------------

import dictionary_graph  # noqa: E402

DATA_DIR = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"


def _graph_csvs(root):
    """A 5-table synthetic estate exercising every edge kind: an fk
    chain, a composite join, a DATETIME rule edge pair, an island, and
    a ghost table for the no-match note."""
    (root / "02_emr_data_dictionary_extraction_table.csv").write_text(
        "TABLE_ID\tTABLE_NAME\tTABLE_INTRODUCTION\tDEPRECATED_YN\n"
        "T1\tPATIENT\tThe patient table.\tN\n"
        "T2\tZC_SEX\tSex categories.\tN\n"
        "T3\tPAT_ENC\tThe encounter table.\tN\n"
        "T4\tDATE_DIMENSION\tThe date dimension table.\tN\n"
        "T5\tISLAND_TBL\tAn isolated table.\tN\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_column.csv").write_text(
        "COLUMN_ID\tTABLE_ID\tTABLE_NAME\tCOLUMN_NAME\tDATA_TYPE\t"
        "DESCRIPTION\tDEPRECATED_YN\n"
        "C1\tT1\tPATIENT\tPAT_ID\tVARCHAR\tThe patient id.\tN\n"
        "C2\tT1\tPATIENT\tSEX_C\tINTEGER\tThe sex category code.\tN\n"
        "C3\tT2\tZC_SEX\tSEX_C\tINTEGER\tCategory value.\tN\n"
        "C4\tT2\tZC_SEX\tNAME\tVARCHAR\tCategory name.\tN\n"
        "C5\tT3\tPAT_ENC\tPAT_ID\tVARCHAR\tThe encounter's patient id.\tN\n"
        "C6\tT3\tPAT_ENC\tCONTACT_DATE\tDATETIME\tThe encounter date.\tN\n"
        "C7\tT4\tDATE_DIMENSION\tCALENDAR_DT\tDATETIME\tThe calendar date.\tN\n"
        "C8\tT5\tISLAND_TBL\tISLAND_ID\tVARCHAR\tThe island id.\tN\n"
        "C9\tT3\tPAT_ENC\tSEX_C\tINTEGER\tThe encounter sex code.\tN\n"
        "C10\tT3\tPAT_ENC\tDISCH_DATE\tDATETIME\tThe discharge date.\tN\n",
        encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_join.csv").write_text(
        "TABLE_ID\tFOREIGN_KEY_NUM\tORDINAL_POSITION\tSOURCE_TABLE_NAME\t"
        "SOURCE_COLUMN_ID\tSOURCE_COLUMN_NAME\tDEST_TABLE_ID\t"
        "DEST_TABLE_NAME\tDEST_COLUMN_ID\tDEST_COLUMN_NAME\tCONDITIONAL_C\t"
        "MAY_BE_STALE_C\tIS_CURRENT_DATA_MODEL_YN\tIS_SUPPLEMENTAL_YN\n"
        "T3\t1\t1\tPAT_ENC\tC5\tPAT_ID\tT1\tPATIENT\tC1\tPAT_ID\t3\t2\tY\tN\n"
        "T1\t1\t1\tPATIENT\tC2\tSEX_C\tT2\tZC_SEX\tC3\tSEX_C\t3\t2\tY\tN\n"
        "T3\t2\t1\tPAT_ENC\tC5\tPAT_ID\tT1\tPATIENT\tC1\tPAT_ID\t3\t2\tY\tN\n"
        "T3\t2\t2\tPAT_ENC\tC9\tSEX_C\tT1\tPATIENT\tC2\tSEX_C\t3\t2\tY\tN\n"
        "T1\t2\t1\tPATIENT\tC1\tPAT_ID\tT9\tOUTSIDE_TBL\tC99\tPAT_ID\t3\t2\tY\tN\n",
        encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_pk.csv").write_text(
        "TABLE_ID\tTABLE_NAME\tLINE\tPK_COLUMN_ID\tCOLUMN_DESCRIPTOR\n"
        "T1\tPATIENT\t1\tC1\tPATIENT__PAT_ID\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_iniitm.csv").write_text(
        "COLUMN_ID\tLINE\tCOLUMN_INI\tCOLUMN_ITEM\n"
        "C1\t1\tEPT\t.1\n", encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_value.csv").write_text(
        "TABLE_NAME\tCODE\tMEANING\n"
        "ZC_SEX\t1\tFemale\n"
        "ZC_SEX\t2\tMale\n", encoding="utf-8")
    doc = {"files": [], "derived": {
        "tables": [
            {"sql_file_name": "f1", "name": n,
             "class": "emr_or_enterprise_table", "database_name": "Clarity",
             "schema_name": "dbo", "source": "pending",
             "written_as": f"Clarity.dbo.{n}"}
            for n in ("PATIENT", "ZC_SEX", "PAT_ENC", "DATE_DIMENSION",
                      "ISLAND_TBL", "GHOST_TBL")],
        "columns": [], "anomalies": [], "unresolved": []}}
    tree = root / "02_sql_extraction.json"
    tree.write_text(json.dumps(doc), encoding="utf-8")
    return tree


@pytest.fixture(scope="module")
def mini_graph(tmp_path_factory):
    root = tmp_path_factory.mktemp("graph")
    tree = _graph_csvs(root)
    build_dictionary_sheets.build_sheets(root, tree, root, real_embedder)
    sheets = dictionary_graph.load_sheets(root)
    graph = dictionary_graph.build_graph(sheets)
    return sheets, graph


def test_graph_fk_edges_group_by_join_id(mini_graph):
    _, graph = mini_graph
    fk = {k: e for k, e in graph["edges"].items()
          if e["kind"] == "joins_by_fk"}
    # 3 in-scope join_ids: T3:1, T1:1, T3:2 — the outside row is no edge
    assert set(fk) == {"T3:1", "T1:1", "T3:2"}
    # the composite join is ONE edge with its ordered pairs assembled
    comp = fk["T3:2"]
    assert [(p["source_column_name"], p["destin_column_name"])
            for p in comp["column_pairs"]] == [("PAT_ID", "PAT_ID"),
                                               ("SEX_C", "SEX_C")]


def test_graph_rule_edges_are_parallel_and_derived(mini_graph):
    _, graph = mini_graph
    rule = {k: e for k, e in graph["edges"].items()
            if e["kind"] == "joins_by_rule"}
    # C6 and C10 (DATETIME, outside DATE_DIMENSION) — C7 never self-joins
    assert set(rule) == {"rule:date_dimension:C6",
                         "rule:date_dimension:C10"}
    for e in rule.values():
        assert e["destin_table_name"] == "DATE_DIMENSION"
        assert e["column_pairs"][0]["destin_column_name"] == "CALENDAR_DT"


def test_graph_census_counts_and_components(mini_graph):
    _, graph = mini_graph
    census = graph["census"]
    assert census["tables"] == 5 and census["columns"] == 10
    assert census["joins_by_fk"] == 3 and census["joins_by_rule"] == 2
    comps = sorted(census["components"], key=len, reverse=True)
    assert len(comps) == 2 and comps[1] == ["ISLAND_TBL"]


def test_connect_unions_pairwise_paths(mini_graph):
    _, graph = mini_graph
    sub = dictionary_graph.connect(
        graph, [graph["tables_by_name"][n]
                for n in ("ZC_SEX", "DATE_DIMENSION", "PAT_ENC")])
    # PATIENT joins the subgraph as the shared intermediate, ONCE
    assert sorted(sub["tables"]) == ["DATE_DIMENSION", "PATIENT",
                                     "PAT_ENC", "ZC_SEX"]
    assert not sub["gaps"]
    # every hop cites a real edge with its kind
    for hop in sub["hops"]:
        assert hop["edge_key"] in graph["edges"]
        assert hop["edge_kind"] in ("joins_by_fk", "joins_by_rule")
    # no duplicate edges even though pairs share the PATIENT bridge
    keys = [h["edge_key"] for h in sub["hops"]]
    assert len(keys) == len(set(keys))


def test_connect_reports_gaps_never_invents(mini_graph):
    _, graph = mini_graph
    sub = dictionary_graph.connect(
        graph, [graph["tables_by_name"][n]
                for n in ("PATIENT", "ISLAND_TBL")])
    assert sub["gaps"] == [{"from": "ISLAND_TBL", "to": "PATIENT"}] or \
        sub["gaps"] == [{"from": "PATIENT", "to": "ISLAND_TBL"}]
    assert "ISLAND_TBL" in sub["tables"]  # the anchor stays visible


def test_accept_has_no_cliffs_and_honors_the_split():
    scored = [
        {"kind": "table", "name": "A", "table_name": "A",
         "scores": {"name": 0.30, "description": 0.30}},   # sum .6, best .3
        {"kind": "table", "name": "B", "table_name": "B",
         "scores": {"name": 0.45, "description": 0.10}},   # best .45
        {"kind": "table", "name": "C", "table_name": "C",
         "scores": {"name": 0.28, "description": 0.05}},   # floor only
        {"kind": "table", "name": "D", "table_name": "D",
         "scores": {"name": 0.10, "description": 0.05}},   # below floor
    ]
    anchors, candidates = dictionary_graph.accept(
        scored, floor=0.25, match=0.4, margin=0.1)
    # best-single decides the match: B anchors, A does NOT despite the sum
    assert [a["name"] for a in anchors] == ["B"]
    cand_names = [c["name"] for c in candidates]
    # A and C stay visible with scores — thresholds are never cliffs
    assert "A" in cand_names and "C" in cand_names
    assert "D" not in cand_names  # below floor may be unknown
    # margin: a second anchor outside the margin is trimmed but VISIBLE
    scored.append({"kind": "table", "name": "E", "table_name": "E",
                   "scores": {"name": 0.41, "description": 0.0}})
    anchors2, candidates2 = dictionary_graph.accept(
        scored, floor=0.25, match=0.4, margin=0.02)
    assert [a["name"] for a in anchors2] == ["B"]
    assert any(c["name"] == "E" and c.get("margin_trimmed")
               for c in candidates2)


@pytest.fixture(scope="module")
def real_graph():
    sheets = dictionary_graph.load_sheets(DATA_DIR)
    return dictionary_graph.build_graph(sheets)


def test_real_graph_structure_pins_the_corpus(real_graph):
    census = real_graph["census"]
    # Re-based 2026-10-02: the CR_STAT_EXECUTION supplemental entry.
    assert census["tables"] == 39 and census["columns"] == 1621
    assert census["joins_by_fk"] == 210      # the in-scope join rows
    assert census["joins_by_rule"] == 182    # DATETIME columns, L08
    # (+1 2026-10-02: EXEC_START_TIME's date_dimension rule edge)
    # shape 9 closes: ONE component with the rule edges built —
    # CR_STAT_EXECUTION joins the component through its rule edge
    assert len(census["components"]) == 1
    assert len(census["components"][0]) == 39


def test_first_lock_round_rulings_are_mapped(extraction):
    # Sunny's 2026-09-28 rulings, pinned mechanically:
    entries, _ = extraction
    all_nodes = [n for e in entries for n in _walk_nodes(e)]
    # USE [CookClarity] -> statement kind USE with the database name.
    uses = [n for n in all_nodes if n.get("statement_kind") == "USE"]
    assert uses and all(n["database"] == "CookClarity" for n in uses)
    # STRING_SPLIT in FROM -> a function_ref, never a table_ref.
    fn_refs = {n.get("function_ref") for n in all_nodes if "function_ref" in n}
    assert "STRING_SPLIT" in fn_refs
    # A qualified call keeps its whole name.
    fn_names = {n.get("name") for n in all_nodes
                if n.get("kind") == "function"}
    assert any(str(n).startswith("Clarity.EPIC_UTIL.") for n in fn_names), (
        f"qualified names found: {sorted(x for x in fn_names if x and '.' in x)}")
    # WITHIN GROUP ordering rides on its function node.
    assert any(n.get("within_group") for n in all_nodes
               if n.get("kind") == "function")
    # The accepted remainder stays a counted remainder.
    rem_types = {i["type"] for e in entries for i in e["remainder"]}
    assert "SetTransactionIsolationLevelStatement" in rem_types
