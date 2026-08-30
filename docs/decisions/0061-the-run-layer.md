# ADR 0061 — The run layer: Pro runs the confirmed definition

**Status:** ACCEPTED 2026-08-29 — review-authored from Sunny's
Phase 2 direction ("nobody just wants to ask questions about
metadata; everyone's end goal is to see the data"); slice 1 built
and verified 2026-08-29; all three §6 calls RULED by Sunny
2026-08-29 (cap 200 · no charts slice 1 · shelf-standing runs).

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

1. RULED (Sunny, 2026-08-29): cap 200, org-configurable.
2. RULED (Sunny, 2026-08-29): NO charts in slice 1 — tables until
   the run loop earns trust on glass.
3. RULED (Sunny, 2026-08-29): shelf items STAY RUNNABLE — the
   shelf is the standing confirmation; change propagation
   invalidates a shelf entry when its definition changes.

## 7. Relations

0056 (confirm/run verbs, capture store) · P5 · the tier line ·
PRODUCT_PICTURE.md three-phase roadmap · Ground-Truth Shelf
(shelf items become runnable — film three's beat) · 0038/0058
(multi-persona escalation consumes this layer in phase 3).
