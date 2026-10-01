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
  TERMINATED EARLY (ruled 2026-10-01) after two recorded misses: the
  failure is STRUCTURAL, not per-question — the agent searches the
  schema OF the catalog, never the catalog's rows; it has no concept
  of data-as-dictionary. Ten more questions would copy the same miss.
  (This structural gap is precisely what the product exists to fill.)
- **Round B** — lightly instructed: the instruction text recorded
  verbatim below before any Round B question runs (teaches HOW, never
  answers — the standing law).
- DIRECTION LAW: our chat is the ground truth and the acceptance gate;
  the Agent is the subject, never the validator.
- Ours column = the twelve-shape runs already passed (2026-09-30
  local, 2026-10-01 Fabric-backed).
- ROUND B FINDING (after shapes 1-2): the instruction BRIDGED the
  structural gap — the agent now queries the catalog's rows. The
  remaining difference is retrieval quality: SQL LIKE string-matching
  vs our semantic layers (embeddings + abstracts + values). Round B
  continues through all shapes — now informative.

## The scorecard

| # | question | ours | Agent round A | Agent round B |
|---|---|---|---|---|
| 1 | Which table has the patient's race? | PASS — PATIENT_RACE 0.80 + ZC_PATIENT_RACE 0.71 pre-selected | **MISS** (2026-10-01): "wasn't able to find any tables or columns… no matches for race-related fields" — despite tables literally named PATIENT_RACE / ZC_PATIENT_RACE | **HIT, partial** (2026-10-01): found PATIENT_RACE.PATIENT_RACE_C with the verbatim description (+2 related columns) — but MISSED ZC_PATIENT_RACE, the category table with the race values, which ours surfaced |
| 2 | Where can I find how many days a patient spent in the hospital? | PASS — F_IP_HSP_PAT_DAYS top table | **MISS** (2026-10-01): found no length-of-stay columns, then recited generic hospital-data-model advice — while F_IP_HSP_PAT_DAYS's stored description, a ROW in dict_tables, answers verbatim | **PARTIAL** (2026-10-01): proposed PAT_ENC_HSP admission/discharge + DATEDIFF (competent compute-it-yourself) — but MISSED F_IP_HSP_PAT_DAYS, the purpose-built patient-days table: its description says "census days"/"duration of stay" and the agent's SQL LIKE searched the literal phrase "length of stay". LIKE vs semantics, demonstrated |
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

## Round B instruction (verbatim — recorded 2026-10-01 BEFORE use,
pasted into the Agent by Sunny the same hour)

```
These six tables ARE a data dictionary — a catalog of an EMR database.
User questions are about the objects cataloged IN THE ROWS, never
about this lakehouse's own schema. Always answer by querying the rows.

- dict_tables: one row per cataloged table — tableName,
  tableDescription.
- dict_columns: one row per cataloged column — tableName, columnName,
  dataType, columnDescription, isPrimaryKey.
- dict_joins: the foreign-key relationships between cataloged tables —
  sourceTableName.sourceColumnName -> destinTableName.destinColumnName.
- dict_values: the category code lists — tableName, code, meaning.
- dict_no_match: objects used in source SQL but absent from the
  dictionary.
- Ignore every column whose name ends in Embedding — numeric arrays,
  not usable in SQL.

Method: match the user's words against names AND descriptions AND
meanings, case-insensitive and partial. Answer with the cataloged
object names and their stored descriptions verbatim. For questions
about joins, read dict_joins rows. If nothing matches, say so plainly
— and check dict_no_match before concluding an object is unknown.
```
