# Brief_Gate_Number_Rebase — finish the M3 condition re-base in the two stale gate lines (FL7)

**Status: CLOSED** (built 2026-09-17; estate battery 21/21 green)

| field | content |
|---|---|
| class | fix — the answer key drifted from the ruled M3 measurement (twin 748 → store 1141, accepted at M3); two lines kept the old count and now disagree with the census in the same files |
| claims | ds.m3_condition_layer (batch CLOSED with the 1141 re-base) · FL7 RULED (Sunny "yes", 2026-09-17: correct the two stale lines to the measured numbers) |
| impacts (computed) | expected_m_gates.json line 203: "748/748 at M3, 754/754 at M5" → "1141/1141 at M3, 1147/1147 at M5" · GQL_Gates.md line 551: "total→754" → "total→1147". No test reads the coverage string (verified — only a docstring mention of the derived_column row); no registry, no served data, no export. Re-verify: test_ed_sepsis_dev_estate full battery |
| ambiguities | none — the numbers are arithmetic on ruled facts (1141 measured at M3, +6 IF predicates at M5) |
| debt declared | none |
| Sunny's approval | **"approve"** — 2026-09-17, after the FL7 ruling ("yes" on correcting the two stale lines to the measured numbers) |
| closing check | **BALANCED** — files changed == the three declared (the two stale lines corrected; this brief). test_ed_sepsis_dev_estate 21/21 green after the change |

## Files declared

    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json
    AIVIA_Test/GQL_Gates.md
    AIVIA_Design/briefs/Brief_Gate_Number_Rebase.md
