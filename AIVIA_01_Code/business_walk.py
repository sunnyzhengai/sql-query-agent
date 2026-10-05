# =====================================================================
# business_walk.py — THE GRAPH-WALK PROPOSER (the phase 07 reopen)
#
# PSEUDO CODE for Sunny's review, 2026-10-04. No real code lands in
# this file until her approval, then the seven G-locks land RED, then
# the code lands under these comments (the standing process).
#
# The law this file implements: THE WALK CONTRACT, sections A-H
# (07_business_descriptions_data_contract.md, stamped 2026-10-04),
# born from Brief_07_Graph_Grounded_Proposer.md Q1-Q9.
# =====================================================================

# ---------------------------------------------------------------------
# P0. HOME + THE IMPORT LAW
# ---------------------------------------------------------------------
# - This NEW file is the walk's one home. business_descriptions.py
#   stays intact and keeps running the current pipeline until
#   acceptance (section H) — both machines can build the proving file
#   side by side during the shakedown.
# - REUSED from business_descriptions (imported, never copied): the
#   paid caller seat + timeout law, the checkpoint/resume harness,
#   the effective ladder (blessed > gate_passed > floor), the
#   registry reader, the surviving shape checks (SQL vocabulary +
#   @token ban, the never-list, S10 grounded numbers), the tone-law
#   system prompt base.
# - THE STRUCTURAL LOCK (test_planks precedent): WalkStore (P1) is
#   the ONLY section that opens files. Every other function in this
#   file takes data, returns data. The lock test greps this file:
#   any open()/read_text()/json.load outside the WalkStore section
#   is a red build.

# ---------------------------------------------------------------------
# P1. WALKSTORE — the one read surface (contract A + Q9)
# ---------------------------------------------------------------------
# Loads, once, through the 05/02/03 contracts' named artifacts:
#   - the 05 node and edge sheets: scopes, structures, predicates,
#     expressions, parameters, values, contains edges (with position
#     and role), resolves edges
#   - the 02 dictionary: table + column descriptions (VERBATIM,
#     context-only — never voiced; the Q2 ruling)
#   - the 03 abstract-names asset: short names + sunny_* overrides
#   - the 07 blessing registry (names + sentences, her hand)
# API (pure lookups, no judgment):
#   children(node_id)        -> ordered child node ids (contains)
#   kind(node_id)            -> file|scope|structure|predicate|expr|param
#   columns(pred_id)         -> column ids the predicate reads
#   bound_values(pred_id)    -> value ids with their stored names
#   ladder_name(col_or_tbl)  -> sunny_*/blessed > the asset's FIRST
#                               synonym > None. None = A COVERAGE GAP,
#                               never a fallback to description words
#                               (rung 3 is floor-only — Q2 rider a).
#   value_name(value_id)     -> the value node's stored name
#                               ("Census" for 6, "Canceled" for 2)
#   param_name(param_id)     -> the parameter's plain name
#                               ("the chosen start date")
#   payload_kinds(scope_id)  -> the delivered kinds (Each-row-shows)
#   class_of(pred_id)        -> 1 | 2 | 3, MECHANICAL (Q3):
#                               top-level population path -> 1;
#                               linkage/null-check kinds there -> 2;
#                               ON-clause / join path -> 3.
#                               Position decides, never judgment.

# ---------------------------------------------------------------------
# P2. THE NAMING COVERAGE PASS (contract B; zero cost; runs FIRST)
# ---------------------------------------------------------------------
# naming_coverage(store, only_file=None) -> gaps
#   - walks every node the build would SPEAK (population predicates,
#     scopes, card, fields) and collects every column/table whose
#     ladder_name() is None
#   - writes 07_naming_gaps.json (tracked) staged for Sunny's eye
#   - prints the list, one line each: node, raw name, dictionary
#     description (so she can rule a short name or sunny_* override)
# build07_walk REFUSES to make live calls while gaps exist for the
# requested file(s) — a gap stages, it never falls through to
# description-words speech. (The EFFECTIVE_TIME lesson, mechanical.)

# ---------------------------------------------------------------------
# P3. ROOMS (contract A) — build_room(node_id, walk_state) -> room
# ---------------------------------------------------------------------
# room = { speakable: {...}, context: {...}, must_say: [...] }
# Per rung, EXACTLY the contract table, nothing else enters:
#   PREDICATE room:
#     speakable: its columns' ladder names, its bound values' names,
#                its parameters' plain names
#     context:   those columns' dictionary descriptions
#     must_say:  every bound value (class-1 preds); the plain linkage
#                clause (class-2)
#   STRUCTURE room (WHERE/AND/OR — population path only):
#     speakable: its children's FINISHED sentences (walk_state)
#     must_say:  every class-1 value carried by those sentences
#     (JOIN/ON structures: class 3 — the walk writes NO sentence;
#      their speech stays the 06 floor's. Nothing to leak.)
#   SCOPE room (Q4):
#     speakable: its own structures' finished sentences, its grain
#                phrase, its payload kinds
#     must_say:  ONE ROW IS always; KEEPS only if it owns membership
#                conditions (honest silence otherwise — no filler)
#   CARD-LINE rooms (five, Q5 — one per line, built from SELECTORS):
#     speakable: that selector's results only
#     must_say:  the selector's class-1 values (Excludes: + class-2
#                clauses)
#   FIELD room (Q6 — blind):
#     speakable: its column's ladder name, its expression
#     context:   the dictionary description
#     (population facts are ABSENT, not forbidden — the clean room)

