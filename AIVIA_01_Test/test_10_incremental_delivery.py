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

LEDGER = "10_corpus_ledger.json"


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
