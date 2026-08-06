# Ownership Attribution — Entra ID Feasibility & Design

**Date:** 2026-08-06 · **Decision:** [ADR 0027](../decisions/0027-ownership-attribution-layered-sources.md)
**Requirement:** customers must quickly see which DEVELOPER owns the SQL and
which BUSINESS STEWARD owns the report logic, on every agent answer.
Preferred: Entra ID integration. Minimum bar: manual name entry.

## Feasibility findings (verified against live Microsoft docs, 2026-08-06)

### 1. Calling Microsoft Graph from a Fabric notebook — PARTIAL

- `notebookutils.credentials.getToken(audience)` supports exactly four
  audiences: `storage`, `pbi`, `keyvault`, `kusto`. **No Microsoft Graph
  audience**, no arbitrary resource URIs. The notebook user's own token
  cannot reach Graph — no on-behalf-of broker is exposed to notebook code.
- Graph lookups (users, groups) therefore require **our own app
  registration**: MSAL confidential-client flow, secret/cert in Key Vault
  (via `getSecret`), with application permissions `User.Read.All` (+
  `GroupMember.Read.All` for group expansion) — **both need tenant-admin
  consent**. This is a hard customer prerequisite to document.
- Sources: learn.microsoft.com/fabric/data-engineering/notebookutils/notebookutils-credentials;
  learn.microsoft.com/graph/permissions-reference

### 2. Does the Data Agent know who is asking? — PARTIAL

- Identity passthrough is documented for authorization: the agent runs
  NL2SQL **as the asking user** (least-privilege, RLS applies). So SQL
  constructs (`USER_NAME()`, `SUSER_SNAME()`, RLS predicates) resolve to
  the asker at query time.
- But there is **no documented contract exposing the asker's UPN/object id
  to agent instructions or grounding tables** — the identity exists only
  implicitly at the SQL layer. Known holes: RLS must be defined at
  warehouse/table level (semantic-model-only RLS didn't protect the
  warehouse path); identity can fail to propagate via Azure AI Foundry;
  SPN-invoked agents (preview) have **no user context at all**.
- Sources: learn.microsoft.com/fabric/data-science/concept-data-agent;
  learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric

### 3. Mapping developers to SQL objects — PARTIAL

- **SQL metadata is a dead end**: `sys.objects.principal_id` is NULL for
  schema-owned objects (the default) — SQL Server never records the
  creating user reliably. `create_date` has no identity attached.
- **Git authorship works, via the provider not Fabric**: Fabric's Git APIs
  expose no commit history; Azure DevOps `Commits – Get Commits` with
  `searchCriteria.itemPath` (and GitHub's `commits?path=`) returns
  author/email/date per item folder. Caveat: Fabric UI "commit all" makes
  the *syncing* identity the author — authorship ≈ who synced.
- **Forward capture**: Fabric warehouse `queryinsights.exec_requests_history`
  exposes `login_name` + full DDL text (~30-day rolling window,
  unverified exact retention) — attributes `CREATE PROCEDURE` to the
  submitting user going forward, no backfill.
- Sources: learn.microsoft.com/rest/api/azure/devops/git/commits/get-commits;
  learn.microsoft.com/sql/relational-databases/system-catalog-views/sys-objects-transact-sql;
  learn.microsoft.com/fabric/data-warehouse/query-insights

### 4. Fabric people-attribution APIs — SUPPORTED

- **Workspace role assignments** (`GET /v1/workspaces/{id}/roleAssignments`)
  — callable with the notebook's `pbi` token at Member+ role. GA.
- **Admin Items – List Items** returns `creatorPrincipal` (object id,
  displayName, **UPN**) per item, tenant-wide — the direct "who owns this
  item" answer. **Preview API**, Fabric-admin/SPN only, 200 req/hr.
- **Scanner APIs** (metadata scanning): item name, owner, endorsement,
  sensitivity — GA, no special license, the canonical ISV bulk pattern.
- **Microsoft Graph is now a supported Data Agent data source** (2026
  docs) — org-people lookups can be answered by the agent itself under the
  asker's identity.

## Design consequences (see ADR 0027 for the decision)

1. **Two-identity architecture is unavoidable.** Enrichment (Graph, admin
   APIs, DevOps commits) runs as an admin-consented SPN at pipeline time;
   ask-time identity arrives only implicitly via SQL passthrough. Neither
   can do the other's job.
2. **Manual entry is the floor and the tie-breaker.** Every automated
   signal has holes (preview APIs, sync-authorship, no backfill), so the
   product contract is: attribution always *works* manually, and Entra
   signals *prefill and enrich* rather than being required.
3. **Four joinable automated signals**, all keyed on Entra object id:
   admin-items `creatorPrincipal`, scanner-API owner, workspace roles,
   DevOps `itemPath` commit authorship. Store the winning value plus its
   `source` so provenance is disclosed, not implied.
