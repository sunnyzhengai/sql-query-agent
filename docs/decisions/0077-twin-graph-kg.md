# ADR 0077 — The twin-graph KG: meaning is a stored homomorphic twin

**Status:** ACCEPTED 2026-09-06 — Sunny's ratification, same-day
paragraph-by-paragraph review ("all good, go with your
recommendations"). **Component:** the knowledge graph (meaning
layer). **Full ruling + change ledger:**
`AIVIA_Design/Twin_Graph_KG_RULING.md` — this ADR is the decision
record's pointer per the doc hierarchy; rationale lives there.

## Decision (one paragraph)

Meaning stops being computed-on-read by lenses and becomes a STORED
GRAPH: KG2b, the homomorphic twin of the parsed graph — every parsed
node translated or counted, at every grain, composite nodes composing
their children's meanings. Three layers (KG1 declared/fused, KG2
derived/twinned, KG3 governance overlay anchored to meaning
identity); three builders (loader, parser, TRANSLATOR — the
"translation lens" renamed to what it is); the lens stratum retires
into builder + reading contracts; voicing becomes policy over the
twin (select-never-compress, the voicing ledger); change quanta
(data changes incremental per layer quantum, rule changes total).

## Origin

ED-sepsis gap-check findings 3 and 4 (invisible ON-filters; invisible
composition) traced to one generator: the flat-set yield shape of the
decisions lens — a field-era patch ratified by restatement. This ADR
is the first-principles re-derivation (the design-first-triage rule,
set the same day). Generalizes ADR 0076 (capture once, interpret by
grammar) from expression grain to the whole tree.

## Landed 2026-09-06 (documents and registries; NO code)

- `AIVIA_Design/Twin_Graph_KG_RULING.md` — the ruling, ratified
- `AIVIA_Design/AIVIA Design Document.md` — L0 rewritten as the
  blueprint; body sections carry dated AMENDED/SUPERSEDED blocks
- `AIVIA_Design/Floor_Grammar.md` — R9 retired into voicing policy
- Registries v1.1.0 (all seven; validator green): meaning-node
  kinds · Meaning_Twin sheet · Incremental_Intake ·
  lens Reclassification (builders/readings/queries) · governance
  overlay merge + anchor rule · Change_Quanta + Twin_Graph_Phasing
- `L1_KG1_CONTRACT_DATALOAD.md` §13 — incremental intake
  (content_hash, equivalence audit, INTAKE-11/12/13)

## The spec ledger plan (ADR 0073 rule honored)

`src/spec_registry.py` is NOT pre-amended: its closed status
vocabulary (ENFORCED/PARTIAL/GATED/JUDGED) describes implemented
behavior, and none of this is implemented. Each phase's ADR lands
its axioms with real statuses and checks: Phase A (projection
conservation), Phase B (homomorphism, content_key laws), Phase C
(the voicing ledger), Phase D (the anchor rule). Phasing is ruled
in the ruling 5d and the flows registry; each phase gates on a real
ED-sepsis gap-check.

## Relations

0076 (the expression-grain precursor, generalized) · 0044 (the
conservation law, generalized from predicates to all nodes) · 0074
(the description architecture this supersedes in part: the skeleton
composer's rules survive as voicing policy) · 0073 (the spec
amendment rule this ADR schedules against) · Floor_Grammar
v1.0.0–v1.3.1 (the truth rulings, all carried forward).
