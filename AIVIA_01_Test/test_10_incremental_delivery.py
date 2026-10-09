"""Phase 10 incremental-delivery tests (10_work_wheel.md D11 + D12,
ruled 2026-10-07 — her work scale-up: described = done; batches pick
themselves; bare-name collisions refused mechanically).

Written test-first: RED until sqldesc_cli exposes
    plan_corpus(sql_dir, out_dir, max_new=None, force=False)
        -> {"new": [names], "done": [names], "remaining": int}
    record_corpus(sql_dir, out_dir, files=None)  # the hash ledger
writing/reading 10_corpus_ledger.json in out_dir, and until the
preflight carries the D11 bare-name collision check.

DETERMINISTIC — no LLM, no network, no cost. Synthetic fixtures with
invented names only (the estate boundary).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"
sys.path.insert(0, str(CODE_DIR))

import sqldesc_cli  # noqa: E402

# THE NAMING LAW (ruled 2026-10-08, the step table): engine-made
# files end _output. RED until the 0.7.0 renames land.
LEDGER = "10_corpus_ledger_output.json"
LEDGER_OLD = "10_corpus_ledger.json"
STAMP = "13_build_stamp_output.json"


def _corpus(tmp_path, names=("fix_a.sql", "fix_b.sql", "fix_c.sql")):
    sql = tmp_path / "sql"
    sql.mkdir(exist_ok=True)
    for n in names:
        (sql / n).write_text(f"SELECT 1 -- {n}\n")
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return sql, out


# ------------------------------------------------- the plan (D12)

def test_plan_first_run_everything_new_name_order(tmp_path):
    sql, out = _corpus(tmp_path)
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["new"] == ["fix_a.sql", "fix_b.sql", "fix_c.sql"]
    assert plan["done"] == []
    assert plan["remaining"] == 0


def test_plan_max_new_takes_first_n_counts_rest(tmp_path):
    sql, out = _corpus(tmp_path)
    plan = sqldesc_cli.plan_corpus(sql, out, max_new=2)
    assert plan["new"] == ["fix_a.sql", "fix_b.sql"]
    assert plan["remaining"] == 1


def test_recorded_files_are_done_not_new(tmp_path):
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out)
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["new"] == []
    assert plan["done"] == ["fix_a.sql", "fix_b.sql", "fix_c.sql"]
    assert (out / LEDGER).exists()


def test_changed_content_is_new_again(tmp_path):
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out)
    (sql / "fix_b.sql").write_text("SELECT 2 -- changed\n")
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["new"] == ["fix_b.sql"]
    assert plan["done"] == ["fix_a.sql", "fix_c.sql"]


def test_new_arrivals_never_reprocess_the_done(tmp_path):
    """Her 3.1 (2026-10-07): later runs of the same folder skip the
    described and take only what arrived."""
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out)
    (sql / "fix_d.sql").write_text("SELECT 4\n")
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["new"] == ["fix_d.sql"]
    assert len(plan["done"]) == 3


def test_force_makes_everything_new(tmp_path):
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out)
    plan = sqldesc_cli.plan_corpus(sql, out, force=True)
    assert plan["new"] == ["fix_a.sql", "fix_b.sql", "fix_c.sql"]


def test_partial_record_marks_only_named_files(tmp_path):
    """deliver() records ONLY the files the run described — a
    max_new batch must not mark the remainder as done."""
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out, files=["fix_a.sql"])
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["done"] == ["fix_a.sql"]
    assert plan["new"] == ["fix_b.sql", "fix_c.sql"]


# ------------------------------- the collision refusal (D11 path 2)

def _twin_tmdl(tmp_path):
    """Two workspaces, one bare model name — the silent last-wins
    hazard the preflight must catch."""
    tmdl = tmp_path / "tmdl"
    for ws in ("WS Fix One", "WS Fix Two"):
        d = (tmdl / ws / "Fix Twin.SemanticModel" / "definition"
             / "tables")
        d.mkdir(parents=True)
        (d / "T.tmdl").write_text(
            "table T\n\n\tcolumn Fix Col\n"
            "\t\tsourceColumn: Fix Col\n\n"
            "\tpartition p1 = m\n\t\tmode: import\n\t\tsource =\n"
            '\t\t\tlet q = Value.NativeQuery(db,\n'
            '\t\t\t"EXEC rpt.USP_FIX_ONE") in q\n')
    return tmdl


def test_preflight_fails_on_bare_name_collision(tmp_path):
    tmdl = _twin_tmdl(tmp_path)
    sql = tmp_path / "sql"
    sql.mkdir()
    (sql / "USP_FIX_ONE.sql").write_text("SELECT 1\n")
    out = tmp_path / "out"
    out.mkdir()
    fails = sqldesc_cli.preflight(tmdl, sql, out)
    assert any("Fix Twin" in f for f in fails), fails


# =================================================================
# 0.7.0 — D14 THE SPLIT + THE STAMP + THE NAMING LAW (ruled
# 2026-10-08; pseudo APPROVED same day). RED until the code lands.
# Free paths only: build() makes no paid call; describe() is
# tested up to its refusals; its paid internals stay module-owned.
# =================================================================


def _tmdl_one(tmp_path):
    """One workspace, one model — a preflight-clean tmdl."""
    d = (tmp_path / "tmdl" / "Fix Model.SemanticModel" /
         "definition" / "tables")
    d.mkdir(parents=True)
    (d / "T.tmdl").write_text(
        "table T\n\n\tcolumn Fix Col\n"
        "\t\tsourceColumn: Fix Col\n\n"
        "\tpartition p1 = m\n\t\tmode: import\n\t\tsource =\n"
        '\t\t\tlet q = Value.NativeQuery(db,\n'
        '\t\t\t"EXEC rpt.FIX_A") in q\n')
    return tmp_path / "tmdl"


# --------------------------------------------- build(): the free door

def test_build_writes_stamp_and_no_paid_outputs(tmp_path,
                                                monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fix-dummy-key")
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    sqldesc_cli.build(tmdl, sql, out)
    stamp = out / STAMP
    assert stamp.exists()
    import json
    body = json.loads(stamp.read_text())
    assert set(body) >= {"corpus", "files"}
    assert body["files"] == 3
    assert (out / "05_semantic_graph").is_dir()
    assert not (out / "07_business_descriptions").exists()
    assert not (out / "12_ai_delivery_output.json").exists()
    assert not (out / LEDGER).exists()


def test_build_refuses_without_key(tmp_path, monkeypatch):
    """D4 amendment: the key is a BLOCKING row for every door —
    the sequence law, no degrade anywhere."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    try:
        sqldesc_cli.build(tmdl, sql, out)
        raise AssertionError("build ran without a key")
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    assert not (out / STAMP).exists()


