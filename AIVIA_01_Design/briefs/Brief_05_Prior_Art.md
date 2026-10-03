# Brief_05_Prior_Art — what the previous estate already solved for the semantics layer

Status: REFERENCE (survey run 2026-10-01 at Sunny's direction, before
designing phase 05). Source: the live `aisql` package in this repo.
Context: there were TWO prior estates. Era 1 (`src/parser/`,
`src/tree/`) was deleted 2026-09-19 (commit 91b198a, 831 files) and
survives only in git history. Era 2 = the `aisql/` package — it is
live in the tree today and is everything below. `build/lib/aisql/**`
is a stale build copy; never read or port from it.

## 1. Parsing

The single ScriptDom door: `aisql/graph/kg2_mapper/scriptdom_loader.py`
(160 lines).
- `ensure_scriptdom()` — idempotent coreclr + DLL load, caches
  TSql160Parser. `parse_tsql(sql) -> (fragment, errors)` is the only
  parse call; errors are human strings "L{line}C{col}: {msg}";
  rejecting is the caller's decision.
- macOS subprocess probe before hosting coreclr (Apple's hardened
  Python SIGKILLs otherwise); four DLL locations (env var, libs/,
  wheel-internal, Fabric lakehouse); NO fallback parser by design
  (ADR 0001), test-locked.
- ALREADY PORTED to AIVIA_01_Code/scriptdom_loader.py — the one parse
  door of the new estate, test-locked. This step is done.

The parse-tree walker: `aisql/graph/kg2_mapper/__init__.py`
(1238 lines) — the one module allowed to touch parser machinery
(CHECK-KG2-1, enforced by tests/aisql/test_planks.py).
- `map_tree(file_name, text)` (L501) is the entry point: normalize
  CRLF, parse, raise on parse error, walk fragment.Batches.
- `executable_statements()` (L515) unwraps CreateProcedureStatement /
  BeginEndBlock to an ordered flat statement list.
- `process(stmt)` (L530) dispatches per statement kind (IF, SELECT,
  SELECT INTO, INSERT, WHILE, DELETE, SET, …); unknown kinds land in
  a counted remainder — handled + remainder = total, always.
- Key ruling: CTEs AND temp tables are the same kind of thing — a
  NAMED SCOPE. `WITH x AS (...)` and `SELECT ... INTO #x` both mint a
  named scope in the tree. Scope identity: `file::name` (the single
  result-set emitter keys `file::delivery`).
- Every node carries evidence: {fragment verbatim, offset, line,
  column} — every claim traces to source.
- `resolve()` (L753) binds column_ref/table_ref to known identities
  or same-tree scopes; unresolved are counted by class.
- `record_exclusion()` (L1147): a parse failure is a counted, named
  exclusion — never silent, never fatal.
- Output is plain nested dicts (JSON-able), not objects.

## 2. Graph: node and edge kinds (the prior registry's law)

Node kinds (registries/kg2_logic.json, 8 rows): file, statement,
scope (SELECT+clauses / CTE / subquery / temp-table stage — "every
logic boundary"), structure (FROM/JOIN/WHERE/GROUP BY/ORDER BY/
UNION/CASE), predicate (one condition), expression, parameter; every
node carries evidence + version stamps.

Edge kinds: `contains` (parent→child through the whole tree, with
position where order is meaning, and role on predicate→expression),
`resolves_to` (*_ref → the thing it names). The dictionary layer
(KG1) adds has_part and joins_to.

Closed vocabularies (registries/kg2_kind_library.json v1.52.0 — THE
single highest-value port, nearly verbatim):
- Predicate_Kinds (13): COMPARE_EQ/NEQ/GT/GTE/LT/LTE, PATTERN_MATCH,
  IN_LIST, IN_SELECTION, RANGE, NULL_CHECK, EXISTS_SELECTION,
  QUANTIFIED_COMPARE. Negated syntax normalizes to structural NOT
  over the positive kind.
- Expression_Kinds (10), Roles (6), Operational_Statement_Kinds (9,
  ruled-silent), Gap_Classes (10, each gap classed + owned).
- TSQL_Denominator (17 rows): EVERY ScriptDom boolean type mapped or
  explicitly deferred; anything beyond the table = RED BUILD (a
  reflection check fails until the new type is ruled). This is the
  coverage guarantee.
- Statement_Voicings (4) and Function_Voicings (19, each with a
  measured estate count: DATEDIFF 56, ROW_NUMBER 26, DATEADD 13 …) —
  the library was built evidence-ordered by frequency, not guessed.

Store substrate (small, copyable): `aisql/graph/store.py` (137
lines) — append-only NodeVersion/Edge, supersede = append + valid_to,
no update/delete. `read_api.py` (34 lines) — the single read surface.

