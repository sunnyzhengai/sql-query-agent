"""Brief_Packaging locks (STAMPED 2026-10-04): the deterministic
work wheel aivia01-sqldesc. RED until build_sqldesc_wheel.py
exposes the builder. The wheel is built INTO tmp here — no
network (pip wheel --no-build-isolation), no keys, no estate
data; the locks read the built artifact's own bytes.
"""

import json
import os
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
# THE LLM SEAT EXEMPTION (RULED 2026-10-05, Brief_Packaging
# amendment — "approve the wheel change"): the two LLM phases
# may import the openai client; the CLI may read the key's
# PRESENCE (env name only, for the honest degrade). The KEY
# still never rides (the literal-key lock covers every member).
LLM_MODULES = ("business_descriptions.py", "business_terms.py",
               "sqldesc_cli.py")


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
    for m in ("business_descriptions.py", "business_terms.py",
              "ai_delivery.py"):
        assert m in payload, m   # the 0.5.0 ruling, test-locked


def test_wheel_carries_no_secret_shapes(tmp_path):
    """Lock 2 (amended 2026-10-05): outside the exempt LLM
    modules, no key-shaped strings and no network clients; in
    EVERY member, no literal key (sk-...)."""
    import re
    whl = _wheel(tmp_path)
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        blob = z.read(n)
        assert not re.search(rb"sk-[A-Za-z0-9_-]{16,}", blob), n
        if not n.endswith(".py") or n in LLM_MODULES:
            continue
        text = blob.decode("utf-8", errors="replace")
        for shape in SECRET_SHAPES:
            assert shape not in text, (n, shape)


def test_wheel_contains_no_aivia_string(tmp_path):
    """RULED 2026-10-05 (her word: 'replace aivia with ai
    everywhere in the wheel'): no member of the artifact —
    code, assets, metadata — carries the brand string, any
    case. The work-transition tripwire law."""
    whl = _wheel(tmp_path)
    assert "aivia" not in whl.name.lower()
    z = zipfile.ZipFile(whl)
    for n in z.namelist():
        assert "aivia" not in n.lower(), n
        assert b"aivia" not in z.read(n).lower(), n


def test_wheel_version_and_llm_seat_dependency(tmp_path):
    """The 0.5.x ruling: openai a declared dependency (installed
    by the environment, key at runtime); the name pins to the
    builder's VERSION so a changed artifact always bumps."""
    import build_sqldesc_wheel as bw
    whl = _wheel(tmp_path)
    assert f"ai01_sqldesc-{bw.VERSION}-" in whl.name
    z = zipfile.ZipFile(whl)
    meta = next(n for n in z.namelist()
                if n.endswith("METADATA"))
    text = z.read(meta).decode()
    assert "Requires-Dist: openai" in text


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


def test_cli_business_dir_serves_the_07_card(tmp_path):
    """RULED 2026-10-04 (her 'build it' on the 07-card rider):
    report_descriptions accepts a RUNTIME-OFFERED 07 folder —
    each report row gains the business card for its linked
    files (blessed lines ride, since the stored sheet carries
    them). The wheel ships no 07 content, ever."""
    import sqldesc_cli
    tmdl = tmp_path / "tmdl"
    tdir = tmdl / "Fix.SemanticModel" / "definition" / "tables"
    tdir.mkdir(parents=True)
    (tdir / "T.tmdl").write_text(
        "table T\n\tcolumn A\n\t\tsourceColumn: A\n"
        "\tpartition p = m\n\t\tmode: import\n\t\tsource =\n"
        '\t\t\tValue.NativeQuery(db,"EXEC dbo.USP_FIX_BIZ")\n')
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "USP_FIX_BIZ.sql").write_text("SELECT 1 AS A\n")
    biz = tmp_path / "07"
    biz.mkdir()
    (biz / "07_business_sheet.json").write_text(json.dumps([
        {"node_id": "file::USP_FIX_BIZ", "grain": "file",
         "audience_text": "One row is: a fixture row. "
                          "Time window: HER BLESSED SENTENCE.",
         "status": "blessed"}]))
    out = tmp_path / "out"
    rows = sqldesc_cli.report_descriptions(
        tmdl, sql, out, business_dir=biz)
    r = rows[0]
    assert r["business"]["USP_FIX_BIZ.sql"].startswith(
        "One row is: a fixture row.")
    assert "HER BLESSED SENTENCE" in str(r["business"])


