"""Outward stage 1: PRODUCE — graph -> layer-3 machine versions.

The floor composer implements the RATIFIED Floor Grammar
(AIVIA_Design/Floor_Grammar.md, FLOOR_GRAMMAR_VERSION) rule by rule; the grammar version
stamps into every run's basis. The staleness lens IS the worklist
(PROD-2) — nobody hand-picks; ECON v1 (aivia/flows/econ_params.json,
ruled 2026-09-05) paces it: batch, budget, usage-weighted priority
(an empty ledger degrades to worklist order — declared, not silent).

Deterministic composition + bounded smoothing + the gate: the model
never adds a fact; on gate failure or no model THE FLOOR SHIPS
(skeleton_floor — plain but true). Per-artifact atomicity (OPS-2):
one append or a counted absence, never a half-write.
"""
import json
import pathlib
import re
from typing import Any, Callable, Dict, List, Optional

from aivia.flows import gates, run_events
from aivia.graph import kg3_artifacts
from aivia.graph.read_api import ReadApi
from aivia.lenses import anchors, decisions, derivation

ECON = json.loads((pathlib.Path(__file__).parent / "econ_params.json")
                  .read_text())
# 2.0.0 (Phase C, ADR 0077): the POLICY-WALK major — the spine reads
# the meaning twin (composition sentence from source nodes; the
# voicing ledger); leaf voicings survive verbatim (ruling 4b). The
# 24-hour-window bound gains the DATEADD phrase (ADR 0076's
# evidence-ordered overlay: 12 estate uses ordered it) — the line-83
# raw-token corpse from Sunny's gap-check dies here.
# 2.2.0: the ABX FIRST LEG (Sunny): IN/EXISTS subselections voice
# their aggregate reads + restrictive-spine conditions (nested
# membership; OUTER-APPLY interiors and combination arms excluded).
# 2.1.0: the ABX corpse (Sunny's Phase-C gap-check find) — a UNION
# CTE floored as 'no source records are read': COMBINATION scopes now
# map (arms in order, dedup flag), voice per arm, and an unmapped
# query shape floors as its honest counted state, never a claim.
# 2.3.0: R10 — THE REPORT FLOOR (live find #9): file floors compose
# from scopes — deliveries lead, spine voiced, intermediates counted,
# census closes; file ask-index words = the delivery lead.
FLOOR_GRAMMAR_VERSION = "2.3.0"
_PREPOSITIONS = ("of", "on", "per", "for", "in", "at", "by", "with")


# ---- R5: steward words, graph-sourced (v1.3.1 rendering) ----
_BOILERPLATE = re.compile(
    r"(?i)^this\s+(?:column|item|field|table)\s+"
    r"(?:holds|contains|stores|indicates|captures|is)"
    r"(?:\s+details|\s+information)?(?:\s+about)?\s+")
_TOKEN_HEADS = {"id", "code", "number", "identifier", "key", "nbr"}


def _noun_phrase(description: str, column: str) -> str:
    """The R5 rendering, v1.3.1 (the ED-sepsis phrasing corpses):
    1. strip meta-boilerplate leads ('This column holds details
       about ...' describes the column, not the thing);
    2. first sentence, comma-truncated (a trailing clause after a
       comma is commentary, not the subject), article stripped;
    3. '<X> of|for the <Y>': when head(X) is a TOKEN word (id, code,
       number...) the subject IS Y — 'The ID number of the unit ...'
       speaks about the unit; reorder to '<Y> <head(X)>' only when
       BOTH sides are short (visit date, appointment status); long
       phrases stand as written — gluing a head onto them made
       '...it became effective id';
    4. backstop: cut a reduced relative clause at a non-initial
       ' this ' and strip dangling prepositions."""
    first = (description or "").strip().split(". ")[0].rstrip(".").strip()
    if not first:
        return re.sub(r"[_\W]+", " ", column).strip().lower()
    phrase = _BOILERPLATE.sub("", first)
    phrase = phrase.split(",")[0].strip()
    phrase = re.sub(r"^(the|a|an)\s+", "", phrase, flags=re.I)
    m = re.match(r"(?i)^(.*?)\s+(?:of|for)\s+the\s+(.+)$", phrase)
    if m:
        x, y = m.group(1), m.group(2)
        head = x.split()[0].lower()
        if head in _TOKEN_HEADS:
            phrase = y  # the token names the column; Y names the thing
        elif len(x.split()) <= 3 and len(y.split()) <= 3:
            phrase = f"{y} {head}"
    cut = re.search(r"\s+this\s+", phrase)
    if cut and cut.start() > 0:
        phrase = phrase[:cut.start()]
        phrase = re.sub(
            r"\s+(?:in|on|of|for|to|at|by|with|from)$", "", phrase)
    return phrase.lower()


