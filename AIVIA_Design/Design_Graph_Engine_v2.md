# Design — Graph Engine v2 (THE ONE GRAPH)

**STATUS: DRAFT for Sunny's ratification (2026-09-10).** Derived
from the first-principles brainstorm of 2026-09-10. On
ratification this content REPLACES `Design_Graph_Engine.md` and
this file is renamed over it (the v2 filename is transitional by
design and dies at ratification — the naming law's status-in-
header rule resumes).

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
  derived_column`
- consumption: `pbi_report`
- governance: `description · term · usage · disposition ·
  proposal · acronym · person · agent · role` (+ `drift`)

**Every node row carries:** name · **description** (its English)
· descriptionStatus / curation state · provenance columns ·
contentKey (meaning identity — the drift anchor) · label-specific
properties.

**Edge vocabulary:** containment `has_part` (db→db_schema→table→
column; file→statement→scope→condition/param); `reads`
(scope→table, true grain); `joins_to` (table→table, DECLARED —
dictionary truth, with key columns); `resolves_to`
(condition→column — OBSERVED logic; the declared-vs-observed diff
is a pure GQL query and IS the documentation-drift product
story); `cites` (scope→column outputs); `uses_param`;
consumption `executes`; governance `describes / performed_by /
approved_by / used_by / supersedes / assigns`. Clause provenance
(`where` vs `join_on`) is a property on condition nodes — clause
containers are syntax, not meaning, and are not nodes.

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

---

## The laws carried forward from v1 (storage-independent, all kept)

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