# ------------------------------------------ describe(): the guard

def test_describe_without_build_refuses(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fix-dummy-key")
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    try:
        sqldesc_cli.describe(tmdl, sql, out)
        raise AssertionError("describe ran with no build stamp")
    except ValueError as exc:
        assert "run the build cell first" in str(exc)


def test_describe_stale_stamp_refuses_before_paying(tmp_path,
                                                    monkeypatch):
    """A changed corpus after build = refusal, ledger untouched —
    no paid call against a stale graph."""
    monkeypatch.setenv("OPENAI_API_KEY", "fix-dummy-key")
    sql, out = _corpus(tmp_path)
    tmdl = _tmdl_one(tmp_path)
    sqldesc_cli.build(tmdl, sql, out)
    (sql / "fix_b.sql").write_text("SELECT 99 -- drifted\n")
    try:
        sqldesc_cli.describe(tmdl, sql, out)
        raise AssertionError("describe ran against a stale build")
    except ValueError as exc:
        assert "run the build cell first" in str(exc)
    assert not (out / LEDGER).exists()


def test_describe_is_the_paid_door_signature(tmp_path):
    """The ruled names: describe() is the batch door (max_new,
    force); the old free txt door lives on as
    describe_technical() — the CLI bare mode unchanged."""
    import inspect
    params = inspect.signature(sqldesc_cli.describe).parameters
    assert "max_new" in params and "force" in params
    assert hasattr(sqldesc_cli, "describe_technical")


# ------------------------------------------- deliver(): the wrapper

def test_deliver_is_build_then_describe(tmp_path, monkeypatch):
    """Her ruling: deliver() survives as build + describe, nothing
    more. Structural: the two doors record their calls; no engine
    work, no seat, no cost."""
    calls = []
    monkeypatch.setattr(
        sqldesc_cli, "build",
        lambda *a, **k: calls.append(("build", k.get("dict_dir"))))
    monkeypatch.setattr(
        sqldesc_cli, "describe",
        lambda *a, **k: calls.append(("describe", k.get("max_new"))))
    sqldesc_cli.deliver("t", "s", "o", dict_dir=None, max_new=2)
    assert [c[0] for c in calls] == ["build", "describe"]
    assert calls[1][1] == 2


# ------------------------- the migration read (the 20-file ledger)

def test_old_ledger_name_still_counts_as_done(tmp_path):
    """The first tenant holds 10_corpus_ledger.json with paid
    files — the rename must NEVER cause a re-pay: the old name is
    read when the new one is absent."""
    import hashlib
    import json
    sql, out = _corpus(tmp_path)
    h = hashlib.sha256((sql / "fix_a.sql").read_bytes()).hexdigest()
    (out / LEDGER_OLD).write_text(
        json.dumps({"hashes": {"fix_a.sql": h}}))
    plan = sqldesc_cli.plan_corpus(sql, out)
    assert plan["done"] == ["fix_a.sql"]
    assert plan["new"] == ["fix_b.sql", "fix_c.sql"]


def test_record_writes_the_new_ledger_name(tmp_path):
    sql, out = _corpus(tmp_path)
    sqldesc_cli.record_corpus(sql, out, files=["fix_a.sql"])
    assert (out / LEDGER).exists()


def test_delivery_txt_renders_reportless_files_too(tmp_path):
    """Her find (2026-10-08, the view test): the human twin only
    rendered reports[] — a views-heavy corpus printed EMPTY while
    the json held everything. The twin renders BOTH sections."""
    delivery = {
        "reports": [{
            "report": "Fix Dashboard",
            "files": ["fix_a.sql"],
            "files_described": ["fix_a.sql"],
            "files_waiting": ["fix_b.sql"],
            "description": {"text": "Alpha fix text.",
                            "voice": "business",
                            "status": "gate_passed"},
            "terms": []}],
        "reportless_files": [{
            "file": "FIX_VIEW",
            "description": {"text": "Fix view text.",
                            "voice": "technical",
                            "status": "floor"},
            "terms": [{"bt_name": "Fix Term",
                       "bt_name_status": "proposed",
                       "business_description": "Fix card."}]}],
    }
    txt = sqldesc_cli._delivery_txt(delivery)
    assert "REPORT: Fix Dashboard" in txt
    assert "waiting: fix_b.sql" in txt
    assert "FILE: FIX_VIEW" in txt        # reportless rendered
    assert "no report ties to this file yet" in txt
    assert "Fix view text." in txt
    assert "TERM [proposed]: Fix Term" in txt
