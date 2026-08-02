# Internal Documents — Do Not Distribute

Everything in this folder is **internal to AIVIA LLC**: strategy, pricing rationale,
competitive positioning, launch planning, and deployment runbooks.

**Never include this folder in anything a customer, partner, or Microsoft reviewer
receives** — deployment packages, Lakehouse uploads, reviewer sandboxes, or public
repo mirrors. The customer-facing documentation lives in `docs/architecture/`,
`docs/deployment/`, `docs/product/`, and `docs/legal/`.

## Contents

| Document | Purpose |
|---|---|
| [ROADMAP.md](ROADMAP.md) | **Single source of truth for project status.** Phased plan with live checkboxes. |
| [PRODUCT_POSITIONING.md](PRODUCT_POSITIONING.md) | Messaging, pricing anchors, competitive framing, strategic options |
| [LAUNCH_PLAN.md](LAUNCH_PLAN.md) | Go-to-market plan |
| [MARKETPLACE_PIVOT.md](MARKETPLACE_PIVOT.md) | Frozen decision record (2026-07-25) — decisions extracted to `docs/decisions/` |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | Script for recording the Marketplace demo video |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Internal deployment-team runbook (customer-facing guide is `docs/deployment/INSTALLATION_GUIDE.md`) |

## Status ownership rule

**ROADMAP.md owns all status tracking.** No other document — internal or public —
should carry live checkboxes, "done/not started" claims, or current metrics
(parse rates, test counts). Frozen documents (like MARKETPLACE_PIVOT.md) keep
their historical state but are banner-marked as snapshots. Architectural
rationale lives in `docs/decisions/` (ADRs), not here.
