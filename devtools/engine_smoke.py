"""Engine-path smoke harness — the MECHANIZED live-probe law (P0.4).

Sunny's no-whack-a-mole audit (2026-08-23): W12 was the SECOND op
shipped without a live probe through its real call path (1.51.3 was
the first; its lesson lived in a docstring and recurred). Lessons
don't enforce — mechanisms do. This harness exercises EVERY
ENGINE_TOOLS entry through the ACTUAL dispatch (_run_op — the same
function the turn loop calls) with catalog-realistic arguments
derived live from the store.

REQUIRED LEG before any ship that touches src/orchestrator/ops.py or
src/orchestrator/tools.py. The CI leg (tests/orchestrator/
test_engine_smoke_contract.py) checks the dispatch→op argument
mapping offline; THIS runs against the live store.

Acceptance at birth: run against the 2026-08-23 store, it FAILED on
the unfixed W12 bug (compare with two displayed catalog ids → "got
0") and passes after the fix — the compare_catalog_ids case below IS
that reproduction, permanent.

Usage: python3.11 devtools/engine_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.answer_evals import DATABASE, QUERY_URI  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402
from src.orchestrator.ops import COLUMN_COVERAGE_CAVEAT, OpsSession  # noqa: E402
from src.orchestrator.turn_engine import ENGINE_TOOLS, _run_op  # noqa: E402


def main() -> None:
    client = KustoClient(QUERY_URI, DATABASE,
                         az_cli_token_provider(QUERY_URI))
    run_kql = client.run
    run_kql("semantic_catalog | count", {})            # store preflight
    ops = OpsSession()
    failures: "list[str]" = []

    # -- realistic arguments, derived live --------------------------
    census = _run_op("census", {"kind": "metric"}, run_kql, ops)
    assert census.rows, "smoke: empty metric census — store problem"
    m0 = census.rows[0]
    m_name = str(m0.get("business_name") or m0.get("name"))
    two_ids = [str(r["id"]) for r in census.rows[:2]]
    tbl_rows = run_kql(
        "graph_edges | where edge_type == 'transform_to_technical' "
        "| take 1 | project target_id", {})
    table_name = (str(tbl_rows[0]["target_id"]).split(".")[-1]
                  if tbl_rows else "IP_SEPSIS")
    col_rows = run_kql(
        "graph_edges | where edge_type == 'decision_to_column' "
        "| take 1 | project target_id", {})
    col_name = (str(col_rows[0]["target_id"]).split(".")[-1]
                if col_rows else "PATIENTMRN")

    # -- one case per ENGINE_TOOLS entry, through the dispatch ------
    def check_census():
        assert census.rows, "0 rows"

    def check_search_exact():
        rs = _run_op("search", {"phrase": m_name, "mode": "exact"},
                     run_kql, ops)
        assert rs.rows, f"0 rows for real name {m_name!r}"

    def check_search_semantic():
        rs = _run_op("search", {"phrase": "sepsis screening",
                                "mode": "semantic"}, run_kql, ops)
        assert rs.rows, "0 rows"

    def check_retrieve():
        rs = _run_op("retrieve", {"ids": [two_ids[0]]}, run_kql, ops)
        assert rs.rows, f"0 rows for surfaced id {two_ids[0]!r}"

    def check_lineage_table():
        rs = _run_op("lineage", {"table": table_name}, run_kql, ops)
        assert rs.rows, f"0 rows for real table {table_name!r}"

    def check_lineage_column():
        rs = _run_op("lineage", {"column": col_name}, run_kql, ops)
        assert rs.rows or COLUMN_COVERAGE_CAVEAT in rs.note, (
            f"0 rows for {col_name!r} AND no coverage caveat stamped")

    def check_compare_catalog_ids():
        # THE W12 REPRODUCTION (permanent): two valid catalog ids,
        # surfaced this session, passed exactly as the engine passes
        # them. Red on the unfixed bug ("got 0"), green after.
        rs = _run_op("compare", {"refs": two_ids}, run_kql, ops)
        assert rs.rows, "0 rows"

    def check_compare_result_refs():
        rs = _run_op("compare", {"refs": ["R1"]}, run_kql, ops)
        assert rs.rows, "0 rows"

    def check_census_flag():
        # ADR 0054: a pre-sweep store legitimately lacks the table —
        # the op must fail with the NAMED remediation, never a raw
        # Kusto error; a post-sweep store must enumerate.
        from src.orchestrator.ops import OpError
        try:
            rs = _run_op("census", {"kind": "flag"}, run_kql, ops)
            print(f"       (flag surface live: {len(rs.rows)} flag(s))")
        except OpError as e:
            assert "320_red_flag_sweep" in str(e), (
                f"flag census failed WITHOUT the remediation: {e}")
            print("       (flag surface not in store yet — named "
                  "remediation verified)")

    cases = [
        ("census(kind=metric)", check_census),
        ("search(exact, real business name)", check_search_exact),
        ("search(semantic)", check_search_semantic),
        ("retrieve(surfaced metric id)", check_retrieve),
        ("lineage(table=real table)", check_lineage_table),
        ("lineage(column=real filtered column)", check_lineage_column),
        ("compare(two displayed CATALOG IDS — the W12 shape)",
         check_compare_catalog_ids),
        ("compare(result refs)", check_compare_result_refs),
        ("census(kind=flag — ADR 0054 surface or named remediation)",
         check_census_flag),
    ]
    for name, fn in cases:
        try:
            fn()
            print(f"[ok]   {name}")
        except Exception as e:                      # noqa: BLE001
            failures.append(f"{name}: {type(e).__name__}: {e}")
            print(f"[FAIL] {name}: {e}")

    declared = {t["function"]["name"] for t in ENGINE_TOOLS}
    exercised = {"census", "search", "retrieve", "lineage", "compare"}
    missing = declared - exercised
    if missing:
        failures.append(f"ENGINE_TOOLS entries with NO smoke case: "
                        f"{sorted(missing)} — add cases before ship")

    if failures:
        print(f"\n[X] engine smoke: {len(failures)} failure(s)")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("\nengine smoke: all tools green through the real dispatch")


if __name__ == "__main__":
    main()
