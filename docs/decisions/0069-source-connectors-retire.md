# ADR 0069 — SOURCE_CONNECTORS retires into the integration registry (ratchet turn 3)

**Status:** ACCEPTED 2026-09-02 — Sunny's order, executing ADR 0067.
The first ratchet turn that RETIRES a file.

## Why absorption, not conversion

The planned move was a new `connector_registry`. Reconnaissance killed
it: `src/integration_registry.py` already owns the connector landscape,
is CURRENT (the doc was dated 2026-08-11 — before ADR 0049 shipped the
live extractor — so its priorities had drifted), and its generated map
already declared itself the superseder of connector tables. A parallel
registry would have minted a rival truth — `axm:D2`, one owner per
capability, forbids exactly that. So the doc's content went home:

- **Part 1 (the configuration space)** → 8 new registry rows (Synapse,
  RDL, Dataflows, XMLA, ADF, SSIS, pure-M, Oracle), each carrying its
  ex-SOURCE_CONNECTORS id and priority in `notes`. Configurations that
  already had rows needed nothing — the registry had overtaken the doc.
- **Part 2 (the SourceConnector protocol sketch)** → history. Reality
  shipped `src/extractor/` with three connection profiles instead of
  the sketched `src/connectors/`; the landing contract
  (`input_sql_sources`) held. The sketch's value is archaeological —
  git keeps it.
- **Part 3 (change monitoring)** → `CHANGE_TRIGGERS` + `CHANGE_PAYOFF`
  records. The core mechanism (collect + content-hash diff) SHIPPED as
  `src/extractor/tracker.py`; the three triggers stay doctrine.
- **Part 4 (object identity)** → `IDENTITY_RULE`, `IDENTITY_LADDER`
  (each step TYPED per spec:E3 — computable vs judgment, the steward
  never auto-merged), `NATIVE_STABLE_IDS`, and Sunny's 2026-08-11
  shipping decision (v1 ships the limitation, loudly) — all data,
  rendered into INTEGRATION_MAP.

## Also fixed at source

The Databricks/Snowflake rows' mechanism notes still planned a
"sqlglot dialect" — the same ADR-0001 contradiction fixed in
REFERENCE_ARCHITECTURE on 2026-09-01, now corrected where it lives.
A closure check keeps banned parsers out of planned mechanisms.

## Consequences

- `docs/architecture/`: 12 files (6 authored + 6 generated).
- The `connectors` component merges into `integration` (3 ADRs
  re-route; satisfies = D, B, R; stamp → 0069).
- ADR 0049's design-source pointer gains a location note.

## Relations

0067 (the ratchet) · 0009 (the registry absorbed into) · 0049 (the
extractor that outran the doc) · 0022/0016/0015 (the identity trio).
