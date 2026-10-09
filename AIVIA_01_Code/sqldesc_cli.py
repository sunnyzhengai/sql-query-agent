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

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

_EMPTY_02 = ("02_emr_data_dictionary_extraction_column.json",
             "02_emr_data_dictionary_extraction_join.json",
             "02_emr_data_dictionary_extraction_value.json")


def _point_at_packaged_dll():
    """AMENDED 2026-10-06 (the vanishing-DLL find at the
    rehearsal): as_file() can hand out a TEMP copy that dies
    with its context — the env var then points at nothing.
    Now: revalidate an existing pointer (a dead path is
    cleared, never trusted), and stage the packaged bytes to a
    STABLE dir ourselves."""
    dll_name = "Microsoft.SqlServer.TransactSql.ScriptDom.dll"
    current = os.environ.get("SCRIPTDOM_DLL")
    if current:
        if Path(current).exists():
            return
        del os.environ["SCRIPTDOM_DLL"]  # dead pointer: clear
    try:
        from importlib.resources import files
        data = (files("ai_sqldesc_assets") / dll_name).read_bytes()
        stable = Path(tempfile.mkdtemp(prefix="sqldesc_dll_"))
        target = stable / dll_name
        target.write_bytes(data)
        os.environ["SCRIPTDOM_DLL"] = str(target)
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


