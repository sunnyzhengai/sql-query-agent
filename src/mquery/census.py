"""Shape census: total classification of partition files, file grain.

Runs as 12's pre-step and standalone (install-time / pre-sales). Cheap,
read-only, requires NO successful parsing — every file lands in exactly
one bucket, and the coverage report states up front what a harvest will
and won't extract (no more silent partial harvests).

Grain is per FILE (report_name, pbi_table) — amendment 3: report-level
membership masks per-file failures inside otherwise-parsed reports.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from src.mquery.registry import classify_shape
from src.mquery.signature import partition_shape

# The same partition-block grammar the extractor uses (kept in sync by
# the census-vs-extractor CI fixtures, not by copy-paste review).
_M_PARTITION = re.compile(
    r"partition\s+[^\n]+=\s*m\s*\n"
    r"\s+mode:\s*\w+\s*\n"
    r"\s+source\s*=\s*\n(.*?)(?=\n\s*\n|\n\s+annotation|\Z)",
    re.DOTALL,
)
_ENTITY_PARTITION = re.compile(r"partition\s+[^\n]+=\s*entity\b")
_CALCULATED_PARTITION = re.compile(r"partition\s+[^\n]+=\s*calculated\b")


@dataclass
class CensusRow:
    report_name: str
    pbi_table: str
    family: str
    signature: str
    shape: str
    status: str  # supported | recognized_unsupported | unknown


def census_file(report_name: str, pbi_table: str, content: str) -> CensusRow:
    if _CALCULATED_PARTITION.search(content):
        return CensusRow(report_name, pbi_table, "calculated", "calculated",
                         "calculated_table", "recognized_unsupported")
    m = _M_PARTITION.search(content)
    if not m:
        if _ENTITY_PARTITION.search(content):
            return CensusRow(report_name, pbi_table, "directlake",
                             "entity", "directlake_entity", "supported")
        return CensusRow(report_name, pbi_table, "none", "no_partition",
                         "no_partition", "recognized_unsupported")
    family, signature, arg_kinds = partition_shape(m.group(1).strip())
    shape, status = classify_shape(family, signature, arg_kinds)
    return CensusRow(report_name, pbi_table, family, signature, shape, status)


def census_files(tmdl_files: "Iterable") -> "list[CensusRow]":
    return [census_file(f.report_name, f.table_name, f.content)
            for f in tmdl_files]


def coverage_lines(rows: "list[CensusRow]") -> "list[str]":
    """The install-time coverage statement: N sources — X% supported,
    Y% recognized non-SQL (listed), Z% unknown (signatures attached)."""
    total = len(rows)
    if not total:
        return ["shape census: no partition files collected"]
    by_status = Counter(r.status for r in rows)
    sup = by_status.get("supported", 0)
    rec = by_status.get("recognized_unsupported", 0)
    unk = by_status.get("unknown", 0)
    lines = [
        f"shape census: {total} partition files — "
        f"{sup} supported ({100 * sup // total}%), "
        f"{rec} recognized non-SQL ({100 * rec // total}%), "
        f"{unk} unknown ({100 * unk // total}%)",
    ]
    shape_counts = Counter(r.shape for r in rows)
    for shape, n in shape_counts.most_common():
        lines.append(f"  {shape}: {n}")
    unknown_sigs = Counter(r.signature for r in rows if r.status == "unknown")
    if unknown_sigs:
        lines.append("  unknown signatures (safe to send to support — "
                     "whitelist-anonymized):")
        for sig, n in unknown_sigs.most_common(10):
            lines.append(f"    {n}x {sig}")
    return lines
