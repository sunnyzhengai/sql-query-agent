"""Local reference implementation of the graph agent — dev only, never shipped.

Resolve-then-traverse (ADR 0017), exactly as the instructions prescribe for
the Fabric agent, but with each half in its proper engine:

  RESOLVE  — one LLM call: question + catalogs in, JSON plan out
             (intent + anchors as certified keys copied from the catalog)
  TRAVERSE — deterministic templates (src/graph/templates.py), no LLM

The Basis footer is computed BY CODE from what actually executed — honest
by construction, the property the Fabric agent's footer lacked.

When this reference answers the certified answer key correctly and the
Fabric agent does not, the platform's NL2GQL layer is at fault — clean
fault attribution for the rematch writeup.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from src.graph.templates import GraphView

INTENTS = (
    "list_metrics",        # which/what metrics match a topic (resolution IS the answer)
    "explain_metric",      # how is metric M calculated
    "tables_of_metric",    # which tables does metric M use
    "metrics_of_table",    # which metrics read table T
    "shared_sources",      # what shares source tables with metric M
    "columns_of_table",    # which columns does table T have
    "most_read",           # which metric reads the most tables
    "refuse",              # nothing in the catalogs relates
)

RESOLUTION_INSTRUCTIONS = (
    "You are the resolution step of a metrics agent. You receive certified "
    "catalogs and a user question. Match the question's words to catalog "
    "entries SEMANTICALLY — typos, case differences, synonyms, and topic "
    "phrases must still match; a metric reference containing a dot matches "
    "metricId, a bare one matches name (possibly in several schemas — return "
    "all of them). Reply with STRICT JSON only, no prose, no code fences:\n"
    '{"intent": "<one of: ' + ", ".join(INTENTS) + '>",\n'
    ' "anchors": [{"type": "metric"|"table", "key": "<EXACT value copied from '
    'the catalog: metricId for metrics, tableName for tables>"}],\n'
    ' "note": "<one short sentence: why these anchors>"}\n'
    "Rules: keys MUST be copied verbatim from catalog rows, never from the "
    "user's text. If several catalog entries match, include them all. If "
    "nothing in the catalogs relates to the question, use intent refuse with "
    "no anchors."
)

REFUSAL = "I don't have that in the certified knowledge base."


def _catalog_payload(view: GraphView, question: str) -> str:
    metrics = "\n".join(
        f"- metricId: {m['metricId']} | name: {m['name']} | {m.get('description') or ''}"
        for m in view.metric_catalog()
    )
    tables = "\n".join(
        f"- tableName: {t['tableName']} (schema {t.get('schemaName') or '?'})"
        for t in view.table_catalog()
    )
    return (
        f"METRIC CATALOG ({len(view.metric_catalog())} rows):\n{metrics}\n\n"
        f"TABLE CATALOG ({len(view.table_catalog())} rows):\n{tables}\n\n"
        f"QUESTION: {question}"
    )


class LocalGraphAgent:
    """resolver(system, user) -> str lets tests script resolution and lets
    live runs use devtools.local_llm.chat_completion."""

    def __init__(self, view: GraphView, resolver: "Callable[[str, str], str]") -> None:
        self.view = view
        self.resolver = resolver

    def answer(self, question: str) -> "dict[str, Any]":
        raw = self.resolver(RESOLUTION_INSTRUCTIONS, _catalog_payload(self.view, question))
        plan = json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        intent = plan.get("intent")
        anchors = plan.get("anchors") or []

        if intent == "refuse" or (not anchors and intent not in ("most_read", "list_metrics")):
            return self._result(REFUSAL, "catalog fetch -> 0 anchors matched", plan, [])

        if intent == "list_metrics":
            keys = [a["key"] for a in anchors]
            text = f"{len(keys)} certified metrics match: " + ", ".join(keys)
            return self._result(text, f"catalog fetch -> {len(keys)} matched semantically", plan, keys)

        if intent == "most_read":
            rows = self.view.most_read_metrics(top=3)
            text = "; ".join(f"{r['metricId']} ({r['tableCount']} tables)" for r in rows)
            return self._result(text, f"most_read over USES_TABLE -> top {len(rows)}", plan, rows)

        sections, bases, all_rows = [], [], []
        for anchor in anchors:
            key = anchor["key"]
            if intent == "tables_of_metric":
                rows = self.view.tables_of_metric(key)
                names = sorted({r["tableName"] for r in rows})
                sections.append(f"{key} uses {len(names)} tables: " + ", ".join(names))
                bases.append(f"tables_of_metric('{key}') -> {len(rows)} rows")
            elif intent == "metrics_of_table":
                rows = self.view.metrics_of_table(key)
                ids = [r["metricId"] for r in rows]
                sections.append(f"{len(ids)} metrics read {key}: " + ", ".join(ids))
                bases.append(f"metrics_of_table('{key}') -> {len(rows)} rows")
            elif intent == "shared_sources":
                rows = self.view.shared_source_metrics(key)
                top = ", ".join(f"{r['metricId']} ({r['sharedTables']})" for r in rows[:5])
                sections.append(f"{len(rows)} metrics share tables with {key}; top: {top}")
                bases.append(f"shared_source_metrics('{key}') -> {len(rows)} rows")
            elif intent == "columns_of_table":
                rows = self.view.columns_of_table(key)
                sample = ", ".join(r["columnName"] for r in rows[:8])
                sections.append(f"{key} has {len(rows)} dictionary columns (e.g. {sample}, ...)")
                bases.append(f"columns_of_table('{key}') -> {len(rows)} rows")
            elif intent == "explain_metric":
                steps = self.view.steps_of_metric(key)
                tables = self.view.tables_of_metric(key)
                names = sorted({r["tableName"] for r in tables})
                sections.append(
                    f"{key} is calculated in {len(steps)} steps "
                    f"(root: {steps[0]['name'] if steps else '?'}) over "
                    f"{len(names)} tables: " + ", ".join(names)
                )
                bases.append(
                    f"steps_of_metric('{key}') -> {len(steps)} rows; "
                    f"tables_of_metric('{key}') -> {len(tables)} rows"
                )
                rows = steps
            else:
                raise ValueError(f"unknown intent from resolution: {intent!r}")
            all_rows.extend(rows)
            if not rows:
                sections[-1] = f"{key}: nothing found in the certified graph."

        if len(anchors) > 1:
            sections.insert(0, f"Your reference matched {len(anchors)} certified items — answering for each:")
        return self._result("\n".join(sections), "; ".join(bases), plan, all_rows)

    @staticmethod
    def _result(text: str, basis: str, plan: dict, rows: list) -> "dict[str, Any]":
        return {"text": text, "basis": f"Basis: {basis}", "plan": plan, "rows": rows}
