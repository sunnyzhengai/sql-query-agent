"""Phase 08 contract tests (08_pbi_lineage_data_contract.md,
STAMPED 2026-10-04).

Written test-first: RED until pbi_lineage.py exposes build08.
DETERMINISTIC end to end — fixtures are SYNTHETIC TMDL with
invented names only (the estate boundary: no customer text in a
fixture, ever). No LLM, no network, no cost.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
sys.path.insert(0, str(CODE_DIR))


# ------------------------- the synthetic fixture (invented names)

def _table(src_cols, partition_lines):
    body = ["table FixTable", ""]
    for c in src_cols:
        body += [f"\tcolumn {c}", "\t\tdataType: string",
                 f"\t\tsourceColumn: {c}", ""]
    body += ["\tpartition p1 = m", "\t\tmode: import",
             "\t\tsource ="]
    body += [f"\t\t\t{ln}" for ln in partition_lines]
    return "\n".join(body) + "\n"


def _model(root, name, tables):
    d = root / f"{name}.SemanticModel" / "definition" / "tables"
    d.mkdir(parents=True)
    for tname, text in tables.items():
        (d / f"{tname}.tmdl").write_text(text)


def _fixture(tmp_path):
    """One model with all three binding kinds + plumbing + an
    unresolved exec; a corpus with one untouched file."""
    tmdl = tmp_path / "tmdl"
    tmdl.mkdir()
    _model(tmdl, "Fix Dashboard", {
        "ProcFed": _table(
            ["Fix Col A", "Fix Col B"],
            ['let q = Value.NativeQuery(db,',
             '"EXEC rpt.USP_FIX_ONE") in q']),
        "LakeFed": "\n".join([
            "table LakeFed", "",
            "\tcolumn Fix Col C", "\t\tsourceColumn: Fix Col C",
            "", "\tpartition p1 = entity",
            "\t\tmode: directLake",
            "\t\tsource", "\t\t\tentityName: V_FIX_ENTITY",
            "\t\t\tschemaName: rpt", ""]),
        "ViewFed": _table(
            ["Fix Col D"],
            ['let s = Sql.Database("srv","db"),',
             't = s{[Schema="rpt",Item="V_FIX_VIEW"]}[Data]',
             'in t']),
        "GhostFed": _table(
            ["Fix Col E"],
            ['let q = Value.NativeQuery(db,',
             '"EXEC rpt.USP_FIX_GHOST") in q']),
        "LocalDateTable_abc123": _table(
            ["Date"], ["Calendar()"]),
    })
    corpus = tmp_path / "sql"
    corpus.mkdir()
    for f in ("USP_FIX_ONE.sql", "V_FIX_ENTITY.sql",
              "V_FIX_VIEW.sql", "USP_FIX_LONELY.sql"):
        (corpus / f).write_text("SELECT 1\n")
    out = tmp_path / "08"
    out.mkdir()
    return tmdl, corpus, out


def _build(tmp_path):
    import pbi_lineage as pl
    tmdl, corpus, out = _fixture(tmp_path)
    reports = pl.build08(tmdl, corpus, out)
    ledger = json.loads(
        (out / "08_pbi_lineage_ledger_output.json").read_text())
    return reports, ledger, out


# --------------------------------------- the locks (L1-L7, D1-D4)

def test_08_l1_exec_binding_resolves(tmp_path):
    reports, _, _ = _build(tmp_path)
    r = next(x for x in reports if x["name"] == "Fix Dashboard")
    assert "USP_FIX_ONE.sql" in r["executes"]
    assert r["bound_fields"]["USP_FIX_ONE.sql"] == \
        ["Fix Col A", "Fix Col B"]


def test_08_l2_entity_binding_resolves(tmp_path):
    reports, _, _ = _build(tmp_path)
    r = reports[0]
    assert "V_FIX_ENTITY.sql" in r["executes"]
    kinds = {b["binding_kind"] for b in r["bindings"]}
    assert "entity" in kinds


def test_08_l3_source_binding_resolves(tmp_path):
    reports, _, _ = _build(tmp_path)
    r = reports[0]
    assert "V_FIX_VIEW.sql" in r["executes"]
    assert any(b["binding_kind"] == "source" and
               b["resolved"] == "V_FIX_VIEW.sql"
               for b in r["bindings"])


def test_08_l4_unresolved_is_counted_never_dropped(tmp_path):
    reports, ledger, _ = _build(tmp_path)
    u = ledger["unresolved"]
    assert any("USP_FIX_GHOST" in row["raw_target"] for row in u)
    r = reports[0]
    assert not any("GHOST" in e.upper() for e in r["executes"])


# ---------------- 0.8.0 THE VIEW TIE (D15, ruled 2026-10-08
# evening — the first tenant's views were ALL reportless; a
# report consumes a view by SELECT or Item, never EXEC). RED
# until the two binding kinds land.

def test_08_v1_select_from_binds_a_view(tmp_path):
    tmdl = tmp_path / "tmdl"
    tmdl.mkdir()
    _model(tmdl, "Fix Views", {
        "ViewFed": _table(
            ["Fix Col V"],
            ['let q = Value.NativeQuery(db,',
             '"SELECT * FROM COOK_X.V_FIX_VIEW") in q'])})
    corpus = tmp_path / "sql"
    corpus.mkdir()
    (corpus / "V_FIX_VIEW.sql").write_text(
        "CREATE VIEW COOK_X.V_FIX_VIEW AS SELECT 1 AS A;\n")
    out = tmp_path / "out"
    out.mkdir()
    import pbi_lineage as pl
    reports = pl.build08(tmdl, corpus, out)
    r = next(x for x in reports if x["name"] == "Fix Views")
    assert "V_FIX_VIEW.sql" in r["executes"]


def test_08_v2_item_import_binds_a_view(tmp_path):
    tmdl = tmp_path / "tmdl"
    tmdl.mkdir()
    _model(tmdl, "Fix Items", {
        "ItemFed": _table(
            ["Fix Col I"],
            ['let s = Sql.Database("srv", "db"),',
             'v = s{[Schema="COOK_X",Item="V_FIX_ITEM"]}[Data]',
             'in v'])})
    corpus = tmp_path / "sql"
    corpus.mkdir()
    (corpus / "V_FIX_ITEM.sql").write_text(
        "CREATE VIEW COOK_X.V_FIX_ITEM AS SELECT 1 AS A;\n")
    out = tmp_path / "out"
    out.mkdir()
    import pbi_lineage as pl
    reports = pl.build08(tmdl, corpus, out)
    r = next(x for x in reports if x["name"] == "Fix Items")
    assert "V_FIX_ITEM.sql" in r["executes"]


def test_08_v3_select_from_no_corpus_match_counted(tmp_path):
    """A FROM over a raw warehouse table is NOT a corpus file —
    counted, named, never guessed into executes."""
    tmdl = tmp_path / "tmdl"
    tmdl.mkdir()
    _model(tmdl, "Fix Raw", {
        "RawFed": _table(
            ["Fix Col R"],
            ['let q = Value.NativeQuery(db,',
             '"SELECT * FROM dbo.FIX_RAW_TABLE") in q'])})
    corpus = tmp_path / "sql"
    corpus.mkdir()
    (corpus / "V_UNRELATED.sql").write_text(
        "CREATE VIEW dbo.V_UNRELATED AS SELECT 1 AS A;\n")
    out = tmp_path / "out"
    out.mkdir()
    import pbi_lineage as pl
    reports = pl.build08(tmdl, corpus, out)
    assert all("FIX_RAW_TABLE.sql" not in r.get("executes", [])
               for r in reports)
    ledger = json.loads(
        (out / "08_pbi_lineage_ledger_output.json").read_text())
    assert any("FIX_RAW_TABLE" in json.dumps(e)
               for e in ledger.get("unresolved", [])), ledger


def test_08_l5_plumbing_skipped_and_counted(tmp_path):
    reports, ledger, _ = _build(tmp_path)
    assert ledger["counts"]["plumbing_skipped"] == 1
    r = reports[0]
    assert not any("LocalDateTable" in b["table"]
                   for b in r["bindings"])


def test_08_l6_no_shells_untouched_file_is_unconsumed(tmp_path):
    reports, ledger, _ = _build(tmp_path)
    assert "USP_FIX_LONELY.sql" in ledger["unconsumed_sql"]
    assert len(reports) == 1  # no minted shell rows, ever


def test_08_l7_conservation_and_byte_determinism(tmp_path):
    import pbi_lineage as pl
    _, ledger, out = _build(tmp_path)
    c = ledger["counts"]
    assert c["bindings"] == c["resolved"] + c["unresolved"]
    first = (out / "08_pbi_lineage_output.json").read_bytes()
    tmdl, corpus = out.parent / "tmdl", out.parent / "sql"
    pl.build08(tmdl, corpus, out)
    assert (out / "08_pbi_lineage_output.json").read_bytes() == first


# -------------------------------------- several workspaces (D11 path 2)
# 10_work_wheel.md D11, ruled 2026-10-07 ("path 1 today, path 2 on the
# docket"): tmdl/ may hold ONE SUBFOLDER PER SOURCE WORKSPACE. RED until
# read_models walks recursively; model identity is the relative path
# ("WS Fix One/Fix Twin"), so a bare name in two workspaces never
# silently last-wins. Top-level models keep their bare name — every
# lock above this line must stay green unchanged (back-compat law).

def test_08_l8_workspace_subfolder_discovered(tmp_path):
    import pbi_lineage as pl
    tmdl = tmp_path / "tmdl"
    (tmdl / "WS Fix One").mkdir(parents=True)
    _model(tmdl / "WS Fix One", "Fix Nested", {
        "ProcFed": _table(
            ["Fix Col N"],
            ['let q = Value.NativeQuery(db,',
             '"EXEC rpt.USP_FIX_ONE") in q'])})
    corpus = tmp_path / "sql"
    corpus.mkdir()
    (corpus / "USP_FIX_ONE.sql").write_text("SELECT 1\n")
    out = tmp_path / "08"
    out.mkdir()
    reports = pl.build08(tmdl, corpus, out)
    names = [r["name"] for r in reports]
    assert "WS Fix One/Fix Nested" in names, names
    r = next(x for x in reports
             if x["name"] == "WS Fix One/Fix Nested")
    assert "USP_FIX_ONE.sql" in r["executes"]


def test_08_l9_same_bare_name_in_two_workspaces_both_kept(tmp_path):
    import pbi_lineage as pl
    tmdl = tmp_path / "tmdl"
    for ws, proc in (("WS Fix One", "USP_FIX_ONE"),
                     ("WS Fix Two", "USP_FIX_TWO")):
        (tmdl / ws).mkdir(parents=True)
        _model(tmdl / ws, "Fix Twin", {
            "ProcFed": _table(
                ["Fix Col T"],
                ['let q = Value.NativeQuery(db,',
                 f'"EXEC rpt.{proc}") in q'])})
    corpus = tmp_path / "sql"
    corpus.mkdir()
    for f in ("USP_FIX_ONE.sql", "USP_FIX_TWO.sql"):
        (corpus / f).write_text("SELECT 1\n")
    out = tmp_path / "08"
    out.mkdir()
    reports = pl.build08(tmdl, corpus, out)
    twins = sorted(r["name"] for r in reports
                   if r["name"].endswith("Fix Twin"))
    assert twins == ["WS Fix One/Fix Twin", "WS Fix Two/Fix Twin"]
    by_name = {r["name"]: r for r in reports}
    assert by_name["WS Fix One/Fix Twin"]["executes"] == \
        ["USP_FIX_ONE.sql"]
    assert by_name["WS Fix Two/Fix Twin"]["executes"] == \
        ["USP_FIX_TWO.sql"]


# ---------------- 0.11.1 THE SCHEMA-QUALIFIED TIE (ruled
# 2026-10-10 evening — the census find: the work TMDL calls
# procs by DATABASE-qualified three-part names while the
# intake's collision-safe corpus names files Schema_Object.sql;
# every binding landed unresolved and zero reports tied. Her
# ledger lines verbatim are the locks. RED before code.

def test_08_three_part_target_finds_schema_object_file():
    import pbi_lineage as pl
    corpus = ["COOK_RPT_usp_PTA_CensusDashboard_PBI.sql",
              "Reporting_USP_Hospitalist_Daily_Census_Report_92a_PBI.sql"]
    assert pl.resolve(
        "CookClarity.[COOK_RPT].[usp_PTA_CensusDashboard_PBI]",
        corpus) == "COOK_RPT_usp_PTA_CensusDashboard_PBI.sql"
    assert pl.resolve(
        "[CookClarity].[Reporting]."
        "[USP_Hospitalist_Daily_Census_Report_92a_PBI]",
        corpus) == ("Reporting_USP_Hospitalist_Daily_Census_"
                    "Report_92a_PBI.sql")


def test_08_case_folds_across_every_part():
    import pbi_lineage as pl
    corpus = ["COOK_RPT_USP_SPS_ANTIMICROBIAL_DAYS_ON_THERAPY.sql"]
    assert pl.resolve(
        "COOKCLARITY.[COOK_RPT].[USP_SPS_ANTIMICROBIAL_DAYS_"
        "ON_THERAPY]", corpus) == corpus[0]


def test_08_bare_object_naming_still_resolves():
    """The CCHP regression: a corpus named object.sql (no
    schema prefix) keeps tying exactly as before."""
    import pbi_lineage as pl
    corpus = ["USP_CCHPCHICPilotHIT_PBI.sql"]
    assert pl.resolve(
        "EXECDB.[rpt].[USP_CCHPCHICPilotHIT_PBI]",
        corpus) == corpus[0]
    assert pl.resolve("rpt.USP_CCHPCHICPilotHIT_PBI",
                      corpus) == corpus[0]


def test_08_specific_name_beats_the_legacy():
    import pbi_lineage as pl
    corpus = ["Reporting_X.sql", "X.sql"]
    assert pl.resolve("db.Reporting.X", corpus) \
        == "Reporting_X.sql"


def test_08_a_miss_is_still_none():
    import pbi_lineage as pl
    assert pl.resolve("db.schema.NOWHERE",
                      ["Reporting_X.sql"]) is None
