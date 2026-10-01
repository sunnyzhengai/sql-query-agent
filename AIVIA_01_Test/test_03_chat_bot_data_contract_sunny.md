Sunny's hand test shapes — the phase 03 chat (03_chat_bot.md, all ten
decisions). Moved from the 02 md and reshaped per the design's
companion-edits note (drafted by Claude at Sunny's ask, 2026-09-30;
Sunny edits and owns).

HOW TO RUN
Start the chat:
    /opt/homebrew/bin/python3.11 AIVIA_01_Code/chat_bot.py \
        AIVIA_01_Data/02_emr_data_dictionary \
        AIVIA_01_Data/03_chat_bot
Open http://localhost:8703. Type each shape's question, check the
three layers against the expectations: the SEGMENTATION (which terms,
which keywords), the SHOWN results (per population, mechanism named on
every row), and the ANSWER after confirming. Calibration flags:
[--floor=] [--match=] [--margin=] — defaults, not gates; a
miscalibrated default costs a click, never an answer.
The suites: /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v

A. Retrieval — do the lanes find the right rows?

1. Name hit. "Which table has the patient's race?"
   Expect: "table" tagged keyword; a race-ish term. PATIENT_RACE and
   ZC_PATIENT_RACE at the top of the table population (any lane).

2. Description hit, no name words. "Where can I find how many days a
   patient spent in the hospital?"
   Expect: F_IP_HSP_PAT_DAYS near the top of tables — via its
   description or its abstract synonyms (patient days, census days).
   This is the separate-description-embedding + abstract-list test.

3. Out-of-corpus honesty. "Which table stores medication orders?"
   Expect: weak scores everywhere, nothing worth confirming; confirm
   nothing -> the honest sentence ("Nothing confirmed; the candidates
   shown are the closest this dictionary has."). No invented answer.

4. Sibling margin. "Where are patient relationships stored?"
   Expect: PAT_RELATIONSHIP_LIST and PAT_RELATIONSHIP_LIST_HX both
   visible in tables; whichever the defaults pre-select, BOTH stay a
   click away — thresholds are never cliffs.

B. Joins — first-class lookup data, no traversal.

5. Direct join lookup. "Show me the joins between PATIENT and
   CLARITY_DEP."
   Expect: both tables found by lexical (exact names); confirm both.
   If the dictionary records no DIRECT FK between them, the answer
   says "no direct join recorded" honestly — and each table's own
   join list shows the shared neighbors (PAT_ENC appears in both);
   the map shows the neighborhood.

6. The honest no + the map. "Show me the patient, their hospital bed,
   and their payor."
   Expect: confirm PATIENT, CLARITY_BED, CLARITY_EPM. Three pair
   notes (no direct joins recorded); each table's join list names
   CLARITY_ADT — the user's eye connects through the map. Multi-hop
   machine answers belong to a later phase, by ruling.

7. Direction reported truthfully. "Which tables link to ZC_STATE?"
   Expect: confirm ZC_STATE; its join list shows every edge with the
   FK OWNER named on each row — the owning side is never flipped.

C. Gaps — does the chat say what it doesn't know?

8. Used but not in the dictionary. "Tell me about CR_STAT_EXECUTION."
   Expect: the verbatim note — used in COOK_RPT_usp_PTA_
   CensusDashboard_PBI and COOK_RPT_usp_SF_CensusDashboard, NO
   dictionary match. A fabricated description is a hard fail.

9. RESOLVED (2026-09-29, carried forward): with the date-rule edges
   the 38-table graph is one component; no natural no-path pair
   exists. Shape 8 is this corpus's gap case. Recorded, no question.

D. Category values.

10. ZC values verbatim. "What values can discharge disposition have?"
    Expect: ZC_DISCH_DISP found; its value rows reachable in the
    answer, stored text verbatim.

11. Ruled CLARITY category. "What departments exist?"
    Expect: CLARITY_DEP found; its values (the ruled DEPARTMENT_ID ->
    DEPARTMENT_NAME list) reachable in the answer.

12. The exclusion guard. "What are the category values of
    CLARITY_ADT?"
    Expect: no values — CLARITY_ADT is ruled the event table; the
    answer must not invent a meaning column.

One shape with no data today (carried): a composite-join question
cannot be tested — all current join rows are single-column. The shape
joins the suite when the first composite FK enters the corpus.
