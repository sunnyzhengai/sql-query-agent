# test_05_semantic_graph_data_contract_sunny — Sunny's hand cases

STATUS: RATIFIED 2026-10-02 (Sunny, in chat; S8 in its post-gate
form). Scribed by Claude at her request, grounded in the real
census of the 2026-10-02 build; her eye is the acceptance.

## HOW TO RUN

The build (writes all sheets to AIVIA_01_Data/05_semantic_graph/):

    /opt/homebrew/bin/python3.11 AIVIA_01_Code/semantic_graph.py \
        AIVIA_01_Data/01_subject_sql_files \
        AIVIA_01_Data/05_semantic_graph \
        AIVIA_01_Data/02_emr_data_dictionary

Claude's suite:

    /opt/homebrew/bin/python3.11 -m pytest \
        AIVIA_01_Test/test_05_semantic_graph_data_contract.py -v

## THE CASES

S1 — The census adds up.
Run the build. Expect: 8 files built, 0 excluded, 65 statements,
36 scopes, 218 structures, 211 predicates, 37 parameters.
Every per-file line: handled + operational + gap + remainder =
total, remainder 0 everywhere.

S2 — Dynamic SQL is a named gap, never structure.
Open 05_statement_sheet.json; find the two EXEC rows
(Monthly_IP_Census Days + Totals, stmt/6): disposition "gap",
gap_class "dynamic_sql". The census shows those two files mint
0 scopes — no pretend-structure over an opaque string.

S3 — The drop-guard idiom reads true.
In 05_predicate_sheet.json find a predicate owned by an IF
statement (node_id contains ::stmt/ and ::pred/, no scope):
OBJECT_ID guard — predicate_kind NULL_CHECK, negated true, and in
05_contains_edges.json its edge role is "condition".

S4 — LINE = 1 shapes the lookup, not the population.
In 05_predicate_sheet.json find the predicate whose evidence says
[race_list].LINE = 1 (Detail LOTE file): on_class
"lookup_shaping". Its sibling PAT_ID = PAT_ID predicate under the
same JOIN: on_class "join_pair". No population claim anywhere.

S5 — A department code explains itself.
In 05_resolves_edges.json find to_id "CLARITY_DEP::100108022".
The SQL author hand-commented that department as CCMC Emergency;
check the dictionary meaning agrees. The bridge is the comment,
mechanized.

S6 — Reading through a star is honest.
Find the resolves row for [#combined_census].PAT_ID (Summary LOTE
file): to_kind "scope", match_basis "behind_star" — we know which
temp table it came from, and we do not pretend to know which
upstream column, because #combined_census outputs SELECT *.

S7 — Fine lineage exists where the outputs are explicit.
Count resolves rows with to_kind "member". Pick one; its to_id is
a projection-member expression node inside the minting scope —
follow it in 05_expression_sheet.json and eyeball that the member
really is the column the SQL built.

S8 — The human queue is EMPTY (updated 2026-10-02 after Sunny's
CR_STAT_EXECUTION supplemental entry landed).
The build prints NO "UNKNOWN TABLES" block. In
05_resolves_edges.json: zero rows class "unknown_table", zero
class "blocked_by_unknown_table", and the former CR_STAT columns
now BIND — find EXEC_START_TIME resolving to
CR_STAT_EXECUTION.EXEC_START_TIME (the supplemental metadata,
SUPP:: ids).

S9 — Declared joins bind, direction-free, full coverage.
In 05_resolves_edges.json: 49 rows to_kind "declared_join", every
one coverage "full", missing_ordinals []. Spot-check one:
adt.DEPARTMENT_ID = dep.DEPARTMENT_ID binds the declared
CLARITY_ADT-CLARITY_DEP join.

S10 — The discovered-joins ledger is ore, not noise.
05_discovered_joins.json has 22 rows; 10 with involves_scope true
(temp staging — fine), 12 real. The DATE_DIMENSION calendar joins
and the V_PAT_ADT_LOCATION_HX view joins are there, two with a
related_join_id pointing at their declared CLARITY_ADT cousins.

S11 — The hidden reporting window surfaced.
In 05_parameter_sheet.json find @StartDate (CensusDashboard
files): kind "local_variable", default_text carrying the CASE
with dateadd(m, -24, …) and the '03/01/2018' floor — the
24-month window, preserved verbatim for phase 06 to voice.

S12 — Same input, same graph.
Run the build twice. Every sheet byte-identical except parsed_at
in 05_file_sheet.json. (Claude's suite also locks this.)

## RULINGS THIS FILE WAITS ON
- CR_STAT_EXECUTION: RESOLVED 2026-10-02 — Sunny's supplemental
  entry landed, the queue is empty, the gate is open.
- The 86 absent department codes: environment/vintage research.
- The 12 real discovered joins: declare into the join sheet or
  leave as ledger ore.
