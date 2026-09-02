# AIVIA Data Empowerment Suite — Security Whitepaper

**Version:** 1.0
**Date:** July 2026
**Company:** AIVIA LLC
**Contact:** founder@aiviaapp.com
**Website:** www.aiviaapp.com

---

## Executive Summary

AIVIA Data Empowerment Suite is a Fabric-native data governance platform that extracts business logic from SQL stored procedures, builds a certified knowledge graph, and answers questions about how metrics are defined. This document describes AIVIA's security architecture, data handling practices, and compliance posture.

**Key security principle:** AIVIA operates on a **Bring Your Own Tenant (BYOT)** model. All customer data remains within the customer's own Microsoft Fabric environment. AIVIA does not host, store, transmit, or access customer data outside of the customer's tenant.

**The data boundary (ADR 0061, added 2026-09-01).** Where AIVIA
executes logic against customer data at all — the gated Run tier — the
boundary is architectural, not procedural:

- **Result rows never enter the language model's context.** Rows render
  to the user's screen; the model receives machine-composed stamps only
  (row count, column schema, elapsed time, as-of timestamp, source).
  The AI governs the question; the database answers it; the model never
  touches a patient record. This is cage-tested, not policy.
- **Nothing is generated.** The SQL that executes is byte-for-byte the
  parsed, displayed statement the user confirmed on screen — this is
  not NL2SQL.
- **Read-only by construction:** a dedicated read-only credential AND a
  Microsoft ScriptDom statement-type check that admits a single SELECT.
  DML/DDL/EXEC are refused by the parser, never by pattern matching.
- **Bounded:** statement timeout, TOP-N row cap, and result-size cap,
  with the cap disclosed in the result label rather than silently
  truncating.
- **Gate, not a promise:** execution against real customer estates is
  GA-blocked pending the output-side PHI gate and dedicated read-only
  principals. Current capability runs on synthetic data only.

**Scope note:** the Microsoft Fabric Data Agent appears in this
document as an optional customer-configured surface over the same
certified tables. It is not AIVIA's answer path (ADR 0060).

---

## 1. Architecture Overview

### Deployment Model: Bring Your Own Tenant (BYOT)

AIVIA is deployed as a Python library (`.whl` package) installed into the customer's own Microsoft Fabric environment. The product runs entirely within the customer's tenant:

```
Customer's Microsoft Fabric Tenant
├── Fabric Lakehouse (customer-owned)
│   ├── Input: SQL sources, data dictionary
│   ├── Output: graph_nodes, graph_edges (Delta tables)
│   └── Config: org_config.yaml
├── Fabric Notebooks (run AIVIA library)
├── Fabric Data Agent (customer-configured)
└── Microsoft Purview (customer-owned, optional)
```

**No AIVIA-hosted infrastructure exists.** There are no AIVIA servers, databases, APIs, or cloud services that customer data touches. The product is a library that runs in the customer's environment, not a hosted service.

### What AIVIA Provides
- Python library package (`.whl` file)
- Fabric notebook templates
- Data Agent instruction templates
- Documentation and configuration guides

### What the Customer Provides
- Microsoft Fabric workspace with capacity
- SQL stored procedures (the data to be parsed)
- Data dictionary tables
- Microsoft Purview / Collibra access (optional)
- User accounts and permissions

---

## 2. Data Handling

### Data at Rest

All data is stored in **Microsoft Fabric Delta tables** within the customer's lakehouse. AIVIA creates and writes to the following tables:

| Table | Contents | Sensitivity |
|---|---|---|
| `graph_nodes` | Business metric names, descriptions, SQL fragments | Business logic (may contain hardcoded names from SQL — see HIPAA section) |
| `graph_edges` | Relationships between metrics, logic steps, and tables | Structural metadata only |
| `build_summary` | Parse statistics, error counts, timestamps | Operational metadata |
| `parse_errors` | Names of SQL sources that failed to parse | File names only |
| `parse_successes` | Names of SQL sources that parsed successfully | File names only |
| `steward_assignments` | Steward names mapped to metrics | Business contact info |

