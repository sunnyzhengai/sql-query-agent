# GQL Gates — the M-ladder verification queries (Sunny's surface)

*(Moved from docs/deployment/FABRIC_GRAPH_LOAD.md 2026-09-10 at
Sunny's request: the gates live beside the tests they mirror.
The runbook keeps setup/load/dialect; THIS file is what you run.
Every gate: copy one query, run it, compare the stated answer.
Machine twin of every number:
AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json.)*

## The original M1 gate (VERIFIED by your GQL 2026-09-10, sepsis
estate — kept as record)


```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: `db 1 · db_schema 3 · table 90 · column 4554` —
and NOTHING else (no statement, no scope: the Shape_Ledger's
TARGET rows are honestly absent until their batches land).

```gql
MATCH ()-[c:has_part]->() RETURN count(c) AS cnt
```
Expected: **4647** (3 + 90 + 4554).

```gql
MATCH (t:table) WHERE t.name = 'SEVERE_SEPSIS_STAGING'
RETURN t.description AS tableDescription
```
Expected: "ETL staging table for identifying severe sepsis cases.
Contains records of patients who meet the criteria for severe
sepsis along with tracking for compliance with bundle elements."

```gql
MATCH (s:db_schema)-[:has_part]->(t:table)
RETURN s.name AS schemaName, count(t) AS tables GROUP BY schemaName
```
Expected: the three schemas with their table counts summing to 90.


## THE ONE-PROC LADDER GATES (ruled 2026-09-10): M2–M7 on
ed_sepsis_dev

From M3 on, batches build/test/GATE on the one-proc estate
(`AIVIA_Product/estates/ed_sepsis_dev` — USP_ED_SEPSIS alone,
full dictionary). Answer key with every expected number:
`expected_m_gates.json` in that estate dir — numbers derived from
the parse, pinned by test_ed_sepsis_dev_estate.py BEFORE each
batch builds. Export: `python3.11 -m aivia.flows.export_graph
ed_sepsis_dev`.

**RULED (Sunny 2026-09-10): the gate runs on the DEV ESTATE.**
Load ed_sepsis_dev's exports; the full sepsis estate re-loads at
phase boundaries (M7, M12). The technical layer is identical in
both estates, so nothing M1 verified is invalidated.

Every gate below follows the census shape: label counts == the
key's node rows, edge-type counts == the key's edge rows, plus
the batch's special checks.

**DIALECT CORRECTION (2026-09-11, found live by Sunny): Fabric
GQL has NO `type(r)` function** (that's openCypher; Fabric's
graph functions are labels/nodes/edges/elements/path_length
only). The edge census therefore runs as a PER-TYPE BATTERY plus
a grand total — and the total closes the census: if the per-type
counts SUM to the unfiltered total, no undeclared edge type
exists. Node census stays `labels(n)`:

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
```gql
MATCH ()-[r:has_part]->() RETURN count(r) AS cnt
```
(one per edge type, then:)
```gql
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```

### M1 gate — technical layer + joins_to (re-homed here, Sunny's
redesign ruling)

| expect | value |
|---|---|
| nodes | db 1 · db_schema 3 · table 90 · column 4554 |
| edges | has_part 4647 (3+90+4554) · joins_to 65 (dictionary-declared, onColumns) |
| spot | ADT_EVENTS joins_to neighbors carry onColumns |

THE FULL-CENSUS TABLES (hardened 2026-09-10, Sunny's directive —
the blob-corpse lesson: a spot check passes while the graph
doesn't exist; the gate is EVERY label and EVERY edge type,
totals exact, both directions). Q1/Q3 expected results after each
batch, cumulative:

*(Tables RE-BASED 2026-09-16 to the key at 1.45.0 — they now
carry ERA 3's direct_read/reads-retirement and M4's measured
numbers; the pre-era-3 rows stand in git history.)*

| after | Q1 nodes by label | total |
|---|---|---|
| M1 | db 1 · db_schema 3 · table 90 · column 4554 | **4648** |
| M2 ✅ | + scope 44 · join 95 (+ direct_read 6 at ERA 3) | **4793** |
| M3 ✅ | + condition 1141 · param 2 | **5936** |
| M4 ✅✅ | + derived_column 156 (measured at build; SERVED gate passed 2026-09-16) | **6092** |
| M5 | + statement 67 · condition→1147 · param→4 (holdovers twin-authored) | **6167** |
| M6 | + file 1 | **6168** |
| M7 | + pbi_report 1 · description 1 · agent 1 · role 1 · responsibility 1 · blessed_name 113 | **6286** |

| after | Q3 edges by type | total |
|---|---|---|
| M1 | has_part 4647 · joins_to 65 | **4712** |
| M2 ✅ | + left_side 101 · right_side 87 · has_part→4748 (ERA 3: reads RETIRED, direct_read sided) | **5001** |
| M3 ✅ | has_part 5889 · resolves_to 165 · uses_param 2 · rest same | **6309** |
| M4 ✅✅ | has_part 6045 · + cites 97 (measured at build — 100→97 store grain; SERVED gate passed 2026-09-16) | **6562** |
| M5 | has_part 6095 · resolves_to 169 · uses_param 4 | **6618** |
| M6 | has_part 6166 | **6689** |
| M7 | + executes 1 · describes 1 | **6691** |

(✅ = measured from the built store; unmarked = twin-authored,
reconciled against the tree at build — precedent: joins 93→95,
conditions 748→1141, cites 100→97.)

Any label or edge type not in the row = a gate failure; any
declared count off by one = a gate failure. The machine copy of
these tables (with every per-batch delta and its breakdown) is
`expected_m_gates.json`.

### M2 gate — THE JOIN LAYER [BUILT 2026-09-10, store-verified;
every number below MEASURED from the built store; YOUR GQL on
the dev estate closes the batch]

Load first (once): upload ALL parquets from
`AIVIA_Product/estates/ed_sepsis_dev/graph_export/` → Load to
Tables (dbo) → in the graph model add node `scope` (key nodeId;
name, description, structures) and node `join` (key nodeId;
name, description, onPredicate) → add edges: `has_part`
scope→join via graph_has_part_scopeJoin · `left_side` join→table
AND join→scope (two mappings) · `right_side` likewise · `reads`
scope→table via graph_reads_scopeTable → Save → ONE refresh.

The full census (any extra label/type or off-by-one = failure):

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: db 1 · db_schema 3 · table 90 · column 4554 ·
scope 44 · join **95** — total 4787, nothing else.
**Q1 GREEN — Sunny's GQL 2026-09-10** (the earlier failures were
a missing GROUP BY, not capacity). The edge census's original
`type(r)` form was NEVER runnable — my openCypher habit, not
your capacity (corrected 2026-09-11); use the battery below.

The edge battery (no `type(r)` in Fabric GQL — one count per
type, then the total):

```gql
MATCH ()-[r:has_part]->() RETURN count(r) AS cnt
```
→ **4742**
```gql
MATCH ()-[r:joins_to]->() RETURN count(r) AS cnt
```
→ 65
```gql
MATCH ()-[r:left_side]->() RETURN count(r) AS cnt
```
→ **95**
```gql
MATCH ()-[r:right_side]->() RETURN count(r) AS cnt
```
→ **87**
```gql
MATCH ()-[r:reads]->() RETURN count(r) AS cnt
```
→ **6** — HISTORICAL: `reads` RETIRED at ERA 3 (registries
1.43.0); after the 1.43.0 load the type is unmapped. See the
ERA 3 gate below.
```gql
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```
→ **4995** — and 4742+65+95+87+6 = 4995 proves no undeclared
edge type exists (the census closes arithmetically).

| expect | value |
|---|---|
| descriptions | scope 44/44 · join 95/95 non-empty (verbatim-law checked in AIVIA_Test) |
| join conservation | 95 = 87 two-sided + 8 one-sided (ON vs param/literal — left only, counted) + 0 no-sided |
| side targets | →table 88 · →scope 94 |
| reads coverage | remainder 6 + covered-by-sides 53 == read-set 59 |
| joinType | CLOSED at M3 backfill — the tree carried join_type all along: Inner 39 · LeftOuter 56 |
| spot | `#Base_Pop`'s join#4 description: "Joins REF_ED_DISPOSITION with HOSPITAL_ENCOUNTERS on REDI.ED_DISPOSITION_CODE = HE.ED_DISPOSITION_CODE." |

