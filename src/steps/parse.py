"""Step 02: parse SQL sources into structural extractions.

Logic relations asserted here:
- Every source produces exactly one outcome: a parse result or an error.
- Success and error sets are disjoint and together cover all sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from src.governance.error_log import ErrorLog
from src.graph.serialization import parsed_sql_to_parse_result_row
from src.parser.error_classifier import classify_parse_error


@dataclass
class ParseStepOutput:
    parse_results: "list[dict]"          # ops_parse_results rows
    parse_errors: "list[dict]"           # ops_parse_errors rows
    parse_successes: "list[dict]"        # ops_parse_successes rows
    error_log: ErrorLog                  # append error_log.to_records() to ops_error_log
    run_summary: "dict[str, Any]" = field(default_factory=dict)


def parse_step(
    sql_sources: "list[dict]",
    parse_fn: Callable[[str], Any],
    previous_error_records: "Iterable[dict]" = (),
    previous_success_ids: "Iterable[str]" = (),
    run_id: str = "",
    progress: "Callable[[int, int], None] | None" = None,
) -> ParseStepOutput:
    """Parse every SQL source with parse_fn (ScriptDom on Fabric, sqlglot
    fallback locally). Pure: no I/O — the caller supplies previous-run state
    for regression detection and persists the outputs."""
    error_log = ErrorLog()
    error_log.load_history(list(previous_error_records))
    error_log.set_previous_successes(list(previous_success_ids))
    error_log.start_run(run_id)

    parse_results: "list[dict]" = []
    parse_errors: "list[dict]" = []
    parse_successes: "list[dict]" = []

    for i, source in enumerate(sql_sources):
        metric_id, name, sql = source["metric_id"], source["name"], source["sql"]
        line_count = sql.count("\n") + 1
        try:
            parsed = parse_fn(sql)
            parse_results.append(
                parsed_sql_to_parse_result_row(metric_id, name, parsed, line_count=line_count)
            )
            parse_successes.append({
                "metric_id": metric_id,
                "name": name,
                "cte_count": len(parsed.ctes),
                "table_count": len(parsed.final_select_tables),
                "line_count": line_count,
            })
        except Exception as e:  # noqa: BLE001 — every failure becomes a classified row
            classification = classify_parse_error(str(e), metric_id, line_count)
            parse_errors.append({
                "metric_id": metric_id,
                "name": name,
                "error": str(e)[:200],
                "error_category": classification["error_category"],
                "user_explanation": classification["user_explanation"],
                "suggested_action": classification["suggested_action"],
                "line_count": line_count,
            })
            error_log.record_error(
                metric_id=metric_id, metric_name=name, error_type="parse",
                error_message=str(e), line_count=line_count,
            )
        if progress:
            progress(i + 1, len(sql_sources))

    run_summary = error_log.finish_run([s["metric_id"] for s in sql_sources])

    # Logic relations: one outcome per source, disjoint, covering.
    ok_ids = {r["metric_id"] for r in parse_results}
    err_ids = {r["metric_id"] for r in parse_errors}
    src_ids = {s["metric_id"] for s in sql_sources}
    assert len(parse_results) + len(parse_errors) == len(sql_sources), (
        f"parse_step: {len(sql_sources)} sources -> "
        f"{len(parse_results)} results + {len(parse_errors)} errors"
    )
    assert ok_ids.isdisjoint(err_ids), f"parse_step: overlap {ok_ids & err_ids}"
    assert ok_ids | err_ids == src_ids, (
        f"parse_step: unaccounted sources {src_ids - ok_ids - err_ids}"
    )
    assert {r["metric_id"] for r in parse_successes} == ok_ids

    return ParseStepOutput(parse_results, parse_errors, parse_successes, error_log, run_summary)
