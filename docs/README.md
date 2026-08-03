# Documentation

Organized by audience. **Everything under `internal/` is AIVIA-only — never
include it in customer deployment packages, Lakehouse uploads, or reviewer
sandboxes.** Everything else is safe to share.

## Architecture (public)
- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) — Three-layer graph model, module map, data flow, deployment models
- [PIPELINE_MAP.md](architecture/PIPELINE_MAP.md) — **Generated** dataflow DAG projected from the data contracts (do not edit; `python scripts/generate_docs.py`)
- [USER_FLOW.md](architecture/USER_FLOW.md) — End-to-end question flow (Path A/B, flywheel, row-level security, dual delivery)

## Decision Records (public)
- [decisions/](decisions/README.md) — One ADR per architectural/product decision (native parsers, Delta over graph DB, BYOT, tiering, …). Canonical home for rationale.

## Deployment (customer-facing)
- [INSTALLATION_GUIDE.md](deployment/INSTALLATION_GUIDE.md) — **Canonical install guide** for the customer's IT/data team (Environment, Lakehouse, pipeline, Data Agent)
- [DATA_DICTIONARY_REQUIREMENTS.md](deployment/DATA_DICTIONARY_REQUIREMENTS.md) — Required dictionary CSV format and extraction queries

## Development (contributor-facing)
- [SETUP.md](development/SETUP.md) — Local development environment
- [TESTING.md](development/TESTING.md) — Test strategy and running tests
- [ANONYMIZATION_STRATEGY.md](development/ANONYMIZATION_STRATEGY.md) — How real-world SQL is anonymized for tests and demos

## Product Collateral (external-facing)
- [SECURITY_WHITEPAPER.md](product/SECURITY_WHITEPAPER.md) — BYOT security architecture, data handling, compliance posture
- [MARKETPLACE_LISTING.md](product/MARKETPLACE_LISTING.md) — Marketplace offer copy
- [REVIEWER_GUIDE.md](product/REVIEWER_GUIDE.md) — Step-by-step guide for Microsoft certification testers

## Legal (public)
- [privacy-policy.md](legal/privacy-policy.md)
- [terms-of-service.md](legal/terms-of-service.md)

## Internal (AIVIA only — do not distribute)
- [internal/](internal/README.md) — Strategy, positioning, pricing, launch planning, deployment runbook
- [internal/ROADMAP.md](internal/ROADMAP.md) — **Single source of truth for project status** and canonical metrics

## Other
- [notebooks/data_agent_instructions.md](../notebooks/data_agent_instructions.md) — Fabric Data Agent grounding instructions
- [CHANGELOG.md](../CHANGELOG.md) — Release history
