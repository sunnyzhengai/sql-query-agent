# Handoff — brand-neutral core: no "AIVIA" strings in src/ or numbered notebooks

> **Status (2026-08-17, implemented in 1.13.0 — by the learning session
> in a Sunny-directed role swap):** all six items done. PRODUCT_NAME seam
> (src/branding.py, env SQA_PRODUCT_NAME, neutral default); env renames
> via legacy_env() with constructed legacy prefix (grep-clean) and
> one-release deprecation window (kept because the deployed App Service
> holds the old names — clean break would have broken it); registry
> endpoint token "core"; notebook 11 endpoints moved to org_config
> search: block (also closes the hardcoded-endpoint audit item);
> Fabric telemetry items NOT renamed — excluded via
> docs/deployment/BRAND_NEUTRAL_SNAPSHOT.md (item 6); CI grep test with
> EMPTY allowlist (item 5). grep -ri aivia over src/ + *.Notebook = 0.

**From:** learning/review session, 2026-08-17. **To:** dev session.
**Origin:** Sunny's revised work-separation rule: home→work code snapshots
are allowed, but NO file containing the name "AIVIA" may go to work. A
2026-08-17 sweep shows the name is currently baked into the core, so the
wheel itself violates the rule. Independent second motive: a brand-free
core is a prerequisite for white-label/OEM tiers later.

## Sweep findings (grep -rli aivia)

- **Behavior-affecting (worst):**
  - src/adapters/purview.py — glossary defaults to name="AIVIA";
    published descriptions get a "[AIVIA] ..." trailer stamped into the
    customer's catalog text.
  - src/llm_client.py — env var AIVIA_AZURE_API_VERSION.
  - src/webapp/* + 10_ingest_agent_events — AIVIA_* env vars / events URL.
  - aivia_admin_telemetry.SemanticModel / .Report — Fabric ITEM NAMES
    (renaming = workspace migration steps; plan deliberately).
- **UI strings:** orchestrator/cli.py banner ("AIVIA — ask about...").
- **Comments/docstrings/data:** integration_registry.py (to_tool:
  "AIVIA" values + prose), orchestrator docstrings, notebook 11 comment,
  CHANGELOG heading, tests referencing the above.
- **Branded-by-design (fine, excluded from work sync anyway):** website/,
  presentation/, marketplace_host/, internal/docs strategy files.

## Wanted

1. **One PRODUCT_NAME seam**: a single constant (config-overridable,
   default "AIVIA") in src/, used by purview glossary/trailer, cli
   banner, and anywhere else user-visible. Core code and comments refer
   to "the product"/"the engine", never the brand.
2. **Env var rename** with back-compat window: AIVIA_AZURE_API_VERSION →
   neutral name (e.g. SQA_AZURE_API_VERSION); read old name with a
   deprecation warning for one release.
3. **Registry data**: to_tool "AIVIA" → neutral token ("core"/"engine");
   generated INTEGRATION_MAP inherits automatically.
4. **Fabric item names** (aivia_admin_telemetry.*): decide rename vs
   leave (they never go to work — work sync can simply EXCLUDE them; if
   so, document the work-sync strip list instead of renaming).
5. **Mechanical enforcement** (the 5-rule gate): a CI test asserting
   grep -ri aivia over src/ + *.Notebook/ returns ONLY allowlisted hits
   (ideally zero). Same pattern as the silence contract: undeclared
   brand strings = build failure.
6. **Work-sync strip list** documented (docs/deployment or the
   INSTALLATION_GUIDE appendix): what a brand-free snapshot includes —
   src/ (post-sweep), libs/, numbered notebooks (post-sweep),
   org_config.example.yaml, environment/requirements.txt, agent
   instruction files — and what it never includes (website,
   presentation, marketplace_host, internal/docs, CHANGELOG, dist
   wheels until rebuilt post-sweep).
