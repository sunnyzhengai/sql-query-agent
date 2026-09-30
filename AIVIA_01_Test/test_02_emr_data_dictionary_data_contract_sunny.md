HOW TO RUN (added by Claude at the L06 build, 2026-09-29)

Step 1 — rebuild the sheets once (folds ini/item into the column sheet,
builds the value-embeddings sidecar; ~14,476 new value embeddings,
under a cent, about a minute; everything else reuses):
    /opt/homebrew/bin/python3.11 AIVIA_01_Code/build_dictionary_sheets.py \
        AIVIA_01_Data/02_emr_data_dictionary \
        AIVIA_01_Data/02_emr_data_dictionary/02_sql_extraction.json
Without this step the chat still runs, but value search (shapes 10-12)
is disabled and says so at startup.

Step 2 — RETIRED (2026-09-30): the L06 chat is superseded — the chat is
its own phase now (03_chat_bot.md); graph_chat.py was removed at the
L04 split. The new chat command lands here (or in the 03 md) at the 03
build. The twelve shapes below move to
test_03_chat_bot_data_contract_sunny.md by Sunny's hand, shapes 5-7
reshaped per the 03 design's companion-edits note.

The test suites (Claude's, all green at build):
    /opt/homebrew/bin/python3.11 -m pytest AIVIA_01_Test/ -v

Shape 9 update (2026-09-29): the adjacency check ran — with the L08
date-dimension rule edges the 38-table graph is ONE component
(test-pinned: test_real_graph_structure_pins_the_corpus). There is no
natural no-path pair in this corpus; shape 8 is the gap case. Recorded
here per the shape's own instruction, no question committed.

A. Retrieval — does the embedding + acceptance band find the right rows?

1. Name hit. "Which table has the patient's race?"
Correct: PATIENT_RACE and ZC_PATIENT_RACE accepted as anchors, scores shown.

2. Description hit, no name words. "Where can I find how many days a patient spent in the hospital?"
The words "days spent in the hospital" appear nowhere in a table name — only in the F_IP_HSP_PAT_DAYS description. Correct: it's accepted via the description embedding. This is the test that the separate name/description embeddings ruling earns its keep.

3. Out-of-corpus honesty. "Which table stores medication orders?"
Nothing in these 38 tables covers it. Correct: zero accepted anchors; the top candidates listed with their visible scores below the band; no invented answer.

4. Sibling margin. "Where are patient relationships stored?"
PAT_RELATIONSHIP_LIST and PAT_RELATIONSHIP_LIST_HX will score close together. Correct: both surface with scores; the margin parameter decides, and whichever falls below still shows as a candidate — this is the "thresholds are never cliffs" test.

B. Traversal — does the subgraph answer hold up?

5. Two anchors, one path. "How do I join PATIENT to its department?"
Correct: a path from PATIENT to CLARITY_DEP where every hop cites a join-sheet row (source column → dest column, FOREIGN_KEY_NUM visible). No hop without an edge row.

6. Three-plus anchors, minimal connecting subgraph. "Show me the patient, their hospital bed, and their payor."
Anchors PATIENT, CLARITY_BED, CLARITY_EPM. Correct: the union of pairwise shortest paths — likely meeting through PAT_ENC_HSP / CLARITY_ADT — with shared intermediate tables appearing once, not per-pair.

7. Direction reported truthfully. "Which tables link to ZC_STATE?"
ZC_STATE has edges in both directions (6 as source, 9 as destination). Correct: pathfinding may walk edges either way, but the answer states each join in its stored direction (which side owns the foreign key).

C. Gaps — does the chat say what it doesn't know?

8. Used but not in the dictionary. "Tell me about CR_STAT_EXECUTION."
It appears in both census procedures but has no dictionary rows. Correct: the chat says exactly that — used in COOK_RPT_usp_PTA_CensusDashboard_PBI and COOK_RPT_usp_SF_CensusDashboard, no dictionary match — sourced from 02_no_dictionary_match.json. A fabricated description is a hard fail.

9. No connecting path. Ask for a subgraph joining two anchors that share no edges.
Caveat from the data: the join sheet is dense (F_SCHED_APPT alone has 735 edge rows), so the 38-table graph may be fully connected — in which case this shape has no natural pair and shape 8 is the gap case that exists in this corpus. Worth one adjacency check at build time before you commit a question to it; if connected, record that instead of forcing the case.

D. Category values — does the ruled-list mechanism hold?

10. ZC values verbatim. "What values can discharge disposition have?"
Correct: ZC_DISCH_DISP plus its rows from the value sheet, stored text verbatim.

11. Ruled CLARITY_ category.* "What departments exist?"
CLARITY_DEP is a category table only because your ruled row says DEPARTMENT_ID → DEPARTMENT_NAME. Correct: values returned. This tests the ruled list, which the ZC path never exercises.

12. The exclusion guard. "What are the category values of CLARITY_ADT?"
Correct: no values — CLARITY_ADT is ruled out as the event table, and the chat should say so rather than guessing a meaning column.

One shape with no data today

A composite-join question (multi-column FK, ordinal 1..n walked together) can't be tested — all 5,262 current rows are single-column joins. I'd note that in the file rather than write a dead test: the shape joins the suite when the first composite FK enters the corpus.

That's the full set — four risk families, twelve shapes, one recorded absence. If you adopt them, shapes 3, 8, and 12 are the ones I'd weight hardest: they're the honesty tests, and they're where a chat that "traverses" but hallucinates would pass everything else and still be wrong.
