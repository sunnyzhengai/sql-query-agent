# The Data Contract Is the Prompt — Delta vs. Graph, Round 2 (DRAFT)

> **Status: draft** (2026-08-06). Round 2 is partially run — 3 of 9 questions
> scored, halted by F2 capacity throttling. Numbers below cite
> [REMATCH_SCORECARD.md](REMATCH_SCORECARD.md) (protocol + live defect log)
> and [REMATCH_SCORECARD_result01.md](REMATCH_SCORECARD_result01.md)
> (round-1 transcripts). Finish the remaining questions before publishing;
> the thesis is already supported by the partial run.

## The question

Round 1 (2026-07) ended with a tempting verdict: "LPG unreliable — LLMs
write SQL better than GQL." Round 2 existed to test whether that verdict was
about query languages at all, or about the fact that round 1's graph was
structurally impoverished (case-split nodes, empty dimension layer, floating
column nodes) while the Delta side got a hand-curated table. The hypothesis
on record (2026-08-02): SQL is set theory and LLMs get "creative"
translating natural language into it; graph traversal is semantically closer
to natural language — *given a quality graph structure*, NL-to-traversal
should be easier and more accurate.

## What actually happened

Three rounds of instruction fixes could not make the graph agent correct.
One export reshape did.

The defect log tells the story in order:

1. **Silent undercounts presented as complete.** The graph agent answered
   "5 metrics read HOSPITAL_ENCOUNTERS" (truth: 13) and "11 tables" (truth:
   29) — confidently, no hedge. Local reproduction found the cause: the
   instructions taught a single-hop `CALCULATED_BY->READS_FROM` pattern, but
   `CALCULATED_BY` reaches only root CTEs; the full calculation is the
   `DEPENDS_ON` transitive closure. The generated query was *valid,
   plausible, and shallow* — the worst failure class, because nothing looks
   wrong.
2. **Instruction fixes were stochastic.** Depth-semantics rules and
   variable-length `DEPENDS_ON{0,50}` patterns were added; answers improved,
   then regressed overnight — same instructions, same question, the
   generator flipped its filter property back from `metricId` to bare
   `name`, and the "Basis" footer described a query that was never run.
   Instruction steering of NL2GQL is a probability distribution, not a
   contract.
3. **The export reshape ended it.** ADR 0020 moved the fixes into the data:
   `name` := the schema-qualified identifier (because the generator filters
   `name` with whatever the user typed), and `CALCULATED_BY` := the
   materialized step closure (because the generator writes single-hop
   patterns). Post-1.3.1, the same questions that had survived three
   instruction-fix rounds returned exact sets: Q1 32/32 tables, Q4 13/13
   metrics, Q3 correctly surfaced the two-schema ambiguity trap and asked
   which twin the user meant.

**Verdict line: the data contract, not the prompt, is where correctness
gets enforced.** You cannot instruct your way out of a shape mismatch
between the generator's habits and the graph's semantics — you reshape the
graph to meet the generator where it reliably is.

## Secondary findings (each is its own lesson)

- **Schema descriptions must teach edge transitivity.** LLM query
  generators default to shallow patterns; if an edge's meaning is "closure,"
  either materialize the closure (what ADR 0018/0020 did) or expect
  undercounts. NL2GQL schema docs that omit "this edge is transitive" are
  incomplete in a way that produces *confident wrong answers*.
- **Self-reported provenance needs its own grounding rule.** The agent's
  Basis footer — added as a verification device — echoed the *instructed*
  query shape, not the *executed* query. A footer-honesty rule (Basis must
  describe the executed query; 0-row answers must name the filter that
  returned 0) is now in the instructions. Trust nothing the model says
  about its own retrieval unless the harness can check it.
- **Identity is a two-sided contract.** Qualified user reference vs. bare
  name property (and the reverse) both produced false "not found". The fix
  lived in both places: an identity rule in instructions, and qualified
  names in the export. Case-insensitivity (ADR 0016) was table stakes.
- **Refusal behavior held.** Both agents correctly refused fabricated
  metrics; the graph agent's "vocabulary refusal" on real Epic names
  (PAT_ENC_HSP) against the anonymized dev corpus was *correct* behavior —
  the graph speaks the names it contains, which is exactly the grounding
  guarantee.
- **Operational: F2 supports ~6 agent Q&A per burst** before capacity
  throttling; pause/resume resets. Budget rematch sessions accordingly.

## Where this leaves the hypothesis

Partially confirmed, with a sharper formulation. The graph did not win
because traversal is "closer to natural language" in the abstract — it won
(on the questions run so far) once the *export* encoded the semantics the
generator assumes. The real finding is symmetric and more useful: **both**
NL2SQL and NL2GQL are only as reliable as the agreement between the
generator's habitual query shapes and the data's actual semantics. Delta's
round-1 advantage was exactly that agreement, hand-built
(`output_metric_logic` is pre-joined into the shape questions take).
ADR 0020 gave the graph the same property, mechanically.

## Before publishing

- [ ] Finish Q2, Q4b, Q5–9 on the post-1.3.1 graph (respect the ~6-question
      F2 burst budget; re-Load the Graph Model first — the LPG is a snapshot)
- [ ] Run the Delta agent on the identical set for the head-to-head table
- [ ] Fill the /27 scorecard for both agents; keep verbatim transcripts
- [ ] Decide venue: internal ADR-adjacent note vs. public engineering post
      (public version needs the anonymized-corpus framing made explicit)
