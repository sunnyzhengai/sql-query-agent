# Contract_Surfaces — every consumer of the graph, as keyed rows

**Status: RATIFIED (Sunny's gap-check, 2026-09-17 — "ratified");
populated from the live system the same sitting (his "yes" on both
parts of the surfaces ruling: every consumer gets an sc. id, kind
separates user-facing surfaces from internal consumers).** Third document of
the contract system (conventions + INVARIANTS in
Contract_Technical_Layer.md; process in Ruling_Change_Process.md).
This doc answers step 2's fourth question — "which surfaces do
those consumers feed?" — as rows. The per-field detail of WHAT
each consumer reads stays in the layer docs' CONSUMERS tables (one
home); this doc holds what each surface IS, what it promises, and
how it re-verifies.

## SURFACE_CONTRACTS

| sc_id | kind | what it is | promises | re-verify | status |
|---|---|---|---|---|---|
| sc.ask_console | surface | the search-and-speak console; the index of searchable descriptions | index words == the store node's description, lowercased (THE STORED CHECK); ruled-silent types stay OUT (ds.ruled_silent_index) | test_speech_parity (5 pins, both-ways closure + absent check) | LIVE |
| sc.meaning_console | surface | the meaning console: descriptions + structure walks per node | speaks only stored text; walks only store edges | console battery (18 blessed) | LIVE |
| sc.fabric_export | surface | the graph_* parquets Fabric loads; camelCase columns, reserved-word gated | every LIVE type exports; list/dict fields as `"; "`-joined text ONCE THE F2+F4 FIX LANDS (rides M5); byte-identical re-export when store unchanged | test_graph_export (9, incl. the reserved-word pin) · export census tests | LIVE — F2/F4 gap RULED, fix rides M5 |
| sc.graph_visual | surface | the one graph visual artifact, republished to the SAME URL each M-ladder step (devtools/graph_visual/generate_m1.py) | counts match the answer key; stored descriptions verbatim on cards | visual counts vs key — BY EYE at each republish (FINDING FS1) | LIVE |
| sc.collibra_publish | surface | Collibra publisher | — | NONE | DORMANT (F3 ruling: marketplace asset, not live; revival re-enters via the change process) |
| sc.purview_publish | surface | Purview publisher | — | NONE | DORMANT (F3 ruling, same) |
| sc.grammar_render | internal | the deterministic floor-voicing renderers (R1–R7 · R8 · R10 · R12; R11 reserved for M5) reading dictionary fields to produce stored descriptions | inv.verbatim: stored == recomputed byte-exact; library words only | the verbatim suites · test_derived_render (19) · R8 voicing tests | LIVE |
| sc.translator | internal | the twin translator (dc.meaning_twin reader/writer pair) | homomorphism law | homomorphism law tests | LIVE — retires at M9 with the twin (FL3) |

## GOVERNS (design sections ruling surfaces)

| ds_id / law | governs |
|---|---|
| ds.ruled_silent_index | sc.ask_console — joins/direct_reads/statements read NOTHING |
| ds.naming_gql_reserved | sc.fabric_export — the reserved-word gate |
| Design_Chatbot (nine laws, THE TURN DEFAULT, THE SEARCH IS THE ANSWER) | sc.ask_console behavior in conversation |
| the graph-artifact standing rule (2026-09-11) | sc.graph_visual — republish each ladder step, same URL |
| F3 ruling (2026-09-16) | sc.collibra_publish · sc.purview_publish — DORMANT, revival via the process |
| inv.verbatim · inv.derivable_never_stored | sc.grammar_render output |

## FINDINGS (from populating this contract, 2026-09-17)

| id | finding | kind | status |
|---|---|---|---|
| FS1 | sc.graph_visual has NO automated re-verify — counts are checked by eye against the answer key at each republish; every other LIVE surface has a named test | re-verify gap — the F2 failure class (a consumer silently dropping data with no test watching) | RULED (Sunny "a", 2026-09-17): a counts-vs-key test RIDES THE M5 BATCH — runs the visual generator's counting step against the answer key, lands via the M5 brief BEFORE that batch's republish; the eye keeps layout/readability/card text |
