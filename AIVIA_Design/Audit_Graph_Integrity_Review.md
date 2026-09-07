# Audit — Graph Integrity Review: the Connection Ledger draft

*(2026-09-07, executed per the ratified Audit_Graph_Integrity_Plan
§4. Read-only; verified against the LIVE sepsis store plus code
reads. One row per node kind, four answers, a verdict, and the
PROPOSED birth edge — every row awaits Sunny's ruling. Verdicts:
EDGED (walkable today) · UNWALKABLE (connection exists in data, the
adjacency is blind) · MISSING (the origin is not stored at all) ·
INDEX-ONLY (searchable entry, no graph presence) · ROOTED-CANDIDATE
(may legitimately be an origin) · MISSING-KIND (should exist,
doesn't).)*

## Corrections to the plan's assumptions (found by probing)

1. **file and scope ARE store nodes** (28 + 312, with adjacency
   edges) — not tree-borne pseudo-nodes as the plan assumed. The
   true pseudo-node population: derived columns (3,671 in the
   adjacency, no store nodes), drift names, conditions, parameters.
2. **term.about exists but holds junk**: `_append_version` auto-
   fills `about=[its own name]` — a self-reference, not an origin.
   The slot exists; nothing meaningful was ever put in it.
3. **Even KG1's own hierarchy is partially unwalkable**: db and
   schema nodes have NO adjacency edges — the db→schema→table
   containment chain is not in the connecting graph.

## The Connection Ledger (draft — rule per row)

| kind | n (live) | deduced from | in data? | walkable? | verdict | PROPOSED birth edge |
|---|---|---|---|---|---|---|
| db | 1 | the registration act | yes (`minted_from`) | NO | UNWALKABLE | db —registered_by→ registration/root; db —contains→ schema |
| schema | 3 | the source extract | implicit (identity) | NO | UNWALKABLE | schema —contains→ tables; db —contains→ schema |
| table | 90 | source extract (KG1 load) | implicit | yes (contains/reads) | EDGED | stands |
| column | 4,554 | source extract | implicit | yes (contains/cites) | EDGED | stands |
| file | 28 | estate intake of the .sql | yes (identity + tree) | yes | EDGED | stands |
| scope | 312 | parsed from its file | yes (name_key) | yes (contains) | EDGED | stands |
| meaning_twin | 28 | translated from its file's tree | yes (identity `twin::<file>`) | NO | UNWALKABLE | twin —translates→ file |
| twin interior nodes | 25,812 (data) | translation of parse nodes | yes (points_at, draws_from) | not adjacency citizens | Sunny's call: leave as twin-internal (readings walk them) or expose | leave internal (recommended — the twin is total, its own structure) |
| derived column | 3,671 | its defining scope's projection | yes (identity prefix) | pseudo-node (defines edges) | EDGED-pseudo | stands; note: pseudo status is acceptable (Sunny may rule otherwise) |
| condition | 474 (index) | voiced from its scope's predicate | yes (identity ::cN + owner) | NO — not in adjacency at all | INDEX-ONLY | condition —belongs_to→ scope (facet hits currently rely on owner-chain code, not edges) |
| parameter | ~40 (index) | its file's signature | yes (owner) | NO | INDEX-ONLY | parameter —belongs_to→ file |
| drift name | 132 | unresolved reads of files | yes (identity `file::ref`) | partial (sighted) | EDGED-pseudo | stands |
| description | 0 live (code) | a produce run + gate over a scope | yes (`about` targets + `anchor`) | NO | UNWALKABLE | description —describes→ about-targets; —anchored_to→ meaning identity |
| term | 1+vocab | **a confirmation / minting act over entities** | **NO — about holds its own name** | NO | **MISSING** | term —derived_from→ the confirming usage event; —about→ the entities it grounds (Sunny's ruling: "a term is deduced from a file's SQL") |
| responsibility | 1 | a steward assignment act | yes (about, author) | NO | UNWALKABLE | responsibility —assigns→ target; —by→ person |
| disposition | 0 live (code) | a human ruling on an artifact | yes (about) | NO | UNWALKABLE | disposition —rules_on→ artifact |
| usage | events | a person touching an item | yes (about, author) | NO | UNWALKABLE | usage —about→ item; —by→ person (Sunny's ruling) |
| proposal / redaction / run_event | 0 live (code) | acts with about/accounting | yes | NO | UNWALKABLE | same pattern: —about→ / —by→ |
| concept (KG4) | 0 live (code) | a human minting act over a family | yes (`minting_act` id, validated) | NO | UNWALKABLE | concept —minted_by→ act; —accepts→ terms |
| excluded_file | 0 live (code) | a refused parse at intake | reason only — **no estate/root link** | NO | MISSING-ish | excluded_file —excluded_from→ estate root |
| registration / estate root | (as db.minted_from) | — | — | — | ROOTED-CANDIDATE | THE root: everything intake-born chains to it |
| **person** | **0 — not a kind** | authors exist as strings on every act | strings only | NO | **MISSING-KIND** | person nodes minted on first act; every act —by→ person; the user tree's trunk |

## The tallies

23 kinds reviewed. **EDGED: 6** (the SQL world — where the
conservation laws already live). **UNWALKABLE: 10** (data present,
adjacency blind — one adjacency upgrade heals all ten).
**MISSING: 2** (term origins; excluded_file's root link).
**INDEX-ONLY: 2** (condition, parameter — searchable but not
traversable). **MISSING-KIND: 1** (person). **ROOTED: 1**
(registration). Twin interiors: Sunny's structural call.

The pattern is exactly the birth-edge law's prediction: the SQL
world is EDGED because its laws forced edges (resolves_to,
draws_from, conservation); the governance world is UNWALKABLE
because no law ever demanded its edges — data landed as properties
and stayed prose.

## Proposed build steps (each with its test suite shown FIRST, per the step discipline)

1. **Adjacency upgrade** — build_adjacency gains KG3/KG1 edges
   (about, author→person-pending, anchor, twin→file, db→schema);
   heals all ten UNWALKABLE rows. Test suite: per-kind walkability
   asserts + the connection census equation red-first.
2. **Term origins** — append_term gains derived_from/about origin
   params (junk self-about dies); vocab-term writes cite their
   confirming event + grounded entities; existing orphans counted.
3. **Person nodes** — minted on first act; every act carries —by→;
   the user tree's trunk.
4. **Condition/parameter edges** — belongs_to edges so facet
   provenance walks the graph instead of owner-chain code.
5. **excluded_file→root edge; registration ruled as THE root.**
6. **Registry: Connection_Ledger sheet** (this table, as ruled) +
   census equation swap + gap-check bucket + ADR.
