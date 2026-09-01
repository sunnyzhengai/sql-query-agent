"""Bottom-up description generation over the calculation DAG (ADR 0019).

A CTE is the smallest certified unit of business definition. Descriptions
are generated in topological order — every step's direct dependencies are
described before the step itself — then each metric's description is
composed from its ROOT steps' descriptions (summaries of summaries, never
raw SQL walls).

This module is pure orchestration: ordering, prompts, content-hash caching.
The LLM is a callback `describe(prompt) -> str`, so tests run with a fake,
devtools plugs in a local OpenAI-compatible endpoint, and production plugs
in the customer's Azure OpenAI — the Data Agent is a CONSUMER of these
descriptions, never the generator.

Grounding rule: a step's prompt contains its OWN sql fragment plus only the
names+descriptions of its direct dependencies (context, not content), so a
bad description cannot cascade up the chain.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable

from src.graph.serialization import rows_to_edges, rows_to_nodes
from src.models import EdgeType, NodeLayer

# Bump when a prompt changes: the version is part of every cache key,
# so a prompt upgrade automatically regenerates every description on
# the next 07 run — no flags, no manual cache wipe (live find
# 2026-08-13: vague descriptions survived a rerun because the cache
# key knew only the SQL, not the prompt that read it).
# v3 (live find 2026-08-14): v2 kept actual values but also kept raw
# warehouse identifiers — the fix is grounded translation material
# (the data dictionary the graph already holds) plus a ban on raw
# identifiers in the output.
# v4 hardened the SQL-reading prompt after the fabrication trace.
# v5 (ADR 0044 phase 2, clauses 2+5): the SQL-reading step prompt is
# DELETED — the step path translates typed tree facts via
# src/tree/translate.py; the LLM never sees a SQL statement again.
# TREE_CONTRACT_VERSION rides in the version so tightening the tree
# contract regenerates everything it governs.
from src.tree import TREE_CONTRACT_VERSION
from src.tree.extract import build_decision_tree
from src.tree.translate import translate_tree

# v6 (2026-08-21, walk find 2): the metric-grain scope rule — the
# bump invalidates every cached description so poisoned "without
# applying any filtering decisions" text cannot survive the next run.
PROMPT_VERSION = f"6.t{TREE_CONTRACT_VERSION}"

MEASURE_PROMPT = (
    "You are documenting a Power BI DAX {expression_type} for a business "
    "audience of clinicians and executives.\n"
    "Measure name: {name}\n"
    "Defined in report: {report_name}\n"
    "{dict_block}"
    "DAX expression:\n{expression}\n\n"
    "Write ONE sentence (max 30 words) stating what this calculates in "
    "business terms. Then, if the DAX makes decisions, add one line per "
    "decision, each starting with '- ': filters, thresholds, time "
    "windows, and conditions. Keep the literal VALUES that define each "
    "decision — codes, numbers, statuses — with the business meaning "
    "beside each when the data dictionary above provides one. NEVER "
    "show raw table or column identifiers in the output — use the "
    "dictionary description or a plain phrase instead. Never write "
    "vague fillers such as 'specific', 'specified', 'certain', or "
    "'various' in place of a value. Ground every line in the DAX above. "
    "No patient identifiers, no preamble."
)

METRIC_PROMPT = (
    "You are documenting the certified business metric {metric_name}.\n"
    "Its calculation is assembled from these final steps (each already "
    "described in business terms):\n{roots_block}\n"
    "It draws on {step_count} calculation steps in total, whose "
    "conditions comprise {decision_count} filtering/branching decision "
    "sites.\n\n"
    "Write a concise business description: first, one sentence stating "
    "what this metric reports or measures, grounded strictly in the step "
    "descriptions and the metric name. Then a blank line, then "
    "'Business logic:' followed by 3-6 bullets covering the population "
    "included, time windows, clinical criteria or thresholds, and how the "
    "outcome is calculated — in business terms, grounded ONLY in the step "
    "descriptions above. Bullets must keep the actual values, codes, "
    "thresholds, and time windows the step descriptions name — never "
    "generalize them away, and never write vague fillers such as "
    "'specific', 'specified', 'certain', or 'various' in place of a "
    "value. Do not state purposes, benefits, or decisions "
    "the metric supports unless a step description states them — no "
    "filler like 'supports decision-making' or 'improves outcomes'. "
    "If the decision-site count above is greater than zero, NEVER "
    "claim the metric applies no filters or no filtering criteria — "
    "such absence claims are true only of a single step, never of the "
    "metric; instead say the detailed criteria live in its "
    "{decision_count} decision sites. "
    "Plain text only: no greetings, no markdown headers, no bold, no "
    "trailing spaces, no invented details."
)

# Observation only (never a retry loop): generated text that hides a
# value behind a filler word is flagged for the run report / dashboard.
_VAGUE_FILLERS = re.compile(
    r"\b(specific|specified|certain|various)\b", re.IGNORECASE)

# Raw-identifier smell in OUTPUT text: SNAKE_CASE_CAPS columns,
# #temp tables, backticked/dotted code refs (live find 2026-08-14:
# ADT_DEPARTMENT_ID / #SDX / `pd.PatEncCSNID` all over the workbench).
_RAW_IDENTIFIERS = re.compile(
    r"(#\w+|`[^`]+`|\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b)")




# --- The grounding gate (2026-08-19, TRACE_USP_ED_SEPSIS) -------------
# Field-proven failure modes in production descriptions: (1) SELECTed
# columns hallucinated into filters ("excludes pending or cancelled"
# with no such condition anywhere), (2) invented literal codes
# ("flowsheet IDs 123 and 456" vs the real 900112/900111). The prompt
# already forbade both; prompt instructions are intent — only
# mechanical verification survives (the notebook-contract lesson).

_OUT_NUMBERS = re.compile(r"\d{2,}")
_OUT_QUOTED = re.compile(r"'([^']{1,40})'")
_FILTER_CLAIM = re.compile(
    r"(?i)\b(exclud\w*|includes? only|only includ\w*|filters?\b|"
    r"requir\w+|must have|limited to|restrict\w*)\b")
_CLAIM_STOPWORDS = frozenset(
    "encounters includes include included excludes exclude excluded "
    "filters filter filtered records results patients patient orders "
    "information department departments emergency hospital associated "
    "between during where which their those based table tables step "
    "steps only that this with from have been were each every there "
    "measurements medications details specific specified certain "
    "various".split())


# --- P0-a (DESC-GATE-2, ordered 2026-08-31): TABLE + GRAIN claims --
# The two classes the value/filter checks cannot see. A wrong GRAIN
# claim is the most dangerous description error we can ship: it
# reads fluent and it is false ("counts patients" over a visit-grain
# query). A wrong TABLE claim invents provenance.

# FROM/JOIN/UPDATE/INTO targets — the tables a fragment actually
# touches. Aliases and schema prefixes are stripped to the bare name
# (the alias-never-faces-the-steward rule from CONSOLE-4c).
# real estates read TEMP TABLES (#Staging) and bracketed identifiers
# as often as plain names (P0-c corpus find on Clarity-shaped SQL)
# READS only. INTO/UPDATE name a WRITE TARGET, not a source — a
# SELECT…INTO #X does not read #X, and listing it made a step
# appear to read itself (DESC-TEMP-1 live find).
_FROM_TABLES = re.compile(
    r"(?is)\b(?:FROM|JOIN|APPLY)\s+"
    r"([#@]?\[?[A-Za-z_][\w]*\]?(?:\.\[?[A-Za-z_][\w]*\]?){0,2})")
# a CTE name is not a base table — it is defined in the same text
_CTE_NAMES = re.compile(r"(?is)(?:WITH|,)\s*([A-Za-z_][\w]*)\s+AS\s*\(")

# the entity words a description may claim to count, and the column
# tokens that evidence each. Word-grain, never question shapes.
_GRAIN_WORDS = {
    "patient": ("patient", "member", "person", "mrn"),
    "visit": ("visit", "encounter", "enc_", "_enc", "admission",
              "appointment", "appt", "stay"),
    "order": ("order", "prescription", "med_order"),
    "claim": ("claim", "billing", "cpt", "charge"),
    "result": ("result", "lab", "observation"),
}
_GRAIN_CLAIM = re.compile(
    r"(?i)\b(?:counts?|per|one row per|number of|distinct)\s+"
    r"(?:the\s+)?([a-z]+?)s?\b")


def _bare(name: str) -> str:
    """The comparable table name: schema and brackets stripped, the
    temp-table marker KEPT (#Staging and Staging are different
    objects to a reader, and both must be recognisable)."""
    last = name.split(".")[-1].strip()
    return last.strip("[]").lower()


def parsed_tables(fragment: str) -> "set[str]":
    """The base tables a fragment reads — FROM/JOIN targets minus the
    CTE names it defines itself. Approximate by design and used only
    to REFUSE claims about tables that appear nowhere."""
    ctes = {_bare(c) for c in _CTE_NAMES.findall(fragment or "")}
    return {_bare(m) for m in _FROM_TABLES.findall(fragment or "")
            if _bare(m) not in ctes}


def parsed_grain(fragment: str) -> "set[str]":
    """The entity grain(s) the fragment's KEY columns evidence.

    Precedence, strongest evidence first (the parser decides which
    columns define a row, not prose):
      1. DISTINCT / GROUP BY columns — they DEFINE the row;
      2. otherwise the SELECT list's *_ID columns — the row's keys;
      3. otherwise nothing: an unknown grain refuses no claim
         (absence of evidence is not evidence).
    When (1) or (2) yields any entity, that set is the grain — a
    PATIENT_ID also present in a visit-keyed select does not make
    the query patient-grain."""
    frag = fragment or ""
    explicit = " ".join(re.findall(
        r"(?is)\b(?:DISTINCT|GROUP\s+BY)\b(.{0,160})", frag))
    source = explicit if explicit.strip() else " ".join(re.findall(
        r"(?is)\bSELECT\b(.*?)\bFROM\b", frag))
    # KEY columns only — an *_ID / *_KEY / *_NO column names the row.
    # The table alias is stripped first: FROM ENCOUNTER_DIAGNOSIS ED
    # must not make every column look encounter-grained (dry-run find,
    # P0-b corpus: the table NAME was leaking into key matching).
    ids = re.findall(r"(?i)\b(?:[\w\[\]]+\.)?([\w\[\]]*"
                     r"(?:_ID|_KEY|_NO|_NUM))\b", source)
    keys_low = " ".join(ids).lower()
    found = set()
    for entity, tokens in _GRAIN_WORDS.items():
        if any(tok in keys_low for tok in tokens):
            found.add(entity)
    return found


def _grain_violations(text: str, fragment: str) -> "list[str]":
    evidence = parsed_grain(fragment)
    if not evidence:
        return []          # unknown grain refuses nothing
    out = []
    for claim in set(_GRAIN_CLAIM.findall(text)):
        claimed = claim.lower().rstrip("s")
        if claimed not in _GRAIN_WORDS:
            continue       # not a grain word — other checks own it
        if claimed not in evidence:
            out.append(
                f"grain claim {claim!r} contradicts the parsed grain "
                f"({', '.join(sorted(evidence))})")
    return out


def _table_violations(text: str, fragment: str,
                      dict_lines: "list[str] | None") -> "list[str]":
    reads = parsed_tables(fragment)
    if not reads:
        return []
    # a claim names a table when it uses a TABLE-SHAPED token
    # (UPPER_SNAKE or a known read) — prose nouns are not claims
    dict_blob = " ".join(dict_lines or []).lower()
    out = []
    for token in set(re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b",
                                text)):
        bare = _bare(token)
        if bare in reads:
            continue
        if bare in dict_blob or bare in (fragment or "").lower():
            continue       # named in the source or its dictionary
        out.append(
            f"ungrounded table claim: {token!r} — the fragment reads "
            f"{', '.join(sorted(reads)) or 'no table'}")
    return out


# --- DESC-VOICE-1 (Sunny's grading, 2026-08-31) ---------------------
# Her verdict on ACCURACY was clean; the failures were VOICE. A
# steward's field must not carry a developer's sentence: the source
# objects are already carried by the RELATIONSHIP (landing matrix
# §1a), so the sentence never needs them.

_TECH_WORDS = (
    "temporary table", "temp table", "table", "cte",
    "common table expression", "join", "joins", "joined", "select",
    "subquery", "query", "dataset", "data set", "column", "columns",
    "row", "rows", "schema", "index",
)
# the word must be the SUBJECT, not part of a computation's name:
# "Row_Number" / "row number" describes a real ranking the SQL does,
# while "the rows" is developer voice (P0-c variance find — the
# false positive emptied an otherwise-honest description)
_TECH_SUBJECT = re.compile(
    r"(?i)(?:^|[-\s(])(?:the\s+)?(" + "|".join(_TECH_WORDS)
    + r")\b(?![\s_-]*(?:number|num|count|numbering))")
_HASH_OBJECT = re.compile(r"#\w+")
# "X (ACRONYM)" or "ACRONYM (expansion)" — the model teaching us
# medicine from its own knowledge rather than from the source
_ACRONYM_GLOSS = re.compile(
    r"([A-Za-z][A-Za-z\s/-]{3,40}?)\s*\(([A-Z]{2,6})\)"
    r"|\b([A-Z]{2,6})\s*\(([A-Za-z][A-Za-z\s/-]{3,40}?)\)")


def voice_violations(text: str, fragment: str,
                     dict_lines: "list[str] | None" = None
                     ) -> "list[str]":
    """The business-voice rules. Not accuracy — AUDIENCE."""
    out: "list[str]" = []
    ground = ((fragment or "") + "\n"
              + "\n".join(dict_lines or [])).lower()
    for obj in set(_HASH_OBJECT.findall(text)):
        out.append(
            f"technical object in a business description: {obj!r} — "
            "the source object is carried by the relationship, not "
            "the sentence")
    for m in _TECH_SUBJECT.finditer(text):
        out.append(
            f"technical vocabulary in a business description: "
            f"{m.group(1)!r} — say what is included, not how the "
            "SQL assembles it")
    # an acronym may be EXPANDED only from the source or dictionary
    for m in _ACRONYM_GLOSS.finditer(text):
        expansion = (m.group(1) or m.group(4) or "").strip()
        acronym = (m.group(2) or m.group(3) or "").strip()
        if not expansion or not acronym:
            continue
        head = expansion.split()[0].lower().rstrip("s")
        if len(head) >= 4 and head not in ground:
            out.append(
                f"ungrounded acronym expansion: {acronym!r} expanded "
                f"as {expansion!r}, which appears nowhere in the "
                "source or dictionary — print the acronym as written")
    return out


# DESC-VOICE-2 (Sunny's second read): the gate stops LIES, it does
# not stop EMPTINESS. A description that says "Encounters are
# included when… critical for tracking treatment protocols" is
# unfalsifiable purpose-speak. The rule: say WHAT is included and
# on WHAT VALUES; never say WHY the business does it — purpose is
# the steward's contribution, and claiming it is how a
# machine-written field starts lying politely.
_PURPOSE_TAIL = re.compile(
    r"(?i)\b(?:"
    r"critical (?:for|to)|essential (?:for|to)|important (?:for|to)|"
    r"key (?:for|to)|vital (?:for|to)|"
    r"ensur\w+|allow\w+ (?:for|us|them)|enabl\w+|facilitat\w+|"
    r"align\w+ with|help\w* (?:to )?(?:identify|ensure|track|"
    r"capture|target)|"
    r"support\w* (?:the )?(?:analysis|tracking|monitoring|quality)|"
    r"provid\w+ (?:a )?(?:clear|comprehensive|insight)|"
    r"for (?:quality|reporting|analysis|tracking) (?:metrics|"
    r"purposes)|"
    r"so that|in order to|which is useful|thereby|"
    r"relevant (?:cases|records|data) are (?:captured|considered)|"
    r"comprehensive view|effective\w* (?:tracking|monitoring)"
    r")\b")


# a prompt placeholder echoed into the output is the instruction
# leaking through as data (P0-c find: "(first: <first_value>, last:
# <last_value>)" reached a steward-facing description)
_PLACEHOLDER = re.compile(r"<[a-z_]{3,24}>")


def placeholder_violations(text: str) -> "list[str]":
    return [f"prompt placeholder echoed: {m!r} — the instruction "
            "leaked into the description as data"
            for m in set(_PLACEHOLDER.findall(text))]


def purpose_violations(text: str, fragment: str) -> "list[str]":
    """DESC-VOICE-2 item 3: purpose speculation is banned unless the
    SOURCE states it (a comment we can quote)."""
    ground = (fragment or "").lower()
    out: "list[str]" = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _PURPOSE_TAIL.search(line)
        if not m:
            continue
        phrase = m.group(0).lower()
        if phrase in ground:          # the source says it; quote ok
            continue
        out.append(
            f"purpose speculation: {m.group(0)!r} in {line[:60]!r} — "
            "say WHAT is included and on WHAT VALUES; why is the "
            "steward's to write")
    return out


_GRAIN_SUBJECT = {
    "patient": "patients", "visit": "encounters",
    "order": "medication orders", "claim": "billing records",
    "result": "lab results",
}


def subject_for(fragment: str) -> str:
    """The SUBJECT a description should name, from the parsed grain
    (DESC-VOICE-1 item 2). 'records' only when grain is unknown —
    and that fallback is a signal worth logging."""
    grain = parsed_grain(fragment)
    for key in ("patient", "visit", "order", "claim", "result"):
        if key in grain:
            return _GRAIN_SUBJECT[key]
    return "records"


def _condition_text(fragment: str) -> str:
    """The parts of the SQL that actually DECIDE: windows of text after
    WHERE / ON / HAVING / AND / WHEN keywords. Approximate by design —
    used to tell 'filtered on' apart from 'merely selected'."""
    return " ".join(
        m.group(1)
        for m in re.finditer(
            r"(?is)\b(?:WHERE|HAVING|ON|AND|WHEN)\b(.{0,240})", fragment)
    )


def grounding_violations(
    text: str, fragment: str, dict_lines: "list[str] | None" = None,
    dialect: str = "sql", voice: bool = True,
) -> "list[str]":
    """Deterministic checks of a generated description against the ONE
    source it claims to describe. Returns human-readable violations;
    empty list = grounded.

    dialect: "sql" applies the full check set. "dax"/"prose" skip the
    selected-not-filtered heuristic — it reads SQL structure (WHERE/ON
    windows vs SELECT list), which does not exist in a DAX expression
    or in composed prose (field find, tenant 600 run 2026-08-20: a
    legitimate CALCULATE filter was stripped as 'selected-not-
    filtered' until the whole description emptied). Value grounding
    (checks 1) applies to every dialect."""
    violations: "list[str]" = []
    ground = (fragment or "") + "\n" + "\n".join(dict_lines or [])
    ground_low = ground.lower()
    conditions = (ground_low if dialect != "sql"
                  else _condition_text(fragment or "").lower())

    # 1) every literal value in the output must exist in the source
    for num in set(_OUT_NUMBERS.findall(text)):
        if num not in ground:
            violations.append(f"ungrounded value: {num!r} not in the SQL")
    for quoted in set(_OUT_QUOTED.findall(text)):
        toks = _OUT_NUMBERS.findall(quoted)
        probe = toks[0] if toks else quoted
        if probe and probe.lower() not in ground_low:
            violations.append(f"ungrounded value: '{quoted}' not in the SQL")

    # 2) filter-claims need support in the DECIDING part of the SQL
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- ") or not _FILTER_CLAIM.search(line):
            continue
        terms = [w for w in re.findall(r"[a-z]{5,}", line.lower())
                 if w not in _CLAIM_STOPWORDS]
        if not terms:
            continue
        in_fragment = [w for w in terms if w in ground_low]
        in_conditions = [w for w in in_fragment if w in conditions]
        has_literal = any(n in ground for n in _OUT_NUMBERS.findall(line))
        if not in_fragment and not has_literal:
            violations.append(f"ungrounded filter claim: {line!r}")
        elif in_fragment and not in_conditions and not has_literal:
            violations.append(
                f"selected-not-filtered: {line!r} — the concept appears "
                f"only in the SELECT list, never in a condition")

    # 3) TABLE claims (P0-a): only tables the fragment reads
    # 4) GRAIN claims (P0-a): the counted entity must match the keys
    if dialect == "sql":
        violations.extend(_table_violations(text, fragment, dict_lines))
        violations.extend(_grain_violations(text, fragment))
    # 5) VOICE (DESC-VOICE-1): audience, not accuracy — a steward's
    # field must not carry a developer's sentence. Skipped with
    # voice=False for MACHINE-COMPOSED text (the template fallback
    # is stilted truth by design; policing its voice would floor
    # the floor).
    if voice:
        violations.extend(voice_violations(text, fragment, dict_lines))
        violations.extend(purpose_violations(text, fragment))
        violations.extend(placeholder_violations(text))
    return violations


def enforce_grounding(
    text: str, fragment: str, dict_lines: "list[str] | None" = None,
    dialect: str = "sql",
) -> "tuple[str, list[str]]":
    """Surgical fallback after a failed retry: strip the violating
    lines, keep grounded content. If the remaining text still violates
    (bad summary sentence), drop everything — absence over fabrication.
    Returns (clean_text_or_empty, removed_violations)."""
    violations = grounding_violations(text, fragment, dict_lines, dialect)
    if not violations:
        return text, []
    bad_lines = {v.split(": ", 1)[1].split(" — ")[0].strip("'\"")
                 for v in violations if ": '" in v or ": \"" in v}
    kept = []
    for line in text.splitlines():
        if any(repr(line.strip()) == b or line.strip() == b.strip("'")
               for b in bad_lines):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    if cleaned and not grounding_violations(cleaned, fragment, dict_lines,
                                            dialect):
        return cleaned, violations
    return "", violations


def step_content_hash(fragment: str, dep_names: "list[str]",
                      dict_lines: "list[str] | None" = None) -> str:
    payload = (
        PROMPT_VERSION + "\n" + (fragment or "")
        + "\n--deps--\n" + "\n".join(sorted(dep_names))
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def measure_content_hash(name: str, expression: str,
                         dict_lines: "list[str] | None" = None) -> str:
    payload = (
        PROMPT_VERSION + "\n--measure--\n" + name + "\n" + (expression or "")
        + "\n--dict--\n" + "\n".join(dict_lines or [])
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def metric_content_hash(metric_name: str, roots: "list[tuple[str, str]]",
                        step_count: int, decision_count: int = 0) -> str:
    payload = (
        PROMPT_VERSION + "\n" + metric_name + f"\n{step_count}\n"
        + f"{decision_count}\n"
        + "\n".join(f"{n}\t{d}" for n, d in sorted(roots))
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


@dataclass
class DescriptionResult:
    descriptions: "dict[str, str]" = field(default_factory=dict)  # node_id -> text
    cache_hits: int = 0
    generated: int = 0
    failed: "list[str]" = field(default_factory=list)
    # (node_id, "reason_code: detail") — the WHY behind every failed
    # node, persisted to ops_fallout by 600 (field find 2026-08-20:
    # four failures whose causes existed only in printed output)
    failed_reasons: "list[tuple[str, str]]" = field(default_factory=list)
    vague: "list[str]" = field(default_factory=list)   # filler-word flags
    jargon: "list[str]" = field(default_factory=list)  # raw-identifier flags
    # grounding gate (2026-08-19): (node_id, violations) that survived a
    # corrective retry — the offending lines were stripped or the whole
    # description dropped; absence over fabrication.
    ungrounded: "list[tuple[str, list[str]]]" = field(default_factory=list)
    # (step_id, count): facts the translator failed to voice — their
    # lines came from the deterministic template floor (clause 5); the
    # text stays complete, the miss stays counted.
    unvoiced: "list[tuple[str, int]]" = field(default_factory=list)

    def fail(self, node_id: str, reason: str) -> None:
        self.failed.append(node_id)
        self.failed_reasons.append((node_id, reason))


def topological_step_order(nodes: dict, edges: list) -> "list[str]":
    """Transformation node_ids, every direct dependency before its dependent.

    DEPENDS_ON points dependent -> dependency, so emit in DFS post-order.
    Cycles (shouldn't exist; parser output is a DAG) are broken at the
    back-edge — the step is emitted once, grounded in its own fragment.
    """
    dependencies: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dependencies.setdefault(e.source_id, []).append(e.target_id)

    ordered: "list[str]" = []
    done: "set[str]" = set()
    in_progress: "set[str]" = set()

    def visit(node_id: str) -> None:
        if node_id in done or node_id in in_progress:
            return
        in_progress.add(node_id)
        for dep in dependencies.get(node_id, []):
            visit(dep)
        in_progress.discard(node_id)
        done.add(node_id)
        ordered.append(node_id)

    for node_id, node in sorted(nodes.items()):
        if node.layer == NodeLayer.TRANSFORMATION:
            visit(node_id)
    return ordered


MAX_DICT_LINES = 30


def dictionary_for_step(
    step_id: str, nodes: dict, tech_map: "dict[str, list[str]]",
    columns_map: "dict[str, list[str]]", fragment: str,
) -> "list[str]":
    """Dictionary lines for the tables a step touches, plus only the
    COLUMNS the fragment actually references (whole-table column lists
    would drown the prompt). Pure selection — the dictionary text
    itself is the customer's own, from graph_nodes."""
    frag = (fragment or "").lower()
    lines: "list[str]" = []
    for table_id in sorted(tech_map.get(step_id, [])):
        table = nodes.get(table_id)
        if table is None:
            continue
        if (table.description or "").strip():
            lines.append(f"- {table.name}: {table.description.strip()}")
        for col_id in sorted(columns_map.get(table_id, [])):
            col = nodes.get(col_id)
            if col is None or not (col.description or "").strip():
                continue
            if col.name.lower() in frag:
                lines.append(f"  - {col.name}: {col.description.strip()}")
    return lines


def build_measure_prompt(
    name: str, expression: str, expression_type: str,
    report_name: str, dict_lines: "list[str] | None" = None,
) -> str:
    if dict_lines:
        entries = "\n".join(dict_lines[:MAX_DICT_LINES])
        dict_block = (
            "Data dictionary for the columns this DAX references "
            f"(translate identifiers using these):\n{entries}\n\n"
        )
    else:
        dict_block = ""
    return MEASURE_PROMPT.format(
        name=name, expression=expression or "(none)",
        expression_type=("calculated column" if expression_type == "calculated_column"
                         else "measure"),
        report_name=report_name or "(unknown)", dict_block=dict_block,
    )


def build_metric_prompt(metric_name: str, roots: "list[tuple[str, str]]",
                        step_count: int, decision_count: int = 0) -> str:
    roots_block = "\n".join(f"- {n}: {d}" for n, d in roots) or "- (no described steps)"
    return METRIC_PROMPT.format(
        metric_name=metric_name, roots_block=roots_block,
        step_count=step_count, decision_count=decision_count,
    )


# Walk corpse (Sunny, 2026-08-21 evening — find 2): metric
# descriptions claimed "without applying any filtering decisions" on
# metrics carrying HUNDREDS of decision sites (427 on
# USP_Severe_Sepsis) — the final_select step's true no-WHERE fact
# over-scoped to the whole metric, and the engine faithfully repeated
# the poisoned text. Sunny's rule: a metric-grain description may not
# make absence-of-filtering claims scoped beyond its step; when
# decision sites exist, the description voices their existence and
# count.
_ABSENCE_OF_FILTERING = re.compile(
    r"(?i)\b(?:without|no|not)\b[^.\n]{0,60}?\bfilter")


def metric_scope_violations(text: str, decision_count: int) -> "list[str]":
    """Deterministic metric-grain scope check (find 2). Empty list =
    no over-scoped absence claim."""
    if decision_count <= 0:
        return []
    out = []
    for line in text.splitlines():
        if _ABSENCE_OF_FILTERING.search(line):
            out.append(
                f"over-scoped absence claim: {line.strip()!r} — this "
                f"metric carries {decision_count} decision sites; an "
                "absence-of-filtering fact is true only of a single "
                "step, never of the metric")
    return out



_RETRY_NOTE = (
    "\n\nYour previous draft was REJECTED by an automatic grounding "
    "check for these violations:\n{violations}\n"
    "Rewrite it. Every value must appear in the SQL above; describe a "
    "column as a filter ONLY if it appears in a WHERE / JOIN ON / "
    "HAVING / CASE WHEN condition; name ONLY tables the SQL reads; "
    "state the counted entity ONLY as the key columns define it "
    "(do not say patients when the row is a visit); write for a "
    "STEWARD, not a developer — never mention tables, temp tables, "
    "joins, columns, queries or datasets, and never expand an "
    "acronym the source does not expand; drop any claim you cannot "
    "ground."
)


def _grounded_describe(
    describe, prompt: str, fragment: str,
    dict_lines: "list[str] | None", dialect: str = "sql",
) -> "tuple[str, list[str]]":
    """describe() + gate + ONE corrective retry + surgical fallback.
    Returns (text_or_empty, violations_removed)."""
    text = describe(prompt).strip()
    if not text:
        return "", []
    violations = grounding_violations(text, fragment, dict_lines, dialect)
    if not violations:
        return text, []
    note = _RETRY_NOTE.format(
        violations="\n".join(f"- {v}" for v in violations))
    try:
        retry = describe(prompt + note).strip()
    except Exception:  # noqa: BLE001 — retry is best-effort
        retry = ""
    if retry:
        text = retry
    return enforce_grounding(text, fragment, dict_lines, dialect)


def generate_descriptions(
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
    describe: "Callable[[str], str]",
    cache: "dict[str, str] | None" = None,
) -> DescriptionResult:
    """Walk the DAG bottom-up; describe steps, then compose metrics.

    cache maps content_hash -> description and is mutated in place — the
    caller persists it (Delta table on Fabric, JSON locally). The cache
    is the ONLY regeneration authority: keys include PROMPT_VERSION and
    the exact inputs, so a description regenerates precisely when its
    SQL, its dependencies, or the prompt changed — an existing text on
    the node never blocks an upgrade from reaching it.
    """
    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)
    cache = cache if cache is not None else {}
    result = DescriptionResult()

    dep_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TRANSFORM:
            dep_map.setdefault(e.source_id, []).append(e.target_id)
    roots_map: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.CANONICAL_TO_TRANSFORM:
            roots_map.setdefault(e.source_id, []).append(e.target_id)
    tech_map: "dict[str, list[str]]" = {}       # step -> touched tables
    columns_map: "dict[str, list[str]]" = {}    # table -> its columns
    for e in edges:
        if e.edge_type == EdgeType.TRANSFORM_TO_TECHNICAL:
            tech_map.setdefault(e.source_id, []).append(e.target_id)
        elif e.edge_type == EdgeType.TABLE_TO_COLUMN:
            columns_map.setdefault(e.source_id, []).append(e.target_id)

    described: "dict[str, str]" = {}

    for step_id in topological_step_order(nodes, edges):
        node = nodes[step_id]
        fragment = node.properties.get("sql_fragment", "")
        dep_names = [nodes[d].name for d in dep_map.get(step_id, []) if d in nodes]
        dict_lines = dictionary_for_step(
            step_id, nodes, tech_map, columns_map, fragment)
        key = step_content_hash(fragment, dep_names, dict_lines)
        if key in cache:
            described[step_id] = cache[key]
            result.descriptions[step_id] = cache[key]
            result.cache_hits += 1
            continue
        deps = [
            (nodes[d].name, described.get(d, ""))
            for d in dep_map.get(step_id, []) if d in nodes
        ]
        try:
            # Phase 2 (ADR 0044 clauses 2+5): the LLM translates typed
            # tree facts — it never sees the SQL statement. The ledger
            # guarantees completeness: unvoiced facts appear via the
            # deterministic template floor and are counted.
            tree = build_decision_tree(fragment)
            tr = translate_tree(tree, dict_lines, describe,
                                name=node.name, deps=deps)
            if tr.unvoiced:
                result.unvoiced.append((step_id, len(tr.unvoiced)))
            text, removed = enforce_grounding(tr.text, fragment, dict_lines)
        except Exception as err:  # noqa: BLE001 — one bad step must not kill the batch
            result.fail(step_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if removed:
            result.ungrounded.append((step_id, removed))
        if not text:
            result.fail(step_id, "grounded_to_empty: every generated line "
                                 "failed the grounding check")
            continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(step_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(step_id)
        cache[key] = text
        described[step_id] = text
        result.descriptions[step_id] = text
        result.generated += 1

    # Measures (ADR 0040): DAX is business logic — same treatment as SQL
    # steps. Independent of the step DAG; grounded in its own expression
    # plus the dictionary text of the columns it provably references
    # (MEASURE_TO_COLUMN edges — resolved, never guessed).
    measure_cols: "dict[str, list[str]]" = {}
    for e in edges:
        if e.edge_type == EdgeType.MEASURE_TO_COLUMN:
            measure_cols.setdefault(e.source_id, []).append(e.target_id)

    for node_id, node in sorted(nodes.items()):
        if node.layer != NodeLayer.MEASURE:
            continue
        expression = node.properties.get("dax_expression", "")
        if not expression:
            result.fail(node_id, "no_dax_expression: measure ingested "
                                 "without an expression")
            continue
        dict_lines = []
        for col_id in sorted(measure_cols.get(node_id, [])):
            col = nodes.get(col_id)
            if col is not None and (col.description or "").strip():
                dict_lines.append(f"- {col.name}: {col.description.strip()}")
        key = measure_content_hash(node.name, expression, dict_lines)
        if key in cache:
            result.descriptions[node_id] = cache[key]
            result.cache_hits += 1
            continue
        prompt = build_measure_prompt(
            node.name, expression,
            node.properties.get("expression_type", "measure"),
            node.properties.get("report_name", ""), dict_lines,
        )
        try:
            text, removed = _grounded_describe(
                describe, prompt, expression, dict_lines, dialect="dax")
        except Exception as err:  # noqa: BLE001 — one bad measure must not kill the batch
            result.fail(node_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if removed:
            result.ungrounded.append((node_id, removed))
        if not text:
            result.fail(node_id, "grounded_to_empty: every generated line "
                                 "failed the grounding check")
            continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(node_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(node_id)
        cache[key] = text
        result.descriptions[node_id] = text
        result.generated += 1

    # Metrics: composed from ROOT step descriptions (raw roots-only edges)
    step_count_by_metric: "dict[str, int]" = {}
    decision_count_by_metric: "dict[str, int]" = {}
    for node_id, node in nodes.items():
        if node.layer == NodeLayer.TRANSFORMATION:
            metric_id = node.properties.get("metric_id", "")
            step_count_by_metric[metric_id] = step_count_by_metric.get(metric_id, 0) + 1
        elif node.layer == NodeLayer.DECISION:
            metric_id = node.properties.get("metric_id", "")
            decision_count_by_metric[metric_id] = (
                decision_count_by_metric.get(metric_id, 0) + 1)

    for node_id, node in sorted(nodes.items()):
        if node.layer != NodeLayer.CANONICAL:
            continue
        metric_id = node_id.replace("canonical:", "")
        roots = [
            (nodes[r].name, described.get(r, ""))
            for r in roots_map.get(node_id, []) if r in nodes
        ]
        if not roots:
            result.fail(node_id, "no_root_steps: metric node has no "
                                 "root-step edges to compose from")
            continue
        step_count = step_count_by_metric.get(metric_id, len(roots))
        decision_count = decision_count_by_metric.get(metric_id, 0)
        key = metric_content_hash(node.name, roots, step_count,
                                  decision_count)
        if key in cache:
            result.descriptions[node_id] = cache[key]
            result.cache_hits += 1
            continue
        prompt = build_metric_prompt(node.name, roots, step_count,
                                     decision_count)
        roots_ground = "\n".join(d for _, d in roots)
        # Facts WE put in the prompt are grounded by definition — the
        # gate greps only roots_ground, so the step_count it asked the
        # LLM to voice ('computed in 122 steps') must be in the ground
        # (field find, tenant 600 run 2026-08-20).
        prompt_facts = ([node.name, str(step_count), str(decision_count)]
                        + [n for n, _ in roots])
        try:
            text, removed = _grounded_describe(
                describe, prompt, roots_ground, prompt_facts,
                dialect="prose")
        except Exception as err:  # noqa: BLE001
            result.fail(node_id, f"generation_error: {type(err).__name__}: {err}"[:300])
            continue
        if removed:
            result.ungrounded.append((node_id, removed))
        if not text:
            result.fail(node_id, "grounded_to_empty: every generated line "
                                 "failed the grounding check")
            continue
        # Metric-grain scope rule (walk find 2, Sunny 2026-08-21): one
        # corrective retry, then strip the violating lines; if the
        # remainder still over-scopes, drop the description entirely —
        # absence over poisoned certainty.
        scope_v = metric_scope_violations(text, decision_count)
        if scope_v:
            note = ("\n\nYour previous draft was REJECTED: it makes "
                    "absence-of-filtering claims at metric grain:\n"
                    + "\n".join(f"- {v}" for v in scope_v)
                    + "\nRewrite it without any such claim; say the "
                    "detailed criteria live in the "
                    f"{decision_count} decision sites.")
            try:
                retry = describe(prompt + note).strip()
            except Exception:   # noqa: BLE001 — retry is best-effort
                retry = ""
            if retry and not grounding_violations(
                    retry, roots_ground, prompt_facts, "prose"):
                text = retry
            if metric_scope_violations(text, decision_count):
                kept = [ln for ln in text.splitlines()
                        if not _ABSENCE_OF_FILTERING.search(ln)]
                text = "\n".join(kept).strip()
            result.ungrounded.append((node_id, scope_v))
            if not text or metric_scope_violations(text, decision_count):
                result.fail(node_id,
                            "over_scoped_absence: metric-grain "
                            "no-filtering claim survived retry+strip")
                continue
        if _VAGUE_FILLERS.search(text):
            result.vague.append(node_id)
        if _RAW_IDENTIFIERS.search(text):
            result.jargon.append(node_id)
        cache[key] = text
        result.descriptions[node_id] = text
        result.generated += 1

    return result
