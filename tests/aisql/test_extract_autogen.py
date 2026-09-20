"""Brief_Extract_Autogen (Sunny, 2026-09-19: "this is too manual.
can you automate: read the sql files in the estate_snapshot/
folder, extract the clarity tables and columns, and populate these
queries? i don't want to keep manually writing and maintaining
these lists and files"): THE DERIVED-LIST LAW. extract_scripts
parses the estate's SQL through the ONE parse door (map_tree) and
writes the pack scripts with the batch list filled — no
hand-maintained list, ever. EA2: an unparseable file is a counted,
named line; generation continues.

Proves: contract:aisql-design-to-code
"""
import pytest

from aisql import fabric_run
from aisql.graph.kg2_mapper.scriptdom_loader import ScriptDomUnavailable


def _estate(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    snap = tmp_path / "estate_snapshot"
    snap.mkdir()
    (snap / "a.sql").write_text(
        "SELECT e.PAT_ID FROM dbo.PAT_ENC e "
        "JOIN ZC_ACUITY z ON e.ACUITY_C = z.ACUITY_C;")
    (snap / "b.sql").write_text(
        "SELECT * FROM reporting.F_ED_ENCOUNTERS;")
    (snap / "broken.sql").write_text("SELEC FORM ((;")
    return tmp_path


def _run(tmp_path, capsys):
    try:
        tables = fabric_run.extract_scripts(str(tmp_path))
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    return tables, capsys.readouterr().out


def test_the_list_derives_from_the_sql(tmp_path, capsys):
    tables, out = _run(_estate(tmp_path), capsys)
    assert {"PAT_ENC", "ZC_ACUITY", "F_ED_ENCOUNTERS"} <= set(tables)
    gen = tmp_path / "extract_scripts"
    one = (gen / "01_tables.sql").read_text()
    assert "'PAT_ENC'" in one and "'ZC_ACUITY'" in one
    for name in ("01_tables.sql", "02_columns.sql", "03_pk.sql",
                 "04_joins.sql"):
        text = (gen / name).read_text()
        assert "PASTE_YOUR_BATCH_TABLES_HERE" not in text, name
    assert (gen / "05_values.sql").is_file()
    assert (gen / "06_manifest.sql").is_file()


def test_04_carries_the_list_on_both_sides(tmp_path, capsys):
    _run(_estate(tmp_path), capsys)
    four = (tmp_path / "extract_scripts" / "04_joins.sql").read_text()
    assert four.count("'PAT_ENC'") == 2


def test_unparseable_files_are_counted_not_fatal(tmp_path, capsys):
    _, out = _run(_estate(tmp_path), capsys)
    assert "broken.sql" in out
    assert "unparseable" in out


def test_refuses_an_estate_without_sql(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    (tmp_path / "estate_snapshot").mkdir()
    with pytest.raises(SystemExit) as err:
        fabric_run.extract_scripts(str(tmp_path))
    assert err.value.code == 2
