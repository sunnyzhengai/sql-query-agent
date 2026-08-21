# Φ_AIVIA — The Shadow Specification

**Version:** 0.6 (adopted; ADR 0047, extended by ADR 0048, 0051; §3b ratified by ADR 0052, first live use: the reachability contract)
**Date:** 2026-08-19 (v0.5: 2026-08-21)
**Origin:** review session with Sunny; motivated by three recurring deviation
classes discovered by code-walking: (1) missing EMR join edges — the technical
layer was not the complete vendor join map; (2) LLM components repeatedly
drifting into retrieval/query decisions; (3) collaborators defaulting back to
regex/sqlglot after ScriptDom was settled. v0.2 adds the findings of the
first blind round-trip review (Sunny reconstructed the system in her own
words; mismatches against v0.1 became axioms C4, E5, E6, D3, the T_org sort,
and §13) — see Changelog.

---

## 1. What this document is

This is the **theory** the system is supposed to be a model of — a shadow
design that lives beside the code. It has three properties the ADRs alone
don't:

1. **It is closed.** The ADRs record decisions as they were made; this spec
   states the *complete* set of laws in one place, so an absence (a missing
   axiom, a missing extraction source) is visible as a gap in a finite list,
   not as a surprise found by reading code.
2. **Every axiom binds to a mechanical check.** Same doctrine as the tree
   contract (ADR 0044) and notebook contract (ADR 0042): intentions decay
   under pressure; only enforcement survives. An axiom without a check is
   marked UNBOUND and is a known debt, never an implied guarantee.
3. **Correctness is one judgment.** The pipeline's validation gate checks
   `G ⊨ Φ_data` (the data satisfies the data axioms); CI checks
   `Code ⊨ Φ_code` (the codebase satisfies the code axioms). "Drift" is a
   named axiom violation with a citation — never a feeling.

Relationship to ADRs: each axiom cites the ADR(s) it formalizes. Changing an
axiom requires an ADR (the amendment rule). The ADRs are the changelog of
this theory.

Citation handle: `spec:<axiom-id>` (e.g. `spec:C1`), the ADR 0039 pattern
applied to the spec itself.

---

## 2. Reading the notation (a 2-minute primer)

| Symbol | Read as | Example |
|---|---|---|
| `∀x. P(x)` | "for all x, P holds" | `∀m. id(m) is unique` |
| `∃x. P(x)` | "there exists an x such that P" | "a witness exists" |
| `A → B` | "if A then B" | violation → reject |
| `A ⟺ B` | "A exactly when B" (both directions) | accept ⟺ trees match |
| `A ⊆ B` | "every element of A is in B" | image lands in graph |
| `A ⊎ B` | disjoint union — a **partition**: everything is in exactly one side | handled ⊎ fallout |
| `f : X → Y` | f is a **function** from X to Y: every x gets exactly one y | one owner per capability |
| `∘` | function composition | fold∘fold |
| `lfp` | least fixpoint — "keep applying the rule until nothing new appears"; how transitive closure is defined | closure = lfp |
| `G ⊨ Φ` | "G models Φ" — the structure G satisfies every sentence in Φ | validation = model check |
| `dom(f)` | the domain of f (its inputs) | dom(extractor) = source rows |
| `∖` | set difference ("minus") | `Uses ∖ S = ∅` means no unsanctioned use |

Everything below uses only these. Each formula carries a plain-language gloss;
the formula is the law, the gloss is the teaching aid.

---

## 3. Status vocabulary

| Status | Meaning |
|---|---|
| **ENFORCED** | a passing mechanical check exists today (file cited) |
| **GATED** | check exists as a strict-xfail skeleton (ADR 0044 pattern) — red by design until its phase ships; flipping the marker is the exit gate |
| **PARTIAL** | enforced for some instances, not all — the gap is stated |
| **UNBOUND** | axiom is agreed doctrine; no mechanical check yet — a named debt |

An UNBOUND axiom is a **proposal to the dev session**: adopting the spec means
either building its check or demoting it explicitly.

---

## 3b. The design-review clause (the three questions)

**Mandated by Sunny, 2026-08-21.** Every NEW artifact class — a
registry, a projection, a tool surface, a prompt surface, an export,
a graph layer, any subsystem that produces or consumes governed
artifacts — MUST answer the three questions **before its first line
of code**, and the answers become its registry rows:

1. **The inventory question (spec:C1 shape).** What is this thing's
   complete frontier, enumerated as data? What is the exclusion row
   for everything deliberately outside it? ("Nobody decided that; it
   just happened" is only possible for an artifact class never asked
   this question — the EMR-joins incident and the 7%-reachability
   incident were both question-1 omissions.)
2. **The conservation question (spec:C2 shape).** What equation proves
   nothing vanished between input and output —
   `handled ⊎ fallout = total`? Where do the fallout rows land?
3. **The drift question (STPA shape).** When reality diverges from the
   declaration, what MECHANICALLY fires — a red build, a checklist
   row, a funnel bar? "Someone would notice" is the definition of a
   missing feedback loop.

