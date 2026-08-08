# Contact Me Listing — Submission Runbook

**Purpose:** every step from today to a live Marketplace listing, in
execution order. Status reconciled against the build on **2026-08-09**.
ROADMAP Phase 4 stays the strategic view; this is the do-list. Check
items off here while executing; fold final status back into ROADMAP at
submission.

**Definition of done:** the offer is live on Microsoft Marketplace as
Contact Me, and a lead that arrives tomorrow gets a professional
response.

---

## Already done (verified, with dates)

- [x] Partner Center: business verification (2026-08-06), W-9
      (2026-08-06), payout profile → Chase (2026-08-06)
- [x] Offer assets: name, description (MARKETPLACE_LISTING.md), logos
      (4 sizes), pricing ($2,000/mo · $21,600/yr · 30-day trial),
      keywords, privacy/terms/support URLs live on aiviaapp.com
- [x] Security whitepaper, reviewer guide, installation guide (incl.
      Azure OpenAI step 3f), data-dictionary requirements
- [x] Architecture diagrams: Lucid V2 PDF in docs/product + mermaid
      sources (System at a Glance = the security-boundary diagram)
- [x] Demo tenant runs the full product: 1.4.2 pipeline green, PHI
      gate live, descriptions live, business names + report links live
- [x] Delta agent passes the 6-question demo QA (2026-08-08, 6/6);
      demo report exists (ED Sepsis Screening Dashboard, synthetic
      footer)
- [x] validate_deployment.py + build_deployment_package.py exist and
      are tested

## Blockers — must happen before submission, in order

1. [ ] **Checklist E first** (you're running it now): golden snapshot,
       then the semantic-catalog on-tenant pass. The snapshot matters
       here because the demo gets recorded against a state you can
       restore.
2. [ ] **Publish both agents** (they are still **Draft** — tonight's QA
       ran in the test pane): open each agent → **Publish**. Then ask
       the Delta agent one question on the published surface and
       LEFT-CLICK the report link — if it opens, the video shows a
       click; if not, the video shows open-in-new-tab. Ten minutes.
3. [ ] **Record the demo video** (~5 min, per DEMO_SCRIPT.md — but
       note the script predates business names/report links; adjust
       beats to feature: "How is ED Sepsis Screening calculated?" →
       certified steps → "Used in:" link → open the dashboard; the
       28-metric business-name listing; the FAKE_METRIC refusal; the
       honest no-steward answer). No org-specific data on screen —
       the corpus is anonymized and the dashboard is synthetic-footed.
4. [ ] **Capture 3–5 screenshots** while recording: business answer
       with report link, metric listing, refusal, validation health
       (06 output), architecture diagram. Save originals to
       presentation/ for reuse.
5. [ ] **Package + self-validate** (30 min, terminal):
       `python scripts/build_deployment_package.py` then point
       `python scripts/validate_deployment.py --root <unzipped output>`
       at it — the artifact a lead receives must pass our own
       pre-flight. Claude can run this with you.
6. [ ] **Lead-handling minimum** (writing, ~1 hour, Claude drafts):
       - support@ response expectation on the listing (e.g. 2 business
         days) + the escalation note (support@ → founder)
       - lead intake questionnaire (Fabric capacity? dictionary ready?
         SQL dialect? Azure OpenAI available?)
       - scheduling link (Calendly/Bookings) for qualified leads
7. [ ] **Partner Center: create the offer** (portal, ~1–2 hours):
       New offer → SaaS → listing option **Contact Me** → paste/upload
       assets from docs/product → lead destination: start with email
       (Referrals workspace default), CRM connector later →
       **Publisher Attestation questionnaire** (answers project from
       SECURITY_WHITEPAPER.md; Claude drafts responses on request)
8. [ ] **Review and publish** → automated validation (<30 min) → fix
       anything the validation report flags → certification (days,
       lighter for Contact Me — no API tests) → **live**.

## Should-do (not blocking; before or during certification wait)

- [ ] Whitepaper refresh: PHI scanning is now IMPLEMENTED (ADR 0025,
      live on tenant 2026-08-08) — claim it accurately; add the Azure
      OpenAI abuse-monitoring exemption note for strict-PHI customers
- [ ] Reviewer guide refresh: business names, report links, and the
      required agent table scoping (incl. graph_edge_uses_table +
      graph_canonical — learned 2026-08-08)
- [ ] Purview glossary screenshots (checklist D.4, short-lived
      provision) — strengthens listing imagery; not required
- [ ] Fabric/API error codes in error_classifier (403/404/429)
- [ ] CSA STAR self-attestation — review; likely defer to transactable

## Explicitly NOT for this listing (tracked elsewhere)

- Transactable conversion (ADR 0028 phase T2; host scaffold built
  2026-08-08, deploys at first-buyer signal)
- Semantic catalog agent wiring (checklist E; product feature, not
  listing-blocking)
- Rematch Round 3, dimension layer, connectors (ROADMAP)
