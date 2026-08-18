# 0031 — Business terms: a weighted plurality, citizen-endorsed, steward-arbitrated

**Status:** Accepted — amended 2026-08-18
**Date:** 2026-08-08

## Context

The same business concept is defined in multiple places with — sometimes
— different logic: a metric whose report is *about* cancelled
appointments, and a CTE named `CancelledAppts` inside a diabetes metric,
may not agree. Today those definitions are findable individually
(transformation catalog, business names) but nothing represents the
*concept* they both implement, so answers can't say "two certified
definitions of this exist," and Purview receives asset descriptions but
no glossary.

The governance stance (Sunny, 2026-08-08, extending ADRs 0021/0023/0024):
**citizens are stewards.** When a user selects a business term and
affirms it, that endorsement adds weight. Multiple definitions of the
"same" concept may legitimately coexist — named distinctly so humans can
tell them apart — and their relative weights speak for their legitimacy.
Nobody is forced onto one certified definition; the steward intervenes
only when a definition is demonstrably wrong.

## Decision

1. **Business terms live in governance tables, projected into the graph.**
   The graph is overwritten every pipeline run; terms are durable,
   human-owned truth — so `gov_business_terms` (+ links, endorsements)
   is the source of truth, and 03 *projects* terms into the graph as
   nodes/edges each build (the steward-assignment pattern). Resolution
   catalogs include terms; agents can answer "what does X mean?" at term
   grain.
2. **One term = one definition; the concept is a family.** A term row
   carries exactly one definition. Sibling definitions of the same
   concept share a `concept_key` and carry distinct names
   ("Cancelled Appointment (scheduling)", "Cancelled Appointment
   (diabetes cohort)"). Answers about a concept surface the whole
   family with weights — plurality is disclosed, never collapsed.
3. **Links, not copies:** `gov_term_links` connects a term to the assets
   that define/implement it — canonical metrics and transformation steps
   today, DAX measures when that lane ships. A term may link many
   assets; an asset may implement many terms.
4. **Weight is derived, never stored** (ADR 0023 discipline):
   `gov_term_endorsements` is an append-only log of citizen actions —
   `endorse` ("I used this and it's what I meant") and `dispute`. Weight
   = f(endorsements, ask-time usage, implementation count). High weight
   = legitimacy signal, disclosed in answers and catalogs.
5. **Steward arbitration, not steward gating** (ADR 0021): term status
   `emergent | certified | disputed | retired` discloses trust and never
   hides a term. The steward's job is arbitration — typically triggered
   by a dispute or by a report shown to use a wrong definition — not
   admission control. Certification pins the definition text reviewed
   (ADR 0022 spirit).
6. **Candidates are mined, not authored from blank:** deterministic
   mining over the transformation layer — the same folded step name
   appearing across ≥2 metrics is a candidate concept; same name + same
   fragment hash → one shared definition linking all implementations;
   same name + different hashes → sibling variants, pre-grouped under
   one concept_key for steward review. Mined terms enter as `emergent`
   with `source=mined`; descriptions seed from the steps' generated
   descriptions (ADR 0019).
7. **Purview mapping:** each term row = one Purview **glossary term**
   (Atlas glossary API), with `assignedEntities` = its linked assets —
   Purview natively supports one term assigned to many assets. Purview
   does **not** support one term with multiple definitions, which is
   exactly why sibling definitions are distinct terms (decision 2);
   siblings are cross-linked as related ("see also") terms. Weight and
   status travel in the term's description/attributes. Collibra follows
   the same shape when wired.

## Consequences

- The cancelled-appointments answer becomes first-class: "Two
  definitions exist — [scheduling] (weight 214, certified) and
  [diabetes cohort] (weight 12, emergent) — here's each, and who owns
  what." No static catalog does this.
- The flywheel gains its second loop: answers surface terms → citizens
  endorse → weights shift → stewards arbitrate only where weights and
  disputes say attention is needed.
- Naming discipline is the price of plurality: sibling terms need
  distinguishing names; mining pre-groups them, humans name them.
- Endorsement capture needs an interaction surface (agent feedback or a
  small steward UI) — the contract fixes the shape now; capture wiring
  follows the ADR 0023 usage-event surface.
- Demo path (this listing cycle): mine candidates from the dev corpus,
  author 2–3 terms, push to a short-lived Purview as glossary terms with
  multi-asset assignment — the architecture diagram's Purview edge shown
  live at term grain, not just asset descriptions.


## Amendment (2026-08-18)

The Purview glossary-publishing surface (`ensure_glossary`,
`publish_glossary_term`) was DELETED per the ghost rule — built ahead of
its data, zero callers ever (HANDOFF_PURVIEW_GLOSSARY_PATH). Term MINING
remains live and tested. When the gov_business_terms contracts flip
active and term-grain publishing is scheduled, rebuild the surface with
two recorded requirements: the glossary NAME comes from org_config (a
branding block), never an env var (Fabric notebooks don't see App
Service settings); and wiring must target the existing tenant glossary,
not silently create a second one (split-brain catalog risk).