THE DRIFT QUERY — DIALECT NOTE (2026-09-11): Fabric GQL does not
yet support pattern predicates in WHERE nor EXISTS-with-pattern
("not supported yet"), so the single-statement form is COUNTED as
a pending capability. The gate runs as TWO pure-GQL steps + a
set difference, plus a per-finding absence proof:

```gql
MATCH (j:join)-[:left_side]->(a:table), (j)-[:right_side]->(b:table)
RETURN DISTINCT a.name AS a, b.name AS b ORDER BY a, b
```
→ 28 observed table-pairs.
```gql
MATCH (x:table)-[:joins_to]->(y:table) RETURN DISTINCT x.name AS a, y.name AS b
```
→ 65 declared pairs. Observed − declared = EXACTLY:
ENCOUNTER_VISIT_REASONS↔VISIT_REASONS and
MEDICATIONS↔REF_GENERIC_MED. Absence proof per finding:

```gql
MATCH (x:table WHERE x.name = 'MEDICATIONS')-[:joins_to]-(y:table WHERE y.name = 'REF_GENERIC_MED')
RETURN count(*) AS cnt
```
→ 0 (no declared edge exists).
**VERIFIED LIVE on the served graph 2026-09-11.**

THE COVERAGE INVARIANTS (superseding the side-reads invariant —
reads is the remainder, never the union). Disjointness must
return zero:

