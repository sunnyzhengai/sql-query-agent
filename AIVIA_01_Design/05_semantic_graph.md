05_semantic_graph.md

Status: DRAFT IN PROGRESS (started 2026-10-01). Sunny owns this doc;
Claude scribes drafts at her direction during the design sessions —
document-as-we-go so no draft is lost in chat. Nothing below is
ruled unless marked RULED with a date.
Product phase: I — Describe (00_Architecture.md).
Prior art: AIVIA_01_Design/briefs/Brief_05_Prior_Art.md — consult
before designing each piece; do not re-derive what the previous
estate solved.

Design description (draft):
- Parse the 8 subject SQL files (phase 01's corpus) with ScriptDom
  through the one parse door (AIVIA_01_Code/scriptdom_loader.py) and
  build the semantic graph: the nodes and edges that represent each
  file's internal logic, bridged to the phase 02 dictionary graph.
- This phase produces STRUCTURE only. Technical descriptions and the
  chat-page join are later build phases (see the phase split below).

THE PHASE SPLIT — RULED 2026-10-01 (Sunny, in chat): the semantics
layer is three build phases, not one —
- 05 semantic graph: parse + node/edge sheets + the bridge edges
  into the 02 dictionary + the parse-exclusion ledger. Acceptance:
  counts and conservation (every statement handled or counted in a
  remainder), Sunny eyeballs the sheets.
- 06 technical descriptions: the grammar-floor port; every ruled
  node grain gets its deterministic description; regenerates a
  tracked descriptions file per SQL file for Sunny's gap-check.
  Acceptance: byte-exact pinned sentences + her eye.
- 07 chat join: terms-list rows, abstracts, embeddings, per-node-kind
  detail contracts, map treatment. Acceptance: shape runs against
  the page, like phase 03.
Why split: three different data products with three different
acceptance styles (conservation counts / exact strings / shape
runs); each independently designed, built, tested per the standing
development principle; Sunny gap-checks real output at each stage
before the next builds on it.

THE DECISIONS (to rule, in discussion order):

1. Node kinds — UNDER DISCUSSION; Sunny's hierarchy spoken
   2026-10-01 (in chat), converging with the prior estate's
   metamodel:

   file
    └─ statement                 (the file's ordered steps)
        └─ scope                 (CTE / temp table / subquery /
                                  final SELECT — a logic boundary)
            └─ structure         (SELECT…, FROM…, JOIN-ON…, WHERE…)
                └─ dictionary nodes (phase 02 columns and tables)

   - Sunny's invariant (the load-bearing sentence, refined
     2026-10-01): every branch of the parsed file ends on a
     dictionary node (column or table) OR on an earlier scope of
     the same file (FROM #temp / FROM cte) — and since every
     scope's own branches obey the same rule, everything grounds in
     the dictionary transitively. The semantic layer never has
     leaves of its own. This is what makes it a layer ON TOP of the
     foundation, and what Phase III traversal will one day walk.
   - JOIN BINDING (ruled 2026-10-01; REFINED 2026-10-02 in the
     stage-5 debate — the contract's D4 is the full law): join
     relationships are DIRECTION-FREE (the asymmetric facts — FK
     owner/cardinality, outer-preserved side — stay properties,
     never arrow semantics). Binding records COVERAGE against the
     declared join's ordinal set: full | partial (still bound,
     missing ordinals listed — the half-key signal, recorded not
     judged) | discovered (the ledger, verbatim, with
     related_join_id when a pair overlaps) — never silent, and
     product signal (a join used in real SQL that the dictionary
     never declared is the usage flywheel's ore). Non-pair ON
     predicates get a stored on_class: join_pair |
     population_filter (INNER) | lookup_shaping (OUTER — never
     voiced as a population filter).
   - Structures (SELECT/FROM/WHERE/JOIN-ON/GROUP BY/…) ARE nodes —
     they are the junction where the semantic layer touches columns;
     a column reached through WHERE is a filter, through SELECT an
     output, through ON a join key — the difference is structural.
     (Corrects Claude's earlier demote-to-detail proposal.)
   - Sub-rulings (a-c RULED 2026-10-01, Sunny, in chat):
     a. RULED: ONE `scope` kind with a scope_kind property (cte |
        temp_table | subquery | delivery) — the parse proves they
        are the same thing, a named logic boundary; the property
        keeps the user-facing words.
     b. RULED: predicates and expressions ARE nodes (Sunny's
        preference, the prior estate's shape): a condition is a
        predicate node whose kind comes from the closed set of 13
        (COMPARE_EQ, RANGE, IN_LIST, PATTERN_MATCH, NULL_CHECK, …;
        the operator is the node's KIND, not a child node), with
        contains edges carrying roles (subject | comparand |
        lower_bound | upper_bound | pattern | …) to expression
        nodes (column_ref, literal, parameter_ref, function,
        arithmetic, case, …). column_ref expressions resolve to
        dictionary columns.
     c. RULED IN: the VALUE bridge — a literal expression in a
        predicate resolves to a phase 02 stored value row when one
        matches (code + meaning), so filters can answer as
        ADT_PAT_CLASS_C = 101 "Inpatient". New capability; the
        prior estate had no value estate to bind to.
     d. OPEN (phase 07's dial): which kinds are chat-SEARCHABLE
        populations — being a node does not obligate being a search
        population.

2. Edge kinds — RULED 2026-10-01 (Sunny, in chat): the graph stores
   ONLY what the parse proves —
   - `contains`: parent→child through the whole tree, with position
     where order is meaning and role (subject | comparand |
     lower_bound | …) on predicate→expression.
   - `resolves_to`: expression/table_ref → dictionary column, table,
     value row (sub-ruling 1c), or earlier same-file scope; plus the
     join binding of decision 1.
   - NO derived/shortcut rollup edges (Sunny's ruling: "I don't like
     shortcuts. I prefer walking the graph naturally to find
     answers"). One source of truth; nothing duplicated.
   - Consequences, accepted: multi-hop questions ("which tables does
     this file use?") are Phase III — Traverse territory, answered
     by walking the chains naturally. Phase I still conveys coarse
     facts through STORED technical descriptions (phase 06): the
     file-grain description names what the file reads, stages and
     delivers as prose — a lookup, not a walk. Phase I tells you;
     Phase III shows you the path.

3. Parse failure posture — RULED 2026-10-01 (Sunny, in chat): adopt
   record_exclusion verbatim — a failed parse is a counted, named
   exclusion row, never silent, never fatal. 8 files, expect 100%.

4. Closed vocabularies — RULED 2026-10-01 (Sunny, in chat): port
   kg2_kind_library's predicate kinds / expression kinds /
   operational statement kinds as a data file in AIVIA_01_Data/05_*;
   keep the TSQL_Denominator red-build rule (an unmapped ScriptDom
   type fails the build until ruled).

5. Sheet formats — RULED 2026-10-01 (Sunny, in chat): emit
   AIVIA_01's own JSON sheet shapes (the phase 02 pattern), NOT the
   prior estate's store/registry machinery; port ideas and data,
   not plumbing.

6. Technical description grain + the floor-vs-pseudo-code question —
   belongs to phase 06's doc, but the node-kind ruling here decides
   which grains CAN carry descriptions. Claude's standing
   recommendation: the ported grammar floor IS the technical
   description (deterministic, exact, proven); a rawer pseudo-code
   layer would re-derive solved work.

7. Embedding grains — deferred to phase 07's contract (ruled open in
   00_Architecture.md: technical description, business description,
   or both; plus whether phase 01's file-NAME embeddings are
   superseded by file-node embeddings).

8. Build sequencing — RULED 2026-10-01 (Sunny, in chat): the two
   phases run in OPPOSITE directions —
   - Phase 05 builds TOP-DOWN (file → statement → scope → structure
     → predicate/expression → resolution), because the parse hands
     us the tree from the root (leaves cannot be found without
     walking through their ancestors), and because each stage's
     completeness check uses the stage above as its denominator —
     every statement accounted before scopes claim them, every
     scope before structures — so a silent gap has nowhere to hide,
     and each stage's sheet is small enough for Sunny's eye.
   - Phase 06 builds BOTTOM-UP (Sunny's direction): a scope's
     description composes from its predicates' voiced sentences, a
     statement's from its scope, the file's from its statements —
     the prior estate's ruled order, continuing upward into Phase
     II's business descriptions.
   - The sentence: structure pours down, meaning climbs back up.

9. Dynamic SQL — RULED 2026-10-01 (Sunny, in chat, from the L03
   census: 2 of 8 files run EXEC (@SQL)): counted NOW as the named
   gap class dynamic_sql (library sheet Statement_Gap_Classes; the
   string-form EXEC only — a procedure-call EXEC is a different,
   future thing). The affected file's description must say plainly
   that its logic is partially opaque (phase 06). THE CHASE —
   reconstructing a statically-built @SQL string and parsing the
   reconstruction, always marked reconstructed, never parse-proven —
   is a CANDIDATE FUTURE PHASE, not part of 05/06/07.
   Same ruling: UseStatement added to the library's operational
   kinds (USE [db] shapes no population).

Local build steps (draft, follows the top-down staging if ruled):
    L01: data contract 05_semantic_graph_data_contract.md.
    L02: port the closed vocabularies as the 05 kind data file
         (decision 4), with the red-build denominator check.
    L03: mapper stage 1 — file + statement sheets + remainder
         ledger; Sunny eyeballs against the raw SQL.
         BUILT 2026-10-01: pseudo code approved (two contract
         refinements: dotted paths, disposition field), tests red
         then green. SAME DAY, from the census: decision 9 ruled
         (dynamic_sql gap class + UseStatement operational), gap
         disposition built test-first. Final census: 8/8 parsed,
         65 statements, 0 remainder (2 gap: the EXEC (@SQL) pair).
         10 stage tests green, full suite 151 in 111.29s, ruff
         clean. Build run at Sunny's word ("go"), sheets live in
         AIVIA_01_Data/05_semantic_graph/.
         OPEN: Sunny's eyeball of the sheets; her hand-written
         cases md not yet authored.
    L04: stage 2 — scope sheet (cte | temp_table | subquery |
         delivery named and claimed).
         BUILT 2026-10-02: contract stage-2 amendment approved
         (five rulings: name-keyed ids, write_target kind +
         operation field, edge declaration order, conservation,
         the two stage-4 notes), 7 tests red then 16 green, ruff
         clean, full suite 157 in 110.73s. Census: 24 scopes / 8
         files; the dynamic-SQL pair mints ZERO scopes (their
         logic lives in the @SQL string — decision 9 visible).
         OPEN: Sunny's eyeball; her hand-written cases md.
    L05: stage 3 — structure sheet (positioned clauses per scope).
         BUILT 2026-10-02: contract stage-3 amendment approved (six
         rulings: closed clause set, TOP its own kind, union arms
         as full scopes, member_total counts stars, closed join
         types, kind-scoped sibling ids), Clause_Structure_Kinds
         mirrored to the library, 7 tests red then 22 green, ruff
         clean, full suite 163. FIELD FINDING: the comma join
         arrives as MULTIPLE TableReferences entries, not a join
         node — n sources = n-1 comma joins, handled at clause
         level. Census: 154 structures / 28 scopes (4 union arms).
         OPEN: Sunny's eyeball; her hand-written cases md.
    L06: stage 4 — predicate + expression sheets (kinds from the
         closed sets, roles on contains).
         BUILT 2026-10-02: contract stage-4 amendment approved
         (eight rulings), 12 tests red then 33 green, ruff clean,
         full suite 174. THE RED-BUILD LAW FIRED ON ITS FIRST
         CORPUS RUN: IIfCall (IIF) was beyond the closed set —
         ruled into `case` (value branching in sugar form), the
         law's first catch. Census: 211 predicates (124 COMPARE_EQ,
         22 NULL_CHECK, 17 IN_LIST, 11 negated, 0 DEFERRED), 1096
         expressions (573 column_ref, 373 literal, 75 function),
         42 boolean nodes (30 AND / 12 OR), 8 predicate-level
         subqueries minted full, 6 projections carry stars.
         OPEN: Sunny's eyeball; her hand-written cases md.
    L07: stage 5 — resolution: dictionary bindings (column / table /
         value / earlier scope), join bindings + discovered-join
         ledger, unresolved counted by class.
         BUILT 2026-10-02: the six-decision debate ruled D1-D6 same
         day (contract stage-5 amendment), Resolution_Classes (9 +
         the gap-first gate) ported to the library, 13 tests red
         then 45 green, ruff clean, full suite 186.
         The build command (three dirs now):
         /opt/homebrew/bin/python3.11 AIVIA_01_Code/semantic_graph.py
             AIVIA_01_Data/01_subject_sql_files
             AIVIA_01_Data/05_semantic_graph
             AIVIA_01_Data/02_emr_data_dictionary
         CENSUS: 851 bound / 102 unresolved; 49 declared joins all
         FULL coverage; 119 value binds; 37 parameter nodes.
         FINDINGS FOR SUNNY'S RULING:
         - THE HUMAN QUEUE: one unknown table —
           clarity.dbo.CR_STAT_EXECUTION (2 uses + 6 blocked
           columns). The gap-first gate holds phase 06 until it is
           dictionaried or accepted by name.
         - 86 value_code_unknown, ALL department ids
           (CLARITY_DEP/ADT.DEPARTMENT_ID codes like 108022) — the
           value extract misses departments the SQL filters on;
           gap-check material.
         - 22 discovered joins: 10 involve temp/cte scopes (staging
           mechanics), 12 REAL undeclared joins (DATE_DIMENSION
           calendar joins, V_PAT_ADT_LOCATION_HX view joins — two
           with a related declared join noted) — dictionary-growth
           ore.
         CR_STAT_EXECUTION — RULED 2026-10-02 (Sunny, in chat,
         option 1): the table exists in Clarity but Epic's own
         dictionary (CLARITY_TBL/CLARITY_COL) has NO entry — Sunny
         AUTHORS A SUPPLEMENTAL ENTRY in the 02 estate (structure
         from INFORMATION_SCHEMA, descriptions her hand, marked
         supplemental). Used by the two CensusDashboard files only
         (the data-freshness stamp; 2 columns). The gate opens when
         her rows land and the 05 build re-runs clean.
         SUPPLEMENTAL ENTRY LANDED + GATE CLEARED 2026-10-02:
         Claude authored at Sunny's word (SUPP:: ids; table + the
         3 used columns incl. EXEC_NAME, which the 02 no-match
         cross-check caught after the first 2); Sunny ran the 02
         sheet build (embeddings: new rows only, reuse law held);
         abstracts regenerated (4 new / 1656 reused, sunny_* rows
         preserved); goldens re-based by measurement in both
         pinned places (39 tables / 1621 columns / no-match 0 /
         rule edges 182 — EXEC_START_TIME's date_dimension edge —
         / abstracts 1660); 05 rebuilt: 859 bound / 94 unresolved,
         unknown_table AND blocked_by_unknown_table EMPTY (pinned
         by test_corpus_queue_is_empty; the queue mechanism now
         tested on a fabricated estate). Suite 187 green, ruff
         clean. THE GAP-FIRST GATE IS OPEN — phase 06 may be
         defined.
         THE 86 DEPARTMENT CODES — RESOLVED 2026-10-02 (Sunny's
         find, in chat): the corpus had been PARTIALLY
         DE-IDENTIFIED — department ids had their leading 10/100
         stripped (100050003 -> 0050003). Sunny pulled the fresh
         CLARITY_DEP list; reconstruction mapped ALL 86 (72 by the
         SQL's own trailing-comment names, 14 by unique prefix
         restore, both methods agreeing everywhere; map in the
         session scratchpad). Sunny ruled REPAIR THE CORPUS; 86
         replacements applied (Totals_SSRS 8, LOTE Detail 78),
         rebuild: 945 bound / 8 unresolved — value_code_unknown
         EMPTY; suite 187 green. The 8 remaining unresolved are
         the ruled floor: 2 table_function (STRING_SPLIT), 2
         unknown_column (its 'value' output), 4 wildcard.
         Her cases md RATIFIED 2026-10-02 (S8 in post-gate form).
         OPEN (non-gating, the LAST one): the 6 declare-or-leave
         discovered-join candidates (the 4 DATE_DIMENSION calendar
         joins recommended leave — the rule edges already model
         that class).
         D3 REOPENED 2026-10-02 (Sunny's ruling, in the 06 design
         session while debating 3c member lineage): stars over
         SCOPES expand through the graph's own stored outputs —
         new match_basis star_member, one edge per union arm,
         recursing to explicit outputs; star over a BASE TABLE
         stays behind_star (the genuinely blind class — corpus
         holds zero today). Measured trigger: all 67 behind_star
         edges were the expandable kind (59 #combined_census, 8
         #coverage). Contract D3 amended same day.
         BUILT 2026-10-02 (same session): pseudo code approved
         (Sunny: "go" — both sub-rulings as proposed: mixed case
         keeps the behind_star remainder; union name-vs-position
         bound stands, positional machinery deliberately not
         built), 6 tests red then green (_expand_star +
         bind_through_star at both bind sites; conservation law
         amended to one-BINDING-per-reference with the star_member
         fan shape), prediction confirmed EXACTLY: behind_star
         67 -> 0, star_member = 126 (59 dual-arm + 8 single).
         Sheets rebuilt: 1004 bound / 8 unresolved (the same ruled
         floor; 945 + 126 - 67 = 1004, conservation closes). Full
         suite 193 green, ruff clean. A side honesty gain: a name
         NO arm holds now lands scope_column_missing, not
         behind_star.
    Each stage: pseudo code first, Sunny approves, tests red, then
    code — the standing process.
Data contract: 05_semantic_graph_data_contract.md — TBD, authored
with the decisions.
