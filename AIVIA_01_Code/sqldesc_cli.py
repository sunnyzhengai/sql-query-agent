# =====================================================================
# sqldesc_cli.py — the work wheel's one command (Brief_Packaging,
# STAMPED 2026-10-04; pseudo + code in one landing at her "build
# the wheel").
#
# PSEUDO:
#   ai-describe <sql_dir> <out_dir>
#       stage an EMPTY 02 dictionary (no dictionary at work —
#       degraded words, honest, counted by the 06 ledger) ->
#       semantic_graph.build (05 sheets, temp) ->
#       technical_descriptions.build06 -> per-file .txt in out_dir
#   ai-describe --reports <tmdl_dir> <sql_dir> <out_dir>
#       the D8 end-to-end: pbi_lineage.build08 + the describe
#       chain -> 08_report_descriptions.json (report name +
#       the description of each linked sql file)
#   The DLL: before any engine import, point SCRIPTDOM_DLL at
#   the packaged copy (ai_sqldesc_assets) — the loader's
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
        dll = files("ai_sqldesc_assets") / \
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
        src = files("ai_sqldesc_assets") / \
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


def preflight(tmdl_dir, sql_dir, out_dir, dict_dir=None):
    """THE PREFLIGHT (her ask, 2026-10-06, after the rehearsal's
    httpx find): check EVERY prereq before any paid call —
    report-all, each failure names its fix, zero network, zero
    cost. Returns the failure list (empty == go); prints the
    full board either way."""
    checks = []  # (ok, line)

    def _check(ok, what, fix):
        checks.append((ok, f"{what}" + ("" if ok else
                                        f" -> FIX: {fix}")))

    # 1. the engine modules (the dueling-wheels trap)
    for m in ("semantic_graph", "technical_descriptions",
              "pbi_lineage", "business_descriptions",
              "business_terms", "ai_delivery"):
        try:
            __import__(m)
            _check(True, f"module {m}", "")
        except Exception as exc:  # noqa: BLE001
            _check(False, f"module {m}: {type(exc).__name__}",
                   "one sqldesc wheel only; publish; FRESH session")
    # 2. the parser door (the loader's two-route law: env var
    # from the packaged assets, or the repo's libs/ fallback)
    _point_at_packaged_dll()
    repo_dll = (Path(__file__).resolve().parents[1] / "libs" /
                "Microsoft.SqlServer.TransactSql.ScriptDom.dll")
    _check(bool(os.environ.get("SCRIPTDOM_DLL"))
           or repo_dll.exists(),
           "ScriptDom DLL reachable",
           "the wheel's assets package should set SCRIPTDOM_DLL")
    # 3. the seat (amended 2026-10-06, the httpx2 find: never
    # guess transport names — import openai and CONSTRUCT the
    # client with a dummy key; zero network, and any missing
    # dependency fails here with its real message)
    try:
        import openai as _oa
        _check(True, f"seat library openai {_oa.__version__}",
               "")
        try:
            from openai import OpenAI
            OpenAI(api_key="preflight-construct-probe")
            _check(True, "seat client constructs", "")
        except Exception as exc:  # noqa: BLE001
            _check(False, "seat client: "
                   f"{type(exc).__name__}: {str(exc)[:120]}",
                   "the openai install is incomplete — add "
                   "openai (pinned) as a PUBLIC/YML library; "
                   "publish; FRESH session")
    except Exception as exc:  # noqa: BLE001
        _check(False, f"seat library openai: "
               f"{type(exc).__name__}",
               "add openai (pinned) as a PUBLIC library in the "
               "environment; publish; FRESH session")
    # 4. the key (presence only — never printed)
    _check(bool(os.environ.get("OPENAI_API_KEY")),
           "OPENAI_API_KEY offered",
           "set it from the vault secret BEFORE the run, else "
           "honest degrade: technical voice, no terms")
    # 5. the folders
    sql_dir, tmdl_dir = Path(sql_dir), Path(tmdl_dir)
    n_sql = len(list(sql_dir.glob("*.sql"))) \
        if sql_dir.exists() else 0
    _check(n_sql > 0, f"sql input: {n_sql} *.sql file(s)",
           "upload .sql files WITH the extension (bare names "
           "are invisible to the sweep)")
    n_mod = len(list(tmdl_dir.glob("*.SemanticModel"))) \
        if tmdl_dir.exists() else 0
    _check(n_mod > 0,
           f"tmdl: {n_mod} *.SemanticModel folder(s)",
           "point at the folder CONTAINING the .SemanticModel "
           "folders (else every term lands report-less)")
    if dict_dir:
        d02 = Path(dict_dir)
        missing = [f for f in
                   ("02_emr_data_dictionary_extraction_column"
                    ".json",
                    "02_emr_data_dictionary_extraction_value"
                    ".json",
                    "02_emr_data_dictionary_extraction_table"
                    ".json")
                   if not (d02 / f).exists()]
        _check(not missing,
               "dictionary: the three files present" if not
               missing else f"dictionary missing: {missing}",
               "upload the three extraction files (words speak)")
    try:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        probe = out / ".preflight_probe"
        probe.write_text("ok")
        probe.unlink()
        _check(True, "out dir writable", "")
    except Exception as exc:  # noqa: BLE001
        _check(False, f"out dir: {type(exc).__name__}",
               "check the lakehouse path/permissions")

    for ok, line in checks:
        print(("PASS  " if ok else "FAIL  ") + line)
    failures = [line for ok, line in checks if not ok]
    print(f"preflight: {len(checks) - len(failures)} pass / "
          f"{len(failures)} fail")
    return failures


