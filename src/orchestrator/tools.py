"""The deterministic toolset (ADR 0035): find, read, list, link,
verify, census.

Seven tools shaped by what the STORE can do — never by question types.
Each is a fixed parameterized query plus pure computation; the LLM can
choose which tool and what parameters, never compose a query. The
dispatcher enforces the two structural guarantees:

1. No unsurfaced facts — read/verify tools accept only ids that a tool
   call in THIS conversation surfaced, or that the user's own words
   contain.
2. Every call lands in the trace, from which code stamps the Basis
   line (see agent.py) — silent selection is structurally impossible.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Callable

from src.graph.templates import _fold
from src.orchestrator.assemble import (
    AssemblyError,
    assemble_consumption_node,
    assemble_metric,
    assemble_step,
)
from src.orchestrator.core import resolve

# --- fixed queries ----------------------------------------------------

# Exact match on internal name, business name, or (for metrics) the
# ref itself — live find 2026-08-10: users say "ED Sepsis Screening"
# (business name) and "reporting.USP_IP_SEPSIS" (ref); matching only
# the internal name refused both.
FIND_BY_NAME_QUERY = (
    "declare query_parameters(p_name:string);\n"
    "semantic_catalog\n"
    "| where tolower(name) == tolower(p_name)\n"
    "    or tolower(business_name) == tolower(p_name)\n"
    "    or (['kind'] == 'metric' and tolower(['ref']) == tolower(p_name))\n"
    "| project node_id, ['kind'], ['ref'], name, business_name\n"
    "| order by node_id asc"
)

# Complete enumeration of one kind — the census (field find
# 2026-08-20, Sunny's web-UI test: "how many metrics are there" was
# planned as a name-search for the phrase 'metrics'; the honest empty
# was then captioned as "no metrics exist". Enumeration questions need
# an enumeration tool, not a phrase slot.)
# Name-containment companions to a semantic search (2026-08-21, live
# find: the top-K embedding ranking buried the literal near-names —
# 'Sepsis Case Details' absent from the top 12 for 'Sepsis Case').
# Deterministic, question-agnostic: containment IS relevance.
NAME_CONTAINS_QUERY = (
    "declare query_parameters(p_phrase:string);\n"
    "semantic_catalog\n"
    "| where name contains p_phrase or business_name contains p_phrase\n"
    "| project node_id, ['kind'], ['ref'], name, business_name\n"
    "| order by name asc, node_id asc\n"
    "| take 10"
)

LIST_CATALOG_QUERY = (
    "declare query_parameters(p_kind:string);\n"
    "semantic_catalog\n"
    "| where ['kind'] == p_kind\n"
    "| project node_id, ['kind'], ['ref'], name, business_name\n"
    "| order by name asc, node_id asc"
)

STEPS_OF_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "semantic_catalog | where ['kind'] == 'step' and ['ref'] == p_ref\n"
    "| project node_id, name\n"
    "| order by node_id asc"
)

# B3 step dep-chains (green-lit 2026-08-25, built 2026-08-27): the
# transform_to_transform edges enter the ask surface. Build direction
# is consumer -> dependency (builder.py wires each CTE to what it
# reads), so: fed_by = targets of edges FROM the step; feeds = sources
# of edges INTO the step.
STEP_FED_BY_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_edges\n"
    "| where source_id == p_id and edge_type == "
    "'transform_to_transform'\n"
    "| project node_id = target_id\n"
    "| join kind=inner (graph_nodes | project node_id, name) on node_id\n"
    "| project node_id, name\n"
    "| order by node_id asc"
)

STEP_FEEDS_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_edges\n"
    "| where target_id == p_id and edge_type == "
    "'transform_to_transform'\n"
    "| project node_id = source_id\n"
    "| join kind=inner (graph_nodes | project node_id, name) on node_id\n"
    "| project node_id, name\n"
    "| order by node_id asc"
)

BATCH_FRAGMENTS_QUERY = (
    "declare query_parameters(p_ids:string);\n"
    "graph_nodes\n"
    "| where set_has_element(todynamic(p_ids), node_id)\n"
    "| project node_id, name, description, properties"
)

# Token-degraded containment (suite find 2026-08-21: the model
# paraphrased the user's name into 'Sepsis Case Definition' — the
# full-phrase containment found nothing and no sibling stamp fired).
# has_all is Kusto term matching: every token must appear in the
# name/business-name text.
# p_tokens is a SPACE-JOINED string, split server-side — a dynamic
# query parameter is not reliably deserialized by the v2 REST body
# (live find 2026-08-21: the degraded-containment union silently
# returned 0 rows in the suite while the L0 fake passed).
NAME_CONTAINS_TOKENS_QUERY = (
    "declare query_parameters(p_tokens:string);\n"
    "semantic_catalog\n"
    "| where strcat(name, ' ', business_name) has_all (split(p_tokens, ' '))\n"
    "| project node_id, ['kind'], ['ref'], name, business_name\n"
    "| order by name asc, node_id asc\n"
    "| take 10"
)

# RW-18 (measured 2026-08-29: an exact MISS cost 15.8s and a
# semantic MISS 29.5s against ~1.9s hits — the containment
# degradation probed one query PER TOKEN, serially, twice per
# entity; ~10-15 round trips at ~1s each IS Sunny's 30s blank).
# One labeled scan replaces the whole probe loop: every row that
# matches ANY token rides back with the set of tokens it matched;
# productive/conjunctive/disjunctive all derive client-side.
NAME_CONTAINS_ANY_TOKEN_QUERY = (
    "declare query_parameters(p_tokens:string);\n"
    "let toks = split(p_tokens, ' ');\n"
    "semantic_catalog\n"
    "| extend blob = strcat(name, ' ', business_name)\n"
    "| mv-apply tok = toks to typeof(string) on (\n"
    "    where blob contains tok\n"
    "    | summarize matched_tokens = make_set(tok))\n"
    "| where array_length(matched_tokens) > 0\n"
    "| project node_id, ['kind'], ['ref'], name, business_name,\n"
    "          matched_tokens\n"
    "| order by array_length(matched_tokens) desc, name asc, "
    "node_id asc\n"
    "| take 40"
)

# Step-name universe (walk W6/W7, Sunny 2026-08-23: "is another
# metric using the same base population?" — the mention census saw 2
# description mentions while NINE procs build a step named Base_Pop
# with materially different logic; sameness claims from name evidence
# are the corpse). Exact step-NAME match (case-insensitive, space and
# underscore interchangeable), one row per (step_name, parent metric).
STEP_NAME_UNIVERSE_QUERY = (
    "declare query_parameters(p_name:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'transform:'\n"
    "    and (name =~ p_name\n"
    "         or replace_string(name, '_', ' ') =~ "
    "replace_string(p_name, '_', ' '))\n"
    "| extend ['ref'] = tostring(split(node_id, ':')[1]), step_name = name\n"
    "| distinct step_name, ['ref']\n"
    "| join kind=leftouter (semantic_catalog\n"
    "    | where ['kind'] == 'metric'\n"
    "    | project ['ref'], business_name) on ['ref']\n"
    "| project step_name, ['ref'], business_name\n"
    "| order by ['ref'] asc"
)

# Source-table identity (walk find 2026-08-21, Sunny: "how is
# IP_SEPSIS defined" — the phrase names a TECHNICAL node, which the
# semantic_catalog surfaces cannot see; the model census'd steps, got
# an honest 0, and concluded 'cannot be provided' while the graph held
# the answer). Technical nodes + transform_to_technical edges resolve
# a table-like phrase to the certified metrics that read it.
TABLE_USED_BY_QUERY = (
    "declare query_parameters(p_phrase:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'tech:' and name contains p_phrase\n"
    "| project tech_id = node_id, table_name = name\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'transform_to_technical'\n"
    "    | project tech_id = target_id, source_id) on tech_id\n"
    "| extend ['ref'] = tostring(split(source_id, ':')[1])\n"
    "| distinct table_name, ['ref']\n"
    "| join kind=leftouter (semantic_catalog\n"
    "    | where ['kind'] == 'metric'\n"
    "    | project ['ref'], business_name) on ['ref']\n"
    "| project table_name, ['ref'], business_name\n"
    "| order by table_name asc, ['ref'] asc"
)

# Decision layer to the ask-surface (ADR 0044 nodes, ADR 0052
# backfill item 1, Sunny's 2026-08-21 order): the WHERE/CASE criteria
# of one step, as first-class rows. Expression content passes the
# ADR 0025 PHI gate before it enters any prompt.
# Both decision queries join the sites' COLUMNS (columns work,
# 2026-08-22, walk probe C3): decision_to_column targets are column
# nodes whose name is the column name.
_DECISION_COLUMNS_JOIN = (
    "| join kind=leftouter (\n"
    "    graph_edges | where edge_type == 'decision_to_column'\n"
    "    | project node_id = source_id, col_id = target_id\n"
    "    | join kind=leftouter (graph_nodes\n"
    "        | project col_id = node_id, colname = name) on col_id\n"
    "    | summarize columns = make_set(colname) by node_id) on node_id\n"
)

DECISIONS_OF_STEP_QUERY = (
    "declare query_parameters(p_step:string);\n"
    "graph_edges\n"
    "| where edge_type == 'step_to_decision' and source_id == p_step\n"
    "| project node_id = target_id\n"
    "| join kind=inner (graph_nodes\n"
    "    | project node_id, name, description, properties) on node_id\n"
    + _DECISION_COLUMNS_JOIN +
    "| project node_id, name, description, properties, columns\n"
    "| order by node_id asc"
)

# Column blast radius (columns work 2026-08-22, walk probes C2/D5):
# which metrics FILTER on a column — decision sites are the only
# column-grain relation in the graph (transform_to_technical reads
# are table-grain, verified 2026-08-22: all 681 edges); SELECT-only
# usage is not tracked at column grain, and results say so.
COLUMN_FILTERS_QUERY = (
    "declare query_parameters(p_col:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'tech:'\n"
    "    and array_length(split(node_id, '.')) == 3\n"
    "    and name contains p_col\n"
    "| project col_id = node_id, column_name = name\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'decision_to_column'\n"
    "    | project col_id = target_id, source_id) on col_id\n"
    "| extend ['ref'] = tostring(split(source_id, ':')[1]),\n"
    "         step_name = tostring(split(source_id, ':')[2])\n"
    "| join kind=leftouter (semantic_catalog\n"
    "    | where ['kind'] == 'metric'\n"
    "    | project ['ref'], business_name) on ['ref']\n"
    "| project column_name, ['ref'], business_name, step_name\n"
    "| order by column_name asc, ['ref'] asc"
)

# Projection-grain selection (ADR 0053): which metrics SELECT a
# column — transform_to_column edges, minted resolved-only at build.
COLUMN_SELECTS_QUERY = (
    "declare query_parameters(p_col:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'tech:'\n"
    "    and array_length(split(node_id, '.')) == 3\n"
    "    and name contains p_col\n"
    "| project col_id = node_id, column_name = name\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'transform_to_column'\n"
    "    | project col_id = target_id, source_id) on col_id\n"
    "| extend ['ref'] = tostring(split(source_id, ':')[1]),\n"
    "         step_name = tostring(split(source_id, ':')[2])\n"
    "| join kind=leftouter (semantic_catalog\n"
    "    | where ['kind'] == 'metric'\n"
    "    | project ['ref'], business_name) on ['ref']\n"
    "| project column_name, ['ref'], business_name, step_name\n"
    "| order by column_name asc, ['ref'] asc"
)

# Presence probe: a graph export that predates ADR 0053 has zero
# projection edges — 'selected by none' must not be claimed then.
PROJECTION_EDGES_COUNT_QUERY = (
    "graph_edges | where edge_type == 'transform_to_column' | count"
)

# The table record (walk probe D4): a table's columns, from the
# dictionary-derived table_to_column edges — never parsed from SQL
# text at ask time.
TABLE_COLUMNS_QUERY = (
    "declare query_parameters(p_table:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'tech:'\n"
    "    and array_length(split(node_id, '.')) == 2\n"
    "    and name contains p_table\n"
    "| project table_id = node_id, table_name = name\n"
    "| join kind=leftouter (graph_edges\n"
    "    | where edge_type == 'table_to_column'\n"
    "    | project table_id = source_id, col_id = target_id) on table_id\n"
    "| join kind=leftouter (graph_nodes\n"
    "    | project col_id = node_id, column_name = name) on col_id\n"
    "| project table_id, table_name, column_name\n"
    "| order by table_name asc, column_name asc"
)

# One aggregate per metric: how many decision sites its steps carry
# (suite find 2026-08-21 post-tightening: mini retrieved the METRIC,
# whose record holds no decisions, and summarized — the count plus a
# stamped pointer makes the second hop machine truth on screen).
DECISION_COUNT_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "graph_nodes\n"
    "| where node_id startswith strcat('decision:', p_ref, ':')\n"
    "| count"
)

# The metric's decision evidence, inline (M2 design pass 2026-08-21,
# ADR 0018's move): the metric→decision closure is ALREADY
# materialized by the ADR 0044 id scheme (decision:{metric}:{step}:
# {site}) — this prefix query IS the closure, verified conserving
# against step_to_decision (1831=1831, 0 orphans, live 2026-08-21).
# Top sites by predicate weight, deterministic order; the cap is
# constant in the query text (today's lesson: nontrivial parameter
# types need live probes) and DISCLOSED in the stamped headline (B3).
# CONSOLE-4d: the OUTPUT-REACHABLE step set — canonical_to_transform
# points at the output step(s) only (build-time, parser-derived);
# closure over transform_to_transform gives the steps whose logic
# the metric's RESULT actually depends on. Dead CTEs (seeded estate
# noise) fall outside and their sites must never phrase as criteria.
CANONICAL_TARGETS_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "graph_edges\n"
    "| where edge_type == 'canonical_to_transform'\n"
    "    and source_id == strcat('canonical:', p_ref)\n"
    "| project target_id"
)

STEP_DEP_EDGES_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "graph_edges\n"
    "| where edge_type == 'transform_to_transform'\n"
    "    and source_id startswith strcat('transform:', p_ref, ':')\n"
    "| project source_id, target_id"
)

DECISIONS_OF_METRIC_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "graph_nodes\n"
    "| where node_id startswith strcat('decision:', p_ref, ':')\n"
    "| extend pc = tolong(todynamic(properties).predicate_count)\n"
    + _DECISION_COLUMNS_JOIN +
    "| project node_id, name, description, properties, pc, columns\n"
    "| order by pc desc, node_id asc\n"
    "| take 12"
)

# Consumption-layer links (ADR 0040): deterministic edges from TMDL
# partition lineage, exposed via the graph_edges shortcut.
REPORTS_OF_METRIC_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_edges\n"
    "| where edge_type == 'report_to_canonical' and target_id == p_id\n"
    "| project node_id = source_id\n"
    "| join kind=inner (graph_nodes | project node_id, name, description) on node_id\n"
    "| project node_id, name, description\n"
    "| order by node_id asc"
)

LINKS_OF_REPORT_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_edges\n"
    "| where source_id == p_id and edge_type in ("
    "'report_to_canonical', 'report_to_technical', 'report_to_measure')\n"
    "| project edge_type, node_id = target_id\n"
    "| join kind=inner (graph_nodes | project node_id, name) on node_id\n"
    "| project edge_type, node_id, name\n"
    "| order by edge_type asc, node_id asc"
)

MAX_VERIFY_IDS = 40
_MAX_FRAGMENT_CHARS = 4000
_MAX_DIFF_LINES = 60


# --- the content kernel (was variants.py) -----------------------------

def _normalized(text: str) -> str:
    """Equality view: whitespace collapsed, casefolded (T-SQL default
    collation is case-insensitive). Literal/structural differences
    still count as distinct."""
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def _content_key(text: str) -> str:
    return hashlib.sha256(_normalized(text).encode()).hexdigest()[:16]


def _cap(text: str) -> str:
    if len(text) <= _MAX_FRAGMENT_CHARS:
        return text
    return text[:_MAX_FRAGMENT_CHARS] + "\n... (truncated)"


def _diff(a: str, b: str) -> str:
    lines = list(difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile="group_1", tofile="group_2", lineterm="", n=1,
    ))
    if len(lines) > _MAX_DIFF_LINES:
        lines = lines[:_MAX_DIFF_LINES] + [
            f"... ({len(lines) - _MAX_DIFF_LINES} more diff lines)"]
    return "\n".join(lines)


# --- session (guarantee 1 state) --------------------------------------

@dataclass
class Session:
    """Ids this conversation may legitimately read: surfaced by a tool,
    or present verbatim in the user's own words."""
    surfaced: "set[str]" = field(default_factory=set)
    user_text: str = ""

    def note_user(self, text: str) -> None:
        self.user_text += "\n" + _fold(text)

    def allow(self, ids) -> None:
        self.surfaced.update(ids)

    def permitted(self, an_id: str) -> bool:
        return an_id in self.surfaced or _fold(an_id) in self.user_text


