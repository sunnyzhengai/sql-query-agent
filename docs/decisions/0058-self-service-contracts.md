# ADR 0058 — The self-service contracts (contracts-first for the Pro pillar)

**Status:** ACCEPTED 2026-08-29 — Sunny ratified C1–C6 with two
rulings: C2 validates TYPES ONLY at parameter sites (allowed-range
checks deferred, addable later without breakage); C4 quarantine
releases on CREATOR CONFIRMATION (steward gate would edge toward
gate-on-certification; stewards see drafts via flags). Build still
lands with Pro; nothing enters the current queue.

Governance's supply side shipped under a full contract regime; the
self-service pillar has design records (the ladder, 0056 P4/P5) but
no contracts. This ADR closes that asymmetry — six contracts, each
with its enforcement point named.

## C1 — The provenance-grade contract (the rungs)

Every executed answer carries a machine-stamped RUNG:
certified-verbatim (1) · parameterized (2) · composed-draft (3).
No execution without a rung classification; rung-3 output is
ALWAYS marked "uncertified draft" on screen and in the graph.
Enforcement: the execution boundary refuses unclassified requests;
the caption gate holds answers to displaying the stamped grade.

## C2 — The parameterization contract (values, never logic)

A rung-2 request is valid iff the parameterized SQL's normalized
AST equals the certified SQL's AST EXCEPT at declared parameter
sites (typed: name, type, optional allowed range). Machine-provable
via ScriptDom diff — parameterization validity is PARSED, never
trusted; injection-safe by construction. Any deviation beyond
declared sites is not rung 2 — it is a FORK (0038 path), and the
engine says so ("logic changed — this becomes your variant").

## C3 — The execution contract (0056 P4/P5, made enforceable)

Passthrough identity — AIVIA holds no data entitlements; the source
database authorizes. Plan-confirm before every run (ADR 0050).
P5 ABSOLUTE: result payloads render display-only and provably never
enter model context — L0-testable (no result object serializes into
history); row counts/timings loggable, values never. Runs mint the
`executed` testimony edge.

## C4 — The composition contract (rung 3: claimed = parsed)

Composed SQL assembles from certified steps + FOUNDATION join paths
(sovereignty precondition — see C5); free generation only for glue,
always displayed, always confirmed. THE CONSERVATION: the
composer's claimed building blocks must equal the parsed lineage of
the draft — every rung-3 artifact is re-ingested through the same
parser as any org artifact, and it is trusted only after its parse
matches its claim (assertion opens, parsing closes — applied to
generated SQL). Mismatch = the draft is quarantined with the diff
displayed.

## C5 — The foundation-sovereignty precondition

Rung-3 composition REFUSES loud when the foundation lacks the
needed join topology: "cannot compose — the join path between X and
Y is not in the foundation" (the honest wall, composition edition).
Never inferred joins; never guessed keys. This makes foundation
completeness a measured prerequisite, not a hope.

## C6 — The flywheel contract (the crossing, conserved)

The governance↔self-service flywheel is enforced as conservation,
not aspiration:
- every run event ⇒ exactly one `executed` testimony edge (no
  unrecorded executions; no phantom edges);
- every rung-3 draft ⇒ an owner (creator, immediately — 0057), a
  provenance grade, and a canonical claim candidate (it ENTERS the
  differentiation machinery like any extracted definition);
- usage weights from executions flow into governance ranking
  (0056 application) — the strongest elector feeds the map.
Audit leg: runs ⊎ edges reconcile; drafts ⊎ owners reconcile;
orphan drafts are a flag class.

## RULED (Sunny, 2026-08-29)

1. C1–C6 RATIFIED (wording amendable at Pro build time).
2. C2: TYPES ONLY.
3. C4: CREATOR CONFIRMATION releases quarantine.