def _pluralize(grain: str) -> str:
    words = grain.split()
    head_idx = len(words) - 1
    for i, w in enumerate(words):
        if w.lower() in _PREPOSITIONS and i > 0:
            head_idx = i - 1
            break
    head = words[head_idx]
    plural = head + ("es" if head.endswith(("s", "x", "ch", "sh"))
                     else "s")
    if head.endswith("sis"):
        plural = head[:-3] + "ses"  # diagnosis -> diagnoses
    words[head_idx] = plural
    return " ".join(words)


class _Voice:
    """Graph-backed voicing context for one scope."""

    def __init__(self, read: ReadApi, tree: Dict[str, Any]):
        self._columns = {n.identity: n.properties
                         for n in read.nodes("column")}
        self._tables = {n.identity: n.properties
                        for n in read.nodes("table")}
        self._params = {p["name"]: p for p in tree.get("parameters", [])}
        self.disagreements: List[str] = []  # declared vs annotation (R8)

    def subject(self, expr) -> str:
        if expr.get("kind") == "column_ref":
            col_id = expr.get("resolves_to") or ""
            desc = self._columns.get(col_id, {}).get("description", "")
            return _noun_phrase(desc, expr["ref"].split(".")[-1])
        # a computed subject voices through the value path (DATEADD
        # overlay, steward words) — raw tokens never face the steward
        phrase = self.value(expr, expr)
        return phrase[4:] if phrase.startswith("the ") else phrase

    def value(self, expr, subject_expr) -> str:
        kind = expr.get("kind")
        if kind == "parameter_ref":
            name = expr["ref"].lstrip("@")
            words = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
            param = self._params.get(name)
            if param:
                return (f"the {words} parameter (default "
                        f"{param['default_logic']} when none is supplied)")
            return f"the {words} parameter"
        if kind == "literal":
            raw = str(expr["value"])
            col_id = subject_expr.get("resolves_to") or ""
            values_map = self._columns.get(col_id, {}).get("values") or {}
            meaning = values_map.get(raw.strip("'"))
            note = expr.get("annotation")
            if meaning:  # R8 precedence: the DECLARED meaning wins
                if note and note.lower() != meaning.lower():
                    self.disagreements.append(
                        f"{raw}: declared '{meaning}' vs source note "
                        f"'{note}'")
                return f"{raw} ('{meaning}')"
            if note:
                return f"{raw} (noted '{note}')"
            return raw
        if kind == "column_ref":
            # a column as a VALUE voices by its steward words too —
            # raw identifiers never face the steward (R5; the line-83
            # corpse: '[#base_pop].ed_departure_time' in prose)
            return f"the {self.subject(expr)}"
        if kind == "case":
            return "a value derived by rule"
        if kind == "function" and expr.get("name", "").upper() \
                == "COALESCE":
            parts = [self.value(a, a) for a in expr.get("args", [])]
            return "the first recorded of " + ", ".join(parts)
        if kind == "function" and expr.get("name", "").upper() in \
                ("LEFT", "RIGHT") and len(expr.get("args", [])) == 2:
            side = ("first" if expr["name"].upper() == "LEFT"
                    else "last")
            n = expr["args"][1].get("value")
            return (f"the {side} {n} characters of "
                    f"{self.value(expr['args'][0], expr['args'][0])}")
        if kind == "function" and expr.get("name", "").upper() == "DATEADD" \
                and len(expr.get("args", [])) == 3:
            # ADR 0076 evidence-ordered overlay: DATEADD earned its
            # phrase (12 estate uses). Unit arg arrives as a column_ref
            # token (HH) — read its raw name, never its resolution.
            unit_words = {"HH": "hour", "HOUR": "hour", "DD": "day",
                          "D": "day", "DAY": "day", "MI": "minute",
                          "MINUTE": "minute", "SS": "second",
                          "WK": "week", "MM": "month", "MONTH": "month",
                          "YY": "year", "YEAR": "year"}
            first = expr["args"][0]
            unit = str(first.get("value") or first.get("ref", "")
                       ).split(".")[-1].upper()
            n = expr["args"][1].get("value")
            base = self.value(expr["args"][2], expr["args"][2])
            if unit in unit_words and n is not None:
                word = unit_words[unit] + ("" if str(n) == "1" else "s")
                return f"{n} {word} after {base}"
        return decisions.render_expr(expr).lower()

    def forbidden_tokens(self, scope) -> List[str]:
        tokens = []
        for ref in scope.get("from_refs", []):
            name = ref.get("table_ref")
            if name:
                tokens.append(name.split(".")[-1])
        for col in decisions.flatten_where(scope.get("where")):
            for role in ("subject", "comparand", "pattern"):
                e = col.get(role)
                if e and e.get("kind") == "column_ref":
                    tokens.append(e["ref"].split(".")[-1])
                    tokens.append(e["ref"])
        return tokens