class ToolError(Exception):
    """Returned to the model as the tool result — visible, recoverable."""


# --- the five tools ---------------------------------------------------

def search_catalog(phrase: str, run_kql, session: Session) -> dict:
    """Find things: the one fixed semantic search, stratified plurality
    (closest metrics + closest steps), closeness visible."""
    result = resolve(phrase, run_kql)
    candidates = [
        {"id": (c.ref if c.kind == "metric" else c.node_id),
         "kind": c.kind, "name": c.name,
         "business_name": c.business_name or None,
         "of_metric": c.ref if c.kind == "step" else None,
         "closeness": round(c.closeness, 3)}
        for c in result.candidates
    ]
    session.allow(c["id"] for c in candidates)
    return {"candidates": candidates,
            "cleared_similarity_floor": result.total_matches,
            "note": ("closeness is the honest relevance signal; the floor "
                     "count is context, not a relevance claim")}


def find_by_name(name: str, run_kql, session: Session) -> dict:
    """Find things by EXACT (case-folded) name — families of same-named
    steps, precise refs. Leading # (temp-table spelling) is forgiven."""
    clean = name.strip().lstrip("#").strip("[]")
    rows = run_kql(FIND_BY_NAME_QUERY, {"p_name": clean})
    matches = [
        {"id": (r["ref"] if r["kind"] == "metric" else r["node_id"]),
         "kind": r["kind"], "name": r["name"],
         "business_name": r.get("business_name") or None,
         "of_metric": r["ref"] if r["kind"] == "step" else None}
        for r in rows
    ]
    session.allow(m["id"] for m in matches)
    out = {"matches": matches, "count": len(matches)}
    if not matches:
        # E6 guard (field find 2026-08-20): an empty NAME lookup says
        # nothing about how many items of a KIND exist — captioning it
        # as "none exist" is exactly the over-claim this note blocks.
        out["note"] = ("no item bears this exact NAME — this is not a "
                       "statement about how many items of a kind exist; "
                       "for 'how many / list all metrics|reports|...' "
                       "use list_catalog")
    return out


