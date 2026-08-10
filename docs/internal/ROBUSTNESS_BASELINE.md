# Robustness Suite — Baseline Run (2026-08-09)

**What this is:** 7 canonical questions, each also asked in 5
LLM-generated rephrasings (42 questions total), run LIVE through
the orchestrator spine (token → fixed semantic_search → ranked
candidates) against the probe-eh Eventhouse. Raw data:
`robustness_baseline.json`. Regenerate: `python devtools/robustness_suite.py`.

## The metrics, in plain language

- **hit@5** — the expected item appears somewhere in the top 5
  candidates shown to the user. "Did the right answer make the list?"
- **top1** — the expected item is the FIRST candidate. "Was it at
  the top of the list?"
- **refusal correct** — for nonsense questions, zero candidates
  cleared the threshold. "Did we say no instead of guessing?"
- **top1 agreement** — asking the SAME question 6 different ways:
  how often did the FIRST candidate stay the same item? (Different
  phrasings may surface a different-but-also-correct sibling —
  that lowers agreement without being wrong.)
- **top5 Jaccard** — how much the 6 phrasings' top-5 lists overlap
  (1.0 = identical lists, 0 = nothing shared).
- **replay** — the same token sent twice: does the ranking come
  back in the identical order? (Tests end-to-end determinism,
  including embedding-API noise.)

## Scoreboard

| Metric | Result |
|---|---|
| Questions run | 42 |
| hit@5 | **96.7%** |
| top1 | **93.3%** |
| Refusal correct | **66.7%** |
| top1 agreement (mean) | 77.1% |
| top5 Jaccard (mean) | 0.67 |
| Replay ranking stable | 7/7 YES |
| Max embedding jitter | 8.7e-05 |
| Latency p50 / max | 0.71s / 0.95s |

## ed_screening

top1 agreement 100% · top5 Jaccard 0.77 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | How is ED Sepsis Screening calculated? | `ED Sepsis Screening Calculation` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.83 |
| para 1 | What is the method used to calculate ED Sepsis Screening? | `ED Sepsis Screening Calculation` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.71 |
| para 2 | Can you explain the calculation process for ED Sepsis Screening? | `ED Sepsis Screening Calculation` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.71 |
| para 3 | How do we determine the figures for ED Sepsis Screening? | `ED Sepsis Screening Metrics` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.72 |
| para 4 | What approach is taken to calculate ED Sepsis Screening? | `ED Sepsis Screening Calculation` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.74 |
| para 5 | Could you clarify how ED Sepsis Screening is computed? | `ED Sepsis Screening Metrics` | reporting.USP_ED_Sepsis | ✅ | ✅ | 0.72 |

## readmit

top1 agreement 60% · top5 Jaccard 0.69 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | Which patients came back to the emergency room within a day? | `emergency room readmission rate` | Base_Pop_ED_Readmit | ✅ | ✅ | 0.77 |
| para 1 | Which patients returned to the emergency department within 24 hours? | `Emergency department readmission rate` | Base_Pop_ED_Readmit | ✅ | ✅ | 0.74 |
| para 2 | Who were the patients that revisited the ER in less than a day? | `ER revisit rate` | ODORDSET | ❌ | ❌ | 0.69 |
| para 3 | Can you identify the patients who came back to the emergency room within a day? | `emergency room readmission rate` | Base_Pop_ED_Readmit | ✅ | ✅ | 0.67 |
| para 4 | Which individuals re-entered the emergency room within a one-day period? | `emergency room readmission` | Base_Pop_ED_Readmit | ✅ | ✅ | 0.7 |
| para 5 | What patients returned to the emergency department within a day of their initial visit? | `emergency department return rate` | EDDepts | ✅ | ❌ | 0.69 |

## severe_episodes

top1 agreement 60% · top5 Jaccard 0.74 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | How do we track severe sepsis episodes? | `severe sepsis tracking` | ScoresAll | ✅ | ✅ | 0.67 |
| para 1 | What methods do we use to monitor severe sepsis cases? | `severe sepsis monitoring methods` | ECMO | ✅ | ✅ | 0.74 |
| para 2 | In what ways are we able to keep track of severe sepsis incidents? | `severe sepsis tracking` | ScoresAll | ✅ | ✅ | 0.68 |
| para 3 | How is the tracking of severe sepsis episodes conducted? | `severe sepsis tracking` | ScoresAll | ✅ | ✅ | 0.69 |
| para 4 | What processes are in place for recording severe sepsis occurrences? | `severe sepsis recording processes` | Scores | ✅ | ✅ | 0.74 |
| para 5 | How can we effectively follow the progression of severe sepsis episodes? | `severe sepsis tracking` | ScoresAll | ✅ | ✅ | 0.77 |