def _official_fixture(tmp_path):
    tmdl = tmp_path / "tmdl"
    tdir = tmdl / "Fix.SemanticModel" / "definition" / "tables"
    tdir.mkdir(parents=True)
    (tdir / "T.tmdl").write_text(
        "table T\n\tcolumn A\n\t\tsourceColumn: A\n"
        "\tpartition p = m\n\t\tmode: import\n\t\tsource =\n"
        '\t\t\tValue.NativeQuery(db,"EXEC dbo.USP_FIX_OFF")\n')
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "USP_FIX_OFF.sql").write_text("SELECT 1 AS A\n")
    return tmdl, sql


def test_cli_official_txt_speaks_its_voice(tmp_path):
    """RULED 2026-10-04 (her official-output ask): every run
    writes 08_report_descriptions.txt — report, sql file, and
    the description, with the VOICE labeled: business when a
    07 sheet is offered, technical otherwise — never a silent
    downgrade (the work-transition law)."""
    import sqldesc_cli
    tmdl, sql = _official_fixture(tmp_path)

    out1 = tmp_path / "out1"
    sqldesc_cli.report_descriptions(tmdl, sql, out1)
    t1 = (out1 / "08_report_descriptions.txt").read_text()
    assert "REPORT: Fix" in t1
    assert "feeds from: USP_FIX_OFF.sql" in t1
    assert "voice: technical" in t1

    biz = tmp_path / "07"
    biz.mkdir()
    (biz / "07_business_sheet.json").write_text(json.dumps([
        {"node_id": "file::USP_FIX_OFF", "grain": "file",
         "audience_text": "One row is: an official fixture "
                          "row. Time window: HER SENTENCE.",
         "status": "blessed"}]))
    out2 = tmp_path / "out2"
    sqldesc_cli.report_descriptions(tmdl, sql, out2,
                                    business_dir=biz)
    t2 = (out2 / "08_report_descriptions.txt").read_text()
    assert "voice: business" in t2
    assert "HER SENTENCE" in t2


def test_names_asset_absence_is_honest_and_offerable(tmp_path,
                                                     monkeypatch):
    """The Fabric rehearsal crash (2026-10-05): the 03 naming
    asset's repo-relative default dies inside a wheel. The name
    ladder's own law: the asset is ONE RUNG, never a requirement
    — absence returns blessed-names-only, no raise; and the
    runner may OFFER the real location via AI_NAMES_DIR (the
    runtime-offered precedent)."""
    import json as _json

    import business_descriptions as bd
    empty = tmp_path / "nowhere"
    names = bd.load_names(empty, {"names": []})
    assert names == {}                   # absent -> honest empty
    offered = tmp_path / "03"
    offered.mkdir()
    (offered / "03_chat_abstract_names.json").write_text(
        _json.dumps([{"object_kind": "table",
                      "object_name": "FIX_TBL",
                      "synonyms": ["fix things"]}]))
    monkeypatch.setenv("AI_NAMES_DIR", str(offered))
    assert str(bd._dir03()) == str(offered)   # the offer wins
    assert bd._dir03(tmp_path / "x") == tmp_path / "x"
    # the corpus home rides the same law (the second rehearsal
    # crash, same night): AI_SQL_DIR offers it at runtime —
    # the repo-relative default was the LAST of the four
    # parents[1] paths (sweep 2026-10-05; loader + kind library
    # already packaged-first)
    monkeypatch.setenv("AI_SQL_DIR", str(offered))
    assert str(bd._dir01()) == str(offered)
    assert bd._dir01(tmp_path / "y") == tmp_path / "y"


