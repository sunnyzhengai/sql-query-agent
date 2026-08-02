"""Tests for the persistent error log (ops_error_log writer logic)."""

from src.governance.error_log import ErrorLog
from src.schemas import ERROR_LOG


def _log_with_history():
    log = ErrorLog()
    log.load_history([
        {
            "run_id": "2026-08-01T00:00:00",
            "run_timestamp": "2026-08-01T00:00:00",
            "metric_id": "reporting.USP_OLD_FAIL",
            "metric_name": "USP_OLD_FAIL",
            "error_type": "parse",
            "error_message": "boom",
            "status": "new",
        },
    ])
    log.set_previous_successes(["reporting.USP_WAS_OK"])
    log.start_run("2026-08-02T00:00:00")
    return log


def test_status_new_for_first_time_metric():
    log = _log_with_history()
    entry = log.record_error("reporting.USP_BRAND_NEW", "USP_BRAND_NEW", "parse", "err")
    assert entry.status == "new"


def test_status_known_for_repeat_failure():
    log = _log_with_history()
    entry = log.record_error("reporting.USP_OLD_FAIL", "USP_OLD_FAIL", "parse", "err")
    assert entry.status == "known"


def test_status_regressed_for_previously_passing_metric():
    log = _log_with_history()
    entry = log.record_error("reporting.USP_WAS_OK", "USP_WAS_OK", "parse", "err")
    assert entry.status == "regressed"


def test_finish_run_detects_resolutions():
    log = _log_with_history()
    # USP_OLD_FAIL does not fail this run -> resolved
    summary = log.finish_run(["reporting.USP_OLD_FAIL", "reporting.USP_WAS_OK"])
    assert summary["resolved"] == 1
    assert summary["resolved_metrics"] == ["reporting.USP_OLD_FAIL"]
    assert summary["total_errors"] == 0
    assert summary["success_rate"] == 100.0


def test_finish_run_counts_by_status():
    log = _log_with_history()
    log.record_error("reporting.USP_BRAND_NEW", "n", "parse", "e")
    log.record_error("reporting.USP_OLD_FAIL", "o", "parse", "e")
    log.record_error("reporting.USP_WAS_OK", "w", "parse", "e")
    summary = log.finish_run([
        "reporting.USP_BRAND_NEW", "reporting.USP_OLD_FAIL", "reporting.USP_WAS_OK",
    ])
    assert summary["new_errors"] == 1
    assert summary["known_errors"] == 1
    assert summary["regressions"] == 1
    assert "reporting.USP_WAS_OK" in summary["regressed_metrics"]


def test_error_message_and_preview_are_truncated():
    log = ErrorLog()
    log.start_run("r1")
    entry = log.record_error(
        "m", "m", "parse", "x" * 1000, clean_sql_preview="y" * 1000
    )
    assert len(entry.error_message) == 500
    assert len(entry.clean_sql_preview) == 300


def test_records_match_the_ops_error_log_contract():
    """Module output must align with the ERROR_LOG data contract."""
    log = ErrorLog()
    log.start_run("r1")
    log.record_error("m", "m", "parse", "err")
    record_keys = set(log.to_records()[0])
    contract_columns = {c[0] for c in ERROR_LOG["columns"]}
    assert record_keys == contract_columns


def test_stored_statuses_are_the_contract_vocabulary():
    """record_error can only produce the three stored statuses."""
    log = ErrorLog()
    log.start_run("r1")
    for mid in ("a", "b", "c"):
        log.record_error(mid, mid, "parse", "e")
    assert {e.status for e in log.current_run} <= {"new", "known", "regressed"}