def _nested_selection_phrase(selection, voice: "_Voice") -> str:
    """Grammar 2.2.0: an IN/EXISTS subselection voices its aggregate
    reads + restrictive-spine conditions in one phrase. Returns ''
    when there is no mapped interior (the pre-sweep pointer wording
    stands) or when the interior is a combination (alternatives
    cannot flatten; the pointer wording stays honest)."""
    scope = (selection or {}).get("scope")
    if not scope or "combination_arms" in scope:
        return ""
    sources = decisions.nested_sources(scope)
    if not sources:
        return ""
    phrases = []
    for ref in sources:
        p = _source_phrase(ref.get("table_ref"),
                           ref.get("resolves_to"), [])
        if p not in phrases:
            phrases.append(p)
    conds = []
    for pred in decisions.nested_membership(scope):
        if decisions.is_degenerate(pred):
            continue
        phrase = _voice_predicate(pred, voice)
        if phrase and phrase not in conds:
            conds.append(phrase)
    out = "a nested selection reading " + ", ".join(phrases)
    if conds:
        joined = "; and ".join(p.rstrip(".")[0].lower() + p.rstrip(".")[1:]
                               for p in conds)
        out += f", where {joined}"
    return out


def _voice_predicate(pred, voice: _Voice) -> str:
    kind = pred["kind"]
    subj_expr = pred.get("subject", {})
    subj = voice.subject(subj_expr)
    if kind in ("COMPARE_GTE", "COMPARE_GT", "COMPARE_LTE", "COMPARE_LT"):
        temporal = "date" in subj or "time" in subj
        verb = {"COMPARE_GTE": "is on or after" if temporal else "is at least",
                "COMPARE_GT": "is after" if temporal else "exceeds",
                "COMPARE_LTE": "is on or before" if temporal else "is at most",
                "COMPARE_LT": "is before" if temporal else "is below"}[kind]
        return (f"The {subj} {verb} "
                f"{voice.value(pred['comparand'], subj_expr)}.")
    if kind == "COMPARE_EQ":
        return (f"The {subj} is "
                f"{voice.value(pred['comparand'], subj_expr)}.")
    if kind == "COMPARE_NEQ":
        return (f"The {subj} is not "
                f"{voice.value(pred['comparand'], subj_expr)}.")
    if kind == "PATTERN_MATCH":
        pattern = str(pred["pattern"].get("value", "")).strip("'")
        if pattern.endswith("%") and "%" not in pattern[:-1] \
                and "_" not in pattern:
            return f"The {subj} starts with '{pattern[:-1]}'."
        if pattern.startswith("%") and "%" not in pattern[1:] \
                and "_" not in pattern:
            return f"The {subj} ends with '{pattern[1:]}'."
        if pattern.startswith("%") and pattern.endswith("%") \
                and "%" not in pattern[1:-1]:
            return f"The {subj} contains '{pattern[1:-1]}'."
        return f"The {subj} matches the pattern '{pattern}'."
    if kind == "IN_LIST":
        members = ", ".join(voice.value(m, subj_expr)
                            for m in pred["comparand_list"])
        return f"The {subj} is one of the values {members}."
    if kind == "RANGE":
        return (f"The {subj} is between "
                f"{voice.value(pred['lower_bound'], subj_expr)} and "
                f"{voice.value(pred['upper_bound'], subj_expr)} (inclusive).")
    if kind == "NULL_CHECK":
        return f"The {subj} has no recorded value."
    if kind == "EXISTS_SELECTION":
        detail = _nested_selection_phrase(pred.get("selection"), voice)
        if detail:
            return f"A matching record exists in {detail}."
        return "A matching record exists in a separately defined selection."
    if kind == "IN_SELECTION":
        # grammar 2.2.0 (Sunny's ABX first-leg find): the value-set
        # pointer gains its CONTENT now that subquery interiors are
        # mapped — the nested selection's reads and its restrictive-
        # spine conditions; OUTER-APPLY interiors stay excluded (an
        # optional lookup never restricts the producing rows)
        detail = _nested_selection_phrase(pred.get("selection"), voice)
        if detail:
            return f"The {subj} is one of the values from {detail}."
        return (f"The {subj} is one of the values defined by another "
                "selection.")
    if kind == "QUANTIFIED_COMPARE":
        quant = ("every row of" if pred.get("quantifier") == "All"
                 else "any row of")
        return (f"The {subj} compares against {quant} another selection.")
    if kind == "OR":
        arms = [_voice_predicate(c, voice).rstrip(".")
                for c in pred["children"]]
        return " or ".join(arms) + "."
    if kind == "NOT":
        inner = _voice_predicate(pred["children"][0], voice).rstrip(".")
        return f"It is not the case that {inner[0].lower()}{inner[1:]}."
    return ""  # remainder predicates voice nothing; they are counted


