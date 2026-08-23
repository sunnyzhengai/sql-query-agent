# Walk verdicts — 1.52.3, Sunny's session of 2026-08-21 (evening)

**From:** Sunny + review session. Passes confirmed: census (28),
ED-logic token fix (2), anaphora-by-pronoun (122 steps), sql_request
(verbatim), definition (Sepsis Case Encounters), IP_SEPSIS
source-table note (fired as designed). Anti-flail visible and benign.
Four finds, typed and routed:

## Find 1 — REJECTED: drilldown answered by census-dodge (engine, M2)

"In Severe Sepsis Episodes, how is a patient diagnosed with severe
sepsis" ran census-contains, answered from the two DESCRIPTIONS, and
verdicted "answered (evidence verified)" — actual codes/thresholds
absent. The mind never retrieved the metric record (which, per the
R11 headline, already carries the top-12 decision sites inline).
Typed: DUMB under the ratified floor (quotes verified, nothing
invented) — but it is Sunny's original rejection recurring via a new
path: the census route satisfies the verdict without depth. Fixture:
this exact phrasing must reach the record/sites. The M2
materialization pass is the fix's home; note the walk shows the
inline top-12 already renders on retrieve — the gap is the mind
answering from census instead of retrieving when the question is
decision-grade. Watch that the fix stays data/verdict-shaped (e.g.
the depth stamp demoting the verdict when a decision-grade ask is
answered without any site rows displayed) — no prompt casebook.

## Find 2 — THE BIG ONE: poisoned stored descriptions (data layer, 0044/0019)

Multiple metric descriptions claim "without applying any filtering
decisions" / "no filtering criteria applied" — on metrics carrying
HUNDREDS of decision sites (USP_Severe_Sepsis: 427). The Severe
Sepsis answer was internally contradictory: "diagnostic codes and
clinical indicators as defined in the calculation steps" AND
"aggregating from 122 steps without applying any filtering
decisions." Likely root: the metric-grain description faithfully
reports that the FINAL_SELECT step has no WHERE, then over-scopes
that fact to the whole metric. This is a truth defect in stored
artifacts — the engine faithfully repeated a misleading description.
Route: the description pipeline (600 / tree-contract), not the
engine. Rule to implement: a metric-grain description may not make
absence-of-filtering claims scoped beyond its step; when decision
sites exist, the description voices their existence and count.
Regenerate affected descriptions; add the corpse as a description
fixture. (Note: this is exactly what ADR 0044's round-trip verifier
should catch when phases 2–3 ship — a blind reconstruction of "no
filtering decisions" yields a tree with zero decision sites, and the
judge's diff against 427 fails. This find is the standing argument
for finishing those phases.)

## Find 3 — caption misattribution over correct stamps (engine, grading)

"How is IP_SEPSIS defined": the stamp correctly listed the 5 READERS
(Sepsis Bundle Compliance Metrics, ...by Shift, Case Details, Case
Encounters, Screening Tool Results). The commentary presented a
reader list that SWAPPED two readers for near-name procs from the
did-you-mean stamp (USP_IP_SEPSIS_COMPLIANCE,
..._COMPLIANCE_BY_SHIFT_NURSES) — attributing reader status to items
the stamp never claimed read the table. The honesty gate could not
catch it: every name appears on screen, so quotes verify — the
string-space gate is blind to the RELATIONSHIP claimed (0044's
founding lesson at caption grain). Typed: misattribution (dumb
class, but flag for grader visibility). Fixture + candidate
data-shaped fix: when a readers stamp is on screen, the floor/answer
echoes the stamped reader list verbatim as a rendered list, LLM
narrates around it — list identity becomes machine-rendered, not
model-copied.

## Find 4 — lineage question routed to mention-census (reachability)

"Is there any other metrics using IP_SEPSIS?" ran census-contains
(name/description MENTIONS) — honestly scoped, floor caught two
invented counts — but "using" is the READER relation, which today is
reachable only as the passive empty-result note. Promotes the
reachability roadmap's tables/columns item: a first-class
readers-of-table op (the uses closure, already materialized in the
graph) so lineage questions route to lineage, not mentions. This is
dev's audit rank-3 item, now with a walk corpse.

## Standing instructions

- All four become fixtures before their fixes ship (real-corpses).
- Finds 1+3 stay inside ADR 0050/one-mind bounds: data-shaped or
  verdict-shaped, zero prompt casebook, pin intact.
- Find 2 regenerations flow through the content-hash cache and PHI
  gate as usual; TREE/PROMPT version bump per the 0044 mechanism so
  stale certified text cannot survive.
- Receipts row still held — walk finds 1 and the anaphora residual
  share the same M2 resolution; claim after it lands and measures.
