"""Phase 06 — technical descriptions, THE DETERMINISTIC HALF.

Contract: AIVIA_01_Design/06_technical_descriptions_data_contract.md
(APPROVED 2026-10-02). Zero LLM calls — the two-machines ruling:
every sentence renders mechanically from the stored 05 graph + the
02 dictionary; every word traces to a stored row.

Stages mirror the build ladder (06_technical_descriptions.md):
  L03 predicate voicing (THIS SLICE) · L04 condition composition ·
  L05 scope sentences · L06 statements/file/ledger · L07 texts+SVGs.

Prior art consulted, never re-derived (Brief_05_Prior_Art §3):
Grammar_Floor.md R4-R8 verbatim; aisql/flows/produce.py
_voice_predicate/_voice_negated (the ruled negation closed set).
"""

# ==== L03 PSEUDO CODE — awaiting Sunny's approval ===================
# (standing process: the real code lands right below this block
# only after her stamp; tests are red now.)
#
# BASIS_VERSION = "06.3.0"  # 06.3.0: gap-check rulings (7 voicings, Supplemental: strip, instant temporal) 2026-10-03
#   The 06 grammar constant; stamped on every output row; bumped on
#   any wording-law change.
#
# LOADING (read-only inputs, per contract):
#   _load_graph(dir05)   -> the 11 sheets, indexed:
#       expr_by_id, pred_rows, roles: pred_id -> {role: [expr_id]}
#       (from contains edges), resolves: from_id -> [rows]
#       (star_member fans arrive as lists).
#   _load_words(dir02)   -> column words + value meanings:
#       words[TABLE][COLUMN] = (subject_words, gap_flag)  # R5
#       values[TABLE][code] = meaning                      # 3a
#   _load_sql(dir01)     -> file lines for R8 (the ONE permitted
#       raw-SQL read: the trailing same-line comment at a
#       predicate's evidence line).
#
# R5 — SUBJECT WORDS (ported verbatim):
#   from column_description's FIRST sentence: strip leading
#   article + terminal period; if the shape is "<X> of|for the <Y>"
#   reorder to "<Y> <head(X)>" (head = first word of X:
#   "date of the visit" -> "visit date"); otherwise the phrase
#   stands. Awkward-but-grounded beats raw tokens. No description:
#   the readable form of the column name (underscores -> spaces,
#   lowercased) AND a counted column_words_gap row (contract class,
#   amended today) — never silent.
#   NAME WORDS (R5.c lineage, recordedness only): the readable
#   column name — "is recorded" IDENTIFIES its column, it does not
#   teach its meaning. NO owner-possessive here (blessed names are
#   Phase II; the 's rule rode the blessed tier).
#
# 3a — VALUE WORDS (THE WORDING RULING, flagged for Sunny):
#   a comparand literal whose resolves row binds to_kind=value
#   voices MEANING-FIRST AND QUOTED: "'Lucky' (7)" (quoted form
#   RULED 2026-10-03; was bare in 06.1.0) — per the ruled 3a
#   department example (the REAL ruled text lives in the 06 design
#   doc; an INVENTED stand-in here — "department is 'North Annex'
#   (900000001)" — because code TRAVELS and customer values never
#   do; the wheel canary enforces, 2026-10-04). This SUPERSEDES the
#   prior estate's code-first "7 ('Lucky')" format, uniformly (EQ,
#   IN_LIST members, everywhere). Unbound literals stay bare, as
#   written in the SQL. [Sunny confirms or flips at this approval.]
#
# R4 — PREDICATE VOICINGS (total over the closed kind set):
#   COMPARE_EQ   "The {subject} is {value}."
#   COMPARE_NEQ  "The {subject} is not {value}."
#   GTE/GT/LTE/LT: temporal when the subject words contain "date"
#     or "time" ("is on or after / is after / is on or before /
#     is before"); numeric otherwise ("is at least / exceeds /
#     is at most / is below"). The word test decides; no type
#     metadata consulted.
#   PATTERN_MATCH by wildcard shape of a literal pattern:
#     trailing % -> "starts with '{stem}'"; leading % -> "ends
#     with '{stem}'"; both -> "contains '{stem}'"; else ->
#     "matches the pattern {pattern}".
#   IN_LIST  "The {subject} is one of the values {m1, m2, ...}"
#     (member order = declared position; meanings where bound).
#   RANGE    "The {subject} is between {lower} and {upper}
#     (inclusive)."
#   NULL_CHECK "The {subject} has no recorded value."
#   EXISTS_SELECTION "A matching record exists in a separately
#     defined selection."   (the nested-selection detail phrase is
#     L04/L05 territory — this slice voices the floor form)
#   IN_SELECTION "The {subject} is one of the values defined by
#     another selection."
#   QUANTIFIED_COMPARE: the comparison voicing against "every row
#     of" (ALL) / "any row of" (ANY, SOME) "another selection".
#
# R6 — DEGENERATES: a predicate whose every operand is a literal
#   (1 = 1) voices NOTHING; it lands a counted
#   degenerate_never_voiced row. No sentence contains "1 = 1".
#
# NEGATION (the ruled closed set, produce.py _voice_negated):
#   negated=True on the 05 row. NULL_CHECK -> the POSITIVE fact,
#   name-words subject: "The {name words} is recorded."
#   Order/equality comparisons FLIP to their opposite kind (GTE<->
#   LT, GT<->LTE, EQ<->NEQ) and voice positively. IN_LIST -> "is
#   none of the values ...". IN_SELECTION -> "is not one of the
#   values defined by another selection." EXISTS_SELECTION -> "No
#   matching record exists in a separately defined selection."
#   PATTERN_MATCH negates its verb ("does not start with" /
#   "does not end with" / "does not contain" / "does not match
#   the pattern"). Anything else keeps the honest wrapper: "It is
#   not the case that {inner}."
#
# R8 — ANNOTATIONS (evidence, never fact): the trailing same-line
#   comment at the predicate's evidence line (after the fragment),
#   whitespace collapsed, capped 60 chars. Predicate-level: the
#   sentence gains " (annotated '{text}' in the source)".
#   IN_LIST member-level: the member renders "{value} (noted
#   '{text}')". Precedence: a DECLARED meaning always wins the
#   voicing; declared + annotation disagreeing = the declared
#   meaning voiced AND a counted annotation_disagreement row
#   (contract class, amended today). Only trailing same-line
#   comments annotate; a block comment above a WHERE belongs to
#   nothing, deterministically.
#
# PUBLIC (this slice):
#   render_predicates(dir05, dir02, dir01)
#     -> (rows, counted)
#     rows:    description-sheet rows for grain "predicate":
#              node_id (the 05 pred node), grain, sentence,
#              basis_version, evidence_refs (the pred node +
#              its operand expr ids + any resolves rows used).
#     counted: ledger rows minted HERE, landing in
#              06_technical_descriptions_voicing_output.json at L06 (the contract names
#              the landing step — the placeholder law's ledger
#              arm): degenerate_never_voiced, column_words_gap,
#              annotation_disagreement.
#   Determinism: rows in predicate node_id order; same inputs,
#   same bytes.
# ==== (pseudo code APPROVED 2026-10-02, Sunny: "go" — 3a
#       meaning-first confirmed; real code follows) ================
#
# ==== L04 PSEUDO CODE — awaiting Sunny's approval ===================
# Condition composition: boolean trees to prose. Prior art ported,
# never re-derived: Grammar_Floor R2 (predicate-identity grain),
# R3 (shape preservation: an OR is ONE phrase — splitting it into
# bullets silently turns it into an AND), produce.py _bt_condition
# (the recursive compose: AND -> " and ", OR -> " or " with
# nested ORs prefixed "either ", degenerates pruned, single child
# collapses).
#
# WHICH TREES (the condition grain, decision 2): one row per
#   WHERE structure, HAVING structure, JOIN structure's condition
#   tree (the ON), and IF/WHILE condition tree. node_id = the
#   owning structure node. sentence = the composed phrase,
#   capitalized, terminal period.
#
# THE COMPOSE (recursive over contains edges, position order):
#   leaf predicate -> its L03 sentence, trailing period stripped
#     (annotations ride along inside the phrase);
#     degenerate leaf -> pruned (already counted at L03).
#   AND  -> children joined " and " (first letters lowered after
#     the first child).
#   OR   -> children joined " or "; top-of-tree OR stays plain,
#     a NESTED or-group is prefixed "either " (R3's shape law).
#   NOT  -> "it is not the case that {inner}" (leaf-level
#     negation is already folded into the 05 rows; this handles
#     the structural NOT over a group).
#   single surviving child -> collapses to that child's phrase.
#
# ALL-DEGENERATE TREE (flag A, Sunny's call at this approval):
#   a tree whose every leaf is degenerate (WHERE 1 = 1) composes
#   to the empty phrase -> NO description row; ONE counted ledger
#   row (class degenerate_never_voiced, grain condition) — the
#   silence is by rule and lands in the equation. The scope-level
#   honest no-conditions sentence (R7) is L05's.
#
# ON_CLASS ROUTING (3b, flag B): the JOIN tree's description row
#   voices the NEUTRAL composed phrase at this grain (the
#   condition's content). The ROUTING is exposed to L05 as
#   partitioned phrases — per tree: {join_pair: [...],
#   lookup_shaping: [...], population_filter: [...]} (per-leaf
#   on_class from the 05 predicate rows) — so the scope sentence
#   places each where 3b rules (join phrase / attachment rule /
#   membership bullets). Placement happens at L05, never here.
#
# PUBLIC (this slice):
#   render_conditions(dir05, dir02, dir01)
#     -> (rows, counted, parts)
#     rows:    condition-grain description rows (node_id, grain
#              "condition", sentence, basis_version,
#              evidence_refs = the tree's structure + leaf ids).
#     counted: all-degenerate-tree rows (grain condition) PLUS
#              everything L03 mints (it runs the leaves).
#     parts:   {tree node_id: {on_class: [leaf phrases]}} — the
#              L05 routing feed; internal API, never stored.
# ====================================================================

