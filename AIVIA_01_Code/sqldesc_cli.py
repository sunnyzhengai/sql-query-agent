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


def describe(sql_dir, out_dir, dict_dir=None):
    """Folder of .sql in -> per-file technical .txt out.
    dict_dir (RULED 2026-10-04, her post-D8 ask): a RUNTIME-
    OFFERED 02 dictionary folder — value meanings and column
    words speak; None = the empty-dictionary work mode (the
    wheel itself still ships NO dictionary, ever)."""
    _point_at_packaged_dll()
    import semantic_graph
    import technical_descriptions as td
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d02 = Path(dict_dir) if dict_dir else \
            _stage_empty_dict(tmp)
        d05 = Path(tmp) / "05"
        d05.mkdir()
        _stage_kind_library(d05)
        semantic_graph.build(sql_dir, d05, d02)
        td.build06(d05, out, d02, sql_dir)
    return out


def report_descriptions(tmdl_dir, sql_dir, out_dir,
                        dict_dir=None, business_dir=None):
    """The D8 chain: reports -> linked sql -> descriptions.
    business_dir (RULED 2026-10-04, her 'build it'): a RUNTIME-
    OFFERED 07 folder — each report row gains the clinician
    card for its linked files (blessed lines ride, the stored
    sheet carries them). The wheel ships no 07 content, ever."""
    import pbi_lineage as pl
    out = Path(out_dir)
    reports = pl.build08(tmdl_dir, sql_dir, out)
    describe(sql_dir, out, dict_dir=dict_dir)
    sheet = json.loads(
        (out / "06_description_sheet.json").read_text())
    file_sentence = {r["node_id"].split("::")[1]: r["sentence"]
                     for r in sheet if r["grain"] == "file"}
    business_card = {}
    if business_dir:
        biz = json.loads(
            (Path(business_dir) / "07_business_sheet.json")
            .read_text())
        business_card = {
            r["node_id"].split("::")[1]: r["audience_text"]
            for r in biz if r["grain"] == "file"}
    rows = []
    for r in reports:
        row = {
            "report": r["name"],
            "executes": r["executes"],
            "descriptions": {
                f: file_sentence.get(
                    f.removesuffix(".sql"),
                    "(no description rendered)")
                for f in r["executes"]},
        }
        if business_dir:
            row["business"] = {
                f: business_card.get(
                    f.removesuffix(".sql"),
                    "(no business card offered for this file)")
                for f in r["executes"]}
        rows.append(row)

    # THE OFFICIAL READ FILE (RULED 2026-10-04, her work-
    # transition ask): report, sql file, the description — the
    # VOICE labeled: business when a 07 sheet offered the card,
    # technical otherwise; never a silent downgrade.
    blocks = []
    for row in rows:
        for f in row["executes"]:
            card = (row.get("business") or {}).get(f)
            if card and not card.startswith("(no business"):
                voice = "business"
            else:
                voice = "technical"
                card = row["descriptions"].get(
                    f, "(no description rendered)")
            blocks.append(f"==== REPORT: {row['report']} ====\n"
                          f"feeds from: {f}\n"
                          f"voice: {voice}\n\n{card}\n")
    (out / "08_report_descriptions.txt").write_text(
        "\n".join(blocks))
    (out / "08_report_descriptions.json").write_text(
        json.dumps(rows, indent=1))
    print(f"08 report descriptions: {len(rows)} report(s)")
    return rows


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dict_dir = business_dir = None
    if "--dict" in argv:
        i = argv.index("--dict")
        dict_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if "--business" in argv:
        i = argv.index("--business")
        business_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if argv and argv[0] == "--reports":
        if len(argv) != 4:
            print("usage: aivia-describe --reports <tmdl_dir> "
                  "<sql_dir> <out_dir> [--dict <dir02>] "
                  "[--business <dir07>]")
            return 2
        report_descriptions(argv[1], argv[2], argv[3],
                            dict_dir=dict_dir,
                            business_dir=business_dir)
        return 0
    if len(argv) != 2:
        print("usage: aivia-describe <sql_dir> <out_dir> "
              "[--dict <dir02>]")
        return 2
    describe(argv[0], argv[1], dict_dir=dict_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