def _twin_selection(read: ReadApi, tree, scope):
    """The scope's selection node in the stored meaning twin (KG2b) —
    the spine the policy walk reads since grammar 2.0.0."""
    want = scope.get("name") or scope.get("name_key")
    for n in read.nodes("meaning_twin"):
        twin = n.properties.get("twin", {})
        if twin.get("file") != tree.get("name"):
            continue
        for node in twin["nodes"]:
            if node["kind"] == "selection" \
                    and node["content"].get("selection") == want:
                return twin, node
    return None, None


def _source_phrase(name: str, resolved, depth2_counter: List[int]) -> str:
    if resolved and str(resolved).startswith("SAME-TREE"):
        words = re.sub(r"[_\W]+", " ", name.lstrip("#")).strip().lower()
        return (f"the {words} selection defined earlier in this "
                "procedure")
    if name is None:  # an anonymous derived table — depth-1 inline
        return "an inline selection"
    words = re.sub(r"[_\W]+", " ", name.split(".")[-1]).strip().lower()
    return f"{words} records"


def _composition_sentence(read: ReadApi, tree, scope,
                          ledger: Dict[str, int]) -> Optional[str]:
    """The composition sentence (the finding-4 heir; ruling 4c): what
    this selection READS and how the joins compose the population —
    INNER voices as restriction; any OUTER present demotes the wording
    to 'combined with' (voicing an optional match as a restriction
    would lie the other way — the v1.3.0 posture)."""
    refs = scope.get("from_refs", [])
    if not refs:
        return None
    join_kinds = {str(on.get("join_type"))
                  for on in scope.get("join_on", [])}
    # restriction wording needs a LINK: an ON clause, or comma-join
    # keys (col=col) in the WHERE; linkless multi-source = cartesian,
    # voiced neutrally ("combined with") — never a false restriction
    linked = bool(scope.get("join_on")) or any(
        decisions.is_join_key(leaf)
        for leaf in decisions.flatten_where(scope.get("where")))
    inner_only = join_kinds <= {"Inner"} and linked
    phrases = []
    for ref in refs:
        if "derived_scope" in ref:
            phrases.append("an inline selection")
            # depth-2 nesting: translated in full (the twin is total);
            # PROSE inlines depth 1 only — deeper is counted with the
            # revisit trigger (ruled 2026-09-06, the depth cap)
            inner_refs = ref["derived_scope"].get("from_refs", [])
            if any("derived_scope" in r for r in inner_refs):
                ledger["deep_nesting_counted"] = \
                    ledger.get("deep_nesting_counted", 0) + 1
            continue
        phrases.append(_source_phrase(ref.get("table_ref"),
                                      ref.get("resolves_to"), []))
    if not phrases:
        return None
    # 2.3.0 phrasing (truth unchanged, count visible): a RUN of
    # identical source phrases aggregates — "combined with an inline
    # selection" seven times is mechanics, "7 inline selections" is
    # the same fact spoken once
    compressed = []
    i = 0
    while i < len(phrases):
        j = i
        while j < len(phrases) and phrases[j] == phrases[i]:
            j += 1
        n = j - i
        if n == 1:
            compressed.append(phrases[i])
        elif phrases[i] == "an inline selection":
            compressed.append(f"{n} inline selections")
        else:
            compressed.append(f"{phrases[i]} ({n} reads)")
        i = j
    phrases = compressed
    sentence = f"Drawn from {phrases[0]}"
    connector = (", restricted to records also present in "
                 if inner_only and len(join_kinds) > 0
                 else ", combined with ")
    for p in phrases[1:]:
        sentence += connector + p
    return sentence + "."