```gql
MATCH (s:scope)-[:reads]->(t:table),
      (s)-[:has_part]->(:join)-[:left_side|:right_side]->(t)
RETURN count(*) AS doubleConnected
```
Expected: 0. Coverage (reads ∪ join-sides == the parse read-set,
per scope) runs store-side in the census — the parse read-set is
not itself in the graph.
HISTORICAL: at ERA 3 the DISJOINT half goes VACUOUS (`reads` is
gone — one mechanism left) and the two invariants collapse into
ONE COVERING check; see the ERA 3 gate's uniform walk below.

**GATE RESULTS 2026-09-11 (Sunny's refresh; the battery run live
against the served graph):** M1+M2+M3 censuses GREEN (5930 nodes
/ 8 labels · 6303 edges / 7 types, battery sum == unfiltered
total) · per-kind census exact · join-rooted 95 · degenerate 25 ·
joinType 39/56 · All_LDAs spot GREEN · DRIFT GREEN (2 findings +
absence proofs). ROLES GREEN 2026-09-11 08:07 (Sunny mapped the role
property on both resolves_to mappings + refresh): subject 119 ·
comparand 44 · lower_bound 1 · upper_bound 1 — THE SHEET IS 100%.

### M3 gate — THE CONDITION LAYER [BUILT 2026-09-10,
store-verified; numbers MEASURED; your GQL on the dev estate
closes it. NOTE: the tree out-counts the twin — 1141 conditions,
not the authored 748 (IS NOT NULL parses as a NOT+NULL_CHECK
pair, etc.); same verdict as joins 95 vs 93]

Load: upload the new parquets (graph_condition, graph_param,
graph_has_part_joinCondition / scopeCondition /
conditionCondition, graph_resolves_to_conditionColumn /
conditionParam, graph_uses_param_scopeParam) → Load to Tables
(dbo) → graph model: add node `condition` (key nodeId; name,
description, kind, degenerate, fragment) + node `param` (key
nodeId; name, description) → add edges: has_part join→condition ·
scope→condition · condition→condition · resolves_to
condition→column + condition→param (property role) · uses_param
scope→param → Save → ONE refresh.

The full census:

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: db 1 · db_schema 3 · table 90 · column 4554 ·
scope 44 · join 95 · condition **1141** · param **2** — total 5930.

The edge battery (one count per type, then the total):
has_part → **5883** · joins_to → 65 · left_side → 95 ·
right_side → 87 · reads → 6 · resolves_to → **165** ·
uses_param → **2** (each via
`MATCH ()-[r:<type>]->() RETURN count(r) AS cnt`), then:

```gql
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```
→ **6303** — the seven counts sum to 6303, closing the census
with no undeclared type.

THE PER-KIND CENSUS (one label, kind as property — an unlisted
kind or moved count = failure):

```gql
MATCH (c:condition) RETURN c.kind AS kind, count(*) AS cnt GROUP BY kind
```
Expected: NULL_CHECK 333 · NOT 238 · COMPARE_EQ 220 · AND 191 ·
IN_LIST 47 · COMPARE_LTE 33 · COMPARE_LT 24 · RANGE 22 · OR 12 ·
COMPARE_GT 8 · EXISTS_SELECTION 7 · COMPARE_GTE 3 ·
COMPARE_NEQ 2 · IN_SELECTION 1.

