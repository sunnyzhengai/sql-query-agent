# Brief_M5_Statement_Layer — the statement layer + R11, with the F2+F4 export fix and the FS1 visual counts test riding

**Status: BUILT** (full suite 2196 passed / 0 failed, 12:06, 2026-09-17; R11 RATIFIED v2.11.0 at the mid-build checkpoint; CLOSED follows Sunny's load + the served §M5 gates + the visual republish)

| field | content |
|---|---|
| class | planned addition — fills FL2, the declared M5 slot; the entry gate held since the M4 close ("M5 now holds the next entry gate") |
| claims | ds.birth_edge_law (statements' birth edges point down at scopes/conditions — now homed in Design_Graph_Engine) · the 2026-09-10 identity ruling (statement id = `<file>::stmt/<position>`; R11 suite-first, Sunny gap-checks phrasing) · the (b) ruling 2026-09-17 (36 R11 descriptions + 31 operational empty-by-rule, counted) · ds.ruled_silent_index (statements OUT of the ask index — gap-checked list) · F2+F4 RULED (export list/dict fields as `"; "`-joined text; pairs `code = meaning`) · FS1 RULED (visual counts-vs-key test lands BEFORE this batch's republish) · FL8 (the dead counter + the subkind writer — carried as ambiguities below) |
| impacts (computed, step-2 query over the three contracts) | **new graph data** (twin-authored, re-based by measurement at build — the 748→1141 precedent): statement ×67 · condition +6 (the IF predicates) · param +2 (@StartDate @EndDate) · edges has_part statement→scope 44, statement→condition 2, condition→condition 4, resolves_to→param 4, uses_param 2. **writers**: `_store_statement_layer` new in aivia/flows/inbound.py (called before the condition layer or via second pass — ambiguity M5-1); R11 renderer in aivia/flows/produce.py; FLOOR_GRAMMAR_VERSION 2.10.0→2.11.0 at the first build slice (the R12 precedent: constant holds until then). **registries**: 1.45.0→1.46.0 via the converter (Shape_Ledger statement counts · Connection_Ledger counted-missing 31 row · Speech_Sources absent row); JSONs regenerate — exempt by location, enumerated at close. **consumers**: sc.ask_console reads NOTHING (ruled-silent — parity gate's absent-check extends to statement; NO new searchable sentences → NO recording run needed) · sc.meaning_console walks the new structure (battery) · sc.fabric_export ships graph_statement.parquet + new has_part rows, AND the F2+F4 fix changes graph_table (pkColumns arrives) + graph_column (values arrives) · sc.graph_visual republishes WITH the new FS1 counts test green first. **served data changes → Sunny's load, ONE refresh for the whole batch, his hand or word.** **answer key**: expected_m_gates.json M5 numbers re-based by measurement if the tree out-counts the twin (the _pin_at_build note anticipates it) |
| ambiguities | M5-1 · M5-2 · M5-4 RULED, M5-3 RESOLVED by investigation (2026-09-17, one at a time, Sunny's words quoted below) — ZERO OPEN |
| debt declared | the 31 operational statements ship with NO downward edge — DECLARED counted-missing (Connection_Ledger row), landing step M6 (file→statement) — the placeholder law satisfied by the counted row + named landing step, standing since the batch plan |
| Sunny's approval | **"approved"** — 2026-09-17, after ruling M5-1/2/4 one at a time, the M5-3 investigation, and re-affirming ruled-silent ("let's leave as is, no searchable statement descriptions for now") |
| closing check | (filled at CLOSED) |

## The ambiguities — Sunny rules each

| id | question | proposal (Sunny may overrule) |
|---|---|---|
| M5-1 | builder ordering: the +6 conditions and +2 params are statement-rooted; the birth-edge law needs statement nodes to exist BEFORE their predicates parent to them. Statement layer runs before the condition layer, or the condition layer gains a second pass? | **RULED (Sunny, 2026-09-17: "build order is the reverse. after scopes")** — the boot sequence is scopes → STATEMENTS → conditions → derived columns: statements after scopes (their birth edge statement—has_part→scope points down at verified nodes) and before conditions (statement-rooted predicates find their parent standing). The containment reads top-down (file→statement→scope, his shape confirmed); the build runs bottom-up per the batch law. One ordering change, no second pass |
| M5-2 | FL8: `"held_statement_rooted": 0` in the condition-layer receipt can never fire (the walker never visits statement predicates). Give it a real value or retire it? | **RULED (Sunny, 2026-09-17: "real value")** — with the M5-1 ordering the walker reaches statement predicates and the counter counts the statement-rooted conditions (expected 6, checked against the key); the receipt's number becomes a measured conservation line, never a constant zero |
| M5-3 | the subkind writer: the estate test asserts twin `subkind == "operational"` but kg2_mapper writes no `subkind` string — WHERE it's written must be located and named before code. If the twin doesn't carry it, who classifies the 31? | **RESOLVED by investigation (2026-09-17, presented to Sunny):** the writer is the TRANSLATOR — kg2_translator stamps `subkind="operational", voiced="never"` from the T-2 RULED list (Sunny 2026-09-06: "operational statement kinds carry no voice"); the twin's census carries the 31. The M5 builder READS the twin's subkind, never re-derives it — one writer, ruled since 09-06; the (b) ruling's "voiced never" is this law carried into the store |
| M5-4 | R11 phrasing — the rule is UNWRITTEN; the 2026-09-10 ruling: suite-first, Sunny gap-checks the wording | **RULED (Sunny, 2026-09-17: "confirmed")** — the R12 arc: §R11 authored DRAFT in Grammar_Floor → pins authored FAILING (byte-exact, test_statement_render) → renderer built → THE 36 RENDERED SENTENCES PRESENTED for his gap-check (a mid-build checkpoint, his eyes before anything ships) → he ratifies phrasing → FLOOR_GRAMMAR_VERSION 2.10.0→2.11.0 (constant held until ratification, the declared-deferral form) |

## Files declared

    aivia/flows/inbound.py
    aivia/flows/produce.py
    aivia/flows/export_graph.py
    AIVIA_Design/registries/convert_from_xlsx.py
    AIVIA_Design/Grammar_Floor.md
    AIVIA_Design/Contract_Logic_Layer.md
    AIVIA_Design/Contract_Technical_Layer.md
    AIVIA_Design/Contract_Surfaces.md
    AIVIA_Product/estates/ed_sepsis_dev/expected_m_gates.json
    AIVIA_Test/test_ed_sepsis_dev_estate.py
    AIVIA_Test/test_speech_parity.py
    AIVIA_Test/GQL_Gates.md
    tests/aivia/test_statement_render.py
    tests/aivia/test_statement_layer.py
    tests/aivia/test_shape_census.py
    tests/aivia/test_connection_census.py
    tests/aivia/test_metamodel.py
    src/zones.py
    AIVIA_Test/test_meaning_console.py
    docs/architecture/TEST_MAP.md
    tests/aivia/test_derived_render.py
    tests/aivia/test_produce.py
    tests/aivia/test_graph_export.py
    tests/aivia/test_visual_counts.py
    devtools/graph_visual/generate_m1.py

(Regenerated registry JSONs are exempt by location — AIVIA_Design/ —
and are enumerated in the closing diff. Amending this list after
approval needs Sunny's word, per H5. AMENDED twice, both gate catches: tests/aivia/
test_statement_layer.py added with Sunny's "yes" 2026-09-17 —
THE HARD GATE's first live catch (the M4 precedent file split
under-declared); tests/aivia/test_shape_census.py added with his
"approve the shape census file" same night — the gate's third
catch (its stale "statement is TARGET" pin must evolve with the
batch; the second catch, aivia/flows/speech.py, turned out NOT
NEEDED — the census reads index labels only, so the gate stopped
an assumed edit that verification then disproved. AMENDED a
third time with Sunny's "yes" (2026-09-17, the full-suite
triage): five evolution files — connection-census pin (statement
= the declared missing kind), metamodel version pin 1.46.0,
src/zones.py (.claude became TRACKED at commit 48433c1 — the
zone gate's catch, not M5's doing), the two console param pins
2→4, TEST_MAP.md regen. AMENDED a fourth time, his "yes": the
two standing grammar-version pins (test_derived_render :245 ·
test_produce :86) move 2.10.0→2.11.0 with the ratification — the
conscious-bump mechanism, the R12 arc's same two files.)

## Build order (after APPROVED)

1. M5-3 investigation presented (the subkind writer named).
2. Registry rows via the converter (1.46.0) — Shape/Connection/
   Speech rows.
3. Tests FIRST, authored failing: R11 pins (test_statement_render)
   · export list/dict pins (test_graph_export) · FS1 counts pins
   (test_visual_counts) · parity absent-extension · the M5 battery
   already stands (test_m5_key_matches_twin).
4. §R11 drafted in Grammar_Floor → the 36 renders presented →
   Sunny ratifies phrasing → FLOOR_GRAMMAR_VERSION 2.11.0.
5. Code: the ordering change + `_store_statement_layer` (M5-1) ·
   the counter (M5-2) · the export fix (F2+F4, the one separator).
6. Full suite + ruff · export regen (byte-identical prior files
   except the three the fix touches + the new statement parquet).
7. Sunny's load + ONE refresh · §M5 gates run on the served graph ·
   the visual republishes (FS1 test green BEFORE) · close with the
   declared-vs-actual diff; dc.statement flips TARGET→LIVE and the
   contract stamps move same breath.