def voicing_ledger(read: ReadApi, target: str) -> Dict[str, int]:
    """THE VOICING LEDGER (ruling 4a; ADR 0044 clause 5 generalized):
    every membership-grain decision in the scope is VOICED or COUNTED
    — voiced + counted == total, disjoint, queryable. Silent omission
    has no constructible path."""
    tree, scope = None, None
    for t in read.trees().values():
        for s in decisions.named_scopes(t):
            if s["name_key"] == target:
                tree, scope = t, s
    if scope is None:
        raise KeyError(target)
    voice = _Voice(read, tree)
    voiced = counted = 0
    detail: Dict[str, int] = {}
    for pred in decisions.membership_predicates(scope):
        if decisions.is_degenerate(pred):
            counted += 1
            detail["degenerate_policy_silent"] = \
                detail.get("degenerate_policy_silent", 0) + 1
        elif _voice_predicate(pred, voice):
            voiced += 1
        else:
            counted += 1
            detail["remainder_unvoiced"] = \
                detail.get("remainder_unvoiced", 0) + 1
    arms = [scope] + scope.get("combination_arms", [])
    outer = sum(1 for s in arms for on in s.get("join_on", [])
                if str(on.get("join_type")) != "Inner")
    counted += outer
    if outer:
        detail["outer_match_conditions"] = outer
    total = voiced + counted
    return {"voiced": voiced, "counted": counted, "total": total,
            "detail": detail}


def compose_floor(read: ReadApi, target: str) -> str:
    """The ratified grammar, rule by rule, over the graph's facts."""
    tree, scope = None, None
    for t in read.trees().values():
        for s in decisions.named_scopes(t):
            if s["name_key"] == target:
                tree, scope = t, s
    if scope is None:
        raise KeyError(f"no scope {target} in the parsed estate")
    return _compose_scope(read, tree, scope)