Conservation by parent (95 join-rooted + 229 scope-rooted + 817
nested == 1141):

```gql
MATCH (j:join)-[:has_part]->(c:condition) RETURN count(c) AS cnt
```
Expected: 95.

Role-tagged resolution (subject 119 · comparand 44 · lower_bound
1 · upper_bound 1) — REQUIRES the `role` COLUMN mapped as a
property on BOTH resolves_to mappings (found live 2026-09-11:
unmapped property → "Property 'role' does not exist"); after
mapping + refresh:

```gql
MATCH (c:condition)-[r:resolves_to]->() RETURN r.role AS role, count(*) AS cnt GROUP BY role
```

Degenerate census — `MATCH (c:condition) WHERE c.degenerate =
'true' RETURN count(c) AS cnt` → 25.

joinType — the M2 deferral CLOSED (the tree held it all along):

```gql
MATCH (j:join) RETURN j.joinType AS jt, count(*) AS cnt GROUP BY jt
```
Expected: Inner 39 · LeftOuter 56.

The spot check (the All_LDAs conversation made real — note the
HOP RANGE: the RANGE condition nests under the AND root, so
direct has_part returns nothing):

```gql
MATCH (s:scope)-[:has_part]->{1,4}(c:condition)
FILTER s.name = 'All_LDAs' AND c.kind = 'RANGE'
RETURN c.description AS descr
```
Expected: the ED-stay window voiced through dictionary words —
"…is between the adt arrival time and the ed departure time
(inclusive)."

### ERA 3 gate — THE FROM-STRUCTURE FAMILY [BUILT 2026-09-14,
registries 1.43.0, a1 as the ruled default; rides Sunny's next
load per the batch law. TWO ACTS AT ONE CAPACITY WINDOW, PROBE
FIRST: the probe runs against the CURRENT served graph (the
5930-node M3 shape, BEFORE any reload) and settles a1/a2; the
load fires only after a1 confirms. Every expected number below
is verified against the export truth 2026-09-15.]

**Act 1 — the probe rerun (3 spends, pre-reload).** The
2026-09-14 attempt returned 429 CapacityLimitExceeded on all
three before touching the question. Right after a capacity
resume expect CapacityNotActive for ~a minute — wait and re-ask
(FABRIC_GRAPH_LOAD.md).

Probe 1, sanity single-label:

```gql
MATCH (j:join) RETURN count(j) AS cnt
```
→ 95.

Probe 2, edge alternation:

