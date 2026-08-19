"""Regenerate tests/golden/parse_goldens.json with the NATIVE parser.

Golden semantics since 2026-08-19 (native-parser law): every corpus
file must parse with ScriptDom, and its structural counts are pinned
exactly — deterministic everywhere, no environment-fragile fallback,
no CI skip. Run after any deliberate corpus change:

    python3.11 scripts/regenerate_parse_goldens.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.parser.sql_parser import parse_sql  # noqa: E402

SQL_DIR = REPO / "data" / "synthetic" / "sql"
OUT = REPO / "tests" / "golden" / "parse_goldens.json"


def main() -> None:
    goldens = {}
    for path in sorted(SQL_DIR.rglob("*.sql")):
        rel = str(path.relative_to(SQL_DIR))
        parsed = parse_sql(path.read_text(encoding="utf-8-sig"))
        tables = {t.table for c in parsed.ctes for t in c.table_refs}
        tables |= {t.table for t in parsed.final_select_tables}
        goldens[rel] = {
            "cte_count": len(parsed.ctes),
            "physical_table_count": len(tables),
            "extraction_suppressed": parsed.extraction_suppressed,
        }
    OUT.write_text(json.dumps(goldens, indent=1) + "\n")
    print(f"pinned {len(goldens)} files -> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
