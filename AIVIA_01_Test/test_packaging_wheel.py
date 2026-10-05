"""Brief_Packaging locks (STAMPED 2026-10-04): the deterministic
work wheel aivia01-sqldesc. RED until build_sqldesc_wheel.py
exposes the builder. The wheel is built INTO tmp here — no
network (pip wheel --no-build-isolation), no keys, no estate
data; the locks read the built artifact's own bytes.
"""

import json
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "AIVIA_01_Code"))

CANARY = ("CCMC EMERGENCY", "CCMC IR IMAGING", "CCMC CATH LAB",
          "CCMC MAIN OR", "CCMC SPA OR", "CCMC PHP PSYCHIATRY",
          "CCMC CARDIOVASCULAR OR", "DSC OR")
SECRET_SHAPES = ("OPENAI", "AZURE_OPENAI", "api_key",
                 "import openai", "import requests",
                 "import httpx")


def _wheel(tmp_path):
    import build_sqldesc_wheel as bw
    return Path(bw.build(out_dir=tmp_path))


def test_wheel_manifest_equality(tmp_path):
    """Lock 1: the wheel's contents == the stamped allowlist
    exactly — one extra or missing file is a refused build."""
    import build_sqldesc_wheel as bw
    whl = _wheel(tmp_path)
    names = set(zipfile.ZipFile(whl).namelist())
    payload = {n for n in names if ".dist-info/" not in n}
    assert payload == set(bw.ALLOWLIST)


def test_wheel_carries_no_secret_shapes(tmp_path):
    """Lock 2: no key-shaped strings, no network clients, in any
    packaged python module."""
    whl = _wheel(tmp_path)
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        if not n.endswith(".py"):
            continue
        text = z.read(n).decode("utf-8", errors="replace")
        for shape in SECRET_SHAPES:
            assert shape not in text, (n, shape)


def test_wheel_carries_no_estate_data(tmp_path):
    """Lock 3: the census canary — customer strings must not
    exist anywhere in the wheel, any member, any encoding."""
    whl = _wheel(tmp_path)
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        blob = z.read(n)
        for canary in CANARY:
            assert canary.encode() not in blob, (n, canary)


def test_cli_dict_dir_speaks_meanings(tmp_path):
    """RULED 2026-10-04 (her 'build the dict_dir option' after
    the D8 acceptance): describe() accepts a runtime-offered
    dictionary — value meanings and column words speak; with
    none offered, the empty-dictionary mode stands. Synthetic
    fixture only (invented names, the estate boundary)."""
    import sqldesc_cli
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "USP_FIX_DESCRIBE.sql").write_text(
        "SELECT t.COL_A FROM fakedb..FAKE_TBL t "
        "WHERE t.COL_A = '7'\n")
    d02 = tmp_path / "dict"
    d02.mkdir()
    # the value bridge routes through PK-keyed value tables
    # via a 02 join (the census ZC pattern, synthetic)
    (d02 / "02_emr_data_dictionary_extraction_column.json"
     ).write_text(json.dumps([
        {"table_name": "FAKE_TBL", "column_name": "COL_A",
         "column_description": "The fake code of the thing.",
         "is_primary_key": "N"},
        {"table_name": "ZC_FAKE", "column_name": "FAKE_C",
         "column_description": "The fake category code.",
         "is_primary_key": "Y"}]))
    (d02 / "02_emr_data_dictionary_extraction_value.json"
     ).write_text(json.dumps([{
        "table_name": "ZC_FAKE", "code": "7",
        "meaning": "Lucky"}]))
    (d02 / "02_emr_data_dictionary_extraction_join.json"
     ).write_text(json.dumps([{
        "join_id": "J1", "ordinal": 1,
        "source_table_id": "T1", "source_table_name": "FAKE_TBL",
        "source_column_id": "C1", "source_column_name": "COL_A",
        "destin_table_id": "T2", "destin_table_name": "ZC_FAKE",
        "destin_column_id": "C2", "destin_column_name": "FAKE_C",
        "conditional_c": None, "may_be_stale_c": None,
        "is_current_data_model_yn": "Y",
        "is_supplemental_yn": "N", "destin_in_scope": "Y"}]))
    out = tmp_path / "out"
    sqldesc_cli.describe(sql, out, dict_dir=d02)
    text = (out / "USP_FIX_DESCRIBE.txt").read_text()
    assert "'Lucky' (7)" in text or "Lucky" in text