def describe_technical(sql_dir, out_dir, dict_dir=None):
    """Folder of .sql in -> per-file technical .txt out.
    (RENAMED from describe() 2026-10-08, the naming law: the
    ruled name describe() now belongs to the PAID batch door;
    this free door keeps the CLI bare mode unchanged.)
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
    describe_technical(sql_dir, out, dict_dir=dict_dir)
    sheet = json.loads(
        (out / "06_technical_descriptions_output.json").read_text())
    file_sentence = {r["node_id"].split("::")[1]: r["sentence"]
                     for r in sheet if r["grain"] == "file"}
    business_card = {}
    if business_dir:
        biz = json.loads(
            (Path(business_dir) / "07_business_descriptions_output.json")
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
    # the naming law (2026-10-08): step-08 door, step-08 names
    (out / "08_pbi_lineage_descriptions_output.txt").write_text(
        "\n".join(blocks))
    (out / "08_pbi_lineage_descriptions_output.json").write_text(
        json.dumps(rows, indent=1))
    print(f"08 report descriptions: {len(rows)} report(s)")
    return rows


def sweep(sql_dir, out_dir, dict_dir=None):
    """THE CONSTRUCT CENSUS (ruled 2026-10-07, first customer
    tenant — the step-back after TRY_PARSE stopped a paid run).

    PSEUDO:
      walk EVERY corpus file through ScriptDom + the stage 1-5
      mapping with the four RED BUILD stops set to collect-and-
      continue (semantic_graph.build collect_unmapped) ->
      aggregate {construct, site} -> count / files / one evidence
      example -> print the census, write out/11_construct_census
      .json, return it.
      ZERO LLM calls — free, repeatable; run BEFORE the first
      paid run, rule every missing construct in ONE batch, pay
      once. deliver()/describe() keep the hard stop unchanged.
    """
    _point_at_packaged_dll()
    import semantic_graph
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    collected = []
    with tempfile.TemporaryDirectory() as tmp:
        d02 = Path(dict_dir) if dict_dir else _stage_empty_dict(tmp)
        d05 = Path(tmp) / "05"
        d05.mkdir()
        _stage_kind_library(d05)
        semantic_graph.build(sql_dir, d05, d02,
                             collect_unmapped=collected)
    groups = {}
    for e in collected:
        g = groups.setdefault((e["construct"], e["site"]), {
            "construct": e["construct"], "site": e["site"],
            "count": 0, "files": [],
            "example": {"file": e["file"], "line": e["line"],
                        "fragment": e["fragment"]}})
        g["count"] += 1
        if e["file"] not in g["files"]:
            g["files"].append(e["file"])
    constructs = sorted(groups.values(),
                        key=lambda g: (-g["count"], g["construct"]))
    for g in constructs:
        g["files"].sort()
    census = {
        "files_swept": len(_corpus_files(sql_dir)),
        "files_affected": sorted({e["file"] for e in collected}),
        "constructs": constructs,
    }
    (out / "11_construct_census_output.json").write_text(
        json.dumps(census, indent=1))
    for g in constructs:
        ex = g["example"]
        print(f"UNMAPPED {g['construct']} ({g['site']}): "
              f"{g['count']} hit(s) in {len(g['files'])} file(s) — "
              f"e.g. {ex['file']} L{ex['line']}: {ex['fragment']!r}")
    print(f"sweep: {census['files_swept']} file(s), "
          f"{len(census['files_affected'])} with unmapped "
          f"constructs, {len(constructs)} distinct construct(s)")
    return census


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

    # 0. the DLL pointer stages BEFORE any engine import
    # (rehearsal find #5: imports first froze an empty pointer)
    _point_at_packaged_dll()

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
    # 4. the key (presence only — never printed). BLOCKING since
    # 2026-10-08 (D4 degrade retired): the sequence law — fix,
    # re-run this cell, only then proceed.
    _check(bool(os.environ.get("OPENAI_API_KEY")),
           "OPENAI_API_KEY offered",
           "set it from the vault secret (the key cell), then "
           "re-run this cell")
    # 5. the folders
    sql_dir, tmdl_dir = Path(sql_dir), Path(tmdl_dir)
    n_sql = len(list(sql_dir.glob("*.sql"))) \
        if sql_dir.exists() else 0
    _check(n_sql > 0, f"sql input: {n_sql} *.sql file(s)",
           "upload .sql files WITH the extension (bare names "
           "are invisible to the sweep)")
    # D11 path 2 (2026-10-07): one subfolder per source workspace
    # is legal — the count walks recursively, and two models
    # sharing a BARE name is a refusal (the silent last-wins trap).
    qual_names = sorted(
        m.relative_to(tmdl_dir).as_posix()
        .removesuffix(".SemanticModel")
        for m in tmdl_dir.glob("**/*.SemanticModel")) \
        if tmdl_dir.exists() else []
    n_mod = len(qual_names)
    _check(n_mod > 0,
           f"tmdl: {n_mod} *.SemanticModel folder(s)",
           "point at the folder CONTAINING the .SemanticModel "
           "folders (else every term lands report-less)")
    by_base = {}
    for n in qual_names:
        by_base.setdefault(n.rsplit("/", 1)[-1], []).append(n)
    twins = {b: ns for b, ns in sorted(by_base.items())
             if len(ns) > 1}
    for base, ns in twins.items():
        _check(False,
               f"tmdl: bare model name collision: {base} "
               f"({', '.join(ns)})",
               "two workspaces ship the same report name — "
               "rename one folder or keep one copy")
    if n_mod and not twins:
        _check(True, "tmdl: no bare-name collisions", "")
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


# PSEUDO-CODE — D12 the ledger + batch door, D11 the collision
# refusal (10_work_wheel.md, ruled 2026-10-07; red tests:
# test_10_incremental_delivery.py x8, test_07 defer x1, test_09
# l17 x1). APPROVED by Sunny 2026-10-07; the code follows:
#
#   THE LEDGER (10_corpus_ledger.json in <out>):
#   1. record_corpus(sql_dir, out_dir, files=None) — store the
#      sha256 of each named file's content (default: all corpus
#      files); merge into the existing ledger, never truncate.
#   2. plan_corpus(sql_dir, out_dir, max_new=None, force=False)
#      -> {"new": [...], "done": [...], "remaining": int}
#      done = hash matches the ledger; new = the rest (force
#      makes everything new), NAME ORDER; max_new caps new and
#      counts the overflow in remaining. Corpus selection law =
#      semantic_graph's (regular, non-hidden, non-.json).
#
#   THE THREE CLASSES PER RUN (the batch door):
#      done     -> skip_files  (carry + refusal — built)
#      taken    -> the active set (proposes, pays)
#      deferred -> defer_files (new beyond max_new: DROPPED from
#                  the run — no rows, no carry, no refusal; a
#                  later run takes them). defer_files is a new
#                  param on build07 AND build09, filtering
#                  exactly like skip_files minus the carry.
#
#   DELIVER WIRING:
#   3. deliver(..., max_new=None, force=False): after the
#      preflight gate, plan once; 05/06/08 still build over the
#      WHOLE corpus (local, free — the graph stays whole);
#      build07/build09 get skip_files=stems(done),
#      defer_files=stems(deferred).
#   4. record_corpus runs ONLY after the paid chain succeeded,
#      and ONLY for the taken files — the honest-degrade path
#      (no key) records NOTHING: nothing was described.
#   5. The run SAYS it: "N described, M remain" (M = deferred).
#
#   THE PREFLIGHT (D11 path 2):
#   6. New check row: read_models over tmdl; two model names
#      sharing a BASENAME (same bare name, different workspace
#      folders) -> FAIL line naming the twins and both folders.
#      Rides the existing refusal: deliver() refuses on any
#      preflight failure except the missing key.


# =====================================================================
# PSEUDO-CODE — 0.7.0: D14 THE SPLIT + THE STAMP, THE NAMING LAW,
# D4 DEGRADE RETIRED (10_work_wheel.md D4/D7/D8/D12/D14 + the step
# table in 10_work_wheel_data_contract.md + the 09 contract's
# delivered-goods ruling, all RULED 2026-10-08). AWAITING SUNNY'S
# APPROVAL; red tests before code; the code follows this block.
#
#   THE TWO DOORS (D14):
#   1. build(tmdl_dir, sql_dir, out_dir, dict_dir=None) — FREE,
#      whole corpus, run when inputs change:
#        preflight FIRST — ANY failure refuses (the sequence law;
#        the missing-key exception is DEAD, build included) ->
#        05 graph + 06 technical + 08 links over ALL files ->
#        write the stamp: 13_build_stamp_output.json =
#        {"corpus": sha256 over the sorted "name:content-sha256"
#         lines of 01_sql_input, "files": N, "_law": ...} ->
#        print "built: N file(s), stamp written".
#   2. describe(tmdl_dir, sql_dir, out_dir, dict_dir=None,
#      max_new=None, force=False) — PAID, the batch:
#        preflight FIRST (same refusal) ->
#        THE GUARD: recompute the corpus fingerprint; stamp
#        missing or mismatched -> refuse: "the build is stale:
#        run the build cell first" (no paid call against a
#        stale graph — a test, not advice) ->
#        plan_corpus -> done/taken/deferred (D12 unchanged) ->
#        build07 cards + build09 terms (skip/defer as built) ->
#        record_corpus(taken) ->
#        assemble the delivery (LEDGER-ONLY membership +
#        files_described[]/files_waiting[] — ai_delivery.py's
#        own pseudo, next file) ->
#        write 12_ai_delivery_output.txt (the human twin; the
#        old 08_report_descriptions.txt name RETIRES) ->
#        say it: "N described (K already done), M remain".
#   3. deliver(...) SURVIVES as the wrapper (her ruling): build
#      then describe, same signature as today, nothing more.
#
#   THE NAME COLLISION (flagged for Sunny): this file already
#   owns describe() — the FREE technical-txt door (ai-describe's
#   bare mode, built 2026-10-04). RECOMMENDATION: rename it
#   describe_technical() (the CLI bare mode calls it unchanged);
#   the paid batch door takes the ruled name describe().
#
#   THE RENAMES THIS FILE OWNS (the step table):
#   4. LEDGER_NAME -> "10_corpus_ledger_output.json";
#      11_construct_census.json -> 11_construct_census_output
#      .json (sweep); the official txt -> 12_ai_delivery_output
#      .txt; the working dirs out/05 -> out/05_semantic_graph,
#      out/06 dies (06 files land in out root per the table),
#      out/07 -> out/07_business_descriptions.
#   5. THE MIGRATION READ (first customer tenant already holds
#      a 20-file ledger — renaming must never cause a re-pay):
#      _read_ledger reads the NEW name; absent, it reads the OLD
#      10_corpus_ledger.json once and the next record writes the
#      new name. Same one-time fallback where the registry is
#      read (07_business_descriptions_blessings_output.json -> its _output name).
#      Delivery/txt need no migration — regenerated every run.
#   6. The --reports door (report_descriptions / home-side
#      convenience): its 08_report_descriptions.{txt,json} —
#      the txt name now belongs to nobody; per the law they
#      become 08_pbi_lineage_descriptions_output.{txt,json}
#      [flagged: or retire the door — Sunny's call].
#
#   THE PREFLIGHT AMENDMENT (D4/D8):
#   7. The key row's fix line drops the degrade words: "set it
#      from the vault secret, then re-run this cell" — and the
#      callers stop filtering it: build/describe/deliver refuse
#      on ANY failure. The degrade branch in the describe door
#      (the else-print) is DELETED.
#
#   THE LOCKS (red before code):
#   8. test_10_incremental_delivery: the split (build alone
#      writes no 07/12; describe without build refuses; stamp
#      mismatch refuses with the fix line; deliver == build +
#      describe); the migration read (old ledger name honored
#      once, no re-pay). test_packaging_wheel: the degrade lock
#      FLIPS (no key -> ValueError refusal, nothing written);
#      the official-txt lock moves to the 12 name. The rename
#      sweep itself locks in each module's own test file as its
#      pseudo lands (one file at a time).
# =====================================================================

LEDGER_NAME = "10_corpus_ledger_output.json"
LEDGER_OLD = "10_corpus_ledger.json"   # pre-0.7.0 tenants
STAMP_NAME = "13_build_stamp_output.json"


def _corpus_files(sql_dir):
    """The corpus selection law — semantic_graph's, verbatim:
    every regular, non-hidden, non-.json file."""
    return sorted(p.name for p in Path(sql_dir).iterdir()
                  if p.is_file() and not p.name.startswith(".")
                  and p.suffix != ".json")


def _read_ledger(out_dir):
    """THE MIGRATION READ (2026-10-08): the new name first; a
    pre-rename tenant's old ledger is honored so the rename
    never causes a re-pay. The next record writes the new name."""
    for name in (LEDGER_NAME, LEDGER_OLD):
        p = Path(out_dir) / name
        if p.exists():
            return json.loads(p.read_text())
    return {"hashes": {}}


def record_corpus(sql_dir, out_dir, files=None):
    """D12: mark files DESCRIBED — content sha256 into the
    ledger; merge, never truncate. deliver() calls this for the
    taken files only, after the paid chain succeeded."""
    sql_dir = Path(sql_dir)
    names = (list(files) if files is not None
             else _corpus_files(sql_dir))
    led = _read_ledger(out_dir)
    led.setdefault("_law", "described = done (D12, 2026-10-07): "
                   "a matching hash is never re-sent to the seat")
    for n in names:
        led["hashes"][n] = hashlib.sha256(
            (sql_dir / n).read_bytes()).hexdigest()
    (Path(out_dir) / LEDGER_NAME).write_text(
        json.dumps(led, indent=1))


def plan_corpus(sql_dir, out_dir, max_new=None, force=False):
    """D12: the run plans itself — nobody types file names.
    done = content hash matches the ledger; new = the rest, name
    order; max_new caps new and counts the overflow."""
    sql_dir = Path(sql_dir)
    hashes = _read_ledger(out_dir)["hashes"]
    done, new = [], []
    for n in _corpus_files(sql_dir):
        h = hashlib.sha256((sql_dir / n).read_bytes()).hexdigest()
        (done if not force and hashes.get(n) == h
         else new).append(n)
    remaining = 0
    if max_new is not None and len(new) > max_new:
        remaining = len(new) - max_new
        new = new[:max_new]
    return {"new": new, "done": done, "remaining": remaining}


def _refuse_on_preflight(tmdl_dir, sql_dir, out_dir, dict_dir):
    """D8 as amended 2026-10-08: ANY failure refuses — the
    missing-key exception retired with D4's degrade."""
    blocking = preflight(tmdl_dir, sql_dir, out_dir,
                         dict_dir=dict_dir)
    if blocking:
        raise ValueError("preflight refused the run:\n  "
                         + "\n  ".join(blocking))


