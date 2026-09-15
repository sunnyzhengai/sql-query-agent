# Design — Graph Engine (THE ONE GRAPH)

**STATUS: RATIFIED by Sunny 2026-09-10.** Derived from the
first-principles brainstorm of 2026-09-10; drafted as
`Design_Graph_Engine_v2.md` and renamed over the prior
`Design_Graph_Engine.md` at ratification (the prior content
stands in git history as the ratified record it was). The build
ladder implementing this design: Manifest_Build §E6.

---

## The four principles (Sunny, 2026-09-10 — the mission restated)

1. Answer users' natural-language questions about a hospital's
   knowledge.
2. The hospital's knowledge is hidden in SQL.
3. Extract that knowledge and give it English meanings.
4. A question's intent searches the knowledge base, reaches the
   SQL, and grounds the answer.

## The verdict that makes this v2 (ruled 2026-09-10)

The v1 engine held one truth in six forms: raw SQL, AST blob,
twin blob, the in-memory boot store, the search index, and the
Fabric export. Every major corpse of 2026-09-09/10 — the blob
corpse, the dual-namespace corpse, export-mirror drift, boot
races — was an artifact of that layering. v2 has ONE home of
meaning: **the graph**. Everything else either feeds it
(evidence) or derives from it (projections).

**THE TWIN DISSOLVES.** Its condition fact becomes the condition
node row; its content_key becomes a column (the drift anchor);
its points_at becomes a provenance column; its voicings become
the description ladder; its census becomes the run ledger. Sunny's
original mind image — every grain a node with its description,
edges between them — is the architecture.

---

## L0 — Evidence (what the sources SAID)

Append-only Delta tables in an `evidence` schema of the
customer's lakehouse. One table per source contract; every row
hashed and as-of stamped. **Nothing is read without storing;
nothing is ever edited** — upstream change = a new snapshot row,
old rows stand forever (provenance stability, diffs,
reproducibility, audit).

| source | upstream form | landing |
|---|---|---|
| SQL logic | lives in the DB (`sys.sql_modules`) or a repo where one exists | one row per object per captured version: objectId, schema, name, **definitionText verbatim**, contentHash, sourceModifyDate, capturedAt |
| dictionaries | vendor documentation (Epic Clarity docs), INFORMATION_SCHEMA + extended properties, glossaries | ONE normalized tabular contract: tables, columns, keys, declared joins, value sets — descriptions included (vendor/human-authored text, trusted as-is) |
| report definitions | BI service artifacts (TMDL/XMLA, layout JSON; SSRS RDL) — extractable far more often than assumed | definition text rows, same discipline |

Cadence: scheduled + change-triggered pulls, hash-gated — an
unchanged object produces nothing. L0 contains **zero
interpretation**: no facts, no edges, ever.

Mappings that cannot be extracted may later be *inferred* (usage
logs, naming) — those enter the graph flagged `inferred` vs
`declared`: a queryable confidence class, never a silent guess.

## L1 — Extraction (what the parser SAW + the gated sentence)

**Input: L0 rows only. Never live sources.** Two workers, hard
wall between them:

- **The parser** (deterministic, the dialect's native parser —
  no fallback, ADR 0001 law carried forward) does ALL structural
  interpretation. Its output persists: **`derived.parse_records`**
  — one row per (contentHash, parserVersion), the complete
  structural record (the AST) as a JSON text column. Persisted
  for provenance-address stability and cost; it is DERIVED
  EVIDENCE — rebuildable by definition, hash-locked to its input.
  Parser upgrade = new parserVersion; old records stand.
- **The LLM** contributes prose compression ONLY (see the English
  ladder) — drafted FROM the deterministic anatomy, never
  independent of contents. Its output persists:
  **`derived.english_drafts`** — (meaningKey, model,
  promptVersion, text, status drafted→approved/rejected,
  approver, timestamps). Not rebuildable; the governance
  workbench lives here; approved text lands on graph nodes.
  Drafts anchor to meaning keys, so upstream change visibly
  orphans them.

**Structural facts get NO L1 store** — they flow straight to
graph rows carrying provenance columns (evidenceRowId,
parseRecordId, parsePath, contentHash). Zero copies.

Plus **`derived.derivation_runs`**: run stamps, input versions,
parser/prompt versions, conservation counts (parsed / skipped /
failed — all counted, nothing silent).

**Dictionaries skip L1 storage entirely** — mechanical integrity
checks in flight (bad rows refused + counted), then straight to
graph citizens.

