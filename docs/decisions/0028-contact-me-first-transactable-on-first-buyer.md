# 0028 — List as Contact Me now; convert the same offer to transactable at first-buyer signal

**Status:** Superseded (2026-08-11) — Partner Center does not offer a
Contact Me listing path for this offer; the listing ships TRANSACTABLE
from day one (Sunny, from the portal). The staging logic below is moot;
the transactable scaffold (marketplace_host/, built 2026-08-08 for the
"first-buyer signal") deploys now, sharing one App Service with the
ADR 0035 web chat surface. Pricing unchanged.
**Date:** 2026-08-06

## Context

ADR 0013 decided the destination: transactable SaaS on the Microsoft
Marketplace. The open question was timing — the ROADMAP carried
"Contact Me first, convert after 3 customers" as a recommendation without a
verified basis. Research against live Partner Center docs (2026-08-06,
[MARKETPLACE_TRANSACTABLE_PLAN.md](../../internal/docs/MARKETPLACE_TRANSACTABLE_PLAN.md))
established the facts that decide it:

- **Contact Me → Transact is a same-offer republish for SaaS** — listing
  option update, same offer ID and URL. No new offer, no listing reset.
- **Transactable is a one-way door with frozen choices:** once published
  transactable you cannot revert, and the *pricing model* (flat vs
  per-user) and *Standard Contract vs custom terms* choice freeze at that
  publish.
- **Private offers require a transactable offer** — founding-customer
  pricing (custom terms PDF, 1–120-month terms, expiry dates) is
  unavailable in a Contact-Me-only phase. This is the strongest argument
  against lingering.
- Transactable demands real infrastructure: Fulfillment API v2
  service-to-service integration, a 24/7 SSO landing page (multitenant +
  MSA), a 24/7 authenticated connection webhook — behind a certification
  pass realistically taking weeks, all gated anyway on business
  verification, tax (W-9), and payout profiles which are still in flight.
- Marketplace has consolidated to a single "Microsoft Marketplace" brand
  (2026); mechanics unchanged.

## Decision

1. **List as Contact Me as soon as business verification clears.** Zero
   technical prerequisites, leads flow to Partner Center Referrals, the
   listing exists and ranks while the demo tenant and fulfillment work
   finish. (Tax/payout profiles are not needed for Contact Me — keep
   pushing them in parallel since they gate the conversion.)
2. **Build the fulfillment integration now, in-repo, test-first:** the
   subscription state machine and webhook processing land as pure,
   framework-free library code (`src/marketplace/`) with full test
   coverage — the future Azure Function/App Service is a thin host around
   it, same pattern as notebooks around `src/steps/`.
3. **Convert to transactable at first-buyer signal** — a qualified lead
   ready to purchase, or the demo tenant live and submission-ready,
   whichever comes first. Not "after 3 customers": every early deal wants
   a private offer (custom price, custom terms), and private offers need
   transactable. First customers transact as private offers against a
   $2,000/mo public plan.
4. **Decisions to make deliberately at conversion (they freeze):** flat-rate
   pricing model (per-site flat fee, matches current $2,000/mo pricing;
   per-user makes no sense for a workspace-installed library), Standard
   Contract unless a lawyer says otherwise, and auto-activation OFF
   initially (manual activate after the landing-page handshake keeps
   billing honest while deployment is high-touch).

## Consequences

- The listing goes live weeks earlier than a transactable-first path, at
  the cost of no self-serve purchase in the interim — acceptable while
  onboarding is founder-led anyway.
- The scaffold (state machine + webhook contract in `src/marketplace/`)
  de-risks the certification items reviewers actually reject on
  (fulfillment API round-trip, webhook behavior, SSO landing page), before
  any Azure hosting exists.
- Supersedes the ROADMAP's "convert after 3 customers" note; ADR 0013
  stands (transactable remains the destination).
- Revisit only if Microsoft changes conversion mechanics (the one-way
  door and frozen choices are re-verified at conversion time).
