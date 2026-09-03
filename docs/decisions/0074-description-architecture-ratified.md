# ADR 0074 — The description architecture, ratified: skeleton floor, gate acceptance, and the metric-level design (amends 0044 phase 3, 0019)

**Status:** ACCEPTED 2026-09-02 — Sunny ratified all four §5 calls
as recommended, same day ("ok to your recommendations"). Spec
amendments landed with ratification: `spec:B2`'s vocabulary is now
{gate_passed, skeleton_floor, flagged}; `spec:F`/`T1` are re-scoped
as the MEASUREMENT INSTRUMENT. The call-3 sub-ruling
landed 2026-09-02: **empties = (a)** — see §5.3a.

## 1. Context — how the design went unrecorded

The wedge evaluation found metric descriptions under-planned; this
ADR's audit found why. Between 2026-08-31 and 09-01 the description
pipeline went through five architectural pivots — recorded ONLY in
commit messages and handoffs, and the handoffs were then deleted in
the internal/docs cleanup. Under ADR 0067 the design must exist as a
record with checks; this ADR is that record's rationale.

**What ADR 0044 designed** (2026-08-19): typed tree facts → translator
(never sees SQL) → blind round-trip verifier → deterministic κ-judge →
template floor; provenance ∈ {round_trip_verified, template_fallback,
flagged}.

**What actually runs** (reconstructed from the commit trail + code):

- **0044 phases 1–2 are LIVE and held.** Production (600 →
  `generate_descriptions`) builds the decision tree and calls
  `translate_tree`; `TREE_CONTRACT_VERSION` participates in cache
  keys. The translator-blindness design worked.
- **Phase 3's acceptance was substituted in the field.** The blind
  verifier was never wired (the long-stated "phase 3b" gap). In its
  place, incident by incident: the GROUNDING GATE grew classes
  (values → claims → tables → grain → voice: misattributed
  predicates, dictionary-as-substitutions, tech-vocabulary ban) with
  corrective retry; then **DESC-MEANING-1, the reframe** — *parse
  gives structure, the dictionary gives meaning, a deterministic
  SKELETON composes them; the model only smooths, and the skeleton is
  the floor so nothing empties* (0 empty on 20 live steps); then
  DESC-TEMP-1 (temp-table steps: 26 → 413 describable steps — 23 of
  28 real procs stage through temp tables, not CTEs); then
  DESC-SKELETON-3, the AST-first composer (the ScriptDom node held
  and passed down; regexes deleted and CI-banned, GATE-REGEX-1).
- **In flight when work stopped:** DESC-SKELETON-3a — derived-table
  filters leak into the outer step (ordered in the final pre-cleanup
  commit, 8a8f13d; unbuilt).

The skeleton is 0044's own logic completed differently: it is
**unfalsifiable by construction** (every element from the parse or
the dictionary), which is the same property the template floor had —
but composed well enough to BE the description, not a stilted
fallback.

## 2. Decision (proposed)

1. **Ratify the field architecture as 0044's phase-3 amendment.**
   Acceptance = grounding gate (closed violation classes) + bounded
   corrective retry + **skeleton floor**. The blind round-trip
   verifier is re-scoped per call 1. Clauses 1, 2, 4, 5 of the tree
   contract stand untouched; clause 6's floor is the skeleton; clause
   3 follows call 1.
2. **The metric-level design** (the gap the wedge evaluation found):
   - 0019's composition survives with its premise fixed: metric
     description ← composed from its **terminal steps** (CTE or
     temp-table alike), not "root CTEs" — the real estate broke the
     CTE-only premise 23/28.
   - **The deliverable is a description per SQL FILE** (DESC-FILE-1,
     ruled 09-01 by commit, ratified here): single-statement procs
     are one block; multi-step files compose from described steps;
     coverage is measured in files described.
