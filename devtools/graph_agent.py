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
import re
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

INTENT_GUIDE = """\
- tables_of_metric: "which tables does metric M use/read?" -> ONE anchor {type: metric}
- metrics_of_table: "which metrics use/read table T?" -> ONE anchor {type: table}
- explain_metric: "how is metric M calculated?" -> ONE anchor {type: metric}
- shared_sources: "what shares source tables with metric M?" -> ONE anchor {type: metric}
- columns_of_table: "which columns does table T have?" -> ONE anchor {type: table}
- list_metrics: "which metrics are about <topic>?" -> anchors: ALL matching metrics
- most_read: "which metric reads the most tables?" -> no anchors
- refuse: nothing in the catalogs relates -> no anchors
Direction check before answering: the anchor is the entity NAMED in the
question; the intent's output is the OTHER side. If the question names a
metric and asks about tables, that is tables_of_metric, never metrics_of_table."""

RESOLUTION_INSTRUCTIONS = (
    "You are the resolution step of a metrics agent. You receive certified "
    "catalogs and a user question. Match the question's words to catalog "
    "entries SEMANTICALLY — typos, case differences, synonyms, and topic "
    "phrases must still match; a metric reference containing a dot matches "
    "metricId, a bare one matches name (possibly in several schemas — return "
    "all of them).\n\nIntents:\n" + INTENT_GUIDE + "\n\n"
    "Reply with STRICT JSON only, no prose, no code fences:\n"
    '{"intent": "<one of: ' + ", ".join(INTENTS) + '>",\n'
    ' "anchors": [{"type": "metric"|"table", "key": "<EXACT value copied from '
    'the catalog: metricId for metrics, tableName for tables>"}],\n'
    ' "note": "<one short sentence: why these anchors>"}\n'
    "CRITICAL — anchors are the entities the question is ABOUT (the traversal "
    "INPUTS), never your guess at the answer. 'Which metrics read table T?' "
    "has exactly ONE anchor: {type: table, key: T}. The traversal engine finds "
    "the metrics — you do not. 'Which tables does metric M use?' has ONE "
    "anchor: {type: metric, key: M}.\n"
    "Rules: keys MUST be copied verbatim from catalog rows, never from the "
    "user's text. Include several anchors ONLY when the question's reference "
    "itself is ambiguous (same bare name in two schemas) or names several "
    "entities. If nothing in the catalogs relates, use intent refuse with no "
    "anchors."
)

# Deterministic guardrails around the LLM boundary: each intent takes
# anchors of exactly one type, and every key must exist in its catalog.
ANCHOR_TYPE_BY_INTENT = {
    "list_metrics": "metric",
    "explain_metric": "metric",
    "tables_of_metric": "metric",
    "shared_sources": "metric",
    "metrics_of_table": "table",
    "columns_of_table": "table",
    "most_read": None,
    "refuse": None,
}

REFUSAL = "I don't have that in the certified knowledge base."


def _parse_plan(raw: str) -> dict:
    return json.loads(
        raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    )


def _lexical_hits(view: GraphView, question: str) -> "list[dict]":
    """Deterministic recall pass (ADR 0017): exact fold-matches of question
    tokens against catalog names. Identifier-shaped references get found by
    code; the LLM only arbitrates — it cannot wander past an exact hit."""
    hits = []
    tokens = {t.upper() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_.]{3,}", question)}
    for m in view.metric_catalog():
        if m["metricId"].upper() in tokens or m["name"].upper() in tokens:
            hits.append({"type": "metric", "key": m["metricId"],
                         "label": f"metric {m['metricId']} (name: {m['name']})"})
    for t in view.table_catalog():
        if t["tableName"].upper() in tokens:
            hits.append({"type": "table", "key": t["tableName"],
                         "label": f"table {t['tableName']}"})
    return hits


