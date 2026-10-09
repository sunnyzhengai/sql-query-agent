05_semantic_graph_data_contract

Status: APPROVED 2026-10-01 (Sunny, in chat), same day as the draft.
Scribed by Claude from the ruled design decisions; the kind library
was ratified by Sunny the same day.

Who is the owner of this data contract?
- Sunny Zheng

What is the input of this data contract?
- The 8 sql files from phase 01 (AIVIA_01_Data/01_subject_sql_files/)
  — read only, never written by this phase. Selection law (noted at
  L03 build, 2026-10-01): the corpus files carry NO extension; the
  build takes every regular, non-hidden, non-.json file in the
  folder (the data sheet json is the folder's only other resident).
- The phase 02 dictionary sheets (table, column, join, value) — read
  only; resolution targets.
- The kind library (Input File 1 below) — the closed vocabularies.

Where are these data files located for local development?
- /Users/sunnyzheng/sql-query-agent/AIVIA_01_Data/05_semantic_graph/

Where are these data files located for production?
- Fabric lakehouse, AIVIA_01_LH/Files/Data/05_semantic_graph/

Input File 1: the kind library
- Name: 05_semantic_graph/05_kind_library.json
- Content, ported from the prior estate's kg2_kind_library registry
  (v1.52.0) per design decision 4: predicate kinds (13), expression
  kinds, structure kinds, roles, operational statement kinds
  (ruled-silent), and the TSQL denominator table (every ScriptDom
  boolean type mapped or explicitly deferred).
- The red-build law: a ScriptDom type the build meets that is not in
  this file FAILS the build until a row is added. Adding a row is
  the ruling, dated (the 03_chat_technical_terms.md precedent).
- Authorship — RULED 2026-10-01 (Sunny, in chat): Claude ported once
  at her word (done 2026-10-01, from kg2_kind_library v1.52.0, rows
  verbatim); Sunny ratifies the file; from ratification on it grows
  by her hand only, one ruled row at a time, dated. Ratification
  status lives in the file's own "status" field.
- Omitted on port, named in the file: the voicing sheets (phase 06),
  Meaning_Node_Kinds (prior twin graph), Gap_Classes (stage 5
  defines its own unresolved classes; port then if wanted), and the
  prior process sheets.

What is the output of this data contract?

THE RENAME AMENDMENT (2026-10-08, the naming law — step table
row 05 in 10_work_wheel_data_contract.md; approved + built same
day): every output below is `05_semantic_graph_<content>_output
.json` — "_sheet" dies, the step prefix says who made it. Older
passages in this contract citing the pre-rename names
(05_<content>_sheet.json / _edges.json / _ledger.json /
_joins.json) read as their new names below. 05_kind_library.json
keeps its name: it is the ratified ASSET (an input), not an
engine output.

- The semantic graph sheets, one per node kind + two edge sheets +
  two ledgers, written stage by stage (design decision 8, L03-L07):
  1. 05_semantic_graph_file_output.json        (stage 1, L03)
  2. 05_semantic_graph_statement_output.json   (stage 1, L03)
  3. 05_semantic_graph_scope_output.json       (stage 2, L04)
  4. 05_semantic_graph_structure_output.json   (stage 3, L05)
  5. 05_semantic_graph_predicate_output.json   (stage 4, L06)
  6. 05_semantic_graph_expression_output.json  (stage 4, L06)
  7. 05_semantic_graph_contains_edges_output.json (grows at every stage)
  8. 05_semantic_graph_resolves_edges_output.json (stage 5, L07)
  9. 05_semantic_graph_exclusion_ledger_output.json (parse failures —
      counted, named)
  10. 05_semantic_graph_discovered_joins_output.json (stage 5 — joins
      used in SQL with no declared dictionary join row; counted,
      named, flywheel ore)
  11. 05_semantic_graph_parameter_output.json  (stage 5 — D6, the
      stage-5 amendment)
- NO LLM output and NO embeddings in this phase: phase 05 is fully
  deterministic — zero paid calls. Descriptions are phase 06;
  embeddings are phase 07.

What is the identity law (every row, every edge)?
- Every node row carries node_id: the hierarchical path from its
  file, deterministic and human-readable, e.g.
  file::<file_name>
  file::<file_name>::stmt/<position>    (REFINED 2026-10-01 with the
      L03 pseudo-code approval: position is a DOTTED PATH through
      nested control flow — stmt/3 top level, stmt/3.1 inside it,
      stmt/3.1.2 deeper. Nothing is silently skipped at any depth —
      the prior estate's BEGIN..END lesson.)
  file::<file_name>::scope/<scope_name>      (dupes: /<name>#2;
                                              the delivery scope:
                                              scope/delivery)
  …::structure/<kind>/<position>
  …::pred/<position>
  …::expr/<position>
- Edges reference node_ids on both ends. resolves_to edges point at
  phase 02 identities (table name, table.column, value row key) or
  at an earlier same-file scope node_id.
- Re-running the build on unchanged SQL reproduces identical ids
  (deterministic, no timestamps inside ids).

What is the evidence law (every row)?
- Every node row carries evidence: the verbatim SQL fragment, line,
  column. Every claim traces to source (the prior estate's witness
  law, adopted).

What are the sheet fields?
- Common to every node sheet: node_id, file_name, kind fields as
  below, evidence {fragment, line, column}.
- 05_file_sheet.json: file_name, dialect (tsql), parsed_at,
  statement_total, statements_handled, statements_operational,
  statements_gap, remainder_total (conservation: handled +
  operational + gap + remainder = total), parser_version,
  kind_library_version.
- 05_statement_sheet.json: node_id, position (dotted path),
  scriptdom_type (verbatim parser class name), statement_kind (from
  the kind library; a remainder row repeats its scriptdom_type),
  disposition (REFINED 2026-10-01 with the L03 pseudo-code
  approval): handled | operational | gap | remainder, plus
  gap_class (null unless disposition is "gap"). Remainder
  statements get FULL VISIBLE ROWS, not just a count — unknown
  kinds land in the remainder with their ScriptDom type name,
  counted on the file row.
  The "gap" disposition — RULED 2026-10-01 (Sunny, in chat, from
  the L03 census): a statement whose logic static parsing cannot
  open, classed by the library's Statement_Gap_Classes sheet. First
  class: dynamic_sql (EXEC of a string; the string-form EXEC only —
  a procedure-call EXEC is not this class). The placeholder law:
  no naked gaps — every gap is counted, classed, and named in its
  file's description (phase 06).
- 05_scope_sheet.json — STAGE 2 AMENDMENT (drafted 2026-10-01,
  APPROVED 2026-10-02, Sunny in chat, all five new rulings;
  supersedes the thin one-line spec):
  - node_id, by the scope identity law:
    - NAMED scopes key by NAME, not position (a later FROM #temp /
      FROM cte must resolve to them by name at stage 5):
      file::<file>::scope/<name> — a CTE by its declared name, a
      temp-table stage by its #name, a write target (INSERT/UPDATE/
      DELETE) by its target table name. Duplicate names within a
      file: file::<file>::scope/<name>#2, #3 … in statement order.
    - The DELIVERY scope (the statement that emits the procedure's
      result set): file::<file>::scope/delivery.
    - UNNAMED subqueries key positionally under their statement:
      file::<file>::stmt/<pos>::scope/sub1, sub2 …
  - scope_name: the declared name (CTE name, #temp name, target
    table name); null for subqueries; "delivery" for the delivery.
  - scope_kind (decision 1a): cte | temp_table | subquery |
    delivery | write_target.
  - operation: select | insert | update | delete — what the scope
    DOES to its population (a write_target scope's verb; delivery
    and cte are always select).
  - owning_statement: the statement node_id that mints this scope.
  - evidence {fragment, line, column} — the scope's verbatim SQL.
  - contains edges (statement -> scope) carry position = the
    declaration order within the statement: CTEs 1..n in WITH
    order, the statement's main scope last.
  - CONSERVATION (stage-2 tests): every handled population
    statement (SELECT / SELECT INTO / INSERT / UPDATE / DELETE)
    mints EXACTLY ONE main scope (+ one per declared CTE); IF /
    WHILE / SET / GOTO mint none (their predicates attach at stage
    4, directly under their statement). Per file: scope_total =
    main scopes + ctes + subqueries, printed in the census.
  - Stage-4 notes, recorded now: (a) control-flow predicates (IF
    x=1, WHILE …) have no scope or structure above them — they
    attach via contains directly to their STATEMENT with role
    "condition" (the ladder bends for control flow; ruled here so
    stage 4 doesn't improvise). (b) subquery scopes INSIDE
    predicates (IN (SELECT…), EXISTS (…)) are invisible until
    predicates are walked — those scope rows APPEND at stage 4;
    stage 2 mints what the query level shows (CTEs, main scopes,
    FROM-level derived tables). Named here so the stage-2 census
    is never mistaken for the final subquery count.
  - SELECT INTO precision: INTO #name is a temp_table scope; INTO
    a real table is a write_target scope (the # prefix decides).
- 05_structure_sheet.json — STAGE 3 AMENDMENT (APPROVED 2026-10-02,
  Sunny in chat, all six rulings; supersedes the thin one-line
  spec):
  - node_id: <owning_scope_id>::structure/<KIND>/<n> — n is the
    1-based index among same-kind siblings in the scope (JOIN/1,
    JOIN/2 …).
  - structure_kind, THE CLOSED CLAUSE SET (ruled here; mirrored to
    the kind library as a Clause_Structure_Kinds sheet on approval):
    PROJECTION | FROM | JOIN | WHERE | GROUP BY | HAVING |
    ORDER BY | TOP | COMBINATION | SET.
    - PROJECTION = the SELECT list (the library's Phase A row).
    - TOP is its own kind (it shapes the population even without
      an ORDER BY).
    - SET = UPDATE's assignment clause (no corpus occurrences
      today; fabricated-test covered).
    - CASE is NOT here — it is an expression (stage 4), per the
      library's Expression_Kinds.
    - Boolean AND / OR / NOT are NOT here — they are the predicate
      TREE'S shape, landing at stage 4 (stage-4 note c, recorded
      now).
  - position: encounter order within the scope, 1-based.
  - kind properties (null unless named):
    - JOIN: join_type (Inner | LeftOuter | RightOuter | FullOuter |
      Cross | comma | CrossApply | OuterApply — the comma join and
      APPLY are the prior estate's field lessons).
    - COMBINATION: combination_type (Union | Except | Intersect),
      all (true = UNION ALL, duplicates kept).
    - PROJECTION: distinct (true/false — the grain ruling),
      member_total (count of select elements INCLUDING stars — the
      stage-4 conservation denominator, no silent skips).
    - TOP: top_text (verbatim until stage 4 maps the expression).
  - owning_scope: the scope node_id; contains edges scope ->
    structure carry the position.
  - evidence: the verbatim clause fragment (PROJECTION spans the
    first through last select element).
  - COMBINATION ARMS — new ruling: a UNION/EXCEPT/INTERSECT scope
    gets ONE COMBINATION structure, and each arm is minted as a
    SCOPE row (scope_kind "union_arm" — the SIXTH kind, appended
    to the stage-2 sheet at stage 3 the way predicate subqueries
    append at stage 4), node_id <owning_scope_id>::arm1, arm2 …,
    contains edge COMBINATION structure -> arm scope. Arms then
    grow their own structures normally — the prior estate's
    lesson: an empty combination scope laundered a counted gap
    into "no sources are read"; arms are ALWAYS full scopes.
  - CONSERVATION (stage-3 tests): every select-operation scope has
    exactly one PROJECTION (arms included; a pure combination
    scope has exactly one COMBINATION and >= 2 arms instead);
    FROM present whenever the SQL reads a source; every structure
    owned by an existing scope; evidence on every row.
- 05_predicate_sheet.json + 05_expression_sheet.json — STAGE 4
  AMENDMENT (APPROVED 2026-10-02, Sunny in chat, all eight
  rulings; supersedes the two thin lines):

  THE PREDICATE SHEET
  - node_id: <parent_id>::pred/<n>. The parent is the attachment
    point: a clause structure (WHERE / HAVING / a qualified JOIN's
    ON), a boolean structure (below), or a STATEMENT (control-flow
    condition — note a, edge role "condition").
  - predicate_kind: the closed 13 (library Predicate_Kinds; the
    operator IS the kind). Roles per kind are the library's Roles
    column — conservation checks them (a COMPARE has subject +
    comparand; a RANGE has subject + both bounds; a NULL_CHECK has
    subject only; EXISTS_SELECTION has selection only).
  - negated: structural NOT over ONE predicate folds to this flag
    (NOT LIKE, NOT IN, NOT BETWEEN, IS NOT NULL included); NOT over
    a GROUP mints a NOT structure node. LOGIC IS NEVER REWRITTEN —
    no De Morgan, ever.
  - BOOLEAN SHAPE: AND / OR / NOT append to the STRUCTURE sheet at
    stage 4 (their kinds are already ratified Structure_Kinds rows),
    ids <parent_id>::structure/AND/<n> chaining downward;
    parentheses dissolve (ratified: syntax only). A WHERE owns
    exactly one child tree root; a comma JOIN owns none.
  - evidence on every row.
  - DENOMINATOR LAW ARMS HERE: a boolean ScriptDom type in the
    library's TSQL_Denominator as "mapped" maps; one marked
    DEFERRED met in real SQL becomes a VISIBLE COUNTED row
    (predicate_kind "DEFERRED:<type>", never voiced, never red);
    a boolean type beyond the table = RED BUILD, the build dies
    naming it.

  THE EXPRESSION SHEET
  - node_id: <parent_id>::expr/<n>; expression_kind: the closed 10
    (library Expression_Kinds); raw_text verbatim; evidence.
  - ROLES RIDE THE CONTAINS EDGES (the library's own law), and are
    MIRRORED on the expression row for the eye. Structure-owned
    members (PROJECTION / GROUP BY / ORDER BY / TOP) have role null
    and position = member order; projection members also carry
    output_name (the AS name or the column's own name; null when
    anonymous).
  - Nesting: function args, arithmetic sides, cast/unary inners are
    expression -> expression contains edges, position-ordered. CASE:
    WHEN branches hold PREDICATE children (edge role "condition"),
    THEN/ELSE hold expression children — recursion stays inside the
    closed sets.
  - STARS ARE COUNTED, NOT ROWS: SELECT * means "every column of
    the source at read time" (the ratified enumeration-free
    meaning) — no expression row; the PROJECTION structure gains
    star_total (+ star qualifiers), and conservation reads
    expression members + star_total == member_total.
  - PREDICATE-LEVEL SUBQUERIES (stage-4 note b lands): IN (SELECT
    …) / EXISTS (…) mint their scope rows NOW — scope_kind
    subquery, numbering CONTINUING the statement's subN counter —
    complete with their own structures and predicates (full
    recursion; never an empty scope). The subquery_ref expression
    resolves_to its scope at stage 5.
  - IF / WHILE conservation: exactly one condition tree per
    control-flow statement, attached to the statement itself.
- 05_contains_edges.json: from_id, to_id, position, role.
- 05_resolves_edges.json + 05_parameter_sheet.json — STAGE 5
  AMENDMENT (APPROVED 2026-10-02, Sunny in chat — "go" — after the
  six-decision debate; each D-section ruled individually the same
  day):

  THE RESOLVES SHEET — the ledger of every binding attempt. EVERY
  reference gets exactly ONE BINDING, resolved or not; binding is
  EDGES, never properties (Phase III walks edges). A binding is one
  row — EXCEPT a star_member binding (D3 as reopened 2026-10-02),
  which is a FAN: N rows with the same from_id, one per origin arm,
  plus at most one behind_star remainder row when an arm is blind.
  Fields: from_id, to_kind, to_id, match_basis, class (unresolved
  rows only), ref_text (verbatim), plus the join-binding fields
  below. The closed match_basis vocabulary: exact | fold (D1,
  name-matching) · member | star_member | behind_star (D3, reads
  through scopes).
  [PROCESS NOTE 2026-10-02, Sunny's catch: the star_member build
  landed before this conservation text was amended — the contract
  must be whole BEFORE the first red test, amendments included.]

  D1 — THE NAME-MATCHING LAW (ruled 2026-10-02): table and column
  names match BARE (qualifiers the SQL happened to use are dropped;
  the dictionary carries database/schema separately) and
  CASE-FOLDED — nothing fuzzier: no spelling distance, no synonyms
  (lane-1 discipline). Every edge records match_basis (exact |
  fold). Aliases walk the FROM's alias map first ([relation].NAME →
  the aliased table → its column). A bare column matching MORE THAN
  ONE in-scope table is unresolved class ambiguous_column with the
  candidates listed — NEVER a pick.

  D2 — THE UNRESOLVED VOCABULARY (ruled 2026-10-02): a non-binding
  is a counted row with a class from the closed set (ported to the
  kind library as a Resolution_Classes sheet on approval; grows by
  Sunny's ruled row):
    unknown_table            table absent from the dictionary — the
                             HUMAN QUEUE: each row is a
                             request-for-metadata; also dictionary-
                             growth flywheel ore
    unknown_column           table known, column genuinely absent —
                             a phase 02 extract-quality signal
    blocked_by_unknown_table columns whose every candidate table is
                             unknown — consequences, not causes; no
                             lookups attempted; they clear
                             themselves when the table lands
    ambiguous_column         D1's never-pick rule
    wildcard                 the * references — nothing to resolve
                             by design; classed so conservation
                             balances
    table_function           a function used as a source
                             (STRING_SPLIT) — not a table, visible
    scope_column_missing     D3's pathological branch
    value_code_unknown       D5's routed-but-missing code
    unknown_parameter        D6's undeclared @name
  THE GAP-FIRST GATE (ruled 2026-10-02): phase 06 does NOT open
  while unknown_table is outstanding — each one is resolved into a
  dictionary (Sunny's authorship) or accepted by her named ruling;
  stage 5 re-runs and the blocked_by rows clear.

  D3 — LINEAGE THROUGH SCOPES (ruled 2026-10-02; REOPENED AND
  AMENDED 2026-10-02, Sunny's ruling in the 06 design session): a
  table_ref to #temp / a CTE binds to the minting scope (to_kind
  scope). A COLUMN read through that scope binds FINE — to the
  projection-member expression node that produced it (to_kind
  member, match_basis member), so Phase III can walk field →
  CASE → source column → dictionary.
  STAR EXPANSION (the amendment): when the minting scope's outputs
  include a star, the star is EXPANDED THROUGH THE GRAPH when its
  source is itself a scope whose outputs the graph holds — the
  name is matched through the source scope's explicit outputs and
  the read binds to that member with match_basis star_member (a
  new match_basis value, counted apart from member; NOT a
  Resolution_Class — those name unresolved reasons). A union-arm
  star yields one star_member edge PER ARM (multi-origin is the
  truth: #combined_census.PAT_ID originates in both
  #census_monthly and #clinic_monthly). Expansion recurses: a star
  over a scope that is itself star-fed walks until explicit
  outputs or a base table. When the star's source is a BASE TABLE,
  the read binds to the scope with match_basis behind_star,
  honestly blind — the column list lives in the run-time catalog,
  not the SQL text; expanding from the dictionary snapshot would
  claim catalog truth the parse does not have (ordinal-order risk
  on positional inserts; silent staleness when the table changes).
  Rationale for reopening: star-over-scope expansion uses ONLY
  stored graph truth — the same evidence standard as every other
  bind; measured 2026-10-02: all 67 behind_star edges in the
  corpus were the expandable kind (59 #combined_census, 8
  #coverage), zero were star-over-base-table.
  Neither bind possible: unresolved scope_column_missing.

  D4 — JOIN BINDING (ruled 2026-10-02, supersedes the match/
  discovered binary): join relationships are DIRECTION-FREE —
  matching, storage semantics and traversal are symmetric; the
  asymmetric facts stay properties (FK owner / cardinality on the
  dictionary join row; the outer join's preserved side as
  join_type on the semantic JOIN node). A JOIN structure's
  table-to-table equality pairs bind to a declared join
  direction-blind with COVERAGE recorded: full (pairs == the
  declared join_id's whole ordinal set) or partial (strict subset;
  STILL BOUND, missing ordinals listed — the fan-out-risk /
  half-key signal, queryable, never judged by the machine). No
  declared match → 05_discovered_joins.json verbatim, with
  related_join_id noted when >= 1 pair overlaps a declared join.
  ON-CLASS (ruled 2026-10-02, stored): stage 5 stamps on_class on
  every predicate under a JOIN structure: join_pair (an equality
  between columns resolving to the two sides) | population_filter
  (non-pair residue under an INNER join — a membership decision) |
  lookup_shaping (non-pair residue under an OUTER join — picks
  which row decorates, NEVER voiced as a population filter; the
  race_list LINE = 1 lesson).

  D5 — THE VALUE BRIDGE (ruled 2026-10-02): fires for
  comparand-role literals (all COMPARE_* kinds and IN_LIST
  members; not pattern/escape, not RANGE bounds) when the resolved
  subject column ROUTES to a value-bearing table — directly (the
  subject's own table carries value rows: CLARITY_DEP.
  DEPARTMENT_ID = 100108022 → "CCMC Emergency") or via ONE
  declared join (PATIENT_RACE_C = 1001 → ZC table → "Hispanic or
  Latino"). Code match is exact after string normalization (1001
  == '1001'); no folding. Routed + matched → the literal binds
  to_kind value. Routed + missing → counted value_code_unknown
  (the false-absence lesson). No route → no attempt, no noise
  (LINE = 1 is just a number).

  D6 — PARAMETERS (ruled 2026-10-02): 05_parameter_sheet.json —
  node_id file::<file>::param/@name, name, kind
  (procedure_parameter — the CREATE PROCEDURE header, Phase IV's
  future knobs | local_variable — DECLAREd, whose default_text
  often hides population logic: the @StartDate 24-month window),
  data_type verbatim, default_text verbatim when present,
  evidence; contains edge file → parameter in declaration order.
  The DECLARE statements themselves stay operational statement
  rows; stage 5 reads their contents. Every parameter_ref resolves
  to_kind parameter; an undeclared @name is unresolved
  unknown_parameter.

  MECHANICAL CATCH-UP (no ruling needed, noted 2026-10-02): stage
  5 mints table_ref EXPRESSION rows for the FROM/JOIN clauses'
  named tables (stage 3 only scoped derived tables), with alias
  recorded — the nodes the resolves rows hang from.

  CONSERVATION (stage-5 tests): every table_ref, column_ref and
  parameter_ref expression, every routed comparand literal, and
  every qualified JOIN structure gets exactly one BINDING — one
  resolves row, or a star_member fan (same from_id: N star_member
  rows + at most one behind_star remainder; no other multi-row
  shape is legal); resolved-by-to_kind + unresolved-by-class ==
  total attempts; the census prints both breakdowns and the
  unknown_table list PROMINENTLY (the human queue).
- 05_exclusion_ledger.json: file_name, reason (the parser's error
  strings), recorded_at. A file here is counted out of every
  conservation total, loudly.
- 05_discovered_joins.json: file_name, left table.column, right
  table.column, join_type, evidence — the ON pairs seen in SQL with
  no declared dictionary join row.

What models are used?
- None. Phase 05 is deterministic: ScriptDom (the one parse door,
  AIVIA_01_Code/scriptdom_loader.py) + plain Python. No LLM calls,
  no embedding calls, no keys consumed.

Who fills out the sheets?
- All sheets: the phase 05 build script (Claude-authored in
  AIVIA_01_Code/, run by Sunny's hand), stage by stage per design
  decision 8. No hand-edited rows in any output sheet; a wrong row
  is fixed by fixing the build and re-running.

Who can read these files?
- Sunny Zheng
- Claude Code Agent
- Code script authorized by Sunny Zheng

Who can edit these files?
- 05_kind_library.json: Sunny only (after the one ratified port —
  see [SUNNY?] above).
- All output sheets and ledgers: the build script only.

How to test?
/opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v
- Claude's tests: AIVIA_01_Test/test_05_semantic_graph_data_contract.py
  (red before each stage's code, per the standing process).
- Sunny's tests: AIVIA_01_Test/test_05_semantic_graph_data_contract_sunny.md
  (her hand-written cases; Claude adds the run commands after build).
- The conservation checks are tests, not advice: handled +
  operational + gap + remainder = total per file; every scope's structures accounted; every
  predicate's expressions accounted; resolved + unresolved-by-class
  = total references; an unmapped ScriptDom type is a RED build.
