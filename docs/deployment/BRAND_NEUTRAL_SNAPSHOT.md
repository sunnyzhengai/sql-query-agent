# Brand-neutral snapshot — what a neutral deployment includes

The core (src/ and the numbered notebooks) contains no product branding:
the display name comes from deployment config (`SQA_PRODUCT_NAME` env
var; neutral default "SQL Intelligence Agent"). This is enforced by
`tests/test_brand_neutral_core.py` — brand strings in the core fail CI.
Use this list for any deployment that must not carry the commercial
brand (white-label/OEM installs, neutral point-in-time snapshots).

## Include

- `src/` — the engine (or the built wheel from `dist/`, same content)
- `libs/` — the ScriptDom DLL (loaded from Files, NOT from the wheel)
- the numbered `*.Notebook/notebook-content.py` files (the pipeline)
- `org_config.example.yaml` — template; the real org_config.yaml is
  always authored inside the target environment, never copied
- `environment/requirements.txt` — public library pins
- `notebooks/` agent instruction files + data_loading/utility helpers
  as needed

## Never include

- `website/`, `presentation/`, `marketplace_host/` — branded by design
- `docs/` (strategy, ADRs, CHANGELOG carry the product name freely)
- `aivia_admin_telemetry.SemanticModel` / `.Report` — branded Fabric
  items (deliberately NOT renamed; they simply don't travel)
- `org_config.yaml`, `llm_api_key.txt`, `private/`, `learning/` —
  gitignored anyway; config and credentials never leave an environment
- `dist/` wheels built BEFORE the brand-neutral release (older wheels
  contain brand strings)

## Branding a deployment

Set `SQA_PRODUCT_NAME` (env) on the web app / host. Purview glossary
naming follows it automatically; UI titles and the agent system prompt
read it at startup. Legacy env names (pre-rename prefix) are still read
for one release with a deprecation warning — see src/branding.py.
