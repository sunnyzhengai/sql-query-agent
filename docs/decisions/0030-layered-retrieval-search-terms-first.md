# 0030 — Layered retrieval: search-terms first, vectors where the engine allows

**Status:** Accepted (amended same day — see Amendment)
**Date:** 2026-08-08

## Amendment (2026-08-08, after product review + deep-dive research)

Sunny's product call: L0/L1 are not the product answer — LIKE-widening
reads as a workaround, and the product's credibility rides on real
semantic retrieval. Revised posture:

- **L1 is demoted** from "default product answer" to an available
  fallback; it is not on the roadmap unless L3's gate fails.
- **L3 is the intended path**, and the deep-dive (round 2 in
  [FABRIC_RETRIEVAL_CAPABILITIES.md](../development/FABRIC_RETRIEVAL_CAPABILITIES.md))
  found it green on every documented axis (AI_GENERATE_EMBEDDINGS on
  Fabric SQL DB with the customer's own Azure OpenAI; exact scan
  documented adequate under 50k vectors; explicit nightly write path)
  EXCEPT one undocumented gate: whether agent-generated SQL against a
  Fabric SQL DB source executes on the operational engine (where
  AI_GENERATE_EMBEDDINGS works) or the read-only SQL analytics endpoint
  (where it does not). **A live probe decides** — seeded example pair
  with `ORDER BY VECTOR_DISTANCE(emb, AI_GENERATE_EMBEDDINGS(...))`,
  verified via the agent's run-steps view. Probe passes → L3 becomes
  the semantic-retrieval architecture. Probe fails → Eventhouse/KQL
  fallback (ai_embeddings preview) is evaluated before any retreat to
  L1.
- **L2 ships regardless** (embeddings for runtimes we control); it does
  not solve Fabric-agent ask-time retrieval and is not claimed to.

## Probe verdict (2026-08-08): FAIL — SQL-DB path ruled out empirically

