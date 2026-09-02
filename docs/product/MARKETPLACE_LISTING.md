# Marketplace Listing Draft

> **TABLED 2026-09-01 (Sunny).** Not in flight. Nothing here is
> committed copy, and no other document may cite this file as a source
> of truth. Revisit at listing time.
>
> The **offer itself** — tiers, packaging, sequencing, positioning — is
> governed by [PRODUCT_TIERS.md](PRODUCT_TIERS.md) (ADR 0063). That is
> the blueprint; this file is one downstream expression of it for one
> audience. If the two ever disagree, PRODUCT_TIERS.md wins and this
> draft is wrong.

**Rewritten 2026-09-01** against the ADR 0063 tier lock, replacing the
2026-07-25 draft (which sold the demoted Fabric Data Agent as the answer
surface, advertised "automated sync," and priced a single SKU). Kept as
a starting point for whenever the listing resumes.

**Parked calls appear as `<TBD — Sunny>`.** ADR 0063 §5 and §8 leave
X-Ray pricing/engagement length and final naming/pricing wording to
listing time. The SHAPE below is ruled; the numbers are not. Do not
invent them.

---

## Offer Name

AIVIA — Governance Intelligence for Microsoft Fabric

*(Alternate, if the listing favors the problem over the category:
"AIVIA — Make Your Data Catalog True." Final wording `<TBD — Sunny>`.)*

## Search Results Summary (99 chars)

Parse your SQL estate into governed truth. Every definition traced to
the code that computes it.

## Short Description (250 chars)

AIVIA parses your SQL and Power BI estate into a certified knowledge
graph, then writes governed descriptions and business terms into
Purview or Collibra — every write approved by your own steward. Runs
entirely in your tenant. Your data never leaves.

## Full Description

**The Problem**

Your catalog is full of definitions nobody trusts. The logic that
actually computes each metric lives in thousands of stored procedures
and Power BI models that only a few developers can read. So the same
metric gets three different definitions, nobody can tell which is
right, and the AI tools you bought to fix this hallucinate — because
they were trained on the documentation, not the code.

**The Solution**

AIVIA reads the code. It parses your SQL estate with Microsoft's own
ScriptDom parser, builds a knowledge graph of what each metric
genuinely computes, and finds the places where your definitions
contradict each other. Then it proposes governed descriptions and
business terms into the catalog you already own — with every proposal
approved by a named human before it lands.

**How It Works**

1. Deploy the engine into your Fabric workspace (a Python library —
   no external service).
2. AIVIA harvests and parses your SQL and Power BI estate.
3. It builds a certified knowledge graph: business metrics →
   calculation logic → source tables → the reports that consume them.
4. It sweeps for governance red flags — duplicate definitions,
   misnomers, and near-identical logic under different names — each
   with its members and code-level basis.
5. Approved descriptions, terms, and relationships flow into Purview
   or Collibra through the Write-Back Queue.

**Key Capabilities**

- **Native parsing, never text extraction** — Microsoft ScriptDom for
  T-SQL, the same grammar the database engine uses. No regex, no LLM
  guessing at your code.
- **Deterministic answers** — every factual claim comes from the graph,
  code-stamped with what was consulted. The model reads and writes
  language; it never computes an answer or invents a number.
- **Refusal over fabrication** — when there's no grounded answer, AIVIA
  says so and names what's missing.
- **Nothing lands unapproved** — machine-authored content enters your
  catalog only after a named developer or steward approves it, carrying
  its provenance grade.
- **Tenant-local by construction** — no data reaches AIVIA. The only AI
  dependency is your own Azure OpenAI endpoint, with PHI redacted by
  deterministic rules before any prompt is built.
- **Certification discloses, never gates** — governance state is shown
  in the answer; it never blocks access.

**Fabric-Native, BYOT**

AIVIA runs entirely within your Microsoft Fabric tenant — Delta tables,
Spark notebooks, your own Azure OpenAI. No external infrastructure,
no vendor-held keys, no data egress.

---

## The Offer — four tiers (ADR 0063)

**The cross-cutting promise: artifacts land, chat doesn't.** Every tier
produces a durable, graded artifact in a system of record. Conversation
is a query surface, not a filing cabinet.

### The Estate X-Ray — the diagnostic

A fixed-price, one-shot engagement in your tenant. We deploy, harvest,
parse, and sweep — then deliver **the X-Ray Report**: your real counts,
your red flags with members and code-level basis, and an AI-readiness
verdict explaining why your Copilot hallucinates. The engine is
removable afterward.

