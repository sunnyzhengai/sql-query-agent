# Marketplace Demo Script (~5.5 minutes, AI voiceover)

**Canonical recording script** — Sunny's V1 narrative flow, claims
verified against the shipped product (gap analysis 2026-08-16),
**written for AI text-to-speech** (decision 2026-08-16): the voice is
generated, the screen capture is silent, and the video is edited TO the
voice.

**Production workflow (in this order):**

1. Capture all screen footage SILENTLY, unhurried — agent latency and
   navigation time don't matter; they get trimmed in edit. The QA gate
   below still applies: every answer on screen must be real.
2. Generate the VO **one block at a time** (blocks below are numbered
   VO-1 … VO-9). Per-block generation lets you regenerate a single
   block after a wording fix without re-rendering the rest.
3. Edit visuals to the voice. Each block lists target words and
   seconds at ~145 wpm — if a visual needs longer, hold the shot in
   silence; never stretch the voice.

**TTS writing rules (applied throughout — keep when editing):**

- The voice NEVER speaks a raw identifier, filename, or table name —
  the screen shows them; the voice says the business phrase. (The
  product enforces this same rule on its own generated descriptions.)
- Short sentences. Em-dashes and periods are the pacing controls.
- No conversational filler ("as you can see", "let's take a look") —
  every sentence carries informational weight.
- Bold in VO blocks = words the edit should land a visual on, not an
  instruction to the TTS.

**Pronunciation table (configure in the TTS tool; spot-check each):**

| Written | Speak as |
|---|---|
| AIVIA | "ay-VEE-uh" (lock one pronunciation and reuse everywhere) |
| DAX | the word "dax" (not letters) |
| T-SQL | "tee-sequel" |
| TMDL | letters: "T-M-D-L" (avoid speaking it if possible) |
| ScriptDom | "script-dom" |
| Entra, Purview, Collibra, Fabric | standard product names — verify once |
| PHI | letters: "P-H-I" |

---

## Tenant prep (run BEFORE capture day — plain steps)

1. Resume the capacity.
2. Update from Git; publish **sql-logic-env** with the current wheel
   (v1.11.0+); verify the version in any notebook's Cell 0.
