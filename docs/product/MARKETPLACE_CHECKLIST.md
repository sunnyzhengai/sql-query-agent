# Microsoft Marketplace Readiness Checklist

Everything needed to pass Microsoft's evaluation and maintain the product post-launch.
Use this during development to avoid retrofitting requirements later.

---

## 1. Business Setup (Do First)

### Partner Registration
- [ ] Join the **Microsoft AI Cloud Partner Program**
- [ ] Create a **publisher account** in Partner Center
- [ ] Complete **identity verification** (business entity background check, 3-5 business days)
- [ ] Explore **Microsoft for Startups Founders Hub** (free, self-paced, AI credits, mentorship)
- [ ] Explore **ISV Success Program** (free 12 months, then ~$1,550/yr; Azure credits, 1:1 technical consultations)

### Legal Entity
- [ ] Establish business entity (LLC or similar) — separate from personal identity
- [ ] Business bank account linked for Marketplace disbursements
- [ ] Business email domain (not personal Gmail)

### Conflict of Interest Protection
- [ ] Review employment contract for "assignment of inventions" clauses
- [ ] Ensure complete separation of resources (no company laptop, software, cloud accounts, email)
- [ ] Development strictly outside working hours
- [ ] Code on personal hardware, personal cloud instances
- [ ] Consider formal HR disclosure for written release/waiver
- [ ] Product documentation explicitly states "general SQL schema analysis" — not clinical/hospital-specific

---

## 2. Code Quality Requirements

Microsoft evaluates code indirectly through functional testing and security review.
Build these in from the start — retrofitting is painful.

### Packaging
- [ ] Valid `pyproject.toml` with metadata (author, license, version, description)
- [ ] **SemVer versioning** (e.g., 1.0.0) — signal breaking changes properly
- [ ] Package builds cleanly as `.whl` and `.tar.gz`
- [ ] Run `twine check` to validate distribution artifacts
- [ ] Clear `LICENSE` file (MIT, Apache 2.0, or similar)

### Dependency Management
- [ ] **Pin exact dependency versions** in requirements (e.g., `pandas==2.2.0`)
- [ ] Regularly scan dependencies with `pip-audit` or `safety` for known vulnerabilities
- [ ] Minimal dependency footprint — don't pull in packages you don't need

### Code Standards
- [ ] Type hints throughout (`mypy` clean)
- [ ] Linting with `ruff` (already configured — `E, F, I, N, W`)
- [ ] PEP 8 compliant (line length 120 already set)
- [ ] **No hardcoded secrets** — all credentials via environment variables or Azure Key Vault
- [ ] Input validation/sanitization on all SQL parsing (injection prevention)
- [ ] Principle of least privilege — only request permissions the tool actually needs

### Logging
- [ ] Use Python `logging` module throughout the library (not print statements)
- [ ] Structured log levels: INFO for pipeline progress, WARNING for recoverable issues, ERROR for failures
- [ ] Critical for customers debugging in their own tenants — print statements vanish in production

### Distribution
- [ ] Build `.whl` file with `python -m build --wheel`
- [ ] Distribute via **Fabric Environment** (upload .whl to custom libraries)
- [ ] Do NOT rely on `%pip install` in notebook cells for production
- [ ] Document upgrade path: new .whl version -> update Fabric Environment -> republish

### Testing
- [ ] Automated test suite (`pytest`) with meaningful coverage
- [ ] Unit tests for parser, builder, traversal (existing)
- [ ] Integration tests for full pipeline (existing)
- [ ] Adapter tests with fake/mock adapters (existing — 9 tests)
- [ ] Golden file tests for critical query outputs
- [ ] Acceptance tests (question -> expected traversal path)
- [ ] **CI/CD pipeline** (GitHub Actions) runs tests on every push

