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

{{AXIOMS:A1,A2,A3}}

---

## 6. Group B — Soundness (nothing exists without a witness)

{{AXIOMS:B1,B2}}

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

{{AXIOMS:C1,C2,C3,C4}}

**THE GRAPH IDENTITY THEOREM** (what B and C jointly force):

    G  =  ⋃_k F_k(handled_k)

*Gloss:* the graph is **exactly** the union of the declared extraction images —
no more (soundness: B1 forbids unwitnessed edges) and no less (completeness:
C1+C3 over the whole inventory). "Complete knowledge graph" now has a
definition: it is this equation, checked against the inventory. The technical
layer being "the vendor's complete join map" is the k = J_D instance.

---

## 8. Group D — Derived structure (fixpoint and projection correctness)

{{AXIOMS:D1,D2,D3}}

---

## 9. Group E — Ask-time determinism (anchor → discover → match → rank)

{{AXIOMS:E1,E2,E3,E4,E5,E6}}

---

## 10. Group F — The round trip (ADR 0044 as equations)

{{AXIOMS:F}}

---

## 11. Group G — Mechanism uniqueness (the codebase axioms)

> The group that ends "two tools for one job." These axioms are about the
> CODE, not the data; their model checker is CI reading the AST.

Declare a **capability-ownership registry**: `own : Capabilities → Modules`,
plus per-capability sanctioned primitives `prims(c)`. Proposed home:
`CAPABILITY_REGISTRY` in src/, the fifth peer registry.

{{AXIOMS:G1,G2,G3}}

*Honest residue:* G-group catches the high-risk primitive classes. Two
innocent pure-Python functions independently reimplementing the same logic
(a second fold, a second hash) are not mechanically detectable — mitigated by
owning primitive operations in single modules and by review. Stated so nobody
mistakes the fence for a force field.

---

## 12. Group H — Escalation (no silent residue)

{{AXIOMS:H1,H2}}

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

{{AXIOMS:T0,T1,T2,T3}}

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

{{AXIOMS:P1,P2,P3,P4,P5,P6}}

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

{{AXIOMS:Q1,Q2,Q3}}

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

{{AXIOMS:R1,R2,R3,R4,R5}}

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

{{AXIOMS:R6,R7,R8}}

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

{{AXIOMS:L1,L2,L3}}

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
