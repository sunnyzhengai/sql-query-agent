# The Sphere — AIVIA's complete architecture model

**Design record of the Sunny + review-session debates, 2026-08-25.
Ratified by ADR 0057. This is the big picture the product answers
to; the build queue is governed separately.**

## The four shells (inside → out)

1. **Foundation — EMR reality.** The customer's schema truth:
   tables, columns, keys, declared join topology, AND the standard
   vocabularies (ICD-10, LOINC, RxNorm). SOVEREIGN: independent of
   what any SQL happens to use. Built at BYOT ingestion from the
   customer's proprietary dictionaries — the deliverable is the
   ingestion tooling. **Rung-3 composition depends on foundation
   sovereignty**: new questions need join paths no existing SQL ever
   used. Owners: admins/IT (rightfully — this IS their layer).
2. **Org artifacts — organizational reality.** Parsed SQL (steps,
   decision sites) AND PBI reports/semantic models — everything the
   organization built, pointing down into foundation. PARSED TRUTH:
   AIVIA is never the editor; writes here are OBSERVED (ingestion
   diffs — the "3 changed, 0 new" machinery is the write-detection
   surface; ripple latency = sync cadence). Owners: developers.
3. **Canonical — the organization's ontology.** Named business
   concepts as first-class nodes, **born bottom-up from extraction**,
   with many-to-many CLAIM edges onto org artifacts. NOT
   descriptions (those are 1:1 attributes on org nodes); the layer
   exists because meaning has identity, cardinality, and lifecycle
   apart from implementation (one concept, N implementations; the
   concept survives reimplementation; governance objects attach
   here). **A term is GOVERNED when its claims are
   consistent-or-dispositioned** — the red-flag sweep is this
   layer's health meter; KPI: unlabeled divergences → 0.
4. **The human shell.** Users as nodes; decisions (ADR 0056) as
   typed asserted edges; ownership as SCOPED edges (administers /
   develops / stewards / owns-citizen-copy). The shell ADDS to inner
   shells (testimony, forks, rung-3 drafts, canonical amendments);
   it never rewrites parsed fact (P2).

## Radial dynamics — the two pillars are two directions

- **Governance = outward:** extract from SQL → translate → attach to
  concepts → searchable. (Basic tier.)
- **Self-service = inward:** concept → implementation → foundation →
  EXECUTE → data. (Pro tier; the execution leg unbuilt, declared
  incomplete.) Three rungs as provenance grades — see
  PRODUCT_PICTURE.md.

## The nervous system (change propagation)

ONE RULE: for every changed node, walk one hop; notify along
ownership edges; payload = typed delta (breaking vs additive) with
error-contract receipts (delta + node + drill + suggested action).
- Native writes (canonical, citizen, decisions) ripple instantly.
- Observed writes (foundation, org) ripple at ingestion diff.
- **Meaning-leads-code:** a steward's canonical amendment (e.g., the
  81st ICD code) opens a typed `pending_implementation` gap;
  developers are notified with blast radius; **the gap closes by
  PARSING, never by claiming** — assertion opens, evidence closes.
- Inboxes are usage-ranked (0056 decision weights) and digested —
  governance interrupts in usefulness order.

## The ownership economy

- **Unbundle "owner":** SUBSCRIBER (unbounded, automatic — testimony
  edges ARE the subscription list: your past decisions are your
  subscriptions) · ACCOUNTABLE OWNER (one-or-few; must act) ·
  AUTHORITY (scoped certification). "Forty owners is zero owners."
- **Stewards follow uses:** stewardship is accountability for a
  USE (regulatory submission, board metric, contract measure),
  never authority over a MEANING. Meanings stay plural; uses have
  owners; a term with no single-truth use needs NO steward.
- **Staffing = harvest, not campaign:** the seat is OFFERED at the
  moment of demonstrated care (first strong testifier:
  "accept stewardship?" — opt-in at peak willingness). Two doors:
  earned (default, disclosed as earned, contestable) and appointed
  (org override; use-anchored stewards are structural — the
  submission owner). Rung-3 drafts: creator owns immediately;
  promotion to shared truth is where accountability formalizes.