### Documentation (In-Repo)
- [ ] `README.md` with installation instructions, quick-start, configuration
- [ ] `ARCHITECTURE.md` (exists)
- [ ] `USER_FLOW.md` (exists)
- [ ] `SETUP.md` (exists)
- [ ] `TESTING.md` (exists)
- [ ] `FABRIC_SETUP.md` (exists)
- [ ] Inline docstrings on all public functions/classes

---

## 3. Security & Compliance Documents

Microsoft's certification team will review these. Prepare them before submission.

### Security Whitepaper (1-2 pages)
- [ ] **Data handling:** How the tool accesses, processes, and stores data
- [ ] **Identity management:** How authentication works (Microsoft Entra ID / SSO)
- [ ] **Encryption:** Data at rest and in transit
- [ ] **RBAC:** How the tool respects existing data permissions
- [ ] **Data sovereignty:** Guarantee that customer data never leaves their tenant (BYOT model)
- [ ] **No model training:** Customer data is never used to train external AI models

### Data Flow Diagrams
- [ ] Visual showing how the Python tool interacts with SQL sources, graph storage, and catalog APIs
- [ ] Show data boundaries — what stays in customer tenant vs. what (if anything) leaves
- [ ] Mark authentication/authorization points in the flow

### Privacy Policy
- [ ] Published on your business website
- [ ] Covers what data the tool accesses and how it's handled
- [ ] GDPR and HIPAA considerations (even if BYOT, state it clearly)

### Terms of Use / EULA
- [ ] Published on your business website
- [ ] Covers licensing, liability, data handling responsibilities
- [ ] Clear delineation: customer is responsible for their data, you provide the tool

---

## 4. Marketplace Listing Assets

Microsoft reviews the "commercial readiness" of your listing. Professional presentation matters.

### Required
- [ ] **Offer name** and **summary** (clear value prop in 3 paragraphs)
- [ ] **Detailed description** — what the tool does, who it's for, key benefits
- [ ] **Pricing plans** — Basic (Bulk Loader) and Pro (+ Agent + Purview) tiers
- [ ] **Categories and search keywords** — data governance, AI agent, Microsoft Fabric
- [ ] **Support contact** and support URL
- [ ] **Privacy policy URL**
- [ ] **Terms of use URL**

### Visual Assets
- [ ] **Logo** — high-quality, professional (required sizes: 48x48, 90x90, 216x216, 255x115)
- [ ] **Screenshots** — at least 3-5 showing the tool in action
- [ ] **Demo video** (optional but highly recommended) — 5-minute walkthrough

### Marketing Copy
- [ ] Frame around **risk reduction** and **productivity** — not "SQL-to-graph conversion"
- [ ] Target audience: Data Governance Officers, BI Leaders, Data Architects
- [ ] Highlight: BYOT (data never leaves tenant), Fabric-native, reduces governance overhead

---

## 5. Technical Integration for Marketplace