**THE HASH CHAIN** (unbroken end to end): evidence contentHash →
parse record (hash, parserVersion) → meaning keys → graph
provenance → approved English anchored to keys. Change anywhere
upstream cascades visibly, never silently.

## L2 — THE GRAPH (what it MEANS — the single source of truth)

A REAL graph database: **nodes and edges as Delta table rows**
(properties as columns), served by Fabric Graph. The same rows
are GQL-traversable, SQL-auditable, lakehouse-versioned. JSON
lives only at L0/L1 — never here.

**Node vocabulary** (the Shape_Ledger carries forward as the
ruled census target; GQL-reserved words never used as names —
the vendored-list gate stands):

- technical: `db · db_schema · table · column`
- logic: `file · statement · scope · condition · param ·
  derived_column · join · direct_read` (join ADDED 2026-09-10,
  Sunny's hand-drawn ruling; label gate-checked — JOIN is
  SQL-reserved, not ISO-GQL-reserved; direct_read ADDED at ERA 3,
  ratified 2026-09-14 — the single-table FROM's sided node, see
  the era-3 section)

Labels are GRAINS, never kinds (clarified 2026-09-10, answering
Sunny's per-predicate question; the kind-vs-label standard):
`condition` is ONE label for every predicate — leaf (COMPARE_*,
RANGE, IN_*, NULL_CHECK, EXISTS_* …) and composite (AND/OR/NOT,
nested via has_part) — with the predicate kind as a PROPERTY from
the registry's closed library. Per-predicate structure lives in
ROLE-tagged `resolves_to` edges (subject · comparand ·
lower_bound · upper_bound · pattern · escape · selection ·
quantifier — the ratified role vocabulary); role-completeness per
kind is GV-B's rule table. A new predicate kind is a registry
row, never a new label.
- consumption: `pbi_report`
- governance: `description · term · usage · disposition ·
  proposal · acronym · person · agent · role` (+ `drift`)

**Every node row carries:** name · **description** (its English)
· descriptionStatus / curation state · provenance columns ·
contentKey (meaning identity — the drift anchor) · label-specific
properties.

**Edge vocabulary** (AMENDED 2026-09-10 — THE JOIN-NODE RULING,
Sunny's hand-drawn graph): containment `has_part` (db→db_schema→
table→column; file→statement→scope→condition/param/join;
join→condition — the ON predicate's home); `reads` (scope→table —
THE REMAINDER RULE, Sunny's M2-redesign ruling 2026-09-10: a
scope's tables are reached THROUGH ITS JOIN NODES; a direct reads
edge exists ONLY for a table no join side covers — the
one-table-no-join scope, and single-table subqueries attaching to
their named ancestor per A4. The read-set is DERIVED: reads ∪
join sides. Measured on USP_ED_SEPSIS: 47 of ~50 scope→table
connections travel through joins; ~6 reads survive. **RETIRED
AT ERA 3 (ratified 2026-09-14, see the era-3 section): the
remainder now travels scope—has_part→direct_read—left_side→
table — one sided mechanism for every FROM clause; the one
invariant: per scope, side-targets == read-set. The reads NAME
survives as the question relation only**); `joins_to` (table→table, DECLARED — dictionary
truth, with key columns; NEVER written by observation — the
observed side lives on join nodes, so the declared edge's
integrity is preserved: one edge name, one authority);
`left_side` / `right_side` (join→table-or-scope — the OBSERVED
pair. Names ruled 2026-09-10: bare LEFT/RIGHT are ISO-GQL
reserved, gate-checked. PAIR SEMANTICS ruled same day: the two
targets are the tables the ON condition's columns RESOLVE to —
the same grain as declared joins_to — with side assignment
following the syntactic operand order so outer-join semantics
survive; an ON touching 3+ tables is a counted case; a side may
be a SCOPE — a CTE/#temp join, same target set as table_ref
resolution); `resolves_to` (condition→column — OBSERVED logic);
the declared-vs-observed diff is now DIRECT and pure GQL: every
join node's (left_side, right_side) table pair carries a declared
`joins_to` or is a compliance finding — the documentation-drift
product story (scope-sided joins excluded by construction);
`cites` (scope→column outputs); `uses_param`; consumption
`executes`; governance `describes / performed_by / approved_by /
used_by / supersedes / assigns`. Clause provenance as a STORED
PROPERTY RETIRES (superseded 2026-09-10): parentage carries it —
a condition under a join IS a join condition, under the scope a
where condition; derivable is never stored. Clause CONTAINERS
(WHERE, FROM as syntax boxes) remain non-nodes; the join is not a
container — it is relational meaning: which pair combines, how
(`joinType` property: inner | left_outer | right_outer |
full_outer | cross), and by what predicate. THE COVERAGE INVARIANTS
(SUPERSEDING the earlier side-reads invariant — Sunny's
M2-redesign ruling, same day: reads is the REMAINDER, never the
union): per scope, (1) DISJOINT — no table is connected both by
a reads edge and a join side; (2) COVERING — reads ∪ join sides
== the parse's read-set, so no table a scope touches is silently
unconnected. Both are standing census lines from the join batch
on; divergence is a builder bug.

**THE ENGLISH LADDER (amended by Sunny's readability challenge,
2026-09-10):** every node ALWAYS keeps its deterministic render —
the factual anatomy (audit, evidence, verbatim-checkable). The
DESCRIPTION is: the render itself where composition is small
(conditions, small scopes); an **LLM compression of the render**
where composition is large (big scopes, procs, reports) — gated
drafted→approved, attributed. Checkable law: a compressed
description may only contain concepts present in its anatomy —
hallucination detectable by comparison; the reviewer's question
is mechanical.

Sources of English, by grain: vendor documentation (table,
column — trusted as-is) → grammar renders composed upward from
those words (condition, scope leads — deterministic) → LLM
compression at the top (proc, report aboutness — gated). Reports
DERIVE their description from their executed procs (Sunny's
derivation ruling: "the report users SHOULD see the logic").

**Rebuild law:** the graph regenerates from evidence + parse
records at any time; human approvals anchor to contentKeys and
therefore SURVIVE unchanged meanings and VISIBLY ORPHAN changed
ones (drift detection is the anchoring rule, not a subsystem).

## L3 — Projections (derived, never authoritative)

One embedding per node description, stored as a **vector column
on the node's own row** — recomputed when the description changes
(hash-gated), never re-embedded otherwise. ONE ANN index over the
column, label-filterable: every grain findable by meaning because
every grain HAS a meaning. Projections rebuild from the graph;
never the reverse. Any lexical index follows the same law.

## L4 — The answering loop

TABLED (Sunny, 2026-09-10) pending the engine graph. The ratified
chatbot design (`Design_Chatbot.md` — THE SEARCH IS THE ANSWER,
the nine laws, the seats and cages) remains the governing design
for this layer and re-derives its index from L3 at convergence.

**THE MEANING-TEST CONSOLE (ruled by Sunny 2026-09-11):** each
ACCEPTED ladder batch earns a conversational test surface — the
ask console booted over the store as-built, which scopes it to
exactly the accepted grains by construction. Its purpose is the
check the GQL gates cannot make: MEANING QUALITY — are the
descriptions readable, does NL search find the right node, does
traversal ground the answer. The division is law: GATES verify
STRUCTURE (deterministic, exact, they close batches); the console
tests MEANING (probabilistic, human-judged, it closes nothing).
Scope clarified same day: the standing ban is the FABRIC DATA
AGENT specifically — it fabricated answers — never
chatbot-testing as such. The first target is the TECHNICAL LAYER
(table/column names + dictionary descriptions — already index-
carded; embeddings cache-seeded across estates by content key);
later grains enter the index as §D resumes; L3 re-homes the
vectors onto node rows at M12. THE ALGORITHM is ruled in
Design_Chatbot.md §"THE MEANING-TEST CONSOLE" (Sunny's five
steps, 2026-09-11: LLM tokenizes only · vector match sets ·
deterministic planner writes a GRAPH query via one topology
algorithm · evidence returned with the query as artifact).

---

## The laws carried forward from v1 (storage-independent, all kept)

[registry stamps: kg1_technical v1.43.0 · kg2_logic v1.43.0 ·
kg2_kind_library v1.43.0 · kg3_artifacts v1.43.0 ·
kg4_concepts v1.43.0 · flows v1.43.0 · lenses v1.43.0]
(stamp block restored 2026-09-10 — the ratification rename dropped
v1's per-section stamps; RG-A2 caught it same day. One block here,
the same-breath rule mechanical again; registries carry their own
section provenance. 1.37.0 = the join-node ruling, landed in the
CONVERTER — registry JSONs are generated data, never hand-edited;
the determinism test enforces it and caught the first attempt.
1.40.0 = THE STRUCTURE-WORD CLAIM + THE RELATION-WORD SEAT,
Sunny's "fix these gaps" go 2026-09-12: prompt 3.1.0, _edge
self-speech rows, _self scope speaks "subquery" — prompts and
speech only, the twin's structure untouched. 1.41.0 = THE NAMER
SEAT, Sunny's "rule riders c and d" 2026-09-12: Seat_Prompts
gains the namer row 1.0.0 (Grammar_Floor §R5.b's proposer) —
one prompt row, the twin's structure untouched. 1.42.0 = THE
READS RELATION SPEAKS, Sunny's "fix all three gaps" go
2026-09-14: Speech_Sources gains the _edge reads row and the
v1.40.0 'reads'-card deferral closes — its recorded reason (a
'read' constraint would veto join-side travel) dissolved by the
READS COMPOUND in the console; one speech row, the twin's
structure untouched. The determinism test caught the hand-edit
attempt AGAIN this round — second catch of the class, the
converter-first law holds. 1.43.0 = ERA 3 THE FROM-STRUCTURE
FAMILY, Sunny's ratification 2026-09-14: direct_read joins the
ledger PRESENT, the reads edge RETIRES into it — the twin's
structure moves for the first time since M3; the answer key
re-based with the structural delta.)

Conservation (handled ⊎ counted == everything) · meaning-identity
anchoring (contentKeys → drift) · the voicing grammar (registry-
versioned) · the verbatim law (stored == recomputed) · the LLM
cage (structure never, prose only, gated) · the censuses incl.
the SHAPE CENSUS (store == Shape_Ledger, both directions, reading
THE STORE) · the literal law + mirror checks · the naming law +
GQL-reserved gate · the live-seat rule · the verification law
(mind images become standing queries; BUILT claims carry their
proving query) · batch-verify discipline (small batches, Sunny's
GQL gates, commit ids in the ledger) · capacity discipline (one
refresh per batch, Sunny's hand or word).

## Migration (convergence, not rewrite)

- **Phase 1 — finish the ladder (in flight):** M3–M7 complete the
  graph's layers exactly as this v2 specifies. Nothing already
  shipped is discarded.
- **Phase 2 — the primacy flip:** evidence and parse records
  re-home from snapshot files/blobs into their Delta tables; the
  boot store demotes to a BUILDER that writes the graph tables;
  tree/twin blobs retire (parse records inherit the AST's role;
  the twin's columns are already in the graph); the search index
  re-derives from graph rows (embeddings move onto nodes).
- **Phase 3 — the answering loop converges** (untabled by Sunny
  when ready): the chatbot's index becomes the L3 projection;
  scoring work (§D) resumes on top.

## Open items

- Connector scope v1 (agent jobs? SSIS? dbt? beyond modules)
- Landing contract details per source
- Fabric Graph vector capability specifics at implementation time
- The inferred-mapping confidence classes (vocabulary)

## ERA 3 — THE FROM-STRUCTURE NODE FAMILY (RATIFIED by Sunny
## 2026-09-14: "ratified — build era 3, a1 if the probe passes";
## BUILT same day, a1 as the ruled default — the probe stayed
## capacity-blocked, so the a2 relabel is the RECORDED
## CONTINGENCY: it fires only if the probe, at capacity resume,
## refuses BOTH unlabeled middle nodes and edge alternation)

**Origin.** Sunny's step-back on the reads inventory: "I wanted
all scopes to use the same joins node with left and right edges;
when there is only 1 table, the right edge is null or a keyword."
The ruled re-derivation keeps the goal and moves the absence: a
property graph has no null endpoints, and a one-sided node named
JOIN would claim a combining fact the parse never said — so the
absence lives in the KIND, never in a null.

**The shape.** One FROM-structure node family with two kinds:

- kind `join` — today's node, byte-for-byte: left_side +
  right_side, ON meaning, join type, ON-root conditions.
- kind `direct_read` — the single-table FROM: ONE side edge, no
  ON, no type. This is the null-right case expressed honestly:
  the kind that has no right edge. It twins a REAL parse node —
  ScriptDom's NamedTableReference — where a null-sided join
  would twin nothing (ADR 0001: the twin claims parse facts
  only).

Every FROM clause then walks the same two hops:
scope —has_part→ (node) —left_side/right_side→ table-or-scope.
The era-2 `reads` remainder edge RETIRES from the store: its 6
edges migrate into 6 direct_read nodes (+ has_part + left_side).
The two M2 invariants collapse into one: per scope,
side-targets == read-set (COVERING, with DISJOINT now vacuous —
there is no second mechanism left to overlap).

**Two sub-variants — the live-wire probe decides:**

- (a1) NEW LABEL beside the sealed batch: direct_read is its own
  node label; the 95 join nodes and every M2 census stand
  untouched. Uniform queries then need either an UNLABELED
  middle node — MATCH (a:scope)-[:has_part]->()-[:left_side]->
  (b:table) — or node-label alternation. GATED on the probe.
- (a2) ONE MERGED LABEL (the SQL standard's own name for the
  family is TABLE REFERENCE — a joined table IS a <table
  reference> in the grammar) with kind as a property. No
  alternation needed anywhere, but the 95 sealed join nodes
  relabel: M2 reseals. The heavier quantum; take it only if the
  engine refuses unlabeled nodes and alternation both.

PROBE RECORD (3 counted spends, Sunny's word, 2026-09-14): all
three probes — sanity single-label, edge alternation
[:left_side|:right_side], unlabeled middle node — returned
http 429 CapacityLimitExceeded (retriable) before touching the
question. RERUN AT CAPACITY RESUME, Sunny's hand; the variant
choice waits on it.
PROBE GREEN (Sunny's rerun, 2026-09-15): 95 / 88 / 51, all
three exact — **a1 CONFIRMED, the a2 contingency is DEAD**.
Dialect finding en route: Fabric GQL rejects Cypher's `|:type`
alternation at parse; ISO single-colon `[r:left_side|right_side]`
is the accepted form (recorded in GQL_Gates.md). Both uniform-
query mechanisms exist — alternation AND the unlabeled middle;
the a1 shape needs no relabel, ever. The served-graph load +
Act 3 gate remain the batch's close.

**Blast radius (declared, the a1 costing):** kg2 mapper births
direct_read at translate; store +6 nodes +12 edges −6 reads;
Shape_Ledger reads row flips RETIRED-INTO-direct_read (converter
first — the law this week's determinism catch re-proved);
export ships the new node/edge parquets and drops the reads
parquet; the M-gate answer key re-bases WITH structural delta
(+6/+12/−6, its first non-zero re-base — the recompute tests
are the check); gate sheet re-runs at the next served load; the
console adjacency swaps reads-edge links for the new walk and
THE READS COMPOUND simplifies (the owner-to-side legality rule
covers direct_read unchanged: enter has_part, exit side);
Ranking_Weights' stale "reads … table/scope" row retires in the
same registry breath. The floor grammar does NOT move: single-
source scopes already voice "Drawn from X records" without a
join — every stored text byte-identical is an acceptance gate.

**Acceptance gates (pre-code):** node census join 95 +
direct_read 6 · per-scope side-targets == read-set (the one
invariant) · all 1,185 stored voicings byte-identical · answer-
key recompute green at the re-base · the served-graph uniform
query returns the same rows as the local walk on the live wire
(one spend, Sunny's hand).

**What this does NOT rule:** the derived read_set edge (the
export shortcut) stays unbuilt unless separately ruled; the
question-word grounding (v1.42.0 THE READS COMPOUND) stands
under every variant — it simply gets simpler when the store
becomes uniform.

**The questions — answered at the build (2026-09-14):**
(1) a1 built (the ruled default; the probe rerun at capacity
resume either confirms it or fires the a2 contingency);
(2) the label is `direct_read` (the draft's word stood);
(3) it landed as its own act BEFORE M4, amending the M2 layer —
the answer key's M2 delta carries the amendment, the
ERA3_FROM_STRUCTURE entry carries the act, registries 1.43.0.
BUILT: inbound births direct_read at the join-layer
materialization (read_render: "Reads <table> records."); the
console walks it as connective structure (the owner-to-side
legality covers it unchanged); the export ships
graph_direct_read + has_part_scopeDirectRead +
left_side_directReadTable and RETIRES graph_reads_scopeTable;
enrich's worklist reads the same tables through the new shape.
LIVE CONFIRMATION at the export regen: exactly two stored
condition texts moved — #PatientLocation cond#3/#4 gaining the
R5.c owner-possessive ("The patient location history's
department is (not) recorded.") — the standing query verified
against the store. The served-graph GQL gate rides Sunny's next
load (batch law).