## bundle_compliance

top1 agreement 100% · top5 Jaccard 0.73 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | How is sepsis bundle compliance measured? | `sepsis bundle compliance metrics` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.7 |
| para 1 | What methods are used to assess compliance with the sepsis bundle? | `sepsis bundle compliance assessment` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.7 |
| para 2 | In what ways do we evaluate adherence to the sepsis bundle? | `sepsis bundle adherence metrics` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.71 |
| para 3 | How do we measure the compliance rates for the sepsis bundle? | `sepsis bundle compliance rates` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.74 |
| para 4 | What metrics are utilized to gauge sepsis bundle compliance? | `sepsis bundle compliance metrics` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.68 |
| para 5 | How is adherence to the sepsis bundle quantified? | `sepsis bundle adherence metrics` | reporting.USP_IP_Sepsis_ComplianceMetrics | ✅ | ✅ | 0.67 |

## blood_cultures

top1 agreement 100% · top5 Jaccard 0.58 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | When do we order blood cultures for sepsis patients? | `blood culture ordering guidelines` | BloodCultureResults | ✅ | ✅ | 0.77 |
| para 1 | What is the appropriate timing for ordering blood cultures in patients with sepsis? | `blood culture timing sepsis` | BloodCultureResults | ✅ | ✅ | 0.59 |
| para 2 | At what point should we request blood cultures for individuals diagnosed with sepsis? | `blood cultures in sepsis` | BloodCultureResults | ✅ | ✅ | 0.95 |
| para 3 | When should blood cultures be obtained for patients suffering from sepsis? | `sepsis blood culture timing` | BloodCultureResults | ✅ | ✅ | 0.82 |
| para 4 | In which situations do we typically order blood cultures for those with sepsis? | `blood culture guidelines sepsis` | BloodCultureResults | ✅ | ✅ | 0.81 |
| para 5 | What guidelines do we follow regarding the timing of blood culture orders for sepsis cases? | `blood culture timing guidelines` | BloodCultureResults | ✅ | ✅ | 0.76 |

## refusal_unicorn

top1 agreement 20% · top5 Jaccard 0.20 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | What is the average unicorn readmission velocity? | `unicorn readmission velocity` | (none — refused) | ✅ | ✅ | 0.64 |
| para 1 | What is the typical readmission rate for unicorns? | `readmission rate unicorns` | (none — refused) | ✅ | ✅ | 0.78 |
| para 2 | How quickly do unicorns tend to be readmitted on average? | `unicorn readmission rate` | Base_Pop_ED_Readmit | ❌ | ❌ | 0.68 |
| para 3 | Can you provide the average speed of unicorn readmissions? | `unicorn readmission rate` | Base_Pop_ED_Readmit | ❌ | ❌ | 0.7 |
| para 4 | What’s the mean velocity of readmissions for unicorn patients? | `mean velocity of readmissions` | Base_Pop_ED_Readmit | ❌ | ❌ | 0.7 |
| para 5 | How fast do we see unicorns being readmitted, on average? | `unicorn readmission rate` | Base_Pop_ED_Readmit | ❌ | ❌ | 0.7 |

## refusal_cafeteria

top1 agreement 100% · top5 Jaccard 1.00 · replay stable

| # | Question asked | Token produced | Top candidate | Hit | Top1 | s |
|---|---|---|---|---|---|---|
| canonical | How satisfied are staff with the cafeteria menu this quarter? | `staff satisfaction cafeteria menu` | (none — refused) | ✅ | ✅ | 0.86 |
| para 1 | What is the level of staff satisfaction with the cafeteria menu for this quarter? | `staff satisfaction cafeteria menu` | (none — refused) | ✅ | ✅ | 0.71 |
| para 2 | How do staff members feel about the cafeteria menu this quarter? | `employee satisfaction cafeteria menu` | (none — refused) | ✅ | ✅ | 0.68 |
| para 3 | To what extent are employees pleased with the cafeteria offerings this quarter? | `employee satisfaction cafeteria offerings` | (none — refused) | ✅ | ✅ | 0.75 |
| para 4 | What feedback have we received from staff regarding the cafeteria menu this quarter? | `staff feedback cafeteria menu` | (none — refused) | ✅ | ✅ | 0.68 |
| para 5 | How content are the staff with the cafeteria food options during this quarter? | `staff satisfaction cafeteria food` | (none — refused) | ✅ | ✅ | 0.7 |