# ==== L05 PSEUDO CODE — awaiting Sunny's approval ===================
# Scope sentences: THE CENTRAL SENTENCE, one row per scope (all 36,
# union arms included). Prior art ported: Grammar_Floor R1 (lead),
# R7 (honest no-conditions), R10's spirit at scope grain, R12
# (computed outputs: the function library + composite rules),
# produce.py scope_sentence (lead · membership · kept · payload).
#
# SHAPE:
#   "{LEAD}{, join phrases}: {membership}; {kept-rule};
#    grouped per {g}; carrying {payload items}."
#
# LEAD (FLAG C, Sunny's call): R1's ratified lead speaks the
#   source's GRAIN ("a selection of patient encounters") — but our
#   02 dictionary carries NO table-grain metadata, so that lead
#   cannot port honestly. Proposal: name the sources as stored —
#   "This is a selection from T1" / "from #census_monthly";
#   DELETE -> "This step removes records from {source}." (R1
#   verbatim); no tables read -> "This step produces derived
#   values; no source records are read" (R1 verbatim). Grain-words
#   can upgrade the lead in a later phase when the dictionary
#   learns grains.
# JOINS (3b, from L04's routing feed, position order):
#   inner-family -> ", joined with {source} (matched where {pair
#   phrases})"; preserved-side joins (LEFT/RIGHT/FULL) ->
#   ", attaching {source} (matched where {pairs}; attachment
#   rule: {lookup phrases})" — an attachment NEVER reads as a
#   filter. population_filter leaves join the MEMBERSHIP instead.
# MEMBERSHIP: the WHERE phrase (uncapitalized) + any
#   population_filter join phrases, '; '-joined. Empty -> R7:
#   "no membership conditions are applied".
# KEPT-RULE: a TOP structure -> "; the first {n} records are
#   kept". (ROW_NUMBER-kept detection needs OVER contents — see
#   FLAG D.)
# GROUP BY -> "; grouped per {column words, ...}".
# PAYLOAD -> "; carrying {items}", one item per projection output:
#   - column bound to a base column -> "the {subject words}"
#     (alias differing from the column -> "{alias words} (the
#     {subject words})").
#   - MEMBER lineage (3c) -> "{name words} (built in {scope},
#     from {origin TABLE.COLUMN})" — the walked chain.
#   - STAR_MEMBER dual (3c as reopened) -> "{name words} (read
#     through {scope}, origins {A} and {B})" — both arms voiced.
#   - BEHIND_STAR -> "{name words} (from {scope}, read through a
#     SELECT *; base origin not traced)" — honestly blind.
#   - COMPUTED (R12): "{name words} ({defining phrase})", the
#     expression voiced INSIDE-OUT: named functions by their
#     Function_Voicings row (renderers in code, one per ported
#     row; a coverage test pins code == library); composites by
#     rule — case -> "a value derived by rule"; cast ->
#     TRANSPARENT (voices as its inner); unary folds the sign;
#     arithmetic -> plus · minus · times · divided by. An
#     operation with NO row -> "a value computed from {operand
#     words}" + counted unvoiced_function (the ruled remainder).
#   - literal -> "{name words} (the constant {raw})"; star ->
#     "every column of {source}".
# COMBINATION scopes -> "This selection combines {n}
#   alternatives."; the arms speak their own full rows.
# FLAG D (measured, Sunny's call): 05 does not capture OVER-clause
#   contents, so ROW_NUMBER / LAG / LEAD (library rows that NEED
#   partition/order words) voice as the counted remainder — the 2
#   corpus ROW_NUMBERs land counted, a measured 05 gap; capturing
#   OVER is a future 05 amendment, not a silent guess here.
# PREDICTED UNVOICED CENSUS (corpus, for her words at gap-check):
#   MAX, COUNT, CONCAT, CHAR, SUM, FORMAT (+ the 2 ROW_NUMBER
#   remainders above).
# PUBLIC: render_scopes(dir05, dir02, dir01) -> (rows, counted)
#   rows: grain "scope", node_id = the scope node, sentence as
#   shaped above; counted: everything the leaves and the payload
#   mint. Deterministic: scope node_id order.
# ====================================================================

# ==== L06 PSEUDO CODE — awaiting Sunny's approval ===================
# Statements (R11) · the file floor (R10/R13 three levels) · the
# gap sentence (3e) · parameter voicing (3d) · THE VOICING LEDGER
# (decision 5). Prior art: Grammar_Floor R10/R11/R13 verbatim;
# inbound._render_technical_definition (the three-level shape).
#
# STATEMENT GRAIN (R11, the ported closed library):
#   SELECT INTO -> "Builds the {name} selection." (name fold:
#     # stripped, underscores to spaces, lowercased); CTE helpers
#     "..., preparing the {x} selection first." in declaration
#     order.
#   SELECT (emits) -> "Delivers the procedure's result set."
#   IF -> "A decision step, taken when {condition phrase}."
#     (zero corpus cases; wired for the fabricated estates)
#   A handled kind with NO voicing row (the corpus's 8 SET
#     assignments) -> counted unvoiced_statement_kind, visible,
#     awaiting her words. Operational -> counted
#     operational_statement. Gap -> counted dynamic_sql_gap (its
#     speech is the FILE floor's gap sentence, below).
#
# FILE GRAIN — THE THREE LEVELS (R13 v2 as ported):
#   (1) HEADLINE: per delivery, "Delivers a selection from ..."
#     — the delivery scope's L05 sentence with the lead rewritten
#     "This is a selection" -> "Delivers a selection" ("This step
#     produces derived values" -> "Delivers derived values").
#     NO delivery -> the last built scope's sentence + "Builds
#     {n} working selections; delivers nothing." (never silent).
#   (2) PIPELINE: "Pipeline: (1) {step}. (2) {step}." — voiced
#     statement lines only, build order.
#   (3) APPENDIX:
#     "Presents: {delivery payload items ; -joined}."
#     "Population: In {selection}: {WHERE phrase}. ..." — the
#       delivery chain (delivery + transitively read named
#       scopes), grouped per selection, chain order; outer-join
#       attachment rules EXCLUDED (they do not restrict).
#     "Inner joins: In {selection}: {pair phrases}. ..." — inner
#       only, per Sunny's ruled "(inner)".
#   PARAMETERS (3d): "Parameters shaping the population: @X
#     (default \"{default_text verbatim}\"); @Y (no default)."
#     — only parameters a predicate actually binds to (resolves
#     to_kind parameter from a pred expr).
#   THE GAP SENTENCE (3e — FLAG E, contract amendment needed):
#     05 stores NO expression trees for the SET assembly
#     statements (handled, scope-less), so the shaper list
#     promised by the contract is not derivable from stored rows.
#     AMENDED SHAPE (for her stamp): "Part of this file's logic
#     is built as a string at run time and is not described
#     here; it is executed by \"{gap evidence fragment}\". {k} of
#     {n} statements are in this gap." Naming the fed parameters
#     becomes a NAMED FUTURE CLASS, contingent on a 05 SET-
#     capture amendment (same family as the OVER amendment).
#   CENSUS CLOSE (R10.3): "Steps: {total}, {voiced} voiced,
#     {operational} operational, {gap} gap. Selections: {named
#     scope list}." — honest mechanics, always last.
#
# THE LEDGER (decision 5 — FLAG F, the equation's exact terms):
#   render_all(dir05, dir02, dir01) -> (rows, ledger): ONE pass,
#   all five grains, counted rows deduped by (node_id, class).
#   THE EQUATION, per file per grain (the contract's test):
#     predicate: rows + degenerate_never_voiced == pred total
#     condition: rows + condition-grain degenerates == tree total
#     scope:     rows == scope total
#     statement: rows + operational + gap + unvoiced == stmt total
#     file:      exactly one row per file
#   lookup_shaping_attachment rows are the APARTNESS record (the
#   predicate IS voiced — as an attachment — and additionally
#   counted apart from membership); they stand OUTSIDE the
#   silence equation. [FLAG F: this reading for her stamp.]
# ====================================================================

