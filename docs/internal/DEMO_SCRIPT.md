# Marketplace Demo Script (~5 minutes)

**Canonical recording script** — Sunny's V1 narrative flow
(DEMO_SCRIPT_V1, 2026-08-16) with every claim verified against the
shipped product (gap analysis 2026-08-16). Problem → Ingestion → the
"Aha!" (drift + blast radius) → Write-back → Admin close.

**Tone:** fast, value-first; the architecture is SHOWN (Basis line,
computed verdicts), never narrated as history. Deviation from the
scripted wording is welcome — but run the QA gate below first: the
report-layer questions are newer than the robustness baseline.

---

## Tenant prep (run BEFORE recording day — plain steps)

1. Resume the capacity.
2. Update from Git; publish **sql-logic-env** with the current wheel
   (v1.11.0+); verify the version in any notebook's Cell 0.
3. Create the **graph_edges** OneLake shortcut in the Eventhouse
   (RESUME_CHECKLISTS has the click path, next to the existing two).
4. Seed the demo source database: create a **Fabric SQL database**,
   deploy the 28 synthetic procs into it, and set the extractor config
   to `source_type: "fabric_native"` pointing at its SQL endpoint.
   Run extract_views once end-to-end (this is ALSO the extractor's
   live-parity verification). Two days later, edit 2–3 procs
   trivially so the on-camera re-run shows a real CHANGED delta.
5. Demo semantic model: the ED Sepsis dashboard's model must EXECUTE
   the demo procs (EXEC partitions — same shape as the real Cook
   fixtures). Its displayName must match the semantic-model name
   (the publish matcher is lineage-exact on the name). Leave the
   report's description field EMPTY.
6. Set `semantic_models.source_type: "workspace"` (no git needed) and
   run 12 → 03 → 04 → 05 → 07 → 11.
7. **QA gate** — ask the live agent, verbatim, and confirm grounded
   answers: (a) the headline metric question; (b) the drift question
   phrased WITHOUT the literal step name; (c) "which dashboards are
   impacted by these?" after the drift verdict; (d) the DAX measure
   question. Fix anything that wobbles before scheduling the recording.
8. Admin dashboard tab pre-loaded; fresh chat conversation; sign in as
   a real Entra user.

---

## Opening: The Hook (30 seconds)

**[Screen: split — a 2,000-line SQL procedure | a Power BI dashboard]**

"Every hospital runs on two layers of hidden business logic: thousands
of lines of legacy SQL, and the undocumented DAX inside your Power BI
reports. When an executive asks *'how exactly is this compliance
metric calculated?'*, it takes days to answer. And when a generic AI
answers instead, it hallucinates.

Meet **AIVIA**. AIVIA parses both layers with each platform's own
native parser and stitches them into a single certified knowledge
graph that lives entirely inside your tenant. Every answer comes with
exact provenance — or it doesn't answer at all."

---

## Part 1: Turn-key Ingestion & Guardrails (45 seconds)

**[Screen: extract_views review cell — the NEW / CHANGED / DELETED
delta, e.g. "3 changed, 0 new"]**

"Setup is turn-key. Point AIVIA at your database — on-prem SQL Server
through a gateway, Azure SQL, or Fabric-native — and it discovers
your procedures and views itself. This is a re-run: it found only
what changed since last week, and it stops here for review before
anything is written. Nothing moves without your eyes on it.

**[Screen: 12_ingest_semantic_models output — reports, measures,
derived business names]**

Power BI is the same motion — read straight from the workspace, no
exports, no git setup required: which SQL feeds which report, every
DAX measure, and the business names your people actually use.

And a built-in PHI gate scans both SQL and DAX *before* anything
reaches an AI model, which runs against your own Azure OpenAI
endpoint. Your data never leaves your tenant."

---

## Part 2: Ask Anything, With Proof (2 minutes)

**[Screen: the AIVIA web chat]**

**[Ask: "How is our ED Sepsis Screening rate calculated?"]**

"Plain business language, ending with the live dashboard link. Two
things to notice. It answered to the business name — learned
automatically from your report estate. And the **Basis line** here:
a code-stamped record of exactly what was searched, read, and
computed. Not the AI's account of itself — the system's.

