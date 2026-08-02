# ADR 0013: List as Transactable SaaS on Microsoft Commercial Marketplace

**Status:** Accepted
**Date:** 2026-07-25 (extracted from MARKETPLACE_PIVOT.md D7)

## Context

Distribution options: sell directly, list as "Contact Me" (lead-gen only), or
list as a transactable SaaS offer through Partner Center.

## Decision

Target a transactable SaaS offer. The listing may launch as "Contact Me" first
to ship faster (no landing page/fulfillment API needed), converting to
transactable once early customers validate demand.

## Consequences

- Transactable offers are MACC-eligible — enterprise customers can spend
  pre-committed Azure budget on AIVIA
- Co-Sell Ready status becomes available once listed; Microsoft's sales force is
  incentivized to pitch Co-Sell Ready products
- Transactable requires a landing page, Fulfillment API integration, and webhook
  handlers; Microsoft takes a 3% fee
- The SaaS *offer type* is a billing construct — the architecture remains BYOT
  (ADR 0007); nothing is hosted by AIVIA
