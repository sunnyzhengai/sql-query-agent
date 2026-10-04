# debug01 — the "Who's in it" experiment

Date: 2026-10-03. Sunny's experiment, verbatim; Claude's answers
and the findings that followed. File under test:
COOK_RPT_USP_CCHCS_ADT_MONTHLY_INPATIENT_CENSUS_TOTALS_SSRS.

## Sunny's two questions

1. Can you read the sql file and tell me "who's in it"?
2. Can you then read the floor of the file and tell me
   "who's in it"?

## Claude's two answers

FROM THE RAW SQL:
> Daily inpatient census events — one row per patient, per day,
> per bed they occupied — for dates between @StartDate and
> @EndDate as the data stood on @AsOfDate, limited to the chosen
> service areas and locations, excluding eight procedural and
> behavioral departments (ORs, cath lab, IR imaging, PHP
> psychiatry).

FROM THE FLOOR ONLY:
> Event records of category '6' with a recorded patient ID, in
> the date window, not deleted as of the as-of date, in the
> chosen service areas and locations, excluding eight named
> departments.

THE CONFESSION: answer 1 is better ONLY because Claude used
knowledge from outside the estate — that CLARITY_ADT is Epic's
admission/discharge/transfer table and that EVENT_TYPE_C = 6
means "Census". Strip that and answer 1 collapses into answer 2.

## Finding 1 — why category '6' is not mapped

The chain is intact until the last link:
- Epic's own metadata DECLARES the route:
  CLARITY_ADT.EVENT_TYPE_C -> ZC_EVENT_TYPE.EVENT_TYPE_C — the
  join row is IN the 02 join extract.
- But that row carries destin_in_scope: FALSE — ZC_EVENT_TYPE
  was never pulled into the 02 extraction scope. It has no rows
  in the column sheet and no rows in the value sheet (the value
  sheet covers 20 tables; ZC_EVENT_TYPE and ZC_EVENT_SUBTYPE are
  not among them).
- So the 05 resolver has the route but no values at the far end:
  the bind stays value_code_unknown territory, the floor
  honestly says '6', the proposer has nothing better, the gate
  refuses everyone's Epic memories.

THE FIX (Sunny's hand, the flywheel's exact mechanism): extend
the 02 extraction scope to ZC_EVENT_TYPE + ZC_EVENT_SUBTYPE
(columns + values). Then mechanically: the floor says "the event
record category is 'Census' (6)", and "Who's in it" writes
itself at every layer.

THE GENERALIZATION: destin_in_scope=False join rows whose source
column the corpus actually FILTERS ON are a ready-made,
queryable scope-expansion queue — the dictionary grows exactly
where the SQL proves it matters.

## Finding 2 — is "deterministic technical description first"
## still valid?

YES — and this experiment is the proof, not the doubt:

- Compare the two answers: the floor preserved EVERY fact the
  SQL held. The delta between answer 1 and answer 2 is exactly
  the knowledge that lives in NEITHER source — Epic domain
  memory. The floor is not the bottleneck; dictionary coverage
  is.
- The floor even BEAT the raw SQL on one axis: the SQL's
  department exclusion list is eight bare codes; the floor
  speaks their names ('CCMC MAIN OR', 'CCMC CATH LAB'...) —
  because the floor is where dictionary meanings get injected.
  A raw-SQL-reading LLM would NOT have had those names.
- And the floor is the only CHECKABLE substrate: the gate
  verifies business claims against stored sentences; it cannot
  verify against raw SQL plus a model's memories. Drop the
  floor-first strategy and the no-lie guarantee goes with it.

ONE HONEST CONCESSION: the floor's prose can be awkward ("the
unit of the event record at the effective time ID"), which is
noise the proposer wades through. If evidence ever shows the
prose itself misleads proposals, the docket can gain a
STRUCTURED facts block beside the prose — an upgrade to the
docket, not a retreat from the strategy.

VERDICT: keep the strategy; fix the data. One extraction-scope
row does what no prompt engineering can.

## debug02 — the A/B gate experiment (Sunny's protocol, 2026-10-03)

Protocol: same file, same docket (with table descriptions + the
Census meaning). RUN 1: no rules, no gate, one bare call. RUN 2:
the full rules prompt + ONLY the six surviving v2 gates (quoted
values + numbers must be in docket; never-list; SQL-word/@token
ban; template; budgets; must-say). NO word whitelist.

RUN 1 OUTPUT (ungated, verbatim):
> Who's in it: Patients with ADT "Census" events (valid patient
> ID) that match the selected service areas/locations and were
> created before @AsOfDate.
> Each row shows: event type & subtype, scheduled timestamp and
> census day, patient ID and patient class, department & service,
> room & bed, ADT event ID, dept/room/bed IDs, created_at and
> deleted_at, service area.
> Time window: Events scheduled >= @StartDate and <= @EndDate
> (EndDate treated inclusively via DATEADD); dataset evaluated as
> of @AsOfDate — canceled events kept only if deleted on/after
> DATEADD(D,1,@AsOfDate).
> Excludes: records without patient ID; these specific units:
> CCMC EMERGENCY, ... DSC OR; canceled events deleted before the
> evaluation cutoff; locations/service areas not in the input
> parameter lists.

RUN 2 OUTPUT (v2-gated — PASSED ROUND 1, zero repairs):
> Who's in it: hospital event records of census type for
> encounters with recorded patient identifiers.
> Each row shows: event type and subtype, scheduled and audit
> timestamps, patient and location details.
> Time window: configured start-to-end window for scheduled
> event times.
> Excludes: non-census events; no patient identifier; outside
> start-end window; canceled deleted before as-of; listed
> locations

CLAUDE'S SCORING (claim-by-claim vs the SQL):
- RUN 1 accuracy ~90%: rich and mostly right (names all 8
  departments; the cancel logic correct) BUT: "created_at /
  deleted_at" are INVENTED column names; "created before
  @AsOfDate" is an off-by-one (truth: through @AsOfDate); and
  the register is wrong for a business user — @tokens, DATEADD,
  ">=", a full field inventory. Cheap v2 gates would catch every
  register violation (@token, template, budgets); the off-by-one
  only a human or verifier catches.
- RUN 2 accuracy ~100%, register clean, ZERO gate-ese — but
  terser and less specific ("listed locations" instead of the
  eight names; "details" as a kind). Budget pressure shows in
  the telegraphic Excludes phrases.

VERDICT:
1. The docket drives accuracy — even ungated, the model is ~90%
   right BECAUSE the floor + dictionary are under it.
2. The word whitelist was the gate-ese generator: removing it
   cost ZERO accuracy and bought first-round convergence.
3. What cheap gates are FOR: register and structure (run 1's
   @tokens/inventory die mechanically). What HITL is FOR: the
   off-by-one class — semantic slips in fluent English that no
   deterministic check sees.
4. Open dial for Sunny: the S8 budget may be ONE notch too
   tight (run 2's telegraphic Excludes).
