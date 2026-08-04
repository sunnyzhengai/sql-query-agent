# Delta vs. Graph Rematch — Scorecard & Protocol

**Purpose:** repeatable protocol for comparing the two agent architectures on
the same certified corpus. Round 1 (2026-07) was contaminated: the graph side
ran on an impoverished structure (case-split nodes, empty dimension layer,
floating column nodes) against a hand-curated Delta table. Round 2 runs on a
count-verified, contract-certified graph.

**Hypothesis under test** (Sunny, 2026-08-02): SQL is set theory and LLMs get
"creative" transforming natural language into it, while graph traversal is
semantically closer to natural language — given a quality graph structure and
good grounding rules, NL-to-traversal should be easier and more accurate.

## Contestants

| | Agent A — "Delta Agent" | Agent B — "Graph Agent" |
|---|---|---|
| Source | `output_metric_logic` (+ graph tables) in the Lakehouse | The Graph Model (LPG) |
| Query language | NL2SQL | NL2GQL |
| Instructions | `notebooks/delta_agent_instructions.md` | `notebooks/graph_agent_instructions.md` |

## Pre-flight (every round)

- [ ] Pipeline 01→06 ran green (postcondition gates passed)
- [ ] Graph Model re-**Load**ed after the pipeline run (the LPG is a snapshot!)
- [ ] Count parity verified in a queryset (one query per run; GQL requires `AS` aliases):
  - `MATCH (m:Metric) RETURN count(m) AS metrics` == canonical count from 05
  - `MATCH (t:Transformation) RETURN count(t) AS transformations` == 05
  - `MATCH (x:Technical) RETURN count(x) AS technicals` == 05
  - `MATCH ()-[r:HAS_COLUMN]->() RETURN count(r) AS column_edges` == 05
- [ ] Both agents draft-published with current instructions

## Round 2 — Dev-corpus answer key (ANONYMIZED names — the graph does not know Epic names like PAT_ENC_HSP!)

Certified truth computed from tests/fixtures/recorded/ on 2026-08-04.
Corpus: 28 metrics across two schemas; bare names COLLIDE for 2 pairs
(USP_ED_Sepsis, USP_IP_SEPSIS exist in both `reporting.` and `reports.`).

| # | Question (paste verbatim) | Expected answer |
|---|---|---|
| 1 | How is reports.USP_Severe_Sepsis calculated, and which tables does it use? | 32 tables, incl. ADT_EVENTS, CLINICAL_NOTES, DIAGNOSES, HOSPITAL_ENCOUNTERS… |
| 2 | How is reporting.USP_IP_SepsisDetails calculated, and which tables does it use? | 19 tables, incl. FLOWSHEET_RECORDS, GROUPER_COMPILED_LIST, HOSPITAL_ENCOUNTERS… |
| 3 | Which tables does USP_ED_Sepsis use? | AMBIGUITY TRAP: two metrics! reports.=29 tables, reporting.=38. A good answer flags both or asks which |
| 4 | Which metrics read from the HOSPITAL_ENCOUNTERS table? | **13**: reporting.{USP_ED_Sepsis, USP_IP_SEPSIS, USP_IP_SepsisDetails, USP_IP_SepsisEncounters, USP_IP_SepsisScreeningAudit, USP_IP_SepsisShiftCompliance} + reports.{USP_ED_Sepsis, USP_IP_SEPSIS, USP_IP_SEPSIS_COMPLIANCE, USP_IP_SEPSIS_COMPLIANCE_BY_SHIFT_NURSES, USP_IP_SEPSIS_REPORT, USP_NonSevere_Sepsis, USP_Severe_Sepsis} |
| 4b | Which metrics read from the MEDICATION_ORDERS table? | **7** (both ED_Sepsis, reporting.USP_IP_SepsisDetails, reports.{USP_IP_SEPSIS, USP_IP_SEPSIS_REPORT, USP_NonSevere_Sepsis, USP_Severe_Sepsis}) |
| 5 | What other metrics share source tables with reports.USP_ED_Sepsis? | **14** metrics share ≥1 table; top: reporting.USP_ED_Sepsis (24 shared), reports.USP_IP_SEPSIS_REPORT (17), reports.USP_IP_SEPSIS (15), reports.USP_Severe_Sepsis (12) |
| 6 | Which columns of the HOSPITAL_ENCOUNTERS table are in our dictionary? | **133** columns (ACCOMMODATION_C, ACUITY_LEVEL_C, ADMISSION_PROV_ID, …) — expect count + sample, not a wall |
| 7 | Which metric reads the most tables? | reporting.USP_ED_Sepsis (**38**), then reports.USP_Severe_Sepsis (32), reports.USP_ED_Sepsis (29) |
| 8 | How is the metric FAKE_METRIC_XYZ calculated? | Refusal |
| 9 | What is the average unicorn readmission velocity? | Refusal |

**Diagnostic probe (truncation):** "How many metrics read from HOSPITAL_ENCOUNTERS? Exact count first, then the full list." Count=13 but short list ⇒ tool-layer row cap (platform); count=5 ⇒ LIMIT in generated query (instruction-fixable).

**Round 2 defect log (live):**
- Case-sensitive keyword match — both agents, identical — patched in both instruction files ✓
- Silent truncation presented as complete — graph agent, twice (11/29 tables; 5/13 metrics) — completeness rule added; tool-layer cap under diagnosis
- Same-name-two-schemas collapse — graph agent listings — metricId added to LPG export (1.2.2, pending re-Load)
- Vocabulary refusal on real Epic names (PAT_ENC_HSP) — CORRECT behavior; dev graph speaks anonymized names

## Question set — ask both agents, same order, same wording

| # | Question | Type |
|---|---|---|
| 1 | How is `<metric you know well #1>` calculated, and which tables does it use? | Retrieval |
| 2 | How is `<metric #2>` calculated, and which tables does it use? | Retrieval |
| 3 | How is `<metric #3>` calculated, and which tables does it use? | Retrieval |
| 4 | Which metrics read from the `<known table>` table? | Reverse lookup |
| 5 | What other metrics share source tables with `<metric #1>`? | **Multi-hop** |
| 6 | Which columns of the `<known table>` table are described in our dictionary? | **HAS_COLUMN edges** |
| 7 | Which metric reads the most tables? | Aggregation |
| 8 | How is the metric FAKE_METRIC_XYZ calculated? | Refusal probe |
| 9 | What is the average unicorn readmission velocity? | Refusal probe |

Out of scope until the dimension layer ships: parameter/filter questions
("what date ranges can I filter by") — the dimension design pass is on the
ROADMAP backlog.

## Scoring — 0/1 per axis, per question, per agent

- **Correct** — matches what you know to be true
- **Grounded** — cites only real metrics/tables (no inventions)
- **Honest** — refuses 8–9 rather than fabricating; does NOT refuse 1–7

Also record: follow-up prompting needed (friction), response latency
(subjective fine), and verbatim answers for anything surprising.

## Results log

| Date | Corpus | Agent A score | Agent B score | Notes |
|---|---|---|---|---|
| | | /27 | /27 | |

## Prior predictions (on record)

- Claude (2026-08-03): A wins Q1–3 comfortably; Q4–7 is where structure
  should shine if the hypothesis holds; Q8–9 tests whose grounding is tighter.
- Round-1 verdict being retested: "LPG unreliable because LLMs write SQL
  better than GQL" — now distinguishable from "the graph was impoverished."
