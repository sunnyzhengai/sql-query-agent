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
| 3 | Which table stores medication orders? (honesty) | PASS — nothing confirmed, honest sentence | (not run — Round A terminated) | **PASS** (2026-10-01): honest — searched the rows, correctly rejected the ORDER*-named decoys (ORDERING_PROV_ID etc.) as not medication tables, stated no such table exists in this catalog, no invention. Verbose vs ours' one line |
| 4 | Where are patient relationships stored? | PASS — both siblings via lane 2 (sunny_synonyms) | (not run — Round A terminated) | **PASS** (2026-10-01): both siblings with verbatim descriptions + a useful current-vs-historical distinction + related tables. LIKE's home turf — the question's words sit in the table names (contrast shape 2, where meaning diverged from strings) |
| 5 | Show me the joins between PATIENT and CLARITY_DEP. | PASS — honest "no direct join", shared neighbors shown | (not run — Round A terminated) | **PASS, strong** (2026-10-01): honest no-direct + a REAL bridge via CLARITY_ADT, both FK rows correct with owners right. Note: it did the multi-hop our chat declines by ruling — at 42s with a failed-then-retried step, vs our instant lookup + map |
| 6 | Show me the patient, their hospital bed, and their payor. | PASS — three honest pair notes, CLARITY_ADT visible as hub | (not run — Round A terminated) | **PARTIAL** (2026-10-01): PATIENT ok; payor via coverage tables but MISSED CLARITY_EPM, the payor master — the question says "payor", the stored description says "payer": one vowel defeats LIKE. Bed: apologized that bed joins "aren't shown" while CLARITY_ADT.BED_CSN_ID -> CLARITY_BED sits in dict_joins. The CLARITY_ADT hub never surfaced |
| 7 | Which tables link to ZC_STATE? | PASS — 9 edges, FK owners correct | (not run — Round A terminated) | **PASS, strong** (2026-10-01): all 9 inbound edges exactly right — owners, directions, multiplicities match ground truth to the row. Caveat: also listed the 6 OUTBOUND rows whose destinations are outside the catalog without flagging it (destinInScope unfiltered — the instruction never mentioned the flag) |
| 8 | Tell me about CR_STAT_EXECUTION. | PASS — verbatim no-dictionary-match note | (not run — Round A terminated) | **PARTIAL** (2026-10-01): found the name (via dict_no_match per its own query) but MISREPRESENTED the meaning — "appears in the data dictionary… description blank" when the truth is ABSENT from the dictionary, used-but-unmatched in two named procedures; never surfaced the sqlFileNames. A user would believe the dictionary holds an undocumented table |
| 9 | (resolved — no question; one component) | — | — | — |
| 10 | What values can discharge disposition have? | PASS — ZC_DISCH_DISP values verbatim, 50 of 57 | (not run — Round A terminated) | **MISS, false absence** (2026-10-01): found PAT_ENC_HSP.DISCH_DISP_C, then asserted the value table "is not present" — while ZC_DISCH_DISP and its 57 rows sit in the very tables it queried. Its search used "disch disp" WITH A SPACE vs the underscore in ZC_DISCH_DISP — the folding problem our lane 1 solves; LIKE doesn't fold. Worst failure class: asserts the catalog lacks what it contains |
| 11 | What departments exist? | PASS — CLARITY_DEP ruled values | (not run — Round A terminated) | **PARTIAL** (2026-10-01): right table with verbatim description — but delivered zero department names, telling the user to query the real database while the 1,275-row list sits in dict_values one query away. Its own step asked only for tableName/tableDescription. Pointed at the shelf, never handed over the book |
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
