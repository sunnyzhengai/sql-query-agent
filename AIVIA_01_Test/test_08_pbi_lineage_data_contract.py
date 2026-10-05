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
        (out / "08_lineage_ledger.json").read_text())
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
    first = (out / "08_pbi_reports.json").read_bytes()
    tmdl, corpus = out.parent / "tmdl", out.parent / "sql"
    pl.build08(tmdl, corpus, out)
    assert (out / "08_pbi_reports.json").read_bytes() == first