def _offer_runtime_assets(sql_dir, dict_dir):
    """The runtime-offered pair (2026-10-05, both rehearsal
    crashes): the names asset beside the dictionary and the
    corpus home — offered to the paid voices via env."""
    d03 = Path(dict_dir).parent / "03_chat_bot" \
        if dict_dir else None
    if d03 and d03.exists() \
            and not os.environ.get("AI_NAMES_DIR"):
        os.environ["AI_NAMES_DIR"] = str(d03)
    os.environ.setdefault("AI_SQL_DIR", str(Path(sql_dir)))


def _corpus_fingerprint(sql_dir):
    """The stamp's one number: sha256 over the sorted
    name:content-hash lines of the corpus."""
    sql_dir = Path(sql_dir)
    lines = sorted(
        f"{n}:{hashlib.sha256((sql_dir / n).read_bytes()).hexdigest()}"
        for n in _corpus_files(sql_dir))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def build(tmdl_dir, sql_dir, out_dir, dict_dir=None):
    """THE BUILD DOOR (D14, ruled 2026-10-08): the free
    whole-corpus work — 05 graph + 06 technical + 08 links —
    run it when the input folders change. Writes the step-13
    stamp so describe() can prove its graph is current. The
    preflight refuses on ANY failure (the sequence law)."""
    _refuse_on_preflight(tmdl_dir, sql_dir, out_dir, dict_dir)
    _point_at_packaged_dll()
    import pbi_lineage as pl
    import semantic_graph
    import technical_descriptions as td
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    d05 = out / "05_semantic_graph"
    d05.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d02 = Path(dict_dir) if dict_dir else \
            _stage_empty_dict(tmp)
        _offer_runtime_assets(sql_dir, dict_dir)
        _stage_kind_library(d05)
        semantic_graph.build(sql_dir, d05, d02)
        td.build06(d05, out, d02, sql_dir)
        pl.build08(tmdl_dir, sql_dir, out)
    n = len(_corpus_files(sql_dir))
    (out / STAMP_NAME).write_text(json.dumps({
        "corpus": _corpus_fingerprint(sql_dir),
        "files": n,
        "_law": "the guard (D14, 2026-10-08): describe() "
                "refuses when 01_sql_input no longer matches "
                "this stamp — run the build cell first"},
        indent=1))
    print(f"built: {n} file(s), stamp written")
    return out


