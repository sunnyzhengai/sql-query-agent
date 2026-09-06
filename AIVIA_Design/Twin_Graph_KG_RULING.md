# The Twin-Graph KG — RATIFIED (Sunny, 2026-09-06)

*RATIFIED 2026-09-06: Sunny reviewed paragraph by paragraph the
same night — amendments landed in place during the review
(composed-meaning sentence · the change quanta · lens-stratum
retirement → builders + readings · the voicing ledger) — and
closed with "all good, go with your recommendations": every
register call adopts its recommendation. Origin: ED-sepsis
gap-check findings 3 and 4 traced to ONE generator — the flat-set
yield shape of the decisions lens, inherited from the field era
and ratified by restatement (the design-first-triage lesson).
This ruling is the first-principles re-derivation of the meaning
layer across ALL strata: Blueprint (L0), The Graph, The Flows
(the lens stratum retired mid-review). Remaining transplant:
piece 1 replaces L0 in "AIVIA Design Document.md" (Sunny's doc,
his edit). Next build act: Phase A — metamodel bump + A12
projection re-parse (5d).*

---

## Piece 1 — the L0 REWRITE (RESTATEMENT RATIFIED by Sunny
## 2026-09-06: three layers, twin KG2, governance overlay, the
## lineage guarantee; blueprint form — a two-way engine, components
## + interactions — never a lyric summary)
**Lands in: AIVIA Design Document, L0 — REPLACES the ratified
sentence in full.**

