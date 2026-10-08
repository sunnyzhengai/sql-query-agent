"""Wheel 0.6.1 contract tests — the PARSE ruling + the construct
census sweep (chat-ruled 2026-10-07 on the first customer tenant:
TRY_PARSE hit the RED BUILD stop mid-paid-run; the step-back ask:
discover EVERY unmapped construct in one free pass, rule in batch,
pay once).

Written RED first:
  1. ParseCall/TryParseCall join the cast kind (the conversion
     family's two string-input members — StringValue + optional
     Culture, verified against ScriptDom 18.0.78.1).
  2. sqldesc_cli.sweep(sql_dir, out_dir, dict_dir=None) — parse-only
     census: collects every unmapped construct at all four RED BUILD
     sites, never stops, writes out/11_construct_census.json,
     returns the census. Zero LLM calls.
  3. The honesty lock stays: WITHOUT collect mode, an unmapped
     construct still raises RED BUILD (deliver/describe unchanged).
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
KIND_LIBRARY = (REPO_ROOT / "AIVIA_01_Data" / "05_semantic_graph"
                / "05_kind_library.json")

sys.path.insert(0, str(CODE_DIR))
import semantic_graph  # noqa: E402
import sqldesc_cli  # noqa: E402

PARSE_SQL = """\
CREATE PROCEDURE dbo.USP_PARSE_FAMILY AS
BEGIN
    SELECT TRY_PARSE(PAT.BIRTH_TXT AS DATE) AS BORN,
           PARSE(PAT.SCORE_TXT AS INT USING 'en-US') AS SCORE
    FROM PATIENT PAT;
END
"""

# NEXT VALUE FOR is parseable, legal T-SQL and OUTSIDE the ratified
# expression set — the sweep's stand-in for the next unknown.
MYSTERY_SQL = """\
CREATE PROCEDURE dbo.USP_MYSTERY AS
BEGIN
    SELECT NEXT VALUE FOR dbo.SEQ_VISIT AS VISIT_ID;
END
"""

CLEAN_SQL = """\
CREATE PROCEDURE dbo.USP_CLEAN AS
BEGIN
    SELECT PAT.PAT_ID FROM PATIENT PAT WHERE PAT.PAT_ID > 0;
END
"""


def _stage(tmp_path, files):
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    for name, text in files.items():
        (sql_dir / name).write_text(text)
    d05 = tmp_path / "05"
    d05.mkdir()
    (d05 / "05_kind_library.json").write_text(
        KIND_LIBRARY.read_text())
    d02 = sqldesc_cli._stage_empty_dict(str(tmp_path))
    return sql_dir, d05, d02


def test_parse_family_maps_to_cast(tmp_path):
    """PARSE and TRY_PARSE land as the cast kind; the culture
    argument rides as a counted child, never dropped."""
    sql_dir, d05, d02 = _stage(tmp_path, {"pf.sql": PARSE_SQL})
    semantic_graph.build(sql_dir, d05, d02)  # must not raise
    rows = json.loads((d05 / "05_expression_sheet.json").read_text())
    casts = [r for r in rows if r["expression_kind"] == "cast"
             and "PARSE" in r["raw_text"].upper()]
    assert len(casts) == 2, [r["raw_text"] for r in casts]
    roles = {r.get("role") for r in rows}
    assert "culture" in roles  # PARSE ... USING 'en-US'


def test_red_build_still_raises_without_collect(tmp_path):
    """The honesty lock: no collect mode = the stop stands."""
    sql_dir, d05, d02 = _stage(tmp_path, {"m.sql": MYSTERY_SQL})
    with pytest.raises(RuntimeError, match="RED BUILD"):
        semantic_graph.build(sql_dir, d05, d02)


def test_build_collect_mode_continues(tmp_path):
    """collect_unmapped: the walk records and keeps going —
    every file finishes, the entry names file/construct/line."""
    sql_dir, d05, d02 = _stage(tmp_path, {
        "m.sql": MYSTERY_SQL, "ok.sql": CLEAN_SQL})
    collected = []
    semantic_graph.build(sql_dir, d05, d02,
                         collect_unmapped=collected)
    assert len(collected) == 1
    entry = collected[0]
    assert entry["file"] == "m.sql"
    assert entry["construct"] == "NextValueForExpression"
    assert entry["line"] >= 1
    assert "NEXT VALUE" in entry["fragment"].upper()


def test_sweep_census(tmp_path):
    """sweep(): aggregate census construct -> count/files/example,
    the json artifact lands, the clean file stays out of it."""
    sql_dir, d05, d02 = _stage(tmp_path, {
        "m.sql": MYSTERY_SQL, "ok.sql": CLEAN_SQL})
    out_dir = tmp_path / "out"
    census = sqldesc_cli.sweep(sql_dir, out_dir, dict_dir=d02)
    assert census["files_swept"] == 2
    assert census["files_affected"] == ["m.sql"]
    (hit,) = census["constructs"]
    assert hit["construct"] == "NextValueForExpression"
    assert hit["count"] == 1
    assert hit["files"] == ["m.sql"]
    on_disk = json.loads(
        (out_dir / "11_construct_census.json").read_text())
    assert on_disk == census


def test_sweep_clean_folder_is_empty_census(tmp_path):
    sql_dir, d05, d02 = _stage(tmp_path, {"ok.sql": CLEAN_SQL})
    out_dir = tmp_path / "out"
    census = sqldesc_cli.sweep(sql_dir, out_dir, dict_dir=d02)
    assert census["constructs"] == []
    assert census["files_affected"] == []