def test_dead_dll_pointer_is_cleared_never_trusted(monkeypatch):
    """The vanishing-DLL find (2026-10-06): an env pointer at a
    path that no longer exists must be CLEARED, not trusted —
    the loader then takes a live route instead of dying on a
    ghost."""
    import sqldesc_cli
    monkeypatch.setenv("SCRIPTDOM_DLL", "/nonexistent/ghost.dll")
    sqldesc_cli._point_at_packaged_dll()
    assert os.environ.get("SCRIPTDOM_DLL") != \
        "/nonexistent/ghost.dll"


def test_cli_preflight_names_every_missing_prereq(tmp_path,
                                                  monkeypatch):
    """Her ask at the rehearsal (2026-10-06, after the httpx
    find): one check for ALL prereqs before any paid call.
    Report-all (never stop at the first), each failure NAMES
    its fix; zero network, zero cost."""
    import sqldesc_cli
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    bad_sql = tmp_path / "sql"
    bad_sql.mkdir()
    (bad_sql / "BARE_NAME_NO_EXT").write_text("SELECT 1")
    empty_tmdl = tmp_path / "tmdl"
    empty_tmdl.mkdir()
    fails = sqldesc_cli.preflight(
        empty_tmdl, bad_sql, tmp_path / "out")
    text = " | ".join(fails)
    assert any("OPENAI_API_KEY" in f for f in fails)
    assert "*.sql" in text          # the bare-name trap, named
    assert "SemanticModel" in text  # the empty-tmdl trap, named
    # the good world: everything present -> only the key fails
    (bad_sql / "GOOD.sql").write_text("SELECT 1")
    model = empty_tmdl / "Fix.SemanticModel" / "definition"
    model.mkdir(parents=True)
    fails2 = sqldesc_cli.preflight(
        empty_tmdl, bad_sql, tmp_path / "out")
    assert all("OPENAI_API_KEY" in f or "degrade" in f
               for f in fails2)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-for-preflight")
    fails3 = sqldesc_cli.preflight(
        empty_tmdl, bad_sql, tmp_path / "out")
    assert fails3 == []


def test_deliver_refuses_on_preflight_failure(tmp_path,
                                              monkeypatch):
    """THE REFUSAL (Brief_Preflight, ruled 2026-10-06): deliver
    runs the preflight first and refuses to start on any
    failure except the missing key — no paid call ever fires
    into a broken environment, mechanically."""
    import sqldesc_cli
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    empty_sql = tmp_path / "sql"
    empty_sql.mkdir()                       # zero *.sql: a FAIL
    tmdl = tmp_path / "tmdl"
    (tmdl / "Fix.SemanticModel").mkdir(parents=True)
    try:
        sqldesc_cli.deliver(tmdl, empty_sql, tmp_path / "out")
        raise AssertionError("deliver must refuse on preflight "
                             "failures")
    except ValueError as e:
        assert "*.sql" in str(e)            # the board rides out


def test_cli_deliver_no_key_degrades_honestly(tmp_path,
                                              monkeypatch):
    """The 0.5.0 --deliver chain without a key: technical voice
    only, no terms proposed, ai_delivery.json + the official txt
    still land — an honest degrade, never a crash, never a
    silent business claim."""
    import sqldesc_cli
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    tmdl, sql = _official_fixture(tmp_path)
    out = tmp_path / "out"
    delivery = sqldesc_cli.deliver(tmdl, sql, out)
    assert (out / "ai_delivery.json").exists()
    rep = next(e for e in delivery["reports"]
               if e["report"] == "Fix")
    assert rep["description"]["voice"] == "technical"
    assert rep.get("terms", []) == []      # no key, no proposals
    txt = (out / "08_report_descriptions.txt").read_text()
    assert "voice: technical" in txt
