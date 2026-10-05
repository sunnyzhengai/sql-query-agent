# Brief_M07_Stage_B_Host

Status: RULED (Sunny, 2026-10-01, in chat): B1 builds in this phase
(04); B2 deferred to its own later phase; Shape 2 rejected
(one-engine law). SaaS-offer timing: still open.
Drafted: Claude, overnight 2026-10-01.
Audited 2026-10-04 (the briefs sweep): rulings match the estate;
the stale "TBD" at 04 decision 7 and the stale header TBD line
(secret names + stage B host) were found in 04_fabric_move.md and
aligned same day. SaaS timing verified still unruled.
The question: where does the production chat surface live? (04 design
decision 7, stage B.)

## The finding that reshapes the question

The 2026 Fabric Extensibility Toolkit is NOT the heavy lift the
original decision assumed. A Fabric "workload" today is:

- **a web app you host in your own cloud** (React is the sample),
  which Fabric loads in an iframe and makes feel native via a
  manifest (identity, item types, routes, permissions);
- **frontend-only by default** — the toolkit's model is a browser app
  using Entra ID tokens to call Fabric APIs *and your own backend
  services directly*; the sample even hosts on Azure Storage static
  websites;
- **publishable two ways**: the Workload Hub (attestation document,
  a <5-second trial experience, an Azure Marketplace SaaS offer,
  validation) — or, new in 2026, **private preview direct to up to 20
  customer tenants with NO Microsoft certification** — a
  pilot-friendly path that did not exist when the tier lock was
  ratified.

Consequence: the two options from the 04 design doc are not rivals —
they are **layers of the same build**. An Azure-hosted backend is the
substrate of BOTH; the Fabric workload is a React frontend + manifest
wrapped around it. And the Azure Marketplace SaaS offer is required
for listing in either path.

## The three shapes, honestly costed

**Shape 1 — Azure-hosted web app only (no Fabric presence).**
The Python engine productionized behind a real web host (Azure App
Service ~ $13-55/mo, or Container Apps near-zero at pilot traffic),
Entra sign-in in front, the existing page served from it, reading the
lakehouse exactly as stage A proved and the vault for keys.
- Effort: smallest. Hardening the stdlib server (or porting its 3
  endpoints to a small framework), Entra auth middleware, deployment.
- What it buys: a URL a pilot customer can use. What it lacks: zero
  presence inside Fabric; "open another tab" product feel.

**Shape 2 — pure frontend-only toolkit port.**
Rebuild the chat UI in React inside Fabric's iframe, port the ENGINE
to the browser (TypeScript) or call Fabric APIs directly from the
frontend.
- Effort: largest — the funnel, LLM calls, and provenance logic would
  need a TypeScript twin, violating the one-engine law. NOT
  RECOMMENDED; listed for completeness.

**Shape 3 — the hybrid (the toolkit's own intended pattern).**
Shape 1's backend stays the one engine; a thin React frontend (the
existing page's JS is already close to framework-free React shape)
rides in Fabric's iframe via the manifest and calls our backend with
Entra tokens. AIVIA becomes an ITEM in the customer's workspace —
the native marketplace story — while the engine stays Python, ours,
tested, one codebase.
- Effort: Shape 1 + a frontend wrapper + manifest + (eventually) the
  Workload Hub obligations (attestation, <5s trial, SaaS offer).
- De-risked by the 2026 private-preview path: AIVIA can sit in up to
  20 pilot tenants BEFORE any certification.

## The recommendation

**Stage B splits in two, and only B1 needs ruling now:**

- **B1 (recommended to rule into phase 04 or its own small phase):
  build Shape 1** — the Azure-hosted, Entra-fronted engine. It is the
  substrate of every future, it unblocks pilots with a URL, and
  nothing about it is throwaway.
- **B2 (defer, keyed to marketplace timing): the Fabric workload
  wrapper (Shape 3)** — its own phase when the marketplace push
  starts; the 20-tenant private preview is its pilot on-ramp. The
  Agent-posture ruling already guarantees zero architectural
  dependency on anything Fabric-Agent-related.

Also needed on the marketplace path regardless of shape: the Azure
Marketplace SaaS offer (can start as a "contact me" listing for lead
generation before transactability).

## For Sunny's ruling

[x] B1 ruled: Shape 1 builds in phase 04 (Sunny, 2026-10-01)
[x] B2 deferred to its own phase, keyed to the marketplace push
    (Sunny, 2026-10-01)
[x] Shape 2 rejected (one-engine law) (Sunny, 2026-10-01)
[ ] The SaaS offer's timing — with B1, with B2, or later

## Sources

- [Fabric Workload Hub validation guidelines and requirements](https://learn.microsoft.com/en-us/fabric/workload-development-kit/publish-workload-requirements)
- [Extensibility Toolkit Architecture](https://learn.microsoft.com/en-us/fabric/extensibility-toolkit/architecture)
- [Extend the Microsoft Fabric frontend](https://learn.microsoft.com/en-us/fabric/workload-development-kit/extensibility-front-end)
- [Publishing Requirements for Microsoft Fabric Workloads](https://learn.microsoft.com/en-us/fabric/extensibility-toolkit/publishing-requirements-overview)
- [How to host your workload in Azure](https://learn.microsoft.com/en-us/fabric/extensibility-toolkit/tutorial-host-workload-in-azure)
- [Fabric Workload Development Kit monetization](https://learn.microsoft.com/en-us/fabric/workload-development-kit/monetization)
- [Fabric Extensibility Toolkit: Publishing Workloads announcements](https://community.fabric.microsoft.com/t5/Fabric-Updates-Blog/Fabric-Extensibility-Toolkit-Publishing-Workloads-announcements/ba-p/5172418)
