# 0049 — Ingestion routes: filedrop, folders, and the live extractor are peer front doors

**Status:** Accepted (retroactive record, 2026-08-20 — the first ghost
finding of the ADR 0048 totality check)
**Date:** 2026-08-20 (decision made earlier via
internal/docs/HANDOFF_INGESTION_ROUTES.md and
docs/architecture/SOURCE_CONNECTORS.md (location note 2026-09-02: retired into src/integration_registry.py by ADR 0069; git keeps the original); recorded as an ADR when the
trace registry's ghost rule flagged the implementing modules as
uncited by any decision)

## Context

SQL logic reaches the pipeline through more than one honest route:
customers drop .sql files (010), point at OneLake folders (020), or
connect live to a database and extract view/procedure definitions from
system catalogs (030). The route landscape — including the on-prem
extractor-script route for hospitals with zero inbound connectivity —
is designed in docs/architecture/SOURCE_CONNECTORS.md (location note 2026-09-02: retired into src/integration_registry.py by ADR 0069; git keeps the original). The live
extractor was built against that design but the decision was never
recorded as an ADR.

## Decision

The three ingestion routes are peers converging on one contract:
whatever the route, output lands as `input_sql_sources` rows with
`metric_id` identity (ADR 0015) and flows through the same parse door
(ADR 0001). The live route is implemented by `src/extractor/`:
connection handling (`connection.py`), catalog discovery
(`discovery.py`), change tracking (`tracker.py`), and orchestration
(`extractor.py`) — sources are discovered, tracked for change, and
formatted; never silently dropped (conservation, spec:C2 spirit).

## Consequences

- The ghost rule works: uncited code surfaced within hours of the
  totality check existing, and the fix was recording truth, not
  inventing lineage.
- Future routes (gateway, RDL, DevOps repos) extend SOURCE_CONNECTORS
  and this ADR's route table; each new route cites this decision.
