# Demo Video Script (5 minutes)

**Target audience:** Microsoft Marketplace reviewers, prospective customers
**Tone:** Professional, concise, focused on value — not technical internals
**Refreshed 2026-08-09** for business names, report links, and honest
governance — every question below passed live QA on 2026-08-08 (6/6).
Ask questions EXACTLY as written; they are the tested set.

---

## Opening (30 seconds)

**[Screen: Fabric workspace showing the SQL Intelligence Agent]**

"Every health system has hundreds of SQL stored procedures powering their
reports. The business logic inside them — the filters, the clinical
criteria, the compliance calculations — is undocumented. When an analyst
asks 'How is this metric calculated?', the answer takes days.

The SQL Intelligence Agent solves this automatically. It reads your SQL,
extracts the business logic, and lets anyone ask questions in plain
English — using the names the business actually uses."

---

## Part 1: Show the Problem (30 seconds)

**[Screen: Open USP_Severe_Sepsis SQL — scroll through it]**

"Here's a real example — a sepsis compliance procedure. Thousands of
lines of T-SQL, dozens of temp tables, complex clinical criteria. No one
has time to read this. No one documents it. And the business doesn't
even call it 'USP_Severe_Sepsis' — they call it the severe sepsis
report."

---

## Part 2: Run the Pipeline (45 seconds)

**[Screen: 01_install output → 02_parse output → 06_validate output]**

"Setup is one notebook. The pipeline parses every SQL file with
Microsoft's own ScriptDom parser — 28 of 28 files, zero errors — scans
for hardcoded PHI before anything reaches an AI model, builds a
three-layer knowledge graph, and generates business descriptions for
every calculation step using YOUR Azure OpenAI endpoint. Your SQL never
leaves your tenant."

**[Show 06_validate: DEPLOYMENT READY, 100% parse rate]**

---

## Part 3: Ask the Agent (2.5 minutes — the heart)

**[Screen: the published SQL Intelligence Agent chat]**

### Beat 1 — the headline (the whole product in one answer)

**[Type: `How is ED Sepsis Screening calculated?`]**

"I asked by the BUSINESS name — no proc names. The agent resolves it to
the certified procedure, and answers with the actual calculation steps:
the patient population, the screening criteria, the exclusions — every
claim traced to certified logic, not AI guesswork.

And notice the last line: 'Used in: ED Sepsis Screening Dashboard' —
with a link."

**[Open the report link — the dashboard appears]**

"From question to certified answer to the live report. That loop
normally takes a week of asking around."

### Beat 2 — the portfolio

**[Type: `What sepsis metrics do we have?`]**

"All 28 metrics, as business names with their technical identity beside
them. Two departments define ED Sepsis differently? Both are here,
clearly labeled — operational and regulatory — nothing silently merged."

### Beat 3 — impact analysis

**[Type: `Which metrics read from the HOSPITAL_ENCOUNTERS table?`]**

"Reverse lineage: if this table changes, these 13 metrics are affected —
computed from the FULL dependency chain, however deep the SQL nesting
goes. This completeness is precomputed at build time, not improvised by
the AI."

### Beat 4 — honesty (the differentiator)

**[Type: `How is the metric FAKE_METRIC_XYZ calculated?`]**

"I asked about a metric that doesn't exist. The agent refuses — it will
not invent an answer. Every response is grounded in the certified
knowledge graph, or it says so."

**[Type: `Who owns ED Sepsis Screening?`]**

"And when governance has a gap, it says that too: no steward assigned
yet. Honest disclosure over confident guessing — in healthcare, that's
the whole point."

---

## Part 4: The Value (30 seconds)

**[Screen: split view — raw SQL left, agent answer right]**

"What took a developer hours of reading SQL now takes anyone ten
seconds — in their own vocabulary, with named accountability, linked to
the reports they already use. Your undocumented SQL library becomes a
governed, searchable knowledge base — automatically."

---

## Closing (30 seconds)

**[Screen: workspace overview]**

"The SQL Intelligence Agent runs entirely inside your Microsoft Fabric
workspace, on your capacity, with your Azure OpenAI endpoint. Your SQL,
your data, your tenant — nothing ever reaches us.

Available now on the Microsoft Marketplace."

**[End screen: AIVIA — product name, aiviaapp.com, contact email]**

---

## Recording Notes

- **Use the PUBLISHED agents, not the test pane** (links left-click
  there; verify once before recording — fallback: open in new tab,
  looks fine on video)
- Ask questions verbatim from this script — this exact set is QA-passed
  (2026-08-08); do NOT improvise count questions ("how many...") on
  camera
- Clear chat before each beat so answers are clean and un-contaminated
- Resolution 1920x1080; clean browser profile; no personal bookmarks
- All data on screen is anonymized (corpus) or synthetic-footed
  (dashboard) — say so if a reviewer could wonder
- Pause 2–3 s after each answer; voiceover recorded separately
- Target 4–5 minutes; cut ruthlessly