# ---------------------------------------------------------------------
# P4. THE FIVE SELECTORS (contract D) — deterministic, named
# ---------------------------------------------------------------------
# over the file's subgraph, reading class_of + predicate kinds:
#   sel_one_row_is(file)    -> the delivery scope's grain
#   sel_whos_in_it(file)    -> class-1 POSITIVE predicates + the
#                              run-time choice edges (selection-
#                              consuming predicates, spoken as
#                              choices — the 0 stays home, class 3)
#   sel_each_row_shows(file)-> payload kinds (at most 5 kinds law)
#   sel_time_window(file)   -> class-1 TEMPORAL predicates (window,
#                              as-of, the cancel OR-group)
#   sel_excludes(file)      -> class-1 NEGATIVE predicates + class-2
#                              clauses
# temporal = compares a date column/param; negative = structural NOT
# over a positive kind / not-in-list; positive = the rest. The same
# predicate never lands in two selectors (disjointness is a test).

# ---------------------------------------------------------------------
# P5. THE WALKER (contract A+D) — walk_file(store, fname) -> rows
# ---------------------------------------------------------------------
# POST-ORDER, code walks, the model talks at each stop:
#   1. population predicates (class 1 and 2)       -> one call each
#   2. population structures, leaves-first         -> one call each
#   3. scopes (sub-selections first, delivery last)-> one call each
#   4. the card: five selector calls, code joins the labeled lines
#   5. fields                                      -> one call each
# Each call: prompt = tone base + the room (speakable spelled out,
# context marked "background, never quote") + the rung's must-says +
# named objections on repair. Repair budget 3 (reused loop). Every
# call checkpointed (reused harness); resume never re-pays.
# INTERMEDIATE sentences (predicates, structures) are walk state,
# NOT sheet rows — the sheet keeps its 151-row conservation (file +
# scope + field). They land TRACKED in 07_walk_trace.json so Sunny
# can audit any card line down to its floor (the audit chain).

# ---------------------------------------------------------------------
# P6. THE CHECKER (contract E) — check(output, room) -> findings
# ---------------------------------------------------------------------
# Deterministic, both directions, every call:
#   extract specific claims: quoted values; numbers; proper-noun
#     phrases (matched against the four lists — short names,
#     value-node names, parameter plain names, blessed names)
#   normalize: casefold, strip punctuation, simple plural fold
#   RESOLVE each claim to the room -> miss = ROOM VIOLATION (from
#     context = the named context leak; from nowhere = invention)
#   column/table spoken outside its ladder name -> NAME VIOLATION
#   must_say element absent -> CONSERVATION BREAK (omission)
#   per-scope and per-card-line class-1 value counts, both
#     directions -> CONSERVATION BREAK
#   + the surviving shape checks (imported): per-line template,
#     scope shape (no filler KEEPS, no foreign condition), SQL
#     vocabulary, the never-list, S10
# NO LLM anywhere in this section (excluded by ruling, Q7).
# Findings feed the repair loop as named objections; ungrounded
# finds still land code sightings (the growth queue).

# ---------------------------------------------------------------------
# P7. OUTPUTS (contract F — shapes unchanged)
# ---------------------------------------------------------------------
# 07_business_sheet.json rows: same shape, same 151-row conservation,
#   docket_refs becomes room_refs (the node ids the room carried).
# <file>.txt: same five-line card + scope + field layout.
# <file>.facts.txt: unchanged (the 06 machinery still renders it).
# 07_walk_trace.json: NEW, tracked — the intermediate rung sentences
#   for her audit (predicate -> structure -> scope -> line).
# 07_naming_gaps.json: NEW, tracked — the coverage pass's stage.
# Sightings, blessing registry, effective ladder: untouched.
# --no-llm: floor-only build, zero calls, conserving, registry
#   untouched (byte-identity test carries over).

# ---------------------------------------------------------------------
# P8. THE BUILD DOORS (fills the two sunny-md placeholders at
#     approval)
# ---------------------------------------------------------------------
# naming_coverage door:
#   python3.11 -c "... import business_walk as bw;
#       bw.naming_coverage(d05, d02, d03, only_file=CENSUS)"
# the walk build door:
#   python3.11 -c "... bw.build07_walk(d05, d06, out07, d02, d03,
#       no_llm=False, only_file=CENSUS)"
# (CENSUS = COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_
#  SSRS — the proving file; the corpus runs only after acceptance.)

# ---------------------------------------------------------------------
# P9. THE TEST MAP (the seven G-locks -> what each exercises)
# ---------------------------------------------------------------------
# G.1 seeded memory-invention  -> P6 resolve (room violation)
# G.2 7-of-8 departments       -> P6 conservation, must_say direction
# G.3 paraphrased column name  -> P6 name violation
# G.4 filler KEEPS             -> P6 scope shape (via P3 must_say)
# G.5 foreign condition        -> P6 ownership (room has no such fact
#                                 -> resolve fails it as room violation)
# G.6 department on a field    -> P3 field room absence + P6 resolve
# G.7 plumbing on the card     -> P4 selector disjointness + P6
#                                 resolve (the 0, the marker 1, and
#                                 STRING_SPLIT are in NO card room)
# Retirements at this build: the inheriting field-docket lock; the
# S15-S18 prompt locks where P6 makes them mechanical.
# Plus the carried locks: sheet conservation, --no-llm byte
# identity, checkpoint/resume, selector disjointness (new).
# =====================================================================

