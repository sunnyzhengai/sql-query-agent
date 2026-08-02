"""SQL object identity extraction — the source of metric_id.

Contract (input_sql_sources): metric_id = "<schema>.<name>", derived from the
CREATE/ALTER statement inside the SQL text — never from the filename. Two
files with the same name in different schemas are distinct metrics; two
definitions of the same schema.name are a collision the installer must
reject (unique(metric_id) invariant, and ADR 0005: refuse over guess).

Also owns entry-point normalization: SQL text is normalized to \\n line
endings HERE, at ingestion, so no downstream code ever sees \\r\\n.
"""

from __future__ import annotations

import re

# CREATE [OR ALTER] PROCEDURE|VIEW [schema].[name] — brackets optional,
# whitespace around the dot tolerated, case-insensitive.
_QUALIFIED = re.compile(
    r"(?:CREATE|ALTER)\s+(?:OR\s+ALTER\s+)?(PROCEDURE|VIEW)\s+"
    r"\[?(\w+)\]?\s*\.\s*\[?(\w+)\]?",
    re.IGNORECASE,
)
_UNQUALIFIED = re.compile(
    r"(?:CREATE|ALTER)\s+(?:OR\s+ALTER\s+)?(PROCEDURE|VIEW)\s+\[?(\w+)\]?",
    re.IGNORECASE,
)


def normalize_sql_text(text: str) -> str:
    """Normalize line endings at the entry point (contract: sql uses \\n)."""
    return text.replace("\r\n", "\n")


def fold_identifier(identifier: str) -> str:
    """Case-fold an identifier for matching (ADR 0016).

    SQL Server's default collation is case-insensitive, and Oracle/Snowflake
    fold unquoted identifiers to uppercase — so UPPER is the canonical match
    form. Stored/display values keep their original case; only match keys
    and node IDs are folded.
    """
    return identifier.upper()


def extract_object_identity(sql: str) -> "tuple[str | None, str | None, str | None]":
    """Extract (schema, name, source_type) from a SQL object definition.

    source_type is "procedure" or "view". Objects without a schema default
    to "dbo", matching SQL Server resolution. Returns (None, None, None)
    when no CREATE/ALTER PROCEDURE|VIEW statement is found.
    """
    m = _QUALIFIED.search(sql)
    if m:
        return m.group(2), m.group(3), m.group(1).lower()
    m = _UNQUALIFIED.search(sql)
    if m:
        return "dbo", m.group(2), m.group(1).lower()
    return None, None, None


def find_duplicate_identities(
    identities: "list[tuple[str, str]]",
) -> "dict[str, list[str]]":
    """Given (identity, label) pairs, return {folded_identity: [labels]} for
    every identity defined more than once. Comparison is case-insensitive
    (fold_identifier), mirroring SQL Server collation semantics."""
    by_id: "dict[str, list[str]]" = {}
    for identity, label in identities:
        by_id.setdefault(fold_identifier(identity), []).append(label)
    return {mid: labels for mid, labels in by_id.items() if len(labels) > 1}