- Price: `<TBD — Sunny>` · Engagement length: `<TBD — Sunny>`
- No integration, no end users, one admin. The report's last page is
  the Bridge order form.

### Tier 1 — AIVIA Bridge (headless)

Admin-only, no end-user interface. Continuous harvest → parse → graph →
**Write-Back Queue** into the governance estate you already own:

- business and technical descriptions onto assets, and Power BI report
  descriptions;
- proposed business terms derived from parsed transformations;
- relationships: technical tables ↔ business terms ↔ reports;
- steward conflict alerts (drift, misnomers, grain fights);
- continuous monitoring — estate changes re-parse and re-propose.

Every proposed write is reviewed: technical items approved by a
developer, business items by a steward, then landed and logged with
approver and basis. v1 delivers approved sets as native import files
(Collibra Data Intake, Purview glossary CSV); direct API is stage 2.

*"You aren't buying a new tool; you're buying the engine that makes
your expensive catalog true."*

- Price: `<TBD — Sunny>` · Separately purchasable.

### Tier 2 — AIVIA Workbench: the Resolution Console

Sessions start from a machine-found flag with its computed evidence —
members, diffs, why-sentences, the graph panel — and every action is a
button: **compare · certify · delegate · deny with reason**; developers
additionally **approve technical writes** and **fork**. The console and
the Write-Back Queue are one surface: stewards see flags to resolve and
business writes to approve; developers see technical writes.

- Price: `<TBD — Sunny>` · Sold with Bridge as the launch bundle.

### Tier 3 — AIVIA Run (availability gated)

Executes the definition you confirmed, read-only, against your bound
source, and shows the rows. Nothing is generated: the SQL that runs is
byte-for-byte the statement you approved on screen. Result rows render
to your screen and never enter the language model's context.

- **Not generally available.** Gated on the output-side PHI gate and
  dedicated read-only principals. Do not list as available.

---

## Packaging

Separable SKUs, bundled launch. Bridge is purchasable alone — the
UI-averse enterprise exists. The launch offer and every demo lead with
**Bridge + Workbench together**: the write-back proves ROI, the console
proves the magic.

**Launch motion:** X-Ray → Bridge + Workbench bundle → Run when the
gates clear and pilots warrant.

| Plan | Price | Notes |
|---|---|---|
| Estate X-Ray | `<TBD — Sunny>` | One-shot engagement, fixed price |
| AIVIA Bridge | `<TBD — Sunny>` | Headless; purchasable alone |
| Bridge + Workbench | `<TBD — Sunny>` | The launch bundle |
| AIVIA Run | not listed | Gated (see Tier 3) |

*Recorded but not ruled: a $25k/yr anchor was noted in the ADR 0063
debate (architect's figure). Free-trial terms `<TBD — Sunny>`.*

## Positioning — the four moats (ADR 0063 §6)

1. Catalog-first incumbents carry architecture debt; a graph-native
   engine is the light one.
2. Generic LLM summarization hallucinates; deterministic parsers plus
   an honesty gate give code-level trust anchors.
3. Tenant-local: no data ever reaches AIVIA; PHI-safe by construction.
4. A closed loop — diagnose → interrogate → certify → write back —
   not descriptions in a parking lot.

## Search Keywords

1. data governance automation
2. business logic extraction
3. Purview glossary automation
4. SQL lineage
5. metric definition management

## Categories

- Primary: Data & Analytics > Data Governance
- Secondary: AI + Machine Learning > AI Services

## Visual Assets Needed

- [ ] Logo: 48x48, 90x90, 216x216, 255x115 (PNG, transparent)
- [ ] Screenshots: the X-Ray report's flag page; the Resolution Console
      with a flag and its evidence; the Write-Back Queue mid-approval
- [ ] Demo video: X-Ray verdict → console resolution → approved write
      landing in the catalog

## Claims discipline (read before publishing)

Every capability sentence above traces to a ratified decision. Four
claims from the previous draft were removed and must not return:

1. **"Users ask a Fabric Data Agent"** — demoted (ADR 0060 §3). It is
   an optional customer-configured surface over the same certified
   tables, never the product's answer path.
2. **"Automated sync to Collibra, Purview, Power BI"** — replaced by
   the Write-Back Queue and the OUTBOX model. Nothing machine-authored
   lands unapproved; we do not police their catalog between
   engagements.
3. **A single $2,000/month SKU** — superseded by the four-tier lock.
4. **"Enables self-service analytics"** — that is Tier 3, and it is
   GA-blocked on the output-side PHI gate.

Parse-rate and corpus figures: quote only the customer's own numbers
from their X-Ray. Internal corpus measurements are evidence for us, not
marketing claims about their estate.
