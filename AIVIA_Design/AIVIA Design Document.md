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
KG Layer 3 — artifact layer                            [ratified]
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
    -- authorship (DERIVED, never stored — ruled 2026-09-04):
       machine iff the author edge targets an agent identity;
       human otherwise (killed as a stored field: it restated the
       author's identity kind)
    -- ownership (DERIVED, never stored — ruled 2026-09-04):
       human iff any version has a human author OR an accepting
       disposition targets the artifact; otherwise machine. Once
       human, pipelines may only propose. The flip is one-way BY
       CONSTRUCTION — append-only history cannot be un-happened,
       so no rule needs enforcing. (Supersedes the earlier stored
       owner field: authorship alone misses
       certification-without-edit; a stored owner could drift
       from the history it summarizes.)
    -- status: OPTIONAL, machine versions only (amended
       2026-09-04): declared per class only where it says
       something authorship cannot; a class with nothing to say
       declares none (a status restating authorship is drift
       waiting to happen); an undeclared status value is a
       conformance failure
    -- created_at (events: occurred_at — when it happened, not
       when recorded)
    -- supersedes (ruled: NOTHING in this layer is ever edited in
       place — an edit appends a new version with a supersedes
       edge; "current" is derived. State-shaped = chains with a
       derived current pointer; event-shaped = chains without
       supersession. The layer is append-only because it is not
       regenerable. Version NUMBER is DERIVED — chain depth,
       never stored; ruled 2026-09-04) [axm:D3, axm:R4]
    -- basis (machine-authored only): the version stamps of
       everything the artifact derived from — tree version,
       metamodel version, source-pack version, prompt/gate
       version. The witness chain [axm:B1] AND the regeneration
       trigger: any basis version moving marks the artifact
       stale. Human-authored artifacts may carry a free-text
       reason; nothing is demanded of humans.
- Per-class properties (minimal by ruling — the spine does the
  work; anything derivable is a lens, anything event-shaped lives
  in events):
    -- description: text
       status vocabulary: machine versions gate_passed |
       skeleton_floor | flagged; human versions authored
       IOU (recorded 2026-09-04): kill accounting (dropped
       sentences counted, text never kept) and the absence rule
       (a failed description is NO artifact, counted in the run's
       ledger) relocate to the GENERATION RUN EVENT — lands with
       layer rules or the outward flow, whichever first
    -- term: name, definition; one class-specific edge:
       parent → term (hierarchy between term artifacts; can't
       ride about, which points at the estate). NO status —
       machine-nominated vs human-authored is the spine's
       authorship; accepted/rejected are dispositions; current
       standing is derived. Evidence (the name family, member
       tree versions) rides basis; what the term governs rides
       about.
    -- responsibility: kind (closed set: steward | owner |
       expert | dba | ...); holder → identity edge (the bearer —
       distinct from author, who recorded the assignment). NO
       status — usage-derived nominations are machine-authored
       versions w/ evidence in basis; a human's accepting
       disposition makes them real; ending/transfer = superseding
       version or revoking disposition; "currently responsible"
       is derived (and the identity node's own status feeds the
       lens — the person-left-the-org case).
    -- disposition: ruling (closed set: accept | reject | revoke
       | acknowledge — 'certify' merged into 'accept' 2026-09-04:
       one meaning, one verb — a human blessing machine output,
       whatever the class) + optional reason text. RULE:
       authorship is always HUMAN — machines never rule. Machine
       "findings" (divergence, staleness, human text contradicted
       by moved reality) need NO stored class: they are derived
       states computed by lenses on read — the machine never
       writes a judgment; it computes one when asked (completes
       the retirement of stored "conflict" verdicts).
    -- usage event: action (closed set: asked | ran | confirmed —
       'relied_on' cut 2026-09-04: no concrete capture point yet;
       enters by ratification when one exists); about = the node
       touched, author = the user, occurred_at = when. Nothing
       else — the flywheel is lenses over exactly this.
    -- proposal: kind (sent | observed).
       sent: target_system (closed set: purview | collibra | ...);
       about → the artifact version proposed.
       observed: outcome (closed set: published | denied | edited
       | missing); about → the sent event it observes.
       Current outcome is DERIVED (latest observation) — append-
       only forces sends and sightings apart; each look is its
       own fact.
- Edge types (ratified 2026-09-04 — five, all pointing at things
  that existed first; layers 1-2 never point up):
    -- about: artifact/event → what it concerns — a KG1/KG2 node,
       OR a layer-3 citizen (a disposition about a description; an
       observation about its sent event)
    -- author: any artifact/event → identity node
    -- holder: responsibility → identity node (the bearer — the
       governed node rides about; two different facts, two edges)
    -- parent: term → term (the hierarchy)
    -- supersedes: version → its predecessor
- Rules (ratified 2026-09-04; axiom citations per the standing
  practice):
    -- the ledger law: nothing edited or deleted in place — change
       is a superseding version, history is the truth; and
       anything computable from accumulated facts is a LENS, never
       a stored field (ownership, authorship, version, standing,
       findings) [axm:R4, axm:D3, axm:S3]
    -- human sovereignty: human-owned artifacts are never
       overwritten by pipelines — machines only propose;
       dispositions are human-only — machines never rule
       [axm:D3, axm:M5]
    -- witness: every machine-authored version carries basis (full
       input version stamps); every machine claim traces to the
       graph [axm:B1]
    -- gate at the boundary, absence over fabrication: machine
       text enters only through its class's gate with its closed
       vocabulary; total failure produces NO artifact. Every
       production run lands a GENERATION-RUN EVENT with
       conservation accounting: shipped ⊎ killed-lines ⊎ absent =
       attempted [axm:B2, axm:R1]
    -- durability: the layer is not regenerable — a backed-up
       asset, retention forever by default; loss is unrecoverable
       by definition [axm:S3]
    -- single writer per class: descriptions from the generation
       pipeline, dispositions from the human surface, usage from
       the ask surface, proposals from the bridge — one producing
       component each, writer-census checkable [axm:D3]
    -- metamodel conformance: every node/edge validates against
       the versioned registry; closed sets stay closed; identity
       edges resolve to identity nodes [axm:S2, axm:D4]
- Forward note [axm:B4]: a proposal SENT event is an outward,
  irreversible act — the outward flow's contract owes a
  human-confirmation clause.
KG Layer 4 — concept layer                             [ratified]
- The founding ruling (Sunny, 2026-09-04, option c): THE LENS
  COMPUTES; A HUMAN TOUCH MINTS. Relatedness (same-name families,
  similar logic, shared targets) is a lens over layers 1-3 —
  recomputed freely, never stored. A CONCEPT NODE is minted only
  at the first human act on a family (a ruling, or accepting a
  term nominated from it): identity + basis (the shape evidence
  at minting time), nothing else. Future lens runs REPORT AGAINST
  minted concepts ("this family gained two members"), never
  replace them. The layer is sparse by design: its population is
  every concept a human has engaged — not every cluster the math
  can find. Minted nodes share layer 3's nature: non-regenerable,
  because they exist exactly because a human touched them.
- Node type (ratified 2026-09-04): concept — id (content-keyed at
  minting) + basis (the family snapshot: member tree versions, the
  lens version that computed it). NOTHING else — no name, no
  description. The concept's human-facing identity IS its accepted
  parent term (layer 3, about → concept); naming the concept twice
  is the drift class. Before a term exists, the concept is known
  by its evidence.
- Edges (all point AT it; it points at nothing new):
    -- term.about → concept (the ratified name-and-definition)
    -- disposition.about → concept (rulings on the family)
    -- lens reports reference it by id — reports are derived, not
       edges
- Membership is NEVER stored: the lens recomputes it each run
  against current reality; basis holds what was seen at minting;
  the difference between them is itself a derived finding ("two
  definitions joined this family since the ruling").
- Rules (ratified 2026-09-04):
    -- human-mint-only: a concept node exists only as the anchor
       of a human act — machines compute families, never mint
       concepts [axm:M5, axm:D3]
    -- append-only: minted concepts are never edited or deleted;
       they share layer 3's non-regenerable nature [axm:R4]
    -- metamodel conformance [axm:S2, axm:D4]
Lenses                                                 [ratified]
- Definition: a lens is a named, versioned, DERIVED reading of the
  graph — the graph stores what is; lenses say what it means for
  one consumer; no consumer's lens constrains another's.
- The determinism rule (ratified 2026-09-04): A LENS IS
  DETERMINISTIC — same inputs, same graph state, same answer,
  replayable. If it needs a model, it is not a lens: model-shaped
  reading is MATCHING and belongs to the inward flow, with its own
  honesty machinery. Derivation and interpretation stay separate
  [axm:M5].
- The lens contract (ratified 2026-09-04) — every lens declares:
    -- name + version (results cite the lens version that computed
       them)
    -- reads: the node/edge classes consumed — declared, closed.
       The registry's union of reads, held against all layer 2-3
       classes, IS axm:D1's reachability accounting: every class
       read by some lens or carrying a recorded exclusion (IOU
       closed by mechanism)
    -- yields: the output shape, declared before code [axm:D4]
    -- completeness: whether the answer is total over what it
       read; downstream quantified claims inherit it [axm:B3]
    -- writes: NOTHING, ever — results return to consumers or land
       in regenerable report surfaces; layers 1-4 are never
       touched (the layer-4 mint is a HUMAN act citing lens
       output; the lens never mints)
- Catalog v1 (ratified 2026-09-04; each a registry entry under the
  lens contract; reads/yields formalized in the registry at build):
    -- ownership: version chains + dispositions → machine|human
    -- authorship: author edges + identity kind → machine|human
    -- version: supersedes chains → number per version
    -- standing: artifacts + dispositions →
       pending|accepted|rejected|revoked
    -- current-outcome: proposal sent+observed → latest outcome
    -- staleness: basis stamps vs current layer versions → stale set
    -- decisions(class): L2 predicates by tree position →
       membership|grain|value|path decision sets per scope
    -- degenerate: both-sides-literal predicates → decides-nothing
    -- join-compliance: L2 practiced vs L1 declared joins →
       violation findings (computed, never stored)
    -- divergence: human-owned artifacts vs moved reality →
       steward flags
    -- relatedness: names + tree content keys → families w/
       content-keyed ids (feeds concept minting + nomination)
    -- concept-drift: concept basis vs current relatedness →
       membership changes since minting
    -- expertise: usage events per node → de-facto experts
    -- blast-radius: usage + graph edges → dependents (people +
       consumers)
    -- working-set: L2 resolves_to → tables the estate touches
    -- gap-census: unresolved refs, keyless tables, unmapped
       remainder → the counted-absence surfaces, queryable
  Completeness swept both directions: every derived-never-stored
  ruling from layers 2-4 has its lens; no lens lacks a ratified
  origin.
The flows                                              [in design]
- The map (ruled 2026-09-04): THREE flows; one already contracted.
  Inbound (estate → graph) = CONTRACT_DATALOAD + layer 2's mapper
  rules, complete. This section designs outward (graph → catalog)
  and inward (inquiry → graph → estate, generating new estate when
  none matches — which re-enters through the parser).

- OUTWARD FLOW — three stages: produce → approve → land.

  Stage 1: PRODUCE (ratified 2026-09-04) — graph → layer-3
  machine versions:
    -- deterministic composition (lenses + tree evidence) +
       bounded model smoothing (linguistic seat only) + the class
       gate; the model never adds a fact — the gate enforces it
       [axm:B1, axm:M5/J2]; model failure degrades to the
       deterministic floor — an outage costs polish, never truth
    -- the trigger: the STALENESS LENS is the worklist (basis
       moved, no artifact yet, or explicit human request). No
       change, no production, no noise; nobody hand-picks; full
       regeneration = a version bump making everything stale —
       the same rule, not an exception
    -- writes: layer-3 machine versions ONLY; against human-owned
       artifacts it may APPEND a superseding version — rendered
       "proposed" by the ownership lens, never current
    -- every run lands the GENERATION-RUN EVENT: author = agent
       identity; basis = model/prompt/lens/metamodel versions +
       worklist; accounting shipped ⊎ absent = attempted, with
       killed-lines counted per shipped artifact [axm:R1]. The
       run event is the ONLY production ledger — quality numbers
       are lenses over run events, never separate bookkeeping
    -- replay floor: same graph + same versions → identical
       skeletons and gate verdicts; prose may vary, truth may not
       [axm:M5]
    -- checks: PROD-1 conservation event per run · PROD-2
       worklist = staleness-lens output · PROD-3 gate outcomes in
       closed vocabularies · PROD-4 human-owned never overwritten
       · PROD-5 replay determinism of the floor

  Stage 2: APPROVE — [next]
  Stage 3: LAND — [next]

- INWARD FLOW — [next]

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