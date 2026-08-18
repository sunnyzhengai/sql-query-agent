"""Publishing-side ASSET MATCHING: find the Collibra asset for a report.

Identity correction (2026-08-16): despite the filename, this is NOT
lineage — lineage is deterministic and comes from TMDL partition parsing
(ADR 0040). This module answers a publishing question: given a proc/view
we hold a description for, WHICH Collibra Power BI Report asset should
the description be written onto?

Two matching tiers, best first:

1. EXACT report name — when input_metric_names (12_ingest_semantic_models)
   recorded the actual TMDL-derived report for the metric, match the
   Collibra asset by that name, case-insensitively. Deterministic;
   score 1.0.
2. _PBI-suffix heuristic (legacy fallback) — V_ACME_SomeReport_PBI /
   USP_ACME_Some_Report_PBI: strip prefix + company segment + suffix,
   fuzzy-match the middle against Collibra report names. Only names
   ending in _PBI are considered; min_score gates acceptance.

Usage:
    from src.adapters.collibra_lineage_match import CollibraLineageMatcher
    matcher = CollibraLineageMatcher(collibra_client)
    result = matcher.match_objects(objects, known_report_names=names)
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
        V_ACME_SomeReport_PBI          → "somereport"
        V_ACME_Some_Report_Name_PBI    → "some report name"
        USP_ACME_Some_Report_PBI       → "some report"
        USP_ACME_ED_Sepsis_PBI         → "ed sepsis"
        V_ACME_340B_Charges_PBI        → "340b charges"
        SomeOtherProc                  → None (no _PBI suffix)

    Returns:
        Normalized match key (lowercase, underscores→spaces), or None if
        the name doesn't end with _PBI.
    """
    # metric_ids are schema-qualified since the 00b identity fix
    # (2026-08-17): key on the BARE object name (ADR 0020 bareName) —
    # qualified input once produced junk keys and 128 unmatched reports
    # plus garbage 1.00 fuzzy matches (field failure 2026-08-18).
    name = object_name.strip().rsplit(".", 1)[-1]

    # Must end with _PBI (case-insensitive)
    if not re.search(r"_PBI$", name, re.IGNORECASE):
        return None

    # Strip the _PBI suffix
    name = re.sub(r"_PBI$", "", name, flags=re.IGNORECASE)

    # Strip leading V_ or USP_ prefix
    name = re.sub(r"^(V|USP)_", "", name, flags=re.IGNORECASE)

    # Strip the company prefix (first segment — e.g., ACME, COOK, etc.)
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

    # Check each key token against report tokens. Substring matching is
    # restricted to tokens of length >= 3: one- and two-character junk
    # tokens ("a", "of") are substrings of nearly everything and once
    # produced 1.00 scores for unrelated names (field failure
    # 2026-08-18). Short tokens must match exactly.
    matched_tokens = 0
    for kt in key_tokens:
        for rt in report_tokens:
            if kt == rt:
                matched_tokens += 1
                break
            if len(kt) >= 3 and len(rt) >= 3 and (kt in rt or rt in kt):
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

    def match_object(
        self, object_name: str, object_type: str = "VIEW",
        exact_report_name: "str | None" = None,
    ) -> LineageMatch | None:
        """Match a single proc/view name to a Collibra PBI Report asset.

        Args:
            object_name: The proc/view name (e.g., V_ACME_SomeReport_PBI).
            object_type: "VIEW" or "SQL_STORED_PROCEDURE".
            exact_report_name: The TMDL-derived report name for this
                object (from input_metric_names), when known. Matched
                exactly (case-insensitive), score 1.0 — the heuristic
                never runs.

        Returns:
            LineageMatch if a match is found above min_score, else None.
        """
        if exact_report_name:
            wanted = exact_report_name.strip().lower()
            for report in self._load_reports():
                if report.get("name", "").strip().lower() == wanted:
                    return LineageMatch(
                        object_name=object_name,
                        object_type=object_type,
                        extracted_key=exact_report_name,
                        report_name=report["name"],
                        report_asset_id=report["id"],
                        score=1.0,
                    )
            # A recorded exact name that is absent from Collibra is a
            # real answer (asset not synced yet) — do NOT fall through
            # to fuzzy guessing against a known-correct name.
            return None

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
        known_report_names: "dict[str, str] | None" = None,
    ) -> LineageMatchResult:
        """Match a list of procs/views to Collibra PBI Report assets.

        Args:
            objects: List of dicts with 'object_name' and 'object_type' keys.
                     Without a known name, only _PBI-suffixed names are
                     considered (legacy heuristic).
            known_report_names: object_name (case-insensitive) -> exact
                     TMDL-derived report name, typically built from
                     input_metric_names. Objects present here match
                     exactly and skip the heuristic entirely.

        Returns:
            LineageMatchResult with matched and unmatched lists.
        """
        result = LineageMatchResult()
        known = {k.lower(): v for k, v in (known_report_names or {}).items()}

        for obj in objects:
            name = obj["object_name"]
            obj_type = obj.get("object_type", "VIEW")

            match = self.match_object(
                name, obj_type, exact_report_name=known.get(name.lower())
            )
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