# ==== L07 PSEUDO CODE — awaiting Sunny's approval ===================
# The artifacts land: the sheet, the ledger, the eyeball texts
# (decision 6), the SVGs (decision 8), the build command
# (contract): technical_descriptions.py <dir05> <out06> <dir02>
# <dir01> -> writes into AIVIA_01_Data/06_technical_descriptions/.
#
# ==== PSEUDO — 0.8.0 COMMENT-FIRST (D15, ruled 2026-10-08 ====
# evening; contracts amended same day; AWAITING SUNNY'S
# APPROVAL; red tests before code):
#
#   R8 PRECEDENCE FLIPS (the 06 contract's amendment):
#   1. A trailing same-line comment on a value predicate is
#      voiced AS THE MEANING, 3a's meaning-first shape:
#        "The pcp id is not 'TAPESTRY GENERIC PCP' (47080)."
#      The "(annotated '...' in the source)" suffix retires for
#      predicates that carry a comment — the comment IS the
#      voice now. A DECLARED dictionary meaning that disagrees
#      is the counted annotation_disagreement (read the other
#      way from 2026-10-02). No comment -> everything exactly
#      as today. BASIS_VERSION bumps 06.3.0 -> 06.4.0; the two
#      pinned sentences re-pin (the byte-exact posture's ruled
#      path, never a drift).
#   2. THE HEADER READ (one new helper beside _comment_at, the
#      same one-permitted-raw-read law): header_description(
#      sql_dir, stem) -> the text after "Description:" in the
#      file's leading block comment (up to the next labeled
#      line or the comment's end, whitespace collapsed), or
#      None. Stored NOWHERE — read at build time, offered to
#      the 07 docket (her no-side-store ruling).
# ===============================================================
#
# ==== PSEUDO — 0.7.0 THE 06 RENAMES (the naming law, ruled ====
# 2026-10-08, step table row 06; AWAITING SUNNY'S APPROVAL):
#   06_description_sheet.json -> 06_technical_descriptions_output.json
#   06_voicing_ledger.json    -> 06_technical_descriptions_voicing_output.json
#   THE PER-FILE <name>.txt / <name>.svg KEEP THEIR NAMES
#   [flagged]: they are named by their subject sql file — the
#   step identity rides the folder; suffixing hundreds of
#   per-file artifacts adds noise, not truth.
#   No migration read: regenerated whole by every build (the 05
#   precedent). Readers flip in the same landing: ai_delivery,
#   sqldesc_cli (report_descriptions), business_descriptions,
#   business_terms, business_walk + fixtures.
# ===============================================================
#
# build06(dir05, out06, dir02, dir01):
#   rows, ledger = render_all(...)
#   writes 06_technical_descriptions_output.json (the rows, five grains),
#          06_technical_descriptions_voicing_output.json   (the counted rows),
#          <file_name>.txt  one per corpus file,
#          <file_name>.svg  one per corpus file;
#   prints the census (rows per grain, ledger per class) and
#   RETURNS it — the descriptions-in-the-loop law's hook.
#
# THE TEXT (decision 6's blocks, ruled order scope-statement-file;
# FLAG G, the modernized format for Sunny's stamp):
#   ==== <file_name> ====
#   basis <BASIS_VERSION>
#   -- THE SELECTIONS --
#   <scope_name>: <scope sentence>          (scope-sheet order)
#   -- THE STEPS --
#   (<pos>) <statement sentence>            (voiced steps)
#   (<pos>) [<counted class>]               (silent steps, loud)
#   -- THE FILE --
#   <the three-level floor, verbatim from the file row>
#
# THE SVG (decision 8 as ruled — deterministic, plain Python,
# fixed char-width metrics, zero randomness):
#   statements down the spine (y-stacked, position order), each
#   voiced sentence or [counted class]; the owned scopes as boxes
#   beneath, each listing its structures in position order (FROM/
#   JOIN sources by stored raw text, WHERE/ON predicate leaves by
#   their evidence fragments, a value bind suffixed
#   "= '<meaning>' (<code>)", PROJECTION as member/star counts);
#   RESOLVES EDGES drawn across on the right margin — one
#   polyline per distinct (reading scope, source scope, basis),
#   color by basis (member / star_member both arms / behind_star
#   / fold), label = the basis word; the dynamic-SQL gap a
#   red-stroked statement line, marked visibly.
#   A node with no sheet row cannot appear (everything drawn
#   reads from the 05/06 rows). Byte-stable: two builds, same
#   bytes — pinned by test.
# ====================================================================

import json
import re
from pathlib import Path

BASIS_VERSION = "06.3.0"  # 06.3.0: gap-check rulings (7 voicings, Supplemental: strip, instant temporal) 2026-10-03

_ARTICLE = re.compile(r"^(the|a|an)\s+", re.IGNORECASE)
_OF_FOR_THE = re.compile(r"^(.+?)\s+(?:of|for)\s+the\s+(.+)$")


def _read(path: Path):
    return json.loads(path.read_text())


def _readable(name: str) -> str:
    return name.lower().replace("_", " ").strip()


def _noun_phrase(description: str):
    """R5: the description's first sentence as a noun phrase.
    -> (words, gap) — gap True when there is no description and
    the readable column name stands in (counted, never silent)."""
    text = (description or "").strip()
    if text.lower().startswith("supplemental:"):
        # the strip law (ruled 2026-10-03): provenance lives in
        # the SUPP:: id, never in prose
        text = text[len("supplemental:"):].strip()
    if not text or text.lower() in ("null", "none", "nan", "n/a"):
        return None, True  # a 'NULL'-string description is no
        # description (the ZC_PAT_SERVICE.HOSP_SERV_C corpus find)
    first = re.split(r"(?<=\.)\s", text)[0].rstrip(".").strip()
    first = _ARTICLE.sub("", first)
    m = _OF_FOR_THE.match(first)
    if m:
        head = m.group(1).split()[0]
        return f"{m.group(2)} {head}", False
    return first, False


def _load_words(dict_dir: Path):
    cols = _read(dict_dir /
                 "02_emr_data_dictionary_extraction_column.json")
    words = {}
    for c in cols:
        tu, cu = c["table_name"].upper(), c["column_name"].upper()
        phrase, gap = _noun_phrase(c.get("column_description", ""))
        words[(tu, cu)] = (phrase if phrase is not None
                           else _readable(c["column_name"]), gap)
    vals = _read(dict_dir /
                 "02_emr_data_dictionary_extraction_value.json")
    values = {}
    for v in vals:
        values[(v["table_name"].upper(), str(v["code"]))] = \
            v["meaning"]
    return words, values


def _load_graph(dir05: Path):
    g = {
        "preds": _read(dir05 / "05_semantic_graph_predicate_output.json"),
        "exprs": {e["node_id"]: e for e in
                  _read(dir05 / "05_semantic_graph_expression_output.json")},
    }
    g["pred_by_id"] = {p["node_id"]: p for p in g["preds"]}
    g["struct_kind"] = {s["node_id"]: s["structure_kind"] for s in
                        _read(dir05 / "05_semantic_graph_structure_output.json")}
    g["roles"], g["children"] = {}, {}
    for e in _read(dir05 / "05_semantic_graph_contains_edges_output.json"):
        if e.get("role"):
            g["roles"].setdefault(e["from_id"], []).append(e)
        pos = str(e["position"]).split(".")[0]
        key = ((0, int(pos), "") if pos.isdigit()
               else (1, 0, pos))  # subquery edges ('sub1') after
        g["children"].setdefault(e["from_id"], []).append(
            (key, e["to_id"]))
    for lst in g["roles"].values():
        lst.sort(key=lambda e: int(str(e["position"])))
    g["children"] = {k: [t for _, t in sorted(v)]
                     for k, v in g["children"].items()}
    g["resolves"] = {}
    for r in _read(dir05 / "05_semantic_graph_resolves_edges_output.json"):
        g["resolves"].setdefault(r["from_id"], []).append(r)
    return g


def _load_sql(sql_dir: Path):
    """R8's one permitted raw read: file lines, for trailing
    same-line comments only."""
    lines = {}
    for p in sorted(Path(sql_dir).iterdir()):
        if p.is_file() and not p.name.startswith(".") \
                and p.suffix != ".json":
            lines[p.stem] = p.read_text().splitlines()
    return lines


def _comment_at(lines_by_file, node_id, line_no):
    """The trailing same-line comment at a 1-based line, collapsed,
    capped 60 — or None. (A '--' inside a string literal would
    false-match; the corpus has none and the sentence would still
    quote verbatim estate text — grounded either way.)"""
    stem = node_id.split("::")[1]
    lines = lines_by_file.get(stem)
    if not lines or not (1 <= line_no <= len(lines)):
        return None
    line = lines[line_no - 1]
    idx = line.find("--")
    if idx < 0:
        return None
    text = re.sub(r"\s+", " ", line[idx + 2:]).strip()
    return text[:60] if text else None


class _Voice:
    """Operand words over the stored graph (R5 + 3a)."""

    def __init__(self, graph, words, values):
        self.g, self.words, self.values = graph, words, values
        self.counted = []
        self.refs = []          # evidence_refs for the current row

    def _column_words(self, to_id, pred_id, expr_id=None):
        tu, cu = to_id.split(".", 1)
        phrase, gap = self.words.get(
            (tu.upper(), cu.upper()),
            (_readable(cu), True))
        if gap:
            # the gap row carries the READ (the expression node):
            # the dictionary-growth queue counts every gap read
            self.counted.append({"node_id": expr_id or pred_id,
                                 "class": "column_words_gap",
                                 "grain": "predicate",
                                 "basis_version": BASIS_VERSION})
        self.refs.append(to_id)
        return phrase

    def subject(self, expr_id, pred_id, depth=0):
        """Subject words: a column bind speaks its dictionary
        words; a member/star_member bind walks one hop toward its
        origin (full lineage phrasing is L05's); anything else
        speaks the readable form of the written reference."""
        self.refs.append(expr_id)
        for r in self.g["resolves"].get(expr_id, []):
            if r["to_kind"] == "column":
                return self._column_words(r["to_id"], pred_id,
                                          expr_id)
            if r["to_kind"] == "member" and depth < 8:
                return self.subject(r["to_id"], pred_id, depth + 1)
        expr = self.g["exprs"].get(expr_id, {})
        # a COMPUTED member speaks its author's output name (R12
        # name-words law) — never the defining expression's raw
        # tokens (the 'calendar dt))' corpus find, 2026-10-03)
        if expr.get("output_name"):
            return _readable(expr["output_name"])
        token = (expr.get("ref") or expr.get("raw_text") or "value")
        return _readable(token.split(".")[-1])

    def name_words(self, expr_id):
        """Recordedness identifies its column (R5.c lineage,
        possessive-free): the readable column name."""
        self.refs.append(expr_id)
        expr = self.g["exprs"].get(expr_id, {})
        token = (expr.get("ref") or expr.get("raw_text") or "value")
        return _readable(token.split(".")[-1])

    def value(self, expr_id, pred_id=None):
        """3a MEANING-FIRST: 'Lucky (7)' when the literal binds to
        a value row; a COLUMN comparand speaks its words prefixed
        'the' (R5: raw tokens never reach prose — the join shape);
        the literal as written otherwise.
        -> (text, declared_meaning or None)."""
        self.refs.append(expr_id)
        expr = self.g["exprs"].get(expr_id, {})
        raw = expr.get("raw_text", "")
        for r in self.g["resolves"].get(expr_id, []):
            if r["to_kind"] == "value":
                tu, code = r["to_id"].split("::", 1)
                meaning = self.values.get((tu.upper(), code))
                if meaning:
                    self.refs.append(r["to_id"])
                    return f"'{meaning}' ({code})", meaning
        if expr.get("expression_kind") == "column_ref":
            return ("the " + self.subject(expr_id, pred_id)), None
        return raw, None


_NEGATED_COMPARE = {"COMPARE_GTE": "COMPARE_LT",
                    "COMPARE_GT": "COMPARE_LTE",
                    "COMPARE_LTE": "COMPARE_GT",
                    "COMPARE_LT": "COMPARE_GTE",
                    "COMPARE_EQ": "COMPARE_NEQ",
                    "COMPARE_NEQ": "COMPARE_EQ"}