**No patient data, PHI, PII, or clinical records are stored in AIVIA tables.** The product processes SQL *logic* (the structure of queries), not the *data* those queries return. SQL fragments stored in the graph contain column names and filter conditions, not actual data values.

### Data in Transit

All communication within the customer's Fabric environment uses Microsoft's built-in encryption:
- **HTTPS/TLS 1.2+** for all API calls (Purview, PBI, Collibra)
- **Fabric internal encryption** for data movement within the tenant
- No data is transmitted to AIVIA servers (none exist)

### Data Processing

AIVIA processes SQL files through the following pipeline:
1. **Read:** SQL text is read from the customer's `sql_sources` Delta table
2. **Parse:** SQL is parsed using Microsoft's ScriptDom parser (loaded locally via pythonnet — no external calls) and Python libraries running in the customer's Fabric notebook
3. **Build:** A knowledge graph is constructed in memory from the parsed structure
4. **Write:** The graph is written to Delta tables in the customer's lakehouse
5. **Optional:** Metadata is pushed to customer's Purview or Collibra via their own APIs

**All processing occurs within the customer's Fabric compute resources.** No data is sent to external services during the parse-and-build pipeline. No LLM or AI service is called during parsing — the pipeline is entirely deterministic.

---

## 3. Authentication & Identity

### User Authentication

AIVIA does not implement its own authentication system. It relies entirely on **Microsoft Entra ID (Azure Active Directory)**, which is already configured in the customer's tenant:

- Users authenticate to Fabric using their existing organizational credentials
- No separate AIVIA login, API keys, or user accounts
- Multi-factor authentication (MFA) is supported if configured by the customer's IT

### Service Principals

For automated pipelines (scheduled graph rebuilds, catalog sync), AIVIA uses **Microsoft Entra ID Service Principals**:
- Created and managed by the customer's IT team
- Granted only the minimum permissions needed (principle of least privilege)
- No shared or hardcoded credentials in the AIVIA library

### Permissions Required

| Permission | Purpose | Scope |
|---|---|---|
| Fabric Workspace Contributor | Run notebooks, read/write Delta tables | Customer's workspace |
| Purview Data Curator (optional) | Push metadata to Purview catalog | Customer's Purview |
| PBI Report.ReadWrite.All (optional) | Update Power BI report descriptions | Customer's PBI workspace |

---

## 4. Access Control

### Role-Based Access Control (RBAC)

AIVIA respects the customer's existing Fabric workspace permissions:
- **Workspace Admins** can configure AIVIA, run the orchestrator, manage steward assignments
- **Workspace Contributors** can run notebooks and view graph data
- **Workspace Viewers** can query the Data Agent but cannot modify the graph

### Data Agent Access

The Fabric Data Agent inherits the permissions of the user who queries it:
- Users only see data they are authorized to access in the underlying tables
- Row-level security (RLS) can be configured on the Delta tables by the customer
- The Data Agent does not bypass any Fabric security controls

### Human-in-the-Loop (HITL) Certification

AIVIA implements a two-stage certification workflow for metric definitions:
1. **Developer Review:** Technical accuracy of parsed SQL logic
2. **Steward Review:** Business correctness of metric definitions

Only steward-certified definitions are marked as "certified" in the graph. The Data Agent can be configured to only answer questions from certified paths, refusing to guess on uncertified metrics.

---

## 5. Configuration Security

### org_config.yaml

AIVIA's configuration file contains:
- Lakehouse table paths (not sensitive)
- Data dictionary column mappings (not sensitive)
- Catalog adapter settings (Purview account name, Collibra URL)
- **No passwords, API keys, or secrets** are stored in the config file

### Secrets Management

- Catalog credentials (Collibra password, API keys) should be stored in **Azure Key Vault**
- AIVIA's adapters support Key Vault integration for production deployments
- During development, credentials may be passed via notebook cells (not persisted)

### Source Code

- AIVIA is distributed as a compiled Python wheel (`.whl`), not source code
- The customer does not need access to AIVIA's source code to use the product
- Notebook templates are provided as reference implementations

---

## 6. Compliance Considerations

### HIPAA

AIVIA processes SQL query **definitions** (the structure of queries), not query **results** (the data those queries return). The knowledge graph stores metadata about how reports are calculated, not clinical or patient data.

