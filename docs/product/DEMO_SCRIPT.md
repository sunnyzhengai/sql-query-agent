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

## Minute 0:00–1:30 — The Problem & The Breakthrough

**[SLIDE 1: The Problem — show a sprawling list of report names, or a cluttered BI portal]**

*Voiceover:*
"Every healthcare organization is sitting on millions of dollars of ungoverned technical debt — that can be turned into their strongest foundation for self-service analytics.

Thousands of SQL-based reports are the hidden treasure of business logic definitions. These reports were requested by clinicians based on real clinical needs. They were built by highly skilled BI developers. They were validated and put into production."

*[Delivery cue: Shift tone to highlight the friction]*

"But here's the problem: these thousands of reports are not governed. There is no visibility into the logic behind each report name. Some are outdated. Some are conflicting duplicates of the same metric with different numbers.

So when a clinician needs to make a decision, they search through different BI tools, staring at multiple report names and the different numbers in them — unable to know which one to trust. Their cognitive load skyrockets.

And what do they do? They submit yet another request to create a new report they can trust. That process takes weeks, sometimes months. Clinicians end up frustrated, and further distrust the Analytics team's products."

*[Delivery cue: Pause briefly, then deliver firmly]*

"This is the cycle we break."

**[SLIDE 2: Architecture Diagram — clean, professional]**

*Voiceover:*
"AIVIA takes those thousands of existing reports — the ones your organization already invested in — and automatically extracts the business logic from the SQL behind them. Using Microsoft's own ScriptDom parser, the same engine that powers SQL Server Management Studio.

But we don't just parse code. We build an intelligent, multi-layer knowledge graph — a certified map of your organization's business logic. Business metrics at the top, calculation logic in the middle, source tables at the bottom. Every connection traced, every filter documented. Every report finally visible and understood."

**[SLIDE 3: ScriptDom results — linger on 99% parse rate for 4 full seconds]**

*Voiceover:*
"We tested this against over 1,300 real enterprise SQL sources — stored procedures and views. Ninety-nine percent parsed. Zero errors."

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