_ORDER_VERBS = {  # (temporal, numeric) — the R4 word test decides
    "COMPARE_GTE": ("is on or after", "is at least"),
    "COMPARE_GT": ("is after", "exceeds"),
    "COMPARE_LTE": ("is on or before", "is at most"),
    "COMPARE_LT": ("is before", "is below"),
}

def _is_temporal(words):
    """The ruled temporal word test: date | time | instant
    (instant added 2026-10-03, gap-check item 4)."""
    return any(w in words for w in ("date", "time", "instant"))


def _bare(phrase):
    """Drop a leading article so 'the earliest the visit date'
    can never render."""
    return phrase[4:] if phrase.startswith("the ") else phrase


_PATTERN_NEGATION = {"starts with": "does not start with",
                     "ends with": "does not end with",
                     "contains": "does not contain",
                     "matches the pattern":
                     "does not match the pattern"}


def _role_ids(graph, pred_id, role):
    return [e["to_id"] for e in graph["roles"].get(pred_id, [])
            if e["role"] == role]


def _is_degenerate(graph, pred_id):
    """R6: every operand a literal (1 = 1)."""
    operands = [e["to_id"] for e in graph["roles"].get(pred_id, [])
                if e["role"] in ("subject", "comparand",
                                 "lower_bound", "upper_bound",
                                 "pattern")]
    return operands and all(
        graph["exprs"].get(x, {}).get("expression_kind") == "literal"
        for x in operands)


def _pattern_verb(raw_pattern):
    pat = raw_pattern.strip()
    literal = pat.startswith("'") and pat.endswith("'")
    stem = pat[1:-1] if literal else pat
    if literal and stem.endswith("%") and "%" not in stem[:-1] \
            and not stem.startswith("%"):
        return "starts with", f"'{stem[:-1]}'"
    if literal and stem.startswith("%") and "%" not in stem[1:]:
        return "ends with", f"'{stem[1:]}'"
    if literal and stem.startswith("%") and stem.endswith("%") \
            and "%" not in stem[1:-1]:
        return "contains", f"'{stem[1:-1]}'"
    return "matches the pattern", pat


def _voice_positive(kind, pred, voice, graph):
    pid = pred["node_id"]
    subj_ids = _role_ids(graph, pid, "subject")
    sw = voice.subject(subj_ids[0], pid) if subj_ids else None

    if kind == "COMPARE_EQ" or kind == "COMPARE_NEQ":
        val, meaning = voice.value(
            _role_ids(graph, pid, "comparand")[0], pid)
        verb = "is" if kind == "COMPARE_EQ" else "is not"
        return f"The {sw} {verb} {val}.", meaning
    if kind in _ORDER_VERBS:
        temporal = _is_temporal(sw)
        verb = _ORDER_VERBS[kind][0 if temporal else 1]
        val, meaning = voice.value(
            _role_ids(graph, pid, "comparand")[0], pid)
        return f"The {sw} {verb} {val}.", meaning
    if kind == "PATTERN_MATCH":
        raw = graph["exprs"][
            _role_ids(graph, pid, "pattern")[0]]["raw_text"]
        verb, shown = _pattern_verb(raw)
        return f"The {sw} {verb} {shown}.", None
    if kind == "IN_LIST":
        members = [voice.value(x, pid)[0]
                   for x in _role_ids(graph, pid, "comparand")]
        return (f"The {sw} is one of the values "
                f"{', '.join(members)}.", None)
    if kind == "RANGE":
        lo, _ = voice.value(_role_ids(graph, pid, "lower_bound")[0],
                            pid)
        hi, _ = voice.value(_role_ids(graph, pid, "upper_bound")[0],
                            pid)
        return (f"The {sw} is between {lo} and {hi} "
                "(inclusive).", None)
    if kind == "NULL_CHECK":
        return f"The {sw} has no recorded value.", None
    if kind == "EXISTS_SELECTION":
        return ("A matching record exists in a separately "
                "defined selection.", None)
    if kind == "IN_SELECTION":
        return (f"The {sw} is one of the values defined by "
                "another selection.", None)
    if kind == "QUANTIFIED_COMPARE":
        # zero corpus cases; the every/any word needs a 05 field
        # when the first real case arrives — new ruling then
        return (f"The {sw} is compared against another "
                "selection.", None)
    return None, None  # unreachable: the kind set is closed


def _voice_predicate(pred, voice, graph):
    """-> (sentence or None, declared_meaning or None)."""
    kind = pred["predicate_kind"]
    pid = pred["node_id"]
    if not pred.get("negated"):
        return _voice_positive(kind, pred, voice, graph)

    if kind == "NULL_CHECK":
        nw = voice.name_words(_role_ids(graph, pid, "subject")[0])
        return f"The {nw} is recorded.", None
    if kind in _NEGATED_COMPARE:
        return _voice_positive(_NEGATED_COMPARE[kind], pred,
                               voice, graph)
    if kind == "IN_LIST":
        subj = voice.subject(_role_ids(graph, pid, "subject")[0],
                             pid)
        members = [voice.value(x, pid)[0]
                   for x in _role_ids(graph, pid, "comparand")]
        return (f"The {subj} is none of the values "
                f"{', '.join(members)}.", None)
    if kind == "IN_SELECTION":
        subj = voice.subject(_role_ids(graph, pid, "subject")[0],
                             pid)
        return (f"The {subj} is not one of the values defined by "
                "another selection.", None)
    if kind == "EXISTS_SELECTION":
        return ("No matching record exists in a separately "
                "defined selection.", None)
    if kind == "PATTERN_MATCH":
        positive, _ = _voice_positive(kind, pred, voice, graph)
        for verb, neg in _PATTERN_NEGATION.items():
            if f" {verb} " in positive:
                return positive.replace(f" {verb} ",
                                        f" {neg} ", 1), None
    positive, _ = _voice_positive(kind, pred, voice, graph)
    inner = (positive or "").rstrip(".")
    if not inner:
        return "The inner condition does not hold.", None
    return (f"It is not the case that "
            f"{inner[0].lower()}{inner[1:]}.", None)


def _leaf_sentence(pred, voice, graph, sql_lines):
    """One predicate leaf -> its full sentence (annotation
    riding), or None for a degenerate (counted here, grain
    'predicate'). Appends into voice.refs / voice.counted."""
    pid = pred["node_id"]
    if _is_degenerate(graph, pid):
        voice.counted.append({"node_id": pid,
                              "class": "degenerate_never_voiced",
                              "grain": "predicate",
                              "basis_version": BASIS_VERSION})
        return None
    voice.refs.append(pid)
    sentence, meaning = _voice_predicate(pred, voice, graph)
    if sentence is None:
        return None
    note = _comment_at(sql_lines, pid, pred["evidence"]["line"])
    if note:
        if meaning and re.sub(r"\s+", " ", note).strip().lower() \
                != meaning.strip().strip("'").lower():
            voice.counted.append(
                {"node_id": pid,
                 "class": "annotation_disagreement",
                 "grain": "predicate",
                 "basis_version": BASIS_VERSION})
        sentence = (sentence.rstrip(".")
                    + f" (annotated '{note}' in the source).")
    return sentence


def render_predicates(dir05, dir02, dir01):
    """L03's public door: every predicate leaf -> its description
    row (grain 'predicate'), plus the counted rows minted here
    (landing in 06_technical_descriptions_voicing_output.json at L06)."""
    dir05, dir02, dir01 = Path(dir05), Path(dir02), Path(dir01)
    graph = _load_graph(dir05)
    words, values = _load_words(dir02)
    sql_lines = _load_sql(dir01)
    voice = _Voice(graph, words, values)

    rows = []
    for pred in sorted(graph["preds"],
                       key=lambda p: p["node_id"]):
        voice.refs = []
        sentence = _leaf_sentence(pred, voice, graph, sql_lines)
        if sentence is None:
            continue
        rows.append({"node_id": pred["node_id"],
                     "grain": "predicate",
                     "sentence": sentence,
                     "basis_version": BASIS_VERSION,
                     "evidence_refs": list(dict.fromkeys(
                         voice.refs))})
    return rows, voice.counted


# ==== L04 — condition composition (pseudo code above, approved
#      2026-10-03 with flags A and B ruled) ==========================

_TREE_ROOTS = {"WHERE", "HAVING", "JOIN"}
_BOOLEANS = {"AND", "OR", "NOT"}


def _lower_first(s: str) -> str:
    return s[0].lower() + s[1:] if s else s


def _compose(node_id, graph, voice, sql_lines, leaves, top):
    """The R2/R3 compose over the stored tree: leaf sentences
    period-stripped; AND joins ' and '; OR joins ' or ' (nested
    or-groups prefixed 'either '); NOT wraps 'it is not the case
    that'; degenerate leaves pruned; a single survivor collapses."""
    kind = graph["struct_kind"].get(node_id)
    if kind is None:  # a predicate leaf
        pred = graph["pred_by_id"].get(node_id)
        if pred is None:
            return ""
        sentence = _leaf_sentence(pred, voice, graph, sql_lines)
        if sentence is None:
            return ""
        leaves.append((pred, sentence))
        return sentence.rstrip(".")
    if kind not in _BOOLEANS and kind not in _TREE_ROOTS:
        return ""
    child_top = top if kind in _TREE_ROOTS else False
    parts = [_compose(k, graph, voice, sql_lines, leaves,
                      child_top)
             for k in graph["children"].get(node_id, [])]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if kind == "NOT":
        return ("it is not the case that "
                + _lower_first(parts[0]))
    if len(parts) == 1:
        return parts[0]
    lowered = [parts[0]] + [_lower_first(p) for p in parts[1:]]
    if kind == "OR":
        joined = " or ".join(lowered)
        return joined if top else "either " + _lower_first(joined)
    return " and ".join(lowered)  # AND, and the root clauses


