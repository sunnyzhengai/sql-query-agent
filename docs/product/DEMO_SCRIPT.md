# Product Demo Script — 5 Minutes

**Target audience:** Microsoft Founders Hub reviewers, potential investors, enterprise prospects
**Recording environment:** Work Fabric (crop URLs, scrub org names in voiceover)
**Tone:** Confident, concise, problem-focused

---

## Before Recording

**Setup checklist:**
- [ ] Fabric Data Agent open in browser (crop the URL bar)
- [ ] Agent instructions updated with latest version
- [ ] Graph tables loaded with latest ScriptDom-parsed data
- [ ] Architecture slide ready (screenshot or PDF)
- [ ] www.aiviaapp.com open in another tab
- [ ] Screen recording tool ready (crop to just the agent chat window)

**Voiceover tips:**
- Say "a healthcare organization" not your employer's name
- Say "a reporting stored procedure" not specific proc names in voiceover
- The agent's text responses are safe to show — they're business logic descriptions
- Don't show the workspace name or lakehouse sidebar

---

## Minute 0:00–1:00 — The Problem & Architecture

**[SLIDE: The Problem]**

*Voiceover:*
"Every healthcare organization has hundreds — sometimes thousands — of SQL stored procedures that power their reports. Inside each one is critical business logic: how metrics are calculated, what filters apply, which tables are used.

But nobody documents them. New analysts spend weeks reverse-engineering queries. Three people run the same metric and get three different numbers. And governance? It's a spreadsheet nobody reads.

We built AIVIA to solve this."

**[SLIDE: Architecture Diagram]**

*Voiceover:*
"AIVIA uses Microsoft's own ScriptDom parser — the same engine that powers SQL Server Management Studio — to parse every stored procedure with 99% accuracy. It builds a three-layer knowledge graph: business metrics at the top, calculation logic in the middle, source tables at the bottom. All stored in Fabric Delta tables.

Then a Fabric Data Agent, grounded in this graph, lets anyone ask questions in plain English."

**[SHOW: Cell 6 output screenshot showing 99% parse rate, or the number 788/790]**

*Voiceover:*
"We tested this against 790 real enterprise stored procedures. 99% parsed with zero errors. In 24 minutes."

---

## Minute 1:00–3:00 — The Core Magic (Live Demo)

**[SWITCH TO: Fabric Data Agent chat window]**

*Voiceover:*
"Let me show you what this looks like for an end user."

**Question 1: Business user question**

*Type in the agent:*
> How is the Census Dashboard calculated?

*Wait for response. Voiceover while it loads:*
"The user asks a plain English question. The agent traverses the knowledge graph, reads the SQL logic, and translates it into business language."

*When response appears, read the key points:*
"It tells us exactly what the metric measures, what filters are applied — census events only, valid patients, specific service areas — and which data sources it uses. All extracted automatically from the stored procedure."

**Question 2: Criteria deep-dive**

*Type in the agent:*
> What filters does it apply?

*Voiceover:*
"The user can dig deeper. Every filter condition from the SQL is translated into a business rule. No SQL knowledge required."

**Question 3: A different metric**

*Type in the agent:*
> How is the ED Dashboard calculated?

*Voiceover:*
"This works for any metric in the system. Different proc, different logic, same experience."

---

## Minute 3:00–4:00 — Persona Flexibility

**Question 4: Developer view**

*Type in the agent:*
> Show me the technical details for the Census Dashboard

*Voiceover:*
"For developers who need the full picture, the agent switches to technical mode — showing SQL fragments, source tables with descriptions, and the transformation chain."

**Question 5: Admin view**

*Type in the agent:*
> /coverage

*Voiceover:*
"Administrators get system health through the same interface. How many metrics are in the system, how many have stewards assigned, how many have descriptions. One agent, multiple personas — business users, developers, and admins."

---

## Minute 4:00–5:00 — Roadmap & Close

**[SLIDE: Roadmap]**

*Voiceover:*
"What you just saw is the core intelligence layer — extracting business logic and making it queryable. On the roadmap:

First, automated metadata sync to Microsoft Purview and Power BI — so report descriptions are always up to date.

Second, a governance flywheel where every user question strengthens the knowledge base. High-demand metrics get promoted to dashboards. Unknown questions trigger steward review.

Third, expanding beyond T-SQL to support Oracle PL/SQL and Snowflake — using native parsers for each dialect."

**[SHOW: www.aiviaapp.com in browser]**

*Voiceover:*
"AIVIA is built entirely on Microsoft Fabric. It runs in the customer's own tenant — no data ever leaves. We're currently in the Microsoft for Startups Founders Hub program, building toward a Marketplace launch.

Learn more at aiviaapp.com. Thank you."

---

## Backup Questions (if doing a live demo with Q&A)

If someone asks follow-up questions, these are strong ones to show:

| Question | What it demonstrates |
|---|---|
| "Which metrics use the PATIENT table?" | Reverse lineage — trace from table to metrics |
| "Who owns the Census Dashboard?" | Steward assignment (if populated) |
| "What metrics are available?" | Full catalog browsable via agent |
| "How do I set up automated refresh?" | Agent knows about itself (self-service support) |
| "/health" | System health check via admin command |

---

## Recording Tips

1. **Crop the browser** to show only the agent chat — no URL bar, no sidebar
2. **Use a clean browser** with no bookmarks or tabs visible
3. **Type slowly** so viewers can read what you're typing
4. **Pause 2-3 seconds** after each agent response before moving on
5. **Don't rush** — 5 minutes is plenty for 5 questions + slides
6. **Record in a quiet room** with a good microphone
7. **Do a practice run** before the real recording
