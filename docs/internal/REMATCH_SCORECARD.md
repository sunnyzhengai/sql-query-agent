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