def render_conditions(dir05, dir02, dir01):
    """L04's public door: one row per WHERE / HAVING / JOIN
    condition tree (sentence = the composed phrase), the counted
    rows (incl. flag A's all-degenerate trees, grain 'condition'),
    and the 3b routing feed: per JOIN tree, its leaf phrases
    partitioned by on_class (placement happens at L05)."""
    dir05, dir02, dir01 = Path(dir05), Path(dir02), Path(dir01)
    graph = _load_graph(dir05)
    words, values = _load_words(dir02)
    sql_lines = _load_sql(dir01)
    voice = _Voice(graph, words, values)

    rows, parts = [], {}
    for tree_id in sorted(graph["struct_kind"]):
        kind = graph["struct_kind"][tree_id]
        if kind not in _TREE_ROOTS:
            continue
        has_preds = any(graph["pred_by_id"].get(k) is not None
                        or graph["struct_kind"].get(k)
                        in _BOOLEANS
                        for k in graph["children"].get(tree_id, []))
        if not has_preds:
            continue  # a JOIN with no ON tree captured, etc.
        voice.refs = [tree_id]
        leaves = []
        phrase = _compose(tree_id, graph, voice, sql_lines,
                          leaves, True)
        if not phrase:  # flag A: all leaves degenerate
            voice.counted.append(
                {"node_id": tree_id,
                 "class": "degenerate_never_voiced",
                 "grain": "condition",
                 "basis_version": BASIS_VERSION})
            continue
        rows.append({"node_id": tree_id, "grain": "condition",
                     "sentence": phrase[0].upper() + phrase[1:]
                     + ".",
                     "basis_version": BASIS_VERSION,
                     "evidence_refs": list(dict.fromkeys(
                         voice.refs))})
        by_class = {}
        for leaf, sentence in leaves:
            oc = leaf.get("on_class")
            if oc:
                by_class.setdefault(oc, []).append(
                    sentence.rstrip("."))
        if by_class:
            parts[tree_id] = by_class
    return rows, voice.counted, parts


# ==== L05 — scope sentences (pseudo code above, approved
#      2026-10-03: flags C and D as proposed) ========================

_ARITH_WORDS = {"Add": "plus", "Subtract": "minus",
                "Multiply": "times", "Divide": "divided by",
                "Modulo": "modulo"}


def _fn(op):
    """Register a Function_Voicings renderer (coverage-tested
    against the library — every ported row needs one)."""
    def wrap(f):
        FUNCTION_RENDERERS[op] = f
        return f
    return wrap


FUNCTION_RENDERERS = {}


def _unit(args):
    return (args[0][0].get("raw_text", "") or "unit").lower()


@_fn("DATEDIFF")
def _r_datediff(args):
    return (f"the number of {_unit(args)}s between {args[1][1]} "
            f"and {args[2][1]}")


@_fn("DATEADD")
def _r_dateadd(args):
    n = args[1][1]
    direction = "after"
    if n.startswith("negative "):
        n, direction = n[len("negative "):], "before"
    return f"{n} {_unit(args)}s {direction} {args[2][1]}"


@_fn("DATENAME")
def _r_datename(args):
    return f"the name of the {_unit(args)} of {args[1][1]}"


@_fn("DATEPART")
def _r_datepart(args):
    return f"the {_unit(args)} of {args[1][1]}"


@_fn("CHARINDEX")
def _r_charindex(args):
    return f"the position of {args[0][1]} within {args[1][1]}"


@_fn("LEFT")
def _r_left(args):
    return f"the first {args[1][1]} characters of {args[0][1]}"


@_fn("RIGHT")
def _r_right(args):
    return f"the last {args[1][1]} characters of {args[0][1]}"


@_fn("MIN")
def _r_min(args):
    phrase = _bare(args[0][1])
    if _is_temporal(phrase):
        return f"the earliest {phrase}"
    return f"the smallest {phrase}"


@_fn("MAX")
def _r_max(args):
    phrase = _bare(args[0][1])
    if _is_temporal(phrase):
        return f"the latest {phrase}"
    return f"the largest {phrase}"


@_fn("COUNT")
def _r_count(args):
    if not args or args[0][0].get("raw_text", "").strip() == "*"             or (args[0][0].get("ref") or "") == "*":
        return "the count of records"
    return f"the count of {args[0][1]}"


@_fn("SUM")
def _r_sum(args):
    return f"the total of {args[0][1]}"


@_fn("CONCAT")
def _r_concat(args):
    return ", ".join(p for _, p in args) + " joined into one text"


@_fn("FORMAT")
def _r_format(args):
    return f"{args[0][1]}, formatted as {args[1][1]}"


@_fn("CHAR")
def _r_char(args):
    return f"the character with code {args[0][1]}"


@_fn("FLOOR")
def _r_floor(args):
    return f"{args[0][1]}, rounded down to a whole number"


@_fn("COALESCE")
def _r_coalesce(args):
    return "the first recorded of " + ", ".join(p for _, p in args)


@_fn("ISNULL")
def _r_isnull(args):
    return (f"{args[0][1]}, or {args[1][1]} when {args[0][1]} "
            "is not recorded")


@_fn("ROUND")
def _r_round(args):
    return f"{args[0][1]} rounded to {args[1][1]} decimal places"


@_fn("STRING_AGG")
def _r_string_agg(args):
    return f"every {args[0][1]} joined into one list"


@_fn("STUFF + FOR XML PATH('')")
def _r_stuff_xml(args):
    return f"every {args[0][1]} joined into one list"


@_fn("STUFF")
def _r_stuff(args):
    last = args[-1][1] if len(args) > 1 else "a value"
    return f"{args[0][1]} with a segment replaced by {last}"


@_fn("GETDATE")
def _r_getdate(args):
    return "the current date and time"


# LAG / LEAD: their ruled voicings need the OVER clause's
# partition/order words, which 05 does not capture (flag D) —
# counted remainder until a 05 amendment. ROW_NUMBER carries the
# INTERIM ruled row (gap-check item 1, 2026-10-03); the OVER
# amendment is queued post-06.
@_fn("ROW_NUMBER")
def _r_row_number(args):
    return "its position in an ordered sequence of records"


@_fn("LAG")
def _r_lag(args):
    return None


@_fn("LEAD")
def _r_lead(args):
    return None


def _expr_phrase(expr_id, voice, owner_id):
    """R12: an expression voiced inside-out. Returns the phrase;
    mints unvoiced_function counted rows for library misses."""
    g = voice.g
    expr = g["exprs"].get(expr_id, {})
    kind = expr.get("expression_kind")
    voice.refs.append(expr_id)
    if kind == "column_ref":
        for r in g["resolves"].get(expr_id, []):
            if r["to_kind"] in ("column", "member"):
                return "the " + voice.subject(expr_id, owner_id)
        return "the " + _readable(
            (expr.get("ref") or expr.get("raw_text")
             or "value").split(".")[-1])
    if kind == "literal":
        return expr.get("raw_text", "")
    if kind == "parameter_ref":
        return expr.get("raw_text", "")
    if kind == "case":
        return "a value derived by rule"
    if kind == "cast":  # transparent (R12)
        kids = _expr_children(g, expr_id)
        return (_expr_phrase(kids[0], voice, owner_id)
                if kids else expr.get("raw_text", ""))
    if kind == "unary":
        kids = _expr_children(g, expr_id)
        inner = (_expr_phrase(kids[0], voice, owner_id)
                 if kids else expr.get("raw_text", ""))
        return ("negative " + inner
                if expr.get("op") == "Negative" else inner)
    if kind == "arithmetic":
        kids = _expr_children(g, expr_id)
        word = _ARITH_WORDS.get(expr.get("op"),
                                str(expr.get("op", "")).lower())
        return f" {word} ".join(
            _expr_phrase(k, voice, owner_id) for k in kids)
    if kind == "subquery_ref":
        return "a value from another selection"
    if kind == "function":
        kids = _expr_children(g, expr_id)
        args = [(g["exprs"].get(k, {}),
                 _expr_phrase(k, voice, owner_id)) for k in kids]
        op = (expr.get("name") or "").upper()
        renderer = FUNCTION_RENDERERS.get(op)
        phrase = renderer(args) if renderer else None
        if phrase is not None:
            return phrase
        voice.counted.append({"node_id": expr_id,
                              "class": "unvoiced_function",
                              "grain": "scope",
                              "basis_version": BASIS_VERSION})
        operands = ", ".join(p for _, p in args if p)
        return ("a value computed from " + operands if operands
                else "a value computed at run time")
    return expr.get("raw_text", "")


def _expr_children(g, expr_id):
    return [k for k in g["children"].get(expr_id, [])
            if k in g["exprs"]]


def _source_display(g, expr_id):
    """A FROM/JOIN source's display name: the stored table name,
    the minting scope's short name (#t), or the written ref."""
    for r in g["resolves"].get(expr_id, []):
        if r["to_kind"] == "table":
            return r["to_id"]
        if r["to_kind"] == "scope":
            return r["to_id"].split("::scope/")[-1]
    expr = g["exprs"].get(expr_id, {})
    return expr.get("ref") or expr.get("raw_text") or "a source"


def _scope_short(node_id):
    return node_id.split("::scope/")[-1].split("::")[0]


def _origin_of(voice, member_id, depth=0):
    """Walk a member expression toward its base column (3c)."""
    g = voice.g
    for r in g["resolves"].get(member_id, []):
        if r["to_kind"] == "column":
            return r["to_id"]
        if r["to_kind"] == "member" and depth < 8:
            return _origin_of(voice, r["to_id"], depth + 1)
    return None


