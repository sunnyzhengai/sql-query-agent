"""Brief_Pilot_Build_1 slices A + B (Brief_Pilot_Findings_R1 F6/F7/F8,
rulings (4) "i agree, new ids" and (5) "i agree with option c"):
intake never hands the operator a raw traceback. Every intake text
read decodes utf-8-sig (a Windows editor's BOM is not an error);
a file that exists but does not parse refuses by name (INTAKE-14);
CSV headers are checked against the contract per file (INTAKE-15);
the estate manifest is a named refusal when missing (INTAKE-16) or
undated (INTAKE-17), and extract_scripts writes its template with
the ONE human field — as_of — left empty (the template's tripwire
per the placeholder law).

Proves: contract:aisql-design-to-code
"""
import codecs
import json

import pytest

from aisql import fabric_run
from aisql.flows import inbound
from aisql.graph import kg1_intake
from aisql.graph.kg1_intake import Refusal
from aisql.graph.kg2_mapper.scriptdom_loader import ScriptDomUnavailable
from aisql.graph.store import Store

BOM = codecs.BOM_UTF8.decode("utf-8")
MANIFEST = {"source": "simemr", "operator": "t", "as_of": "2026-09-20",
            "source_pack_version": "simemr-pack-0.1"}
CSVS = {
    "tables.csv": 'schema,table,description\ndbo,PATIENT,"One row."\n',
    "columns.csv": ("schema,table,column,description\n"
                    'dbo,PATIENT,PATIENT_ID,"The id."\n'),
    "pk.csv": "schema,table,column,ordinal\ndbo,PATIENT,PATIENT_ID,1\n",
    "joins.csv": ("fk_num,ordinal,src_schema,src_table,src_column,"
                  "dest_schema,dest_table,dest_column\n"),
    "values.csv": "table,code,meaning\nZC_X,1,Yes\n",
}


def _snapshot(tmp_path, prefix=""):
    (tmp_path / "manifest.json").write_text(prefix + json.dumps(MANIFEST))
    for name, text in CSVS.items():
        (tmp_path / name).write_text(prefix + text)
    return tmp_path


# ---- slice A: the extract reader ----

def test_bom_prefixed_extract_loads_clean(tmp_path):
    """F6: the operator's Windows-saved files carry a BOM on the
    manifest AND on every CSV's first header — both must read as if
    the mark were never there."""
    snap = kg1_intake.load_snapshot(_snapshot(tmp_path, prefix=BOM))
    assert snap.manifest["source"] == "simemr"
    assert snap.tables[0]["schema"] == "dbo"
    assert snap.values[0]["table"] == "ZC_X"


def test_malformed_manifest_refuses_by_name(tmp_path):
    _snapshot(tmp_path)
    (tmp_path / "manifest.json").write_text("{not json")
    with pytest.raises(Refusal) as err:
        kg1_intake.load_snapshot(tmp_path)
    assert err.value.rule == "INTAKE-14"
    assert "manifest.json" in str(err.value)


def test_headerless_csv_refuses_expected_vs_found(tmp_path):
    """F7: the SQL client's grid saved without headers — the first
    DATA row is not the contract's header row; the refusal names the
    file and both header lists."""
    _snapshot(tmp_path)
    (tmp_path / "tables.csv").write_text('dbo,PATIENT,"One row."\n')
    with pytest.raises(Refusal) as err:
        kg1_intake.load_snapshot(tmp_path)
    assert err.value.rule == "INTAKE-15"
    assert "tables.csv" in str(err.value)
    assert "schema" in str(err.value)


def test_wrong_headers_refuse_per_file(tmp_path):
    _snapshot(tmp_path)
    (tmp_path / "pk.csv").write_text(
        "schema,table,col,position\ndbo,PATIENT,PATIENT_ID,1\n")
    with pytest.raises(Refusal) as err:
        kg1_intake.load_snapshot(tmp_path)
    assert err.value.rule == "INTAKE-15"
    assert "pk.csv" in str(err.value)


def test_extra_columns_are_tolerated(tmp_path):
    """The pack's extras-tolerated law + rider (c): data_type is
    opportunistic — extra headers never refuse."""
    _snapshot(tmp_path)
    (tmp_path / "tables.csv").write_text(
        'schema,table,description,extra\ndbo,PATIENT,"One row.",x\n')
    snap = kg1_intake.load_snapshot(tmp_path)
    assert snap.tables[0]["extra"] == "x"


# ---- slice B: the estate manifest ----

def test_missing_estate_manifest_is_a_named_refusal(tmp_path):
    """F8: the operator hit a raw FileNotFoundError mid-boot."""
    estate = tmp_path / "estate_snapshot"
    estate.mkdir()
    (estate / "a.sql").write_text("SELECT 1;")
    with pytest.raises(Refusal) as err:
        inbound.receive_estate(Store(), {}, estate)
    assert err.value.rule == "INTAKE-16"
    assert "manifest.json" in str(err.value)


def test_empty_as_of_refuses_with_the_ruled_sentence(tmp_path):
    """Ruling (5): the template ships with as_of EMPTY and intake is
    its tripwire — the refusal speaks the ruled words. The manifest
    here is BOM'd too: the refusal must be INTAKE-17, not a parse
    error (the utf-8-sig read happened first)."""
    estate = tmp_path / "estate_snapshot"
    estate.mkdir()
    (estate / "manifest.json").write_text(BOM + json.dumps(
        {"location": "estate://t/", "as_of": "", "default_schema": "dbo"}))
    with pytest.raises(Refusal) as err:
        inbound.receive_estate(Store(), {}, estate)
    assert err.value.rule == "INTAKE-17"
    assert "fill in the date this estate SQL was captured" in str(err.value)


def _autogen_estate(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    snap = tmp_path / "estate_snapshot"
    snap.mkdir()
    (snap / "a.sql").write_text(
        "SELECT e.PAT_ID FROM dbo.PAT_ENC e;")
    return tmp_path


def test_extract_scripts_writes_the_manifest_template(tmp_path):
    """Ruling (5), option c: location from the folder, default_schema
    from the source pack (a vendor fact — pack.json), as_of EMPTY."""
    _autogen_estate(tmp_path)
    try:
        fabric_run.extract_scripts(str(tmp_path))
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    manifest = json.loads(
        (tmp_path / "estate_snapshot" / "manifest.json").read_text())
    assert manifest["as_of"] == ""
    assert tmp_path.name in manifest["location"]
    assert manifest["default_schema"] == "dbo"


def test_the_template_never_clobbers_a_filled_manifest(tmp_path):
    _autogen_estate(tmp_path)
    path = tmp_path / "estate_snapshot" / "manifest.json"
    human = json.dumps({"location": "estate://mine/",
                        "as_of": "2026-09-19", "default_schema": "dbo"})
    path.write_text(human)
    try:
        fabric_run.extract_scripts(str(tmp_path))
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    assert path.read_text() == human


def test_bom_prefixed_sql_still_derives_the_list(tmp_path):
    (tmp_path / "registration.json").write_text("{}")
    snap = tmp_path / "estate_snapshot"
    snap.mkdir()
    (snap / "a.sql").write_text(
        BOM + "SELECT e.PAT_ID FROM dbo.PAT_ENC e;")
    try:
        tables = fabric_run.extract_scripts(str(tmp_path))
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    assert "PAT_ENC" in tables