### SaaS Offer Setup
- [ ] Define offer type: **Transactable SaaS Offer** in Partner Center
- [ ] Integrate with **Marketplace Fulfillment API** (subscription lifecycle)
- [ ] Build a **landing page** — customer redirected here after "Get It Now"
- [ ] Handle subscription activation, plan changes, cancellation
- [ ] Consider using the [SaaS Accelerator](https://github.com/Azure/Commercial-Marketplace-SaaS-Accelerator) to speed this up

### Authentication
- [ ] Support **Microsoft Entra ID** (SSO) for customer authentication
- [ ] Service principal support for automated/headless runs in Fabric Notebooks

### Plan Configuration
- [ ] **Basic plan:** Bulk Loader (Collibra + Purview metadata push + PBI description updates)
- [ ] **Pro plan:** Basic + Chat Data Agent + full Purview integration + usage analytics
- [ ] All plans must share the same pricing model (flat-rate recommended)
- [ ] Optional: annual billing discount (10-15% off)

### MACC Eligibility
- [ ] Ensure offer is "transactable" so customers can use Azure Consumption Commitments
- [ ] This is a major selling point — enterprise customers have pre-committed Azure budgets

---

## 6. Reviewer's Experience

Microsoft testers will try to install and use your tool. Make their job easy.

### Test Environment
- [ ] **Reviewer's sandbox** — a dedicated demo Fabric environment with sample data
- [ ] **Test account credentials** — reviewer can log in and see the tool working
- [ ] Pre-loaded sample data (ER_LOS metric, FCOTS, etc.) so reviewers see results immediately

### Tester's Guide (PDF or MD)
- [ ] Step-by-step walkthrough for the reviewer
- [ ] Expected behavior at each step
- [ ] How to verify the tool is working correctly
- [ ] Known limitations and what's out of scope

### Instructions for Reviewers (in Partner Center)
- [ ] Clear, concise setup instructions
- [ ] List of required permissions (Data Curator for Purview, Report.ReadWrite.All for PBI, etc.)
- [ ] Estimated review time

---

## 7. Post-Launch Maintenance

### Ongoing Requirements
- [ ] Monitor sales/subscriptions in **Partner Center**
- [ ] Monthly **disbursement reconciliation** (Microsoft pays out monthly, minus 3% fee)
- [ ] Keep security whitepaper and documentation updated with each release
- [ ] Any significant update (pricing, plans, URLs) requires **re-review by Microsoft**
- [ ] Activate **Marketplace Rewards** benefits for marketing support

### Growth Milestones
- [ ] Track revenue to unlock higher-tier Marketplace Rewards
- [ ] Work toward **Azure IP co-sell status** — unlocks Microsoft sales force collaboration
- [ ] Collect customer testimonials / case studies for listing updates

### Support Model (One-Person Sustainable)
- [ ] **Docs-first:** High-quality implementation guide (MkDocs or GitHub Pages)
- [ ] **AI-powered support bot:** Build an AI support agent using our own knowledge graph approach — eat your own dogfood. Target: handle 80%+ of common user questions automatically. Same flywheel pattern: known questions get instant answers, unknown questions escalate to you.
- [ ] **Consultation upsell:** Premium 2-hour onboarding calls for enterprise customers
- [ ] Avoid becoming a 24/7 support desk — BYOT model means customer's IT handles runtime issues

---

## 8. Development Guardrails

Build these into the codebase from the start so they're not afterthoughts.

### Config-Driven Everything
- [x] `org_config.yaml` for all org-specific settings (gitignored)
- [x] `org_config.example.yaml` committed as template
- [x] Adapters section: customer enables purview, collibra, or both
- [ ] No hardcoded paths, URLs, credentials, or org-specific details anywhere

### Portability
- [x] Works locally from JSON seed data
- [x] Works in Fabric from Spark DataFrames (`.collect()` -> list-of-dicts)
- [ ] No Fabric-specific imports in core library (Fabric deps only in notebooks/orchestrator)
- [ ] Clean separation: library does logic, notebook does orchestration

### Auditability
- [ ] Every agent answer traceable to: canonical node, transformation steps, source tables, certifier
- [ ] Audit trail for certification decisions (who approved, when, what changed)
- [ ] Usage weight tracking with timestamps

### HITL (Human-in-the-Loop)
- [x] Two-stage certification model (Developer -> Steward)
- [ ] Agent suggests, never auto-executes complex actions
- [ ] Steward notification workflow for unknown questions (Path B)

---

## Priority Order

For a solo founder with a full-time job, tackle in this order:

1. **Business setup** — register as partner, set up entity (can do in evenings)
2. **Code quality** — CI/CD, pinned deps, security scanning (integrate once, runs forever)
3. **Wedge feature** — get Bulk Loader working end-to-end with at least one adapter
4. **Security docs** — whitepaper + data flow diagram (1-2 pages each)
5. **Marketplace listing** — copy, screenshots, pricing
6. **Test environment** — sandbox for Microsoft reviewers
7. **Submit for certification**
8. **Post-launch** — rewards, co-sell, iterate based on customer feedback