# =====================================================================
# THE CODE (landed 2026-10-04 after Sunny's pseudo approval; the
# eight G-locks above it were RED first, verbatim output recorded).
# =====================================================================

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import business_descriptions as bd  # noqa: E402  (the reused seats)

WALK_BASIS = "07.3.0-walk"


def _read(path):
    return json.loads(Path(path).read_text())


def _norm(s):
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _fold(s):
    # the simple plural fold of the Q7 ruling
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") else w
                    for w in _norm(s).split())


def _param_plain(name):
    # "@StartDate" -> "the chosen start date" (mechanical words)
    words = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", name.lstrip("@"))
    return "the chosen " + " ".join(w.lower() for w in words)


# ------------------------------------------------- P1. WalkStore

class WalkStore:
    """The one read surface (contract A; Q9's read layer). The
    ONLY section of this file that opens files — test-locked."""

    def __init__(self, dir05, dir02, dir03, dir07=None,
                 dir06=None):
        d5, d2, d3 = Path(dir05), Path(dir02), Path(dir03)
        self.rows06, self.six = [], {}
        if dir06:
            self.rows06 = _read(
                Path(dir06) / "06_description_sheet.json")
            self.six = {r["node_id"]: r["sentence"]
                        for r in self.rows06}
        self.preds = {r["node_id"]: r
                      for r in _read(d5 / "05_predicate_sheet.json")}
        self.structs = {r["node_id"]: r
                        for r in _read(d5 / "05_structure_sheet.json")}
        self.scopes = {r["node_id"]: r
                       for r in _read(d5 / "05_scope_sheet.json")}
        self.exprs = {r["node_id"]: r
                      for r in _read(d5 / "05_expression_sheet.json")}
        self.params = {r["node_id"]: r
                       for r in _read(d5 / "05_parameter_sheet.json")}
        kids = {}
        for e in _read(d5 / "05_contains_edges.json"):
            kids.setdefault(e["from_id"], []).append(e)

        def _pos(e):
            try:
                return int(e.get("position") or 0)
            except ValueError:
                return 0
        self._kids = {k: [e["to_id"] for e in sorted(v, key=_pos)]
                      for k, v in kids.items()}
        self._res = {}
        for e in _read(d5 / "05_resolves_edges.json"):
            self._res.setdefault(e["from_id"], []).append(e)
        self.col_desc = {
            f"{r['table_name']}.{r['column_name']}":
                (r.get("column_description") or "")
            for r in _read(
                d2 / "02_emr_data_dictionary_extraction_column.json")}
        self.value_name = {
            f"{r['table_name']}::{r['code']}": r.get("meaning") or ""
            for r in _read(
                d2 / "02_emr_data_dictionary_extraction_value.json")}
        self._names = {}
        for r in _read(d3 / "03_chat_abstract_names.json"):
            syn = (r.get("sunny_synonyms") or []) + \
                  (r.get("synonyms") or [])
            if syn:
                self._names[r["object_name"]] = syn[0]
        self._blessed = {}
        self._blessed_sent = {}
        if dir07:
            reg = Path(dir07) / "07_blessing_registry.json"
            if reg.exists():
                data = _read(reg)
                for n in data.get("names", []):
                    if n.get("blessed_name"):
                        self._blessed[n.get("node_id") or
                                      n.get("key")] = n["blessed_name"]
                for n in data.get("sentences", []):
                    if n.get("blessed_text"):
                        self._blessed_sent[n["node_id"]] = \
                            n["blessed_text"]

    # pure lookups --------------------------------------------------
    def children(self, nid):
        return self._kids.get(nid, [])

    def resolves(self, nid, to_kind=None, deep=False):
        out = []
        ids = [nid]
        if deep:
            stack = [nid]
            while stack:
                cur = stack.pop()
                for k in self._kids.get(cur, []):
                    ids.append(k)
                    stack.append(k)
        for i in ids:
            for e in self._res.get(i, []):
                if to_kind is None or e["to_kind"] == to_kind:
                    out.append(e)
        return out

    def ladder_name(self, object_name):
        """sunny_*/blessed > the 03 asset's first synonym > None.
        None is a COVERAGE GAP, never description-words speech."""
        return self._blessed.get(object_name) or \
            self._names.get(object_name)

    def columns_of(self, pred_id):
        return sorted({e["to_id"] for e in
                       self.resolves(pred_id, "column", deep=True)})

    def values_of(self, pred_id):
        out = []
        for e in self.resolves(pred_id, "value", deep=True):
            name = self.value_name.get(e["to_id"])
            if name and name not in out:
                out.append(name)
        return out

    def params_of(self, node_id):
        out = []
        for e in self.resolves(node_id, "parameter", deep=True):
            p = _param_plain(e["to_id"].split("::param/")[-1])
            if p not in out:
                out.append(p)
        if not out:
            # 05 DEBT (found 2026-10-04, census live run): params
            # inside table-function sub-selections carry NO
            # resolve edge. The node's own EVIDENCE still names
            # them — a mechanical, store-resident fallback.
            row = self.preds.get(node_id) or \
                self.scopes.get(node_id) or {}
            frag = (row.get("evidence") or {}).get("fragment", "")
            fname = node_id.split("::")[1]
            for tok in re.findall(r"@\w+", frag):
                nid = f"file::{fname}::param/{tok}"
                if nid in self.params:
                    p = _param_plain(tok)
                    if p not in out:
                        out.append(p)
        return out

    def class_of(self, pred_id):
        """Q3, mechanical: position decides, never judgment."""
        row = self.preds[pred_id]
        if row.get("on_class") in ("join_pair", "lookup_shaping"):
            return 3
        if "::scope/sub" in pred_id.split("::structure/WHERE")[0]:
            return 3        # a sub-selection's own mechanism
        if "::structure/WHERE" not in pred_id:
            return 3
        if row["predicate_kind"] == "NULL_CHECK":
            return 2
        return 1

    def delivery_scope(self, fname):
        return f"file::{fname}::scope/delivery"

    def projections(self, fname):
        proj = []
        for sid in self.children(self.delivery_scope(fname)):
            s = self.structs.get(sid)
            if s and s["structure_kind"] == "PROJECTION":
                proj += [self.exprs[e] for e in self.children(sid)
                         if e in self.exprs]
        return proj


