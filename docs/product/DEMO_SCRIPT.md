# Product Demo Script — 5 Minutes

**Target audience:** Microsoft Founders Hub reviewers, investors, enterprise prospects
**Recording environment:** Work Fabric (crop URLs, scrub org names in voiceover)
**Tone:** Confident, commercially sharp, problem-first

---

## Before Recording

**Setup checklist:**
- [ ] Fabric Data Agent open in browser (crop the URL bar)
- [ ] Agent instructions updated with latest version
- [ ] Graph tables loaded with latest ScriptDom-parsed data (all 4 folders)
- [ ] Architecture slide ready
- [ ] Knowledge graph visual ready (node/edge diagram or lineage view)
- [ ] www.aiviaapp.com open in another tab
- [ ] Screen recording tool ready (crop to just the agent chat window)
- [ ] Practice run completed

---

## Minute 0:00–1:00 — The Pain & The Breakthrough

**[SLIDE: The Problem — show a wall of SQL code, messy and intimidating]**

*Voiceover:*
"Every healthcare organization is sitting on millions of dollars of ungoverned business logic trapped inside thousands of legacy SQL scripts.

New analysts spend three weeks figuring out how a single metric is calculated. Executives sit in meetings staring at dashboards, wondering why three different reports show three different numbers. And data governance? It's a spreadsheet that nobody reads and everyone ignores.

The cost isn't just frustration — it's duplicated work, failed audits, and decisions made on numbers nobody trusts."

**[SLIDE: Architecture Diagram — clean, professional]**

*Voiceover:*
"We built AIVIA to solve this. AIVIA reads your existing SQL — stored procedures, views, scripts — and automatically extracts the business logic using Microsoft's own ScriptDom parser.

But here's what makes AIVIA different: we don't just parse code. We build an intelligent, multi-layer knowledge graph — a certified map of your organization's business logic. Business metrics at the top, calculation logic in the middle, source tables at the bottom. Every connection traced, every filter documented."

**[SHOW: Cell 6 output or screenshot — linger on 99% / 788 out of 790 for 4 full seconds]**

*Voiceover:*
"We tested this against 790 real enterprise stored procedures. Ninety-nine percent parsed. Zero errors. Twenty-four minutes."

*[Pause — let the number land]*

---

## Minute 1:00–3:00 — The Core Magic (Live Demo)

**[SWITCH TO: Fabric Data Agent chat window — cropped, no URLs visible]**

*Voiceover:*
"Let me show you what this means for an actual end user."

**Question 1: Business user question**

*Type in the agent:*
> How is the Census Dashboard calculated?

*Wait for response. Voiceover while it loads:*
"A business user asks a plain English question. No SQL knowledge required."

*When response appears:*
"The agent instantly explains what the metric measures, what business rules filter the data — census events only, valid patients, specific service areas — and traces the logic back to the source. All of this was extracted automatically from a stored procedure that nobody had documented."

**Question 2: Criteria deep-dive**

*Type in the agent:*
> What specific filters does it apply?

*Voiceover:*
"The user digs deeper. Every WHERE clause, every JOIN condition, translated into a business rule. This is the kind of detail that used to take a developer three days to reverse-engineer."

**[VISUAL BREAK: Flash the three-layer knowledge graph diagram for 3-4 seconds]**

*Voiceover:*
"Behind the scenes, the agent is traversing this knowledge graph — business metrics connected to calculation logic, connected to source tables. Every answer is traceable. Every metric is auditable."

**Question 3: A different metric**

*Type in the agent:*
> How is the ED Dashboard calculated?

*Voiceover:*
"This works across the entire organization's SQL library. Different procedure, different logic, same instant clarity."

---

## Minute 3:00–4:00 — Persona Flexibility

**Question 4: Developer view**

*Type in the agent:*
> Show me the technical details for the Census Dashboard

*Voiceover:*
"For developers and data engineers, the agent switches to technical mode — SQL fragments, source tables with data dictionary descriptions, the full transformation chain. Same knowledge graph, different lens."

**Question 5: Admin view**

*Type in the agent:*
> /coverage

*Voiceover:*
"Administrators manage the system through the same interface. How many metrics are documented, how many have stewards assigned, system health — all through natural language. One agent, three personas: business users, developers, and administrators."

---

## Minute 4:00–5:00 — Vision & Close

**[SLIDE: Roadmap — clean, three items only]**

*Voiceover:*
"What you just saw is the intelligence layer — the hardest technical problem. On the roadmap:

Automated metadata sync to Microsoft Purview and Power BI — so every report is self-documenting, updated automatically when the SQL changes.

A governance flywheel where every user question strengthens the knowledge base. The more people use it, the more complete and accurate it becomes.

And multi-dialect support — Oracle PL/SQL, Snowflake — using native parsers for each platform. We don't do text guessing. We use each database vendor's own parser for 100% accuracy."

**[SHOW: www.aiviaapp.com]**

*Voiceover:*
"We take a process that traditionally takes months of manual data cataloging and enterprise documentation, and we automate it down to minutes — entirely inside the customer's secure Microsoft Fabric tenant. No data ever leaves.

AIVIA is live, scalable, and ready for deployment. Learn more at aiviaapp.com."

*[Hold on website for 3 seconds — end]*

---

## Backup Questions (if doing a live demo)

| Question | What it demonstrates |
|---|---|
| "Which metrics use the PATIENT table?" | Reverse lineage — trace from table to metrics |
| "Who owns the Census Dashboard?" | Steward assignment |
| "What metrics are available?" | Full catalog via agent |
| "How do I set up automated refresh?" | Agent knows about itself |
| "/health" | System health check |
| "/errors" | Parse error transparency |

---

## Recording Tips

1. **Crop the browser** — show only the agent chat, no URL bar, no sidebar, no workspace name
2. **Linger on the 99% stat** — hold it on screen for at least 4 full seconds
3. **Type at a natural pace** — not too fast, not too slow. Viewers need to read what you type
4. **Pause 2-3 seconds** after each agent response before continuing voiceover
5. **Use the visual break** — flash the knowledge graph diagram between Questions 2 and 3
6. **End strong** — the last words the viewer hears should be "live, scalable, and ready for deployment"
7. **Keep it under 5 minutes** — respect the reviewer's time
8. **Record in a quiet room** with a good microphone
9. **Do a practice run** before the real recording — time it
10. **Don't mention your employer** — say "a healthcare organization" or "an enterprise customer"
