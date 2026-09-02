<!-- GENERATED FILE — do not edit.
     Sources: src/spec_registry.py (the axiom ledger) rendered into
     scripts/spec_frame.md (the frame prose — edit THAT for frame
     changes; edit the LEDGER for axiom changes, via an ADR).
     Regenerate: python scripts/generate_docs.py
     CI fails if stale (tests/test_spec_registry.py). -->

# Φ_AIVIA — The Shadow Specification

<!-- TIER: BLUEPRINT — generated marker, do not remove.
     Component key: spec (src/trace_registry.py ARCHITECTURE_COMPONENTS)
     Enforced by tests/test_trace_registry.py hierarchy checks. -->

> **Blueprint tier.** This file satisfies axiom groups **axm:S**
> (Specification) · **axm:J** (Judgment) · **axm:M** (Mind) · **axm:B**
> (Boundary) · **axm:R** (Residue & Ledger) from
> [AI_VIA_AXIOMS.md](../AI_VIA_AXIOMS.md), and is the architecture home
> for 14 decisions
> (see [TRACE_MAP.md](TRACE_MAP.md#the-blueprint-tier) for the full
> chain: decision → component → axioms → code → tests).

**Version:** 1.0 (ADR 0073 — the spec becomes a projection of its own
ledger: every axiom's law, gloss, origin, parents, checks and status
live as records in `src/spec_registry.py`, and this document is
GENERATED from them. Ratified content unchanged. Lineage: adopted v0.3
by ADR 0047; extended by 0048, 0051, 0059, 0064, 0065, 0067; §3b
ratified by 0052.)
**Date:** 2026-08-19 (v0.5: 2026-08-21; v0.6: 2026-08-26; v0.7/v0.8: 2026-09-01)
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

**The machine-readable ledger (ADR 0067).** Every axiom's id, group,
framework parents, and declared check files live as records in
`src/spec_registry.py` — the single writer, locked to this document at
the id level in both directions (`tests/test_spec_registry.py`; an
axiom cannot exist in only one place). Law formulas and per-axiom
statuses remain HERE, their one home, until the ratchet retires that
prose into the ADRs. The invariant: if an agent must obey it, it is a
record with a check; if a human must understand why, it is an ADR.

**Relationship to the framework (the tier above).** Φ_AIVIA is *this
system's* theory; [AI_VIA_AXIOMS.md](../AI_VIA_AXIOMS.md) is the
general framework AIVIA is the reference implementation of. This file
translates framework groups **axm:S** (Specification), **axm:J**
(Judgment), **axm:M** (Mind), **axm:B** (Boundary) and **axm:R**
(Residue & Ledger) into checkable sentences about this codebase. The
two ID spaces are distinct and their group letters collide — `spec:B1`
(witness totality, here) is not `axm:B1` (no claim without a witness,
there), though the first is the second made mechanical. Always prefix.

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

*Gloss:* folding twice changes nothing — so it never matters how many times a value has been folded before matching.
*Origin:* ADR 0016.
*Grounds in the framework:* axm:D2 — one folding rule, one definition.
*Checks:* `tests/parser/test_identity.py`
**Status: ENFORCED**

**A2 — metric_id is a key.**

    ∀m, m′ ∈ Metric.  id(m) = id(m′) → m = m′

*Gloss:* two metrics with the same id are the same metric, everywhere, including every downstream projection (Purview qualifiedName, exports).
*Origin:* ADR 0015.
*Grounds in the framework:* axm:D3 — identity -> exactly one owner per metric.
*Checks:* `tests/test_invariants.py`, `tests/test_table_contracts.py`
**Status: ENFORCED**

**A3 — fold-collisions are rejected loudly.**

    ∀s, s′ ∈ SourceRow.  fold(name(s)) = fold(name(s′)) ∧ s ≠ s′  →  reject(load)

*Gloss:* two inputs whose identities differ only by case are one object in a case-insensitive database — a data error, never two entries.
*Origin:* ADR 0016.
*Grounds in the framework:* axm:D2 — one folding rule, one definition.
*Checks:* `tests/test_invariants.py`
**Status: ENFORCED**


---

## 6. Group B — Soundness (nothing exists without a witness)

**B1 — witness totality (the anti-fabrication axiom).**

    ∀e ∈ E_G.  ∃w ∈ D ∪ P ∪ M ∪ O ∪ Gov.  justifies(w, e)

*Gloss:* every edge in the graph traces to a source fact — a dictionary row (join edges: a (PK, FK) pair), an AST node, a TMDL partition, an org declaration, a governance record. No edge is ever asserted from model memory or heuristic guess. (Refuse- over-guess, ADR 0005, stated as structure.)
*Origin:* ADRs 0005, 0032, 0044.
*Grounds in the framework:* axm:B1 — witness totality IS 'no claim without a witness'.
*Checks:* `tests/test_invariants.py`, `tests/test_tree_contract.py` — PARTIAL by construction in builders; not yet a uniform declared invariant on every edge table
**Status: PARTIAL** — holds by construction for edges built in 03; not yet a uniform declared invariant on every edge table. Debt: every edge-table contract declares its witness reference.

**B2 — description provenance is total and closed.**

    ∀d ∈ Desc.  provenance(d) ∈ {gate_passed, skeleton_floor, flagged}

*Gloss:* no description exists without a stated epistemic status; no fourth value; no NULL.
*Origin:* ADR 0044 clause 6; vocabulary amended by ADR 0074 call 2 (gate_passed = smoothed prose that cleared the gate; skeleton_floor = deterministic composition, unfalsifiable; template_fallback retired with its mechanism)
*Grounds in the framework:* axm:B1, axm:J4 — provenance closed -> every description judged.
*Checks:* `tests/test_tree_contract.py`
**Status: PARTIAL** — stated gap: provenance PERSISTENCE on stored descriptions lands with the ADR 0074 D1 build (the retired phase-3b anchor is superseded)


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

*Gloss:* every kind of source fact — dictionary join rows, dictionary descriptions, SQL decision sites, TMDL partitions, DAX column refs, org reference tables — either has a declared extractor or a recorded "deliberately not extracted, because…". There is no third state ("nobody thought about it").
*Origin:* the EMR-joins incident: `J_D` (the dictionary's join map) had no functor and no exclusion — the violation existed at the inventory level before any code ran, which is why only a code- walk found it. *Seeded exclusion rows (ruled by Sunny 2026-08-19):* Snowflake views and Databricks/dbt models are **excluded for the Fabric-native v1** — real hospital estates increasingly run them, so the rows exist to make the roadmap pressure visible, per ADR 0001 each future dialect gets its own native parser.
*Grounds in the framework:* axm:D1 — the enumerated frontier -> nothing unreachable.
*Checks:* `tests/test_extraction_registry.py`
**Status: ENFORCED** — `src/extraction_registry.py` + `tests/test_extraction_registry.py` (functor XOR exclusion per row; conservation citations resolve; the joins incident pinned as the acceptance test; every reference structure D/P/M/O/Gov covered).

**C2 — conservation per extractor (no third bucket).**

    ∀k.  dom(R_k) = handled_k ⊎ fallout_k

*Gloss:* every source row is either extracted or counted as fallout — the sum matches the total, and nothing vanishes.
*Origin:* ADR 0044 clause 1 (decision sites: `handled + unextracted == total`), ADR 0041 (M shapes), ADR 0045 (fallout resolution).
*Grounds in the framework:* axm:R1 — handled + fallout = total (conservation).
*Checks:* `tests/test_tree_contract.py`, `tests/mquery/test_mquery.py`
**Status: PARTIAL** — enforced for trees and M shapes; C1's registry (now ENFORCED) carries a conservation citation per row and the citations are checked to resolve — full per-row equation checks remain the stated gap.

**C3 — images land in the graph.**

    ∀k.  F_k(handled_k) ⊆ G

*Gloss:* what an extractor extracts actually arrives — no silent drops between extraction and the graph.
*Grounds in the framework:* axm:R1 — handled + fallout = total (conservation).
*Checks:* `tests/test_invariants.py`
**Status: PARTIAL** — (same universality note as C2).

**C4 — leaf grounding (the termination axiom).**

    ∀f ∈ P.  ∀ℓ ∈ leaves(tree(f)).   ℓ ∈ T_D ∪ T_org   ∨   ℓ ∈ fallout(f)
    completely_parsed(f)  ⟺  fallout(f) = ∅

*Gloss:* after internal references resolve (CTEs and temp tables resolve to their defining steps), every remaining leaf of every parsed tree must bottom out on a vendor table or an org reference table. Anything else — an unresolvable name, a dynamic-SQL branch — is counted fallout, and "completely parsed" is a **computed per-file verdict**, never an impression. Gives the funnel a new honest number: fraction of files fully grounded.
*Origin:* Sunny's blind reconstruction, 2026-08-19 ("any AST tree branch that does not end in EMR tables or org's custom reference table is not a completely parsed sql file").
*Grounds in the framework:* axm:R1, axm:D1 — leaf grounding: termination + reachability.
*Checks:* `tests/governance/test_leaf_grounding.py`
**Status: ENFORCED** — `src/governance/leaf_grounding.py` (verdict + fraction + escalated fallout, stage `500_leaf_grounding`), wired into 500; `tests/governance/test_leaf_grounding.py`. First recorded-corpus verdict: 27/28 files completely parsed (USP_Severe_Sepsis reads 6 tables absent from the dictionary — the number is already working).


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

    reach(x,y) ← dep(x,y)
    reach(x,z) ← reach(x,y) ∧ dep(y,z)
    uses(m,t)  ← calc(m,s) ∧ reach(s,s′) ∧ reads(s′,t)
    Axiom:  uses_materialized = lfp(uses)

*Gloss:* the precomputed USES_TABLE / closure edges must equal what a live traversal would compute. The closure is a **cache with a proof obligation**, not a second truth.
*Origin:* ADRs 0018, 0033, 0037 (closures reclassified as checkable cache; the 5-of-13 undercount was an unstated D1 violation).
*Grounds in the framework:* axm:D4 — closure = shape-defined derivation.
*Checks:* `tests/test_recorded_pipeline.py` — oracles ENFORCED; the general closure-vs-live diff is UNBOUND (ADR 0037 stated gap)
**Status: PARTIAL** — (oracles ENFORCED; general diff UNBOUND).

**D2 — count oracles.**

    |{m : uses(m, HOSPITAL_ENCOUNTERS)}| = 13,   … (fixture constants)

*Gloss:* certified cardinalities from recorded fixtures pin the truth; a derivation change that alters a known count is a red build, never a silent undercount.
*Origin:* ADR 0018.
*Grounds in the framework:* axm:J1 — count oracles = founder-defined correctness.
*Checks:* `tests/test_recorded_pipeline.py`
**Status: ENFORCED**

**D3 — projections are functions of the record.**

    ∀ projection Π ∈ {LPG export, Eventhouse catalog, term nodes,
                      usage-layer edges, Fabric Graph read model}.
        Π = f_Π(Record),   f_Π deterministic and recomputable

*Gloss:* no projection carries information absent from the Delta record; every projection can be rebuilt at will and can never drift into a second source of truth. This is why business terms live in `gov_business_terms` (durable, human-owned) and are *designed to be projected* into the graph each build — the graph is overwritten every run, so anything living only in it would be destroyed. AUDIT FIND (2026-08-19): the Term projection is not yet implemented (no Term nodes, no implements edges) — recorded as an EXTRACTION_REGISTRY exclusion until the builder lands; the gov record and candidate mining exist.
*Origin:* ADRs 0031, 0033, 0038 (usage-layer discipline).
*Grounds in the framework:* axm:D3 — projections have one owning record.
*Checks:* (none declared) — by construction in the builders; no general recompute-and-diff check yet (SPEC stated gap)
**Status: PARTIAL**


---

## 9. Group E — Ask-time determinism (anchor → discover → match → rank)

**E1 — the path space is finite and enumerable.**

    G_tech finite ∧ static
      ⟹  Paths_k(A) = { walks of length ≤ k over joinable, connecting A }
          is finite and mechanically enumerable, for any anchor set A

*Gloss:* the vendor's join map is a known, finite structure. Given anchored nodes, all candidate paths between them are **facts waiting to be enumerated** — a search problem, not a synthesis problem. Nothing needs to "generate" a path, so nothing stochastic may.
*Origin:* ADR 0046 (Sunny's position, settled 2026-08-19).
*Grounds in the framework:* axm:S3 — the path space is data-shaped, hence enumerable.
*Checks:* `tests/test_spec_gates.py`
**Status: PARTIAL** — the deterministic primitive is ENFORCED (`src/discovery/paths.py` + `tests/test_spec_gates.py`, 1.33.0: replay-deterministic simple-path enumeration over the join map, both orientations, hop-capped presentation-never- pruning). Stated gap: the composed 0046 engine (anchor→discover+match→rank→pick) is not built.

**E2 — replay determinism for retrieval components.**

    resolve, discover, rank are functions:
      same (token, catalog_state)  ⟹  byte-identical output

*Gloss:* an LLM fails this **by construction** (it samples) — so it is excluded from these seats by type, not by policy. The recurring "should the LLM help compose the query" debate terminates here: the component violates E2.
*Origin:* ADRs 0032 (the testable definition of deterministic), 0046.
*Grounds in the framework:* axm:J2 — replay determinism = the computable type.
*Checks:* `tests/orchestrator/test_core.py`
**Status: PARTIAL**

**E3 — the decision typing rule (which decider is legal where).**

    decider(d) may be an LLM
      ⟺  codomain(d) is language  ∨  ground_truth(d) is human intent
    a right answer computable from data  ⟹  decider(d) must satisfy E2

*Gloss:* three kinds of decision — computable (code only), judgment (human), linguistic (LLM). An LLM decision is acceptable only where its error mode is visible and bounded. You TEST code; you can only MEASURE models.
*Origin:* ADR 0035 (the taxonomy), 0032, 0046.
*Grounds in the framework:* axm:M5, axm:J2 — the decision-typing rule, verbatim.
*Checks:* `tests/test_methodology.py`
**Status: ENFORCED** — for the control path; each new component declares its decider kind at review.

**E4 — pick containment (the human picks, structurally).**

    pick_human(S) ∈ S        and  no auto-pick:  |S| = 1 does not bypass

*Gloss:* the chosen candidate must be one of those presented — enforced by code, so a silent top-1 pick or an out-of-list answer is impossible, not just discouraged. One candidate is treated the same as ten.
*Origin:* ADRs 0032, 0046 (reaffirmed in strongest form).
*Grounds in the framework:* axm:M5 — intent decisions bind to the human.
*Checks:* (none declared) — structural pick validation in the orchestrator (prose binding, no file named; 0046 re-binds)
**Status: PARTIAL** — (enforced where the orchestrator surface runs; the 0046 engine re-binds it).

**E5 — filter grounding (the 123/456 lesson).**

    ∀v ∈ FilterValues(answer ∪ executed SQL).
        v ∈ Sites ∪ ValueSets ∪ HumanInput

*Gloss:* every literal value in any presented or executed filter comes from a stored decision site, a value-set table (T_org), or the human — never from model memory. Carries the shared- schema/varying-values fact: the EMR schema travels between hospitals; the values never do.
*Origin:* ADR 0046 grounding rules; ADR 0044's captured fabrications.
*Grounds in the framework:* axm:B1 — filter values need witnesses.
*Checks:* `tests/test_spec_gates.py`
**Status: PARTIAL** — the deterministic primitive is ENFORCED (`src/discovery/grounding.py`, 1.33.0: refuse-over-guess on any value without a source). Stated gap: binds to real presented/executed filters when the 0046 engine composes them.

**E6 — presentation honesty.**

    rank PRESENTS, never prunes (caps are disclosed)
    displayed signals ∈ { closeness (relative), usage weight (derived),
                          certification status }
    probabilities are banned display vocabulary

*Gloss:* "confidence" in conversation always means derived edge/usage weights — never a probability the model invented. Closeness is relative geometry, not a likelihood.
*Origin:* ADRs 0032 (threshold is a volume control), 0046 (ranking presents, never prunes)
*Grounds in the framework:* axm:B2, axm:B3 — boundary honesty + bounded quantified claims.
*Checks:* `tests/orchestrator/test_core.py`, `tests/orchestrator/test_caption_gate.py`
**Status: ENFORCED** — (plan surface) — the STAMPED HEADLINE is rendered by code from typed metadata (E6 amendment 2026-08-20, stamp don't audit); the caption LINT is retained as defense-in-depth, MEASURED not tested; stated residue: the superseded agent-loop surface (ADR 0035) is unstamped pending its demolition


---

## 10. Group F — The round trip (ADR 0044 as equations)

**F — the round trip (ADR 0044 as equations).**

    desc  = τ(facts(tree), dict)          τ = translator;  SQL ∉ inputs(τ)
    tree′ = ρ(desc, dict)                 ρ = verifier;    SQL, tree ∉ inputs(ρ)
    ACCEPT(desc)  ⟺  κ(tree′) = κ(tree)   κ and = are deterministic code
    after N rejections:  desc := τ₀(tree),  provenance := template_fallback

*Gloss:* the translator renders typed tree facts (never raw SQL) into prose; a blind verifier reconstructs a tree from the prose alone; a deterministic judge compares canonicalized trees; exhausted retries degrade to the stilted-but-true template. The blindness clauses are **information-flow constraints**: the SQL is not merely ignored — it is unreachable from the function's inputs (enforced at the signature, the noninterference trick).
*Origin:* ADR 0044 clauses 2-6
*Grounds in the framework:* axm:J4 — the round trip is the description's oracle.
*Checks:* `tests/test_tree_contract.py`
**Status: ENFORCED** — as the MEASUREMENT INSTRUMENT — ADR 0074 call 1 re-scoped the round trip out of the production path (acceptance there = gate + skeleton floor); it grades gate output on corpus runs


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

*Gloss:* the registry itself is the proof — a second row claiming an owned capability is a registry validation error, caught before any code review.
*Grounds in the framework:* axm:D2 — one owner per capability, mechanized.
*Checks:* `tests/test_capability_registry.py`
**Status: ENFORCED** — `src/capability_registry.py` (unique keys, one owner prefix per row) + `tests/test_capability_registry.py`.

**G2 — sanctioned powers only (import-graph inclusion).**

    Uses ⊆ S,   where  S = { (own(c), p) : c ∈ C, p ∈ prims(c) }
    equivalently:  Uses ∖ S = ∅

*Gloss:* `Uses` = every (module, powerful-primitive) pair actually present in the code, computed from the AST. `S` = the sanctioned pairs. The check is set difference = empty. Powerful primitives: regex, SQL/M parsers, LLM clients, embedding calls, Delta writes.
*Grounds in the framework:* axm:D2 — one owner per capability, mechanized.
*Checks:* `tests/test_capability_registry.py`, `tests/test_native_parser_law.py`, `tests/test_notebook_contract.py`
**Status: ENFORCED** — the general registry + whole-`src/` inclusion check shipped at adoption: `test_capability_registry.py::test_g2_sanctioned_powers_only` computes Uses from the AST and asserts `Uses ∖ S = ∅` for pythonnet/clr/requests/httpx (+ the absolute sqlglot/sqlparse ban, which no row may ever sanction).

**G3 — no undeclared power.**

    ∀ use of p ∈ PowerPrims.  ∃c.  p ∈ prims(c)

*Gloss:* every use of a dangerous primitive maps back to a declared capability — nothing powerful is used "off the books."
*Grounds in the framework:* axm:D2 — one owner per capability, mechanized.
*Checks:* `tests/test_capability_registry.py`
**Status: ENFORCED** — same inclusion check (an unowned use fails with the registry named) + `test_g3_banned_parsers_have_no_owner`. *Honest residue:* G-group catches the high-risk primitive classes. Two innocent pure-Python functions independently reimplementing the same logic (a second fold, a second hash) are not mechanically detectable — mitigated by owning primitive operations in single modules and by review. Stated so nobody mistakes the fence for a force field. ---

**G4 — checks are claims: fire and cover.**

    enforcement check => frontier enumerated AS DATA, deny-by-default
    trusted check     => proven against an injected violation (pinned)
    new mechanism     => names its pattern ancestor on the record

*Gloss:* red-first proves a check CAN fire; only an enumerated, deny-by-default frontier proves it COVERS. The injected-violation proof is the mechanical second mind; the ancestry line makes prior art a recorded act.
*Origin:* ADR 0075 — the sloppy-ban incident: GATE-REGEX-1 v1 checked one hand-picked function by substring, red-first and still wrong
*Grounds in the framework:* axm:J3, axm:J1 — coverage matches type; correctness of checks is founder-defined too.
*Checks:* `tests/test_check_contract.py`, `tests/test_skeleton_composer.py`, `tests/test_op_frontier.py`
**Status: ENFORCED** — by citation for standing instances (G2 inclusion, 0042 planks, 0044 strict-xfail, TestRegexFrontier) + the scanner meta-test; the design protocol (INDEX step 4) carries it forward for new checks


*Honest residue:* G-group catches the high-risk primitive classes. Two
innocent pure-Python functions independently reimplementing the same logic
(a second fold, a second hash) are not mechanically detectable — mitigated by
owning primitive operations in single modules and by review. Stated so nobody
mistakes the fence for a force field.

---

## 12. Group H — Escalation (no silent residue)

**H1 — fallout resolution is total and closed.**

    resolution : FalloutRow → {auto_resolved, escalated} (total; no NULL)

*Gloss:* everything the pipeline cannot resolve is either recovered by the pipeline or lands on a human's checklist — counted is not the same as owned.
*Origin:* ADR 0045
*Grounds in the framework:* axm:R3 — novelty escalates.
*Checks:* `tests/test_escalation_contract.py`
**Status: GATED** — strict-xfail skeletons, 4 clauses (status shared with H2)

**H2 — novelty always escalates.**

    outcome(x) = unknown  →  resolution(x) = escalated

*Gloss:* everything the pipeline cannot resolve is either recovered by the pipeline or lands on a human's checklist — counted is not the same as owned.
*Origin:* ADR 0045.
*Grounds in the framework:* axm:R3 — novelty escalates.
*Checks:* `tests/test_escalation_contract.py`
**Status: GATED**


---

## 13. Group T — the double-sided function (one law, three instances, two tiers)

*(Promoted to a numbered group 2026-09-01, ADR 0065. This section
called itself "THE LAW" and stated three instances, but only instance 1
had an axiom id — so the crosswalk covered a third of it and nothing
checked the rest. T = the τ/ρ transform pair.)*

The product's two tiers are built from one pair of functions over the same
three-layer structure:

    τ : Tree → Language        render structure into meaning (describe, caption)
    ρ : Language → Tree        translate intent into structure (anchor, propose)

The law is instantiated **three times**, at three grains, with three judges:

**T0 — the round-trip law.**

    ∀t ∈ Tree.  κ(ρ(τ(t))) = κ(t)        modulo canonicalization

*Gloss:* meaning rendered from structure must translate back to the same structure. Each direction's correctness is certified by running the opposite direction — which is why no instance may be checked by inspecting only its own output.
*Origin:* ADR 0044 (instance 1), generalized here.
*Grounds in the framework:* axm:J4 — the round-trip law: kappa(rho(tau(t))) = kappa(t).
*Checks:* (none declared) — instantiated as T1-T3, each with its own judge; no single check by design (ADR 0065)
**Status: PARTIAL** — instantiated three times below with three different judges; T1 is ENFORCED, T2 PARTIAL, T3 human-judged by construction. The law is only as strong as its weakest instance, and that is stated rather than averaged away. The law is instantiated **three times**, at three grains, with three judges: | # | Instance | τ | ρ | Judge | Status | |---|---|---|---|---|---| | **T1** | Descriptions (ADR 0044) | translator | blind verifier | deterministic tree diff (κ-equality) | **ENFORCED** — `tests/test_tree_contract.py`, all six clause gates green; this is `spec:F` stated as a member of the family | | **T2** | SQL stitching (ADR 0033/0061, tier 2) | compile fragments → SQL text | parse back through ScriptDom | tree equality (the parser) | **PARTIAL** — `src/run_layer.py::check_single_select` parses every executed statement through ScriptDom, so PARSEABILITY round-trips and a malformed compile fails closed. **Stated gap:** no κ-equality diff between the compiled tree and the source tree; the parser confirms the SQL is well-formed, not that it means the same thing | | **T3** | Definition creation (ADR 0038/0062, tier 1) | render proposal back for confirmation | user prose → proposed canonical tree | **the human** | **JUDGED, not tested** (§14d L3) — the confirm step (`spec:R3`) is the mechanism; correctness is the human's click. Recorded as judged so nobody mistakes a rendered proposal for a verified one | **Why T2's gap matters and is not quietly closed.** Instance 1 earned its judge — a blind verifier plus κ-equality — because a fabricated description corrupts the human's pick (the E4 dependency). Instance 2 executes SQL against patient data; its current judge answers "does this parse?" and not "is this the tree the user confirmed?" `spec:R7` narrows the exposure to near zero by requiring the executed SQL be byte- for-byte the confirmed step — nothing is compiled at run time today — so the gap is latent, not live. It becomes live the moment fragment stitching ships, and T2 is the axiom that will then need its κ-diff. And the tiers are the two directions of one correspondence: Tier 1 (metadata): Question --ρ--> anchors --enumerate/match/rank--> shapes --τ--> captions --human picks--> answer Tier 2 (self-service): same prefix, then: picked shape --compile--> SQL --execute--> data --human approves--> stamped canonical **Tier 2 = Tier 1 + exactly one arrow** (compile∘execute) — ADR 0046's "Pro adds exactly ONE layer" as a formula. Tier 1 moves structure→meaning; tier 2 moves meaning→structure→data; each direction's correctness is certified by running the opposite direction. Every human approval in either direction is an appended Event, which is how the flywheel (ADR 0023) is the same object as the verification machinery: **verification events ARE governance data.** ---

**T1 — Descriptions.**

    tau=translator; rho=blind verifier; judge=deterministic tree
    diff (κ-equality)

*Grounds in the framework:* axm:J4 — descriptions - blind verifier + kappa-diff.
*Checks:* `tests/test_tree_contract.py`
**Status: ENFORCED** — as the measurement instrument (ADR 0074 call 1); the production judge for descriptions is the grounding gate + skeleton floor. This is spec:F as a family member

**T2 — SQL stitching.**

    tau=compile fragments → SQL text; rho=parse back through
    ScriptDom; judge=tree equality (the parser)

*Grounds in the framework:* axm:J4, axm:B1 — SQL stitching - parseability round-trips; kappa-diff is the stated gap.
*Checks:* `tests/test_run_layer.py` — parseability round-trips; the kappa-equality diff is the stated gap, live when stitching ships
**Status: PARTIAL** — `src/run_layer.py::check_single_select` parses every executed statement through ScriptDom, so PARSEABILITY round- trips and a malformed compile fails closed. Stated gap: no κ-equality diff between the compiled tree and the source tree; the parser confirms the SQL is well-formed, not that it means the same thing

**T3 — Definition creation.**

    tau=render proposal back for confirmation; rho=user prose →
    proposed canonical tree; judge=**the human**

*Grounds in the framework:* axm:M5, axm:J2 — definition creation - the human is the judge (L3 stratum).
*Checks:* (none declared) — JUDGED, not tested — the human is the judge by construction (SPEC 14d, L3 stratum)
**Status: JUDGED** — , not tested (§14d L3) — the confirm step (`spec:R3`) is the mechanism; correctness is the human's click. Recorded as judged so nobody mistakes a rendered proposal for a verified one


**Why T2's gap matters and is not quietly closed.** Instance 1 earned
its judge — a blind verifier plus κ-equality — because a fabricated
description corrupts the human's pick (the E4 dependency). Instance 2
executes SQL against patient data; its current judge answers "does this
parse?" and not "is this the tree the user confirmed?" `spec:R7`
narrows the exposure to near zero by requiring the executed SQL be
byte-for-byte the confirmed step — nothing is compiled at run time
today — so the gap is latent, not live. It becomes live the moment
fragment stitching ships, and T2 is the axiom that will then need its
κ-diff.

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

**P1 — one conversation decides a turn; no separate planner/judge/c.**

    one conversation decides a turn; no separate
    planner/judge/captioner minds

*Grounds in the framework:* axm:M2 — one mind, full evidence.
*Checks:* `tests/orchestrator/test_turn_engine.py`
**Status: ENFORCED**

**P2 — full tool results enter the SAME history and persist across .**

    full tool results enter the SAME history and persist across
    rounds and turns; compaction degrades oldest to stamped headline
    + totals, never drops

*Grounds in the framework:* axm:M2 — one mind, full evidence.
*Checks:* `tests/orchestrator/test_turn_engine.py`
**Status: ENFORCED**

**P3 — thinking room — no forced tool_choice except the final typed.**

    thinking room — no forced tool_choice except the final typed
    verdict

*Grounds in the framework:* axm:M3 — thinking room.
*Checks:* `tests/orchestrator/test_turn_engine.py`
**Status: ENFORCED**

**P4 — no question-family casebook anywhere — invariants + tool sem.**

    no question-family casebook anywhere — invariants + tool
    semantics only

*Grounds in the framework:* axm:M4 — no question-shaped control flow.
*Checks:* `tests/orchestrator/test_turn_engine.py`, `tests/test_methodology.py`
**Status: ENFORCED**

**P5 — honesty at the boundary only.**

    honesty at the boundary only: headlines, caption gate, machine-
    verified evidence-quote verdict, read-only dispatch, write plan-
    confirm, caps as code

*Grounds in the framework:* axm:B2 — honesty at the boundary, never the interior.
*Checks:* `tests/orchestrator/test_turn_engine.py`
**Status: ENFORCED**

**P6 — failure is observation.**

    failure is observation: tool errors return into the
    conversation; caps bound flailing

*Grounds in the framework:* axm:M1 — failure as observation = loop-shape capability.
*Checks:* `tests/orchestrator/test_turn_engine.py`
**Status: ENFORCED**


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

## 14e. Group Q — graph topology (v0.6, ADR 0059; ratified 2026-08-26)

The ADR names these G1–G3; Φ_AIVIA already holds a Group G
(mechanism uniqueness), so they join as Q1–Q3 — the correspondence
is recorded here, never silently renumbered. Measured before
drafted: 1 component / 0 orphans / 0 dangling at 6,669 nodes /
14,994 edges on the recorded corpus (2026-08-26); the measurement is
now the permanent CI baseline.

**Q1 — accounted connectivity.**

    accounted connectivity: components enumerated every build;
    exactly one PRINCIPAL derived component; foundation-only islands
    legitimate under the FOUNDATION EXCEPTION (enumerated, never
    findings); degree-0 forbidden (enumerated exclusion: the
    govmeta:sweep receipt)

*Grounds in the framework:* axm:D1 — accounted connectivity -> nothing unreachable.
*Checks:* `tests/graph/test_topology.py`
**Status: ENFORCED**

**Q2 — edge soundness.**

    edge soundness: every edge referential AND provenance-mapped —
    parsed / declared / derived / asserted, exactly one class per
    edge type (EDGE_PROVENANCE, 0052-pattern totality)

*Grounds in the framework:* axm:B1 — every edge provenance-mapped.
*Checks:* `tests/graph/test_topology.py`
**Status: ENFORCED**

**Q3 — relative completeness.**

    relative completeness: every completeness claim is a
    conservation equation (refs = minted ⊎ dropped; swept = flagged
    ⊎ clean ⊎ excluded; matrix/reachability totality) with ask-time
    boundary disclosure; absolute completeness claims forbidden

*Grounds in the framework:* axm:B3 — completeness claims are conservation equations.
*Checks:* (none declared) — ENFORCED by citation — the existing conservation asserts predate the axiom (ADR 0059)
**Status: ENFORCED** — (by citation — no new mechanism needed; the equations predate the axiom)


**The foundation exception (Sunny, 2026-08-26, verbatim force):**
the dictionary is a source of truth — foundation nodes exist as is;
their islands are legitimate states enumerated for visibility, never
findings, never queue entries, never flags. Q1's principal-component
requirement binds derived layers only.

## 14f. Group R — ask-time interpretation (v0.7, ADRs 0060 + 0062)

Groups E and P govern what happens once a question is understood.
Group R governs the UNDERSTANDING itself — the seam ADR 0060 found
open (the LLM chose the route) and ADR 0062 closed (there are no
routes to choose). The E-group's "which decider is legal where"
(E3) now has a fourth seat with a stated occupant: interpretation
is the LLM's ONLY authorship, and it is bounded by confirmation.

**Relation to Group P.** P1 ("one conversation decides a turn") is
unchanged; R constrains what that conversation may DECIDE. P3's
thinking room survives; R2 removes route choice from the set of
things thinking may land on.

**R1 — Parse, never generate.**

    **Parse, never generate.** The LLM maps the sentence to entity
    phrases + relation words drawn from a closed lexicon; it never
    composes a query, never selects a route, never authors a
    verdict. A model-composed query cannot be stamped; a parse can
    be confirmed.

*Grounds in the framework:* axm:M4, axm:M5 — parse-never-generate: free composition + typing.
*Checks:* `tests/orchestrator/test_parse_plan.py`
**Status: ENFORCED** — (prototype + measured gate: PARSE_EXPERIMENT, 7/7 oracles vs 5/7)

**R2 — No question types.**

    **No question types.** The answer's shape EMERGES from the
    matched subgraph; no enumeration of question shapes, classes, or
    families may exist in the control path. (0062's abolition; the
    P4 casebook ban generalized from prompts to structure.)

*Grounds in the framework:* axm:M4 — no question types.
*Checks:* `tests/test_methodology.py`
**Status: ENFORCED** — for the control path

**R3 — Interpretation confirms before it executes.**

    **Interpretation confirms before it executes.** Every reading
    renders on glass and waits for the click; fuzzy grounding may
    NOMINATE, only the human's click EXECUTES. Plan-confirm-
    execute-display applied to the interpretation itself (0060 call
    1, RULED: confirm every parse).

*Grounds in the framework:* axm:B4 — irreversible acts confirm - applied to interpretation.
*Checks:* `tests/webapp/test_app.py`
**Status: ENFORCED**

**R4 — No dead ends.**

    **No dead ends.** Every state — failure, empty, ambiguity,
    exhaustion — renders as action items; an exhausted loop becomes
    a CAPTURED DEMAND handoff to a developer, never a shrug. The
    escalation door stands at every round.

*Grounds in the framework:* axm:R3 — no dead ends -> novelty escalates.
*Checks:* `tests/webapp/test_app.py`
**Status: ENFORCED**

**R5 — Certain answers.**

    **Certain answers.** Under ambiguity, execute only what every
    surviving reading supports; only genuine ambiguity spawns a
    clarify item. We iterate on UNDERSTANDING, never on mechanical
    execution steps.

*Grounds in the framework:* axm:B3 — certain answers = bounded claims under ambiguity.
*Checks:* (none declared) — the no-nag boundary in the loop; no general multi-reading intersection check (SPEC: PARTIAL)
**Status: PARTIAL** — the rule is implemented in the loop; no general multi-reading intersection check


**The R-group's pedigree** is ADR 0062 §3, the standing axiom
register `0062:A1…A6` (compositionality, small algebras, formal-layer
completeness, irreducible ambiguity, interaction-closes-the-gap,
certain answers). Cite `0062:A<n>` alongside `spec:R<n>` in drift
debates — the ADR carries the literature, this group carries the law.

## 14g. The run-layer boundary (v0.7, ADR 0061)

The Pro tier executes confirmed logic against the customer's
source. Its axioms are boundary axioms — they extend P5 (honesty at
the boundary) to DATA, and they are the reason the tier is
sayable out loud: *the AI governs the question; the database
answers it; the model never touches a patient.*

**R6 — Rows never enter model context.**

    **Rows never enter model context.** Results render to the USER'S
    GLASS; the model sees machine stamps only — row count, column
    schema, elapsed, as-of, source. P5 absolute, extended to result
    sets.

*Grounds in the framework:* axm:B2 — rows never enter model context.
*Checks:* `tests/test_run_layer.py`
**Status: ENFORCED**

**R7 — Nothing is generated; the confirmed SQL is what runs.**

    **Nothing is generated; the confirmed SQL is what runs.** Byte-
    for-byte the parsed, displayed step the user confirmed — not
    NL2SQL. Read-only by construction: a dedicated read-only
    credential AND a ScriptDom statement-type check (the native-
    parser law: the parser decides, never regex). DML/DDL/EXEC →
    typed refusal.

*Grounds in the framework:* axm:B4 — confirmed-only execution.
*Checks:* `tests/test_run_layer.py`
**Status: ENFORCED**

**R8 — Sampling is machine-labelled.**

    **Sampling is machine-labelled.** Every result carries `N rows ·
    TOP <cap> · as of <timestamp> · source <db> · read-only`,
    composed by code, never model-written. The cap is a disclosed
    fact, not a hidden truncation (E6's presentation honesty,
    applied to data).

*Grounds in the framework:* axm:B3 — machine-labelled sampling.
*Checks:* `tests/test_run_layer.py`
**Status: ENFORCED**


**Stated gap (listing-blocking, recorded in ADR 0061 §3):** slice 1
runs on the synthetic demo estate only. The **output-side PHI gate**
and dedicated read-only principals are DESIGN-REQUIRED before any
customer source is ever bound. This is a gate, not a debt — Tier 3
GA is blocked on it.

## 14h. Group L — the ledger (v0.8, ADR 0064; ratified 2026-09-01)

Found by the crosswalk audit (`AXIOM_CROSSWALK.md`): two framework
laws — `axm:R4` (the ledger) and `axm:R2` (drift fires mechanically) —
were **enforced in code but stated in no axiom**. §4's signature Σ even
lists `Event (append-only)`, so the spec *presumed* the law it never
wrote down. That is precisely the failure §1's closure claim promises
to prevent, so the axioms join here rather than the gap being noted and
left.

**L1 — append-only is declared AND obeyed.**

    ∀t ∈ Tables.  write_mode(t) ∈ {overwrite, append}
    ∧  write_mode(t) = append  →  no writer of t uses overwrite semantics

*Gloss:* a table that declares itself a ledger may only ever grow. The declaration existed since the beginning (`TABLE_REGISTRY.write_mode`; 39 overwrite / 10 append) and the label's legality was checked — but nothing checked the label was HONOURED. An append flipped to overwrite destroys every prior run's telemetry silently.
*Origin:* ADR 0064; the 2026-08-15 audit note in 500_validate ("a failing append must RAISE — never silently become an overwrite").
*Grounds in the framework:* axm:R4 — the ledger may only grow.
*Checks:* `tests/test_ledger_contract.py`, `tests/test_table_contracts.py`
**Status: ENFORCED**

**L2 — aggregates are derived, never stored.**

    ∀a ∈ Aggregates.  a = f(Events),  f deterministic and recomputable
    no counter is mutated in place

*Gloss:* usage weights, funnel counts, and every governance number are recomputed from the append-only log — never incremented on a stored row. This is D3 (projections are functions of the record) applied to COUNTS, and it is the law the purged UsageTracker broke.
*Origin:* ADR 0064; the purged in-place usage counter (`axm:R4`'s descent), which had no regression guard until now — the corpse-to- fixture rule (`axm:J3`) applied retroactively.
*Grounds in the framework:* axm:R4, axm:D3 — aggregates derived, never stored.
*Checks:* `tests/test_ledger_contract.py`
**Status: ENFORCED**

**L3 — every declaration has a firing mechanism.**

    ∀d ∈ Declarations.  ∃m.  fires(m, divergence(d))

*Gloss:* §3b's third question, promoted from a review ritual to an axiom: when reality diverges from a declaration, something MECHANICAL fires — a red build, a checklist row, a funnel bar. "Someone would notice" is the definition of a missing feedback loop.
*Origin:* ADR 0064, closing axm:R2
*Grounds in the framework:* axm:R2 — every declaration has a firing mechanism.
*Checks:* `tests/test_spec_gates.py` — ENFORCED by citation (0059 Q3 precedent): the registry closure checks, funnel, reachability
**Status: ENFORCED** — (by citation — the 0059 Q3 precedent): the seven registry closure checks, the funnel, and reachability ARE the firing mechanisms; stated gap: a NEW declaration acquires its mechanism by review (section 3b), not yet by a mechanical check that one exists


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

**Frozen at v1.0 (ADR 0073).** §1 has said it since v0.1: "the ADRs
are the changelog of this theory." From here that is literal — spec
changes are ADRs; this section is preserved history.


- **0.9 + ledger (2026-09-02, ADR 0067)** — the axiom ledger:
  ids/parents/checks as records in `src/spec_registry.py`, this
  document locked to it at the id level both ways. No axiom changed;
  format governance only.

- **0.9 (2026-09-01)** — §13 promoted to **Group T** (ADR 0065), on
  Sunny's ruling from the crosswalk's scope finding. The section called
  itself "THE LAW" and named three instances, but only instance 1 had
  an axiom id, so the crosswalk covered a third of it. Now T0 (the
  round-trip law, PARTIAL — a law is only as strong as its weakest
  instance), T1 (descriptions, ENFORCED — `spec:F` seen as a family
  member), T2 (SQL stitching, PARTIAL — parseability round-trips
  through ScriptDom, but no κ-equality diff between compiled and source
  trees; latent because `spec:R7` executes only byte-for-byte confirmed
  SQL, live the moment fragment stitching ships), T3 (definition
  creation, JUDGED not tested — the human is the judge by
  construction). Zero new mechanisms: T1/T3 cite what exists, T2 states
  a gap. SPEC's un-numbered normative prose now reduces to §3b and
  §14d, both correctly rituals rather than axioms.

- **0.8 (2026-09-01)** — Group L, the ledger (§14h, ADR 0064): L1
  append-only declared AND obeyed, L2 aggregates derived never stored,
  L3 every declaration has a firing mechanism. Closes the two real gaps
  the crosswalk audit found (`axm:R4`, `axm:R2`) — laws this codebase
  enforced but the spec never stated, which contradicted §1's closure
  claim. L1 and L2 ship ENFORCED with new checks
  (`tests/test_ledger_contract.py`, verified against injected
  violations); L3 is ENFORCED by citation of the existing registry
  closure checks (the 0059 Q3 precedent). Also recorded: Group P
  (P1–P6, ADR 0051) had been ratified in §14c since 2026-08-21 but was
  never registered in `SPEC_AXIOMS`, so no ADR could cite `spec:P1` —
  found by the same audit, now fixed and wired to 0051.

- **0.7 (2026-09-01)** — architectural audit + reconciliation. Group R
  (§14f) — ask-time interpretation, from ADR 0060 (parse, never
  generate) and ADR 0062 (there are no question types; show, propose,
  ask, execute): R1 parse-never-generate, R2 no-question-types, R3
  confirm-before-execute, R4 no-dead-ends, R5 certain answers. The
  run-layer boundary (§14g) from ADR 0061: R6 rows-never-in-context,
  R7 confirmed-SQL-only + read-only by ScriptDom check, R8 machine-
  labelled sampling; the output-side PHI gate recorded as a
  GA-blocking gate. The 0062:A1–A6 axiom register is recorded as
  citable pedigree alongside spec:IDs. No existing axiom changed —
  Group R constrains the interpretation seat that E3 typed and P1
  seated; E and P are unamended.

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
