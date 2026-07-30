"""
Automated acceptance test for deployment validation.

Verifies the deployment is complete and functional by checking:
1. Delta table integrity — all required tables exist with rows
2. metric_logic completeness — calculation_logic and source_tables populated
3. Dictionary coverage — SQL table refs found in dict_tables
4. Parse error review — flags unexpected error signatures
5. Agent smoke test — (placeholder) fires test questions via Fabric API

Usage:
    # In a Fabric notebook cell:
    %run scripts/acceptance_test

    # Or import and call:
    from scripts.acceptance_test import run_acceptance_test
    results = run_acceptance_test(spark)
"""

from __future__ import annotations


# Required Delta tables and their minimum expected row counts
REQUIRED_TABLES = {
    "input_sql_sources": 1,
    "input_dict_tables": 1,
    "input_dict_columns": 1,
    "ops_parse_results": 0,      # may be 0 if all procs fail (caught by other checks)
    "ops_parse_successes": 1,
    "ops_parse_errors": 0,        # 0 errors is fine
    "graph_nodes": 1,
    "graph_edges": 1,
    "output_metric_logic": 1,
    "ops_pipeline_validation": 1,
    "ops_build_summary": 1,
}

# Deployment thresholds
THRESHOLDS = {
    "calculation_logic_populated": 0.80,  # >80% of metrics have non-null logic
    "source_tables_populated": 0.70,       # >70% of metrics have non-null tables
    "dictionary_coverage": 0.90,           # >90% of SQL tables found in dict
}


class AcceptanceResult:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, name: str, passed: bool, blocking: bool, detail: str):
        self.checks.append({
            "name": name,
            "passed": passed,
            "blocking": blocking,
            "detail": detail,
        })

    @property
    def all_passed(self) -> bool:
        return all(c["passed"] for c in self.checks if c["blocking"])

    @property
    def blocking_failures(self) -> list[dict]:
        return [c for c in self.checks if not c["passed"] and c["blocking"]]

    @property
    def warnings(self) -> list[dict]:
        return [c for c in self.checks if not c["passed"] and not c["blocking"]]

    def print_report(self):
        print(f"\n{'=' * 60}")
        print(f"ACCEPTANCE TEST RESULTS")
        print(f"{'=' * 60}")

        passed = sum(1 for c in self.checks if c["passed"])
        failed = sum(1 for c in self.checks if not c["passed"])
        print(f"  Passed: {passed}/{len(self.checks)}")
        print(f"  Failed: {failed}/{len(self.checks)}")

        for c in self.checks:
            symbol = "+" if c["passed"] else ("X" if c["blocking"] else "!")
            status = "PASS" if c["passed"] else ("FAIL" if c["blocking"] else "WARN")
            print(f"  [{symbol}] {c['name']}: {status} — {c['detail']}")

        if self.blocking_failures:
            print(f"\n  >>> ACCEPTANCE FAILED — {len(self.blocking_failures)} blocking issue(s) <<<")
        elif self.warnings:
            print(f"\n  >>> ACCEPTANCE PASSED with {len(self.warnings)} warning(s) <<<")
        else:
            print(f"\n  >>> ACCEPTANCE PASSED — all checks green <<<")


