# Product Tiers — the offer structure

<!-- TIER: BLUEPRINT — component key: product
     src/trace_registry.py ARCHITECTURE_COMPONENTS
     Enforced by tests/test_trace_registry.py hierarchy checks. -->

> **Blueprint tier (product).** This file satisfies axiom group
> **axm:S** (Specification) from
> [AI_VIA_AXIOMS.md](../AI_VIA_AXIOMS.md), and is the home for
> decisions about **what is sold** — as distinct from what is built.
> See [TRACE_MAP.md](../architecture/TRACE_MAP.md#the-blueprint-tier)
> for the full chain.

**Scope boundary (ruled 2026-09-01).** Product/offering decisions live
here, not in `docs/architecture/`. Architecture answers *what the
system is and how it works*; this file answers *what a customer buys*.
When the two need each other, they link — they never restate.

Ratified by **ADR 0063** (the tier lock, 2026-08-30), which is also a
SCOPE LOCK: every new idea is sorted into a tier's v1 or the roadmap
before it is built; what fits no box waits.

---

## The cross-cutting law

**Artifacts land, chat doesn't.** Every tier's output lands as a
durable, graded artifact in a system of record (their DG catalog,
Power BI, the certified graph); the chat is a query surface and stores
nothing. The DG tool receives conclusions, not conversations.

## The four tiers

### The Estate X-Ray — the wedge

Fixed-price, one-shot diagnostic, entirely in the customer's tenant:
deploy → harvest + parse the SQL/PBI estate → run the sweep and
closeness machinery → deliver **the X-Ray Report** (their real counts,
red flags with members and code-level basis, the AI-readiness verdict).
Engine removable or dormant after.

Cheap to accept: no integration, no end users, one admin. The report's
final page is Tier 1's order form.
Runbook: [XRAY_ENGAGEMENT.md](XRAY_ENGAGEMENT.md).

### Tier 1 — Bridge (headless; the anchor)

Admin-only, no end-user interface. Continuous harvest → parse → graph
→ the **Write-Back Queue** into the customer's existing governance
estate: descriptions onto assets and reports, proposed business terms,
relationships, steward conflict alerts, and continuous re-parse on
estate change.

**The Write-Back Queue is law:** every proposed write enters a review
set — technical items approved by a developer, business items by a
steward — then lands, logged with approver and basis. Nothing
machine-authored enters an enterprise record unapproved.

Integration is **file-first** (stage 1): approved sets export as native
import files the admin uploads. Direct API is stage 2.

### Tier 2 — Workbench v1 = the Resolution Console

**Not open chat at launch.** Every session starts from a machine-found
flag with its computed evidence, and every action is a predefined
button — **compare · certify · delegate · deny (with reason)**;
developers additionally **approve technical writes / fork**. Closed
domain, so zero open-world parse risk.

**The Inbox:** the console and the Write-Back Queue are ONE surface.
Open interrogation ("ask anything") is roadmap.

### Tier 3 — Run (gated)

Certified, parameterized execution of the confirmed definition. **GA is
gated** on the output-side PHI gate and dedicated read-only principals
(recorded listing blockers). Do not list as available.

## Packaging and sequencing

- **Separable SKUs, bundled launch.** Bridge is purchasable alone (the
  UI-averse enterprise exists); the launch offer and every demo lead
  with Bridge + Workbench together — the sync proves ROI, the chat
  proves magic.
- **Launch motion:** X-Ray → Bridge + Workbench bundle → Run when the
  gates clear and pilots warrant.
- **Pricing and final naming are PARKED** (ADR 0063 §5/§8, Sunny's
  call with the sales motion). The $25k/yr anchor was noted in debate,
  not ruled. No document may invent these numbers.

## Positioning — the four moats

1. Catalog-first incumbents carry architecture debt; a graph-native
   engine is the light one.
2. Generic LLM summarization hallucinates; deterministic parsers plus
   the honesty gate give code-level trust anchors.
3. Tenant-local: no data reaches the vendor; PHI-safe by construction.
4. A closed loop — diagnose → interrogate → certify → write back — not
   descriptions in a parking lot.

## Where the offer meets the architecture

| Offer claim | Architecture that backs it |
|---|---|
| Parses the real estate | [ARCHITECTURE.md](../architecture/ARCHITECTURE.md), [INTEGRATION_MAP.md](../architecture/INTEGRATION_MAP.md) |
| Finds contradictory definitions | ADR 0054 (the red-flag sweep) |
| Writes only what a human approved | [DECISION_LANDING_MATRIX.md](../architecture/DECISION_LANDING_MATRIX.md) |
| Never fabricates an answer | [SPEC.md](../architecture/SPEC.md) — `spec:B1`, `spec:E6` |
| Runs without touching patient data | [SPEC.md](../architecture/SPEC.md) §14g — `spec:R6`–`R8` |

## Downstream artifacts

These express the offer for a specific audience and must not contradict
this file:

- [MARKETPLACE_LISTING.md](MARKETPLACE_LISTING.md) — **TABLED
  2026-09-01.** Not in flight; revisit at listing time.
- [XRAY_ENGAGEMENT.md](XRAY_ENGAGEMENT.md) — the delivery runbook.
- [REVIEWER_GUIDE.md](REVIEWER_GUIDE.md) — Microsoft certification.
- [SECURITY_WHITEPAPER.md](SECURITY_WHITEPAPER.md) — compliance posture.