3. **Provenance vocabulary reopens** (amends `spec:B2`'s closed set)
   per call 2 — the shipped outcomes (gate-passed smoothed prose;
   skeleton floor) have no name in {round_trip_verified,
   template_fallback, flagged}, so today's output is unlabelable.
4. **The wedge description contract** (closes the 0063 gap): the
   X-Ray report carries a hand-gradable description SAMPLE with
   provenance chips (call 4); Bridge's Write-Back Queue accepts only
   gate-passed or skeleton-floor content, and the landing matrix A5
   grade names the provenance it lands.

## 3. What this is NOT

- NOT a weakening of 0044's joint property. "A false statement has no
  constructible path into a published description" is preserved by
  different machinery: translator blindness (live), the gate's closed
  claim classes, and a floor that cannot fabricate. The trade: the
  round trip PROVED faithfulness per description; the gate CHECKS
  claim classes — narrower per-instance proof, vastly better field
  yield. Stated, not hidden.
- NOT new design — the opposite: recording design that already runs,
  so the next agent reads an ADR instead of archaeology.

## 4. Spec amendments (land on ratification, not before)

- `spec:B2`: provenance set becomes the ratified vocabulary (call 2).
- `spec:F` / `spec:T1`: status notes gain "production acceptance =
  gate + skeleton floor (ADR 0074); the round-trip machinery's role
  per call 1" — the T2 lesson (checked ≠ shipping) applied to
  descriptions.
- Ledger rows F/T1/B2 updated; TEST_MAP/crosswalk regenerate.

## 5. Calls — ALL RULED 2026-09-02 (as recommended)

1. **The blind verifier's fate.** (a) RECOMMENDED: retire from the
   production path, keep as a MEASUREMENT instrument (nightly/corpus
   runs grading gate output — the reviewer the single-session era
   lost); (b) wire it as phase 3b after all (cost: 2–3 LLM calls per
   changed step); (c) delete outright.
2. **Provenance names.** RECOMMENDED: `gate_passed` (smoothed prose
   that cleared the gate) · `skeleton_floor` (deterministic
   composition, unfalsifiable) · `flagged` — replacing the 0044
   triple; `template_fallback` retires with its mechanism.
3. **Metric/file-level ratification.** RECOMMENDED: §2.2 as written
   (terminal-step composition + per-file deliverable). Fold in the
   still-parked empties ruling (BOARD: the word "table" empties true
   descriptions — options a/b/c) — it blocks the file-level
   composition's edge cases.

   **3a. THE EMPTIES SUB-RULING — Sunny, 2026-09-02: option (a).**
   Accept empties as the floor; the field stays absent. As posed
   (08-31): (a) absence over fabrication · (b) machine-composed
   fallback so nothing empties (review's recommendation) · (c)
   loosen the voice rules. The world moved between posing and
   ruling — DESC-MEANING-1 built the skeleton floor, which is (b)
   system-wide for GROUNDING failures — so (a) governs the
   RESIDUAL, and the precedence is now law:

       voice/gate kill  >  skeleton floor  >  absent

   Nothing empties for lack of grounding (the skeleton composes);
   a description may empty by VOICE — a grounded, true sentence
   killed by the vocabulary rule stays killed, and the field goes
   absent rather than the ban loosening.

   **3a-1. THE KILL UNIT — Sunny, 2026-09-04: the SENTENCE.** A
   voice violation kills the violating LINE; the remaining true
   bullets ship; every dropped line is COUNTED (a per-step
   `killed_lines` accounting beside `emptied`). The whole step
   empties only when no line survives. This is the ruling's own
   wording taken literally ("a grounded, true sentence ... stays
   killed") — the ban never loosens, but one unvoicable line no
   longer destroys five true ones. Ordered with the 09-03 estate
   evidence: 17 residual whole-step empties, most carrying
   majority-true bullets. This simultaneously rules
   the sibling parked item (the word "table" on temp-staged steps):
   the ban STAYS; `TestTempStepVoiceCost`'s pinned behaviour is now
   the ruled behaviour. Empties are COUNTED (the DESC reports'
   `emptied` column; D1 carries the count into the coverage
   ledger), never silent — absence is honest only when visible.
4. **The wedge sample.** RECOMMENDED: yes — the X-Ray report includes
   N sampled descriptions with provenance chips; it is the Bridge
   order form's evidence ("accurate descriptions your stewards never
   write"), and P0's whole rationale was proving it before
   integration.

## 6. Relations

0044 (amended: phase 3) · 0019 (amended: premise + deliverable unit) ·
0067 (why this must be a record) · 0063/P0 (validate before
integrate — the wedge's proof burden) · 0042/0001 (GATE-REGEX-1 is
their pattern) · DESC-SKELETON-3a (the open defect, on the BOARD).