CATALOG_KINDS = ("metric", "step", "term", "report", "measure", "flag")

# ADR 0054 flag surface, GRAPH-NATIVE (ADR 0057 "Clusters are
# nodes", Sunny's demo law 2026-08-25): the sweep's verdicts are
# reified GOVERNANCE-layer cluster nodes with member_of edges —
# census/retrieve TRAVERSE; the gov_red_flags side table is retired.
_CLUSTER_PROJECT = (
    "| extend p = todynamic(properties)\n"
    "| project flag_id = node_id,\n"
    "          flag_class = tostring(p.flag_class),\n"
    "          grain = tostring(p.grain),\n"
    "          identity = tostring(p.identity),\n"
    "          severity = tostring(p.severity),\n"
    "          scope = tostring(p.scope),\n"
    "          member_count = toint(p.member_count),\n"
    "          distinct_logics = toint(p.distinct_logics),\n"
    "          blast_radius = toint(p.blast_radius),\n"
    "          blast_basis = tostring(p.blast_basis),\n"
    "          disposition = tostring(p.disposition),\n"
    "          disposition_reason = tostring(p.disposition_reason),\n"
    "          drill_query = tostring(p.drill_query),\n"
    # RW-7 flag cards: the sweep's self-description rides every flag
    # row — the card's one-line WHY (machine-authored at mint)
    "          description = description\n"
)