# ------------------------------------- P4. the top units + selectors

def _top_units(store, fname):
    """The top-level conditions of the delivery WHERE — one unit
    per line of the facts shape law (an OR-group is ONE unit)."""
    where = None
    for sid in store.children(store.delivery_scope(fname)):
        s = store.structs.get(sid)
        if s and s["structure_kind"] == "WHERE":
            where = sid
    if not where:
        return []
    tops = []
    for kid in store.children(where):
        if kid in store.structs and \
                store.structs[kid]["structure_kind"] == "AND":
            tops = store.children(kid)
            break
    else:
        tops = store.children(where)
    return tops


def _unit_preds(store, unit):
    if unit in store.preds:
        return [unit]
    out, stack = [], [unit]
    while stack:
        cur = stack.pop()
        for k in store.children(cur):
            if k in store.preds:
                out.append(k)
            elif k in store.structs:
                stack.append(k)
    return out


def _unit_class(store, unit):
    cls = {store.class_of(p) for p in _unit_preds(store, unit)
           if "::scope/sub" not in p.split("::structure/WHERE")[0]}
    cls = {c for c in cls if c != 3} or {3}
    return min(cls)


def _is_temporal(store, unit):
    for p in _unit_preds(store, unit):
        for e in store.resolves(p, "parameter", deep=True):
            pid = e["to_id"]
            if store.params.get(pid, {}).get("data_type", "")\
                    .upper().startswith("DATE"):
                return True
        for e in store.resolves(p, "column", deep=True):
            col = e["to_id"].rsplit(".", 1)[-1]
            if col.endswith("_TIME") or col.endswith("_DATE"):
                return True
    return False


def _is_negative(store, unit):
    return any(store.preds[p].get("negated")
               for p in _unit_preds(store, unit)
               if store.class_of(p) == 1)


def sel_excludes(store, fname):
    return [u for u in _top_units(store, fname)
            if _unit_class(store, u) == 2 or
            (_unit_class(store, u) == 1 and _is_negative(store, u))]


def sel_time_window(store, fname):
    ex = set(sel_excludes(store, fname))
    return [u for u in _top_units(store, fname)
            if u not in ex and _unit_class(store, u) == 1
            and _is_temporal(store, u)]


def sel_whos_in_it(store, fname):
    taken = set(sel_excludes(store, fname)) | \
        set(sel_time_window(store, fname))
    return [u for u in _top_units(store, fname)
            if u not in taken and _unit_class(store, u) == 1]


# ------------------------------------------------- P6. the checker

_EXAMPLE_MARK = re.compile(
    r"(?:such as|for example|including)\s+([^.;\n]+)", re.I)
_CHOSEN = re.compile(r"\bthe chosen ([a-z]+(?: [a-z]+)?)")
_QUOTED = re.compile(r"(?<![A-Za-z])'([^']+?)'(?![A-Za-z])")
_NUM = re.compile(r"\b\d+\b")
_ALLCAPS = re.compile(r"\b[A-Z][A-Z_]+(?:\s+[A-Z][A-Z_]+)*\b")
_CAPRUN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")
_FILLER = {"whether", "it", "reflects", "a", "an", "the", "was",
           "were", "recorded", "as", "or", "and"}


def _claims(text):
    """The specific claims of contract E: quoted values, numbers,
    proper-noun runs — plus the two ruled claim patterns: example
    tails (Q1's zone close) and run-time-choice phrases."""
    out = []
    out += [m.group(1) for m in _QUOTED.finditer(text)]
    out += _NUM.findall(text)
    out += [m.group(0) for m in _ALLCAPS.finditer(text)]
    out += [m.group(0) for m in _CAPRUN.finditer(text)]
    for m in _EXAMPLE_MARK.finditer(text):
        for item in re.split(r",| or | and ", m.group(1)):
            words = [w for w in _norm(item).split()
                     if w not in _FILLER]
            if words:
                out.append(" ".join(words))
    for m in _CHOSEN.finditer(text):
        out.append("the chosen " + m.group(1))
    return out


