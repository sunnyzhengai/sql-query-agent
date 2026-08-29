# ADR 0061 — The run layer: Pro runs the confirmed definition

**Status:** DRAFT 2026-08-28 (overnight) — review-authored from
Sunny's Phase 2 direction ("nobody just wants to ask questions
about metadata; everyone's end goal is to see the data"). Slice 1
is buildable entirely on ratified ground; three open calls await
Sunny's morning (§6).

## 1. The decision

AIVIA executes **confirmed** logic against the customer's source
and shows the data on glass. The loop is plan-confirm-execute-
display applied to data:

```
definition card (phase 1)
  → user CONFIRMS "this is the logic I mean"   [0056 confirm]
  → EXECUTE against the bound source            [read-only]
  → glass shows table (+charts, open call)      [rows to glass]
  → run captured                                [0056 run, weight 8]
```

This is the Pro tier: "Basic governs the definitions; Pro runs
them."

## 2. Inherited laws (ratified; not open for re-debate)

- **P5 absolute:** rows render to the USER'S GLASS and never enter
  the model's context. The model sees machine stamps only —
  row count, column schema, elapsed, as-of, source. Cage-tested.
  This is a differentiator to say out loud: the AI governs the
  question; the database answers it; the model never touches a
  patient.
- **Honest sampling:** every result carries a machine-composed
  label — `N rows · TOP <cap> · as of <timestamp> · source <db> ·
  read-only`. Never model-written.
- **Execution only after confirm.** No auto-run. The confirm is a
  0056 captured decision; the run is a 0056 weight-8 event — the
  strongest flywheel signal.
- **Typed failures** (error-contract philosophy): timeout, denied
  statement, connection failure each render their contract, never
  a stack trace.

## 3. Execution contract (slice 1)

- **Read-only by construction:** dedicated read-only credential;
  AND a ScriptDom statement-type check before execution — only a
  single SELECT statement may run (native-parser law: the parser
  decides, never regex). DML/DDL/EXEC → typed refusal.
- **Bounds:** statement timeout (default 30s), row cap TOP N
  (default 200 — open call), result-size cap.
- **What runs:** STEP SQL — steps are clean SELECT fragments and
  runnable as-is. Whole procedures (wrapping, parameters,
  multi-statement) are a LATER slice, deliberately.
- **Source binding:** `org_config.yaml` new `run:` section
  (connection to the demo SQL endpoint, aivia_shapes_src for the
  demo estate). Local tests run against a bundled fixture DB
  seeded from the palette tables — no tenant dependency in CI.
- **PHI posture:** slice 1 runs on the synthetic demo estate. The
  real-estate output-side PHI gate is DESIGN-REQUIRED before any
  customer source is ever bound (recorded as a listing-blocking
  item, not a slice-1 task).

## 4. Display contract

Results table renders under the §1 loop's conclusion card with
the sampling label; the run stamps join the receipts (folded
rounds). Charts: open call §6.

## 5. What this is NOT

- Not NL2SQL: nothing is generated. The SQL that runs is the
  certified, parsed, displayed step — byte-for-byte what the user
  confirmed on glass.
- Not a BI tool: TOP-N samples answer "is this the data I mean?"
  — the dashboard remains the consumption surface (the pointer
  chase already links to it).

## 6. Open calls (Sunny, morning)

1. **Default sample cap** — 200 rows? (Recommendation: 200,
   configurable per org_config.)
2. **Charts in slice 1?** — Recommendation: NO; table + count
   first, charts as slice 2 once the table loop is trusted. A bad
   chart misleads faster than a bad table.
3. **Re-confirm cadence** — re-confirm every run, or a confirmed
   definition stays runnable from the Ground-Truth Shelf?
   (Recommendation: shelf items stay runnable — the shelf IS the
   standing confirmation; a changed definition invalidates the
   shelf entry via the nervous-system change propagation.)

## 7. Relations

0056 (confirm/run verbs, capture store) · P5 · the tier line ·
PRODUCT_PICTURE.md three-phase roadmap · Ground-Truth Shelf
(shelf items become runnable — film three's beat) · 0038/0058
(multi-persona escalation consumes this layer in phase 3).