# RW-12 (glass check 2026-08-28): member NAMES ride every flag row —
# "10 members means nothing to a user" (Sunny). Bulk 2-hop over the
# member_of chain, one query for all clusters.
GOV_FLAG_MEMBER_NAMES_QUERY = (
    "graph_edges\n"
    "| where edge_type == 'member_of' and target_id startswith "
    "'loggroup:'\n"
    "| project member = source_id, lg = target_id\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'member_of' and target_id startswith "
    "'cluster:'\n"
    "    | project lg = source_id, cluster = target_id) on lg\n"
    "| join kind=leftouter (graph_nodes\n"
    "    | project member = node_id, mname = name) on member\n"
    "| extend shown = coalesce(mname, member)\n"
    # RW-BATCH-4 polish (re-walk 2026-08-29): ids ride along so the
    # census can schema-qualify colliding bare names — the misnomer
    # card's whole point is that a shared name hides difference
    "| summarize member_names = make_list(shown, 64), "
    "member_ids = make_list(member, 64) by cluster"
)

GOV_FLAGS_QUERY = (
    "graph_nodes\n"
    "| where node_id startswith 'cluster:'\n"
    + _CLUSTER_PROJECT
    + "| order by severity asc, flag_class asc, identity asc"
)

# The sweep RECEIPT (smoke find 2026-08-26: a pre-1.58 store answered
# census(flag) with an honest-looking 0 — pre-sweep absence is not
# proven zero-flags; the same false-empty class as W13b). The build
# writes one govmeta node per run; a zero-flag census must cite it or
# refuse with the remediation.
GOV_SWEEP_META_QUERY = (
    "graph_nodes\n"
    "| where node_id == 'govmeta:sweep'\n"
    "| extend p = todynamic(properties)\n"
    "| project swept = toint(p.swept), flagged = toint(p.flagged),\n"
    "          clean = toint(p.clean), run_at = tostring(p.run_at)"
)

