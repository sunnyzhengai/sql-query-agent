# ADR 0035: Agentic Conversation over Deterministic Tools

**Status:** Accepted
**Date:** 2026-08-10 (evening — supersedes the dialogue machinery of ADR 0034, same day)

## Context

ADR 0032 separated the engine from the LLM after both Fabric agents
failed first-principles tests. ADR 0034 implemented that separation as
a typed-intent grammar: the LLM classified each question into a closed
verb menu and CODE ran the conversation — pick menus, confirm prompts,
binding dialogues, aspect ladders, re-route rules. Live testing the
same evening produced Sunny's verdict: "it feels wrong. we are hard
coding all rules again... sometimes the answer is not a list. we
should never be predicting what kinds of conversation will happen."

The correction came from re-deriving the separation from first
principles. Every answering turn is a chain of decisions of exactly
three kinds:

1. **Computable** — a right answer exists given the data (what cleared
   the floor; whether two SQL texts are identical; what tables a
   metric reads). Anything with a right answer must be produced by a
   process that always gets it right.
2. **Judgment** — genuine ambiguity resolvable only by intent ("which
   ED sepsis metric did you mean?"; "do I endorse this?").
3. **Linguistic** — what the question means, how to say the answer.
   No ground truth exists; only a language model can make these, and
   hard-coding them (keyword lists, menus, grammars) is chance with
   extra steps.

The enforcement principle: **an LLM decision is acceptable only when
its error mode is visible and bounded.** A wrong search phrase is
visible and recoverable; a silent top-1 pick is invisible and
corrupting — the Fabric graph agent's cardinal sin. QA corollary: you
TEST code (replay, CI, exactness); you can only MEASURE models
(suites, rates). Yesterday's agents failed because computable and
judgment decisions lived in the measured-only zone.

ADR 0034's grammar violated the principle from the other side: code
was making linguistic decisions (what a follow-up means, when to show
a list), which is why the product "felt dumber" while every retrieval
metric improved.

## Decision

**The LLM owns the conversation. The engine owns every computation.
The trace is always code.**

One conversational agent (function-calling loop over the customer's
Azure OpenAI) with a system prompt of invariants only — no question
templates, no verb menu, no conversation shapes. The deterministic
layer is exposed as tools shaped by WHAT THE STORE CAN DO — find,
read, list, verify — never by question types:

| Tool | Engine behavior (all fixed, parameterized, tested) |
|---|---|
| `search_catalog(phrase)` | the one semantic search; stratified plurality; all candidates with closeness |
| `find_by_name(name)` | exact case-folded name lookup across the catalog (families, refs) |
| `get_facts(id)` | fixed lookup — metric ref or step node_id |
| `list_steps(ref)` | a metric's step inventory |
| `check_same_logic(ids[])` | THE computation: content-hash partition over any nodes, diffs between groups, "cannot verify" for unrecorded SQL — never an LLM impression |

Comparisons, variants, enumerations of fetched facts, follow-ups,
clarifying questions: all LLM assembly over tool results. New node
kinds (tables, columns, users) arrive as rows, not tools.

**Two dispatch guarantees keep judgment decisions safe without menus:**

1. **No unsurfaced facts.** `get_facts`/`list_steps`/`check_same_logic`
   accept only ids that a tool call in THIS conversation surfaced or
   the user themselves named. The model cannot reach around retrieval.
   Enforced in the dispatch layer, not the prompt.
2. **Disclosure is stamped, not written.** The Basis line is built by
   code from the actual tool trace — every search, its candidate
   count, every id read, every computation run. Silent selection is
   structurally impossible: if the model answers from #1 of 5, the
   trace says so under the answer.

Prose invariants stay in the system prompt (facts only from tools,
refuse outside the certified base, PHI rules, ask when materially
ambiguous) and are MEASURED by the robustness suite — instructed
behavior, mechanically disclosed, statistically graded.

## Consequences

- Deleted: the intent grammar and typed-call parsing, pick/confirm
  loops and their escape hatches, detail commands, binding menus, the
  aspect-zoom ladder, validated re-routes, duplicate-list guard, the
  separate narrate edge. The conversation is the model's.
- Kept, inside tools: stratified search, fixed lookups, the content-
  hash kernel and diffs, batched fragment fetches, empty-SQL honesty,
  mid-stream Kusto error raising, closeness/threshold config.
- ADR 0032's "the human picks — no bypass" softens from coded gate to
  instructed-and-disclosed behavior: the agent is told to ask when
  ambiguity is material, and the stamped basis exposes every silent
  assumption. Measured by the suite; revisit if measurements say the
  disclosure isn't enough.
- ADR 0034 status: dialogue machinery superseded; its engine content
  (panel math generalized into check_same_logic) and its lesson
  (language belongs to the LLM) survive here.
- The flywheel logs turns (question, tool trace, answer) append-only;
  pick/confirm event granularity returns when a surface affords it.
- The robustness suite gains an agent-level section over the scorecard
  questions: grade the CONVERSATION (right tools called, grounded
  answer, honest refusal), since grammar-level classification no
  longer exists.