> AIVIA is a TWO-WAY ENGINE over a customer's analytical estate,
> built on one knowledge graph with three layers. Syntax is PARSED
> to the leaf; semantics is DERIVED to the leaf; the two are
> connected at every level — fused in KG1, pointed in KG2.
>
> - **KG1 — the declared layer** (the foundational databases:
>   vendor EMR + the org's own schemas): tables, columns, declared
>   keys, dictionary meanings, value maps — loaded from source
>   metadata. Syntax and semantics are FUSED here: one node carries
>   what a thing is and what it means, because declared meaning
>   needs no pointer to its source. Every object carries a content
>   hash + load stamp; the layer loads INCREMENTALLY — only changed
>   source objects touch the graph. KG1 grounds every translation.
> - **KG2 — the derived layer** (the org's reporting logic: procs,
>   views, metrics, reports), built as TWINS:
>   - **KG2a, the parsed graph**: one tree per file, built by the
>     dialect's NATIVE parser, every node carrying its verbatim
>     source fragment and location. Complete by conservation:
>     handled + counted == everything the AST holds, no third
>     bucket. Its ONLY outward pointers are resolution edges —
>     every table/column reference resolves to KG1 or is counted.
>     That narrowness is the choke point all lineage flows through.
>   - **KG2b, the meaning graph**: the homomorphic twin. Every
>     meaning node POINTS at the parsed node it translates and
>     draws its content from KG1 — derived meaning always cites
>     its source. Total by construction, never by enumeration:
>     every parsed node is translated or counted as a gap; even
>     decides-nothing predicates are translated. Meaning exists at
>     EVERY grain the parse has: leaf nodes translate through KG1;
>     composite nodes — scope, statement, file — translate by
>     COMPOSING their children's meanings, so a file's meaning is
>     the deterministic summary of everything inside it, never a
>     separate invention. Voicing is policy over this twin — what
>     prose prints is a choice; what meaning exists is not.
> - **KG3 — the governance overlay**: users and roles, usage
>   events, dispositions (certify, approve, reject), terms, minted
>   concepts. SPARSE by construction — citizens exist only where
>   someone acted — and NOT REGENERABLE: it holds human judgment
>   and gated machine output that exist nowhere else. Every citizen
>   anchors to MEANING identity (a KG2b content-key, or a KG1
>   node), never to syntax and never to a node instance — so
>   syntax-only churn costs no governance, and a changed meaning
>   visibly orphans its artifacts: drift detection falls out of the
>   anchoring rule.
>
> The graph is written ONLY by three BUILDERS — loader → KG1,
> parser → KG2a, translator → KG2b; governance has no builder,
> only human acts. Everything else that consumes the graph is a
> READING: named, versioned, deterministic — and it writes
> nothing.
>
> The engine runs both directions through the same layers:
>
> - **OUTWARD** (estate → catalog): parse into KG2a → twin into
>   KG2b → voice per policy → land stamped, regenerable catalog
>   metadata; human acts accrete in KG3.
> - **INWARD** (inquiry → estate): match the inquiry against KG2b,
>   the meaning graph → return the estate logic that answers it;
>   when none exists, generate new estate — which enters through
>   the same parser door as everything else: parsed, twinned,
>   voiced, governed.
>
> **The lineage guarantee.** The totality laws compose: every
> reference is captured or counted (conservation), resolved or
> counted (resolution), translated or counted (totality), and
> every governance act anchors to meaning. Therefore every
> ingested thing — an EMR column, a temp table, a metric — is
> reachable by graph traversal or present in a counted gap: NEVER
> SILENTLY ABSENT. Search a column and every table, sql block,
> metric, and user touching it is a traversal away (unresolved
> references stay findable by name). Lineage is not a feature
> built beside the graph; it is a query over edges the laws
> guarantee exist.
>
> ```
>             ┌───────────────────── OUTWARD ─────────────────────────┐
>  estate ──► KG2a PARSED ══ points-at ══ KG2b MEANING ──policy──► catalog metadata
>    ▲        evidence · conservation     translation · total          stamped · regenerable
>    │            │ resolves_to               ▲   │  ▲
>    │            ▼                           │   │  └─ KG3 governance overlay
>    │        KG1 DECLARED (fused syntax+semantics, incremental)      (sparse · non-regenerable
>    │                                            │                    users · usage · decisions)
>    │                                            ▼
>    └──── generated estate ◄── (none exists) ◄─ match ◄── user inquiry
>             └───────────────────── INWARD ────────────────────────────┘
> ```

**Change ledger vs. the ratified L0:**
1. FORM: the single ratified sentence REPLACED by a blueprint.
2. FOUR LAYERS BECOME THREE: KG3+KG4 merge into the governance
   overlay (concept becomes a citizen class keeping its rules).
3. "per-file semantic trees" RETIRED — "semantic" moves to KG2b.
4. NEW at L0 grade: fused-vs-pointed · both totality laws · the
   anchoring rule · the lineage guarantee ("never silently
   absent", not "nothing left behind").
5. PRESERVED in force: vocabulary grounds translation · artifacts
   as citizens · readings pure and write-nothing (the former lens
   law, renamed) · both service directions · one door for new
   estate.

---

## Piece 2 — THE GRAPH (the metamodel; replaces the current
## "Level 1" content under the new strata naming — see Piece 6)

### 2a — KG1 (rider R-1 lands here)
Node shapes unchanged EXCEPT: every KG1 object gains
`content_hash` (over the object's declared syntax + semantics as
loaded) and `loaded_at` + source-snapshot stamp. These two columns
are what make incremental intake and object-grain staleness
mechanical (Piece 5a). Fusion stated as law: a KG1 node carries
what the thing is AND what it means; there is no KG1 twin.

### 2b — KG2a: the A12 un-deferral
PROJECTION enters the metamodel: the SELECT list becomes a
structure kind with one projection-member node per output column
(name, expression subtree — the expression kinds already exist).
The A12 ruling planned this exact recovery: metamodel version
bump + estate re-parse; regenerability makes it cheap. Everything
else in KG2a is unchanged, including: the file-is-one-tree unit
ruling · scope ownership · resolves_to as the only outward
pointers · conservation.

### 2c — KG2b: the meaning node (the new node family)
Every meaning node carries:
- `kind` — from the closed library (2d)
- `content` — the translated meaning material (steward-voiced
  operand words, resolved value meanings, composed phrases)
- `points_at` — edge to EXACTLY ONE KG2a node (the homomorphism;
  a gap meaning-node points at the parsed node or counted site it
  stands for, reason-coded per the 0044 pattern)
- `draws_from` — edges to every KG1 node consulted (dictionary
  entry, values map, pk) — derived meaning cites its sources
- `content_key` — the meaning identity (2e)
- basis stamps — translation version + metamodel version
Laws: homomorphism (translated + gap == every KG2a node, no third
bucket — the conservation equation generalized, queryable) ·
KG2b regenerates WHOLE with KG2a on version bumps, atomically.

### 2d — the meaning-node kind library
**RULED (2026-09-06) — the nine kinds:** selection (scope; carries
grain where derivable) · source (FROM/JOIN ref w/ join kind;
resolves to KG1 table or a same-tree selection node — the handle)
· condition (predicate; kinds = the ratified R4 closed set;
DEGENERATE is a subkind — translated always, voiced never) ·
projection (what an output column IS; rides 2b) · grouping
(GROUP BY/HAVING; shapes grain) · window (ORDER BY/TOP/window
functions; shapes which rows) · combination (UNION w/ dedup flag)
· reference (operand meanings — the R5 material as nodes) · gap
(counted, reason-coded).

### 2e — meaning identity: the content_key
**RULED (2026-09-06) — the boundary that decides when a
certification survives.** Definition: content_key =
hash over (kind, operand identities resolved to KG1 ids or scope
paths, literal values, children's content_keys, join kind).
INVARIANT to: formatting/whitespace · alias names · AND-order and
join order (the _content_key commutativity lineage) · comment
changes. SENSITIVE to: any column, operator, literal value, join
kind, or structural change. Consequence: a
reformat or alias rename costs zero governance; changing `24` to
`48` in the readmit window orphans the certification — visibly.

### 2f — KG3: the merged governance overlay (rider R-2 lands here)
Artifact_Layer_Registry + Concept_Layer_Registry merge into ONE
Governance_Layer_Registry. Citizen classes, each keeping its
ratified rules: description · term · responsibility
(state-shaped) · disposition · usage event · proposal
(event-shaped, append-only) · identity (person|role|agent, thin
Entra proxy) · **concept** (human-mint-only, append-only,
nameless — the term carries the name — basis snapshot; its
about-edges now target a SET of meaning anchors: the family).
THE ANCHOR RULE: `about` targets a meaning identity — a KG2b
content_key at a scope path, or a KG1 object — NEVER a node
instance, NEVER a KG2a syntax node. Corollaries (S1/S2 demoted
from rules): same content_key after regeneration → artifact
survives silently; changed → artifact flags as orphaned (drift);
deleted scope → orphaned with similarity candidates. The
non-regenerable law and the about/author/derived-ownership spine
are unchanged.

---

## Piece 3 — BUILDERS AND READINGS (the lens stratum RETIRES —
## re-ruled in Sunny's review, 2026-09-06)

The review caught the holdover: once KG2b is stored graph,
"translation is a lens" contradicts the lens law itself (lenses
write nothing — the translator's whole job is writing KG2b), and
once meaning lives in the graph, most remaining lenses are
queries. The stratum dissolves into two thin CONTRACTS: builders
write the graph; readings consume it.

### 3a — the three builders (the "translation lens" becomes the
### TRANSLATOR)
parser : KG2a :: translator : KG2b — the translator is the
parser's twin, the second builder, never a lens. The builder
contract (all three: loader → KG1 · parser → KG2a · translator →
KG2b):
- deterministic; if it needs a model it is not a builder step
- versioned; stamps every node it writes (the parser already
  does — parsed_at + parser/metamodel versions; the translator
  stamps translator version + basis)
- writes ONLY its own layer; total over its input with counted
  gaps (conservation at each door)
- version bump → rebuilds everything it governs (the RULE path
  of the change quanta, 5a)
Governance has NO builder: KG3 accretes by human acts and gated
machine proposals only.
Translator specifics: reads KG2a + KG1 (declared, closed); builds
ONE MEANING TWIN PER FILE (the 2c node family); completeness =
the conservation equation; its version stamps into every produce
basis (bump → every floor-derived artifact stale, standing
mechanism).

### 3b — KG2b storage laws (the "shadow" concept DISSOLVES —
### KG2b IS the stored meaning graph)
There is no separate cache to name: the L0 already calls KG2 the
DERIVED layer — derived, stored, regenerable. The former shadow
conditions transmute into KG2b's build laws: rebuilt at the file
quantum — a changed file's meaning rows replaced whole, never
patched at sub-file grain; a version bump rebuilds the whole
estate · every row stamped run_id + translator version; a stamp
mismatch is unreadable, never silently served · KG2b is
regenerable BY DEFINITION — the translator is the definition of
meaning; governance mints only by citing stamped graph state.
"No history, stamps mandatory" — never "no versioning."

### 3c — the readings (the former lens catalog)
THE SURVIVAL PRINCIPLE (ruled in review 2026-09-06): a reading
exists iff its yield is ABOUT the graph for one consumer —
status, aggregation, comparison — never meaning itself; the
translator absorbed everything that was secretly computing
meaning. The reading contract is deliberately thin: named,
versioned, deterministic, writes nothing. It is kept ONLY for
citability — dispositions and concept bases quote reading output
by version — not because readings need a stratum to live in.
Most demote to versioned QUERIES/views over edges that now
exist; relatedness is the one genuinely computed reading left.
- decisions(class): RETIRED — subsumed by the translator
- degenerate: RELOCATED — the condition subkind (2d)
- concept-drift + divergence: anchor-mismatch queries (2f)
- gap-census: gap-node counting queries
- staleness: stamp-arithmetic queries (KG1 object grain included)
- ownership · authorship · version · standing · current-outcome:
  event-derivation queries (their ratified rules unchanged)
- expertise · blast-radius · working-set · referenced-keys:
  traversal/aggregation queries
- join-compliance: comparison query — KG2b source nodes vs KG1
  declared paths
- relatedness: COMPUTED reading over KG2b content_keys (feeds
  concept minting; keeps a full contract entry)

### 3d — search (a service traversal, never a lens)
Search is a flow-level service: traversal over KG2b + KG1 + KG3,
covering resolved edges AND unresolved references BY NAME — drift
refs (SQL reading columns that don't exist) stay findable. The
lineage guarantee's "never silently absent" is enforced here, not
assumed.

---

## Piece 4 — VOICING POLICY (Floor Grammar, next MAJOR version)

4a. The grammar becomes the POLICY WALK over the meaning twin: it
selects which meaning nodes print and composes their content —
it never creates meaning, and it SELECTS, never compresses: a
voiced node renders exactly by its total rule; accuracy risk
lives only in omission. THE VOICING LEDGER (ADR 0044 clause 5,
generalized to the meaning tree): every meaning node in a voiced
surface's scope is VOICED or COUNTED — voiced ∪ unvoiced ==
total, disjoint, queryable — silent omission has no constructible
path, and every omission traces to a policy line or a gap-census
row (the error-contract law: "why isn't X mentioned" always has a
citable answer). R2's spine ("one bullet per membership
decision") becomes "one bullet per condition node the policy
selects." The LLM's seat is unchanged and caged: SMOOTHING only —
fixed task, exact floor text in, natural prose out, mechanically
gated against the typed facts; on gate failure the floor ships
(an outage costs polish, never truth). The LLM never selects:
selection is where omission-skew lives, and a model's omissions
have no mechanical check.

4b. Survives nearly verbatim (they were secretly node translations
all along): R3 shape preservation · R4 predicate voicings · R5
operand words (now the content of reference nodes) · R6 (now:
degenerate nodes translated, policy-silenced) · R8 annotations
with attribution · v1.1.0 dedup (predicate-identity grain ==
content_key grain — the same idea, now first-class) · v1.3.0
inner/outer posture (INNER residues voice as membership; OUTER
residues are match conditions).

4c. The composition sentence (the R9 corpse-fix) is the policy
walk over a scope's SOURCE nodes: first FROM ref, then each join
voiced as restriction (INNER) or optional match (OUTER); named
scope refs voice as reference phrases (readable name + grain,
counted naming gap); **RULED (Sunny, 2026-09-06):** anonymous
derived-table scopes inline at depth 1 only; deeper nesting
counted in gap-census with the revisit trigger declared.
Translation stays total regardless — the cap is on prose.

4d. **RULED (2026-09-06) — the scope-chain story.** The dissolution:
the staging chain ("#A feeds #B feeds the result") IS meaning —
dependency edges between selection nodes exist in KG2b by
construction — and how much of the chain a summary NARRATES is
voicing policy (default: each scope names only its direct
sources; the full chain is a traversal, not a paragraph).

---

## Piece 5 — THE FLOWS

### 5a — inbound (build the graph)
ingest → parse (KG2a) → resolve (against KG1; unresolved counted)
→ translate (the translator BUILDS KG2b), SAME RUN, atomic — a
run that fails mid-way leaves no readable half-state (the stamp
check guarantees it) → voice per policy → land artifacts.
KG1 intake goes INCREMENTAL: hash-diff per object; only changed
objects write; equivalence is MECHANICAL, never trusted — a
scheduled full parallel load compares against the incremental
state and any delta is a counted finding (5-rule gate:
mechanically enforced).
THE CHANGE QUANTA (ruled 2026-09-06 in review: CHANGES trigger
updates — total reload retires as the DATA path but stays as the
RULE path): KG1 — object grain (hash diff). KG2 — FILE grain: a
file re-parses and retranslates only when its content hash
changed; plus the dependency ripple — a changed KG1 object
retranslates only the meaning nodes drawing from it (the
draws_from edges make this mechanical). KG3 — never regenerates;
after any KG2b change its anchors re-check by content_key
(survive silently or flag as drift). RULE changes are the
exception BY DESIGN: a metamodel/translation/grammar version bump
regenerates EVERYTHING it governs — partial regeneration under a
new rule would let dead-rule output linger beside new output (the
grandfathering hazard in pipeline form). H8's budgeted queue
paces both paths.

### 5b — outward (serve the catalog)
Publish reads KG2b + the KG3 overlay. Catalog metadata
stays stamped and regenerable; human-owned artifacts are never
overwritten (unchanged law).

### 5c — inward (serve inquiries)
Match runs against KG2b — meaning, never syntax (the L0
commitment). The honesty floor and agent-loop laws are UNTOUCHED
by this ruling. Generation, when no estate answers, exits through
the parser door and re-enters as estate: parsed, twinned, voiced,
governed — one door, no exceptions.

### 5d — phasing
**RULED (2026-09-06).** Each phase ships real ED-sepsis output
for Sunny's gap-check (the standing acceptance law):
- Phase A: metamodel bump + A12 projection re-parse (KG2a
  complete; nothing downstream changes yet)
- Phase B: the translator + stored KG2b + conservation equation
  green over the sepsis corpus
- Phase C: voicing-policy port (Floor Grammar major) + full
  gap-check rerun as acceptance — findings 3/4 corpses become
  standing tests
- Phase D: governance registry merge + anchor migration
  (existing artifacts re-anchored by content_key; orphans from
  the migration are FINDINGS, not errors)
- KG1 incremental intake (R-1) is independent — can land any
  time after A.

---

## Piece 6 — STRATA NAMING + supersession/staleness ledger

### 6a — strata naming (Sunny's 09-06 question; AMENDED when the
### lens stratum retired in review — piece 3)
**RULED (2026-09-06): rename, don't collapse.** Strata and KG
numbers encode DIFFERENT laws — strata are consumption order (the
import law, plank-checkable), KG numbers are data anatomy. The
numbering collision ("Level 2" vs "KG2") dies with the digits:
strata become **Blueprint · The Graph · The Flows**; digits go
KG-exclusive (KG1/KG2a/KG2b/KG3). Builders and readings are
CONTRACTS riding the strata, never strata themselves. The import
law restates as: The Flows write The Graph only through builders
and read it only through readings; readings write nothing; The
Graph references only itself and its sources.

### 6b — superseded on ratification
decisions(class) flat yields (3a) · the degenerate standalone
lens (3c) · R9 DRAFT as standalone rule (4c; Floor_Grammar.md
already marked superseded-pending) · the A12 projection deferral
(2b) · KG4 as a separate layer (2f) · S1/S2 as rules (now
corollaries, 2f) · "per-file semantic trees" as a name (Piece 1)
· KG1 full-reload as the intake mode (5a) · THE LENS STRATUM
itself (piece 3: builder + reading contracts replace it; the
"translation lens" becomes the TRANSLATOR, a builder) · the
"shadow" as a concept (KG2b is the stored meaning graph, 3b).

### 6c — unchanged, in force
the parsed tree + conservation · reading determinism +
writes-nothing (the former lens law, renamed)
· the concept class's four rules · all v1.1.0–v1.3.1 truth
rulings · the steward-voice ban on raw identifiers (it governs
VOICING, where it always belonged) · honesty floor + agent loop ·
Entra as identity authority · human-owned artifacts never
overwritten · the parser door as the only entry.

### 6d — staleness on ratification
metamodel bump (2a/2b) + translation lens v1 (3a) + Floor Grammar
major (4) — every floor-derived artifact regenerates via the
standing mechanism; the anchor migration (5d Phase D) re-attaches
governance by content_key and reports orphans as findings.

---

## THE RULED REGISTER (all calls RATIFIED 2026-09-06 — "all
## good, go with your recommendations")
- **OPEN-0 → RULED** strata rename-not-collapse: Blueprint · The
  Graph · The Flows; digits KG-exclusive (6a)
- **OPEN-1 → RULED** content_key boundary as drafted (2e) — the
  law of when certifications survive
- **OPEN-2 → RULED** the nine meaning kinds (2d)
- **OPEN-3 → RULED** chain is meaning, narration is policy,
  direct-sources default (4d)
- **OPEN-4 → RULED** phasing A→B→C→D, sepsis gap-check gates
  each (5d)
- **O-L0-3 → RULED** the figure stays
