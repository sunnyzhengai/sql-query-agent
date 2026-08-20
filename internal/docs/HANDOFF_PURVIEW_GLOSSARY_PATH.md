# Handoff — Purview glossary path: wire or delete

> **Status (2026-08-18, dev session): implemented in 1.16.1.**
> VERDICT: DELETED per the ghost rule — built ahead of its data, zero callers ever; term MINING (ADR 0031) stays live and tested. ADR 0031 amended with the resurrection requirements (branding from org_config, never env var; target the existing glossary). Glossary tests removed with the surface.

**From:** review session, 2026-08-17 (found while implementing the brand
seam). **To:** dev session.

## Finding

`PurviewAdapter.ensure_glossary` and `publish_glossary_term` (ADR 0031:
business terms at term grain) have **zero callers** anywhere — notebook 09
publishes catalog entities via `publish()` only. The glossary-term surface
is built, brand-seamed (defaults to `product_name()`), and dead.

## Wanted

1. Wire-or-delete decision per the ghost rule. If ADR 0031's term-grain
   publishing is still the plan, wire it from 09 (or a dedicated cell);
   if superseded, delete both methods and note it against ADR 0031.
2. **If wiring:** the glossary NAME must come from org_config (add a
   `branding:` block), NOT from the SQA_PRODUCT_NAME env var — Fabric
   notebooks don't see App Service settings, and the existing tenant
   glossary is already named with the brand. Wiring with the env-var
   default would silently create a second, neutrally-named glossary
   (split-brain catalog).