def _payload_item(voice, expr_id, owner_id):
    g = voice.g
    expr = g["exprs"].get(expr_id, {})
    kind = expr.get("expression_kind")
    out_name = expr.get("output_name")
    name_words = _readable(out_name) if out_name else None
    if kind == "column_ref":
        res = g["resolves"].get(expr_id, [])
        col = [r for r in res if r["to_kind"] == "column"]
        members = [r for r in res if r["to_kind"] == "member"]
        stars = [r for r in members
                 if r.get("match_basis") == "star_member"]
        blind = [r for r in res
                 if r.get("match_basis") == "behind_star"]
        token = (expr.get("ref") or "value").split(".")[-1]
        if col:
            words = voice.subject(expr_id, owner_id)
            if name_words and name_words != _readable(token) \
                    and name_words != words:
                return f"{name_words} (the {words})"
            return f"the {words}"
        if stars:
            through = _scope_short(stars[0]["to_id"])
            # the reading door: the scope this ref was read FROM
            srcs = {_scope_short(r["to_id"]) for r in res
                    if r["to_kind"] == "scope"}
            through = next(iter(srcs), None) or _read_through(
                voice, owner_id) or through
            origins = []
            for r in stars:
                mexpr = g["exprs"].get(r["to_id"], {})
                oname = (mexpr.get("output_name")
                         or (mexpr.get("ref") or "?").split(".")[-1])
                origins.append(
                    f"{_scope_short(r['to_id'])}.{oname}")
            return (f"{name_words or _readable(token)} (read "
                    f"through {through}, origins "
                    f"{' and '.join(origins)})")
        if members:
            m = members[0]
            built_in = _scope_short(m["to_id"])
            origin = _origin_of(voice, m["to_id"])
            tail = f", from {origin}" if origin else ""
            return (f"{name_words or _readable(token)} (built in "
                    f"{built_in}{tail})")
        if blind:
            return (f"{name_words or _readable(token)} (from "
                    f"{_scope_short(blind[0]['to_id'])}, read "
                    "through a SELECT *; base origin not traced)")
        return "the " + _readable(token)
    if kind == "literal":
        raw = expr.get("raw_text", "")
        voice.refs.append(expr_id)
        return (f"{name_words} (the constant {raw})"
                if name_words else f"the constant {raw}")
    phrase = _expr_phrase(expr_id, voice, owner_id)
    return f"{name_words} ({phrase})" if name_words else phrase


def _read_through(voice, scope_id):
    g = voice.g
    for sid in _scope_structures(g, scope_id, "FROM"):
        for k in g["children"].get(sid, []):
            for r in g["resolves"].get(k, []):
                if r["to_kind"] == "scope":
                    return _scope_short(r["to_id"])
    return None


def _scope_structures(g, scope_id, kind):
    return [k for k in g["children"].get(scope_id, [])
            if g["struct_kind"].get(k) == kind]


def render_scopes(dir05, dir02, dir01):
    """L05's public door: one central sentence per scope."""
    dir05, dir02, dir01 = Path(dir05), Path(dir02), Path(dir01)
    graph = _load_graph(dir05)
    scopes = _read(dir05 / "05_semantic_graph_scope_output.json")
    words, values = _load_words(dir02)
    sql_lines = _load_sql(dir01)
    voice = _Voice(graph, words, values)
    g = graph

    rows = []
    for scope in sorted(scopes, key=lambda s: s["node_id"]):
        sid = scope["node_id"]
        voice.refs = [sid]
        kids = g["children"].get(sid, [])
        kinds = {k: g["struct_kind"].get(k) for k in kids}

        if any(v == "COMBINATION" for v in kinds.values()):
            arms = sum(1 for k in g["children"]
                       if k.startswith(f"{sid}::arm"))
            rows.append({"node_id": sid, "grain": "scope",
                         "sentence": "This selection combines "
                         f"{arms or 2} alternatives.",
                         "basis_version": BASIS_VERSION,
                         "evidence_refs": [sid]})
            continue

        from_sources = []
        for fid in _scope_structures(g, sid, "FROM"):
            for k in g["children"].get(fid, []):
                if k in g["exprs"]:
                    voice.refs.append(k)
                    from_sources.append(_source_display(g, k))

        membership, join_phrases = [], []
        join_ids = [k for k in kids if kinds[k] == "JOIN"]
        for i, jid in enumerate(join_ids):
            jrow_type = _join_row_type(g, dir05, jid)
            _, pair, lookup, pop = _join_parts(
                voice, g, jid, sql_lines)
            # the joined source is the (i+2)-th FROM entry — the
            # JOIN structure holds the condition tree, the FROM
            # holds every source in declaration order
            source = (from_sources[i + 1]
                      if i + 1 < len(from_sources) else "a source")
            membership.extend(pop)
            inner = []
            if pair:
                inner.append("matched where "
                             + " and ".join(pair))
            if lookup:
                inner.append("attachment rule: "
                             + " and ".join(lookup))
            detail = f" ({'; '.join(inner)})" if inner else ""
            verb = ("attaching" if jrow_type in
                    ("LeftOuter", "RightOuter", "FullOuter")
                    else "joined with")
            join_phrases.append(f", {verb} {source}{detail}")

        for wid in [k for k in kids if kinds[k] == "WHERE"]:
            leaves = []
            phrase = _compose(wid, g, voice, sql_lines, leaves,
                              True)
            if phrase:
                membership.insert(0, _lower_first(phrase))

        group = []
        for gid in [k for k in kids if kinds[k] == "GROUP BY"]:
            for k in g["children"].get(gid, []):
                if k in g["exprs"]:
                    group.append(
                        _expr_phrase(k, voice, sid))

        kept = None
        for tid in [k for k in kids if kinds[k] == "TOP"]:
            for k in g["children"].get(tid, []):
                raw = g["exprs"].get(k, {}).get("raw_text")
                if raw:
                    kept = f"the first {raw} records are kept"

        payload = []
        for pid_ in [k for k in kids if kinds[k] == "PROJECTION"]:
            srow = _struct_row(dir05, pid_)
            if srow.get("star_total"):
                payload.append("every column of the source")
            for k in g["children"].get(pid_, []):
                if k in g["exprs"]:
                    payload.append(
                        _payload_item(voice, k, sid))

        if str(scope.get("operation", "")).lower() == "delete":
            target = (from_sources[0] if from_sources
                      else scope.get("scope_name") or "its target")
            lead = f"This step removes records from {target}"

            sentence = lead
            if membership:
                sentence += ": " + "; ".join(membership)
            rows.append({"node_id": sid, "grain": "scope",
                         "sentence": sentence + ".",
                         "basis_version": BASIS_VERSION,
                         "evidence_refs": list(dict.fromkeys(
                             voice.refs))})
            continue

        if from_sources:
            lead = ("This is a selection from "
                    + ", ".join(from_sources[:1] + from_sources[
                        1 + len(join_ids):]))
            lead += "".join(join_phrases)
            sentence = lead + ": " + (
                "; ".join(membership) if membership
                else "no membership conditions are applied")
        else:
            sentence = ("This step produces derived values; "
                        "no source records are read")
        if kept:
            sentence += "; " + kept
        if group:
            sentence += "; grouped per " + ", ".join(group)
        if payload:
            sentence += "; carrying " + ", ".join(payload)
        rows.append({"node_id": sid, "grain": "scope",
                     "sentence": sentence + ".",
                     "basis_version": BASIS_VERSION,
                     "evidence_refs": list(dict.fromkeys(
                         voice.refs))})
    return rows, voice.counted


_STRUCT_CACHE = {}


def _struct_rows(dir05):
    key = str(dir05)
    if key not in _STRUCT_CACHE:
        _STRUCT_CACHE[key] = {
            s["node_id"]: s for s in
            _read(Path(dir05) / "05_semantic_graph_structure_output.json")}
    return _STRUCT_CACHE[key]


def _struct_row(dir05, node_id):
    return _struct_rows(dir05).get(node_id, {})


def _join_row_type(g, dir05, jid):
    return _struct_row(dir05, jid).get("join_type", "Inner")


def _join_parts(voice, g, jid, sql_lines):
    """-> (source display, pair phrases, lookup phrases,
    population phrases) for one JOIN structure."""
    source = "a source"
    pair, lookup, pop = [], [], []
    for k in g["children"].get(jid, []):
        if k in g["exprs"] and \
                g["exprs"][k]["expression_kind"] == "table_ref":
            voice.refs.append(k)
            source = _source_display(g, k)
    leaves = []
    _compose(jid, g, voice, sql_lines, leaves, True)
    for leaf, sentence in leaves:
        phrase = _lower_first(sentence.rstrip("."))
        oc = leaf.get("on_class")
        if oc == "lookup_shaping":
            lookup.append(phrase)
        elif oc == "population_filter":
            pop.append(phrase)
        else:
            pair.append(phrase)
    return source, pair, lookup, pop


# ==== L06 — statements, the file floor, the ledger (pseudo code
#      above, approved 2026-10-03: flags E and F as proposed) ========

def _fold_name(name):
    """The scope-name fold (R5.b lineage): # stripped,
    underscores to spaces, lowercased — the author's words."""
    return str(name or "").lstrip("#").replace("_", " ").lower()


def _pos_key(row):
    return tuple(int(p) for p in str(row["position"]).split(".")
                 if p.isdigit())


def _statement_sentence(stmt, scopes_by_stmt):
    """R11: what THIS STEP does — never its scopes' floors."""
    kind = stmt["statement_kind"]
    owned = scopes_by_stmt.get(stmt["node_id"], [])
    if kind == "SELECT INTO":
        target = next((s for s in owned if s["scope_kind"]
                       in ("temp_table", "write_target")), None)
        name = _fold_name(target["scope_name"] if target
                          else "the target")
        helpers = [_fold_name(s["scope_name"]) for s in owned
                   if s["scope_kind"] == "cte"]
        if helpers:
            if len(helpers) == 1:
                prep = helpers[0]
            else:
                prep = ", ".join(helpers[:-1]) + \
                    " and " + helpers[-1]
            return (f"Builds the {name} selection, preparing "
                    f"the {prep} selection first.")
        return f"Builds the {name} selection."
    if kind == "SELECT":
        return "Delivers the procedure's result set."
    if kind == "IF":
        return "A decision step."
    return None  # a handled kind with no voicing row: counted


