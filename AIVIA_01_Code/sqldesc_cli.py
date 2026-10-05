# =====================================================================
# sqldesc_cli.py — the work wheel's one command (Brief_Packaging,
# STAMPED 2026-10-04; pseudo + code in one landing at her "build
# the wheel").
#
# PSEUDO:
#   aivia-describe <sql_dir> <out_dir>
#       stage an EMPTY 02 dictionary (no dictionary at work —
#       degraded words, honest, counted by the 06 ledger) ->
#       semantic_graph.build (05 sheets, temp) ->
#       technical_descriptions.build06 -> per-file .txt in out_dir
#   aivia-describe --reports <tmdl_dir> <sql_dir> <out_dir>
#       the D8 end-to-end: pbi_lineage.build08 + the describe
#       chain -> 08_report_descriptions.json (report name +
#       the description of each linked sql file)
#   The DLL: before any engine import, point SCRIPTDOM_DLL at
#   the packaged copy (aivia_sqldesc_assets) — the loader's
#   env-var-first route law, no fork.
#   Zero keys, zero network, stdlib only.
# =====================================================================

import json
import os
import sys
import tempfile
from pathlib import Path

_EMPTY_02 = ("02_emr_data_dictionary_extraction_column.json",
             "02_emr_data_dictionary_extraction_join.json",
             "02_emr_data_dictionary_extraction_value.json")


def _point_at_packaged_dll():
    if os.environ.get("SCRIPTDOM_DLL"):
        return
    try:
        from importlib.resources import files
        dll = files("aivia_sqldesc_assets") / \
            "Microsoft.SqlServer.TransactSql.ScriptDom.dll"
        with __import__("importlib.resources", fromlist=["as_file"]
                        ).as_file(dll) as p:
            os.environ["SCRIPTDOM_DLL"] = str(p)
    except (ModuleNotFoundError, FileNotFoundError):
        pass  # repo run: the loader's libs/ route stands


def _stage_kind_library(d05):
    """The ratified closed vocabulary: packaged copy first
    (the wheel), repo copy at home."""
    try:
        from importlib.resources import files
        src = files("aivia_sqldesc_assets") / \
            "05_kind_library.json"
        (Path(d05) / "05_kind_library.json").write_text(
            src.read_text())
        return
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    repo = Path(__file__).resolve().parents[1]
    import shutil
    shutil.copy(repo / "AIVIA_01_Data" / "05_semantic_graph" /
                "05_kind_library.json",
                Path(d05) / "05_kind_library.json")


def _stage_empty_dict(tmp):
    d = Path(tmp) / "02"
    d.mkdir()
    for f in _EMPTY_02:
        (d / f).write_text("[]")
    return d


def describe(sql_dir, out_dir):
    """Folder of .sql in -> per-file technical .txt out."""
    _point_at_packaged_dll()
    import semantic_graph
    import technical_descriptions as td
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d02 = _stage_empty_dict(tmp)
        d05 = Path(tmp) / "05"
        d05.mkdir()
        _stage_kind_library(d05)
        semantic_graph.build(sql_dir, d05, d02)
        td.build06(d05, out, d02, sql_dir)
    return out


def report_descriptions(tmdl_dir, sql_dir, out_dir):
    """The D8 chain: reports -> linked sql -> descriptions."""
    import pbi_lineage as pl
    out = Path(out_dir)
    reports = pl.build08(tmdl_dir, sql_dir, out)
    describe(sql_dir, out)
    sheet = json.loads(
        (out / "06_description_sheet.json").read_text())
    file_sentence = {r["node_id"].split("::")[1]: r["sentence"]
                     for r in sheet if r["grain"] == "file"}
    rows = []
    for r in reports:
        rows.append({
            "report": r["name"],
            "executes": r["executes"],
            "descriptions": {
                f: file_sentence.get(
                    f.removesuffix(".sql"),
                    "(no description rendered)")
                for f in r["executes"]},
        })
    (out / "08_report_descriptions.json").write_text(
        json.dumps(rows, indent=1))
    print(f"08 report descriptions: {len(rows)} report(s)")
    return rows


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--reports":
        if len(argv) != 4:
            print("usage: aivia-describe --reports <tmdl_dir> "
                  "<sql_dir> <out_dir>")
            return 2
        report_descriptions(argv[1], argv[2], argv[3])
        return 0
    if len(argv) != 2:
        print("usage: aivia-describe <sql_dir> <out_dir>")
        return 2
    describe(argv[0], argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