**PHI in SQL Definitions:**
While SQL definitions are primarily structural, they may contain embedded PHI in certain cases:
- Hardcoded provider names in WHERE clauses (e.g., `WHERE provider = 'Dr. Smith'`)
- Department or clinic names that identify specific facilities
- Procedure/report names that contain provider names (e.g., `USP_DrSmith_Clinic_Report`)
- Hardcoded patient IDs or MRNs used as test values in SQL comments

**AIVIA's PHI Protection Mechanisms:**

| Layer | Protection | Implementation |
|---|---|---|
| **Data Agent (runtime)** | PHI redaction in responses | Agent instructions include a mandatory PHI protection rule: never output personal names, MRNs, patient IDs, addresses, or facility names. Provider names in SQL fragments are replaced with generic labels like "[Provider]" in the agent's response. |
| **Knowledge graph (storage)** | SQL fragments only, no data values | The graph stores SQL logic (column names, filter conditions, JOINs) — not the data those queries return. No patient records enter the graph. |
| **BYOT (architecture)** | Customer-controlled environment | All data stays in the customer's Fabric tenant. AIVIA has no access to the data. The customer's existing HIPAA controls (encryption, access control, audit logging) remain fully in effect. |
| **Synthetic demo data** | No real data in demos | AIVIA's demo environment uses synthetic SQL files with anonymized names. No real patient, provider, or organizational data is used in marketing, demos, or reviewer sandboxes. |

**Customer Responsibility:**
Customers should review their SQL source files for embedded PHI before loading them into the system. While AIVIA's agent redacts PHI from responses, the underlying SQL fragments stored in Delta tables may still contain hardcoded values from the original SQL. Customers should apply their standard data classification policies to the `graph_nodes` table's `properties` column, which contains SQL fragments.

**No BAA Required:**
Because AIVIA operates entirely within the customer's tenant and does not access, transmit, or store PHI on the customer's behalf, a Business Associate Agreement (BAA) between AIVIA and the customer is not required. The customer's existing BAA with Microsoft (covering Fabric, Azure, and related services) provides the necessary compliance coverage.

### GDPR

- AIVIA does not collect personal data from end users
- No data is transferred outside the customer's tenant or geographic region
- The BYOT model ensures data sovereignty is maintained by the customer
- Customers retain full control over data deletion (delete the Delta tables)

### SOC 2

AIVIA's BYOT model delegates infrastructure security to Microsoft's Fabric platform, which maintains SOC 2 Type II certification. AIVIA's security controls focus on:
- Secure coding practices (dependency scanning, linting, CI/CD)
- No hardcoded secrets in codebase
- Principle of least privilege in permission requirements
- Audit logging of graph build operations

---

## 7. Incident Response

Since AIVIA does not host customer data or operate infrastructure, security incidents fall into two categories:

### AIVIA Library Vulnerability
- AIVIA monitors dependencies for known vulnerabilities (`pip-audit` in CI/CD)
- Security patches are distributed as updated `.whl` packages
- Customers update at their own pace (BYOT model)

### Customer Environment Incident
- Handled by the customer's IT/security team
- AIVIA does not have access to the customer's environment
- AIVIA can provide technical guidance on which tables/data to review

---

## 8. Summary

| Security Property | AIVIA's Approach |
|---|---|
| **Data residency** | Customer's tenant only (BYOT) |
| **Data access** | No AIVIA access to customer data |
| **Authentication** | Microsoft Entra ID (customer's existing identity) |
| **Encryption** | Fabric-native TLS 1.2+ and at-rest encryption |
| **Secrets** | Azure Key Vault (no hardcoded credentials) |
| **Compliance** | HIPAA-aware design, GDPR-compatible, SOC 2 delegated to Fabric |
| **Access control** | Inherits customer's Fabric RBAC |
| **Audit** | Build logs in Delta tables, Fabric audit logs |
| **Updates** | Customer-managed via `.whl` package updates |
| **Incident response** | Customer-managed infrastructure, AIVIA provides library patches |

---

*For questions about AIVIA's security practices, contact founder@aiviaapp.com.*
