**** AIVIA Description Level 0

AIVIA is a knowledge graph of a customer's analytical logic — built from per-file semantic trees over a shared technical vocabulary, from which decisions are derived as lenses, holding all metadata and governance artifacts as citizens of the graph itself — and it serves two directions: outward, generating catalog metadata from the estate; inward, matching user inquiries to the estate logic that answers them — and generating new estate when none exists, which enters the graph the same way everything else does.

**** Content Descriptions Level 1

KG Layer 1 — source dictionaries technical layer      [ratified]
      L1 companions: Technical_Layer_Registry, CONTRACT_DATALOAD
- Node types: 
    -- db
        --- description
        --- as_of
    -- schema
        --- description
        --- as_of
        --- source
    -- table
        --- description
        --- as_of
        --- pk_columns
        --- grain
    -- column
        --- description
        --- as_of
        --- values
- Edge types: 
    -- db to schema: contains, as_of
    -- schema to table: contains, as_of
    -- table to column: contains, as_of
    -- table to table: joins_to, as_of, on, cardinality
        Normal join — one edge, one pair:

        ENCOUNTER ──joins_to──▶ PATIENT
           on: [[PATIENT_ID, PATIENT_ID]]
           cardinality: many_to_one

        Composite join — still one edge, two pairs:

        DX_COMMENT ──joins_to──▶ ENCOUNTER_DX        (pk_columns: [ENCOUNTER_ID, LINE])
           on: [[ENCOUNTER_ID, ENCOUNTER_ID], [DX_LINE, LINE]]
           cardinality: many_to_one
- Rules
    -- single source of authority, per object: every node and edge derives
   from the registered dictionary extract of the source system that
   owns it; nothing enters this layer except through a registered
   extract — nothing parse-derived, nothing hand-typed. The org's own
   dictionary (control_ tables, join mappings) is a registered source
   like any vendor's. 
    -- regenerability: the layer rebuilds from extracts alone  
    -- metamodel conformance: every node/edge matches the declared kinds and properties
    -- property-vs-node: in the regenerable technical layer, prefer properties; promote to nodes only on demonstrated need — promotion is a re-extract, not a migration.
    -- primary key: every table carries pk_columns when the dictionary declares one; tables without a declared key land in a counted gap list — never guessed. 
    -- join legality: a joins_to edge is legal only if declared by the
   dictionary of the source that owns its dependent (FK) side. Joins
   between two vendor tables must be vendor-declared — never invented
   by the org; joins from org tables into vendor tables are declared
   by the org's dictionary. A practiced join violating this is a
   compliance finding, not a graph edit.
   -- source inheritance: a schema belongs to exactly one source; tables/columns inherit source from the containment chain; a mixed schema is the recorded trigger to push source down a level.

KG Layer 2 — logic layer (one tree per SQL file)       [ratified]
      L1 companions: Kind_Library_TSQL_Predicates, logic contract (tbd)
- The unit (ruled 2026-09-04): the whole FILE is one tree. All
  logic is a natural result of walking the tree; no "smallest unit
  of logic" is ever defined. A #temp table is internal structure of
  its file's tree — a named intermediate scope, like a CTE — never
  a technical-layer citizen.