GOV_FLAG_BY_ID_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_nodes\n"
    "| where node_id == p_id and node_id startswith 'cluster:'\n"
    + _CLUSTER_PROJECT
)

# member rows of one cluster: cluster <- logic_group <- org node
GOV_FLAG_MEMBERS_QUERY = (
    "declare query_parameters(p_id:string);\n"
    "graph_edges\n"
    "| where edge_type == 'member_of' and target_id == p_id\n"
    "| project group_id = source_id\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'member_of'\n"
    "    | project member_id = source_id, group_id = target_id)\n"
    "    on group_id\n"
    "| join kind=inner (graph_nodes\n"
    "    | project group_id = node_id, gprops = properties)\n"
    "    on group_id\n"
    "| join kind=inner (graph_nodes\n"
    "    | project member_id = node_id, member_name = name)\n"
    "    on member_id\n"
    "| project member_id, member_name,\n"
    "          content_key = tostring(todynamic(gprops).content_key)\n"
    "| order by member_id asc"
)

GOV_FLAGS_BY_IDENTITY_QUERY = (
    "declare query_parameters(p_identity:string, p_grain:string);\n"
    "graph_nodes\n"
    "| where node_id startswith 'cluster:'\n"
    + _CLUSTER_PROJECT
    + "| where grain == p_grain and identity =~ p_identity\n"
    "| project flag_id, flag_class, severity, member_count,\n"
    "          distinct_logics, disposition"
)

