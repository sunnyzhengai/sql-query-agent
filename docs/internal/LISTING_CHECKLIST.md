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

## STATE RECONCILIATION (2026-08-11, overnight): the flagship is now
## the ADR 0035 agent (LLM conversation over five deterministic tools),
## live-evaluated 12/12 (docs/internal/AGENT_LIVE_RESULTS.md). The gate
## items below are re-mapped to that architecture.

## Blockers — must happen before submission, in order

0. [~] **READINESS GATE (hard rule, 2026-08-09):**
       1. [x] Answer layer — DONE as ADR 0035: deterministic tools +
          two dispatch guarantees; live-evaluated 12/12 (2026-08-11).
       2. [x] Robustness suite — DONE both levels: retrieval suite
          (hit 100%, group-top1 96.7%, re-based 2026-08-10) AND the
          agent-level paraphrase suite (2026-08-11: 54 live
          conversations, all mechanical checks 100% — see
          AGENT_ROBUSTNESS_BASELINE.md; gate ≥0.95 set).
       3. [ ] Demo recording with deliberate deviation — after the web
          surface exists (see 1b).
1. [x] **Checklist E** — golden snapshot + semantic catalog on tenant:
       DONE (2026-08-10, validated live).
1b. [ ] **NEW — the web surface** (UI decision 2026-08-10: one backend,
       two faces). The demo must show a customer-grade surface, not a
       terminal: FastAPI service wrapping the agent + a chat page +
       Entra sign-in, deployed in the tenant. This is the largest
       remaining build. Teams face is post-listing.
2. [ ] **Fabric Data Agents: decide their listing role** — they are
       demoted secondary surfaces (ADR 0032/0035). Either publish them
       as an optional feature with one verification question each, or
       drop them from the listing narrative entirely. Ten minutes
       either way; the demo no longer depends on them.
3. [ ] **Record the demo video** (~5 min). TWO scripts now exist:
       docs/internal/DEMO_SCRIPT.md (5-min listing cut, QA-verified
       questions) and data/demo/Demo Script Sepsis.md (long-form
       lead-call narrative, reviewed + corrected 2026-08-09 with the
       listing cut listed in its header). Pre-record QA gate: the new
       "How is our sepsis population defined?" question must pass a
       test-pane run first — fallback is the verified headline
       question. Never improvise count questions on camera.
4. [ ] **Capture 3–5 screenshots** while recording: business answer
       with report link, metric listing, refusal, validation health
       (06 output), architecture diagram. Save originals to
       presentation/ for reuse.
5. [x] **Package + self-validate** — DONE 2026-08-09 (Claude):
       v1.4.2 package built (now ships delta_agent_fewshots.json — gap
       found and fixed); validator run against the unzipped artifact:
       all shipped components green; the only failures are the three
       customer-supplied inputs (SQL, dictionary), each with
       fix-stating messages — which IS the pass condition for a fresh
       package (that's the lead's first-run experience working).
6. [~] **Lead-handling minimum** — DRAFTED 2026-08-09
       ([LEAD_HANDLING.md](LEAD_HANDLING.md)): first-response template,
       5-question qualification questionnaire, rubric, listing support
       statement. YOUR two steps: review/edit the template wording, and
       create the Bookings/Calendly page (paste URL into the doc).
7. [ ] **Partner Center: create the TRANSACTABLE offer** (2026-08-11:
       Contact Me is not available — Sunny, from the portal; ADR 0028
       superseded). Two halves:
       1. [ ] Claude: deploy marketplace_host (SaaS Fulfillment API v2
          landing page + lifecycle webhook + Entra app) to the same
          App Service as the web chat surface; end-to-end test with a
          Partner Center preview offer.
       2. [ ] Sunny (portal, ~1–2 hours): New offer → SaaS →
          transactable → plans ($2,000/mo · $21,600/yr · 30-day trial)
          → technical configuration (landing page + webhook URLs +
          Entra ids from step 1) → assets from docs/product →
          **Publisher Attestation** (Claude drafts responses on
          request). Note: transactable certification tests the
          fulfillment APIs — heavier than Contact Me would have been.
8. [ ] **Review and publish** → automated validation (<30 min) → fix
       anything the validation report flags → certification (days,
       lighter for Contact Me — no API tests) → **live**.

## Should-do (not blocking; before or during certification wait)

- [ ] PRE-SUBMISSION: finish the COLUMN-level anonymization crosswalk
      (live find 2026-08-16: PAT_ENC_CSN_ID x2205 in 15/28 files, plus
      PAT_ID/PAT_MRN_ID/HSP_ACCOUNT_ID/SERV_AREA_ID — Epic dialect the
      strategy doc says should be mapped). Sequenced AFTER the demo
      recording: rename pass -> make_golden_snapshot fixture rebuild ->
      full pipeline re-run -> robustness baseline re-earn -> re-seed
      demo source DB.
- [ ] Whitepaper + reviewer guide + DEMO_SCRIPT refresh for ADR 0035:
      the product story is now "conversational agent, deterministic
      tools, code-stamped provenance" — the demo script's beats change
      (basis lines under every answer are the differentiator to show)
- [ ] Architecture diagram redraw (promised post-refactor): agent +
      five tools + guarantees; Data Agents as optional surfaces
- [ ] Data refresh: live output_metric_logic lacks business_name —
      re-run the snapshot/05 path so answers use business names
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