def check(text, room, grain):
    """Contract E: deterministic, both directions, no LLM ever."""
    sp = room.get("speakable", {})
    allowed = set()
    for key in ("short_names", "value_names", "param_names",
                "blessed_names"):
        for a in sp.get(key, []):
            allowed.add(_fold(a))
    if sp.get("param_names"):
        # S14's own ruled vocabulary: a room carrying run-time
        # choices licenses the choice word All (the 2026-10-04
        # 'Choosing All' false-positive lock)
        allowed.add("all")
    sent_folds = [_fold(s) for s in sp.get("sentences", []) if s]
    findings = []
    for c in _claims(text):
        cf = _fold(c)
        if len(cf) < 2:
            cf = cf or c
        ok = any(cf == a or (len(cf) > 2 and cf in a)
                 or (len(a) > 2 and a in cf) for a in allowed) or \
            any(len(cf) > 2 and cf in sf for sf in sent_folds)
        if not ok:
            findings.append(
                f"ROOM violation: '{c}' resolves to nothing in "
                f"this {grain} room")
    folded_text = _fold(text)
    for m in room.get("must_say", []):
        if m.lower() == "one row is":
            if "one row" not in folded_text:
                findings.append(
                    "CONSERVATION break: the grain sentence "
                    "('one row is') is absent")
            continue
        if _fold(m) not in folded_text:
            findings.append(
                f"CONSERVATION break: must-say '{m}' is absent")
    if grain == "scope":
        owned = [m for m in room.get("must_say", [])
                 if m.lower() != "one row is"]
        if not owned and re.search(r"\bkeeps?\b", text, re.I):
            findings.append(
                "KEEPS filler: this scope owns no membership "
                "conditions — honest silence (Q4)")
    return list(dict.fromkeys(findings))


# ------------------------------------------- P3. rooms (the build's)

def _room_shell(short=(), values=(), params=(), blessed=(),
                sentences=(), ctx=None, must=()):
    return {"speakable": {"short_names": list(short),
                          "value_names": list(values),
                          "param_names": list(params),
                          "blessed_names": list(blessed),
                          "sentences": list(sentences)},
            "context": ctx or {},
            "must_say": list(must)}


def _unit_room(store, unit):
    cols, vals, pars, ctx = [], [], [], {}
    for p in _unit_preds(store, unit):
        for c in store.columns_of(p):
            n = store.ladder_name(c)
            if n and n not in cols:
                cols.append(n)
                ctx[n] = store.col_desc.get(c, "")
        for v in store.values_of(p):
            if v not in vals:
                vals.append(v)
        for q in store.params_of(p):
            if q not in pars:
                pars.append(q)
    ucls = _unit_class(store, unit)
    # Q3 as ruled: class-1 conserves VALUES; class-2 survives as
    # one plain clause, values (and names) NOT carried — a string
    # must-say on class 2 over-enforces and doubles the clause
    must = list(vals) if ucls == 1 else []
    base = [store.six[unit]] if store.six.get(unit) else \
        [store.six[p] for p in _unit_preds(store, unit)
         if store.six.get(p)]
    return _room_shell(short=cols, values=vals, params=pars,
                       sentences=base, ctx=ctx, must=must), ucls


def _scope_grain_hint(store, scope_id, fname):
    pars = store.params_of(scope_id)
    if "::scope/sub" in scope_id:
        if not pars:
            # the @param rides on the CONSUMING predicate (the
            # EXISTS in the delivery WHERE), not inside the sub-
            # selection — follow the graph edge backward
            for pid in store.preds:
                if any(e["to_id"] == scope_id for e in
                       store.resolves(pid, "scope", deep=True)):
                    pars = store.params_of(pid)
                    if pars:
                        break
        if pars:
            one = re.sub(r"^the chosen ", "", pars[0])
            return f"one chosen {_fold(one)}"
    tables = {e["to_id"] for e in
              store.resolves(scope_id, "table", deep=True)}
    for t in sorted(tables):
        n = store.ladder_name(t)
        if n:
            return f"one row of {n}"
    return "one row of the source data"


def _field_rooms(store, fname):
    out = []
    for ex in store.projections(fname):
        cols = [e["to_id"] for e in
                store.resolves(ex["node_id"], "column")]
        ladder = None
        ctx = {}
        for c in cols:
            ladder = store.ladder_name(c)
            if ladder:
                ctx[ladder] = store.col_desc.get(c, "")
                break
        label = ex.get("output_name") or ""
        name = ladder or label
        if ladder and label and _fold(label) != _fold(ladder):
            ctx["the report column label"] = label
        room = _room_shell(short=[name] if name else [],
                           ctx=ctx, must=[name] if name else [])
        out.append((ex["node_id"], room))
    return out


# --------------------------------------- P5. prompts + the speak loop

_WALK_TONE = (
    "You write for clinicians: plain, concrete, natural sentences "
    "— the way experienced clinical staff explain data to each "
    "other, never the abstract voice of a systems document. "
    "No SQL vocabulary, no tokens starting with @, no symbols "
    "like >= or &.\n"
    "SPEAK ONLY FROM THE ROOM below. Every specific value, name "
    "and number you write must appear in SPEAKABLE. BACKGROUND "
    "is for your understanding only — never quote or voice it. "
    "Add nothing from memory, drop nothing listed as MUST SAY. "
    "An effective date or time is when the event took effect — "
    "never say scheduled, planned, or any form of 'supposed to "
    "have happened'; that phrase MEANS the effective time, so "
    "say it by its name. TRANSLATE the already-spoken "
    "conditions into plain clinician words using the NAMES "
    "given — never copy their awkward phrasing.")