def _compose_scope(read: ReadApi, tree, scope,
                   include_lead: bool = True) -> str:
    # An unmapped query shape NEVER floors as a claim — the old walk
    # laundered the counted gap into 'no source records are read'
    # (Sunny's ABX corpse). Absence over fabrication.
    if scope.get("unmapped_shape"):
        return ("The logic of this selection is not yet modeled "
                f"(unmapped query shape: {scope['unmapped_shape']}); "
                "its contents are counted for engineering review, "
                "never described by guess.")
    # COMBINATION (grammar 2.1.0, the ABX corpse): lead from the first
    # arm, the combination fact voiced, each arm's composition and
    # conditions voiced in arm order (arm order is meaning)
    if "combination_arms" in scope:
        arms = scope["combination_arms"]
        dupes = ("duplicates kept" if scope.get("combination_all")
                 else "duplicates removed")
        kind_words = {"Union": "combination",
                      "Except": "difference",
                      "Intersect": "intersection"}
        word = kind_words.get(str(scope.get("combination")),
                              "combination")
        first_arm_lines = _compose_scope(read, tree, arms[0],
                                         include_lead=True).split("\n")
        lines = [first_arm_lines[0],
                 f"This selection is the {word} of {len(arms)} "
                 f"alternative selections ({dupes})."]
        ordinals = ("first", "second", "third", "fourth", "fifth")
        for i, arm in enumerate(arms):
            marker = ordinals[i] if i < len(ordinals) else f"#{i + 1}"
            body = _compose_scope(read, tree, arm, include_lead=False)
            lines.append(f"The {marker} alternative:")
            lines.extend(body.split("\n"))
        return "\n".join(line for line in lines if line)
    voice = _Voice(read, tree)
    tables = {n.identity: n.properties for n in read.nodes("table")}
    # R1 — the lead
    reads_tables, lead_grain = False, None
    for ref in scope.get("from_refs", []):
        rt = ref.get("resolves_to") or ""
        if rt in tables:
            reads_tables = True
            if lead_grain is None and tables[rt].get("grain"):
                lead_grain = tables[rt]["grain"]
    if not include_lead:
        lines = []
    elif scope.get("operation") == "delete":
        # a DELETE shapes a population by REMOVAL — 'a selection'
        # would misstate the act (ledger-close, 2026-09-06)
        ref = scope["from_refs"][0]
        phrase = _source_phrase(ref.get("table_ref"),
                                ref.get("resolves_to"), [])
        lines = [f"This step removes records from {phrase}."]
        lines = ["This step produces derived values; no source records "
                 "are read."]
    elif lead_grain:
        lines = [f"This is a selection of {_pluralize(lead_grain)}."]
    else:
        lines = ["This is a selection of records."]
    # Grammar 2.0.0 — the composition sentence (the finding-4 heir):
    # sources + join composition, from the same facts the twin's
    # source nodes hold; reference phrases, never raw temp names
    ledger_counts: Dict[str, int] = {}
    composition = _composition_sentence(read, tree, scope, ledger_counts)
    if composition:
        lines.append(composition)
    # R2 + R6 — one bullet per membership decision (dedup at PREDICATE
    # IDENTITY grain, v1.1.0 — the ED-sepsis two-alias corpse: two
    # predicates that render alike are still two decisions), degenerate
    # silent. Multi-instance reads carry the instance marker.
    alias_instance: Dict[str, str] = {}
    reads_per_table: Dict[str, List[str]] = {}
    for ref in scope.get("from_refs", []):
        rt = ref.get("resolves_to") or ""
        if rt in tables and ref.get("alias"):
            reads_per_table.setdefault(rt, []).append(ref["alias"])
    ordinals = ("first", "second", "third", "fourth", "fifth", "sixth")
    for rt, aliases in reads_per_table.items():
        if len(aliases) < 2:
            continue
        words = re.sub(r"[_\W]+", " ", rt.rsplit("|", 1)[-1]).strip().lower()
        for i, alias in enumerate(aliases):
            marker = ordinals[i] if i < len(ordinals) else f"#{i + 1}"
            alias_instance[alias] = f"For the {marker} {words} record read: "
    bullets = []
    for pred in decisions.membership_predicates(scope):
        if decisions.is_degenerate(pred):
            continue
        phrase = _voice_predicate(pred, voice)
        if not phrase:
            continue
        note = pred.get("annotation")
        if note:  # R8: attributed, never bare fact
            phrase = (phrase.rstrip(".")
                      + f" (annotated '{note}' in the source).")
        subject_ref = pred.get("subject", {}).get("ref", "")
        alias = subject_ref.split(".")[0] if "." in subject_ref else None
        prefix = alias_instance.get(alias, "")
        if prefix:
            phrase = prefix + phrase[0].lower() + phrase[1:]
        bullets.append(f"- {phrase}")
    # R7 — the honest no-conditions fact
    if not bullets and reads_tables:
        bullets = ["- No membership conditions are applied in this "
                   "selection."]
    return "\n".join(lines + bullets)


