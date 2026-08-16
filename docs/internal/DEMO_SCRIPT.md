# Demo Video Script (~7 minutes)

**Target audience:** Microsoft Marketplace reviewers, prospective customers
**Tone:** professional, concise, value-first — the architecture is SHOWN
(the Basis line, computed verdicts), never narrated as history.
**Rewritten 2026-08-16** for the full 1.10.0 surface: turn-key
extraction, the consumption layer (reports + DAX), lineage-exact
publish-back. The through-line is the approved pitch: **"a federation of
native parsers, one per layer, stitched into one graph."**

**Deviation is welcome, not feared (hard rule, 2026-08-09):** the
agent passed a 54-conversation paraphrase suite at 100% on every
mechanical check (AGENT_ROBUSTNESS_BASELINE.md). Phrase the questions
naturally; the script's wording is a guide, not a guardrail. Beat 7
deviates ON CAMERA on purpose.
**QA gate before recording:** the report-layer beats (5 and 6) are NEW
surface — run them as a demo-QA pass on the live tenant first; the
robustness suite predates them.

**Prerequisites:** capacity Active; sql-logic-env at v1.10.0; 12 → 03 →
04 → 05 → 07 → 11 run since the upgrade (consumption layer + measure
descriptions in the graph and catalog); the `graph_edges` shortcut
created in the Eventhouse (RESUME_CHECKLISTS); web chat deployed and
signed in; admin dashboard open in a second tab; one PBI report whose
description field is EMPTY (for Part 4's publish moment); a fresh
conversation.

---

## Opening (30 seconds)

**[Screen: the AIVIA chat page, empty]**

"Every health system runs on two layers of hidden business logic: the
SQL in hundreds of stored procedures, and the DAX inside the Power BI
reports built on top of them. Both undocumented. When an analyst asks
'how is this number calculated?', the answer takes days — and when a
generic AI answers instead, you can't tell whether it's right.

AIVIA parses both layers with each platform's own native parser —
Microsoft's ScriptDom for SQL, the semantic-model definitions for
Power BI — and stitches them into one certified knowledge graph in
YOUR tenant. A federation of native parsers, one graph, and every
answer shows exactly what it consulted. Provable, or it doesn't
answer."

---

## Part 1: The problem (30 seconds)

**[Screen: open USP_Severe_Sepsis SQL — scroll]**

"Here's the SQL half — a sepsis compliance procedure. Thousands of
lines, dozens of temp tables, real clinical criteria. And the business
doesn't even call it 'USP_Severe_Sepsis' — they know it as the
dashboard built on it. That dashboard adds its own logic: DAX measures
nobody documents either. Two layers, zero documentation."

---

## Part 2: Turn-key ingestion (45 seconds)

**[Screen: extract_views cell 5 — the NEW / CHANGED / DELETED review]**

"Setup is turn-key: point AIVIA at your database — on-prem through a
gateway, Azure SQL, or Fabric-native — and it discovers every
procedure and view itself. No exports, no file drops. This is a
re-run: it found only what CHANGED since last week, and stops here for
your review before anything is written.

**[Screen: 12_ingest_semantic_models output — reports + measures +
derived names]**

The Power BI side is the same motion: it reads your semantic models —
git-synced or straight from the workspace — and extracts which SQL
each report executes, every DAX measure, and the reports' names, which
become the business names your people actually use.

**[Screen: 06_validate: DEPLOYMENT READY]**

Everything is parsed by the platform's own parser — never regex, never
guesswork — a PHI scan gates both SQL and DAX before anything reaches
an AI model, and descriptions are generated against your own Azure
OpenAI endpoint. Your logic never leaves your tenant; we never hold a
key."

---

## Part 3: Ask anything (2.5 minutes — the heart)

**[Screen: the AIVIA chat]**

### Beat 1 — the headline answer, with receipts

**[Ask, in your own words: how is ED Sepsis Screening calculated?]**

Answer arrives in business language, ends with the real Power BI
report link. **Point at the Basis line under the answer:**

"Notice the Basis line. Every answer discloses exactly what was
searched, what was read, and what was computed — stamped by code, not
written by the AI. And it answered to the name the business uses —
learned automatically from your own report estate."

### Beat 2 — a real conversation

**[Ask: show me its SQL]** → the actual stored logic, on demand.
**[Ask: who owns it?]** → honest: "no steward recorded." Say:

"It doesn't invent an owner. Unassigned stewardship is a governance
gap — and the admin dashboard tracks exactly that."

### Beat 3 — the governance stunner (the money shot)

**[Ask: are all definitions of Base_Pop_Severe_ED_Scores the same
across our procedures?]**

Six procedures define that step. **Five different definitions.**

"Copy-paste drift caught red-handed — six teams believing they compute
the same thing, five different truths. The comparison is a computed
verdict — content hashes, not an AI's impression."

### Beat 4 — blast radius: logic to dashboards

**[Ask: which reports are built on these?]**

"And here's why drift matters: these are the DASHBOARDS each version
feeds. That link isn't name-matching — it's parsed from the semantic
models themselves. When a definition is wrong, this is the blast
radius; when you fix it, this is who to notify."

### Beat 5 — the DAX layer

**[Ask: what does the Compliance Rate measure on that dashboard do?]**

Business description of the DAX arrives, grounded in the dictionary.
**[Ask: show me the DAX]** → the expression, on demand.

"Same treatment as SQL: parsed natively, PHI-gated, described in
business terms, raw code only when you ask. The report layer stopped
being a black box."

### Beat 6 — it knows what it doesn't know

**[Ask: how many sepsis patients did we have yesterday?]**

"Definitions, not patient data — it refuses instantly and says what it
CAN do. No tools consulted; nothing made up."

### Beat 7 — DELIBERATE DEVIATION (on camera)

"Don't take the script's word for it." **[Have a colleague — or
ChatGPT, on screen — phrase a question about any certified metric
however they like. Ask it verbatim.]**

"Same grounded behavior on a question nobody rehearsed — backed by a
robustness suite that passed at 100% before this recording."

---

## Part 4: The answer becomes the caption (45 seconds)

**[Screen: the empty description field on the PBI report, THEN run
13_publish_pbi cell 1 — the match review — then cell 2]**

"Everything the graph certifies flows back out. Watch this report's
description field — currently empty. AIVIA matches reports to metrics
by parsed lineage — exact, never fuzzy; where it isn't sure, it
declines and says why — and publishes the certified description onto
the report itself.

**[Refresh the report — the description is there.]**

The answer just became the report's caption, where every viewer sees
it. Every push is logged. The same motion publishes to Microsoft
Purview and Collibra."

---

## Part 5: The admin dashboard + close (45 seconds)

**[Screen: aivia_admin_telemetry_report, page through]**

"Admins get a Power BI report — generated and deployed automatically.
Pipeline health with a per-metric validation funnel. Knowledge
coverage, including the honest gaps: unassigned stewards are a work
queue in red, and setup-completeness is a table, not a memory — the
system knows which enrichments you haven't configured yet. Every
error cites the contract it violated, so support starts from the
cause, not the symptom. And agent telemetry: every conversation, WHO
made each decision — the deterministic engine or the language model —
with user feedback joined to it.

**[Final slide: the federation diagram — TMDL parser + ScriptDom → one
graph → the agent]**

AIVIA: a federation of native parsers, one per layer, stitched into
one certified knowledge graph — and a governed AI that answers from
it. Provably, or not at all. Available on Azure Marketplace."

---

## Recording checklist

- [ ] QA pass on Beats 4 and 5 against the live tenant FIRST (new
      surface; the robustness baseline predates the report layer)
- [ ] Fresh conversation (no leftover context on screen)
- [ ] Web app signed in as a real Entra user (identity visible = fine)
- [ ] Admin dashboard tab pre-loaded (page 1 green)
- [ ] Target PBI report's description field emptied BEFORE recording
      (Part 4's reveal depends on it)
- [ ] extract_views run once earlier in the week so the on-camera
      re-run shows a real CHANGED delta, not all-NEW
- [ ] Purview provisioned same-day if its screenshot is still wanted
- [ ] Capture stills: Basis-line answer, drift verdict, report blast
      radius, DAX description, the caption reveal, dashboard page 1+3
- [ ] Beat 7's outside question genuinely unrehearsed