Run live by Sunny on the dev tenant. Setup fully worked when run
directly in the SQL database ("patients who came back to the ER" →
readmission step first, distance 0.49 vs 0.62/0.63 for non-matches,
1.1 s including the embedding round-trip — semantic matching, gap
where the 0.55 threshold sits). But the Data Agent's example-query
validator rejected the vector SQL with, verbatim:
"'AI_GENERATE_EMBEDDINGS' is not a recognized built-in function name"
and "Invalid column name 'emb'". Diagnosis, refined after external
architect review (2026-08-08): the CONFIRMED wall is the agent's own
QUERY-VALIDATION layer — its error "Could not locate entry in
sysdatabases for database 'MODEL'" shows its parser read `USE MODEL`
as an old `USE <database>` statement, i.e. the validator's parser
predates the AI functions regardless of what engine would have
executed. The analytics-endpoint MIRROR dropping the VECTOR column is
a second, PLAUSIBLE wall (consistent with `emb` missing from the
agent's schema panel and with the docs' "executes through the SQL
Analytics Endpoint" statement) but unproven — execution never
happened. Disambiguation completed 2026-08-08, run live on the analytics
endpoint. BOTH walls confirmed, and a third distinguished — the full
taxonomy of why the SQL path is closed:
1. AGENT VALIDATOR: pre-AI-functions parser (misread USE MODEL as
   USE <database>) — blocks before execution.
2. ANALYTICS ENDPOINT ENGINE: modern parser, function deliberately
   disabled ("FUNCTION 'AI_GENERATE_EMBEDDINGS' is not supported",
   Msg 15871) — would block execution even past the validator.
3. MIRROR: vector column genuinely dropped (INFORMATION_SCHEMA lists
   node_id/name/business_name/description — no emb) — no vectors to
   search even if the function existed.
Any one wall suffices; all three are real. Re-test trigger: Microsoft
would need to fix all three (or route agents to the operational
engine) before L3-on-SQL-DB becomes viable.

Consequences:
- L3-on-SQL-database is retired until Microsoft either runs agent
  queries on the operational engine or mirrors vector columns.
- Next fork, in order: (1) **Eventhouse/KQL probe** — the agent
  queries KQL databases directly (no mirror layer to drop columns);
  series_cosine_similarity is GA, ai_embeddings plugin is preview with
  per-user callout/role prereqs. (2) **Azure AI Search source** —
  previously ruled out, now REOPENED: it is the one agent-native
  semantic retrieval path (the agent itself sends the question to the
  index; no in-SQL embedding needed at all), at the cost of an
  external index dependency. Decide after the Eventhouse probe.

## Eventhouse probe verdict (2026-08-08, same day): PASS

Run live by Sunny. Full chain verified: callout policy accepted;
`ai_embeddings` under user impersonation (NO key stored in Fabric)
embedded the seeded catalog; direct search reproduced the SQL probe's
geometry exactly (true match 0.5075 vs 0.375/0.369 — same embedding
model, two engines, identical space; 0.45 threshold confirmed in-gap).
Then the decisive part: the throwaway Data Agent's validator ACCEPTED
the example pair (no inline rejection, unlike SQL), and on a
paraphrased question the agent GENERATED KQL containing ai_embeddings
+ series_cosine_similarity, EXECUTED it (callout fired from
agent-generated code under the asking user's identity), and returned
the correct row (ED Sepsis Screening) with business name attached.

**Eventhouse is the semantic-retrieval architecture (L3 = KQL).**

Observed generator behavior to shape in productization:
- It expanded the embed phrase into a keyword dump (fine for
  embeddings; ignores the "short noun phrase" instruction).
- It IMPROVISED hybrid retrieval: lexical `where ... has` filters ON
  TOP of similarity ranking — correct here, but keyword filters can
  reintroduce exact-vocabulary failure (the readmit row contains no
  "sepsis"). Productization must decide hybrid-vs-pure.
- It ignored the 0.45-threshold/count-reporting discipline.
The remedy is the ADR 0020 move at the database layer: wrap the
pattern in a **stored KQL function** (`semantic_search(phrase)`) —
KQL functions are schema-selectable for Data Agents — so the
generator's job shrinks to calling one function, not composing the
pipeline. Deployment prereqs to document: Eventhouse item + callout
policy (one-time admin) + "Cognitive Services OpenAI User" role for
EVERY asking user (group assignment) on the customer's Azure OpenAI;
~1 embedding call per question (fractions of a cent).
- Bonus empirical finding for the whitepaper/demo: an unscoped Data
  Agent FABRICATED a complete appointments dataset (counts + chart)
  rather than refusing — before/after screenshots captured. The
  platform's default refusal posture is weak; AIVIA's grounding and
  refusal rules are load-bearing, not decoration.

## Context

Resolution today is exact-ish: LIKE on name columns (Delta agent) and
in-context catalog matching (graph agent). Both work at dev scale (28
metrics) and both strain at known first-customer scale — our own source
estate is 1,344 procs, and the scorecard already documents tool-layer
row caps truncating large catalog fetches. Waiting for a deployment to
fail before hardening retrieval is not a plan.

The constraint that shapes everything (verified 2026-08-08,
[FABRIC_RETRIEVAL_CAPABILITIES.md](../development/FABRIC_RETRIEVAL_CAPABILITIES.md)):
ask-time retrieval executes inside the Fabric Data Agent as generated
SQL/KQL — and the SQL endpoint over our Delta tables has **no vector
type, no distance function, and no in-query embedding**. In-language
similarity exists in exactly two groundable engines: **Fabric SQL
database** (VECTOR + VECTOR_DISTANCE GA; AI_GENERATE_EMBEDDINGS
preview-ish) and **Eventhouse KQL** (series_cosine_similarity GA;
ai_embeddings plugin preview, impersonation + callout-policy prereqs).
The agent's one built-in semantic mechanism is vector retrieval over
example query pairs (≤100/source).

## Decision

Retrieval hardens in layers; each ships independently and none breaks
the zero-extra-infrastructure baseline.

1. **L0 — description matching in instructions** (immediate): both
   agents also match user keywords against `description`. Free.
2. **L1 — generated `search_terms` (the default product answer):** 07
   generates 5–10 aliases per metric, business term, and named step
   (synonyms, abbreviations, colloquialisms — "canceled appts",
   "no-shows"), content-hash cached like descriptions, stored as a
   searchable column on `output_metric_logic` (and term/step surfaces).
   Plain LIKE then behaves semantically for the vocabulary that matters,
   on the existing lakehouse tables, deterministic at ask time. This is
   ADR 0020's lesson applied to retrieval: reshape the data so the
   generator's habitual query finds the right rows.
3. **L2 — build-time embeddings for runtimes we control:**
   `graph_node_embeddings` (node_id → vector) generated in 07 via the
   customer's Azure OpenAI embeddings deployment (same `llm_client`
   plumbing) or Fabric's `ai.embed`. Consumers: the local backend today;
   the self-service tier / any API surface tomorrow. Not consumable by
   the Fabric agent on the SQL endpoint — stored anyway because
   generation is cheap and every controlled runtime wants it.
4. **L3 — optional "semantic catalog" add-on for ask-time similarity in
   Fabric:** a small **Fabric SQL database** item holding the resolution
   catalog (ids, names, business names, terms, descriptions,
   `VECTOR` embeddings), refreshed by the pipeline, added as a Data
   Agent source. The agent is steered — via **example query pairs**, the
   mechanism that is itself vector-retrieved — toward the one-statement
   shape `ORDER BY VECTOR_DISTANCE(embedding, AI_GENERATE_EMBEDDINGS(
   <question> USE MODEL ...))`. SQL-database path chosen over Eventhouse:
   GA vector type/function, T-SQL (one dialect for the agent), no
   Real-Time-Intelligence footprint, no per-user callout/role prereqs;
   Eventhouse remains the documented fallback. L3 is an **optional
   adapter** in the ADR 0009 sense: the product is fully functional on
   L0+L1; L3 has its own prerequisites (SQL DB item, external model
   binding, scoped credential) and its own install-guide section.

**Triggers:** L0+L1 before the first deployment beyond ~100 metrics —
i.e., before the first enterprise pilot, since our own estate is 1,344.
L3 before *offering* semantic search as a differentiator, and only
after re-verifying AI_GENERATE_EMBEDDINGS' GA status on Fabric SQL DB.

## Consequences

- The baseline stays BYOT-simple: no new items, no new prereqs; L1 adds
  one LLM-generated column through the existing 07 boundary (PHI gate
  applies to its inputs like everything else that leaves).
- Search-term generation gets the same treatment as descriptions:
  hash-cached, leak-gated, regenerated only on change.
- L3 introduces the product's first non-lakehouse Fabric item — kept
  optional precisely because certification and the 30-minute-install
  promise must not depend on preview features (same rule that keeps the
  Graph Model out of the default path).
- The rematch (Round 3) gains a retrieval dimension: same question set
  at L0/L1 vs L3 quantifies what the semantic layer buys — evidence for
  making L3 default later, or not.
- Azure AI Search stays out: an external index duplicates catalog state
  outside the lakehouse and adds an Azure dependency for a problem L1/L3
  solve in-platform. Revisit only for unstructured-document features.
