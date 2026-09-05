**** AIVIA Description Level 0

AIVIA is a knowledge graph of a customer's analytical logic — built from per-file semantic trees over a shared technical vocabulary, from which decisions are derived as lenses, holding all metadata and governance artifacts as citizens of the graph itself — and it serves two directions: outward, generating catalog metadata from the estate; inward, matching user inquiries to the estate logic that answers them — and generating new estate when none exists, which enters the graph the same way everything else does.

**** Content Descriptions — Levels 1-3 (restratified 2026-09-05)

Level = CONSUMPTION STRATUM (Sunny's ruling): each level may only
reference lower levels — the import law, plank-checkable. "KG
Layer" = anatomy WITHIN level 1's graph; the two words never
substitute.

**** Level 1 — the knowledge graph [stores]

Edge direction convention (ratified 2026-09-05, closing the open
question): REFERENCE edges point toward the more stable node;
CONTAINMENT edges point parent → child. Both layers already obey
this; it is now law, not accident.

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
        --- grain (opportunistic — field-calibrated 2026-09-04:
            declared by phrase on core tables only; absent +
            gap-listed elsewhere, never guessed)
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
    -- primary key: every table carries pk_columns when the dictionary declares one; tables without a declared key land in a counted gap list — never guessed. referenced_keys (each table's declared reference keys, from inbound FK groups) is DERIVED from joins_to edges — a lens, never a stored property (ruled 2026-09-05).
    -- join legality: a joins_to edge is legal only if declared by the
   dictionary of the source that owns its dependent (FK) side. Joins
   between two vendor tables must be vendor-declared — never invented
   by the org; joins from org tables into vendor tables are declared
   by the org's dictionary. A practiced join violating this is a
   compliance finding, not a graph edit.
   -- source inheritance: a schema belongs to exactly one source; tables/columns inherit source from the containment chain; a mixed schema is the recorded trigger to push source down a level.

KG Layer 2 — logic layer (one tree per SQL file)       [ratified]
      L1 companions: Logic_Layer_Registry (subsumes the mapper's
      seam contract), Kind_Library_TSQL_Predicates
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
       files + KG layer 1 alone, never hand-edited. Rebuild
       SUPERSEDES, never deletes (the one-law ruling, 2026-09-05):
       a re-parse appends the new tree version and retires the
       prior; current is derived; retired nodes remain valid
       targets for layer-3 attachments and basis citations
       [axm:D3, axm:S3, axm:R4]
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
      L1 companions: Artifact_Layer_Registry
- The defining property: NOT regenerable. Layers 1-2 rebuild from
  sources; this layer holds human judgment and gated machine
  output that exist nowhere else. Human-owned artifacts are never
  overwritten by pipelines [axm:D3]; machine-owned artifacts
  regenerate freely until a human edit or acceptance flips
  ownership (derived — see the spine's ownership lens; the
  2026-09-04 drift sweep retired the older prefix-drop wording).
- Artifact classes (ruled 2026-09-04; one line each — the
  PER-CLASS SECTION BELOW IS THE TRUTH):
    state-shaped: description · term · responsibility
    event-shaped (append-only; current state DERIVED) [axm:R4]:
    disposition · usage event · proposal
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
    -- about: edge to >=1 target in any LOWER-OR-SAME layer — a
       KG1/KG2 node, a layer-3 citizen, or a minted concept
       (reworded 2026-09-05: the ratified edge sections already
       target all three); artifacts point at what they describe,
       never the reverse — layers 1-2 never know layer 3 exists
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
       status vocabulary (machine versions only, per the amended
       spine): gate_passed | skeleton_floor | flagged
       (IOU CLOSED 2026-09-04: kill accounting + absence rule
       landed in the layer rules AND the produce stage — the
       generation-run event)
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
       conservation accounting: shipped ⊎ absent = attempted,
       killed-lines counted per shipped artifact (aligned
       2026-09-05 to the produce stage — a kill drops a sentence
       inside a shipped artifact, not the artifact)
       [axm:B2, axm:R1]
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
- Forward note [axm:B4] — DELIVERED: the LAND stage carries the
  human-confirmation clause.
KG Layer 4 — concept layer                             [ratified]
      L1 companions: Concept_Layer_Registry
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
**** Level 2 — lenses [read level 1, write nothing]

Lenses                                                 [ratified]
      L2 companions: Lenses_Registry
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
       The registry's union of reads, held against all layer 2-4
       classes (widened 2026-09-05: layer 4 exists and is read),
       IS axm:D1's reachability accounting: every class read by
       some lens or carrying a recorded exclusion (IOU closed by
       mechanism)
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
    -- referenced-keys: inbound joins_to groups per table → each
       table's declared reference keys (added 2026-09-05, ruled
       derived-not-stored — D12)
  Completeness swept both directions: every derived-never-stored
  ruling from layers 2-4 has its lens; no lens lacks a ratified
  origin.
**** Level 3 — the flows [orchestrate: read via level 2, write via level 1's contracts]

The flows                                              [ratified]
      L3 companions: Flows_Registry
- The map (ruled 2026-09-04): THREE flows — L0's "two directions"
  are the two SERVICE flows; inbound is how the graph is built.
  One already contracted.
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

  Stage 2: APPROVE (ratified 2026-09-04) — fully covered by layer
  3's machinery (dispositions human-only; standing/ownership
  derived; the review queue is a lens). One stage rule: the
  approval surface WRITES DISPOSITIONS ONLY — it renders lenses,
  never touches artifacts, trees, or the technical layer
  [axm:D3]. Check: APPR-1 writer census.

  Stage 3: LAND (ratified 2026-09-04) — accepted artifacts → the
  customer's catalog:
    -- rendering: target-native forms only (file-first now, API
       later — the ruled transport order); ZERO custom attributes
       — native column sets held as data; attribution is the
       prefix in text, never a schema footprint
    -- the B4 clause (IOU due): a send is an outward, irreversible
       act — it requires an accepting disposition on the artifact
       AND a named human confirmation of the send itself; no
       autonomy mode exempts it [axm:B4]
    -- every send lands a proposal SENT event before transport;
       every later look lands an OBSERVED event; current outcome
       is the lens
    -- anti-repeat: no send for logic whose current outcome is
       denied unless a new version exists (standing rule R2, read
       from the current-outcome lens)
    -- look-before-write: at send time, read the ONE object about
       to be touched — never the catalog at large (standing rule
       R3); what was seen lands as an observed event
    -- checks: LAND-1 no send without accepting disposition +
       human confirmation · LAND-2 anti-repeat · LAND-3 sent
       event precedes transport · LAND-4 zero custom attributes
       in payloads · LAND-5 observations append-only
  The outward flow adds no new node types and no new classes —
  choreography over ratified contracts, nothing else.

- INWARD FLOW — three stages: match → ground →
  generate-when-missing. Adds no new layers or classes: match
  reads, ground arranges and appends usage events, generate feeds
  the existing inbound door.

  Stage 1: MATCH (ratified 2026-09-04) — inquiry → candidate
  graph objects + evidence:
    -- the seat: interpretation is the model's [axm:J2]; ONE mind
       composes freely over declared operations — lens reads,
       graph traversals, enumeration primitives — with full
       results in context; no question-shaped control flow
       [axm:M2, axm:M3, axm:M4]
    -- match proposes, evidence disposes: output is candidate
       GRAPH OBJECTS (ids) + the evidence trail — never generated
       text posing as fact; nothing model-said becomes a claim
       downstream [axm:B1, axm:B2]
    -- completeness declared on every result: top-K is never "all
       that exists"; enumeration questions use enumeration
       primitives that declare totality [axm:B3]
    -- outcomes, closed set: matched | ambiguous | no-match.
       Ambiguous goes to the HUMAN with candidates (intent
       judgment is human's [axm:M5]; no silent pick among
       near-ties). No-match is typed and counted — the honest
       empty, and stage 3's trigger, never a shrug
    -- writes: ONE thing — usage event `asked`, at inquiry
       arrival (every inquiry is a fact, especially unanswerable
       ones — the demand signal). Nothing else, ever
    -- checks: MATCH-1 writer census (asked only) · MATCH-2
       closed outcome set · MATCH-3 completeness on every result
       · MATCH-4 candidates are ids + evidence, never text ·
       MATCH-5 ambiguity reaches the human

  Stage 2: GROUND (ratified 2026-09-04) — matched objects → the
  answer:
    -- the answer is ARRANGED EVIDENCE: the matched logic, its
       tree, its artifacts, its lens readings — rendered; the
       answer text is a CAPTION over them, composed by the mind
       but adding no claim the evidence doesn't carry; headlines
       and counts are rendered by code from result metadata,
       never model-written [axm:B1, axm:B2 — the standing slogan
       as contract: operations are the product, the answer is a
       caption]
    -- quantified claims inherit the match's declared
       completeness — "all" and counts only over results declared
       total [axm:B3]
    -- execution (the Run act) is a CONSUMER of this stage, not
       part of it: gated, human-confirmed [axm:B4], governed by
       the ruled run machinery; result rows are DISPLAY-ONLY —
       they never enter the graph or the mind's evidence for
       claims. Data values and logic truth stay separate worlds
    -- writes: usage events only — `confirmed` when the human
       accepts an answer; `ran` when they execute. Nothing else
    -- checks: GRND-1 writer census (confirmed | ran only) ·
       GRND-2 caption gate — no ungrounded claim in answer text ·
       GRND-3 quantifiers only over declared-complete results ·
       GRND-4 headlines/counts rendered by code

  Stage 3: GENERATE (ratified 2026-09-04) — no-match → new
  estate, through the front door:
    -- trigger: a no-match outcome AND an explicit human request —
       generation is an act someone asks for, never an automatic
       consolation
    -- the builder's grounding — layer 1 is the whole vocabulary:
       generated SQL composes only from declared reality —
       existing tables/columns, joins along declared joins_to
       paths (the legality rule pays forward: the builder WALKS
       the join graph; an unjoinable pair is an honest refusal
       naming the missing declared path), documented value sets
       for category filters. The model drafts; a DETERMINISTIC
       validator checks every reference and join against layer 1
       before the draft reaches the human [axm:B1, axm:M5]
    -- the draft is DISPLAY-ONLY: delivered through the answer
       surface, writes nothing; a discarded draft leaves no
       residue (demand was captured by asked + no-match)
    -- the parser door (the L0 ruling): a draft becomes estate
       ONLY by the human adopting it into their source and the
       inbound flow parsing it like any customer file — zero
       trust shortcuts; from then on descriptions, terms,
       governance work on it with no special cases
    -- adoption and execution are human-confirmed acts [axm:B4]
    -- generated-file provenance (ruled 2026-09-04, option c):
       unmarked in v1 — the org's repo history carries it;
       revisit trigger: an adoption mechanism that can feed an
       origin property structurally
    -- checks: GEN-1 validator totality (references resolve,
       joins declared; refusals name the missing path) · GEN-2 no
       side channel — the inbound door is the only door · GEN-3
       drafts write nothing · GEN-4 generation only on no-match +
       human request

**** Hardening passes (cross-level law)

The CHANGE pass — what survives change            [ratified]
- Method: scenario-driven (scenarios are the answer key of
  architecture — authored expected outcomes, then the design is
  walked against them). Scenarios blessed 2026-09-05:
    S1 edited file: a certified description's scope gains a
       predicate and the file re-parses → the description
       survives, attached to the SAME scope; divergence flags it;
       nothing dangles or silently re-attaches
    S2 deleted scope: the scope is removed entirely → the
       description neither vanishes nor dangles silently — a
       counted orphan state a steward can see and rule on
    S3 auditor's question: "why did Maria certify this?" a year
       later → the basis chain produces the evidence she saw
       (forces the retention ruling)
    S4 drifted family: a minted concept's family changes → the
       drift lens reports against the minted concept (forces the
       correspondence rule)
    S5 version bump: everything goes stale at once → regeneration
       by declared priority within a budget; proposals at a pace
       a steward survives
- RULING (2026-09-05): Layer-2 node identity is NAME-KEYED for
  the nodes artifacts attach to — file (source path) and scope
  (file :: scope name) — so an attachment survives edits INSIDE
  the named thing; content keys are DRIFT EVIDENCE, not identity.
  S1's expected outcome (survives the edit, gets flagged) is
  exactly name-keyed identity + content-drift detection.
- RULING (2026-09-05, Sunny's call — the one law): NOTHING IN THE
  GRAPH IS EVER PHYSICALLY DELETED. Change supersedes; current is
  derived; retired nodes remain valid targets. A re-parse appends
  the new tree version and retires the prior (valid_to); same for
  extract succession (which already ruled this for layer 1). The
  whole graph is append-and-supersede with derived current —
  layers differ only in AUTHORITY (rebuildable from source vs
  irreplaceable), never in mutation style. Industry basis: SCD
  Type 2; catalog soft-delete (consumers hold references into
  us); event-sourced projections. Known cost, accepted: storage
  grows monotonically — trivial at metadata scale.
  CONSEQUENCES: S2 CLOSED — no orphans exist; artifacts attached
  to a retired node surface in the steward queue ("attached to
  retired scope") with similarity candidates; re-attachment stays
  a human disposition. S3 REDUCED to a retention line: retained
  versions ARE the evidence basis cites; default retention
  forever; pruning is a ruled act, never automatic.
- RULING S4 (2026-09-05, correspondence): each recomputed family
  corresponds to the minted concept whose basis members it
  overlaps MOST, measured on name-keyed member ids (the one law
  guarantees they still exist). Closed outcomes: corresponds
  (drift lens reports against it) · dispersed (surfaced finding)
  · merged (one family, two+ concepts — AMBIGUOUS, both named,
  human rules, never auto-merged) · new territory. Ties →
  ambiguous. The machine never re-anchors; correspondence is a
  REPORT.
- RULING S5 (2026-09-05, staleness economics): staleness is a
  STATE; regeneration is a BUDGETED QUEUE — consumed in
  usage-weighted priority order (blast-radius + expertise lenses
  are the ranking); every produce run has a registered budget and
  records consumed + remaining backlog ("stale but not
  regenerated" is visible and counted, never silent, never a
  stampede); proposals to human-owned artifacts pace at the
  steward's pull. A version bump is an economic event with knobs,
  not an emergency. Checks: ECON-1 worklist order =
  priority-lens output · ECON-2 budget respected · ECON-3
  backlog counted in the run event.
- Node lifecycle contracts (ratified 2026-09-05, the
  operation-grain complement to these scenarios): layer 1 in
  CONTRACT_DATALOAD §11; layers 2-3 as Lifecycle sheets in their
  registries; layer 4 inherits (human-mint CREATE only).
- PASS CLOSED: S1-S5 all pass by construction against the
  ratified rulings.

The EDGES pass — the system's outer boundary       [ratified]
- Scenarios blessed 2026-09-05:
    E1 day one: the SQL estate arrives → a REGISTERED estate
       source; every in-scope file acquired ⊎ counted-excluded;
       nothing silently skipped
    E2 nightly refresh: changed file → supersede; deleted file →
       retire; cadence is a registered property
    E3 the report: blast-radius must answer "what breaks?"
       including reports — or narrow honestly (forces H4)
    E4 the unanswerable question: demand captured; "top
       unanswered questions" answerable later; inquiry shape
       ruled here, PHI treatment deferred to the SAFETY pass
       (recorded coupling)
    E5 the non-SQL file: counted unsupported-dialect with its
       placeholder named — conservation at estate grain
- RULING (2026-09-05, H3 — the estate source contract, the
  inbound door's twin): a registered estate source = (org, kind,
  location/scope declaration, declared dialect(s), cadence),
  producing SELF-CONTAINED SNAPSHOTS identified by (source,
  as_of). File identity = stable source path (the name-key layer
  2 already uses). Scope conservation: acquired ⊎ counted-
  excluded (reason: out-of-scope | unsupported dialect |
  unreadable). Succession per the one law: changed supersedes,
  absent retires, the change report says so. Intake checks mirror
  INTAKE-0..7. Deliberately the same shape as CONTRACT_DATALOAD —
  the two inbound doors are the same door twice.
- RULING (2026-09-05, H4 — consumption): NOT a new layer. Reports
  are estate files in a placeholder dialect (TMDL), entering
  through the registered estate source; consumption edges are
  resolves_to from report trees — to L1 tables (DirectLake) or to
  L2 FILE nodes (proc-backed datasets; a new resolves_to target,
  ruled now so the mapper needs no design change later). UNTIL
  the TMDL mapper is built: report files land as counted
  unsupported-dialect (E5's law), and the blast-radius lens
  DECLARES its completeness as people-only — honest narrowing,
  visible in every result [axm:B3].
- RULING (2026-09-05, H5 — no-match demand): the asked usage
  event gains outcome (matched | ambiguous | no-match — the match
  stage's own closed set) and, on matched/ambiguous, about → the
  candidate node(s); on no-match, NO about edge — nothing was
  touched, and the absence IS the fact. The inquiry TEXT rides
  the asked event as payload (the only place demand content can
  live); its PHI treatment is an explicit SAFETY-pass obligation
  on this field. "Top unanswered questions" = the DEMAND lens
  (catalog #18): no-match asked events → clustered themes +
  counts, feeding generate offers and governance priority. Not an
  inquiry class: demand IS usage — one ledger, never two.
  Checks: MATCH-1 amended (asked carries outcome); DEMAND lens
  declares completeness.
- PASS CLOSED: E1-E5 pass by construction; H3, H4, H5 closed.

The SAFETY pass — PHI and residency                [ratified]
- Scenarios blessed 2026-09-05: SF1 the MRN in a WHERE clause ·
  SF2 the patient name in a question · SF3 the late discovery.
- RULING 1 (the PHI boundary): all inbound text — estate files at
  acquisition, inquiry text at event landing — passes the PHI
  scan/redact gate BEFORE entering any layer; redactions counted,
  never silent; the layer-2 evidence law is amended one word:
  verbatim-AFTER-REDACTION. PHI never stored is PHI never voiced.
  Checks: SAFE-1 both doors gated · SAFE-2 redactions counted.
- RULING 2 (the ONE exception to the one law, stated narrowly):
  for late-discovered PHI or a legal obligation, a RULED
  REDACTION ACT may destroy content in place — human-confirmed
  [axm:B4], scoped to the offending field — and it appends a
  permanent REDACTION EVENT (who, why, what shape was removed,
  never the content). The content dies; the fact that it died is
  forever. Boundary-first means this path should almost never
  run; a design with no lawful path forces improvisation on the
  worst day. Check: SAFE-3 — redaction acts are human-ruled,
  tombstoned, and the ONLY destruction path in the codebase.
- RULING 3 (tenancy, H11): one graph = one org, resident in the
  customer's tenant; nothing crosses out except de-identified
  aggregates, by explicit decision — the intake report's
  residency clause generalized. Check: SAFE-4 egress census.
- PASS CLOSED: SF1-SF3 pass by construction; H6, H11 closed.

The SCALE/OPS pass — envelope and failure          [ratified]
- Scenarios blessed 2026-09-05: SO1 the 39k-table estate · SO2
  the run that dies at artifact 200 of 460 · SO3 the question
  during the batch.
- RULINGS (2026-09-05, H9 + H10):
    -- the ENVELOPE is registry data, not vibes — calibration
       targets (revalidated at first build measurements): estates
       to ~50k tables / ~100k columns / low-thousands of files;
       trees to ~10M nodes; interactive surfaces in seconds;
       batch sweeps in minutes-to-hours, budgeted per S5
    -- lens MATERIALIZATION MODE declared per lens: on-demand
       (cheap derivations) | materialized (estate-scale sweeps —
       relatedness, working-set, gap-census, demand); a
       materialized result is a REGENERABLE report surface
       stamped with lens version + graph state — a cache with a
       birth certificate, never a second truth
    -- run events carry outcome (completed | aborted + progress);
       PER-ARTIFACT ATOMICITY (an artifact lands whole or not at
       all); RESUME = the staleness worklist — landed artifacts
       fall out of it, so no checkpoint machinery exists
    -- readers never block on writers (append-only makes this
       nearly free); a consistent read = a graph-state stamp
  Checks: OPS-1 materialized surfaces regenerable + stamped ·
  OPS-2 no partial artifacts · OPS-3 aborted + rerun = identical
  end state to one completed run · OPS-4 envelope numbers in the
  registry, cited by capacity tests.
- PASS CLOSED: SO1-SO3 pass by construction; H9, H10 closed.

ALL FOUR PASSES CLOSED (2026-09-05): the open register stands at
15/15 drifts and 11/11 holes closed. The Level-1 design is
hardened: every room ratified, every seam contracted, every
lifecycle contracted, every hole ruled.

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
beside it (L1_* files, named for the Level-1 section they attach
to); the doc holds WHAT and the rules, the companions hold the
machine-readable and test-facing detail.

The Disambiguation clause (ratified 2026-09-05 — ambiguity dies
in examples and procedures, never in more prose):
1. DECIDING EXAMPLES: a rule is ratifiable only with at least one
   deciding example — a concrete case + its single expected
   outcome, landed beside the rule. Prose and example must agree;
   the example wins disputes.
2. SELECTION AS PROCEDURE: any rule that picks — "current",
   "stable", "corresponds", "owns" — states its selection as a
   deterministic procedure (or names the lens/function embodying
   it), never as an adjective.
3. TWO-READINGS ESCALATION (the HITL law): anyone — human or
   build agent — finding a point where two readings both comply
   must NOT choose. Both readings land as a register row; the
   ruling is Sunny's. An implementer's uncertainty is a register
   row, not a decision [axm:R3 applied to design gaps].

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