3. Create the **graph_edges** OneLake shortcut in the Eventhouse
   (RESUME_CHECKLISTS has the click path; if the wizard says the name
   already exists, it's DONE — verify with a count query).
4. Seed the demo source database: create a **Fabric SQL database**,
   deploy the 28 synthetic procs into it, and set the extractor config
   to `source_type: "fabric_native"` pointing at its SQL endpoint.
   Run extract_views once end-to-end (this is ALSO the extractor's
   live-parity verification). Two days later, edit 2–3 procs
   trivially so the captured re-run shows a real CHANGED delta.
5. Demo semantic model: the ED Sepsis dashboard's model must EXECUTE
   the demo procs (EXEC partitions — same shape as the real Cook
   fixtures). Its displayName must match the semantic-model name
   (the publish matcher is lineage-exact on the name). Leave the
   report's description field EMPTY.
6. `semantic_models.source_type: "workspace"` in org_config.yaml;
   run 12 → 03 → 04 → 05 → 06 → 07 → 11.
7. **QA gate** — ask the live agent, verbatim, and confirm grounded
   answers: (a) the headline metric question; (b) the drift question
   phrased WITHOUT the literal step name; (c) "which dashboards are
   impacted by these?" after the drift verdict; (d) a DAX measure
   question. Fix anything that wobbles before capture day.
8. Admin dashboard tab pre-loaded; fresh chat conversation; signed in
   as a real Entra user.

---

## VO-1 — The Hook (~75 words, ~30s)

**[Screen: split — a 2,000-line SQL procedure | a Power BI dashboard]**

"Every hospital runs on two layers of hidden business logic. Thousands
of lines of legacy SQL — and the undocumented DAX inside your Power BI
reports. When an executive asks how a compliance metric is calculated,
the answer takes days. When a generic AI answers instead, it
hallucinates.

Meet AIVIA. AIVIA parses both layers with each platform's own native
parser, and stitches them into one certified knowledge graph — inside
your tenant. Every answer carries exact provenance. Or it doesn't
answer at all."

## VO-2 — Turn-key Ingestion (~70 words, ~29s)

**[Screen: extract_views review cell — the CHANGED delta — then the
semantic-model ingestion summary]**

"Setup is turn-key. Point AIVIA at your database — on-premises, Azure
SQL, or Fabric — and it discovers your procedures and views itself.
This is a re-run. It found only what changed — and it stops for your
review before anything is written.

Power BI is the same motion. Straight from the workspace — no exports,
no git required. Which SQL feeds which report, every DAX measure, and
the business names your people actually use."

## VO-3 — Guardrails (~40 words, ~17s)

**[Screen: the PHI gate output lines, then 06: DEPLOYMENT READY]**

"Before anything reaches an AI model, a built-in P-H-I gate scans both
layers — SQL and DAX. Generation runs against your own Azure OpenAI
endpoint. Your data never leaves your tenant. And we never hold a
key."

## VO-4 — Ask, With Proof (~85 words, ~35s)

**[Screen: the chat — the headline question, answer, Basis line;
then the SQL follow-up]**

"Now ask. — How is our E-D sepsis screening rate calculated?

Plain business language — ending with the live dashboard link. Notice
two things. It answered to the business name, learned automatically
from your report estate. And the Basis line — a code-stamped record of
exactly what was searched, what was read, and what was computed. Not
the AI's account of itself. The system's.

Want the raw logic? Ask — and the certified SQL appears, on demand."

## VO-5 — The Drift Stunner (~75 words, ~31s)

**[Screen: the drift question, the computed verdict, the diff]**

"Here is the multi-million-dollar governance problem: copy-paste
drift.

Are all definitions of our base population score consistent? — Six
procedures claim the same calculation. AIVIA found five different
truths. Caught by content hashing — not by an AI's impression.

And because the graph holds the report layer too — one more question:
which dashboards are impacted? That's the blast radius. Parsed from
the semantic models themselves. Never guessed from names."

## VO-6 — It Knows What It Doesn't Know (~40 words, ~17s)

**[Screen: the patient-count question and the refusal]**

"One more thing — what it won't do. Ask for patient counts, and it
refuses. Instantly. Definitions, not data. No tools consulted, nothing
invented — and your compliance team will notice the difference."

## VO-7 — Governance Without the Bottleneck (~80 words, ~33s)

**[Screen: admin telemetry — conversations, WHO-decided, feedback]**

"Certification in AIVIA discloses — it never gates. Users get answers
on day one, and every answer shows its certification status honestly.
Meanwhile, every conversation is recorded: who asked, what was
consulted, which component decided, and how the user rated it.

That usage graph is the foundation of where AIVIA is going — citizen
stewardship. Instead of a central steward team as the bottleneck, the
roadmap connects users to the definitions they query and trust. The
graph gets smarter with every question."

> SCRIPT RULE (verdict 2026-08-16): present tense stops at what ships
> (disclose-never-gate, per-turn telemetry, feedback joins — ADR 0021,
> gov_turn_events). Users-as-nodes / per-user certified definitions
> are ADR 0038, Accepted but BUILD-GATED on the access-control ADR —
> spoken ONLY as roadmap ("where AIVIA is going"). Do not move them
> into present tense until the interaction layer ships.

## VO-8 — The Write-Back Loop (~65 words, ~27s)

**[Screen: empty description field → publish match review → publish →
refresh: populated]**

"Governance shouldn't die in a silo. This report's description field
is empty. AIVIA matches reports to metrics by parsed lineage — exact,
never fuzzy. Where it isn't certain, it declines, and says why.

One action — and the certified definition is published onto the report
itself. The answer just became the caption. Every push is logged. The
same motion syncs to Microsoft Purview and Collibra."

## VO-9 — Admin Close (~55 words, ~23s)

**[Screen: quick pan through the admin dashboard → final slide: the
federation diagram]**

"Administrators see everything. Pipeline health. Validation funnels.
Stewardship gaps as a work queue — in red. And an audit log of every
AI decision.

AIVIA. A federation of native parsers — one knowledge graph — and a
governed AI that answers with proof. Available now, on the Microsoft
Marketplace."

---

*VO total: ~585 words ≈ 4:05 of voice at 145 wpm; with visual holds
and micro-pauses the cut lands ~5:30.*

## Capture-day checklist

- [ ] Tenant prep steps 1–8 done (incl. the QA gate — non-negotiable)
- [ ] Fresh conversation; no leftover context on screen
- [ ] Report description field verified EMPTY right before the
      write-back capture
- [ ] Capture generously: Basis-line answer, drift verdict + diff,
      blast radius, the refusal, the caption reveal, dashboard pages —
      long silent holds are free; missing footage is not
- [ ] Claims audit on the final cut: only the three shipped source
      profiles named; roadmap framing intact in VO-7; nothing on
      screen contradicts the voice
- [ ] TTS pass: listen to every block once for mispronunciations
      (identifiers, product names) BEFORE the edit

## Immediately AFTER recording (same day — wall + credential cleanup)

- [ ] Remove the temporary work-Collibra block from org_config.yaml in
      the AIVIA tenant (sanctioned as demo-only, 2026-08-16; the wall
      rule resumes the moment recording ends)
- [ ] Rotate the Collibra apiuser password AND the Purview app secret —
      both were exposed in plaintext config + screenshot on 2026-08-16
- [ ] Delete the screenshot files containing the credentials