def render_statements(dir05, dir02, dir01):
    """R11's door: one row per VOICED statement; operational /
    gap / unvoiced-kind land counted."""
    dir05 = Path(dir05)
    stmts = _read(dir05 / "05_semantic_graph_statement_output.json")
    scopes = _read(dir05 / "05_semantic_graph_scope_output.json")
    scopes_by_stmt = {}
    for s in scopes:
        scopes_by_stmt.setdefault(s["owning_statement"],
                                  []).append(s)
    rows, counted = [], []
    for st in sorted(stmts, key=lambda s: (
            s["node_id"].split("::")[1], _pos_key(s))):
        disp = st["disposition"]
        if disp == "operational":
            counted.append({"node_id": st["node_id"],
                            "class": "operational_statement",
                            "grain": "statement",
                            "basis_version": BASIS_VERSION})
            continue
        if disp == "gap":
            counted.append({"node_id": st["node_id"],
                            "class": "dynamic_sql_gap",
                            "grain": "statement",
                            "basis_version": BASIS_VERSION})
            continue
        if disp != "handled":  # remainder: already loud in 05
            continue
        sentence = _statement_sentence(st, scopes_by_stmt)
        if sentence is None:
            counted.append({"node_id": st["node_id"],
                            "class": "unvoiced_statement_kind",
                            "grain": "statement",
                            "basis_version": BASIS_VERSION})
            continue
        rows.append({"node_id": st["node_id"],
                     "grain": "statement", "sentence": sentence,
                     "basis_version": BASIS_VERSION,
                     "evidence_refs": [st["node_id"]]})
    return rows, counted


def _delivery_chain(g, scope_id, seen=None):
    """The R10 spine: the scope + every named scope it
    transitively draws from, reading order, depth-first."""
    seen = set() if seen is None else seen
    if scope_id in seen:
        return []
    seen.add(scope_id)
    chain = [scope_id]
    for sid in g["children"].get(scope_id, []):
        if g["struct_kind"].get(sid) in ("FROM", "JOIN"):
            for k in g["children"].get(sid, []):
                for r in g["resolves"].get(k, []):
                    if r["to_kind"] == "scope":
                        chain += _delivery_chain(g, r["to_id"],
                                                 seen)
    return chain


def _scope_where_phrase(voice, g, sid, sql_lines):
    for wid in _scope_structures(g, sid, "WHERE"):
        leaves = []
        phrase = _compose(wid, g, voice, sql_lines, leaves, True)
        if phrase:
            return _lower_first(phrase)
    return None


def _scope_payload_items(voice, g, sid, dir05):
    items = []
    for pid_ in _scope_structures(g, sid, "PROJECTION"):
        if _struct_row(dir05, pid_).get("star_total"):
            items.append("every column of the source")
        for k in g["children"].get(pid_, []):
            if k in g["exprs"]:
                items.append(_payload_item(voice, k, sid))
    return items


def _file_sentence(voice, g, dir05, fname, frow, stmts, scopes,
                   scope_sentences, stmt_rows, params, sql_lines):
    parts = []
    fscopes = [s for s in scopes
               if s["node_id"].split("::")[1] == fname]
    deliveries = [s for s in fscopes
                  if s["scope_kind"] == "delivery"]

    # (1) HEADLINE
    for d in deliveries:
        s = scope_sentences.get(d["node_id"], "")
        if s.startswith("This is a selection"):
            parts.append("Delivers a selection"
                         + s[len("This is a selection"):])
        elif s.startswith("This step produces derived values"):
            parts.append("Delivers derived values" + s[
                len("This step produces derived values"):])
        elif s:
            parts.append("Delivers " + _lower_first(s))
    if not deliveries and fscopes:
        last = fscopes[-1]
        parts.append(scope_sentences.get(last["node_id"], "")
                     + f" Builds {len(fscopes)} working "
                     "selections; delivers nothing.")

    # (2) PIPELINE — voiced lines, build order, original positions
    lines = []
    for st in stmt_rows:
        if st["node_id"].split("::")[1] != fname:
            continue
        pos = st["node_id"].rsplit("/", 1)[-1]
        lines.append(f"({pos}) {st['sentence']}")
    if lines:
        parts.append("Pipeline: " + " ".join(lines))

    # (3) APPENDIX
    chain = []
    for d in deliveries:
        for sid in _delivery_chain(g, d["node_id"]):
            if sid not in chain:
                chain.append(sid)
    presents = []
    for d in deliveries:
        presents += _scope_payload_items(voice, g, d["node_id"],
                                         dir05)
    if presents:
        parts.append("Presents: " + "; ".join(presents) + ".")
    pop_lines, join_lines = [], []
    by_id = {s["node_id"]: s for s in fscopes}
    for sid in chain:
        label = by_id.get(sid, {}).get("scope_name") or \
            _scope_short(sid)
        w = _scope_where_phrase(voice, g, sid, sql_lines)
        if w:
            tag = ("the delivery" if label == "delivery"
                   else label)
            pop_lines.append(f"In {tag}: {w}.")
        for jid in _scope_structures(g, sid, "JOIN"):
            if _struct_row(dir05, jid).get("join_type") \
                    == "Inner":
                _, pair, _, _ = _join_parts(voice, g, jid,
                                            sql_lines)
                if pair:
                    tag = ("the delivery" if label == "delivery"
                           else label)
                    join_lines.append(
                        f"In {tag}: {' and '.join(pair)}.")
    if pop_lines:
        parts.append("Population: " + " ".join(pop_lines))
    if join_lines:
        parts.append("Inner joins: " + " ".join(join_lines))

    # parameters shaping the population (3d) — verbatim defaults
    bound = set()
    for from_id, rlist in g["resolves"].items():
        if "::structure/WHERE/" in from_id \
                or "::structure/JOIN/" in from_id \
                or "::structure/HAVING/" in from_id:
            for r in rlist:
                if r["to_kind"] == "parameter":
                    bound.add(r["to_id"])
    fparams = [p for p in params
               if p["node_id"].split("::")[1] == fname
               and p["node_id"] in bound]
    if fparams:
        bits = []
        for p in sorted(fparams, key=lambda x: x["name"]):
            d = p.get("default_text")
            bits.append(f"{p['name']} (default \"{d}\")"
                        if d and d != "None"
                        else f"{p['name']} (no default)")
        parts.append("Parameters shaping the population: "
                     + "; ".join(bits) + ".")

    # the gap sentence (3e, amended shape — flag E)
    fstmts = [s for s in stmts
              if s["node_id"].split("::")[1] == fname]
    gaps = [s for s in fstmts if s["disposition"] == "gap"]
    if gaps:
        frag = gaps[0]["evidence"]["fragment"].strip().rstrip(";")
        k, n = len(gaps), len(fstmts)
        verb = "is" if k == 1 else "are"
        parts.append("Part of this file's logic is built as a "
                     "string at run time and is not described "
                     f"here; it is executed by \"{frag}\". "
                     f"{k} of {n} statements {verb} in this gap.")

    # the census close (R10.3)
    voiced = len([s for s in stmt_rows
                  if s["node_id"].split("::")[1] == fname])
    op = len([s for s in fstmts
              if s["disposition"] == "operational"])
    unvoiced = len(fstmts) - voiced - op - len(gaps)
    census = (f"Steps: {len(fstmts)}, {voiced} voiced, "
              f"{op} operational, {len(gaps)} gap")
    if unvoiced:
        census += f", {unvoiced} awaiting words"
    named = [s["scope_name"] for s in fscopes
             if s["scope_kind"] in ("temp_table", "cte")]
    census += ". Selections: " + (", ".join(named) if named
                                  else "none") + "."
    parts.append(census)
    return "\n".join(p for p in parts if p)


def render_files(dir05, dir02, dir01):
    """R10/R13's door: the three-level technical definition,
    one row per file."""
    dir05, dir02, dir01 = Path(dir05), Path(dir02), Path(dir01)
    graph = _load_graph(dir05)
    words, values = _load_words(dir02)
    sql_lines = _load_sql(dir01)
    voice = _Voice(graph, words, values)
    files = _read(dir05 / "05_semantic_graph_file_output.json")
    stmts = _read(dir05 / "05_semantic_graph_statement_output.json")
    scopes = _read(dir05 / "05_semantic_graph_scope_output.json")
    params = _read(dir05 / "05_semantic_graph_parameter_output.json")
    scope_rows, _ = render_scopes(dir05, dir02, dir01)
    scope_sentences = {r["node_id"]: r["sentence"]
                       for r in scope_rows}
    stmt_rows, _ = render_statements(dir05, dir02, dir01)

    rows = []
    for f in sorted(files, key=lambda x: x["file_name"]):
        fname = f["file_name"]
        voice.refs = [f"file::{fname}"]
        sentence = _file_sentence(
            voice, graph, dir05, fname, f, stmts, scopes,
            scope_sentences, stmt_rows, params, sql_lines)
        rows.append({"node_id": f"file::{fname}",
                     "grain": "file", "sentence": sentence,
                     "basis_version": BASIS_VERSION,
                     "evidence_refs": list(dict.fromkeys(
                         voice.refs))})
    return rows, voice.counted


def render_all(dir05, dir02, dir01):
    """THE ONE PASS: all five grains + the deduped ledger
    (decision 5). lookup_shaping_attachment rows are the
    apartness record (flag F) — outside the silence equation."""
    dir05 = Path(dir05)
    p_rows, p_cnt = render_predicates(dir05, dir02, dir01)
    c_rows, c_cnt, _ = render_conditions(dir05, dir02, dir01)
    s_rows, s_cnt = render_scopes(dir05, dir02, dir01)
    t_rows, t_cnt = render_statements(dir05, dir02, dir01)
    f_rows, f_cnt = render_files(dir05, dir02, dir01)

    apart = [{"node_id": p["node_id"],
              "class": "lookup_shaping_attachment",
              "grain": "predicate",
              "basis_version": BASIS_VERSION}
             for p in _read(dir05 / "05_semantic_graph_predicate_output.json")
             if p.get("on_class") == "lookup_shaping"]

    ledger, seen = [], set()
    for c in p_cnt + c_cnt + s_cnt + t_cnt + f_cnt + apart:
        key = (c["node_id"], c["class"])
        if key not in seen:
            seen.add(key)
            ledger.append(c)
    ledger.sort(key=lambda c: (c["node_id"], c["class"]))
    rows = p_rows + c_rows + s_rows + t_rows + f_rows
    return rows, ledger


# ==== L07 — the artifacts land (pseudo code above, approved
#      2026-10-03: flag G's text format as pinned) ==================

