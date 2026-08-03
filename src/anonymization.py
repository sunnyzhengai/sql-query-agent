"""Crosswalk-based text anonymization — one home for the core engine.

Consumers: the anonymize_* CLI scripts (dev), the export_test_fixtures
utility notebook (records ScriptDom fixtures for offline testing), and —
future — ingestion-time PHI/hardcoded-value scanning.

The crosswalk (proprietary -> anonymized names) is DATA, supplied by the
caller; nothing org-specific is hardcoded here. Categories ending in "~ci"
match case-insensitively on word boundaries; "id:" categories use digit
boundaries so numeric IDs never match inside longer numbers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


def load_crosswalk(path: "str | Path") -> dict:
    with open(path) as f:
        return json.load(f)


def build_replacements(crosswalk: dict) -> "list[tuple[str, str, str]]":
    """Build ordered (pattern, replacement, category) tuples.

    Order matters — longer/more-specific patterns first to avoid partial
    matches (e.g., a prefixed database name before the bare vendor name).
    """
    replacements: "list[tuple[str, str, str]]" = []

    for orig, anon in crosswalk.get("vendor_functions", {}).items():
        replacements.append((orig, anon, "vendor_function"))

    for _key, entry in crosswalk.get("procedures", {}).items():
        if isinstance(entry, dict) and "original" in entry:
            replacements.append((entry["original"], entry["anonymized"], "procedure"))
            orig_bare = entry["original"].replace("[", "").replace("]", "")
            anon_bare = entry["anonymized"].replace("[", "").replace("]", "")
            if orig_bare != entry["original"]:
                replacements.append((orig_bare, anon_bare, "procedure_bare"))

    org_refs = crosswalk.get("org_references_to_remove", {})
    for orig, anon in org_refs.get("department_names", {}).items():
        replacements.append((orig, anon, "department_name"))
    for orig, anon in org_refs.get("file_paths", {}).items():
        replacements.append((orig, anon, "file_path"))
    for orig, anon in org_refs.get("report_paths", {}).items():
        replacements.append((orig, anon, "report_path"))

    for orig, anon in crosswalk.get("tables", {}).get("_org_specific_tables", {}).items():
        replacements.append((orig, anon, "org_table~ci"))
    for orig, anon in crosswalk.get("tables", {}).get("_emr_tables", {}).items():
        if orig != anon:
            replacements.append((orig, anon, "emr_table~ci"))

    for orig, anon in sorted(crosswalk.get("databases", {}).items(), key=lambda x: -len(x[0])):
        if orig != anon:
            replacements.append((orig, anon, "database"))
    for orig, anon in sorted(crosswalk.get("schemas", {}).items(), key=lambda x: -len(x[0])):
        if orig != anon:
            replacements.append((orig, anon, "schema"))
    for orig, anon in sorted(crosswalk.get("author_names", {}).items(), key=lambda x: -len(x[0])):
        replacements.append((orig, anon, "author"))
    for orig, anon in crosswalk.get("ticket_numbers", {}).items():
        replacements.append((orig, anon, "ticket"))

    for orig, anon in sorted(
        org_refs.get("string_literals", {}).items(), key=lambda x: -len(x[0])
    ):
        replacements.append((orig, anon, "string_literal"))
    for orig, anon in org_refs.get("grouper_name_prefixes", {}).items():
        replacements.append((orig, anon, "grouper_prefix"))
    for orig, anon in sorted(
        org_refs.get("prefix_patterns", {}).items(), key=lambda x: -len(x[0])
    ):
        replacements.append((orig, anon, "prefix_pattern"))

    for orig, anon in crosswalk.get("cook_fy_columns_to_rename", {}).items():
        replacements.append((orig, anon, "renamed_column"))
    for orig, anon in sorted(crosswalk.get("proc_codes", {}).items(), key=lambda x: -len(x[0])):
        replacements.append((orig, anon, "proc_code"))

    for id_category, mapping in crosswalk.get("hardcoded_ids", {}).items():
        if not isinstance(mapping, dict) or id_category.startswith("_"):
            continue
        for orig, anon in sorted(mapping.items(), key=lambda x: -len(x[0])):
            if orig != anon:
                replacements.append((orig, anon, f"id:{id_category}"))

    return replacements


def apply_replacements(
    text: str,
    replacements: "list[tuple[str, str, str]]",
    verbose: bool = False,
) -> "tuple[str, list[str]]":
    """Apply all replacements to text. Returns (anonymized_text, log_entries)."""
    log = []

    for orig, anon, category in replacements:
        use_ci = category.endswith("~ci")
        use_digit_boundary = category.startswith("id:")
        base_category = category.removesuffix("~ci")

        if use_ci:
            pattern = re.compile(r"\b" + re.escape(orig) + r"\b", re.IGNORECASE)
            matches = pattern.findall(text)
            if not matches:
                continue
            count = len(matches)
            text = pattern.sub(anon, text)
        elif use_digit_boundary:
            pattern = re.compile(r"(?<!\d)" + re.escape(orig) + r"(?!\d)")
            matches = pattern.findall(text)
            if not matches:
                continue
            count = len(matches)
            text = pattern.sub(anon, text)
        else:
            if orig not in text:
                continue
            count = text.count(orig)
            text = text.replace(orig, anon)

        entry = f"  [{base_category}] {orig!r} -> {anon!r} ({count}x)"
        log.append(entry)
        if verbose:
            print(entry)

    return text, log


def scan_for_missed(text: str, forbidden_terms: "Iterable[str]") -> "list[str]":
    """Check anonymized text for remaining proprietary terms.

    forbidden_terms is caller-supplied (crosswalk `_scan_terms` or a local
    list) — nothing org-specific lives in this module.
    """
    warnings = []
    for term in forbidden_terms:
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            context = text[start:end].replace("\n", " ").strip()
            warnings.append(f"  MISSED: '{term}' found in: ...{context}...")
    return warnings


def get_scan_terms(crosswalk: dict, fallback: "Iterable[str]" = ()) -> "list[str]":
    """Forbidden-term list for scan_for_missed, from the crosswalk if present."""
    return list(crosswalk.get("_scan_terms", fallback))


def anonymize_record(
    record: dict,
    replacements: "list[tuple[str, str, str]]",
) -> "tuple[dict, list[str]]":
    """Anonymize every string in a row dict (nested JSON strings included)
    by round-tripping through its JSON form. Returns (record, log)."""
    text = json.dumps(record, sort_keys=True)
    text, log = apply_replacements(text, replacements)
    return json.loads(text), log
