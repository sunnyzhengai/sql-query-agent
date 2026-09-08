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
| 1 | pre-tier still in code (ruled dead) | B | OPEN |
| 2 | prompt still has kind menu/synonyms; drops mentions | C | OPEN |
| 3 | proposal-cache key ignores prompt version | C | OPEN |
| 4 | labels not searchable as entries (the group hit) | B | OPEN |
| 5 | string-tier ladder runs before vectors | B | OPEN |
| 6 | expansions not used as search text | B | OPEN |
| 7 | kind machinery alive (VALID_KINDS, marks, kindset engine, metric pseudo) | B | OPEN |
| 8 | kind → label rename (field, registries, docs) | D | OPEN |
| 9 | PBI/TMDL layer not loaded (data, own GO) | — | PARKED |
| 10 | no ranked-results renderer (outcome branches are the default) | B | OPEN |
| 11 | thresholds are behavioral gates, not display bands | B | OPEN |
| 12 | clicks travel as questions (reroute ruled, unbuilt) | A | OPEN |
| 13 | user decisions die on restart (governance journal) | E | OPEN |
| 14 | no revoke at the surface | E | OPEN |
| 15 | clarify-actions LIVE BUG (typed input after a clarify errors) | E | OPEN |
| 16 | literal-census enforcement unbuilt | F | OPEN |
| 17 | "delivery · delivery" labels (expected to dissolve in #10) | B | OPEN |

Steps: **A** click reroute (the dependency) · **B** the search
rebuild (1,4,5,6,7,10,11,17) · **C** prompt v3 + registry +
versioned cache key (2,3) · **D** the label rename (8) · **E** bug
+ persistence + revoke (13,14,15) · **F** the literal census (16).