def run_acceptance_test(spark) -> AcceptanceResult:
    """Run all acceptance checks. Pass the Spark session from the notebook."""
    result = AcceptanceResult()

    # --- Check 1: Delta table integrity ---
    for table_name, min_rows in REQUIRED_TABLES.items():
        try:
            count = spark.table(table_name).count()
            if count >= min_rows:
                result.add(
                    f"table:{table_name}",
                    passed=True, blocking=True,
                    detail=f"{count} rows",
                )
            else:
                result.add(
                    f"table:{table_name}",
                    passed=False, blocking=True,
                    detail=f"{count} rows (minimum: {min_rows})",
                )
        except Exception as e:
            result.add(
                f"table:{table_name}",
                passed=False, blocking=True,
                detail=f"Table not found: {e}",
            )

    # --- Check 2: metric_logic completeness ---
    try:
        ml_df = spark.table("output_metric_logic")
        total = ml_df.count()
        if total == 0:
            result.add(
                "metric_logic:completeness",
                passed=False, blocking=True,
                detail="metric_logic is empty",
            )
        else:
            with_logic = ml_df.filter("calculation_logic IS NOT NULL AND calculation_logic != ''").count()
            with_tables = ml_df.filter("source_tables IS NOT NULL AND source_tables != ''").count()

            logic_pct = with_logic / total
            tables_pct = with_tables / total

            result.add(
                "metric_logic:calculation_logic",
                passed=logic_pct >= THRESHOLDS["calculation_logic_populated"],
                blocking=True,
                detail=f"{with_logic}/{total} ({logic_pct:.0%}) have calculation logic (threshold: {THRESHOLDS['calculation_logic_populated']:.0%})",
            )
            result.add(
                "metric_logic:source_tables",
                passed=tables_pct >= THRESHOLDS["source_tables_populated"],
                blocking=False,  # warning, not blocking
                detail=f"{with_tables}/{total} ({tables_pct:.0%}) have source tables (threshold: {THRESHOLDS['source_tables_populated']:.0%})",
            )
    except Exception as e:
        result.add(
            "metric_logic:completeness",
            passed=False, blocking=True,
            detail=f"Cannot read metric_logic: {e}",
        )

    # --- Check 3: Dictionary coverage ---
    try:
        dict_tables = set(
            r["TABLE_NAME"].upper()
            for r in spark.table("input_dict_tables").collect()
        )
        # Get unique table names from graph_nodes (technical layer)
        import json as _json
        sql_tables = set()
        for r in spark.table("graph_nodes").filter("layer = 'technical'").collect():
            rd = r.asDict()
            props = rd.get("properties", "{}")
            if isinstance(props, str):
                props = _json.loads(props)
            tname = props.get("table", "")
            if tname and not props.get("column"):  # table nodes, not column nodes
                sql_tables.add(tname.upper())

        if sql_tables:
            covered = len(sql_tables & dict_tables)
            coverage = covered / len(sql_tables)
            missing = sql_tables - dict_tables
            missing_sample = sorted(missing)[:5]

            result.add(
                "dictionary:coverage",
                passed=coverage >= THRESHOLDS["dictionary_coverage"],
                blocking=True,
                detail=f"{covered}/{len(sql_tables)} ({coverage:.0%}) SQL tables found in dictionary (threshold: {THRESHOLDS['dictionary_coverage']:.0%})"
                + (f". Missing: {', '.join(missing_sample)}{'...' if len(missing) > 5 else ''}" if missing else ""),
            )
        else:
            result.add(
                "dictionary:coverage",
                passed=True, blocking=True,
                detail="No technical table nodes found (skipped)",
            )
    except Exception as e:
        result.add(
            "dictionary:coverage",
            passed=False, blocking=True,
            detail=f"Cannot check dictionary coverage: {e}",
        )

    # --- Check 4: Parse error review ---
    try:
        parse_errors = spark.table("ops_parse_errors")
        error_count = parse_errors.count()
        parse_successes = spark.table("ops_parse_successes")
        success_count = parse_successes.count()

        total_parsed = error_count + success_count
        if total_parsed > 0:
            error_rate = error_count / total_parsed
            result.add(
                "parse:error_rate",
                passed=error_rate <= 0.10,  # <10% error rate
                blocking=True,
                detail=f"{error_count} errors out of {total_parsed} ({error_rate:.0%} error rate)",
            )
        else:
            result.add(
                "parse:error_rate",
                passed=False, blocking=True,
                detail="No parse results found",
            )
    except Exception as e:
        result.add(
            "parse:error_rate",
            passed=False, blocking=True,
            detail=f"Cannot read parse tables: {e}",
        )

    # --- Check 5: Agent smoke test (placeholder) ---
    # This requires Fabric REST API access and a running Data Agent.
    # For now, document the test but don't execute it automatically.
    result.add(
        "agent:smoke_test",
        passed=True, blocking=False,
        detail="Placeholder — run golden path tests manually in Phase 5.3 or via Fabric REST API",
    )

    result.print_report()
    return result
