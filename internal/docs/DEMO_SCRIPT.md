# Marketplace Demo Script (~4.5–5 minutes, AI voiceover)

**Canonical recording script** — V1's four-part flow (simple,
value-driven, low cognitive load — Sunny's call 2026-08-16), written
for ElevenLabs-style TTS. The voice is generated per block; the screen
capture is silent; the video is edited TO the voice.

**Production workflow:**

1. Capture all screen footage SILENTLY, unhurried — latency and
   navigation get trimmed in edit. The QA gate below still applies:
   every answer on screen must be real.
2. Generate the VO one block at a time (VO-1 … VO-6) so a wording fix
   regenerates one block, not the track.
3. Edit visuals to the voice. Budgets assume ~145 wpm; if a visual
   needs longer, hold the shot in silence — never stretch the voice.

**TTS writing rules (keep when editing):**

- The voice NEVER speaks a raw identifier, filename, or table name —
  the screen shows them; the voice says the business phrase.
- Short sentences. Em-dashes and periods are the pacing controls.
- No filler ("as you can see", "let's take a look") — every sentence
  carries weight.

**Pronunciation table (configure in the TTS tool; listen to every
block once before editing):**

| Written | Speak as |
|---|---|
| AIVIA | "ay-VEE-uh" (lock one pronunciation, reuse everywhere) |
| DAX | the word "dax" (not letters) |
| T-SQL | "tee-sequel" |
| PHI | letters: "P-H-I" |
| ScriptDom | "script-dom" |
| Entra, Purview, Collibra, Fabric | standard product names — verify once |

---