- **Ownership lifecycle (conservation over accountability):**
  unowned+unused (retirement candidate) ⊎ unowned+used (harvest
  queue) ⊎ provisional (earned) ⊎ stewarded. New flag classes:
  orphaned ownership; retirement candidates; reference-vocabulary
  violations (invalid codes — machine-detectable case-a wrongness).

## The wrongness taxonomy (typed deny; ADR 0056 amendment)

Wrongness is always relative to a GROUND; each ground has a
structurally rightful owner:
| deny type | ground | routes to |
|---|---|---|
| defect | code vs its own intent (typo/invalid vocab) | developer (bug report; vocab flags pre-file most) |
| mismatch | valid definition, not MY definition | back to denier as a FORK OFFER |
| noncompliance | definition vs external mandate | the use-owner |

## Contracts in the graph (the split)

- **Static system contracts** (schemas, consumers, op registry,
  guards): CODE-AUTHORITATIVE (intentions decay; only enforcement
  survives), PROJECTED into the graph as generated read-only nodes;
  CI asserts projection == code (conservation). The agent answers
  questions about the rules by traversal; the rules are not
  editable as data.
- **Dynamic governance contracts** (ownership edges, scoped
  authority, subscriptions): GRAPH-NATIVE by necessity
  (per-customer, runtime-born via decisions); enforced by code that
  READS them; asserted-layer disciplines apply.
- **Guard:** the graph may describe every rule; only the most
  protected writes may change a rule; the rules about changing
  rules never leave code.
- **Self-ingestion (direction):** AIVIA's own pipeline is
  SQL-and-Python over tables — ingest it; declared consumers become
  verifiable by our own lineage machinery. The product governs
  itself with itself.

## The presentation doctrine (Sunny's reframe, 2026-08-25)

AIVIA delivers THE MAP, NOT THE VERDICT. Answer-time surface:
matches-with-differences (every matching definition, diffed by
path/persona/grain/codeset — the variant map IS the answer; choose
follows). Estate surface: the DIFFERENTIATION QUEUE (the flag
objects, reframed — addressable nouns the disposition acts attach
to), usage-ranked, never a violations list. Alarm semantics
reserved for the defect class alone (invalid vocab, typos, mandate
violations — the one place wrongness exists). Detection machinery
identical under both framings; internal table names unchanged; the
reframe lands at the 0056 build.

## Clusters are nodes (Sunny's ruling, 2026-08-25)

Shapes live IN the graph as REIFIED CLUSTER NODES with membership
edges — never pairwise edges (N-member clusters explode O(N²) and
give dispositions no home), never labels alone (no addressable
noun). Structure: name_cluster node → logic_group nodes (the
content-hash partition — identical in shape to the compare verdict)
→ member_of edges. Dispositions, certifications, and 0056 testimony
attach to cluster/group nodes as asserted edges; the governance
stamps become real one-hop edges; census/retrieve traverse instead
of searching a side table. Detection stays DETERMINISTIC
(fold-name, content-hash, token containment, materialized closures
— never stochastic clustering; M4/E2 hold). Migration: the
gov_red_flags table is a serialized cluster set — right design,
wrong residence; it stays authoritative THROUGH THE DEMO, then at
the 0056 build clusters go graph-native and the table flips to a
projection (the contracts-split authority-flip pattern). Cluster
nodes get 0052 registry rows like every payload.

## The formal guarantee (SPEC amendment authorized by ADR 0057)

Three legs:
1. **Reachability** (ADR 0052, enforced): every element reachable
   by a named op ⊎ excluded-with-reason.
2. **Round-trip translatability** (NEW axiom): SQL → meaning
   findable; meaning → SQL findable; the meaning → data leg
   declared incomplete until Pro execution ships.
3. **Answer-or-named-gap totality:** every question answers with
   evidence or refuses with the NAMED reason; never silent, never
   invented. Conditional on the op algebra's expressiveness —
   out-of-algebra questions fail LOUD at plan time (the proven
   boundary; proof where proof exists, disclosure where it doesn't).
