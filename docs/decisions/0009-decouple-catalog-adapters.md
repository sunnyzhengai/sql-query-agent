# ADR 0009: Catalog Integrations Are Optional Adapters

**Status:** Accepted
**Date:** 2026-07-25 (extracted from MARKETPLACE_PIVOT.md D2)

## Context

Not every org has a data governance tool, and those that do don't all have the
same one (Collibra, Purview, Alation). Bundling any one integration into the
core product blocks the broad product on the narrowest feature.

## Decision

The core product works standalone. Each catalog integration is a separate
adapter module in `src/adapters/` behind the `CatalogAdapter` protocol, enabled
per-customer via the `adapters:` section of `org_config.yaml`.

## Consequences

- A catalog-agnostic `MetadataRecord` model decouples generation from publishing
- New catalogs are additive work (new adapter), never core changes
- Each adapter carries its own credentials and API surface, tested independently
