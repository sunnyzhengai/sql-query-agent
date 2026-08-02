# ADR 0014: Ground the Agent in `metric_logic`; Data Dictionary Is Mandatory

**Status:** Accepted
**Date:** 2026-07 (extracted from DEPLOYMENT_CHECKLIST.md "Architecture Decisions")

## Context

The Data Agent could query the raw graph tables (`graph_nodes`/`graph_edges`),
the typed LPG export tables, or a purpose-built flat table. Separately, the data
dictionary was originally optional input.

## Decision

1. Ground the Data Agent in `metric_logic` — a flattened, pre-joined Delta table
   (one row per metric: calculation logic, source tables, descriptions). The
   graph tables remain sources for traversal and the LPG export.
2. The 8 typed LPG tables are exported automatically by the pipeline (no
   customer action) for future Fabric Graph / self-service report generation.
3. The data dictionary (`dict_tables.csv`, `dict_columns.csv`) is **mandatory**:
   without it the agent gives incomplete or misleading answers, and the
   validation gate enforces >90% dictionary coverage before deployment.

## Consequences

- Flat-table grounding is simpler and proven with Fabric Data Agents — no Graph
  Model setup burden on the customer
- Agent answer quality is capped by dictionary quality; DATA_DICTIONARY_REQUIREMENTS.md
  is part of the customer's mandatory prerequisites
- The dual write (flat + LPG) keeps the future graph-backend migration path open
  without re-parsing (see ADR 0002)
