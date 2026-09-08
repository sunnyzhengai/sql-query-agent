# The Search Rebuild Manifest — the claims ledger for Sunny's pipeline

*(2026-09-07. The ruled behavior: question → LLM (intention,
mentions, expansions) → vector search against EVERYTHING (labels,
names, descriptions — pre-vectorized) → RANKED SCORED HITS returned
→ clicks are steer. Recorded in "AIVIA Design Document Chatbot.md"
(THE SEARCH IS THE ANSWER). Every gap below closes suite-first;
statuses update as steps land. "Done except X" is the only honest
done.)*

| # | gap | step | status |
|---|---|---|---|
| 1 | pre-tier still in code (ruled dead) | B | BUILT | pre-tier deleted; ask() runs memory→model→search |
| 2 | prompt still has kind menu/synonyms; drops mentions | C | BUILT: prompt 3.0.0 in Seat_Prompts (registry 1.26.0) — shapes only, every referring word required |
| 3 | proposal-cache key ignores prompt version | C | BUILT: key = question|model|prompt-version; stale proposals unreachable |
| 4 | labels not searchable as entries (the group hit) | B | BUILT | label:: entries derived from the live store, singular+plural cards; group hits w/ member counts |
| 5 | string-tier ladder runs before vectors | B | BUILT | tier ladder deleted from the search path; cosine≈1 subsumption pinned |
| 6 | expansions not used as search text | B | BUILT | searched_as = mention + expansions; visible in the trace |
| 7 | kind machinery alive (VALID_KINDS, marks, kindset engine, metric pseudo) | B | BUILT | VALID_KINDS deleted; kinds field stripped by the cage; kindset engine deleted |
| 8 | kind → label rename (field, registries, docs) | D | OPEN |
| 9 | PBI/TMDL layer not loaded (data, own GO) | — | PARKED |
| 10 | no ranked-results renderer (outcome branches are the default) | B | BUILT | present_hits: ranked, grouped by label, scores + via-card; clarify/provisional emergent |
| 11 | thresholds are behavioral gates, not display bands | B | BUILT | floor = display band; no behavioral cliffs in the search path |
| 12 | clicks travel as questions (reroute ruled, unbuilt) | A | BUILT | step A: entity + label-group rounds; entity= links; interpreter never consulted by clicks |
| 13 | user decisions die on restart (governance journal) | E | OPEN |
| 14 | no revoke at the surface | E | OPEN |
| 15 | clarify-actions LIVE BUG (typed input after a clarify errors) | E | BUILT: actions joined USAGE_ACTIONS by ruling; hermetic clarify→next-round pin (registry mirror lands in F) |
| 16 | literal-census enforcement unbuilt | F | OPEN |
| 17 | "delivery · delivery" labels (expected to dissolve in #10) | B | BUILT | dissolved into present_hits (names + identities per row) |

Steps: A,B,C + gap 15 LANDED (2026-09-07). Resequenced 2026-09-08
(Sunny's scoring rulings): **D** label rename (PROMOTED — code is
written in label terms before the rework) · **G** total-score
search (label cards replace label:: nodes; card-sum ranking;
lexical = deferred-conditional, trigger: observed label
overcrowding) · **H** the PBI layer (pbi_snapshot intake, PBI
Report label, executes edges, full-word names, short descriptions)
· **I** acronym enrichment (scan → Scribe → bless → acronym nodes;
used_by derived at graph build — the auto-connect sentence IS
contract text) · **E** persistence journal + revoke (acronyms and
the ledger both depend on it) · **F** the literal census.
