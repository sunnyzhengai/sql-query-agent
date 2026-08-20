# Marketplace Transactable — Requirements & Execution Plan

**Date:** 2026-08-06 · **Decision:** [ADR 0028](../decisions/0028-contact-me-first-transactable-on-first-buyer.md)
(Contact Me now → same-offer conversion at first-buyer signal).
Verified against live learn.microsoft.com pages (most revised 2026-07-22/23).
Branding note: Azure Marketplace + AppSource are now one "Microsoft
Marketplace"; mechanics unchanged; new "AI Apps and Agents" category is
relevant for positioning.

## What transactable requires (verified)

### Fulfillment APIs — v2, mandatory, backend-only

Base `https://marketplaceapi.microsoft.com/api/saas`, every call
`?api-version=2018-08-31` (v2's wire version; v1 dead, no v3). Must be
called service-to-service, never from the browser.

| Operation | Call |
|---|---|
| Resolve purchase token | `POST /subscriptions/resolve` (header `x-ms-marketplace-token`, URL-decoded, 24 h validity) |
| Activate | `POST /subscriptions/{id}/activate` — billing starts here (unless auto-activation) |
| Get/List subscriptions | `GET /subscriptions[/{id}]` |
| Change plan / quantity | `PATCH /subscriptions/{id}` — one change per call; 202 + poll `Operation-Location` |
| Cancel | `DELETE /subscriptions/{id}` — 72 h no-bill window |
| Poll/ACK operations | `GET`/`PATCH /subscriptions/{id}/operations/{opId}` |

Subscription statuses: `PendingFulfillmentStart → Subscribed ⇄ Suspended →
Unsubscribed` — modeled in `src/marketplace/fulfillment.py` (tested).

### Landing page — 24/7, SSO, mandatory

Receives `?token=...`; resolve → onboard → activate. Entra SSO for work
accounts **and** personal MSA (tenant `9188040d-6c67-4c5b-b112-36a304b66dad`);
handles first purchase + returning "Manage account"; no `#` in URL.
**Certification policy 1000.3:** request only `User.Read` at activation —
admin-consent permissions on the landing page are a rejection reason.

### Connection webhook — 24/7, authenticated, mandatory

POST events: `Subscribe` (auto-activation), `ChangePlan`, `ChangeQuantity`,
`Renew`, `Suspend`, `Reinstate`, `Unsubscribe`. Rules: always HTTP 200 ACK;
for ChangePlan/ChangeQuantity, accept/reject via operation PATCH within 10 s
(silence = auto-accept); validate each payload via Get Operation before
acting; **validate the Authorization JWT** (aud = our Entra app id, appid =
marketplace resource, tid = our tenant — enforcement is coming); tolerant
deserialization (Microsoft extends the schema); Microsoft retries 500×/8 h.
Event semantics are encoded in `src/marketplace/fulfillment.py` (tested).

### Identity — two app registrations

1. Landing page app: **multitenant**, OIDC, basic consent only.
2. Fulfillment app: **single-tenant**, client credentials; tenant+app id go
   into the offer's Technical configuration. Token:
   `POST login.microsoftonline.com/{tenant}/oauth2/v2.0/token` with
   `scope=20e940b3-4c77-4b0b-9a53-9e16a1b010a7/.default` (marketplace SaaS
   resource id; also `az ad sp create --id 20e940b3-...` once in our
   tenant). 1 h tokens, same token for fulfillment + metering.

### Certification & fees

- Pipeline: automated validation (<30 min reports) → certification (manual
  + automated; SSO, API round-trip, webhook, listing accuracy, working
  privacy/terms/support links) → preview (real test purchase, nominal
  price, cancel <72 h) → go-live. Unlimited resubmissions. No official
  end-to-end SLA; practitioner consensus **2–4 weeks** first time.
- **3% agency fee** (1.5% on qualifying private-offer renewals/migrations,
  self-attested at creation). Monthly payout, $50 minimum, +30 d escrow on
  credit-card transactions. Customer refund window 72 h.
- Go-live gates: business verification authorized, payout profile, tax
  profile (**W-9 mandatory for the LLC**) — each up to 48 h validation.
  None needed for Contact Me.

### 2025–26 changes worth knowing

- **Auto-activation** plan option (Microsoft activates at purchase;
  `Subscribe` webhook instead of resolve/activate) — we start with it OFF
  (ADR 0028) while onboarding is high-touch.
- **Transactable free trials** (1–180 d, auto-convert, `isFreeTrial`
  everywhere) — candidate replacement for the "30-day free trial" listing
  promise when we convert.
- Private offers: custom terms PDF, 1–120-month terms, org-level
  targeting, live in 15 min — the founding-customer vehicle at ~$2,000/mo
  (fee at $24k/yr: $720; private offers **require** transactable).

## Execution plan

**Phase T0 — now (no external deps):**
- [x] Subscription state machine + webhook event contract as pure library
      code with tests (`src/marketplace/`, `tests/marketplace/`) — this
      commit
- [ ] Keep pushing verification/tax/payout in Partner Center (48 h each,
      they gate conversion, not Contact Me)

**Phase T1 — Contact Me listing (when verification clears):**
- [ ] Publish existing listing assets as Contact Me; wire lead intake
      (Referrals workspace; HTTPS endpoint connector later)

**Phase T2 — transactable conversion (first-buyer signal, per ADR 0028):**
- [ ] Azure hosting for landing page + webhook (thin host over
      `src/marketplace/`; App Service or Functions)
- [ ] Two app registrations (multitenant landing / single-tenant
      fulfillment); marketplace SP registered in tenant
- [ ] Technical configuration on the offer; plan: flat $2,000/mo public
      plan (+ annual), Standard Contract, auto-activation off
- [ ] Preview-audience test purchase at nominal price; cancel within 72 h
- [ ] Convert listing option to Transact, republish, respond to
      certification (2–4 wk budget)
- [ ] First customers via private offers (custom terms PDF, founding
      pricing, 1.5% renewal attestation where applicable)

**Unverified items to confirm with publisher support before T2:**
ratings/reviews continuity across the listing-option change; current
end-to-end certification SLA.