GOV_FLAGS_FOR_MEMBER_QUERY = (
    "declare query_parameters(p_ref:string);\n"
    "graph_edges\n"
    "| where edge_type == 'member_of'\n"
    "    and source_id == strcat('canonical:', p_ref)\n"
    "| project group_id = target_id\n"
    "| join kind=inner (graph_edges\n"
    "    | where edge_type == 'member_of'\n"
    "    | project group_id = source_id, cluster_id = target_id)\n"
    "    on group_id\n"
    "| distinct cluster_id\n"
    "| join kind=inner (graph_nodes\n"
    "    | project cluster_id = node_id, properties) on cluster_id\n"
    "| extend p = todynamic(properties)\n"
    "| project flag_id = cluster_id,\n"
    "          flag_class = tostring(p.flag_class),\n"
    "          severity = tostring(p.severity),\n"
    "          identity = tostring(p.identity),\n"
    "          disposition = tostring(p.disposition)"
)


def list_catalog(kind: str, run_kql, session: Session) -> dict:
    """Complete census of one kind — enumeration questions ('how many
    metrics', 'list all reports') are answered here, never by feeding
    a kind word into a name/phrase slot."""
    k = kind.strip().lower()
    if k not in CATALOG_KINDS and k.endswith("s") and k[:-1] in CATALOG_KINDS:
        k = k[:-1]
    if k not in CATALOG_KINDS:
        raise ToolError(
            f"unknown kind {kind!r} — kinds: {', '.join(CATALOG_KINDS)}")
    rows = run_kql(LIST_CATALOG_QUERY, {"p_kind": k})
    items = [
        {"id": (r["ref"] if r["kind"] == "metric" else r["node_id"]),
         "name": r["name"],
         "business_name": r.get("business_name") or None,
         "of_metric": r["ref"] if r["kind"] == "step" else None}
        for r in rows
    ]
    session.allow(i["id"] for i in items)
    return {"kind": k, "count": len(items), "items": items,
            "note": "complete enumeration of this kind — the count is exact"}


def get_facts(an_id: str, run_kql, session: Session) -> dict:
    """Read one thing — a metric ref or a step node_id. Fixed lookups."""
    if not session.permitted(an_id):
        raise ToolError(
            f"id {an_id!r} was not surfaced by any search in this "
            "conversation and does not appear in the user's words — "
            "search first (no unsurfaced facts)")
    try:
        if an_id.startswith("transform:"):
            ref = an_id.split(":", 2)[1]
            fs = assemble_step(an_id, ref, run_kql)
        elif an_id.startswith(("report:", "measure:")):
            fs = assemble_consumption_node(an_id, run_kql)
        else:
            fs = assemble_metric(an_id, run_kql)
    except AssemblyError as e:
        raise ToolError(str(e))
    return {"kind": fs.kind, "ref": fs.ref, "facts": fs.facts,
            "basis": fs.basis}


def list_steps(ref: str, run_kql, session: Session) -> dict:
    """The structure of one metric: its step inventory."""
    if not session.permitted(ref):
        raise ToolError(
            f"metric {ref!r} was not surfaced in this conversation — "
            "search first (no unsurfaced facts)")
    rows = run_kql(STEPS_OF_QUERY, {"p_ref": ref})
    steps = [{"id": r["node_id"], "name": r["name"]} for r in rows]
    session.allow(s["id"] for s in steps)
    return {"metric": ref, "steps": steps, "count": len(steps)}


