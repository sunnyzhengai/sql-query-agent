# Admin Request — Monday Email

Draft email to your IT admin requesting access for the Data Empowerment Suite POC.

---

**Subject:** Access requests for data governance POC — 4 items

Hi [Admin Name],

I'm building a proof-of-concept for automated data governance using Microsoft Fabric. I need access to a few services to test the integration. All testing will be done in **dev/test environments only** — no changes to production.

### 1. Collibra — Service Account with API Access

I need a service account for the **Collibra dev** instance with:
- Basic auth (username/password, not SSO)
- **Author** role on the Clinical Glossary domain
- REST API access (`/rest/2.0/`)

**Purpose:** Automatically populate business term descriptions in the Clinical Glossary from our existing SQL stored procedures.

### 2. Microsoft Purview — Data Curator Role

I need the **Data Curator** role on the root collection in our Purview account.

**Purpose:** Push AI-generated metadata (business metric descriptions) to Purview's Data Catalog via the Data Map REST API.

### 3. Fabric Audit Logs — API Access

I need access to the **Fabric/Power BI Admin API** for reading audit logs:
- `GET /v1.0/myorg/admin/activityevents`
- Or equivalent Fabric audit log access

**Purpose:** Track which metrics users ask about most frequently, so we can prioritize governance efforts and identify gaps.

### 4. Power BI Admin API — Lineage Access

I need access to the **Power BI Admin API** for reading workspace lineage:
- `POST /v1.0/myorg/admin/workspaces/getInfo` (with lineage=true)

**Purpose:** Automatically discover which Power BI reports connect to which data sources, so we can populate report descriptions without manual mapping.

---

All four are **read/write to dev only** — no production impact. Happy to discuss or demo what we've built so far. Thanks!

Sunny
