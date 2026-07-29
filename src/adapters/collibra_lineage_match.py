"""Match stored procedures and views to Power BI reports in Collibra.

Naming conventions:
    Views:  V_CCHP_SomeReport_PBI    → extract "SomeReport"
    Procs:  USP_CCHP_Some_Report_PBI → extract "Some_Report"

The _PBI suffix signals the object feeds a Power BI report.
The first segment after V_ or USP_ is the company prefix (e.g., CCHP)
and is stripped. The remaining middle segments are fuzzy-matched against
Power BI report names in Collibra.

Usage:
    from src.adapters.collibra_lineage_match import CollibraLineageMatcher
    matcher = CollibraLineageMatcher(collibra_client)
    matches = matcher.match_all()
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.adapters.collibra_lineage import CollibraClient

logger = logging.getLogger(__name__)

PBI_REPORT_TYPE_ID = "00000000-0000-0000-0000-100000000006"


@dataclass
class LineageMatch:
    """A matched proc/view → PBI report pair."""
    object_name: str          # original proc or view name
    object_type: str          # "VIEW" or "SQL_STORED_PROCEDURE"
    extracted_key: str        # the middle part used for matching
    report_name: str          # matched Collibra PBI report name
    report_asset_id: str      # Collibra asset ID of the report
    score: float = 0.0        # match confidence (0-1)


@dataclass
class LineageMatchResult:
    """Aggregate result of lineage matching."""
    matched: list[LineageMatch] = field(default_factory=list)
    unmatched_objects: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Matched: {len(self.matched)} | "
            f"Unmatched: {len(self.unmatched_objects)}"
        )


def extract_match_key(object_name: str) -> str | None:
    """Extract the matchable middle part from a _PBI-suffixed object name.

    Examples:
        V_CCHP_SomeReport_PBI          → "somereport"
        V_CCHP_Some_Report_Name_PBI    → "some report name"
        USP_CCHP_Some_Report_PBI       → "some report"
        USP_COOK_ED_Sepsis_PBI         → "ed sepsis"
        V_CCHP_340B_Charges_PBI        → "340b charges"
        SomeOtherProc                  → None (no _PBI suffix)

    Returns:
        Normalized match key (lowercase, underscores→spaces), or None if
        the name doesn't end with _PBI.
    """
    name = object_name.strip()

    # Must end with _PBI (case-insensitive)
    if not re.search(r"_PBI$", name, re.IGNORECASE):
        return None

    # Strip the _PBI suffix
    name = re.sub(r"_PBI$", "", name, flags=re.IGNORECASE)

    # Strip leading V_ or USP_ prefix
    name = re.sub(r"^(V|USP)_", "", name, flags=re.IGNORECASE)

    # Strip the company prefix (first segment — e.g., CCHP, COOK, etc.)
    parts = name.split("_", 1)
    if len(parts) > 1:
        name = parts[1]
    else:
        # Single word left after stripping — use it as-is
        name = parts[0]

    # Normalize: lowercase, underscores to spaces, collapse whitespace
    key = name.lower().replace("_", " ").strip()
    key = re.sub(r"\s+", " ", key)

    return key if key else None


def normalize_report_name(report_name: str) -> str:
    """Normalize a Collibra PBI report name for fuzzy comparison.

    Collibra report names may include bracket-prefixed workspace/report IDs:
        [433bbb97-...] 340B Eligible Charges [667ad212-...]
    Strip those brackets and normalize.
    """
    # Remove bracketed UUIDs
    clean = re.sub(r"\[[0-9a-f-]+\]\s*", "", report_name, flags=re.IGNORECASE)
    # Lowercase, collapse whitespace
    clean = clean.lower().strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean


def fuzzy_match_score(key: str, report_name_normalized: str) -> float:
    """Score how well a proc/view key matches a PBI report name.

    Strategy:
    - Split both into word tokens
    - Count how many key tokens appear in the report name
    - Score = fraction of key tokens found

    Returns:
        Float 0.0-1.0. Higher is better.
    """
    key_tokens = key.split()
    report_tokens = report_name_normalized.split()

    if not key_tokens:
        return 0.0

    # Check each key token against report tokens
    matched_tokens = 0
    for kt in key_tokens:
        # Allow partial match — key token is substring of any report token
        # or report token is substring of key token
        for rt in report_tokens:
            if kt in rt or rt in kt:
                matched_tokens += 1
                break

    return matched_tokens / len(key_tokens)


class CollibraLineageMatcher:
    """Match _PBI-suffixed procs/views to Power BI reports in Collibra.

    Args:
        client: Authenticated CollibraClient instance.
        min_score: Minimum fuzzy match score to accept (0-1). Default 0.5.
    """

    def __init__(self, client: CollibraClient, min_score: float = 0.5) -> None:
        self.client = client
        self.min_score = min_score
        self._report_cache: list[dict] | None = None

    def _load_reports(self, limit: int = 1000) -> list[dict]:
        """Fetch all Power BI Report assets from Collibra."""
        if self._report_cache is not None:
            return self._report_cache

        all_reports = []
        offset = 0
        batch_size = 100

        while offset < limit:
            result = self.client._get("assets", params={
                "typeId": PBI_REPORT_TYPE_ID,
                "offset": offset,
                "limit": batch_size,
            })
            batch = result.get("results", [])
            if not batch:
                break
            all_reports.extend(batch)
            offset += len(batch)

        logger.info("Loaded %d Power BI Report assets from Collibra", len(all_reports))
        self._report_cache = all_reports
        return all_reports

    def match_object(self, object_name: str, object_type: str = "VIEW") -> LineageMatch | None:
        """Match a single proc/view name to a PBI report.

        Args:
            object_name: The proc/view name (e.g., V_CCHP_SomeReport_PBI).
            object_type: "VIEW" or "SQL_STORED_PROCEDURE".

        Returns:
            LineageMatch if a match is found above min_score, else None.
        """
        key = extract_match_key(object_name)
        if key is None:
            return None

        reports = self._load_reports()

        best_match = None
        best_score = 0.0

        for report in reports:
            report_name = report.get("name", "")
            normalized = normalize_report_name(report_name)

            score = fuzzy_match_score(key, normalized)
            if score > best_score:
                best_score = score
                best_match = report

        if best_match and best_score >= self.min_score:
            return LineageMatch(
                object_name=object_name,
                object_type=object_type,
                extracted_key=key,
                report_name=best_match["name"],
                report_asset_id=best_match["id"],
                score=best_score,
            )

        return None

    def match_objects(
        self,
        objects: list[dict[str, str]],
    ) -> LineageMatchResult:
        """Match a list of procs/views to PBI reports.

        Args:
            objects: List of dicts with 'object_name' and 'object_type' keys.
                     Only _PBI-suffixed names are considered.

        Returns:
            LineageMatchResult with matched and unmatched lists.
        """
        result = LineageMatchResult()

        for obj in objects:
            name = obj["object_name"]
            obj_type = obj.get("object_type", "VIEW")

            match = self.match_object(name, obj_type)
            if match:
                result.matched.append(match)
                logger.info(
                    "Matched %s → %s (score=%.2f, key='%s')",
                    name, match.report_name, match.score, match.extracted_key,
                )
            elif extract_match_key(name) is not None:
                # Had _PBI suffix but no match found
                result.unmatched_objects.append(name)
                logger.warning(
                    "No match for %s (key='%s')",
                    name, extract_match_key(name),
                )
            # Objects without _PBI suffix are silently skipped

        return result
