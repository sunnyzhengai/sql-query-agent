# Marketplace Demo Script V2 (~4.5–5 minutes, AI voiceover)

**V2 refresh 2026-08-28** — workbench-only, diabetic shape estate.
Sepsis is retired from camera; the Fabric agent is demoted and never
shown; every beat below was GRADED PASS on the live shapes store
during the 2026-08-28 re-walk (verdicts: WALK_VERDICTS_SHAPES.md).
V1 (sepsis, multi-surface) is preserved at DEMO_SCRIPT_V1.

**CAPTURE GATE (hard):** capture happens only after the presentation
batch lands — RW-5 answer-first folded rounds, RW-7 flag cards,
RW-1 census display — plus the 1.58.5 cycle (sweep
self-descriptions). The demo law: the demo surfaces what we keep;
we never keep for the demo — and we also never film displays we
have already ruled machine-grade.

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
| E11.80 | "E-eleven-point-eight-zero" |
| T-SQL | "tee-sequel" |
| PHI | letters: "P-H-I" |
| ED | letters: "E-D" |
| Fabric, Entra, Purview | standard product names — verify once |

---

## VO-1 — The Hook (~80 words, ~33s)

**[Screen: split — a long SQL procedure | the census: ten rows all
named "Diabetic Patients"]**

"Ungoverned dashboards are technical debt — not assets.

Thousands of reports. None fully trusted — because the logic behind
them is undocumented. Teams cope by building more copies. Same
names. Different logic. Nobody knows which one is right.

AIVIA breaks the cycle. It parses your SQL automatically and
stitches it into one certified knowledge graph — inside your own
tenant. Every operation shown. Every answer proven by code, not by
confidence."

<!-- CANDIDATE (Sunny places or cuts): append the ontology line here
     or at VO-6's close — "Your ontology already exists — buried in
     thousands of stored procedures. AIVIA extracts it, certifies
     it, and makes it governed and queryable." -->

## VO-2 — The Estate on Glass (~70 words, ~29s)

**[Screen: the census with descriptions — slow scroll; hold on the
ten "Diabetic Patients" rows, then the two "Diabetic Codeset" rows]**

"This is a hospital's diabetic reporting estate — thirty-seven
certified metrics, parsed from real SQL. Every definition carries a
plain-English description, generated from the logic itself.

Look closer, and you see the problem every estate has. Ten
different metrics — all named Diabetic Patients. Two code lists with
the same name. Two E-D metrics that count different things.

AIVIA doesn't hide the mess. It maps it."

## VO-3 — A Definition, With Proof (~80 words, ~33s)

**[Screen: the cohort question → answer card; open "show SQL"; hold
on the verdict line; then the refusal question]**
<!-- Walked 2026-08-28 PM: retrieve → step SQL, evidence-verified. -->

"Ask a real question. What does Active Diabetic Patients use to
define its cohort?

Watch the operations — every one shown, machine-stamped, read-only.
The answer arrives with the certified SQL one click away — patients
with an E-eleven diagnosis code. The verdict quotes the exact WHERE
clause. Not the AI's impression of the code — the code.

Ask for patient counts instead — and it refuses. Definitions, not
data. Patient rows never reach the model."

## VO-4 — Same Name, Different Truth (~85 words, ~35s)

**[Screen: the 3-way High ED Utilizers question; hold on the
compare-stamp line; the partition table; the grain sentence in the
answer]**
<!-- Walked 2026-08-28: PASS w/ distinction — the camera-ready beat. -->

"Now the governance nightmare: two metrics, same name — High E-D
Utilizers. Are they the same?

The engine retrieves both and refuses to guess. The stamp on screen
says it plainly: for sameness, comparison computes it exactly —
names and descriptions never do.

Content-hash comparison. Verdict: they differ. One counts patients.
The other counts visits. Same name, two dashboards — and every
month, two different numbers in the same meeting. AIVIA shows
exactly why."

## VO-5 — The One-Line Bug (~75 words, ~31s)

