# ADR 0056 — The decision algebra: every answer ends in a decision

**Status:** ACCEPTED 2026-08-25 — Sunny ratified: taxonomy + weights
AS PROPOSED; disclosure policy = (b) DISCLOSED counts with the
mandatory provenance sentence; deny carries full weight only WITH a
reason. Sequencing: build after the demo capture (review's default,
confirmed below).

**Sunny's framing rulings (2026-08-25, recorded):**
1. Every question/answer should trigger a user DECISION that feeds
   back into the graph — an answer is not a paragraph, it is a
   decision point. (Extends "operations are the product": every
   answer ends in an operation.)
2. **Tier cut:** BASIC = decision capture AND application (the full
   governance flywheel: usage-weighted ranking, flag priority,
   election of officials). PRO = DATA EXECUTION — from a
   choose/fork decision, the saved logic actually runs against the
   source database and returns data. Rationale: data is the
   rubber-meets-the-road moment; it settles logic debates fastest;
   self-service is the holy grail of analytics.
3. Usage is the quiet spokesperson for governance (standing
   philosophy): structural flags find CANDIDATES; decisions ELECT
   what matters.

## First principles

- **P1 — Strength = cost of being wrong.** A decision's weight
  derives from what the decider stakes: nothing (a glance), their
  word (confirm), their role (certify), their work (run). Extends
  Sunny's 2026-08-09 ruling (confirmations heavy, picks light).
- **P2 — Asserted is never parsed.** Decision edges are human
  TESTIMONY, typed and provenance-marked, in an asserted-edge
  layer. Parsed edges are machine FACT. No answer may present
  testimony as fact; any answer leaning on asserted edges discloses
  it.
- **P3 — Append-only, countermand-not-edit.** A decision is an
  event; a later decision supersedes it; nothing is rewritten (ADR
  0023 discipline).
- **P4 — Authority is scoped, not assumed.** Anyone may testify
  (choose/confirm/deny); only stewards certify (0054 ruling);
  fork/personal variants wait behind the ADR 0038 access-control
  gate; execution runs under the user's OWN identity (passthrough)
  — AIVIA never grants data access.
- **P5 — Data never enters the model.** PRO execution results
  render display-only; returned rows NEVER enter LLM context. The
  model orchestrates; it cannot leak what it never saw.

## The taxonomy [RATIFY — weights are proposed ordinals, not tuned]

| decision | actor | asserts | strength | edge minted (asserted layer) | requires | tier | notes |
|---|---|---|---|---|---|---|---|
| view/expand | anyone | attention | 0 (telemetry) | none (event only) | — | Basic | never influences ranking alone |
| **choose** | anyone | "proceeding with this one" (pre-reading, among candidates) | weak (1) | `chose` | candidates displayed | Basic | the 2026-08-09 pick |
| **confirm** | anyone | "this IS the definition I use" (post-reading) | strong (3) | `confirmed` | full record displayed | Basic | the 2026-08-09 confirmation |
| **deny** | anyone | "wrong / not what I need" | strong negative (−3 with reason, −1 without) | `denied` (+reason, TYPED per ADR 0057: defect→developer / mismatch→fork offer / noncompliance→use-owner) | — | Basic | reasoned denial is a fixture candidate; the type routes it |
| **certify** | steward | "official for scope" | authoritative (5) | `certified_official` (scope) | steward role (Entra) | Basic | = 0054 disposition, now also reachable at point of use; mandatory reason per 0054 |
| **label-variant / accept / retire** | steward | 0054 dispositions | authoritative | per 0054 | steward role; mandatory reason | Basic | the steward queue = where contested testimony escalates |
| **fork** | anyone (owner-scoped) | "my variant of this" | strong (3, scoped) | `variant_of` + new artifact | **ADR 0038 gate** | Basic (post-0038) | personal truth layer; stays gated |
| **accept-stewardship** | anyone offered | "I take accountability for this node" | authoritative (scoped) | `stewards` (earned, disclosed) | harvest offer (ADR 0057) | Basic | opt-in at peak willingness; contestable |
| **run** | anyone with DB rights | "I act on this definition's data" | strongest usage signal (8) | `executed` (+count) | plan-confirm; passthrough identity; P5 | **PRO** | repeated runs compound; the ultimate elector |

## Application (Basic — Sunny's ruling: capture AND application)

- Ranking: search/candidate ordering may use decision weight as a
  SECONDARY sort (parsed relevance first — asserted never overrides
  fact; disclosed when it reorders).
- Flag priority: flag rank = f(blast radius, Σ decision weight on
  members) — "this conflict touched N decisions this month."
- Election: officials are CERTIFIED by stewards, never auto-elected
  by usage; usage evidence is PRESENTED to the steward ("confirmed
  41×, denied 0×") — the flywheel informs, the human rules (never
  gate on certification; the regulator pattern).

## Disclosure policy [RATIFY — the open question]

Options: (a) ranking-only (decisions invisible in answers); (b)
disclosed counts with provenance ("chosen 12×, confirmed 3× this
quarter — user testimony, not parsed fact"). Review recommends (b)
with the provenance sentence mandatory — it is the flywheel made
visible, and P2's disclosure duty keeps it honest.

## PRO execution (the ultimate goal — design constraints now, build later)

- Runs governed logic per the self-service ladder (PRODUCT_PICTURE
  .md): rung 1 certified-verbatim, rung 2 typed parameter
  substitution (values never logic), rung 3 composed-from-certified-
  steps marked UNCERTIFIED DRAFT. Generation is never SILENT —
  disclosed, displayed, plan-confirmed before execution (ADR 0050;
  amended 2026-08-25 from 'never LLM-generated' per Sunny's rung-3
  ruling: disclosure, not prohibition).
- Passthrough identity: the source database's security model
  authorizes; AIVIA holds no data entitlements.
- P5 absolute: results render in the UI; no row ever enters model
  context; row counts/timings may be logged, values never.
- Each run mints `executed` testimony — the strongest usage signal
  feeding Basic's flywheel.

## Ratifications (Sunny, 2026-08-25)

1. Taxonomy + weights: RATIFIED as proposed.
2. Disclosure: (b) — decision counts disclosed in answers with the
   mandatory provenance sentence ("user testimony, not parsed fact").
3. Deny: full weight requires a reason. RATIFIED.
4. Sequencing: capture first, 0056 build after (the demo does not
   depend on the decision layer).