def _scope_lead(read: ReadApi, tree, scope) -> str:
    """A scope's lead + composition sentence — the non-bullet head of
    its floor (R10 voices scopes at file grain through this)."""
    lead = []
    for line in _compose_scope(read, tree, scope).split("\n"):
        if line.startswith("- ") or line.endswith("alternative:"):
            break
        lead.append(line)
        if len(lead) == 2:
            break
    return " ".join(lead)


def compose_file_floor(read: ReadApi, target: str) -> str:
    """R10 — THE REPORT FLOOR (grammar 2.3.0, live find #9): a file's
    floor composes from its scopes. Deliveries LEAD, the spine walks
    back to base selections (voiced), intermediates are COUNTED
    (voiced + counted == total extends to file grain), the census
    closes — honest mechanics, never the lead. Deterministic; the
    model adds nothing."""
    tree = None
    for k, t in read.trees().items():
        if k == target or t["name"] == target:
            tree = t
    if tree is None:
        raise KeyError(f"no file {target} in the parsed estate")
    scopes = {sc["name_key"]: sc
              for sc in decisions.named_scopes(tree)}
    deliveries = [st["scope"] for st in tree["statements"]
                  if st.get("emits") and st.get("scope")
                  and st["scope"].get("name_key")]

    lines: List[str] = []
    if not deliveries:
        lines.append("This procedure emits no result set — a "
                     "setup/maintenance script; nothing is delivered "
                     "to a reader.")
    for i, d in enumerate(deliveries):
        prefix = ("This report delivers: " if len(deliveries) == 1
                  else f"This report delivers ({i + 1} of "
                       f"{len(deliveries)}): ")
        lines.append(prefix + _scope_lead(read, tree, d))

    # the spine: every named selection the deliveries draw from,
    # transitively (arms and derived interiors included — a read is
    # a read)
    on_chain: List[str] = []

    def walk(scope):
        for ref in decisions.nested_sources(scope):
            rt = str(ref.get("resolves_to") or "")
            if rt.startswith("SAME-TREE scope "):
                nk = rt.replace("SAME-TREE scope ", "")
                if nk in scopes and nk not in on_chain:
                    on_chain.append(nk)
                    walk(scopes[nk])
    for d in deliveries:
        walk(d)

    def is_base(scope) -> bool:
        refs = decisions.nested_sources(scope)
        return bool(refs) and not any(
            str(r.get("resolves_to") or "").startswith("SAME-TREE")
            for r in refs)
    delivery_keys = {d["name_key"] for d in deliveries}
    chain = [nk for nk in scopes if nk in on_chain]  # tree order
    bases = [nk for nk in chain if is_base(scopes[nk])]
    intermediates = [nk for nk in chain if nk not in bases]
    off_chain = [nk for nk in scopes
                 if nk not in on_chain and nk not in delivery_keys]

    BASE_CAP = 5
    if bases:
        lines.append(f"Built from {len(bases)} base selection(s) "
                     "reading source tables:")
        for nk in bases[:BASE_CAP]:
            name = nk.split("::")[-1]
            lines.append(f"- {name}: "
                         + _scope_lead(read, tree, scopes[nk]))
        if len(bases) > BASE_CAP:
            lines.append(f"- … and {len(bases) - BASE_CAP} more base "
                         "selection(s) — each speaks its own floor.")
    if intermediates:
        lines.append(f"Refined through {len(intermediates)} "
                     "intermediate selection(s) — each speaks its "
                     "own floor.")
    if off_chain:
        lines.append(f"{len(off_chain)} named selection(s) sit "
                     "outside the delivery chain (counted).")
    voiced = len(delivery_keys) + min(len(bases), BASE_CAP)
    counted = (len(intermediates) + len(off_chain)
               + max(0, len(bases) - BASE_CAP))
    lines.append(f"Voicing: {voiced} voiced, {counted} counted, of "
                 f"{len(scopes)} named selections.")

    # the census closes — honest mechanics, never the lead
    names = [nk.split("::")[-1] for nk in scopes]
    lines.append(f"A procedure of {len(tree['statements'])} steps; "
                 f"named selections: "
                 f"{', '.join(names[:12]) or '(none)'}"
                 + (f" … ({len(names) - 12} more)"
                    if len(names) > 12 else "") + ".")
    return "\n".join(lines)