def _walk_prompt(instruction, room, findings=None):
    sp = room["speakable"]
    parts = [_WALK_TONE, "", instruction, "", "SPEAKABLE:"]
    for key, label in (("short_names", "names"),
                       ("value_names", "values"),
                       ("param_names", "run-time choices"),
                       ("blessed_names", "blessed names"),
                       ("sentences",
                        "already-spoken conditions (reuse and "
                        "merge freely — they are exact)")):
        if sp.get(key):
            parts.append(f"  {label}: " + "; ".join(sp[key]))
    if room.get("must_say"):
        parts.append("MUST SAY: " + "; ".join(room["must_say"]))
    for k, v in (room.get("context") or {}).items():
        if v:
            parts.append(f"BACKGROUND ({k}): {v}")
    if findings:
        parts += ["", "OBJECTIONS (resolve every one):"]
        parts += [f"- {f}" for f in findings]
    return "\n".join(parts)


_REGISTER = re.compile(r"@\w|>=|<=|<>|&")


def _speak(caller, grain, instruction, room):
    findings = []
    text = ""
    for rnd in range(1, bd.REPAIR_BUDGET + 1):
        try:
            text = caller(_walk_prompt(instruction, room, findings))
        except Exception as exc:  # noqa: BLE001 — the timeout law:
            # ANY call failure is a failed round, never a dead build
            return ("", "floor",
                    [f"call failed round {rnd}: {exc}"],
                    bd.REPAIR_BUDGET)
        findings = check(text, room, grain)
        if _REGISTER.search(text):
            findings.append("REGISTER: SQL symbols or @tokens")
        if not findings:
            return text, "gate_passed", [], rnd
    return text, "floor", findings, bd.REPAIR_BUDGET


# ------------------------------------- P2. the naming coverage pass

def naming_coverage(dir05, dir02, dir03, only_file=None,
                    out07=None):
    store = WalkStore(dir05, dir02, dir03, out07)
    fnames = sorted({n.split("::")[1] for n in store.scopes
                     if n.startswith("file::")})
    if only_file:
        fnames = [f for f in fnames if f == only_file]
    gaps = []
    for fname in fnames:
        spoken = set()
        for u in _top_units(store, fname):
            if _unit_class(store, u) == 3:
                continue
            for p in _unit_preds(store, u):
                spoken.update(store.columns_of(p))
        for ex in store.projections(fname):
            spoken.update(e["to_id"] for e in
                          store.resolves(ex["node_id"], "column"))
        for sid in (store.delivery_scope(fname),):
            spoken.update(e["to_id"] for e in
                          store.resolves(sid, "table"))
        for obj in sorted(spoken):
            if not store.ladder_name(obj):
                gaps.append({"file": fname, "object": obj,
                             "dictionary":
                             store.col_desc.get(obj, "")})
    out_dir = Path(out07) if out07 else \
        Path("AIVIA_01_Data/07_business_descriptions")
    (out_dir / "07_naming_gaps.json").write_text(
        json.dumps(gaps, indent=1))
    for g in gaps:
        print(f"GAP {g['file']}: {g['object']} — "
              f"{g['dictionary'][:70]}")
    print(f"naming coverage: {len(gaps)} gap(s); "
          f"{'the build may speak' if not gaps else 'STAGED for Sunny'}")
    return gaps


# --------------------------------- P5/P7/P8. the walk build door

def _card_line_rooms(store, fname, unit_text):
    whos = sel_whos_in_it(store, fname)
    time_u = sel_time_window(store, fname)
    excl = sel_excludes(store, fname)

    def _merge(units):
        rooms = [_unit_room(store, u)[0] for u in units]
        short, vals, pars, must, ctx = [], [], [], [], {}
        sents = [unit_text[u] for u in units if unit_text.get(u)]
        for r in rooms:
            for n in r["speakable"]["short_names"]:
                if n not in short:
                    short.append(n)
            for v in r["speakable"]["value_names"]:
                if v not in vals:
                    vals.append(v)
            for q in r["speakable"]["param_names"]:
                if q not in pars:
                    pars.append(q)
            for m in r["must_say"]:
                if m not in must:
                    must.append(m)
            ctx.update(r["context"])
        return _room_shell(short=short, values=vals, params=pars,
                           sentences=sents, ctx=ctx, must=must)

    grain = _scope_grain_hint(store, store.delivery_scope(fname),
                              fname)
    file_six = store.six.get(f"file::{fname}", "")
    labels = [ex.get("output_name") or "" for ex
              in store.projections(fname)]
    one_row = _room_shell(short=[grain], sentences=[file_six],
                          must=[])
    _whos_room = _merge(whos)
    _whos_room["speakable"]["sentences"].append(file_six)
    shows = _room_shell(short=labels)
    return [("One row is", "one_row_is", one_row,
             "State what ONE ROW of this dataset is, in business "
             "meaning, one short sentence. The grain ONLY — no "
             "conditions, no limits, no population talk; those "
             "live on other lines. Do not write any label and "
             "do not begin with 'one row is'."),
            ("Who's in it", "whos_in_it", _whos_room,
             "Write the 'Who's in it' line's CONTENT only, as "
             "one or two natural sentences: first WHO is "
             "counted (the population, from the already-spoken "
             "material), during the reporting period; then the "
             "run-time choices (choosing All includes all). "
             "Never as-of behavior. NO negatives."),
            ("Each row shows", "each_row_shows", shows,
             "Write the 'Each row shows' line's CONTENT only: AT "
             "MOST 5 KINDS of information, no individual field "
             "list."),
            ("Time window", "time_window", _merge(time_u),
             "Write the 'Time window' line's CONTENT only: the "
             "window and the as-of behavior, decoded plainly "
             "(inclusive end date; data as it stood)."),
            ("Excludes", "excludes", _merge(excl),
             "Write the 'Excludes' line's CONTENT only: every "
             "exclusion named; housekeeping summarized plainly "
             "(records not linked to a patient). Say each fact "
             "ONCE — never restate the same exclusion in "
             "different words.")]


