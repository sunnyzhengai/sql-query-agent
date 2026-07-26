# Fabric Readiness Checklist

**Goal:** Deploy AIVIA to own Fabric tenant, record demo, take screenshots, set up reviewer sandbox, submit to Microsoft Commercial Marketplace.

**Updated:** 2026-07-25

---

## 1. Before Fabric (Do Now — No Fabric Needed)

### Partner Center (In Progress)
- [x] Register as ISV on Partner Center
- [x] Enroll in Commercial Marketplace program
- [ ] Business verification approved (resubmitted — waiting 3-5 days)
- [ ] Tax profile W-9 completed (form loading issue — follow up with apmdg@microsoft.com)
- [ ] Payout profile verified

### Legal (Done)
- [x] Privacy policy published at aiviaapp.com/privacy
- [x] Terms of service published at aiviaapp.com/terms
- [x] Email aliases set up (privacy@, support@, legal@)

### Marketing Assets (Done)
- [x] Logo — 4 sizes (48x48, 90x90, 216x216, 255x115)
- [x] Offer name: "AIVIA — SQL Intelligence Agent for Fabric"
- [x] Offer description drafted (MARKETPLACE_LISTING.md)
- [x] Pricing: $2,000/month, $21,600/year, 30-day free trial
- [x] Search keywords: business logic extraction, report metadata summary, data governance agent

### Code Packaging (To Do)
- [ ] Build `.whl` distribution: `python -m build --wheel`
- [ ] Replace `print()` with `logging` module in src/ (notebooks can keep print)
- [ ] Pin exact dependency versions in pyproject.toml
- [ ] Add `LICENSE` file (MIT or Apache 2.0)
- [ ] Update version to `1.0.0` in pyproject.toml
- [ ] Remove dead code (5 unreachable modules identified by detect_dead_code.py)
- [ ] Verify `twine check` passes on built wheel

### Documentation (To Do)
- [ ] Write `DEPLOYMENT_GUIDE.md` — step-by-step admin checklist for customer installation
- [ ] Write `REVIEWER_GUIDE.md` — step-by-step for Microsoft certification testers
- [ ] Update `README.md` with product overview, not dev notes
- [ ] Create `org_config.example.yaml` with all options documented and commented

---

## 2. Fabric Capacity (Blocker)

Get Fabric capacity through one of these:
- [ ] **Option A:** Founders Hub credits approved → provision F2
- [ ] **Option B:** Buy F2 capacity directly ($262/month) → use for demo → cancel after
- [ ] **Option C:** Fabric free trial activates

---

## 3. Deploy to Own Fabric Tenant

### Workspace Setup
- [ ] Provision Fabric F2 capacity in own Azure subscription
- [ ] Create workspace: "AIVIA-Demo"
- [ ] Create lakehouse in workspace
- [ ] Upload sql-query-agent code to Files/sql-query-agent/
- [ ] Upload ScriptDom DLL to Files/sql-query-agent/libs/

### Sample Data
- [ ] Create synthetic SQL files (5-10 diverse patterns, no real patient/org data)
  - Simple SELECT with WHERE filters
  - WITH...CTE pattern
  - Multi-statement with temp tables (#staging)
  - UNION ALL pattern
  - Complex JOINs with CASE expressions
- [ ] Create synthetic data dictionary (dict_tables, dict_columns)
- [ ] Create `org_config.yaml` for demo environment
- [ ] Upload sample SQL files to lakehouse

### Run Pipeline
- [ ] Run 02_parse.py with synthetic data → verify parse_results
- [ ] Run 03_build_graph.py → verify graph_nodes, graph_edges
- [ ] Run 04_build_metric_logic.py → verify metric_logic
- [ ] Run 05_validate.py → verify pipeline health (should be 100%)

### Configure Data Agent
- [ ] Create Fabric Data Agent in workspace
- [ ] Add data sources: metric_logic, graph_nodes, graph_edges, parse_errors
- [ ] Paste agent instructions from data_agent_instructions.md
- [ ] Test: ask about each synthetic metric — verify answers are correct
- [ ] Test: ask /errors — verify error report works
- [ ] Test: ask /coverage — verify coverage report works

---

## 4. Record Demo & Screenshots

### Demo Video (5 minutes)
- [ ] Use demo script from DEMO_SCRIPT.md (update for current product)
- [ ] Show: agent answering a business question
- [ ] Show: agent answering a technical/developer question
- [ ] Show: /coverage or /errors admin command
- [ ] Show: architecture diagram (3-layer graph)
- [ ] Crop browser — no URLs, no workspace names, no org-specific data
- [ ] Record in quiet room with good microphone

### Screenshots (3-5 for listing)
- [ ] Agent answering a business question (plain English response)
- [ ] Agent showing technical details (SQL fragments, source tables)
- [ ] Pipeline validation results (health dashboard)
- [ ] Knowledge graph structure (node/edge counts by layer)
- [ ] Architecture diagram

---

## 5. Marketplace Submission

### Create SaaS Offer in Partner Center
- [ ] Offer setup: name, description, keywords, categories
- [ ] Plan: $2,000/month, $21,600/year, 30-day free trial
- [ ] Upload logos (4 sizes)
- [ ] Upload screenshots (3-5)
- [ ] Upload demo video (optional but recommended)
- [ ] Set privacy policy URL: https://www.aiviaapp.com/privacy
- [ ] Set terms of use URL: https://www.aiviaapp.com/terms
- [ ] Set support URL: mailto:support@aiviaapp.com

### SaaS Technical Integration
- [ ] Decide: Transactable SaaS vs. Contact Me (list-only)
  - **Transactable** requires: landing page, fulfillment API, webhook handlers
  - **Contact Me** requires: nothing — leads come via email, you onboard manually
  - **Recommendation for v1: "Contact Me"** — ship faster, no infrastructure needed
- [ ] If Contact Me: set up lead destination (email or CRM)
- [ ] If Transactable: build landing page + fulfillment API (use SaaS Accelerator)

### Reviewer Sandbox
- [ ] Dedicated Fabric workspace with synthetic data pre-loaded
- [ ] Test account credentials for Microsoft reviewers
- [ ] Data Agent pre-configured and working
- [ ] Upload REVIEWER_GUIDE.md with step-by-step instructions

### Submit
- [ ] Review all listing fields
- [ ] Submit for certification
- [ ] Wait for review (2-4 weeks estimated)
- [ ] Respond to any certification feedback

---

## 6. Key Decision: Transactable vs. Contact Me

For your first listing, **"Contact Me"** is strongly recommended:

| | Contact Me | Transactable SaaS |
|---|---|---|
| Time to list | Days | Weeks-months |
| Infrastructure needed | None | Landing page, fulfillment API, webhooks |
| Customer onboarding | You handle manually | Automated via Marketplace |
| Billing | You invoice directly | Microsoft handles, takes 3% |
| MACC eligible | No | Yes |
| Co-Sell eligible | Yes (after listing) | Yes |

Start with Contact Me. Convert to Transactable after first 3 customers validate demand.

---

## Summary: Critical Path

```
Now:        Code packaging + deployment guide + reviewer guide
            ↓
Week 1:     Get Fabric capacity (buy F2 if needed)
            ↓
Week 1-2:   Deploy to own tenant + create synthetic data
            ↓
Week 2:     Record demo video + take screenshots
            ↓
Week 2-3:   Submit to Marketplace (Contact Me offer)
            ↓
Week 4-6:   Certification review
            ↓
Live:       Product listed on Microsoft Commercial Marketplace
```