- Node types:
    -- file (the tree's root)
        --- physical name, source path
        --- dialect
        --- parsed_at, parser/metamodel versions
    -- statement (children of file, in order — the staging chain;
       a statement is what the dialect's parser says is one
       executable command — never punctuation-defined; control-flow
       blocks nest statements inside statements)
    -- scope (a SELECT with its clauses; also: CTE, subquery,
       temp-table scope — every place logic has its own boundary)
        --- name (CTE/temp name where one exists)
    -- structure (FROM, JOIN w/ type, WHERE, HAVING, GROUP BY,
       ORDER BY/TOP, UNION w/ dedup flag, CASE)
    -- predicate (one condition; kind from the metamodel's
       closed set)
    -- expression (column_ref | table_ref | literal | parameter_ref
       | function | arithmetic | unary | case | cast | subquery_ref)
    -- parameter (file-scope; declared name, default logic)
- Every node carries: evidence (verbatim source fragment +
  location) and the version stamps
- Reference nodes (column_ref, table_ref) are the ONLY pointers
  into KG layer 1, always via resolves_to; unresolved refs are
  counted, never dropped (ruled 2026-09-04; supersedes the earlier
  column_ref-only wording — a FROM clause references tables)
- Not node types, on purpose: decisions (derived by lenses);
  anything the technical layer owns; CTEs-as-statements (a CTE is
  a scope INSIDE its one declaring statement — it cannot stand
  alone; a #temp stage is its own statement — both become SCOPE
  nodes, so downstream consumers never care which staging style
  the author used)
- Edge types (ruled 2026-09-04 — two families):
    -- contains: parent → child through the whole tree
       (file→statement, statement→statement for control-flow
        blocks, statement→scope, scope→structure,
        structure→predicate, predicate→expression,
        expression→expression)
        --- position: where sibling order carries meaning
            (statements in the staging chain, function arguments,
             CASE branches, IN-list members)
        --- role: on predicate→expression children only —
            subject | comparand | lower_bound | upper_bound |
            pattern | escape | selection | quantifier
    -- resolves_to: every *_ref node → the thing it names
       (mention → meaning; points toward the more stable node)
        --- column_ref  → KG1 column
        --- table_ref   → KG1 table OR a scope in the SAME tree
            (a CTE or #temp stage — the staging chain becomes
             graph structure with no special machinery)
        --- parameter_ref → the file's parameter node
        --- subquery_ref  → its scope node
        --- an unresolvable ref gets NO edge — counted, never
            guessed
- Rules (ratified 2026-09-04; each cites its axiom in
  docs/AI_VIA_AXIOMS.md):
    -- parser authority: tree structure comes from the dialect's
       parser and nowhere else — never punctuation, never regex,
       never text heuristics [axm:D2, axm:M5]
    -- conservation: every construct in the source file maps into
       the tree or lands in the counted remainder with reason and
       location — handled ⊎ remainder = total, no third bucket;
       unknown vendor constructs are a red build via the reflected
       denominator; the remainder aggregates to a human ruling
       [axm:R1, axm:R2, axm:R3]
    -- evidence: every node carries its verbatim source fragment
       and location — the tree is the witness chain for everything
       downstream [axm:B1]
    -- scope ownership: every predicate belongs to exactly one
       scope; a nested scope's logic is its own, never the
       parent's [axm:D3]
    -- resolution honesty: a reference resolves via resolves_to or
       carries no edge; unresolved references are counted, never
       guessed; resolution results declare completeness
       [axm:B3, axm:R1]
    -- single writer, regenerable: only the mapper writes this
       layer; trees are derived artifacts, rebuilt from source
       files + KG layer 1 alone, never hand-edited
       [axm:D3, axm:S3]
    -- metamodel conformance: every node and edge validates
       against the versioned registry; kinds are closed; a new
       kind goes doc -> registry -> code, never code-first
       [axm:S2, axm:D4]
    -- structure carried, never lowered: the tree is the ONLY
       representation of a file's logic; downstream consumers read
       the tree, never the source text (evidence is for display
       and audit, not re-parsing) [axm:S1, axm:M5; = spec:G5 in
       the code record]
KG Layer 3 — artifact layer                            [in design]
- The defining property: NOT regenerable. Layers 1-2 rebuild from
  sources; this layer holds human judgment and gated machine
  output that exist nowhere else. Human-owned artifacts are never
  overwritten by pipelines [axm:D3]; machine-owned artifacts
  regenerate freely until a human edit flips ownership (the
  attribution prefix dropping IS the observable flip).
- Artifact classes (ruled 2026-09-04), split by shape:
    state-shaped (versioned, owned transitions):
    -- description (LLM-generated, gated, provenance-stamped;
       owner flips machine->human exactly once)
    -- term (machine-NOMINATED from graph shape w/ evidence, or
       human-authored; only human ratification makes it a term;
       nothing gates on certification — status tells the truth)
    -- responsibility ((person-or-role, kind, target node); kinds:
       steward | owner | expert | dba | ...; multiples allowed —
       one-steward-per-asset is an org policy, never our structure)
    event-shaped (append-only; current state DERIVED by lens,
    never stored) [axm:R4]:
    -- disposition (a human ruling on a target; multiple rulers
       allowed; conflicting rulings surface as a disagreement
       state with names — never silent last-write-wins)
    -- usage event (who asked/ran/confirmed/relied-on which node,
       when — the flywheel's ledger; lenses derive de-facto
       expertise, blast radius in people, personal truth layers,
       usage-weighted priority; usage NOMINATES governance,
       humans ratify — never silent promotion)
    -- proposal record (what was proposed to which catalog and
       the last observed outcome: published | denied | edited |
       missing; buys anti-repeat, divergence detection, honest
       engagement accounting — we leave no marker in their
       catalog, so this is our only memory)
- Identity (ruled 2026-09-04): a NODE kind — person | role |
  agent (the machine is an identity too: pipeline + model,
  versioned). A thin local proxy for the directory entry, keyed by
  the immutable Entra object ID; Entra stays the authority on who
  people are. Note: the regenerable-layer property-vs-node
  principle does NOT transfer here — this layer is not
  regenerable, so promote-later would be a migration of
  irreplaceable history.
- The shared property spine (ruled 2026-09-04; every artifact
  class carries it):
    -- about: edge to >=1 target node in KG layers 1-2; artifacts
       point at what they describe, never the reverse — layers
       1-2 never know layer 3 exists
    -- author: edge to an identity node
    -- authorship: machine | human — explicit, never inferred
    -- ownership (DERIVED, never stored — ruled 2026-09-04):
       human iff any version has a human author OR a certifying
       disposition targets the artifact; otherwise machine. Once
       human, pipelines may only propose. The flip is one-way BY
       CONSTRUCTION — append-only history cannot be un-happened,
       so no rule needs enforcing. (Supersedes the earlier stored
       owner field: authorship alone misses
       certification-without-edit; a stored owner could drift
       from the history it summarizes.)
    -- status: closed set, DECLARED per class; an undeclared
       status value is a conformance failure
    -- created_at (events: occurred_at — when it happened, not
       when recorded)
    -- version + supersedes (ruled: NOTHING in this layer is ever
       edited in place — an edit appends a new version with a
       supersedes edge; "current" is derived. State-shaped =
       chains with a derived current pointer; event-shaped =
       chains without supersession. The layer is append-only
       because it is not regenerable) [axm:D3, axm:R4]
    -- basis (machine-authored only): the version stamps of
       everything the artifact derived from — tree version,
       metamodel version, source-pack version, prompt/gate
       version. The witness chain [axm:B1] AND the regeneration
       trigger: any basis version moving marks the artifact
       stale. Human-authored artifacts may carry a free-text
       reason; nothing is demanded of humans.
- Per-class properties, edge types, rules: [next]
KG Layer 4 — concept layer                             [undesigned]
Lenses                                                 [named, undesigned]
      IOU (recorded 2026-09-04): axm:D1 — when lenses are
      designed, a reachability accounting over KG layer 2 node
      classes is required (every node class reachable through a
      declared operation or carrying an explicit exclusion).
The two flows                                          [later]

**** Design-to-Code Protocol (Level 0 law)

Six steps, in order, for every component; no step skipped:
1. Doc section ratified here first — the doc is the design authority.
2. Metamodel registry updated: the doc's node/edge/property
   definitions restated as a machine-readable data file. Code and
   tests consume the registry, never the prose; any doc change
   updates the registry in the same breath.
3. Every rule gets named checks, enumerated before code — a rule
   with no check is a hope (the rule-to-check map).
4. Fixtures authored: synthetic input + hand-authored expected
   output (the answer key), written before any builder exists.
5. Only then code — until the checks are green. Code never
   introduces a concept the registry doesn't have.
6. Discoveries flow backward: anything code reveals goes to the DOC
   first, then registry, then code — never patched in place.

Companion artifacts are indexed to this doc's levels and live
beside it (L1_KGn_* files, named for the Level-1 section they
attach to); the doc holds WHAT and the rules, the companions hold
the machine-readable and test-facing detail.

Binding mechanisms (ratified 2026-09-04 — what makes steps 2-3
physics instead of discipline; all build deferred with the rest):
a. Registries are code-consumed data, version-bound to the doc:
   each doc section carries a version stamp, its registry declares
   the same stamp, a CI check compares — the same-breath rule made
   mechanical.
b. The rule-to-check closure meta-test: every rule in every
   registry must name at least one existing check — "a rule with
   no check is a hope" enforced as arithmetic.
c. Banned-construct planks: parser-authority and
   structure-never-lowered get AST-level guards on the modules
   they govern (the proven plank pattern, new scope).
d. The metamodel version rides every stamp: stored trees and
   derived artifacts carry the registry version they conform to;
   a metamodel change regenerates everything it governs.