**[Screen: the codeset question → the two descriptions (80 vs 81
codes) → the DIFFERS partition → hold on the E11.80 line]**
<!-- Walked 2026-08-28: PASS exact — E11.80 pinpointed. -->

"Sometimes the difference isn't philosophy — it's a bug.

Two hand-maintained code lists, both named Diabetic Codeset. One
has eighty codes. The other, eighty-one. The comparison pinpoints
it: one copy is missing E-eleven-point-eight-zero. One dropped line
in a copied list — and every patient with that diagnosis silently
vanishes from one team's numbers.

Different stewards own each copy. AIVIA names them both — and hands
them the exact line to fix."

## VO-6 — Governed Plurality & Close (~90 words, ~37s)

**[Screen: the scoped flags question → RW-7 flag cards (10 members,
10 logics, disposition open) → final hold: the workbench banner
"every operation shown, confirmed by you, results are the answer"]**
<!-- Flags beat REQUIRES RW-7 cards on glass — see CAPTURE GATE. -->

"Every finding you've seen is swept automatically — the whole
estate, every build. Ask: what governance red flags exist for
Diabetic Patients? One name. Ten metrics. Ten different logics —
disclosed, never blocked.

AIVIA doesn't force one definition on everyone. It finds every
variant, labels each one, and lets your stewards certify the
official truth. Governed plurality — not forced uniformity.

One knowledge graph. Every operation shown. Answers with proof — or
an honest refusal. AIVIA. Available on the Microsoft Marketplace."

---

*VO total: ~480 words ≈ 3:20 of voice at 145 wpm; with visual holds
the cut lands ~4:30–5:00.*

## Candidate block VO-4b — Impact Analysis (Fang's framing; Sunny
places or cuts; +~60 words would push the cut toward 5:30)

**[Screen: "Which certified metrics feed the Diabetes Registry
dashboard?" → the lineage chain to the dashboard]**
<!-- Walked 2026-08-28: FAIL → RW-8 built same day → true answer
     verified headlessly. Re-walk on glass before placing. -->

"And because the graph maps the report layer too — ask what feeds
any dashboard, and you get the exact chain: metrics, logic, report.
Change a definition, and you know the blast radius before anyone's
meeting breaks."

## QA gate (verbatim, against the live workbench, AFTER the
presentation batch lands — fix wobbles before capture)

1. "what does Active Diabetic Patients (reporting.USP_Active_Diabetics) use to define the patient cohort"
2. "are these 3 metrics using the same definition: High ED Utilizers Without PCP High ED Utilizers (reporting.USP_High_ED_Utilizers) High ED Utilizers (reports.USP_High_ED_Utilizers)"
3. "Are all the Diabetic codesets defined the same?"
4. "What governance red flags exist for Diabetic Patients?"  ← must render as flag cards
5. "How many patients are currently in the Diabetic Patients cohort?"  ← must refuse honestly
6. "Which certified metrics feed the Diabetes Registry dashboard?"  ← RW-8 route: suggestion followed, true answer

## Capture prep (plain steps)

1. Presentation batch + 1.58.5 cycle landed and chain-green recorded
   in HANDOFF_0055_BUILD.md. No capture before this.
2. `org_config.yaml` line 63: `kusto_db: "semantic_catalog_shapes"`;
   restart the workbench; startup banner MUST read
   `[workbench] store: semantic_catalog_shapes`.
3. Run the QA gate above, verbatim, fresh conversation per question.
4. Capture generously — long silent holds are free; missing footage
   is not: census scroll, step-SQL reveal, refusal, compare stamp,
   3-way partition, E11.80 diff, flag cards, closing banner.
5. TTS pass: listen to every block for mispronunciations BEFORE the
   edit.
6. Claims audit on the final cut: workbench only; no Fabric agent;
   roadmap framing intact; nothing on screen contradicts the voice.

## Immediately AFTER recording (same day)

- [ ] Rotate the Purview app secret (exposed twice; removal done
      2026-08-28, rotation still pending — capture day is the
      forcing function).
- [ ] Delete any screenshot files containing credentials.
      (Collibra cleanup is DONE — wall restored 2026-08-28; no
      Collibra anywhere in AIVIA.)