def describe(tmdl_dir, sql_dir, out_dir, dict_dir=None,
             max_new=None, force=False):
    """THE DESCRIBE DOOR (D14): the paid batch — 07 cards + 09
    terms + the 10 ledger + the 12 delivery. Preflight refuses
    on ANY failure; THE GUARD refuses a stale or missing build
    before any paid call. D12 unchanged: described = done,
    max_new caps the batch (name order), force re-pays all."""
    _refuse_on_preflight(tmdl_dir, sql_dir, out_dir, dict_dir)
    out = Path(out_dir)
    stamp_p = out / STAMP_NAME
    stale = (not stamp_p.exists()
             or json.loads(stamp_p.read_text())["corpus"]
             != _corpus_fingerprint(sql_dir))
    if stale:
        raise ValueError("the build is stale or missing: "
                         "run the build cell first")
    _point_at_packaged_dll()
    import ai_delivery
    import business_descriptions as bd
    import business_terms as bt
    d05 = out / "05_semantic_graph"
    d07 = out / "07_business_descriptions"
    d07.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        d02 = Path(dict_dir) if dict_dir else \
            _stage_empty_dict(tmp)
        _offer_runtime_assets(sql_dir, dict_dir)
        plan = plan_corpus(sql_dir, out, force=force)
        taken = (plan["new"] if max_new is None
                 else plan["new"][:max_new])
        deferred = plan["new"][len(taken):]
        skip = {Path(n).stem for n in plan["done"]}
        defer = {Path(n).stem for n in deferred}
        bd.build07(d05, out, d07, d02,
                   skip_files=skip, defer_files=defer)
        bt.build09(d05, out, d02, d07, out, out,
                   skip_files=skip, defer_files=defer)
        record_corpus(sql_dir, out, files=taken)
        print(f"{len(taken)} described ({len(skip)} already "
              f"done), {len(deferred)} remain")
        ai_delivery.assemble(out, d07, out, out)
    delivery = ai_delivery.load(out)
    (out / "12_ai_delivery_output.txt").write_text(
        _delivery_txt(delivery))
    print(f"delivery: {len(delivery['reports'])} report(s), "
          f"{len(delivery['reportless_files'])} reportless "
          "file(s)")
    return delivery