## VO-1 — The Hook (~85 words, ~35s)
<!-- Rewritten 2026-08-17 (Sunny's critique): lead with the pain and the
     debt cycle, not the mechanism. "Duplicate dashboards" deliberately
     foreshadows the drift stunner in VO-4. -->

**[Screen: split — a 2,000-line SQL procedure | a sprawl of look-alike
dashboards]**

"Ungoverned dashboards are technical debt — not assets.

Thousands of reports. None fully trusted — because the logic behind
them is undocumented. Developers don't write plain-English
descriptions. Stewards can't read raw code. So the debt compounds —
and teams cope by building even more duplicate dashboards.

AIVIA breaks the cycle. It parses deep SQL and DAX automatically, and
stitches them into one certified knowledge graph — inside your own
tenant. Answers proven by code, not by confidence.

Stop accumulating debt. Turn hidden code into certified truth."

## VO-2 — Ingestion & Guardrails (~95 words, ~40s)

**[Screen: 030_ingest_sql_live's review cell — "3 changed, 0 new" — then a
quick cut to the semantic-model ingestion summary and the PHI gate
lines]**

"Setup is turn-key. Point AIVIA at your database — on-premises, Azure
SQL, or Fabric — and it discovers your procedures and views itself.
This re-run found only what changed, and it stops for your review
before anything is written.

Power BI is the same motion — straight from the workspace. Which SQL
feeds which report, every DAX measure, and the business names your
people actually use.

And before anything reaches an AI model, a built-in P-H-I gate scans
both layers. Everything runs against your own Azure OpenAI endpoint.
Your data never leaves your tenant."

## VO-3 — Ask Anything, With Proof (~90 words, ~37s)

**[Screen: the chat — the headline question; the answer with the
Basis line; the SQL follow-up]**

"Let's ask a real clinical analytics question. — How is our E-D sepsis
screening rate calculated?

Plain business language, ending with a live link to the dashboard.
Notice two things. It answered to the business name — learned
automatically from your report estate. And the Basis line, right here.
A deterministic, code-stamped record of exactly what was consulted.
Not the AI's account of itself — the system's.

Want the raw logic? Ask — and the certified SQL appears. Ask for
patient counts instead — and it refuses. Definitions, not data."

## VO-4 — Drift & Blast Radius (~75 words, ~31s)

**[Screen: the drift question; the computed verdict with the diff;
then the dashboards follow-up]**

"Now the multi-million-dollar governance nightmare: copy-paste drift.

Are all definitions of our base population score consistent? — Six
procedures claim the same calculation. AIVIA found five different
truths — through content hashing, not an AI's impression.

And because the graph maps the report layer too: which dashboards are
impacted? That's the exact blast radius across your report estate —
parsed from the semantic models themselves, never guessed from
names."

## VO-5 — The Write-Back Loop (~70 words, ~29s)

**[Screen: the empty description field → the publish match review →
publish → refresh: populated]**

"Governance shouldn't die in a silo. This report's description field
is empty. AIVIA matches reports to metrics by parsed lineage — exact,
never fuzzy. Where it isn't certain, it declines, and says why.

One action — and the certified definition is published onto the
report itself. The answer just became the report's live caption. Every
push is logged. The same metadata syncs to Microsoft Purview and
Collibra."

## VO-6 — Admin Trust & Close (~80 words, ~33s)

**[Screen: quick pan through the admin telemetry dashboard → final
slide: the federation diagram]**

"Finally — administrators see everything. Pipeline health. Validation
funnels. Missing stewardship tracked in red. And a full audit log of
every AI decision — who asked, what was consulted, which component
decided.

That usage record is the foundation of where AIVIA is going: citizen
stewardship — users connected to the definitions they query and trust,
so a central steward team is never the bottleneck.

AIVIA. A federation of native parsers, one knowledge graph, a governed
AI that answers with proof. Available now on the Microsoft
Marketplace."

> SCRIPT RULE (verdict 2026-08-16): present tense stops at what ships
> (disclose-never-gate, per-turn telemetry, feedback joins). Citizen
> stewardship (users-as-nodes, per-user certified definitions) is
> ADR 0038 — Accepted, BUILD-GATED on the access-control ADR — spoken
> ONLY as roadmap ("where AIVIA is going") until it ships.

---

*VO total: ~485 words ≈ 3:20 of voice at 145 wpm; with visual holds
the cut lands ~4:30–5:00.*

## Tenant prep (before capture day — plain steps)

1. Resume the capacity.
2. Update from Git; publish **sql-logic-env** (v1.11.0+); verify the
   version in any notebook's Cell 0.
3. `graph_edges` OneLake shortcut in the Eventhouse (if the wizard
   says the name exists, it's DONE — verify with a count query).
4. Seed the demo source: a **Fabric SQL database** with the 28
   synthetic procs; extractor `source_type: "fabric_native"`; run
   extract_views end-to-end (doubles as the live-parity verification).
   Days later, edit 2–3 procs so the captured re-run shows a real
   CHANGED delta.
5. Demo semantic model: must EXECUTE the demo procs (EXEC partitions);
   displayName must match the model name; report description field
   left EMPTY.
6. `semantic_models.source_type: "workspace"`; run (renumbered 1.22.0,
   export now AFTER descriptions): 060 → 300 → 400 → 500 → 600 → 700
   → 800.
7. **QA gate** — verbatim against the live agent: (a) the headline
   question; (b) the drift question WITHOUT the literal step name;
   (c) "which dashboards are impacted?" after the verdict; (d) the
   patient-count refusal. Fix wobbles before capture.

## Capture-day checklist

- [ ] Tenant prep 1–7 done (QA gate non-negotiable)
- [ ] Fresh conversation; description field verified EMPTY
- [ ] Capture generously — long silent holds are free; missing footage
      is not: Basis answer, SQL reveal, refusal, drift verdict + diff,
      blast radius, caption reveal, dashboard pan
- [ ] TTS pass: listen to every block for mispronunciations BEFORE the
      edit
- [ ] Claims audit on the final cut: three shipped source profiles
      only; roadmap framing intact in VO-6; nothing on screen
      contradicts the voice

## Immediately AFTER recording (same day — wall + credential cleanup)

- [ ] Remove the temporary work-Collibra block from org_config.yaml
      (sanctioned demo-only 2026-08-16; the wall resumes at wrap)
- [ ] Rotate the Collibra apiuser password AND the Purview app secret
      (both exposed in config + screenshot 2026-08-16)
- [ ] Delete the screenshot files containing the credentials