def file_words(read: ReadApi, target: str) -> str:
    """The file's delivery lead — a GRAMMAR RENDER (R10). Under ADR
    0080 the composed subject is the TRANSLATOR'S stored work; this
    render is only the delivery half. Total: never raises."""
    tree = None
    for k, t in read.trees().items():
        if k == target or t["name"] == target:
            tree = t
    if tree is None:
        return ""
    deliveries = [st["scope"] for st in tree["statements"]
                  if st.get("emits") and st.get("scope")
                  and st["scope"].get("name_key")]
    if not deliveries:
        return ("emits no result set; a setup or maintenance "
                "script")
    return " ".join(_scope_lead(read, tree, d)
                    for d in deliveries).lower()


def _priority(read: ReadApi, worklist: List[str]) -> List[str]:
    """ECON: usage-weighted — touch counts from the ledger; first
    contact (empty ledger) degrades to worklist order, declared."""
    touches: Dict[str, int] = {}
    for e in read.nodes("usage"):
        about = e.properties.get("about")
        if about:
            touches[about] = touches.get(about, 0) + 1
    return sorted(worklist, key=lambda t: -touches.get(t, 0))


def run(store, occurred_at: str,
        smooth: Optional[Callable[[str], str]] = None):
    """One produce run. Returns the run event node (PROD-1: the only
    production ledger)."""
    read = ReadApi(store)
    worklist = derivation.lens_staleness(read, None)["yield"]  # PROD-2
    batch = _priority(read, worklist)[:min(ECON["batch_size"],
                                           ECON["run_budget"])]
    run = run_events.open_run(
        author="agent:produce",
        basis={"floor_grammar": FLOOR_GRAMMAR_VERSION,
               "econ": ECON["version"], "metamodel": "1.0.0",
               "worklist": list(batch)},
        occurred_at=occurred_at)
    shipped, absent, killed = 0, [], 0
    # Phase D: every new machine description anchors to its scope's
    # MEANING identity at write time (the anchor rule, ruling 2f)
    keys = anchors.selection_keys(read)
    for target in batch:
        try:  # OPS-2: one append or a counted absence, never half
            floor = compose_floor(read, target)
            text, status = floor, "skeleton_floor"
            if smooth is not None:
                candidate = smooth(floor)
                tree = next(t for t in read.trees().values()
                            for s in decisions.named_scopes(t)
                            if s["name_key"] == target)
                scope = next(s for s in decisions.named_scopes(tree)
                             if s["name_key"] == target)
                violations = gates.check_text(
                    candidate, floor,
                    _Voice(read, tree).forbidden_tokens(scope))
                if not violations:
                    text, status = candidate, "gate_passed"
                else:
                    killed += len(violations)  # counted, never silent
            anchor = ({"scope": target, "content_key": keys[target]}
                      if target in keys else None)
            kg3_artifacts.append_description(
                store, artifact_id=f"description:{target}", about=[target],
                text=text, status=status, author="agent:produce",
                basis=run.basis, created_at=occurred_at, anchor=anchor)
            shipped += 1
        except Exception as err:  # noqa: BLE001 — OPS-2: absence counted w/ reason, run continues
            absent.append({"target": target, "reason": str(err)})
    run.accounting["descriptions"] = {
        "attempted": len(batch), "shipped": shipped,
        "absent": len(absent), "absent_detail": absent,
        "killed_lines": killed}
    run.accounting["terms"] = {"attempted": 0}
    return run_events.close_run(store, run, outcome="completed")