Enforcement: a design review that cannot cite the three answers does
not proceed to implementation; the answers are recorded as rows in the
relevant registry (or a new registry born from question 1), so the
declaration is data from day one. Prior art for this clause:
IEC 62304 / DO-178C traceability + coverage analysis, and STPA's
control-loop hazard questions — see docs/METHODOLOGY.md, "The
enforcement lineage."

---

## 4. The signature Σ (the vocabulary of things)

**The layers, pinned to the codebase's vocabulary** (ruled by Sunny
2026-08-19 — one name set for humans, ADRs, and code):

| Layer | Node sorts | Whose reality |
|---|---|---|
| **technical** | Table (= T_D ∪ T_org), Column | the vendor's (EMR dictionary) + org reference tables |
| **transformation** | Step (CTE/temp-table logic), Site (decision site) | organizational logic, decomposed |
| **canonical** | Metric (proc/view deliverables) | the organization's certified definitions |
| **consumption** | Report, Measure (DAX) | how the org consumes logic (ADR 0040) |
| **governance record** | Term (+ gated future: Conversation/Turn/Verdict, ADR 0038) | human-owned truth in gov tables; Term projection into the graph is PENDING (audit find 2026-08-19 — see EXTRACTION_REGISTRY `business_terms` exclusion) |

**Sorts:**

    Values:   Ident, SQL, DAX, Tree, Desc, Hash
    Nodes:    Table, Column, Step, Site, Metric, Report, Measure, Term
    Records:  SourceRow, FalloutRow, Event (append-only)

`T_org` (org-created reference tables: value sets, control parameters) is a
**distinguished subsort of Table**, new in v0.2: it is not witnessed by the
vendor dictionary. Declaration vehicle (ruled at adoption): the `ORIGIN`
column on `input_dict_tables` (vendor|org, NULL = vendor) — one lookup
surface for C4, with the sort distinguished for E5.

**Functions:**

    fold : Ident → Ident          identifier case-folding (ADR 0016)
    hash : SQL → Hash             content identity (ADR 0022)
    κ    : Tree → Tree            canonicalization for tree comparison (ADR 0044)
    id   : Metric → Ident         metric_id = schema.object (ADR 0015)

**Edge relations** (illustrative core; the full list is TABLE_REGISTRY's
edge-table contracts — the registry is the authoritative Σ at column grain):

    joinable ⊆ Table × Column × Table × Column     the vendor join map (PK→FK)
    dep      ⊆ Step × Step                          DEPENDS_ON
    reads    ⊆ Step × Table                         READS_FROM
    calc     ⊆ Metric × Step                        CALCULATED_BY
    uses     ⊆ Metric × Table                       USES_TABLE (derived)
    sites    ⊆ Site × Column                        decision site → column
    r2c      ⊆ Report × Metric                      report_to_canonical (0..n per report)
    r2t      ⊆ Report × Table                       report_to_technical (DirectLake)
    r2m      ⊆ Report × Measure                     report_to_measure
    m2c      ⊆ Measure × Column                     measure_to_column
    implements ⊆ Term × (Metric ∪ Step)             gov_term_links (projection PENDING — audit find)

**Reference structures** (the sources, outside the graph):

    D = (T_D, C_D, J_D)     the vendor dictionary: tables, columns, join map
                             (join edges are witnessed by (PK, FK) pairs)
    P                        the parsed SQL corpus (ScriptDom ASTs)
    M                        the TMDL/M corpus (semantic models)
    O                        org declarations: T_org reference tables, config
    Gov                      governance record tables (terms, assignments,
                             events) — durable, never overwritten by builds

The graph **G** is a Σ-structure built from D, P, M, O, Gov. The spec Φ is
the set of sentences below. The system is correct when `G ⊨ Φ`.

---

## 5. Group A — Identity (equality axioms)

**A1 — folding is idempotent.**

    ∀x ∈ Ident.  fold(fold(x)) = fold(x)

*Gloss:* folding twice changes nothing — so it never matters how many times a
value has been folded before matching.
*Origin:* ADR 0016. *Binding:*
`tests/parser/test_identity.py::test_fold_is_idempotent` (added at
adoption — the v0.2 label cited a test that did not exist; audit find).
**Status: ENFORCED**

**A2 — metric_id is a key.**

    ∀m, m′ ∈ Metric.  id(m) = id(m′) → m = m′

*Gloss:* two metrics with the same id are the same metric, everywhere,
including every downstream projection (Purview qualifiedName, exports).
*Origin:* ADR 0015. *Binding:* `unique` invariants in TABLE_REGISTRY, checked
by `tests/test_invariants.py` / `test_table_contracts.py`. **Status: ENFORCED**

**A3 — fold-collisions are rejected loudly.**

    ∀s, s′ ∈ SourceRow.  fold(name(s)) = fold(name(s′)) ∧ s ≠ s′  →  reject(load)

*Gloss:* two inputs whose identities differ only by case are one object in a
case-insensitive database — a data error, never two entries.
*Origin:* ADR 0016. *Binding:* fold-case unique invariant
(`test_fold_case_unique_catches_case_variant_duplicates`). **Status: ENFORCED**

---