def _delivery_txt(delivery):
    """The human twin — regenerated from the delivery file (the
    consolidation ruling; 12_* per the naming law). BOTH sections
    render (her find, 2026-10-08: reports-only printed EMPTY on a
    views-heavy corpus while the json held everything)."""
    blocks = []

    def _terms(e):
        for t in e.get("terms", []):
            blocks.append(
                f"-- TERM [{t['bt_name_status']}]: "
                f"{t['bt_name']}\n{t['business_description']}\n")

    for e in delivery["reports"]:
        d = e.get("description") or {}
        waiting = e.get("files_waiting", [])
        blocks.append(f"==== REPORT: {e['report']} ====\n"
                      f"feeds from: {', '.join(e['files'])}\n"
                      + (f"waiting: {', '.join(waiting)} "
                         "(incomplete — not published)\n"
                         if waiting else "")
                      + f"voice: {d.get('voice', 'technical')}\n\n"
                      f"{d.get('text', '')}\n")
        _terms(e)
    for e in delivery["reportless_files"]:
        d = e.get("description") or {}
        blocks.append(f"==== FILE: {e['file']} ====\n"
                      "(no report ties to this file yet — "
                      "terms stay unpublished)\n"
                      f"voice: {d.get('voice', 'technical')}\n\n"
                      f"{d.get('text', '')}\n")
        _terms(e)
    return "\n".join(blocks)


def deliver(tmdl_dir, sql_dir, out_dir, dict_dir=None,
            max_new=None, force=False):
    """THE WRAPPER (her ruling, 2026-10-08): build then
    describe, nothing more — the one-call shortcut for a small
    corpus; the runbook's cells call the two doors directly."""
    build(tmdl_dir, sql_dir, out_dir, dict_dir=dict_dir)
    return describe(tmdl_dir, sql_dir, out_dir,
                    dict_dir=dict_dir, max_new=max_new,
                    force=force)


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
    if argv and argv[0] == "--sweep":
        if len(argv) != 3:
            print("usage: ai-describe --sweep <sql_dir> <out_dir> "
                  "[--dict <dir02>]")
            return 2
        census = sweep(argv[1], argv[2], dict_dir=dict_dir)
        return 1 if census["constructs"] else 0
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
    describe_technical(argv[0], argv[1], dict_dir=dict_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
