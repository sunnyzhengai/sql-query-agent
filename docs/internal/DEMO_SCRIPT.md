# Demo Video Script (~6 minutes)

**Target audience:** Microsoft Marketplace reviewers, prospective customers
**Tone:** professional, concise, value-first — the architecture is SHOWN
(the Basis line, computed verdicts), never narrated as history.
**Rewritten 2026-08-13** for the AIVIA agent (ADR 0035): web chat
surface, deterministic tools, code-stamped provenance, admin telemetry.

**Deviation is welcome, not feared (hard rule, 2026-08-09):** the
agent passed a 54-conversation paraphrase suite at 100% on every
mechanical check (AGENT_ROBUSTNESS_BASELINE.md). Phrase the questions
naturally; the script's wording is a guide, not a guardrail. Beat 6
deviates ON CAMERA on purpose.

**Prerequisite:** the web chat (App Service) deployed and signed in;
admin dashboard open in a second tab; capacity Active; a fresh
conversation.

---

## Opening (30 seconds)

**[Screen: the AIVIA chat page, empty]**

"Every health system has hundreds of SQL stored procedures powering
their reports. The business logic inside them — the filters, the
clinical criteria, the compliance calculations — is undocumented. When
an analyst asks 'how is this metric calculated?', the answer takes
days, and when an AI answers instead, you can't tell whether it's
right.

AIVIA reads your SQL, builds a certified knowledge graph in your own
tenant, and answers in plain English — with every answer showing
exactly what it consulted. Provable, or it doesn't answer."

---

## Part 1: The problem (30 seconds)

**[Screen: open USP_Severe_Sepsis SQL — scroll]**

"Here's a real example — a sepsis compliance procedure. Thousands of
lines of T-SQL, dozens of temp tables, complex clinical criteria.
Nobody has time to read this, and the business doesn't even call it
'USP_Severe_Sepsis' — they call it the severe sepsis report."

---

## Part 2: The pipeline (45 seconds)

**[Screen: 02_parse output → 06_validate output]**

"Setup is a notebook pipeline in YOUR Fabric tenant. Microsoft's own
ScriptDom parser reads every file — 28 of 28, zero errors — a PHI scan
gates anything that would reach an AI model, and business descriptions
are generated against your own Azure OpenAI endpoint. Your SQL never
leaves your tenant, and we never hold a key."

**[Show 06_validate: DEPLOYMENT READY]**

---

## Part 3: Ask anything (2.5 minutes — the heart)

**[Screen: the AIVIA chat]**

### Beat 1 — the headline answer, with receipts

**[Ask, in your own words: how is ED Sepsis Screening calculated?]**

Answer arrives in business language, ends with the real Power BI
report link. **Point at the Basis line under the answer:**

"Notice the Basis line. Every answer discloses exactly what was
searched, what was read, and what was computed — stamped by code, not
written by the AI. This is what makes the answer auditable instead of
plausible."

**[Click the report link — the dashboard opens.]**

### Beat 2 — a real conversation

**[Ask: show me its SQL]** → the actual stored logic, on demand.
**[Ask: who owns it?]** → honest: "no steward recorded." Say:

"It doesn't invent an owner. Unassigned stewardship is a governance
gap — and you'll see in a minute that the admin dashboard tracks
exactly that."

### Beat 3 — the governance stunner (the money shot)

**[Ask: are all definitions of Base_Pop_Severe_ED_Scores the same
across our procedures?]**

Six procedures define that step. **Five different definitions.**

"This is copy-paste drift caught red-handed — six teams believing they
compute the same thing, five different truths. The comparison is a
computed verdict — content hashes, not an AI's impression — and this
single answer is why data governance teams want this product."

### Beat 4 — computed comparisons

**[Ask: does ED Sepsis Screening use the same logic as ED Sepsis
(Regulatory)?]**

"Two metrics, one question, a computed answer: distinct definitions.
The AI never judges whether SQL is the same — a hash comparison does,
and the AI just explains it."

### Beat 5 — it knows what it doesn't know

**[Ask: how many sepsis patients did we have yesterday?]**

"Definitions, not patient data — it refuses, instantly, and says what
it CAN do. No tools were consulted; nothing was made up."

### Beat 6 — DELIBERATE DEVIATION (on camera)

"Don't take the script's word for it." **[Have a colleague — or
ChatGPT, on screen — phrase a question about any certified metric
however they like. Ask it verbatim.]**

"Same grounded behavior on a question nobody rehearsed. That's not
luck — it's a 54-conversation robustness suite passing at 100% before
this recording."

---

## Part 4: The admin dashboard (45 seconds)

**[Screen: aivia_admin_telemetry_report, page through]**

"Admins get a Power BI report — generated and deployed automatically,
always current, no refresh to manage. Pipeline health with a
per-metric validation funnel. Knowledge coverage — including the
honest gaps: unassigned stewards are a work queue, in red. And agent
telemetry: every conversation, WHO made each decision — the
deterministic engine or the language model — and user feedback joined
to it, so if answers ever disappoint, you know which component to
blame.

This dashboard found a real validation bug in our own product the
first hour it existed. We fixed it the same day. That's what
observability is for."

---

## Part 5: Governance sync + close (30 seconds)

**[Screen: Purview glossary with published terms/descriptions]**

"Everything certified syncs to Microsoft Purview — descriptions and
business terms published to your catalog, with every push logged.

AIVIA: your SQL becomes a certified knowledge graph, and a governed AI
answers from it — provably, or not at all. Available on Azure
Marketplace."

---

## Recording checklist

- [ ] Fresh conversation (no leftover context on screen)
- [ ] Web app signed in as a real Entra user (identity visible = fine)
- [ ] Admin dashboard tab pre-loaded (page 1 green: 28/28)
- [ ] Purview provisioned same-day for Part 5 (batch with screenshots)
- [ ] Capture stills during recording: Basis-line answer, variants
      answer, refusal, dashboard page 1 + 3, Purview glossary
- [ ] Beat 6's outside question genuinely unrehearsed