def _catalog_payload(view: GraphView, question: str) -> str:
    metrics = "\n".join(
        f"- metricId: {m['metricId']} | name: {m['name']} | {m.get('description') or ''}"
        for m in view.metric_catalog()
    )
    tables = "\n".join(
        f"- tableName: {t['tableName']} (schema {t.get('schemaName') or '?'})"
        for t in view.table_catalog()
    )
    hits = _lexical_hits(view, question)
    hint = (
        "EXACT NAME MATCHES found in the question (strong evidence — anchor "
        "to these unless the question clearly means otherwise):\n"
        + "\n".join(f"- {h['label']}" for h in hits) + "\n\n"
    ) if hits else ""
    return (
        f"METRIC CATALOG ({len(view.metric_catalog())} rows):\n{metrics}\n\n"
        f"TABLE CATALOG ({len(view.table_catalog())} rows):\n{tables}\n\n"
        f"{hint}QUESTION: {question}"
    )


class LocalGraphAgent:
    """resolver(system, user) -> str lets tests script resolution and lets
    live runs use devtools.local_llm.chat_completion."""

    def __init__(self, view: GraphView, resolver: "Callable[[str, str], str]") -> None:
        self.view = view
        self.resolver = resolver

    def _plan_errors(self, plan: dict, hits: "list[dict] | None" = None) -> "list[str]":
        errors = []
        intent = plan.get("intent")
        if intent not in INTENTS:
            return [f"intent {intent!r} is not one of {INTENTS}"]
        anchor_keys = {(a.get("key") or "").upper() for a in plan.get("anchors") or []}
        if hits and not anchor_keys & {h["key"].upper() for h in hits}:
            errors.append(
                "the question contains EXACT catalog matches your plan ignored: "
                + "; ".join(h["label"] for h in hits)
                + " — anchor to these (with their stated type) unless the "
                "question clearly means otherwise"
            )
        if hits:
            # Same bare name in several schemas: anchoring a strict subset
            # silently resolves an ambiguity that belongs to the user.
            by_label: "dict[str, list[dict]]" = {}
            for h in hits:
                if h["type"] == "metric":
                    bare = h["label"].rsplit("name: ", 1)[-1].rstrip(")").upper()
                    by_label.setdefault(bare, []).append(h)
            for bare, group in by_label.items():
                group_keys = {h["key"].upper() for h in group}
                taken = anchor_keys & group_keys
                if taken and taken != group_keys:
                    errors.append(
                        f"the bare name {bare} matches {len(group)} metrics "
                        f"({', '.join(sorted(group_keys))}) — anchor ALL of them; "
                        "the ambiguity is surfaced to the user, never resolved silently"
                    )
        expected = ANCHOR_TYPE_BY_INTENT[intent]
        metric_keys = {m["metricId"].upper() for m in self.view.metric_catalog()}
        table_keys = {t["tableName"].upper() for t in self.view.table_catalog()}
        for anchor in plan.get("anchors") or []:
            a_type, key = anchor.get("type"), anchor.get("key", "")
            if expected and a_type != expected:
                errors.append(
                    f"intent {intent} takes {expected} anchors; got {a_type} "
                    f"({key!r}) — anchors are the question's INPUTS, not the answer"
                )
            elif a_type == "metric" and key.upper() not in metric_keys:
                errors.append(f"{key!r} is not a metricId in the metric catalog")
            elif a_type == "table" and key.upper() not in table_keys:
                errors.append(f"{key!r} is not a tableName in the table catalog")
        return errors

    def answer(self, question: str) -> "dict[str, Any]":
        payload = _catalog_payload(self.view, question)
        hits = _lexical_hits(self.view, question)
        raw = self.resolver(RESOLUTION_INSTRUCTIONS, payload)
        plan = _parse_plan(raw)
        errors = self._plan_errors(plan, hits)
        if errors:
            retry_payload = (
                f"{payload}\n\nYOUR PREVIOUS PLAN WAS INVALID:\n{json.dumps(plan)}\n"
                "Validator errors:\n- " + "\n- ".join(errors) + "\nPlan again, fixing these."
            )
            plan = _parse_plan(self.resolver(RESOLUTION_INSTRUCTIONS, retry_payload))
            errors = self._plan_errors(plan, hits)
            if errors:
                return self._result(
                    "Resolution failed validation twice — no answer attempted.",
                    "invalid plan: " + "; ".join(errors), plan, [],
                )
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
