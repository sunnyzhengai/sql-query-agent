# Tenant Intake Sheet — fill every blank before deployment

One sheet, every value the deployment needs, whoever owns it.
A blank line = not ready to deploy. Fill with the real value,
or `N/A` with a reason. (The deploy-side preflight checks the
technical items live; THIS sheet is the human half — approvals,
ids, and paths that no script can discover.)

## 1. Fabric (owner: the tenant's Fabric admin)

| item | value |
|---|---|
| workspace id | ____ |
| lakehouse id | ____ |
| lakehouse name | ____ |
| environment item name | ____ |
| who can publish the environment | ____ |

## 2. The LLM seat (owner: the tenant / the runner)

| item | value |
|---|---|
| provider + model to use | ____ |
| key stored as (secret name + where) | ____ |
| WRITTEN approval for metadata-only LLM use (who, date) | ____ |
| outbound call to the provider confirmed from a notebook (date) | ____ |

THE METADATA BOUNDARY rides every approval: the engine sends
SQL source text and data-dictionary text only — never query
results, never patient data.

## 3. The inputs (owner: the BI/data team)

| item | value |
|---|---|
| SQL input folder (lakehouse path) | ____ |
| TMDL source (DevOps repo/branch or export path) | ____ |
| Clarity database name (the one edit point in the queries) | ____ |
| dictionary tables readable by whom (account) | ____ |
| who blesses term names (the data owner) | ____ |

## 4. Collibra (owner: the Collibra admin)

| item | value |
|---|---|
| instance base URL | ____ |
| service account / API token stored as (secret name) | ____ |
| Business Term DOMAIN id (the glossary it lands in) | ____ |
| Business Term ASSET TYPE id | ____ |
| description ATTRIBUTE TYPE id | ____ |
| technical-definition ATTRIBUTE TYPE id (exists? or create) | ____ |
| Power BI report ASSET TYPE id | ____ |
| SANDBOX/test domain id (the one-row rehearsal) | ____ |
| which attribute renders as the report description in the UI (eyeballed on one real report asset) | ____ |
| term -> report RELATION TYPE id (optional, phase two) | ____ |

## 5. Sign-offs (owner: named humans)

| item | value |
|---|---|
| capacity/run approval (runs happen by whose hand) | ____ |
| the wall acknowledged: tenant outputs stay on the tenant | ____ |
| sandbox-first acknowledged: one report + one term before any batch | ____ |