def list_report_links(an_id: str, run_kql, session: Session) -> dict:
    """The consumption layer's edges, both directions (ADR 0040).

    For a metric ref: which Power BI reports are built on it. For a
    report id: everything its semantic model links to — metrics it
    executes, warehouse tables it reads directly (DirectLake), and its
    DAX measures. Edges come from parsed TMDL partitions, never name
    similarity."""
    if not session.permitted(an_id):
        raise ToolError(
            f"id {an_id!r} was not surfaced in this conversation and does "
            "not appear in the user's words — search first (no unsurfaced "
            "facts)")
    if an_id.startswith("report:"):
        rows = run_kql(LINKS_OF_REPORT_QUERY, {"p_id": an_id})
        links = {"executes_metrics": [], "reads_tables": [], "measures": []}
        bucket = {"report_to_canonical": "executes_metrics",
                  "report_to_technical": "reads_tables",
                  "report_to_measure": "measures"}
        for r in rows:
            entry = {"id": r["node_id"], "name": r["name"]}
            if r["edge_type"] == "report_to_canonical":
                entry["id"] = r["node_id"].removeprefix("canonical:")
            links[bucket[r["edge_type"]]].append(entry)
        session.allow(
            e["id"] for group in links.values() for e in group)
        return {"report": an_id, **links,
                "note": ("links come from parsed semantic-model partitions "
                         "(deterministic lineage), not name matching")}
    canonical_id = f"canonical:{an_id}"
    rows = run_kql(REPORTS_OF_METRIC_QUERY, {"p_id": canonical_id})
    reports = [
        {"id": r["node_id"], "name": r["name"],
         "description": r.get("description") or None}
        for r in rows
    ]
    session.allow(r["id"] for r in reports)
    return {"metric": an_id, "reports": reports, "count": len(reports),
            "note": ("empty means no semantic model linking this metric has "
                     "been ingested — absence of a link is not proof no "
                     "report exists")}


def check_same_logic(ids: "list[str]", run_kql, session: Session) -> dict:
    """Verify: THE computation. Content-hash partition over any set of
    nodes (step node_ids and/or metric refs — a metric contributes its
    whole calculation_logic). Groups, diffs between the two largest
    groups, and honest 'not comparable' for unrecorded SQL. Never an
    LLM impression."""
    if not ids or len(ids) < 2:
        raise ToolError("give at least two ids to compare")
    if len(ids) > MAX_VERIFY_IDS:
        raise ToolError(f"at most {MAX_VERIFY_IDS} ids per call")
    for an_id in ids:
        if not session.permitted(an_id):
            raise ToolError(
                f"id {an_id!r} was not surfaced in this conversation — "
                "search first (no unsurfaced facts)")

    texts: "dict[str, str]" = {}
    step_ids = [i for i in ids if i.startswith("transform:")]
    if step_ids:
        rows = run_kql(BATCH_FRAGMENTS_QUERY,
                       {"p_ids": json.dumps(sorted(step_ids))})
        for r in rows:
            props = r.get("properties") or "{}"
            if isinstance(props, str):
                props = json.loads(props)
            texts[r["node_id"]] = props.get("sql_fragment") or ""
    for an_id in ids:
        if an_id.startswith("transform:"):
            texts.setdefault(an_id, "")
        else:
            try:
                fs = assemble_metric(an_id, run_kql)
            except AssemblyError as e:
                raise ToolError(str(e))
            texts[an_id] = fs.facts.get("calculation_logic") or ""

    unrecorded = sorted(i for i in ids if not texts[i].strip())
    grouped: "dict[str, list]" = {}
    for an_id in sorted(set(ids) - set(unrecorded)):
        grouped.setdefault(_content_key(texts[an_id]), []).append(an_id)
    groups = sorted(grouped.values(), key=lambda g: (-len(g), g[0]))

    out: dict = {
        "distinct_definitions": len(groups),
        "groups": [{"members": g} for g in groups],
        "all_same": len(groups) == 1 and not unrecorded,
    }
    if unrecorded:
        out["not_comparable"] = unrecorded
        out["note"] = ("SQL not recorded for these ids — absence is not "
                       "sameness; all_same cannot be claimed")
        out["all_same"] = False if len(groups) != 1 else None
    if len(groups) >= 2:
        out["diff_between_two_largest_groups"] = _diff(
            _cap(texts[groups[0][0]]), _cap(texts[groups[1][0]]))
    return out