## 6. Group B — Soundness (nothing exists without a witness)

**B1 — witness totality (the anti-fabrication axiom).**

    ∀e ∈ E_G.  ∃w ∈ D ∪ P ∪ M ∪ O ∪ Gov.  justifies(w, e)

*Gloss:* every edge in the graph traces to a source fact — a dictionary row
(join edges: a (PK, FK) pair), an AST node, a TMDL partition, an org
declaration, a governance record. No edge is ever asserted from model memory
or heuristic guess. (Refuse-over-guess, ADR 0005, stated as structure.)
*Origin:* ADRs 0005, 0032, 0044. *Binding:* `reference` invariants +
deterministic builders (03 builds only from parsed inputs); ADR 0044 clause 1
is B1 for decision sites. **Status: PARTIAL** — holds by construction for
edges built in 03; not yet a uniform declared invariant on every edge table.
Debt: every edge-table contract declares its witness reference.

**B2 — description provenance is total and closed.**

    ∀d ∈ Desc.  provenance(d) ∈ {round_trip_verified, template_fallback, flagged}

*Gloss:* no description exists without a stated epistemic status; no fourth
value; no NULL.
*Origin:* ADR 0044 clause 6. *Binding:* `verified_describe` returns only
the closed set (clause 6 gate green, 1.32.0). **Status: PARTIAL** —
stated gap: provenance persistence on stored descriptions lands with
600's phase-3b wiring.

---

## 7. Group C — Completeness (relative to a declared frontier)

> The group that would have caught the missing EMR joins. Absolute
> completeness is unprovable; completeness **relative to an enumerated
> inventory** is a checkable equation. The inventory converts "did we think
> of it?" from an unbounded worry into a one-page review.

Declare an **extraction-functor inventory**: one row per source kind k with
its extractor F_k : R_k → G (or an explicit exclusion). Proposed home:
`EXTRACTION_REGISTRY` in src/, a peer of TABLE_REGISTRY / NOTEBOOK_REGISTRY /
SHAPE_REGISTRY.

**C1 — the frontier is enumerated (no undeclared source kind).**

    ∀k ∈ SourceKinds.  (∃ F_k)  ∨  (∃ exclusion(k))

