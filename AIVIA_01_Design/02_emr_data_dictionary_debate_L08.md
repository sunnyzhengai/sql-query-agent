The DATE_DIMENSION Debate (2026-09-28, ruled into L08)

THE FINDING THAT STARTED IT
A connectivity check of the phase 02 graph (38 table nodes, edges from
the join sheet, both endpoints in scope) found 2 components: 37 tables
connected, DATE_DIMENSION alone. Yet COOK_RPT_usp_SF_CensusDashboard
joins it in its actual SQL:
    CONVERT(DATE, V_REPORT_RUN_FACT.RUN_DTTM) = DATE_DIMENSION.CALENDAR_DT
A sweep of all join predicates in 02_sql_extraction.json against the FK
sheet found exactly ONE table-pair the SQL joins that the dictionary
lacks — this one. The dictionary is not wrong: DATE_DIMENSION is a
conformed date dimension (Kimball); its joins are a modeling convention,
not foreign keys, so Epic records no FK into it. Isolation is the
dictionary being honest.

THE QUESTION
How does a graph represent a dimension that joins ANY date column —
and where does that representation live, phase 02 or phase 03?

POSITIONS CONSIDERED
1. Materialize an edge to every date column (196 DATETIME columns in
   the corpus -> 181 edges beyond DATE_DIMENSION's own).
   Rejected as a stored fact: storage is NOT the concern (181 rows is
   nothing) — DRIFT is. Edges generated once go stale silently when new
   DATETIME columns enter the corpus; no stored fact is violated, the
   user just gets a false "no path" one day. Also provenance: 181
   minted edges are not 181 facts, they are ONE rule applied 181 times,
   and minting them into the join sheet would blur what the EMR
   asserted vs what we assumed.
2. Do nothing in phase 02, defer to phase 03 with observed_join.
   Rejected: the rule needs no SQL evidence — it derives from the
   column sheet's data types plus one ruled fact about the dimension's
   grain. Technical-layer knowledge, same nature as the ruled CLARITY_*
   category list. Deferral would make every time-phrased question
   (month, quarter, fiscal year — the census dashboards' native
   vocabulary) a reported gap through all of phase 02.
3. RULED: the rule as data, edges as its regenerable output.
   One ruled row: DATE_DIMENSION.CALENDAR_DT, day grain, joins any
   DATETIME column through a date conversion. The builder re-derives
   the edges at every build (every sql-file add/change). The join sheet
   stays verbatim EMR truth. New DATETIME columns get edges
   automatically; retiring the rule retires all its edges together.
   Drift impossible by construction.

THE GQL WORRY AND ITS RESOLUTION
Worry: GQL only traverses physical edges — a rule is invisible to it.
Resolution: the rule is how edges are AUTHORED, not a substitute for
them. Locally the builder derives them into the in-memory adjacency at
load; in Fabric the same builder writes them as rows into the graph
model's edge table (already a derived artifact, distinct from the
dictionary sheets). GQL hops normally either way. One derivation, two
runtimes.

THE MEMORY WORRY AND ITS RESOLUTION
Worry: don't want anything in memory; vectorize the question, match
nodes, generate GQL at runtime instead.
Resolution: that flow is the correct Fabric production design, but it
relocates memory rather than removing it — Fabric Graph traverses an
in-memory snapshot of the edge tables, the vector index holds the
embeddings. The real choice is who OWNS the memory: our Python locally
(38 tables — kilobytes), Microsoft's engines in production. Adjacency
is never the scaling wall (full Clarity ~18k tables would cost ~half a
GB); EMBEDDINGS are (266 MB for 1,618 columns today). And the
"algorithm that covers the matched nodes" is our code in both worlds:
GQL has shortest-path queries but no minimal-connecting-subgraph
statement, so our generator loops anchor pairs and unions the paths.
Same anchors in, same subgraph out — which is why local phase 02
testing transfers: Fabric later swaps only the executor.

THE DECIDING CRITERION (Sunny's)
Phase placement depends on whether EMR-asserted edges and derived edges
must be differentiated. They must — for answer trust, for integrity
re-derivation, and because phase 03's observed edges arrive as a third
authority. Named by provenance (standard terms asserted/inferred):
    joins_by_fk    — asserted by the EMR dictionary (traces by join_id)
    joins_by_rule  — inferred from a ruled rule row
    joins_observed — evidenced by the sql files' joins; phase 03 only
Once the kind field is the wall, our inference cannot pollute EMR
truth — which is exactly what made phase 02 placement safe. RULED:
DATE_DIMENSION lives in phase 02.

STANDING CONSEQUENCES
- Connectivity invariant: one component, or every extra component named
  with a reason. With joins_by_rule built, 38/38 connect.
- Every answer names the edge kind it walked.
- Per-kind edge counts reported at every build.
- Scaling note for the Fabric design: vector search for embeddings,
  never a full-table cosine loop; the graph itself fits engine memory
  at any realistic dictionary size.

One accuracy note: the "~half a GB for full Clarity" figure is my order-of-magnitude arithmetic (assuming a few million FK rows at ~100 bytes per adjacency entry), not a measured number — kept in the record as an estimate, which is how I'd want you to read it.
