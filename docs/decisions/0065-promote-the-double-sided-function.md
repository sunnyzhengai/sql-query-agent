# ADR 0065 — Promote §13 to Group T: the double-sided function as numbered law

**Status:** ACCEPTED 2026-09-01 — Sunny's ruling ("we should promote
§13") on the crosswalk audit's scope finding. SPEC §13 becomes **Group
T** (T0 the law, T1–T3 its instances); SPEC → v0.9.

## 1. Context — what the crosswalk found

The 2026-09-01 audit established that all 44 numbered spec axioms trace
up to `docs/AI_VIA_AXIOMS.md`. Asked whether *every entry* in SPEC.md
traces up, the honest answer was **no**: SPEC contains normative prose
carrying no axiom id, and §13 was the clearest case.

§13 states, in the document's own words, **"THE LAW"**:

    κ(ρ(τ(t))) = κ(t)

and names three instances. Only instance 1 (descriptions) had an id —
`spec:F` — so the crosswalk covered one third of a section that calls
itself a law. Instances 2 (SQL stitching) and 3 (definition creation)
were unnumbered, uncitable, and unchecked.

This is the same failure class as ADR 0064's: **law the codebase
believes but the axiom system never numbered.** SPEC §1 claims to be
closed; un-numbered law is a hole in that claim, and Group P's
year-long invisibility (ratified, ENFORCED, uncitable) showed what
happens when an id is missing.

## 2. Decision

§13 becomes **Group T** — T for the τ/ρ transform pair. (T is free; the
existing groups are A–H, L, P, Q, R.)

- **T0 — the round-trip law.** `∀t. κ(ρ(τ(t))) = κ(t)`. Status
  **PARTIAL**: the law is only as strong as its weakest instance, and
  averaging three different judges into one status would be dishonest.
- **T1 — descriptions.** ENFORCED. This is `spec:F` restated as a
  member of the family; F remains its own axiom, T1 names its role in
  the law. No new mechanism.
- **T2 — SQL stitching.** PARTIAL, with the gap stated (below).
- **T3 — definition creation.** JUDGED, not tested — the human is the
  judge by construction (§14d, L3 stratum).

## 3. The T2 finding (the reason this promotion is worth doing)

Numbering the instances forced a status for each, and T2's is the
finding:

`src/run_layer.py::check_single_select` parses every statement through
ScriptDom before execution, so **parseability** round-trips — a
malformed compile fails closed with a typed refusal. But there is **no
κ-equality diff** between the compiled tree and the source tree. The
judge answers *"does this parse?"*, not *"does this mean what the user
confirmed?"*

**The exposure is latent, not live.** `spec:R7` requires the executed
SQL be byte-for-byte the confirmed step — nothing is compiled at run
time today, so there is no compiled tree to diverge. The gap becomes
live the moment fragment stitching ships (ADR 0003's fragments
recomposed into executable SQL), which is exactly when tier 2's
self-service path needs it.

**Recorded, not built.** Building a κ-diff for a code path that does
not exist would be speculative. T2 carries the stated gap so the
requirement is visible at the design review that ships stitching —
§3b's drift question, asked in advance.

## 4. What this is NOT

- **NOT a new mechanism.** T1 and T3 cite what exists; T2 states a gap.
  Zero new checks ship with this ADR. The value is that three
  previously-unnumbered laws are now citable, statused, and covered by
  the crosswalk.
- **NOT a demotion of spec:F.** F stays. T1 names F's role inside the
  double-sided law; the two are the same obligation seen from two
  angles.
- **NOT a claim the law holds end to end.** T0 is PARTIAL and says so.

## 5. Consequences

- SPEC's un-numbered normative prose shrinks to §3b (a review ritual,
  correctly not an axiom) and §14d (testing strata, where `axm:J3`
  lands). The crosswalk's scope section records both.
- Three new ids join `SPEC_AXIOMS`; `SPEC_TO_AXM` maps them (T0/T1 →
  `axm:J4`; T2 → `axm:J4`, `axm:B1`; T3 → `axm:M5`, `axm:J2`).
- The T2 gap is now a citable requirement (`spec:T2`) rather than a
  paragraph someone might not read.

## 6. Relations

- **ADR 0044** — instance 1; the round trip's original mechanism.
- **ADR 0064** — the sibling promotion; same failure class (law
  enforced or believed, never numbered).
- **ADR 0047 §16** — the amendment rule that requires this ADR.
- **ADR 0061 / `spec:R7`** — why T2's gap is latent rather than live.
- **`axm:J4`** — "every transformation carries formal judgment," the
  framework law the whole group descends from.