*Gloss:* every kind of source fact — dictionary join rows, dictionary
descriptions, SQL decision sites, TMDL partitions, DAX column refs, org
reference tables — either has a declared extractor or a recorded
"deliberately not extracted, because…". There is no third state ("nobody
thought about it").
*Origin:* the EMR-joins incident: `J_D` (the dictionary's join map) had no
functor and no exclusion — the violation existed at the inventory level
before any code ran, which is why only a code-walk found it.
*Seeded exclusion rows (ruled by Sunny 2026-08-19):* Snowflake views and
Databricks/dbt models are **excluded for the Fabric-native v1** — real
hospital estates increasingly run them, so the rows exist to make the
roadmap pressure visible, per ADR 0001 each future dialect gets its own
native parser. **Status: ENFORCED** — `src/extraction_registry.py` +
`tests/test_extraction_registry.py` (functor XOR exclusion per row;
conservation citations resolve; the joins incident pinned as the
acceptance test; every reference structure D/P/M/O/Gov covered).

**C2 — conservation per extractor (no third bucket).**

    ∀k.  dom(R_k) = handled_k ⊎ fallout_k

*Gloss:* every source row is either extracted or counted as fallout — the sum
matches the total, and nothing vanishes.
*Origin:* ADR 0044 clause 1 (decision sites: `handled + unextracted == total`),
ADR 0041 (M shapes), ADR 0045 (fallout resolution). *Binding:*
`tests/test_tree_contract.py` clause 1 (**green, 1.26.0**); `ops_fallout`
writers; shape-census fixtures. **Status: PARTIAL** — enforced for trees and
M shapes; C1's registry (now ENFORCED) carries a conservation citation per
row and the citations are checked to resolve — full per-row equation
checks remain the stated gap.

**C3 — images land in the graph.**

    ∀k.  F_k(handled_k) ⊆ G

*Gloss:* what an extractor extracts actually arrives — no silent drops between
extraction and the graph.
*Binding:* postcondition gates + count-equals-relation invariants
(`test_count_equals_relation_*`). **Status: PARTIAL** (same universality note
as C2).

**C4 — leaf grounding (the termination axiom).**

    ∀f ∈ P.  ∀ℓ ∈ leaves(tree(f)).   ℓ ∈ T_D ∪ T_org   ∨   ℓ ∈ fallout(f)

    completely_parsed(f)  ⟺  fallout(f) = ∅

*Gloss:* after internal references resolve (CTEs and temp tables resolve to
their defining steps), every remaining leaf of every parsed tree must bottom
out on a vendor table or an org reference table. Anything else — an
unresolvable name, a dynamic-SQL branch — is counted fallout, and
"completely parsed" is a **computed per-file verdict**, never an impression.
Gives the funnel a new honest number: fraction of files fully grounded.
*Origin:* Sunny's blind reconstruction, 2026-08-19 ("any AST tree branch that
does not end in EMR tables or org's custom reference table is not a
completely parsed sql file"). **Status: ENFORCED** —
`src/governance/leaf_grounding.py` (verdict + fraction + escalated
fallout, stage `500_leaf_grounding`), wired into 500;
`tests/governance/test_leaf_grounding.py`. First recorded-corpus verdict:
27/28 files completely parsed (USP_Severe_Sepsis reads 6 tables absent
from the dictionary — the number is already working).

**THE GRAPH IDENTITY THEOREM** (what B and C jointly force):

    G  =  ⋃_k F_k(handled_k)

*Gloss:* the graph is **exactly** the union of the declared extraction images —
no more (soundness: B1 forbids unwitnessed edges) and no less (completeness:
C1+C3 over the whole inventory). "Complete knowledge graph" now has a
definition: it is this equation, checked against the inventory. The technical
layer being "the vendor's complete join map" is the k = J_D instance.

---

## 8. Group D — Derived structure (fixpoint and projection correctness)

**D1 — materialized closures equal the fixpoint.**

Datalog definition (the rule applied until nothing new appears):

    reach(x,y) ← dep(x,y)
    reach(x,z) ← reach(x,y) ∧ dep(y,z)
    uses(m,t)  ← calc(m,s) ∧ reach(s,s′) ∧ reads(s′,t)

    Axiom:  uses_materialized = lfp(uses)

*Gloss:* the precomputed USES_TABLE / closure edges must equal what a live
traversal would compute. The closure is a **cache with a proof obligation**,
not a second truth.
*Origin:* ADRs 0018, 0033, 0037 (closures reclassified as checkable cache;
the 5-of-13 undercount was an unstated D1 violation). *Binding:* count
oracles pin known instances; the general closure-vs-live-traverse consistency
diff is planned (ADR 0037). **Status: PARTIAL** (oracles ENFORCED; general
diff UNBOUND).

**D2 — count oracles.**

    |{m : uses(m, HOSPITAL_ENCOUNTERS)}| = 13,   … (fixture constants)

*Gloss:* certified cardinalities from recorded fixtures pin the truth; a
derivation change that alters a known count is a red build, never a silent
undercount.
*Origin:* ADR 0018. *Binding:* recorded-fixture count-oracle tests.
**Status: ENFORCED**

**D3 — projections are functions of the record.**

    ∀ projection Π ∈ {LPG export, Eventhouse catalog, term nodes,
                      usage-layer edges, Fabric Graph read model}.
        Π = f_Π(Record),   f_Π deterministic and recomputable

*Gloss:* no projection carries information absent from the Delta record;
every projection can be rebuilt at will and can never drift into a second
source of truth. This is why business terms live in `gov_business_terms`
(durable, human-owned) and are *designed to be projected* into the graph
each build — the graph is overwritten every run, so anything living only
in it would be destroyed. AUDIT FIND (2026-08-19): the Term projection is
not yet implemented (no Term nodes, no implements edges) — recorded as an
EXTRACTION_REGISTRY exclusion until the builder lands; the gov record and
candidate mining exist.
*Origin:* ADRs 0031, 0033, 0038 (usage-layer discipline). *Binding:* by
construction in the builders; no general recompute-and-diff check yet.
**Status: PARTIAL**

---

## 9. Group E — Ask-time determinism (anchor → discover → match → rank)

**E1 — the path space is finite and enumerable.**

    G_tech finite ∧ static
      ⟹  Paths_k(A) = { walks of length ≤ k over joinable, connecting A }
          is finite and mechanically enumerable, for any anchor set A

*Gloss:* the vendor's join map is a known, finite structure. Given anchored
nodes, all candidate paths between them are **facts waiting to be
enumerated** — a search problem, not a synthesis problem. Nothing needs to
"generate" a path, so nothing stochastic may.
*Origin:* ADR 0046 (Sunny's position, settled 2026-08-19).
**Status: PARTIAL** — the deterministic primitive is ENFORCED
(`src/discovery/paths.py` + `tests/test_spec_gates.py`, 1.33.0:
replay-deterministic simple-path enumeration over the join map, both
orientations, hop-capped presentation-never-pruning). Stated gap: the
composed 0046 engine (anchor→discover+match→rank→pick) is not built.

**E2 — replay determinism for retrieval components.**

    resolve, discover, rank are functions:
      same (token, catalog_state)  ⟹  byte-identical output

*Gloss:* an LLM fails this **by construction** (it samples) — so it is
excluded from these seats by type, not by policy. The recurring "should the
LLM help compose the query" debate terminates here: the component violates E2.
*Origin:* ADRs 0032 (the testable definition of deterministic), 0046.
*Binding:* replay property in CI for the orchestrator's resolve path
(ADR 0032: "replay stable 7/7"); extends to discover/rank with the 0046
engine. **Status: PARTIAL**

**E3 — the decision typing rule (which decider is legal where).**

    decider(d) may be an LLM
      ⟺  codomain(d) is language  ∨  ground_truth(d) is human intent
    a right answer computable from data  ⟹  decider(d) must satisfy E2

*Gloss:* three kinds of decision — computable (code only), judgment (human),
linguistic (LLM). An LLM decision is acceptable only where its error mode is
visible and bounded. You TEST code; you can only MEASURE models.
*Origin:* ADR 0035 (the taxonomy), 0032, 0046. *Binding:*
`tests/test_methodology.py` (control ops registered and justified;
question-shaped names banned in the control path; language patterns banned in
control files). **Status: ENFORCED** for the control path; each new component
declares its decider kind at review.

**E4 — pick containment (the human picks, structurally).**

    pick_human(S) ∈ S        and  no auto-pick:  |S| = 1 does not bypass

*Gloss:* the chosen candidate must be one of those presented — enforced by
code, so a silent top-1 pick or an out-of-list answer is impossible, not just
discouraged. One candidate is treated the same as ten.
*Dependency:* the human picks **by reading descriptions** — so Group F is
load-bearing for E4: a fabricated description corrupts the pick. This is the
formal reason ADR 0044 had to precede ADR 0046.
*Origin:* ADRs 0032, 0046 (reaffirmed in strongest form). *Binding:*
structural pick validation in the orchestrator. **Status: PARTIAL** (enforced
where the orchestrator surface runs; the 0046 engine re-binds it).

**E5 — filter grounding (the 123/456 lesson).**

    ∀v ∈ FilterValues(answer ∪ executed SQL).
        v ∈ Sites ∪ ValueSets ∪ HumanInput

*Gloss:* every literal value in any presented or executed filter comes from a
stored decision site, a value-set table (T_org), or the human — never from
model memory. Carries the shared-schema/varying-values fact: the EMR schema
travels between hospitals; the values never do.
*Origin:* ADR 0046 grounding rules; ADR 0044's captured fabrications.
**Status: PARTIAL** — the deterministic primitive is ENFORCED
(`src/discovery/grounding.py`, 1.33.0: refuse-over-guess on any value
without a source). Stated gap: binds to real presented/executed filters
when the 0046 engine composes them.

**E6 — presentation honesty.**

    rank PRESENTS, never prunes (caps are disclosed)
    displayed signals ∈ { closeness (relative), usage weight (derived),
                          certification status }
    probabilities are banned display vocabulary

*Gloss:* "confidence" in conversation always means derived edge/usage
weights — never a probability the model invented. Closeness is relative
geometry, not a likelihood.
*Origin:* ADRs 0032 (threshold is a volume control), 0046 (ranking presents,
never prunes). *Binding:* the fixed render template + basis stamped by code
(`tests/orchestrator/test_core.py::test_basis_is_stamped_by_code`).
**E6 amendment (2026-08-20, Sunny's verdict via the review session —
stamp, don't audit):** the quantitative/existential sentence on every
result panel is the STAMPED HEADLINE — rendered by code from the
result's own typed metadata (count, scope, completeness, kind-vs-name
redirect), the ADR 0032 provenance pattern. The LLM caption is
commentary beneath it, visually subordinate; a lying caption is not
caught, it is contradicted on screen. Guarantee: no quantitative or
existential claim reaches the user only through LLM prose.
**Status: ENFORCED** (plan surface) —
`src/orchestrator/caption_gate.py::stamped_headline`, stamped at the
protocol layer onto every result; fixture = the 2026-08-20 transcript
("no metrics available" over a names-only empty result). The caption
LINT (claim-shape checks + template floor) is retained as
defense-in-depth and classified MEASURED, not tested — a lexicon
cannot bound English (the ADR 0036 rejection stands); no soundness
claim rests on it. Stated residue: the superseded agent-loop surface
(ADR 0035) is unstamped pending its demolition.

---

## 10. Group F — The round trip (ADR 0044 as equations)

    desc  = τ(facts(tree), dict)          τ = translator;  SQL ∉ inputs(τ)
    tree′ = ρ(desc, dict)                 ρ = verifier;    SQL, tree ∉ inputs(ρ)
    ACCEPT(desc)  ⟺  κ(tree′) = κ(tree)   κ and = are deterministic code
    after N rejections:  desc := τ₀(tree),  provenance := template_fallback

*Gloss:* the translator renders typed tree facts (never raw SQL) into prose; a
blind verifier reconstructs a tree from the prose alone; a deterministic judge
compares canonicalized trees; exhausted retries degrade to the stilted-but-true
template. The blindness clauses are **information-flow constraints**: the SQL
is not merely ignored — it is unreachable from the function's inputs
(enforced at the signature, the noninterference trick).
*Origin:* ADR 0044 clauses 2–6. *Binding:* `tests/test_tree_contract.py`
(prompt-capture + signature + AST planks + never-converging acceptance test).
**Status: ENFORCED** (all six clause gates flipped 1.31.0–1.32.0:
src/tree/{translate,render,verify,diff,pipeline}.py; live round trips
verified on real steps). Stated gap: 600's production wiring of the
verifier (reconstructor callback + provenance persistence) is phase 3b.

---

## 11. Group G — Mechanism uniqueness (the codebase axioms)

> The group that ends "two tools for one job." These axioms are about the
> CODE, not the data; their model checker is CI reading the AST.

Declare a **capability-ownership registry**: `own : Capabilities → Modules`,
plus per-capability sanctioned primitives `prims(c)`. Proposed home:
`CAPABILITY_REGISTRY` in src/, the fifth peer registry.

**G1 — one owner per capability.**

    own : C → M  is a function            (single-valued: no capability
                                           has two implementing modules)

*Gloss:* the registry itself is the proof — a second row claiming an owned
capability is a registry validation error, caught before any code review.
**Status: ENFORCED** — `src/capability_registry.py` (unique keys, one
owner prefix per row) + `tests/test_capability_registry.py`.

**G2 — sanctioned powers only (import-graph inclusion).**

    Uses ⊆ S,   where  S = { (own(c), p) : c ∈ C, p ∈ prims(c) }
    equivalently:  Uses ∖ S = ∅

*Gloss:* `Uses` = every (module, powerful-primitive) pair actually present in
the code, computed from the AST. `S` = the sanctioned pairs. The check is set
difference = empty. Powerful primitives: regex, SQL/M parsers, LLM clients,
embedding calls, Delta writes.
*Existing instances (the axiom is already real, piecewise):*
- `tests/test_native_parser_law.py` — sqlglot/sqlparse **deleted repo-wide
  and CI-banned** (2026-08-19, Sunny verbatim: "under no circumstances";
  ScriptDom port shipped 1.28.0, HANDOFF_TREE_PHASE_1B). ADR 0001 amended
  same day: the law is total, no fallback zone.
- `tests/test_notebook_contract.py` — regex banned in notebooks; imports and
  entry points whitelisted per NOTEBOOK_REGISTRY.
- `tests/test_methodology.py` — control-path vocabulary and op registration.
**Status: ENFORCED** — the general registry + whole-`src/` inclusion check
shipped at adoption: `test_capability_registry.py::test_g2_sanctioned_powers_only`
computes Uses from the AST and asserts `Uses ∖ S = ∅` for
pythonnet/clr/requests/httpx (+ the absolute sqlglot/sqlparse ban, which
no row may ever sanction).

**G3 — no undeclared power.**

    ∀ use of p ∈ PowerPrims.  ∃c.  p ∈ prims(c)

*Gloss:* every use of a dangerous primitive maps back to a declared
capability — nothing powerful is used "off the books."
**Status: ENFORCED** — same inclusion check (an unowned use fails with
the registry named) + `test_g3_banned_parsers_have_no_owner`.

*Honest residue:* G-group catches the high-risk primitive classes. Two
innocent pure-Python functions independently reimplementing the same logic
(a second fold, a second hash) are not mechanically detectable — mitigated by
owning primitive operations in single modules and by review. Stated so nobody
mistakes the fence for a force field.

---

## 12. Group H — Escalation (no silent residue)

**H1 — fallout resolution is total and closed.**

    resolution : FalloutRow → {auto_resolved, escalated}     (total; no NULL)

**H2 — novelty always escalates.**

    outcome(x) = unknown  →  resolution(x) = escalated

*Gloss:* everything the pipeline cannot resolve is either recovered by the
pipeline or lands on a human's checklist — counted is not the same as owned.
*Origin:* ADR 0045. *Binding:* `tests/test_escalation_contract.py`
(strict-xfail skeletons, 4 clauses). **Status: GATED**

---

## 13. The double-sided function (one law, three instances, two tiers)

The product's two tiers are built from one pair of functions over the same
three-layer structure:

    τ : Tree → Language        render structure into meaning (describe, caption)
    ρ : Language → Tree        translate intent into structure (anchor, propose)

    THE LAW:   κ(ρ(τ(t))) = κ(t)      round-trip identity, modulo canonicalization

The law is instantiated **three times**, at three grains, with three judges:

| # | Instance | τ | ρ | Judge |
|---|---|---|---|---|
| 1 | Descriptions (ADR 0044) | translator | blind verifier | deterministic tree diff (κ-equality) |
| 2 | SQL stitching (ADR 0033, tier 2) | compile fragments → SQL text | parse back through ScriptDom | tree equality (the parser) |
| 3 | Definition creation (ADR 0038, tier 1) | render proposal back for confirmation | user prose → proposed canonical tree | **the human** |

And the tiers are the two directions of one correspondence:

    Tier 1 (metadata):     Question --ρ--> anchors --enumerate/match/rank-->
                           shapes --τ--> captions --human picks--> answer
    Tier 2 (self-service): same prefix, then:
                           picked shape --compile--> SQL --execute--> data
                           --human approves--> stamped canonical

**Tier 2 = Tier 1 + exactly one arrow** (compile∘execute) — ADR 0046's "Pro
adds exactly ONE layer" as a formula. Tier 1 moves structure→meaning; tier 2
moves meaning→structure→data; each direction's correctness is certified by
running the opposite direction. Every human approval in either direction is
an appended Event, which is how the flywheel (ADR 0023) is the same object as
the verification machinery: **verification events ARE governance data.**

---

## 14. The model-checking frame (how it all runs)

    Φ_data = A ∧ B ∧ C ∧ D          checked by the validation gate, per run,
                                     over the actual Delta instance
    Φ_code = E ∧ F ∧ G ∧ H(writers)  checked by CI, per commit, over the AST
                                     and recorded fixtures

- A **release** = both judgments hold: `G ⊨ Φ_data` and `Code ⊨ Φ_code`.
- **Drift** = a named violation, e.g. `⊭ spec:C1 — source kind J_D has no
  functor and no exclusion`. Never again a discovery made by code-walking.
- **Measured vs tested** (ADR 0035): axioms about LLM behavior at the edges
  (translation quality, caption faithfulness) are MEASURED by the robustness
  suite, never claimed as proven. Every axiom above is TESTED (deterministic
  check) except where its status says otherwise.

---

## 14b. The admin Σ-structure (v0.4, ADR 0048)

The same axiom groups admit a **second model**: the admin graph, whose
sorts are the system's own governance artifacts rather than the
customer's data.

**New sorts:** `Contract` (table contracts, TABLE_REGISTRY), `NotebookItem`
(NOTEBOOK_REGISTRY), `Module` (src/ files), `Decision` (ADRs,
TRACE_REGISTRY), `Axiom` (this document's ids), `ErrorEvent`
(ops_installation_errors / ops_runtime_error_events rows),
`ChecklistItem` (ops_human_checklist rows).

**Edges** (all deterministic, registry- or event-derived — spec:B1
applies: every admin edge has a witness row): notebook —produces→
contract; contract —enforced_by→ gate/test; module —implements→
decision; decision —grounds→ axiom; decision —traced_by→ module/test;
error —violates→ contract.

**Laws carried over:** B1 (witness totality — no admin edge without a
registry/event witness), C1 reflexively (the admin graph's source
kinds are the registries themselves, declared in EXTRACTION_REGISTRY),
D3 (the admin graph is a projection, rebuilt from the registries and
event tables each run — never a second truth), H (unresolved admin
findings escalate; an uncited module is a finding, not a warning).

**Bindings:** `src/trace_registry.py` + `tests/test_trace_registry.py`
(decision lineage + three closure checks: totality, existence, single
classification); `src/zones.py` + `tests/test_zones.py` (governed ⊎
internal); `src/admin_graph.py` + `tests/test_admin_graph.py` (the
projection — ops_admin_graph_nodes/edges, written by 500 each run);
`src/companion.py` + `tests/test_companion.py` (diagnosis = a path of
real edges, captioned; narration rephrases, never decides).
**Status: ENFORCED** — stated gap: the companion's conversational
surface (webapp/agent wiring, BYOT narration in production) is not yet
exposed to admins; the deterministic core and CLI are.

## 14c. Group P — the one-mind turn (v0.5, ADR 0051)

The six principles of the merged turn engine, each bound to a check
(instrument: prompt capture — assert what the model MUST see; the
0044 clause-2/3 instrument, inverted):

| axiom | statement | binding | status |
|---|---|---|---|
| P1 | one conversation decides a turn; no separate planner/judge/captioner minds | one EngineSession/history on the ask path; retired-prompt ghost grep (tests/test_turn_engine + methodology scans) | ENFORCED |
| P2 | full tool results enter the SAME history and persist across rounds and turns; compaction degrades oldest to stamped headline + totals, never drops | prompt capture: round-2 request carries round-1 FULL rows; compaction test pins headline+totals survival | ENFORCED |
| P3 | thinking room — no forced tool_choice except the final typed verdict | captured tool_choice per request: None in-loop, forced exactly once | ENFORCED |
| P4 | no question-family casebook anywhere — invariants + tool semantics only | control-path lexicon scan + prompt line budget (auto-discovered SYSTEM_PROMPT) + banned-vocabulary pin + thesis prompt content-hash PINNED (suite refuses to grade a changed prompt) | ENFORCED |
| P5 | honesty at the boundary only: headlines, caption gate, machine-verified evidence-quote verdict, read-only dispatch, write plan-confirm, caps as code | cage tests (gate/verdict/whitelist/caps/anti-flail) | ENFORCED |
| P6 | failure is observation: tool errors return into the conversation; caps bound flailing | cage test: scripted error appears as a tool-result message; turn continues within caps | ENFORCED |

**Interior vs boundary (the E-group note, restated):** which tool,
when to stop, how to compose — linguistic, MEASURED (suite thresholds,
honesty 100% as build-stopper). Everything at the user boundary —
TESTED.

## 14d. Testing strata (ADR 0051)

L0 contracts/kernels — tested, CI. L1 structure & information flow —
tested, CI (prompt capture, AST planks, registry closure). L2
behavior — measured (suite thresholds; honesty 100% is a
build-stopper, not a metric). L3 human acceptance — judged (the
Smartness Walk protocol, internal/docs/SMARTNESS_WALK.md; runs ONLY
after L2 clears). Rules: every new capability declares its checks at
every stratum before shipping (the trace registry carries the
declaration); never measure what you could test; never ask L3 eyes to
discover what L2 should have caught.

## 15. Honest limits

1. **C1 cannot force conception.** The inventory makes "sources we haven't
   thought about" a finite reviewable list; it cannot think of a source for
   you. The human review of the inventory is the residue of the original
   problem — shrunk from a codebase to a page.
2. **G-group's residue** — semantic duplication without powerful primitives —
   is stated in §11.
3. **Correlated LLM errors** in the round trip (translator and verifier
   making mirror mistakes) are rare, not zero (ADR 0044's stated limit).
4. **Dynamic SQL** has no static tree, permanently: a counted, escalated gap
   (C2, C4, H2), never a described guess.

---

## 16. Adoption checklist (for the dev session)

All items executed at adoption (2026-08-19, 1.29.0 — ADR 0047):

1. ✔ Audited; overclaims corrected in v0.3 (A1 citation, E6 gap, Term
   projection pending in Σ/D3).
2. ✔ `src/extraction_registry.py` + tests; joins-incident acceptance test
   pinned; Snowflake/Databricks exclusions seeded.
3. ✔ T_org = `ORIGIN` column on `input_dict_tables` (vendor|org).
4. ✔ `src/capability_registry.py` + AST inclusion test.
5. ✔ ADR 0047.
6. ✔ No UNBOUND axiom remains: C1/C4/G1/G3 bound; E1/E5 GATED
   (strict-xfail exit gates, `tests/test_spec_gates.py`).

**Change discipline:** this file carries a version; tightening an axiom that
governs generated artifacts revs the relevant `*_CONTRACT_VERSION` cache keys
(the ADR 0044 mechanism). Axiom changes require an ADR. Status-label changes
(UNBOUND → ENFORCED) require only the check's file citation.

---

## Changelog

- **0.6 (2026-08-21)** — §3b the design-review clause (Sunny's
  mandate, review-session authored, dev ratifies with the next ADR):
  three questions — inventory, conservation, drift — answered before
  any new artifact class's first line of code; answers become registry
  rows. Prior-art lineage recorded in docs/METHODOLOGY.md.
- **0.5 (2026-08-21)** — ADR 0051 (the one-mind turn): E-group note —
  a turn's INTERIOR decisions (which tool, when to stop, how to
  compose) are linguistic and live in one conversation with full
  evidence; they are MEASURED by the conversation suite (spec:E3
  vocabulary), never prompt-scripted per question family. Boundary
  mechanisms remain TESTED: stamped headlines, caption gate, the
  machine-verified evidence-quote verdict, read-only dispatch,
  round/anti-flail caps (src/orchestrator/turn_engine.py +
  tests/orchestrator/test_turn_engine.py). The three-call protocol
  shape retires; ADR 0050's floors carry over unchanged for writes.

- **0.4 (2026-08-20)** — ADR 0048: the admin Σ-structure (§14b) — the
  admin graph as a second model of the same axiom groups (new sorts:
  Contract, NotebookItem, Module, Decision, Axiom, ErrorEvent,
  ChecklistItem). Bindings shipped: TRACE_REGISTRY (decision lineage,
  three closure checks), declared zones (governed ⊎ internal). Stated
  gap: the walkable projection (src/admin_graph.py) is item 3.

- **0.3.2 (2026-08-20)** — E1/E5 primitives ENFORCED (src/discovery/,
  gates flipped); statuses PARTIAL with the engine-composition gap
  stated.

- **0.3.1 (2026-08-20)** — F ENFORCED (all six 0044 clause gates green);
  B2 GATED→PARTIAL (pipeline closed-set shipped; persistence = 3b);
  H updated: escalation clause-3b (flagged descriptions escalate)
  flipped with provenance_fallout_row.

- **0.3 (2026-08-19)** — adopted (ADR 0047). Adversarial audit corrections:
  A1's cited test did not exist (added); E6's gap stated
  (probability-vocabulary ban is prompt-only); Σ/D3 corrected — Term
  projection is PENDING, not current. Bindings shipped: C1 ENFORCED
  (EXTRACTION_REGISTRY), C4 ENFORCED (leaf grounding, first verdict 27/28),
  G1–G3 ENFORCED (CAPABILITY_REGISTRY, Uses ∖ S = ∅), E1/E5 GATED,
  T_org vehicle ruled (ORIGIN column). No UNBOUND axiom remains.

- **0.2 (2026-08-19)** — findings of the first blind round-trip review
  (Sunny reconstructed the system; mismatches became spec content): layer
  vocabulary pinned to the codebase's names (§4 table); `T_org` sort added;
  consumption-layer edges spelled out (r2c/r2t/r2m/m2c per ADR 0040); **C4
  leaf grounding** (every tree branch ends on T_D ∪ T_org or is counted);
  **D3 projections are functions of the record** (why terms live in gov
  tables and appear as nodes); **E5 filter grounding** (values only from
  sites/value sets/human); **E6 presentation honesty** (weights and
  closeness, never probabilities); F→E4 dependency noted (descriptions are
  load-bearing for the pick); §13 the double-sided function (τ/ρ law, three
  instances, tier 2 = tier 1 + one arrow); Snowflake/Databricks recorded as
  explicit C1 exclusions for the Fabric-native v1.
- **0.1 (2026-08-19)** — initial draft: groups A–H, graph identity theorem,
  model-checking frame, adoption checklist.
