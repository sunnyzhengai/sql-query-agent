# The Chatbot Build Manifest — the claims ledger

*(2026-09-07. The unbuilt-build lesson made mechanical: every ruled
clause of the nine-law dig is enumerated here; a build slice may
claim DONE only against evidence (a test, an artifact); anything
else is DEFERRED with its reason on record. "Done except X" is the
only honest done.)*

Statuses: **BUILT** (evidence cited) · **DEFERRED** (reason cited) ·
**OPEN** (this build, not yet reached) · **STANDS** (already built
pre-dig and still lawful).

| # | clause (law) | status | evidence / reason |
|---|---|---|---|
| 1 | Facet cards: name+speech cards per node, max-score, card provenance (FACET DECISION) | BUILT | grounding.cards()/SemanticIndex max-over-cards + via_card; test_facet_cards_name_card_wins; GR-4 cache-key-per-card |
| 2 | Kind_Vocabulary table dies; kinds ground via earned vocab → proposal marks → kind-node speech (L4/RULED) | BUILT | registry tombstone; _earned_vocabulary (terms parent kind::K); proposed-kind marks; _self speech rows; seeded-vocab tests |
| 3 | Anaphor_Vocabulary table dies; Interpreter marks reference-roles; resolution stays deterministic (L4-D3) | BUILT | ground(role=); registry tombstone; FU tests carry proposal roles |
| 4 | THE ONE ENGINE: mentions→sets, connect-the-sets, display set by user's words; execute() dispatch dies (L4-D1) | BUILT | _sets_from/_connected/_topic_filter/one execute; dispatch deleted; buckets by-name→connected→meaning→parts; CN/FU/MT families green |
| 5 | Provisional answer: three shapes by evidence profile, assumption shown, switch links, registry margins (L3-D1) | BUILT | _provisional + Response_Shapes.PROVISIONAL_MARGIN; runners_up carried |
| 6 | Clarify obligations: name-grain dedup, kind grouping, visible cap, score+speech rows (L3-D2) | BUILT | _shape_clarify (name-grain dedup w/ places, kind grouping, CLARIFY_CAP, more_candidates); place-choice expansion; ST-1 green |
| 7 | Clarify-miss counter: next-action recorded (picked/re-typed/abandoned) (L3-D3) | BUILT | console last_clarify → usage clarify-picked/clarify-retyped events |
| 8 | Partial answers as law (L3-D4) | STANDS | 0080 anchored-topic behavior + tests |
| 9 | Meaning-book: confirmation attaches to reference-set; phrasings = evidence; new phrasing → confirmed set answers immediately (L2-D1) | BUILT | reference_set_key/confirmed_reference_sets; via=meaning-book; test_rm3 |
| 10 | Claim/frame/process word classes (L2-D2, L6-D2) | OPEN | slice 7 (review-grade; trace templates) |
| 11 | Confirm card shows the complete boundary artifact (L2-D3) | BUILT | inline confirm renders the kind-marks/mentions of the artifact; full-proposal display rides result[interpretation] |
| 12 | Lines are clickable nodes (L1-D2) | STANDS+OPEN | answer lines partially clickable (Referenced); full per-line links slice 7 |
| 13 | Graph-is-reality absence; search-not-dictionary concepts (L1) | STANDS | honest zeros + topic search (0080 tests) |
| 14 | Seat names + rights (Scribe/Interpreter/Ranker/Smoother) (L1) | BUILT | console docstring names the four seats + rights; Interpreter/Ranker factories annotated |
| 15 | Slot-survival smoothing (L1) | DEFERRED | the Smoother seat itself is deferred (gated, optional); method ruled, wired when the seat wires |
| 16 | Expansion invite in the live prompt (L1/L7 dark half) | BUILT | prompt v2 invites expansions/kinds/references/hint |
| 17 | Display hint preselects a view, visibly (L4-D4) | BUILT (cage+validation) / OPEN (surface preselect button highlight — cosmetic) |
| 18 | Cold start: kind self-description + earned vocabulary (L4-D2) | BUILT | _self rows + kind entries speak them; cold-start = proposals + confirms |
| 19 | Stacked table: bounded, bare→top, kind-qualified→down, round-provenance clarifies (L5-D1) | BUILT | console stacks (TABLE_DEPTH) + ask stack-walk for role-marked mentions |
| 20 | Selections are acts; clarify-picks accrete (L5-D2) | BUILT | clicks/picks land as rounds; picks recorded as usage events (accretion to meaning-book = the confirm click) |
| 21 | The visible table + clear-table (L5-D3) | BUILT | #table right rail (top expanded, rounds collapsed, clear-the-table act) |
| 22 | Session-vs-tree split (L5-D4) | STANDS+DEFERRED | session ephemeral (stands); the TREE SURFACE (my history page) deferred: single-user demo console — needs identity; tree DATA accretes now (author-keyed events) |
| 23 | Trace three layers; process words from data; completeness spec (L6-D1/2/3) | BUILT (work line: plain process words incl. 'no expansions proposed') / PARTIAL (full evidence expansion layer + engine display-rationale line — follow-up polish) |
| 24 | Trace derivable, inputs recorded (L6-D4) | STANDS | proposals + snapshots recorded (0080/Law-4 build) |
| 25 | Scope ladder: personal-first, promotion queue, steward blessing (L7-D1) | PARTIAL/DEFERRED | personal-first accretion built (author-keyed); the QUEUE SURFACE deferred: needs multi-user identity — demo is person:console |
| 26 | Inline confirmation; usage≠consent (L7-D2) | BUILT | pending_confirmation inline; blocking only on clarify |
| 27 | Revocation w/ blast radius (L7-D3) | DEFERRED | steward surface; revoke events exist (dispositions) — the UI affordance ships with the tree surface |
| 28 | Blessings anchor to meaning; telemetry proposes never self-modifies (L7-D4) | PARTIAL | reference-set stored on confirmations; content-key anchoring of blessings = follow-up; self-tuning ban structural |
| 29 | Embedding model = rule; announced migrations (L8-D1) | STANDS | vectors stamped by model version; migration = re-embed (cache keys); announcement rides the registry bump practice |
| 30 | Proposal cache by (question, model version) (L8-D2) | BUILT | make_interpreter cache keyed (question|model), disk-persisted |
| 31 | Degradation ladder as data, what-still-works banners (L8-D3) | BUILT (registry Degradation_Ladder; seat_down banners stand) / the per-level banner text wiring = follow-up polish |
| 32 | Change caption on moved answers (L8-D4) | BUILT | ledger-hit snapshot diff caption |
| 33 | Coverage line: header + inline on absence (L9-D1) | BUILT | __COVERAGE__ header + absence answers cite searched-all-N |
| 34 | Estate card as empty state (L9-D2) | BUILT | /round?card=estate boot round |
| 35 | Counted things askable (L9-D3) | STANDS+OPEN | drift findable (stands); exclusions-as-findable slice 7 |
| 36 | Absence answers are doors (L9-D4) | BUILT | the absence door (universe + nearest + next act) |
| 37 | Access-scoped searchability (L9-D4 note) | DEFERRED | single-user demo; the scope column lands with multi-user identity |
| 38 | PBI/TMDL report layer into the estate (RULED pre-dig) | DEFERRED | own workstream on its own GO: estate-data intake (TMDL parser port) — not a chatbot-code slice |
| 39 | User-tree memory as tree structure (contracts) | PARTIAL | accretion events author-keyed now; tree QUERIES/surface with identity (see 22, 25) |