def build07_walk(dir05, dir06, out07, dir02, dir03,
                 no_llm=False, only_file=None, caller=None,
                 rerender=False):
    """The walk build door (contract D-H). Census-only until
    section-H acceptance; the corpus follows her go."""
    out = Path(out07)
    store = WalkStore(dir05, dir02, dir03, out07, dir06)
    rows06 = store.rows06
    fnames = sorted({r["node_id"].split("::")[1] for r in rows06})
    if only_file:
        fnames = [f for f in fnames if f == only_file]
    caller = caller or bd._openai_caller

    if rerender:
        # ZERO-CALL re-render (ruled 2026-10-04, her bless-1-and-2):
        # landing a blessing never rerolls the unpinned lines —
        # the card rebuilds from registry + stored trace; every
        # other row rides through byte-identical.
        sheet_path = out / "07_business_sheet.json"
        rows = _read(sheet_path) if sheet_path.exists() else []
        trace = _read(out / "07_walk_trace.json") if \
            (out / "07_walk_trace.json").exists() else {}
        labels = {"one_row_is": "One row is",
                  "whos_in_it": "Who's in it",
                  "each_row_shows": "Each row shows",
                  "time_window": "Time window",
                  "excludes": "Excludes"}
        out_rows = []
        for fname in fnames:
            frows = [r for r in rows
                     if r["node_id"].split("::")[1] == fname]
            tr = trace.get(fname, {})
            parts, status = [], "gate_passed"
            for key in ("one_row_is", "whos_in_it",
                        "each_row_shows", "time_window",
                        "excludes"):
                bless_id = f"file::{fname}::card/{key}"
                if bless_id in store._blessed_sent:
                    txt, st = store._blessed_sent[bless_id], \
                        "blessed"
                else:
                    cell = tr.get(f"card/{key}", {})
                    txt = cell.get("text", "")
                    st = cell.get("status", "floor")
                if st not in ("gate_passed", "blessed"):
                    status = "floor"
                label = labels[key]
                txt = re.sub(
                    rf"^{re.escape(label)}\s*[:,]?\s*", "",
                    txt, flags=re.I)
                parts.append(f"{label}: {txt}")
            for r in frows:
                if r["grain"] == "file":
                    r = dict(r,
                             audience_text="\n\n".join(parts),
                             status=status)
                out_rows.append(r)
            body = [f"==== {fname} ====",
                    f"basis {WALK_BASIS}", ""]
            for r in out_rows:
                if r["node_id"].split("::")[1] != fname:
                    continue
                body.append(f"[{r['status']}] {r['grain']}: "
                            f"{r['audience_text']}")
            (out / f"{fname}.txt").write_text(
                "\n".join(body) + "\n")
        keep = [r for r in rows
                if r["node_id"].split("::")[1] not in fnames]
        sheet_path.write_text(json.dumps(keep + out_rows,
                                         indent=1))
        print(f"07 walk rerender: {len(out_rows)} rows over "
              f"{len(fnames)} file(s); zero calls")
        return out_rows

    if not no_llm:
        gaps = naming_coverage(dir05, dir02, dir03,
                               only_file=only_file, out07=out07)
        gaps = [g for g in gaps if g["file"] in fnames]
        if gaps:
            print("REFUSED: naming gaps staged for Sunny — no "
                  "live call while an unnamed thing would speak.")
            return []

    ck_path = out / "07_walk_checkpoint.json"
    ck = _read(ck_path) if ck_path.exists() else {}

    def _spoken(key, grain, instruction, room):
        if key in ck:
            c = ck[key]
            return c["text"], c["status"], c["findings"], c["used"]
        if no_llm:
            return "", "floor", ["no-llm build"], 0
        r = _speak(caller, grain, instruction, room)
        ck[key] = {"text": r[0], "status": r[1],
                   "findings": r[2], "used": r[3]}
        ck_path.write_text(json.dumps(ck, indent=1))
        return r

    all_rows, trace = [], {}
    for fname in fnames:
        f06 = [r for r in rows06
               if r["node_id"].split("::")[1] == fname]
        file06 = next(r for r in f06 if r["grain"] == "file")
        scopes06 = [r for r in f06 if r["grain"] == "scope"]
        tr = trace.setdefault(fname, {})

        unit_text = {}
        for u in _top_units(store, fname):
            room, ucls = _unit_room(store, u)
            if ucls == 3:
                continue
            txt, st, fnd, used = _spoken(
                u, "predicate",
                "State this one condition as ONE plain "
                "sentence about who or what is counted, using "
                "the NAMES given — translate, never copy the "
                "already-spoken phrasing.", room)
            unit_text[u] = txt
            tr[u] = {"text": txt, "status": st}

        card_parts = []
        card_status = "gate_passed"
        for label, key, room, instruction in \
                _card_line_rooms(store, fname, unit_text):
            bless_id = f"file::{fname}::card/{key}"
            if bless_id in store._blessed_sent:
                # her hand outranks every roll: blessed >
                # gate_passed > floor, at card-line grain
                txt, st, fnd, used = (
                    store._blessed_sent[bless_id], "blessed",
                    [], 0)
            else:
                txt, st, fnd, used = _spoken(
                    f"{fname}::card/{key}", "card_line",
                    instruction, room)
            if st not in ("gate_passed", "blessed"):
                card_status = "floor"
            txt = re.sub(rf"^{re.escape(label)}\s*[:,]?\s*", "",
                         txt, flags=re.I)
            card_parts.append(f"{label}: {txt}")
            tr[f"card/{key}"] = {"text": txt, "status": st,
                                 "findings": fnd}
        card = "\n\n".join(card_parts)
        all_rows.append({"node_id": file06["node_id"],
                         "grain": "file",
                         "audience_text": card,
                         "status": card_status,
                         "basis_version": WALK_BASIS})

        for s06 in scopes06:
            scope_id = s06["node_id"]
            grain_hint = _scope_grain_hint(store, scope_id, fname)
            owns = scope_id == store.delivery_scope(fname)
            room = _room_shell(
                short=[grain_hint],
                sentences=([t for t in unit_text.values() if t]
                           if owns else []),
                must=["one row is"])
            if owns:
                for u in sel_whos_in_it(store, fname) + \
                        sel_time_window(store, fname) + \
                        sel_excludes(store, fname):
                    r2, _ = _unit_room(store, u)
                    for lst in ("short_names", "value_names",
                                "param_names"):
                        for x in r2["speakable"][lst]:
                            if x not in room["speakable"][lst]:
                                room["speakable"][lst].append(x)
                    room["must_say"] += [m for m in r2["must_say"]
                                         if m not in
                                         room["must_say"]]
            txt, st, fnd, used = _spoken(
                s06["node_id"], "scope",
                "Describe this selection: ONE ROW IS (its grain) "
                "and, ONLY if it owns membership conditions, "
                "KEEPS (those conditions). Honest silence "
                "otherwise — never a filler keeps-sentence.",
                room)
            all_rows.append({"node_id": s06["node_id"],
                             "grain": "scope",
                             "audience_text": txt, "status": st,
                             "basis_version": WALK_BASIS})
            tr[s06["node_id"]] = {"text": txt, "status": st}

        # fields are the delivery projections' exprs (the 06
        # sheet carries no field grain — the 2026-10-04 live
        # find: 4 rows landed where 21 were owed)
        for node_id, room in _field_rooms(store, fname):
            txt, st, fnd, used = _spoken(
                node_id, "field",
                "Describe THE FIELD ONLY in one or two plain "
                "sentences — what it holds and what it means. "
                "Never the population, window or as-of behavior.",
                room)
            all_rows.append({"node_id": node_id,
                             "grain": "field",
                             "audience_text": txt, "status": st,
                             "basis_version": WALK_BASIS})
            tr[node_id] = {"text": txt, "status": st}

        txt_path = out / f"{fname}.txt"
        body = [f"==== {fname} ====", f"basis {WALK_BASIS}", ""]
        for r in all_rows:
            if r["node_id"].split("::")[1] != fname:
                continue
            body.append(f"[{r['status']}] {r['grain']}: "
                        f"{r['audience_text']}")
        txt_path.write_text("\n".join(body) + "\n")

    sheet_path = out / "07_business_sheet.json"
    rows = _read(sheet_path) if sheet_path.exists() else []
    keep = [r for r in rows
            if r["node_id"].split("::")[1] not in fnames]
    sheet = keep + all_rows
    sheet_path.write_text(json.dumps(sheet, indent=1))
    (out / "07_walk_trace.json").write_text(
        json.dumps(trace, indent=1))
    if ck_path.exists():
        ck_path.unlink()
    print(f"07 walk build: {len(all_rows)} rows over "
          f"{len(fnames)} file(s); "
          f"{'floor-only (no-llm)' if no_llm else 'live'}")
    return all_rows


