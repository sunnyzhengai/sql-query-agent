"""The translator — ADR 0044 clauses 2 and 5, spec:F's τ.

Clause 2 (translator blindness): the LLM NEVER sees SQL statements —
its input is typed tree facts plus dictionary lines. Mechanically: no
`fragment`/`sql` parameter exists on the prompt builder, and the prompt
carries fact lines only (each fact does include its own predicate
expression — the fact IS the predicate — but never the statement:
no SELECT list, no FROM, no sibling predicates).

Clause 5 (every decision is voiced or counted): the LEDGER. Each
must-voice leaf gets a numbered fact; the response is parsed back line
by line; facts the model failed to voice are counted in `unvoiced` and
appear in the output via the deterministic template floor
(src/tree/render.py) — completeness by construction, silence
impossible.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.tree.extract import DecisionTree
from src.tree.render import render_fact

# v2: DESC-VOICE-1 (steward voice, named subject, acronym rule) —
# the version rides the cache key, so every description regenerates
FACT_PROMPT_VERSION = "2"

_MAX_DICT_LINES = 30

_FACT_HEADER = (
    "You are documenting a certified business metric's calculation step "
    "for a business audience of clinicians and executives.\n"
    "Step name: {name}\n"
    "{deps_block}"
    "{dict_block}"
    "The step applies EXACTLY the numbered decisions below (extracted "
    "from the certified logic — there are no other decisions):\n"
    "{facts_block}\n\n"
    "First write ONE sentence (max 30 words) stating what this step "
    "produces in business terms, grounded only in the decisions above "
    "and the dependency descriptions. Name the SUBJECT as "
    "'{subject}' — say '{subject} are included when …', never "
    "'membership' or 'the dataset' (DESC-VOICE-1).\n"
    "Then translate EVERY numbered decision into one line of plain "
    "business language, formatted exactly as 'N| translation' using the "
    "same number N. Keep every literal value (codes, numbers, statuses, "
    "date tokens) exactly as given, adding the dictionary meaning beside "
    "a code when provided. Decisions marked or-group are ALTERNATIVES — "
    "phrase them as either/or, never as combined requirements. Never "
    "show raw table/column identifiers or temp-table names — use the "
    "dictionary description or a plain phrase. Write for a STEWARD, "
    "not a developer: never mention tables, temp tables, joins, "
    "queries, columns or 'the dataset'. Never expand an acronym "
    "unless the source or dictionary expands it — print it as "
    "written. Never invent a value, "
    "never drop a number, never add a decision that is not listed. "
    "No preamble, no markdown."
)


@dataclass
class TranslationResult:
    text: str = ""
    ledger: "dict[str, str]" = field(default_factory=dict)   # node_id -> line
    unvoiced: "list[str]" = field(default_factory=list)      # node_ids
    intro: str = ""


def _or_group(node_id: str, or_roots: "list[str]") -> "str | None":
    for i, root in enumerate(or_roots):
        if node_id.startswith(root + ".") or node_id == root:
            return f"g{i}"
    return None


def tree_facts(tree: DecisionTree) -> "list[dict]":
    """The must-voice leaves as typed fact dicts, with or-group tags
    (the boolean shape must survive into language — the LDA lesson)."""
    or_roots = [n.node_id for n in tree.nodes if n.kind == "or"]
    facts = []
    for node in tree.nodes:
        if not node.must_voice:
            continue
        fact = node.to_dict()
        fact.pop("children", None)
        group = _or_group(node.node_id, or_roots)
        if group:
            fact["or_group"] = group
        facts.append(fact)
    return facts


def _fact_line(i: int, fact: dict) -> str:
    parts = [f"{i}| context={fact.get('context')}", f"op={fact.get('op')}"]
    cols = fact.get("columns") or []
    if len(cols) >= 2:
        parts.append(f"columns={','.join(cols[:4])}")
    elif fact.get("column"):
        parts.append(f"column={fact['column']}")
    elif cols:
        parts.append(f"columns={cols[0]}")
    if fact.get("operands"):
        parts.append(f"values={','.join(fact['operands'][:15])}")
    if fact.get("or_group"):
        parts.append(f"or-group={fact['or_group']}")
    expr = (fact.get("expression_sql") or "")[:200]
    parts.append(f'predicate="{expr}"')
    return " ".join(parts)


def subject_from_facts(facts: "list[dict]",
                       dict_lines: "list[str] | None" = None) -> str:
    """DESC-VOICE-1 item 2: the SUBJECT to name, derived from the
    typed FACTS (never from SQL — clause 2's guarantee holds). The
    columns the decisions touch say what a row is; 'records' only
    when nothing identifies it, and that fallback is a signal."""
    blob = " ".join(
        str(f.get("column") or "") + " " + str(f.get("text") or "")
        + " " + str(f.get("expression") or "")
        for f in (facts or [])).lower()
    blob += " " + " ".join(dict_lines or []).lower()
    for token, subject in (
            ("encounter", "encounters"), ("visit", "encounters"),
            ("admission", "encounters"), ("appt", "appointments"),
            ("appointment", "appointments"),
            ("order", "orders"), ("med", "medication orders"),
            ("claim", "billing records"), ("cpt", "billing records"),
            ("lab", "lab results"), ("result", "lab results"),
            ("patient", "patients"), ("member", "patients")):
        if token in blob:
            return subject
    return "records"


def build_fact_prompt(name: str, facts: "list[dict]",
                      deps: "list[tuple[str, str]] | None" = None,
                      dict_lines: "list[str] | None" = None) -> str:
    """Clause 2's mechanical guarantee lives in this signature: there is
    no parameter through which a SQL statement could arrive."""
    deps_block = ""
    if deps:
        lines = "\n".join(f"- {n}: {d}" for n, d in deps)
        deps_block = f"It builds on these already-described steps:\n{lines}\n\n"
    dict_block = ""
    if dict_lines:
        entries = "\n".join(dict_lines[:_MAX_DICT_LINES])
        dict_block = ("Data dictionary (translate identifiers using "
                      f"these):\n{entries}\n\n")
    facts_block = "\n".join(
        _fact_line(i + 1, f) for i, f in enumerate(facts)) or "(none)"
    return _FACT_HEADER.format(
        name=name, deps_block=deps_block, dict_block=dict_block,
        facts_block=facts_block,
        subject=subject_from_facts(facts, dict_lines))


_NUMBERED = re.compile(r"^\s*(\d+)\|\s*(.+?)\s*$")


def translate_tree(tree: DecisionTree, dict_lines: "list[str]",
                   describe, name: str = "step",
                   deps: "list[tuple[str, str]] | None" = None,
                   ) -> TranslationResult:
    """τ: facts -> language, with the ledger enforced. The output text is
    ALWAYS complete: LLM lines where the model voiced a fact, template
    floor lines (marked nowhere — they are simply true) where it did
    not; the unvoiced list records the misses for observability."""
    facts = tree_facts(tree)
    result = TranslationResult()
    if not facts:
        # A projection-only step (no decision sites). Deterministic,
        # stilted, TRUE — no describe call, nothing to fabricate.
        # Known enrichment gap (phase-3+ candidate): computed SELECT
        # expressions are not yet facts, so their narration is lost
        # relative to the old raw-SQL prompt; the trade is blindness.
        from src.tree.render import render_template
        result.text = render_template([], step_name=name)
        return result
    response = describe(build_fact_prompt(name, facts, deps, dict_lines))
    intro_lines: "list[str]" = []
    voiced: "dict[int, str]" = {}
    for line in (response or "").splitlines():
        m = _NUMBERED.match(line)
        if m:
            voiced[int(m.group(1))] = m.group(2)
        elif line.strip() and not voiced:
            intro_lines.append(line.strip())
    result.intro = " ".join(intro_lines)
    bullets = []
    for i, fact in enumerate(facts, start=1):
        node_id = fact["node_id"]
        if i in voiced:
            result.ledger[node_id] = voiced[i]
            bullets.append(f"- {voiced[i]}")
        else:
            result.unvoiced.append(node_id)
            bullets.append(render_fact(fact))
    result.text = "\n".join(
        ([result.intro] if result.intro else []) + bullets)
    return result