The meaning twin: `aisql/graph/kg2_translator/__init__.py` — one
meaning node per tree node (homomorphism asserted every run, no third
bucket); `content_key` = sha256 meaning identity, invariant to
whitespace/aliases/comments, sensitive to real logic change — what
lets a description's certification survive a reformat. Read its
L1-48 docstring even if nothing else.

## 3. Description generation — the deterministic grammar

The law: `AIVIA_Design/Grammar_Floor.md` (1527 lines, v2.16.0),
rules R1-R16 each with ratification date and ruling quote. R1 lead
sentence · R2 one bullet per membership decision · R4 predicate
voicings (total over the closed kinds) · R5 operand words/blessed
names · R7 honest no-conditions · R8 trailing-comment annotations ·
R10 file/report floor · R11 statement step · R12 computed columns ·
R13 the three-level catch-all · R14 business-term sentence.

The implementation: `aisql/flows/produce.py` (2130 lines). Read
L28-123 first — a rule-by-rule changelog of every bug the grammar
fixed. Key renderers: `_voice_predicate` (L928, filter→sentence per
predicate kind: "is recorded", "is between X and Y (inclusive)", "is
one of N values"); `scope_sentence` (L1621, THE central sentence:
lead → joins → filters → rank-kept → payload); `statement_phrase`
(L1123, closed voicings — returns None for unlisted kinds, never
invents); `compose_file_floor` (L1955); `voicing_ledger` (L1764,
conservation: voiced + counted == total, disjoint — "silent omission
has no constructible path").

Layer build order (ruled, in `aisql/flows/inbound.py` receive_estate
L305-329): scopes → joins → statements → conditions → derived
columns → file. The three-level technical definition (Collibra
field) renders in `inbound._render_technical_definition` (L712):
HEADLINE / PIPELINE / APPENDIX.

The LLM sits strictly OUTSIDE the deterministic path:
`aisql/flows/business_voice.py` — LLM proposes a business sentence,
a no-model mechanical gate (`check_sentence`) checks named rules,
`effective_sentence` picks blessed > gate-passed-proposal > floor.
Gate fails or no model → the floor ships. (= Phase II prior art.)

Who wrote USP_ED_SEPSIS_descriptions.txt: NO committed module — an
untracked operator harness (declared in src/zones.py L68-69) calling
scope_sentence / scope_meaning / statement_phrase /
statement_enduser + _render_technical_definition + file_words.
Regenerating it means rebuilding that harness; only its inputs
survive.

## 4. Scale and quality (measured, not guessed)

- Era 1 full corpus: 788/790 procs (99.7%); 1,337/1,344 (99.5%).
- Era 2 pinned regression estate (sepsis, 28 procs):
  AIVIA_Product/estates/sepsis/expected_shakedown.json + its test —
  90 tables · 4,554 columns · 68 declared joins; 28 acquired ·
  0 excluded (100% parse) · 3,701 resolved refs · 131 unresolved
  (all one named class) · 25,812 twin nodes · 312 scope
  descriptions · 196 scopes with decisions.
- The shakedown json's `_comment` is a forensic list of counting
  holes found and closed (over-redaction breaking parses; filters
  hiding in INNER-join ON clauses; SELECT * silently skipped) — READ
  IT: it is the list of bugs a new build rediscovers otherwise.
- Why name-matching is insufficient: 6 procs share one name,
  5 different logics behind it (internal/docs/VERB_SCORECARD.md).

## 5. Read-first list for the phase 05 design

1. AIVIA_Design/registries/kg2_kind_library.json — the closed
   vocabulary as data; port nearly verbatim.
2. aisql/flows/produce.py — the sentence generator (changelog L28-123
   first).
3. AIVIA_Design/Grammar_Floor.md — the why behind every branch.
4. aisql/graph/kg2_mapper/scriptdom_loader.py — ported already.
5. aisql/graph/kg2_mapper/__init__.py — the walker; its dict shapes
   are the contract.
6. AIVIA_Product/estates/sepsis/expected_shakedown.json — acceptance
   pins + pre-emptive bug list.
7. aisql/flows/inbound.py — the ruled layer order; the catch-all.
8. aisql/lenses/decisions.py (163 lines) — filter vs join-plumbing vs
   noise; the judgment that makes descriptions read as meaning.
9. aisql/graph/store.py + read_api.py — minimal versioned substrate.
10. aisql/graph/kg2_translator/__init__.py — homomorphism +
    content_key (the docstring at minimum).
Spec-by-example tests: tests/aisql/test_scope_sentence.py,
tests/aisql/test_statement_render.py (byte-exact, authored RED
first). Target quality bar: USP_ED_SEPSIS_descriptions.txt.

## Gotchas

- Import laws were structural (test_planks.py): only kg2_mapper may
  touch the parser; only read_api may be imported by lenses.
- produce.py's FLOOR_GRAMMAR_VERSION says 2.15.0 while
  Grammar_Floor.md and the sample output say 2.16.0 — a known
  bookkeeping slip; fix on port.
- build/lib/aisql/** is stale; ignore.
