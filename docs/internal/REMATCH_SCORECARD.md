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
- PENDULUM: over-refusal after hardening (2026-08-08, same session as the
  fabrication): with the new verbatim/no-facts rules pasted, Q1 ("How is
  ED Sepsis Screening calculated?") -> honest refusal, Basis "catalog
  fetch -> 0 matched" — despite businessName being the EXACT string in
  the catalog. Hypothesis: generator's fetch dropped businessName from
  RETURN. The new rules worked as safety (honest footer, no invention)
  but resolution quality regressed same-day — fourth non-determinism
  data point. Reinforcement added (fetch MUST return businessName; a
  businessName match IS resolution). Durable fix remains structural:
  the semantic catalog (Eventhouse) owning resolution. DEMO DECISION:
  video rides the Delta agent (already the GA-default), which handles
  business-name resolution robustly via LIKE.
- FABRICATED count on failed execution (2026-08-08, graph agent, 1.4.2 +
  business names): asked for exact step count of ED Sepsis Screening
  (truth 43). Generated GQL filtered name =
  'reporting.USP_ED_Sepsis (ED Sepsis Screening)' — business name GLUED
  into the identity filter (new failure mode introduced by displaying
  business names) -> execution FAILED ("No data found") -> agent answered
  "15 steps" with Basis claiming "-> 15 rows" — count invented from its
  own prior prose. The fabricated-Basis defect recurring under a new
  trigger. Instruction fixes applied (verbatim-catalog-values rule;
  empty-execution-means-no-facts rule); if it recurs, the ADR 0020 move
  is a displayLabel property so the generator's habitual string matches.
  Count questions stay OUT of the demo video until this passes.
- Case-sensitive keyword match — both agents, identical — patched in both instruction files ✓
- Silent undercount presented as complete — graph agent, twice (11/29 tables; 5/13 metrics) — ROOT CAUSE FOUND by local reproduction: instructions taught single-hop CALCULATED_BY->READS_FROM, but CALCULATED_BY reaches only root CTEs; full calculation is the DEPENDS_ON transitive closure. Shallow pattern reproduces the agent's answers exactly (5==5 readers, 12~=11 tables). Fix: depth-semantics rules + variable-length DEPENDS_ON{0,50} patterns in instructions. Writeup insight: schema descriptions for NL2GQL must teach which edges are TRANSITIVE, or LLMs default to shallow patterns
- Same-name-two-schemas collapse — graph agent listings — metricId added to LPG export (1.2.2, pending re-Load)
- Vocabulary refusal on real Epic names (PAT_ENC_HSP) — CORRECT behavior; dev graph speaks anonymized names
- Identity mismatch, both directions — graph agent: (a) user's qualified ref
  (reports.USP_Severe_Sepsis) exact-matched against BARE name property -> 0 rows
  -> false "not found"; (b) user's bare ref auto-qualified by the agent from a
  prior listing, then matched against bare name -> same 0 rows. Fix: IDENTITY
  rule in instructions (dot => lower(metricId), bare => lower(name), try both
  folded before "not found")
- Generator non-determinism (2026-08-05 morning): same instructions, same
  question as the prior evening — filter property flipped back from metricId
  to bare name; single step; footer again described a query never run.
  Verdict: instruction steering of NL2GQL is stochastic -> ADR 0020
  (compatibility export: name := qualified, CALCULATED_BY := step closure)
- Probe traces (pre-1.3.1 graph): "Which tables does reports.USP_Severe_Sepsis
  use?" -> generator CHOSE USES_TABLE single-hop unprompted (correct shape!)
  but filtered bare name -> 0 rows. "Which metrics read HOSPITAL_ENCOUNTERS?"
  -> shallow CALCULATED_BY chain -> 5/13 undercount. Both exact queries become
  correct under the 1.3.1 export — the shim covers the generator's whole
  observed behavior space
- FABRICATED Basis footer — graph agent claimed
  "Metric->CALCULATED_BY->DEPENDS_ON{0,50}->READS_FROM" while the executed GQL
  was a single-hop exact-match on name. The footer echoed the INSTRUCTED shape,
  not the EXECUTED query — a verification device that lies. Fix: footer-honesty
  rule (Basis must describe the executed query; 0-row answers must name the
  filter that returned 0). Writeup insight: self-reported provenance needs its
  own grounding rule, or the LLM pattern-matches the footer from instructions

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

**2026-08-06 — 1.4.1 deployed (step descriptions live in the LPG):**
informal probe "How is USP_ED_Sepsis calculated" returned a step-catalog
answer — population, timing filters, BPA/alert workflow, 24h readmits,
HemOnc transfers, boarder logic — every distinctive claim verified to
trace to a certified step description (not agent invention). Round-1's
answer to the same question could only list tables. Q1-style questions
should now score materially richer; note for the writeup.

**2026-08-05 — Graph Agent, post-1.3.1 (ADR 0020 shim live), partial run:**

| Q | Result | Notes |
|---|---|---|
| 1 | ✅ 32/32 tables | exact answer-key set, dictionary descriptions attached |
| 4 | ✅ 13/13 metrics | generator chose USES_TABLE unprompted; exact set match |
| 3 | ✅ ambiguity surfaced | flagged both twins, asked which (the pass criterion); twins known from chat context after bare-exact miss. Footer tic persists: Basis said "catalog fetch", executed query was a USES_TABLE traversal |

Run halted at 6 questions: F2 capacity throttled (second time) — **operational
finding: ~6 agent Q&A per burst on F2**; pause/resume resets. Both silent-
undercount defects confirmed dead in production: the same questions that
returned 0 and 5/13 through three instruction-fix rounds returned complete
sets once the export was reshaped to the generator's habits. Verdict line
for the writeup: **the data contract, not the prompt, is where correctness
gets enforced.**

## Prior predictions (on record)

- Claude (2026-08-03): A wins Q1–3 comfortably; Q4–7 is where structure
  should shine if the hypothesis holds; Q8–9 tests whose grounding is tighter.
- Round-1 verdict being retested: "LPG unreliable because LLMs write SQL
  better than GQL" — now distinguishable from "the graph was impoverished."