import sys  # noqa: E402  (the build-command door)

_EDGE_COLORS = {"member": "#2a7d4f", "star_member": "#2a5fbf",
                "behind_star": "#c06000", "fold": "#999999"}
_CHAR_W, _LINE_H = 7, 15


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _file_text(fname, scope_labels, scope_rows, stmt_lines,
               file_sentence):
    lines = [f"==== {fname} ====", f"basis {BASIS_VERSION}", "",
             "-- THE SELECTIONS --"]
    for r in scope_rows:
        lines.append(f"{scope_labels.get(r['node_id'], '?')}: "
                     f"{r['sentence']}")
    lines += ["", "-- THE STEPS --"]
    lines += stmt_lines
    lines += ["", "-- THE FILE --", file_sentence]
    return "\n".join(lines) + "\n"


def _pred_svg_line(g, pid, values):
    frag = g["pred_by_id"][pid]["evidence"]["fragment"]
    frag = re.sub(r"\s+", " ", frag).strip()[:90]
    suffix = ""
    for k in g["children"].get(pid, []):
        for r in g["resolves"].get(k, []):
            if r["to_kind"] == "value":
                tu, code = r["to_id"].split("::", 1)
                meaning = values.get((tu.upper(), code))
                if meaning:
                    suffix = f" = '{meaning}' ({code})"
    return f"- {frag}{suffix}"


def _scope_svg_lines(g, dir05, sid, values):
    """The scope box's content: structures in position order,
    predicate leaves by their stored fragments."""
    lines = []
    for k in g["children"].get(sid, []):
        kind = g["struct_kind"].get(k)
        if kind is None:
            continue
        if kind in ("FROM", "JOIN"):
            srcs = [g["exprs"][x].get("raw_text", "")
                    for x in g["children"].get(k, [])
                    if g["exprs"].get(x, {}).get(
                        "expression_kind") == "table_ref"]
            jt = _struct_row(dir05, k).get("join_type")
            head = kind + (f" ({jt})" if jt else "")
            lines.append(f"{head}: {', '.join(srcs)}"
                         if srcs else f"{head}:")
            if kind == "JOIN":
                for pid in _tree_pred_ids(g, k):
                    lines.append("  "
                                 + _pred_svg_line(g, pid, values))
        elif kind in ("WHERE", "HAVING"):
            lines.append(kind + ":")
            for pid in _tree_pred_ids(g, k):
                lines.append("  " + _pred_svg_line(g, pid, values))
        elif kind == "PROJECTION":
            row = _struct_row(dir05, k)
            star = (", star" if row.get("star_total") else "")
            lines.append(f"PROJECTION: "
                         f"{row.get('member_total', '?')} members"
                         + star)
        elif kind in ("GROUP BY", "ORDER BY", "COMBINATION"):
            lines.append(kind)
    return lines


def _tree_pred_ids(g, node_id):
    out = []
    for k in g["children"].get(node_id, []):
        if k in g["pred_by_id"]:
            out.append(k)
        elif g["struct_kind"].get(k) in _BOOLEANS:
            out += _tree_pred_ids(g, k)
    return out


def _scope_edges(g, fname):
    """Distinct (reader scope, source scope, basis) for every
    scope-to-scope read in the file, sorted — the drawn edges."""
    edges = set()
    for from_id, rlist in g["resolves"].items():
        if from_id.split("::")[1] != fname:
            continue
        if "::scope/" not in from_id:
            continue
        reader = from_id.split("::structure/")[0]
        for r in rlist:
            basis = r.get("match_basis")
            if basis not in _EDGE_COLORS:
                continue
            to = r["to_id"] or ""
            if "::scope/" not in to:
                continue
            source = to.split("::structure/")[0]
            if source != reader:
                edges.add((reader, source, basis))
    return sorted(edges)


def _svg_file(g, dir05, fname, values, stmts, scopes,
              stmt_texts):
    """Decision 8: the deterministic per-file SVG. Statements
    down the spine, scopes as boxes, resolves edges across the
    right margin. Pure function of the stored rows."""
    W_BOX = 760
    x_stmt, x_box = 20, 56
    y = 48
    out, boxes = [], {}
    out.append(f'<text x="20" y="28" font-size="15" '
               f'font-weight="bold">{_esc(fname)}</text>')
    fscopes = {}
    for s in scopes:
        if s["node_id"].split("::")[1] == fname:
            fscopes.setdefault(s["owning_statement"],
                               []).append(s)
    for st in sorted([s for s in stmts
                      if s["node_id"].split("::")[1] == fname],
                     key=_pos_key):
        sid = st["node_id"]
        pos = sid.rsplit("/", 1)[-1]
        text, color = stmt_texts.get(sid, ("", "#333333"))
        out.append(
            f'<text x="{x_stmt}" y="{y}" font-size="12" '
            f'fill="{color}">({pos}) {_esc(text)[:150]}</text>')
        y += _LINE_H + 2
        for sc in fscopes.get(sid, []):
            lines = ([f"{sc['scope_name']} ({sc['scope_kind']})"]
                     + _scope_svg_lines(g, dir05, sc["node_id"],
                                        values))
            h = len(lines) * _LINE_H + 10
            out.append(
                f'<rect x="{x_box}" y="{y}" width="{W_BOX}" '
                f'height="{h}" fill="#f7f7f7" stroke="#888888"'
                ' rx="4"/>')
            yy = y + _LINE_H
            for i, ln in enumerate(lines):
                weight = ' font-weight="bold"' if i == 0 else ""
                out.append(f'<text x="{x_box + 8}" y="{yy}" '
                           f'font-size="11"{weight}>'
                           f'{_esc(ln)[:120]}</text>')
                yy += _LINE_H
            boxes[sc["node_id"]] = (y, y + h)
            y += h + 10
        y += 6
    # the resolves edges, right margin
    xm0 = x_box + W_BOX + 16
    for i, (reader, source, basis) in enumerate(
            _scope_edges(g, fname)):
        if reader not in boxes or source not in boxes:
            continue
        yr = sum(boxes[reader]) // 2
        ys = sum(boxes[source]) // 2
        xm = xm0 + i * 14
        color = _EDGE_COLORS[basis]
        out.append(f'<polyline points="{xm0 - 8},{yr} {xm},{yr} '
                   f'{xm},{ys} {xm0 - 8},{ys}" fill="none" '
                   f'stroke="{color}" stroke-width="1.2"/>')
        out.append(f'<text x="{xm + 2}" y="{min(yr, ys) - 3}" '
                   f'font-size="9" fill="{color}">{basis}</text>')
    height = y + 30
    width = xm0 + 14 * max(1, len(_scope_edges(g, fname))) + 120
    return ('<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            'font-family="monospace">\n'
            + "\n".join(out) + "\n</svg>\n")


def build06(dir05, out06, dir02, dir01):
    """THE BUILD COMMAND (contract): render everything, land the
    sheet, the ledger, the texts and the SVGs."""
    dir05, out06 = Path(dir05), Path(out06)
    dir02, dir01 = Path(dir02), Path(dir01)
    rows, ledger = render_all(dir05, dir02, dir01)
    (out06 / "06_technical_descriptions_output.json").write_text(
        json.dumps(rows, indent=1))
    (out06 / "06_technical_descriptions_voicing_output.json").write_text(
        json.dumps(ledger, indent=1))

    graph = _load_graph(dir05)
    _, values = _load_words(dir02)
    files = _read(dir05 / "05_semantic_graph_file_output.json")
    stmts = _read(dir05 / "05_semantic_graph_statement_output.json")
    scopes = _read(dir05 / "05_semantic_graph_scope_output.json")
    scope_labels = {s["node_id"]: s["scope_name"] for s in scopes}
    stmt_sent = {r["node_id"]: r["sentence"] for r in rows
                 if r["grain"] == "statement"}
    stmt_counted = {c["node_id"]: c["class"] for c in ledger
                    if c["grain"] == "statement"}
    file_sent = {r["node_id"]: r["sentence"] for r in rows
                 if r["grain"] == "file"}
    scope_rows_by_file = {}
    for r in rows:
        if r["grain"] == "scope":
            scope_rows_by_file.setdefault(
                r["node_id"].split("::")[1], []).append(r)

    for f in sorted(files, key=lambda x: x["file_name"]):
        fname = f["file_name"]
        stmt_lines, stmt_texts = [], {}
        for st in sorted([s for s in stmts
                          if s["node_id"].split("::")[1] == fname],
                         key=_pos_key):
            sid = st["node_id"]
            pos = sid.rsplit("/", 1)[-1]
            if sid in stmt_sent:
                stmt_lines.append(f"({pos}) {stmt_sent[sid]}")
                stmt_texts[sid] = (stmt_sent[sid], "#333333")
            else:
                cls = stmt_counted.get(sid, "remainder")
                stmt_lines.append(f"({pos}) [{cls}]")
                color = ("#bb0000" if cls == "dynamic_sql_gap"
                         else "#777777")
                stmt_texts[sid] = (f"[{cls}]", color)
        text = _file_text(
            fname, scope_labels,
            scope_rows_by_file.get(fname, []), stmt_lines,
            file_sent.get(f"file::{fname}", ""))
        (out06 / f"{fname}.txt").write_text(text)
        (out06 / f"{fname}.svg").write_text(
            _svg_file(graph, dir05, fname, values, stmts,
                      scopes, stmt_texts))

    census = {"rows": len(rows), "ledger": len(ledger),
              "files": len(files)}
    by_grain = {}
    for r in rows:
        by_grain[r["grain"]] = by_grain.get(r["grain"], 0) + 1
    by_class = {}
    for c in ledger:
        by_class[c["class"]] = by_class.get(c["class"], 0) + 1
    print(f"06 build: rows {by_grain}; ledger {by_class}; "
          f"{len(files)} texts + {len(files)} svgs")
    return census


def main(argv):
    if len(argv) != 4:
        print("usage: technical_descriptions.py <dir05> <out06> "
              "<dir02> <dir01>")
        return 2
    Path(argv[1]).mkdir(parents=True, exist_ok=True)
    build06(argv[0], argv[1], argv[2], argv[3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