```gql
MATCH (j:join)-[r:left_side|right_side]->(t:table) RETURN count(r) AS cnt
```
→ **88**. DIALECT FINDING (Sunny's run, 2026-09-15): the
Cypher-style spelling `|:right_side` is a SYNTAX error
(42000/22000, offending token the second ':') — Fabric GQL
takes ISO alternation, ONE colon: `[r:left_side|right_side]`.
A syntax error is NOT the refusal the contingency names — only
a "not supported" rejection of the corrected form counts.

Probe 3, unlabeled middle node:

```gql
MATCH (s:scope)-[:has_part]->()-[:left_side]->(t:table) RETURN count(*) AS cnt
```
→ **51**.

DECISION RULE (the recorded contingency, Design_Graph_Engine
ERA 3): a pass = the stated count. If EITHER probe 2 or probe 3
passes, **a1 stands** — proceed to Act 2. Only if the engine
REFUSES BOTH (a "not supported" rejection, not a number) does
the **a2 contingency fire**: STOP, no load — the merged
table-reference label rebuilds first (M2 reseals) and this gate
sheet re-bases again. A wrong COUNT from a supported query is
neither: that is a drift finding, investigate before loading.

**PROBE GREEN — Sunny's run, 2026-09-15: 95 / 88 / 51, all
three exact. BOTH capabilities exist (alternation in ISO
spelling AND the unlabeled middle) — a1 CONFIRMED, the a2
contingency is DEAD. Act 2 unlocked.**

**GATE RESULTS 2026-09-15 (Sunny's load + battery, ALL GREEN):**
the 1.43.0 load landed (5 parquets incl. the records-records
re-voiced texts, graph_reads_scopeTable dropped, direct_read
node + 2 mappings added, ONE refresh) · node census 5936 exact
with direct_read 6 and no reads label · edge battery six types
sum 6309 · uniform walk 94 · read-set 59 rows (6 direct + 53
join-covered) · direct_read spot check 6/6. ERA 3 IS CLOSED —
the served graph and the local walk answer the reads question
identically through one shape.

**Act 2 — the 1.43.0 load (a1 confirmed; ONE refresh).**
Lakehouse half FIRST, model second; drop-and-reload, never
load-into-existing. The changed set:

- NEW parquets (already in graph_export/): `graph_direct_read` ·
  `graph_has_part_scopeDirectRead` ·
  `graph_left_side_directReadTable` → upload to Files, Load to
  Tables into `Tables/dbo/`.
- RETIRED: `graph_reads_scopeTable` — DROP the dbo table AND
  remove the `reads` edge mapping from the graph model.
- Model deltas: add node `direct_read` (key nodeId; name,
  description) · add has_part mapping scope→direct_read
  (graph_has_part_scopeDirectRead) · add left_side mapping
  direct_read→table (graph_left_side_directReadTable) → Save →
  the load (the one spend). Proof a load fired: a new Graph
  model row in Monitor, Succeeded — never the editor's buttons.

**Act 3 — the re-based gate.**

The node census:

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
Expected exactly: db 1 · db_schema 3 · table 90 · column 4554 ·
scope 44 · join 95 · direct_read **6** · condition 1141 ·
param 2 — total **5936**, nothing else (and NO reads-shaped
label).

The edge battery (one count per type via
`MATCH ()-[r:<type>]->() RETURN count(r) AS cnt`):
has_part → **5889** · joins_to → 65 · left_side → **101** ·
right_side → 87 · resolves_to → 165 · uses_param → 2 · `reads`
→ GONE (unmapped type — its 6 edges retired into the 6
direct_read nodes). Then:

```gql
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```
→ **6309** — the six counts sum to 6309, closing the census
with no undeclared type.

THE ONE INVARIANT (COVERING alone — DISJOINT vacuous, one
mechanism left). The uniform walk, every FROM shape through the
same two hops:

```gql
MATCH (s:scope)-[:has_part]->()-[r:left_side|right_side]->(t:table)
RETURN count(r) AS cnt
```
→ **94** (51 join-left + 37 join-right + 6 direct). Then the
read-set itself:

```gql
MATCH (s:scope)-[:has_part]->()-[:left_side|right_side]->(t:table)
RETURN DISTINCT s.name AS scopeName, t.name AS tableName ORDER BY scopeName, tableName
```
→ **59 rows** — the acceptance gate: same rows as the local
walk (6 direct + 53 join-covered == read-set 59). If probe 2
was the refused one (a1 via unlabeled-middle only), split each
query into a `left_side` and a `right_side` statement (counts
57 + 37; distinct-union the pair lists by hand).

The spot check:

```gql
MATCH (d:direct_read) RETURN d.name AS readName, d.description AS descr ORDER BY readName
```
→ 6 rows; read#1 (scope #Final) reads
"Reads NON_SEVERE_SEPSIS_STAGING."

### M4 gate — derived_column [CLOSED ON THE SERVED GRAPH —
### Sunny's hand, 2026-09-16: load + ONE refresh + the full
### battery below, "all passed" (a pass = the stated count, by
### this sheet's own law: node census 6092 · edge battery summing
### 6562 · by-derivation 154/2 · the spot check). BUILT same day,
### store-verified; cites RE-BASED 100→97 at build (store grain:
### three twin-path heads collapse into named scopes — the
### joins-93→95 precedent)]

| expect | value |
|---|---|
| new nodes | derived_column 156 (154 operation + 2 named_literal; 312 passthrough projections and 5 anonymous EXISTS-SELECTs are NOT nodes — counted at build, never minted) |
| new edges | has_part +156 (scope→derived_column, ::dcol# grain) · cites 97 (scope→column at STORE grain) |
| descriptions | 156/156 R12-voiced (Grammar v2.10.0, THE FUNCTION-VOICING LIBRARY), stored == recomputed (verbatim law) |
| special check | case_when conditions STAY parented to scope/condition (condition census 1141 unchanged; no condition under a derived_column) — the stay-flat ruling |
| remainder | function_remainders {} — every practiced operation has its library row |

The node census (full, both directions):

```gql
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```
→ db 1 · db_schema 3 · table 90 · column 4554 · scope 44 ·
join 95 · direct_read 6 · condition 1141 · param 2 ·
derived_column **156** — total **6092**, nothing else.

The edge battery (one count per type, then the closing total):

```gql
MATCH ()-[r:has_part]->() RETURN count(r) AS cnt
```
→ **6045** (5889 + 156)
```gql
MATCH ()-[r:cites]->() RETURN count(r) AS cnt
```
→ **97**
(joins_to 65 · left_side 101 · right_side 87 · resolves_to 165 ·
uses_param 2 — unchanged), then:
```gql
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```
→ **6562** — the eight counts sum exactly, closing the census.

The by-derivation split:

```gql
MATCH (d:derived_column) RETURN d.derivation AS kind, count(*) AS cnt GROUP BY kind
```
→ operation **154** · named_literal **2**.

The spot check (the AGE_IN_DAYS walkthrough made real):

```gql
MATCH (s:scope)-[:has_part]->(d:derived_column) WHERE d.name = 'AGE_IN_DAYS' RETURN d.description AS descr
```
→ the STORED text, verbatim (measured 2026-09-16): "Age in days:
the number of days between the patient's birth date and the date
and time when, rounded down to a whole number." — the dangling
"the date and time when" is ADT_ARRIVAL_TIME's UNBLESSED
dictionary noun phrase (the known R5 vendor-words class, pinned
at M3's build too); blessing that column re-voices it as "the
arrival time" everywhere, per the R5.b delta-by-name law — a
steward act, never a code fix.

**The load (Sunny's hand, batch law — ONE refresh):**

- NEW parquets (already in graph_export/): `graph_derived_column`
  · `graph_has_part_scopeDerivedColumn` · `graph_cites_scopeColumn`
  — every one of the 26 pre-existing parquets is BYTE-IDENTICAL
  (checksummed at export regen; structure and texts never moved).
- Upload the 3 new files → Load to Tables (new tables only).
- Model deltas: add node `derived_column` (key nodeId; name,
  description, derivation, operation, position, fragment) ·
  add has_part mapping scope→derived_column
  (graph_has_part_scopeDerivedColumn) · add edge `cites` with
  mapping scope→column (graph_cites_scopeColumn) → Save →
  item-level Refresh now (ONE).
- Run the gate queries above (answer key: expected_m_gates.json,
  re-based 1.45.0).

### M5 gate — statement (+ the M3 holdovers) [BUILT + LOADED +
### GATED GREEN 2026-09-17 — Sunny's load ("loaded."), the six
### queries Q1–Q6 run on the served graph, his verdict verbatim:
### "ALL GOOD" — statement 67 · 36/31 · 6167/6618 · the two IF
### sentences byte-identical served; the visual republished to
### the standing URL (M1–M5), FS1 counts test green first]

| expect | value |
|---|---|
| new nodes | statement 67 (operational subkind 31, voiced never) · condition +6 (the IF predicates: total→1147, the measured M3 re-base 1141 + 6) · param +2 (@StartDate @EndDate: total→4) |
| new edges | has_part +50 (statement→scope 44 · statement→condition 2 · condition→condition 4) · resolves_to +4 (→param; total resolves_to 169) · uses_param +2 (statement→param; total 4) |
| descriptions | **36 R11-rendered non-empty + 31 EMPTY-BY-RULE (the (b) ruling, Sunny "b" 2026-09-17: operational statements store NOTHING — a fixed phrase would restate the kind field); the split is the check, corrected from the pre-ruling 67/67 draft** |
| counted debt | 31 operational statements have NO downward edge — DECLARED Connection_Ledger counted-missing, landing step named M6 (file→statement). Not silent, not a failure: a counted row |
| census after | nodes 6167 (statement 67) · edges 6618 (has_part 6095 · resolves_to 169 · uses_param 4) — census_after.M5 in the key |

**The M5 gate queries (paste one at a time; the expected value
follows each):**

Q1 — the full node census (every label counted, exact):

```
MATCH (n) RETURN labels(n) AS nodeType, count(*) AS cnt GROUP BY nodeType
```

→ statement 67 · condition 1147 · param 4 · scope 44 · join 95 ·
direct_read 6 · derived_column 156 · table 90 · column 4554 ·
db_schema 3 · db 1 (+ file/meaning_twin per the standing census);
the ladder labels sum to 6167.

Q2 — the edge battery (run per type):

```
MATCH ()-[r:has_part]->() RETURN count(r) AS cnt
```

→ 6095. Then `uses_param` → 4 · `resolves_to` → 169; the total:

```
MATCH ()-[r]->() RETURN count(r) AS totalEdges
```

→ 6618.

Q3 — the subkind split (the (b) ruling as a served query):

```
MATCH (s:statement) RETURN s.subkind AS subkind, count(*) AS cnt GROUP BY subkind
```

→ operational 31; the rest (empty subkind) 36.

Q4 — the description split (36 speak, 31 empty BY RULE):

```
MATCH (s:statement) WHERE s.description <> '' RETURN count(s) AS voiced
```

→ 36.

Q5 — the birth edges point down (statement→scope):

```
MATCH (s:statement)-[:has_part]->(sc:scope) RETURN count(*) AS cnt
```

→ 44.

Q6 — the spot check (the served graph SPEAKS the stored R11 text):

```
MATCH (s:statement) WHERE s.does = 'IF' RETURN s.name AS step, s.description AS descr
```

→ exactly two rows: "A decision step, taken when the start date
parameter is not recorded or the start date parameter is ''."
and the end-date twin — byte-identical to the ratified 36.

**M5 load steps (Sunny's hand, after the build commit):**

1. Copy the changed graph_export parquets to the lakehouse: 5
   updated (graph_table — pkColumns arrives, the F2 fix ·
   graph_condition · graph_param ·
   graph_has_part_conditionCondition ·
   graph_resolves_to_conditionParam) + 4 NEW (graph_statement ·
   graph_has_part_statementScope ·
   graph_has_part_statementCondition ·
   graph_uses_param_statementParam). Everything else is
   byte-identical — including graph_column (no values data in
   this estate; the F4 dict fix is live but writes nothing here).
2. In the Fabric graph model: add node `statement`
   (graph_statement, key nodeId) · add has_part mappings
   statement→scope (graph_has_part_statementScope) and
   statement→condition (graph_has_part_statementCondition) ·
   add uses_param mapping statement→param
   (graph_uses_param_statementParam) → Save → item-level
   Refresh now (ONE — the capacity law).
3. Run the gate queries (answer key: expected_m_gates.json,
   basis 1.46.0). Good looks like: statement 67 · the 36/31
   description split · node total 6167 · edge total 6618.
4. Republish the graph visual (devtools/graph_visual/
   generate_m1.py — the FS1 counts test is GREEN first, the
   standing rule).

### M6 gate — file

| expect | value |
|---|---|
| new nodes | file 1, aboutness STORED + meaning-key anchored |
| new edges | has_part +71 (file→statement 67 · file→param 4); NO file—reads→table rollup (0) |
| debt closed | the 31 counted-missing statements birth-edge via file→statement; the Connection_Ledger row retires |
| composition | the file description contains its children's words (the summing law) |
| walk | file-[:has_part*]->scope-[:reads]->table is complete: every one of the 90-table dictionary's tables the proc touches is reachable |

### M7 gate — governance + consumption

| expect | value |
|---|---|
| new nodes | pbi_report 1 · description 1 · agent 1 · role 1 · responsibility 1 (person/term/usage 0 until acts) |
| new edges | executes 1 (dashboard→USP_ED_SEPSIS) · describes 1 |
| counted gap | executes names reports/USP_RPTS_ED_Sepsis.sql — absent from this estate BY DESIGN, must appear as a counted gap, never silently dropped |
| ledger | Shape_Ledger TARGET rows == 0; shape census Q1/Q2/Q3 green both directions |
| phase boundary | full sepsis estate re-run against its own key |

## Per-batch refresh (M2 and on)

1. Pull the branch; re-run the export command (step 2) with
   estate `ed_sepsis_dev`.
2. Upload the new/changed parquet over the old ones (Files →
   overwrite), **Load to Tables** again for changed tables.
3. New tables (new node kinds) → extend the graph model: new node
   type + its contains mapping, per that batch's runbook note.
4. Run that batch's gate queries above (answer key:
   expected_m_gates.json).