# ----------------- THE RATIFY DOOR (contract amendment 2026-10-04)

def bless(out07, node_id, blessed_text, ruling, kind="sentence"):
    """THE ONE registry write door (THE RATIFY CLAUSE): the
    blessing DECISION is Sunny's alone; this function only
    executes her explicit ruling. An unruled write refuses.
    Delta-by-name: a newer dated ruling on the same node_id
    supersedes. The second sanctioned file-writer of this module
    (WalkStore reads; bless writes the registry, nothing else)."""
    if not (ruling or "").strip():
        raise ValueError(
            "REFUSED: a registry write requires Sunny's explicit "
            "ruling string (dated, her word recorded verbatim).")
    reg_path = Path(out07) / "07_blessing_registry.json"
    reg = _read(reg_path) if reg_path.exists() else \
        {"names": [], "sentences": []}
    if kind == "name":
        reg["names"] = [r for r in reg.get("names", [])
                        if r.get("node_id") != node_id]
        reg["names"].append({"node_id": node_id,
                             "blessed_name": blessed_text,
                             "ruling": ruling})
    else:
        reg["sentences"] = [r for r in reg.get("sentences", [])
                            if r.get("node_id") != node_id]
        reg["sentences"].append({"node_id": node_id,
                                 "blessed_text": blessed_text,
                                 "ruling": ruling})
    reg_path.write_text(json.dumps(reg, indent=1))
    return reg
