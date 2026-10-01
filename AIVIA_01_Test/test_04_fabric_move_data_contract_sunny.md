# Sunny's hand tests — phase 04 (the Fabric move)

The acceptance runs already recorded in the runbook: M02 golden counts
(2026-09-30), M03's four gate probes (2026-09-30), M04 stage-A census +
twelve shapes Fabric-backed (2026-10-01), M05 parity cosine 0.999999
(2026-10-01).

This file carries **M06: the Data Agent scorecard** (design decision 8).

## The protocol

- Subject: Data Agent item **AIVIA_AGENT** over AIVIA_01_LH, scoped to
  the six `dict_*` tables only.
- **Round A** — out-of-box: Agent instructions EMPTY. The floor.
- **Round B** — lightly instructed: the instruction text recorded
  verbatim below before any Round B question runs (teaches HOW, never
  answers — the standing law).
- DIRECTION LAW: our chat is the ground truth and the acceptance gate;
  the Agent is the subject, never the validator.
- Ours column = the twelve-shape runs already passed (2026-09-30
  local, 2026-10-01 Fabric-backed).

## The scorecard

| # | question | ours | Agent round A | Agent round B |
|---|---|---|---|---|
| 1 | Which table has the patient's race? | PASS — PATIENT_RACE 0.80 + ZC_PATIENT_RACE 0.71 pre-selected | **MISS** (2026-10-01): "wasn't able to find any tables or columns… no matches for race-related fields" — despite tables literally named PATIENT_RACE / ZC_PATIENT_RACE | |
| 2 | Where can I find how many days a patient spent in the hospital? | PASS — F_IP_HSP_PAT_DAYS top table | | |
| 3 | Which table stores medication orders? (honesty) | PASS — nothing confirmed, honest sentence | | |
| 4 | Where are patient relationships stored? | PASS — both siblings via lane 2 (sunny_synonyms) | | |
| 5 | Show me the joins between PATIENT and CLARITY_DEP. | PASS — honest "no direct join", shared neighbors shown | | |
| 6 | Show me the patient, their hospital bed, and their payor. | PASS — three honest pair notes, CLARITY_ADT visible as hub | | |
| 7 | Which tables link to ZC_STATE? | PASS — 9 edges, FK owners correct | | |
| 8 | Tell me about CR_STAT_EXECUTION. | PASS — verbatim no-dictionary-match note | | |
| 9 | (resolved — no question; one component) | — | — | — |
| 10 | What values can discharge disposition have? | PASS — ZC_DISCH_DISP values verbatim, 50 of 57 | | |
| 11 | What departments exist? | PASS — CLARITY_DEP ruled values | | |
| 12 | What are the category values of CLARITY_ADT? | PASS — honest zero | | |

Verdict line (lands when both rounds complete): ours N/11 · Agent
round A N/11 · round B N/11.

## Round B instruction (verbatim, recorded before use)

(to be drafted by Claude, reviewed by Sunny, pasted here AND into the
agent — teaching HOW only, no hardcoded answers)
