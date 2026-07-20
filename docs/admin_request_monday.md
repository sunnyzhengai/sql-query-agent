# Admin Access Requests

Prioritized list of access requests for the Data Empowerment Suite.
All testing in **dev/test environments only** — no production impact.

---

## Priority 1: Power BI Admin API — Lineage Access

**What it is:** An API that shows the dependency chain between Power BI reports and their underlying data sources — which report connects to which dataset, which dataset reads from which tables.

**What I need:**
- Access to the Power BI Admin API for reading workspace lineage
- `POST /v1.0/myorg/admin/workspaces/getInfo` (with lineage=true)

**Why I need it:** My tool needs to connect PBI reports to the stored procedures that power them. The lineage API provides this mapping automatically — no manual matching by name (which is unreliable), no guessing.

**What I'll do with it:** When my tool generates a business description for a stored procedure, it can automatically find the PBI report that uses that procedure and update the report's description field. Report → Dataset → Source Tables → Stored Procedure — the full chain traced automatically.

**Why it matters to the org:** Hundreds of PBI reports have empty or outdated description fields. Users open a report and don't know what it shows or where the data comes from. Auto-populating descriptions from the actual SQL logic means every report is self-documenting. New analysts can browse reports and understand what they're looking at without asking someone.

---

## Priority 2: Fabric Audit Logs API

**What it is:** An API that shows which users accessed what resources in Fabric — who ran which report, who used the Data Agent, when, and how often.

**What I need:**
- Access to the Fabric/Power BI Admin API for reading audit logs
- `GET /v1.0/myorg/admin/activityevents`
- Or equivalent Fabric audit log access

**Why I need it:** My tool tracks which metrics users ask about most frequently. This "usage weight" drives governance priorities — if everyone asks about ER Length of Stay, that metric should be governed first, documented best, and maybe promoted to a dashboard.

**What I'll do with it:** Read the audit logs to see which metrics get queried most, who asks about them, and which departments have overlapping data needs. This data feeds back into the knowledge graph — high-demand metrics get prioritized, low-demand metrics get flagged for review.

**Why it matters to the org:** Instead of guessing which reports and metrics matter most, we have actual usage data. Leadership can see: "These are the top 20 metrics our organization cares about, ranked by actual usage." This informs where to invest in data quality, governance, and dashboards.

---

## Priority 3: Microsoft Purview — Data Curator Role

**What it is:** A permission role in Microsoft Purview that allows creating and editing metadata assets (business terms, descriptions, classifications) via the Data Map REST API.

**What I need:**
- The **Data Curator** role on the root collection in our Purview account

**Why I need it:** Our org already has Purview — it came with the Fabric bundle. But it's empty. Nobody's populated it because manual entry is tedious. The Data Curator role lets my tool write metadata programmatically.

**What I'll do with it:** Push AI-generated business descriptions into Purview's Data Catalog. Every table and metric gets a plain-English description. When someone searches Purview for "census" or "readmission," they find the relevant metrics with clear descriptions of what they measure and how they're calculated.

**Why it matters to the org:** Purview is already paid for but unused. Populating it makes it immediately useful. It also prepares the org for compliance — auditors ask "do you have a data catalog?" and the answer becomes yes, with hundreds of documented metrics.

---

## Priority 4: Collibra — Service Account with API Access

**What it is:** A non-SSO username/password account that can call Collibra's REST API programmatically.

**What I need:**
- A service account for the **Collibra dev** instance
- Basic auth (username/password, not SSO)
- **Author** role on the Clinical Glossary domain
- REST API access (`/rest/2.0/`)

**Why I need it:** Our Collibra instance uses SSO (single sign-on), which means personal logins can't authenticate via API — they only work through the browser. A service account uses basic auth (username/password) which works for programmatic API calls.

**What I'll do with it:** Automatically push business term descriptions into the Clinical Glossary. Right now, someone manually types each term into Collibra one at a time. My tool generates descriptions from the SQL logic and bulk-loads them — hundreds of terms at once instead of one by one.

**Why it matters to the org:** Collibra customers have been asking for this bulk loading capability. Collibra itself said they won't build it. This fills that gap. The Clinical Glossary stays current because it's populated automatically whenever the SQL changes.

---

## The Big Picture

All four requests serve one goal: **automatically document the organization's data assets so people can find, understand, and trust the data.** Right now, business logic is buried in 790+ SQL stored procedures that nobody reads. This tool extracts that logic, translates it to plain English, and pushes it to the places people actually look — Power BI report descriptions, Purview catalog, and Collibra glossary.

---

## Draft Email

**Subject:** Access requests for data governance POC — 4 items (prioritized)

Hi [Admin Name],

I'm building a proof-of-concept for automated data governance using Microsoft Fabric. I need access to a few services to test the integration. All testing will be done in dev/test environments only — no changes to production.

In priority order:

1. **Power BI Admin API** — lineage access (`/admin/workspaces/getInfo` with lineage=true). To auto-discover which reports connect to which data sources.

2. **Fabric Audit Logs** — activity events API (`/admin/activityevents`). To track which metrics users query most frequently.

3. **Purview Data Curator role** — on the root collection. To push business metric descriptions to the Data Catalog.

4. **Collibra service account** — for dev instance, basic auth, Author role on Clinical Glossary domain. To bulk-load business term descriptions via REST API.

Happy to discuss or demo what we've built so far. Thanks!

Sunny