def deliver(tmdl_dir, sql_dir, out_dir, dict_dir=None):
    """THE 0.5.0 COLLIBRA CHAIN (ruled 2026-10-05, G-1 + G-2):
    08 links -> 05 graph -> 06 technical -> 07 cards -> 09 terms
    -> ai_delivery.json + the official txt. The LLM seat is
    RUNTIME-OFFERED: OPENAI_API_KEY in the environment (the
    notebook sets it from a secret). No key -> HONEST DEGRADE:
    technical voice, no terms proposed, said out loud.
    THE REFUSAL (Brief_Preflight, 2026-10-06): the preflight
    runs FIRST; any failure except the missing key refuses the
    run — no paid call into a broken environment, ever."""
    blocking = [f for f in preflight(tmdl_dir, sql_dir, out_dir,
                                     dict_dir=dict_dir)
                if "OPENAI_API_KEY" not in f]
    if blocking:
        raise ValueError("preflight refused the run:\n  "
                         + "\n  ".join(blocking))
    _point_at_packaged_dll()
    import ai_delivery
    import pbi_lineage as pl
    import semantic_graph
    import technical_descriptions as td
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    d05, d06, d07 = out / "05", out / "06", out / "07"
    for d in (d05, d06, d07):
        d.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d02 = Path(dict_dir) if dict_dir else \
            _stage_empty_dict(tmp)
        # the naming asset, runtime-offered (2026-10-05): when a
        # dictionary is offered and a 03_chat_bot folder sits
        # beside it, its names speak; absent = honest fallback
        d03 = Path(dict_dir).parent / "03_chat_bot" \
            if dict_dir else None
        if d03 and d03.exists() \
                and not os.environ.get("AI_NAMES_DIR"):
            os.environ["AI_NAMES_DIR"] = str(d03)
        # the corpus home, same law (the second rehearsal
        # crash): the runner knows its sql folder — offer it
        os.environ.setdefault("AI_SQL_DIR", str(Path(sql_dir)))
        _stage_kind_library(d05)
        semantic_graph.build(sql_dir, d05, d02)
        td.build06(d05, d06, d02, sql_dir)
        pl.build08(tmdl_dir, sql_dir, out)
        if os.environ.get("OPENAI_API_KEY"):
            import business_descriptions as bd
            import business_terms as bt
            bd.build07(d05, d06, d07, d02)
            bt.build09(d05, d06, d02, d07, out, out)
        else:
            print("no OPENAI_API_KEY offered: technical voice "
                  "only, no terms proposed (honest degrade)")
        ai_delivery.assemble(out, d07, out, d06)
    delivery = ai_delivery.load(out)

    # the official txt — the human read view, regenerated from
    # the delivery file (the consolidation ruling)
    blocks = []
    for e in delivery["reports"]:
        d = e.get("description") or {}
        blocks.append(f"==== REPORT: {e['report']} ====\n"
                      f"feeds from: {', '.join(e['files'])}\n"
                      f"voice: {d.get('voice', 'technical')}\n\n"
                      f"{d.get('text', '')}\n")
        for t in e.get("terms", []):
            blocks.append(
                f"-- TERM [{t['bt_name_status']}]: "
                f"{t['bt_name']}\n{t['business_description']}\n")
    (out / "08_report_descriptions.txt").write_text(
        "\n".join(blocks))
    print(f"ai_delivery.json: {len(delivery['reports'])} "
          f"report(s), {len(delivery['reportless_files'])} "
          "reportless file(s)")
    return delivery


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
    if argv and argv[0] == "--preflight":
        if len(argv) != 4:
            print("usage: ai-describe --preflight <tmdl_dir> "
                  "<sql_dir> <out_dir> [--dict <dir02>]")
            return 2
        return 1 if preflight(argv[1], argv[2], argv[3],
                              dict_dir=dict_dir) else 0
    if argv and argv[0] == "--deliver":
        if len(argv) != 4:
            print("usage: ai-describe --deliver <tmdl_dir> "
                  "<sql_dir> <out_dir> [--dict <dir02>]")
            return 2
        deliver(argv[1], argv[2], argv[3], dict_dir=dict_dir)
        return 0
    if argv and argv[0] == "--reports":
        if len(argv) != 4:
            print("usage: ai-describe --reports <tmdl_dir> "
                  "<sql_dir> <out_dir> [--dict <dir02>] "
                  "[--business <dir07>]")
            return 2
        report_descriptions(argv[1], argv[2], argv[3],
                            dict_dir=dict_dir,
                            business_dir=business_dir)
        return 0
    if len(argv) != 2:
        print("usage: ai-describe <sql_dir> <out_dir> "
              "[--dict <dir02>]")
        return 2
    describe(argv[0], argv[1], dict_dir=dict_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