# --- schemas + dispatch ----------------------------------------------

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "search_catalog",
        "description": ("Semantic search over the certified catalog of "
                        "metrics and calculation steps. Returns the "
                        "closest metrics and closest steps with a "
                        "closeness score each. TOP MATCHES ONLY — not "
                        "exhaustive; to gather EVERY item bearing a "
                        "specific name, use find_by_name instead."),
        "parameters": {"type": "object", "properties": {
            "phrase": {"type": "string",
                       "description": "short search phrase (2-6 words)"}},
            "required": ["phrase"]}}},
    {"type": "function", "function": {
        "name": "find_by_name",
        "description": ("Exact lookup (case-insensitive) by internal name, "
                        "business name, or metric ref. Use for a specific "
                        "name the user typed, or to find every proc "
                        "defining a same-named step."),
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "list_catalog",
        "description": ("Complete census of one KIND: every metric, "
                        "report, measure, step, or term in the certified "
                        "catalog, with names and an exact count. ALWAYS "
                        "use this for 'how many X are there' and 'list "
                        "all X' — kind words (metrics, reports) are "
                        "categories, never search phrases or names."),
        "parameters": {"type": "object", "properties": {
            "kind": {"type": "string",
                     "enum": ["metric", "step", "term", "report",
                              "measure"]}},
            "required": ["kind"]}}},
    {"type": "function", "function": {
        "name": "get_facts",
        "description": ("Full certified facts for one item: a metric ref "
                        "(e.g. reporting.USP_X) or a step id "
                        "(transform:...). For metrics this includes the "
                        "SOURCE TABLES list, steward/developer, report "
                        "link, description, and full SQL. Only ids "
                        "surfaced this conversation or typed by the "
                        "user."),
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string"}}, "required": ["id"]}}},
    {"type": "function", "function": {
        "name": "list_steps",
        "description": ("All calculation steps (SQL stages) of one metric, "
                        "with ids. Steps are NOT source tables — for "
                        "tables use get_facts."),
        "parameters": {"type": "object", "properties": {
            "ref": {"type": "string"}}, "required": ["ref"]}}},
    {"type": "function", "function": {
        "name": "list_report_links",
        "description": ("The Power BI consumption layer, both directions. "
                        "For a metric ref: which reports are BUILT ON it "
                        "(blast radius up). For a report id (report:...): "
                        "the metrics its semantic model executes, warehouse "
                        "tables it reads directly, and its DAX measures. "
                        "Links are parsed from the semantic models "
                        "themselves — deterministic, never name-matched. "
                        "Only ids surfaced this conversation or typed by "
                        "the user."),
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string"}}, "required": ["id"]}}},
    {"type": "function", "function": {
        "name": "check_same_logic",
        "description": ("Computed verdict on whether items share identical "
                        "SQL logic (content-hash; whitespace/case "
                        "forgiven). Accepts 2-40 step ids and/or metric "
                        "refs; returns groups of identical members, a "
                        "diff, and which ids had no SQL recorded. ALWAYS "
                        "use this for any same/different-logic question — "
                        "never judge SQL equality yourself. For 'is this "
                        "step the same everywhere' questions, gather the "
                        "complete family with find_by_name first."),
        "parameters": {"type": "object", "properties": {
            "ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["ids"]}}},
]

_IMPL: "dict[str, Callable]" = {
    "search_catalog": lambda args, run_kql, s: search_catalog(
        str(args.get("phrase", "")), run_kql, s),
    "find_by_name": lambda args, run_kql, s: find_by_name(
        str(args.get("name", "")), run_kql, s),
    "list_catalog": lambda args, run_kql, s: list_catalog(
        str(args.get("kind", "")), run_kql, s),
    "get_facts": lambda args, run_kql, s: get_facts(
        str(args.get("id", "")), run_kql, s),
    "list_steps": lambda args, run_kql, s: list_steps(
        str(args.get("ref", "")), run_kql, s),
    "check_same_logic": lambda args, run_kql, s: check_same_logic(
        list(args.get("ids", [])), run_kql, s),
    "list_report_links": lambda args, run_kql, s: list_report_links(
        str(args.get("id", "")), run_kql, s),
}


def dispatch(name: str, args: dict, run_kql, session: Session) -> dict:
    """Run one tool call. Errors return AS RESULTS (visible to the
    model, recoverable) — including infrastructure failures (live find
    2026-08-13: a paused capacity became a raw 500 through the web
    surface; the model should instead be able to SAY the knowledge
    base is unreachable)."""
    if name not in _IMPL:
        return {"error": f"unknown tool {name!r}"}
    try:
        return _IMPL[name](args, run_kql, session)
    except ToolError as e:
        return {"error": str(e)}
    except Exception as e:                     # noqa: BLE001 — infra layer
        text = str(e)
        m = re.search(r'"@message"\s*:\s*"([^"]{1,160})', text)
        detail = (m.group(1) if m else text[:140]).strip()
        return {"error": ("the certified knowledge base is unreachable "
                          f"({type(e).__name__}: {detail}) — common "
                          "causes: capacity paused or a broken OneLake "
                          "shortcut in the KQL database")}
