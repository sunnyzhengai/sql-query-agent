"""Search-index refresh: Eventhouse copy + full re-embed (notebook 11).

Productizes the manual refresh flow of devtools/eventhouse_setup.kql
(that script remains the ONE-TIME setup: table DDL, encoding policy,
semantic_search function). This module is the every-run path: whenever
descriptions change, the search documents change, and the embeddings
must be recomputed — or search keeps ranking on stale vectors (live
find 2026-08-13: a 03+07 rerun left the catalog embedded from Aug 9).

Pure command composition plus an injected runner (KustoClient.mgmt /
.run), so tests run offline and the notebook stays thin.
"""

from __future__ import annotations

from typing import Callable

# Columns matched BY NAME (positional copy bit us live 2026-08-09:
# Spark writes dict-rows alphabetically and set-or-replace maps by
# position — 441 embeddings were computed over the wrong column).
# Every emb nulled — that is what forces the full re-embed below.
COPY_COMMAND = (
    ".set-or-replace semantic_catalog <| output_semantic_catalog\n"
    "| project node_id, ['kind'], ['ref'], name, business_name,\n"
    "          search_text, display_text, emb = dynamic(null)"
)

COVERAGE_QUERY = (
    "semantic_catalog | where isnull(emb) or array_length(emb) == 0 "
    "| count"
)

ROWCOUNT_QUERY = "semantic_catalog | count"

# Calibrated adversarial phrase from eventhouse_setup.kql section 4 —
# contains a domain word yet must clear NO threshold (ADR 0005's
# refusal floor in fuzzy form). Nonzero rows after a re-embed means
# the 0.35 threshold needs recalibration for the new doc composition.
REFUSAL_PROBE = 'semantic_search("unicorn readmission velocity")'


def embed_command(embedding_endpoint: str) -> str:
    """Embed rows lacking a vector, in-database, caller impersonation."""
    return (
        ".set-or-replace semantic_catalog <|\n"
        "    let todo = semantic_catalog | where isnull(emb) "
        "or array_length(emb) == 0;\n"
        "    let done = semantic_catalog | where isnotnull(emb) "
        "and array_length(emb) > 0;\n"
        "    let embedded = todo\n"
        "        | evaluate ai_embeddings(search_text,\n"
        f"            '{embedding_endpoint};impersonate')\n"
        "        | project node_id, ['kind'], ['ref'], name, "
        "business_name,\n"
        "                  search_text, display_text, "
        "emb = search_text_embeddings;\n"
        "    union done, embedded"
    )


class SearchIndexError(RuntimeError):
    """The refresh left the index unusable — surfaced, never papered over."""


def refresh_search_index(
    mgmt: "Callable[[str], list[dict]]",
    query: "Callable[[str], list[dict]]",
    embedding_endpoint: str,
) -> dict:
    """Copy the catalog into the Eventhouse and re-embed every row.

    Raises SearchIndexError if any row is left without a vector — a
    partially embedded index silently mis-ranks, which is worse than
    a loud failure. The refusal probe result is REPORTED (threshold
    calibration is a judgment call), never auto-acted on.
    """
    mgmt(COPY_COMMAND)
    mgmt(embed_command(embedding_endpoint))
    total = int(query(ROWCOUNT_QUERY)[0]["Count"])
    missing = int(query(COVERAGE_QUERY)[0]["Count"])
    if missing:
        raise SearchIndexError(
            f"{missing} of {total} rows have no embedding after the "
            "embed pass — check the Azure OpenAI endpoint, callout "
            "policy, and the caller's Cognitive Services OpenAI User "
            "role, then rerun (only missing rows pay)."
        )
    refusal_rows = len(query(REFUSAL_PROBE))
    return {
        "rows": total,
        "missing_embeddings": missing,
        "refusal_probe_rows": refusal_rows,
        "threshold_ok": refusal_rows == 0,
    }
