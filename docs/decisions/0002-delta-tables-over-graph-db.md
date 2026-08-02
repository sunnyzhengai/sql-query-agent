# ADR 0002: Delta Tables over an External Graph Database

**Status:** Accepted
**Date:** 2026-07 (recorded 2026-08-02)

## Context

The three-layer knowledge graph needs a storage backend. Neo4j (or another
dedicated graph database) is the conventional choice for graph workloads, but it
would sit outside the customer's Microsoft Fabric tenant.

## Decision

Store the graph as Delta tables (`graph_nodes`, `graph_edges`) in the customer's
Fabric Lakehouse. Additionally export typed LPG tables (4 node tables, 5 edge
tables) so a native Fabric Graph backend can be adopted later without re-parsing.

## Consequences

- Stays entirely inside the Fabric ecosystem: no external DB to manage, no extra
  auth or networking, consistent with the BYOT security story (ADR 0007)
- Natively queryable from Notebooks, the Data Agent, and Power BI
- Multi-hop traversal is less natural in flat tables; a hybrid is planned —
  Delta for metadata search, Fabric Graph for deep traversal (LPG export tables
  already use camelCase columns as Fabric Graph NL2GQL requires)