**[Ask: "Show me the underlying SQL"]** → the stored logic, on demand.

Now the multi-million-dollar governance problem: copy-paste drift.

**[Ask: "Are all definitions of our base population score consistent
across our procedures?"]**

**[Screen: the computed verdict — six procedures, five distinct
definitions, with a diff]**

Six procedures claiming the same calculation. Five different truths —
caught by content hashing, not an AI's impression. And because the
graph holds the report layer too:

**[Ask: "Which dashboards are impacted by these?"]**

That's the blast radius — parsed from the semantic models themselves,
never name-matching. When a definition is wrong, this is who's
affected; when you fix it, this is who to notify.

One more thing — what it WON'T do:

**[Ask: "How many sepsis patients did we have yesterday?"]**

Definitions, not patient data. It refuses instantly and says what it
can do. No tools consulted, nothing invented — that refusal is a
feature your compliance team will love."

---

## Part 2b: Governance Without the Bottleneck (30 seconds)

**[Screen: the admin telemetry page showing conversations + WHO-decided
+ feedback joined]**

"One more thing about how AIVIA treats governance. Certification here
**discloses — it never gates**: users get answers on day one, and the
answer always shows its certification status honestly. Meanwhile every
conversation is recorded — who asked, what was consulted, which
component decided, and how the user rated it.

That usage graph is the foundation of where AIVIA is going: a
**citizen-stewardship model**. Instead of a central steward team as
the bottleneck, the roadmap connects users to the definitions they
query and confirm — so trusted interpretations can coexist, anchored
to the people who rely on them, and the graph gets smarter with every
question your teams ask."

> SCRIPT RULE (verdict 2026-08-16): present tense stops at what ships
> (disclose-never-gate, per-turn telemetry, feedback joins — ADR 0021,
> gov_turn_events). Users-as-nodes / per-user certified definitions
> are ADR 0038, Accepted but BUILD-GATED on the access-control ADR —
> spoken ONLY as roadmap ("where AIVIA is going"). Do not move them
> into present tense until the interaction layer ships.

---

## Part 3: The Write-Back Loop & Admin Trust (1 minute)

**[Screen: the report's EMPTY description field, then 13_publish_pbi:
the match review, then the publish cell]**

"Governance shouldn't die in a silo. This report's description field
is empty. AIVIA matches reports to metrics by parsed lineage — exact,
never fuzzy; where it isn't certain it declines and says why — and
publishes the certified definition onto the report itself.

**[Refresh — the description is populated.]**

The answer just became the report's caption, visible to every viewer.
Every push is logged, and the same motion syncs to Microsoft Purview
and Collibra.

**[Screen: quick pan through aivia_admin_telemetry_report]**

Administrators see everything: pipeline health, validation funnels,
stewardship gaps as a work queue in red, setup-completeness as data,
and an audit log of every AI decision — which component decided,
with user feedback joined to it.

AIVIA: a federation of native parsers, one knowledge graph, and a
governed AI that answers with proof. Available on the Microsoft
Marketplace."

---

## Recording checklist

- [ ] Tenant prep steps 1–8 done (incl. the QA gate — non-negotiable)
- [ ] Fresh conversation; no leftover context on screen
- [ ] Report description field verified EMPTY right before Part 3
- [ ] Capture stills: Basis-line answer, drift verdict + diff, blast
      radius, the refusal, the caption reveal, dashboard pages 1+3
- [ ] Claims audit on the final cut: only the three shipped source
      profiles named; no "instantly"; no UI/node-map language beyond
      what was actually shown

## Immediately AFTER recording (same day — wall + credential cleanup)

- [ ] Remove the temporary work-Collibra block from org_config.yaml in
      the AIVIA tenant (sanctioned as demo-only, 2026-08-16; the wall
      rule resumes the moment recording ends)
- [ ] Rotate the Collibra apiuser password AND the Purview app secret —
      both were exposed in plaintext config + screenshot on 2026-08-16
- [ ] Delete the screenshot files containing the credentials
