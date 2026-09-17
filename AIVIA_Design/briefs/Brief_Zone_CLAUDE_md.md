# Brief_Zone_CLAUDE_md — classify CLAUDE.md in the zone gate

**Status: CLOSED** (built + full suite green 2173/0, 2026-09-17 just past midnight)

| field | content |
|---|---|
| class | fix — the repo drifted from the zone law (every top-level tracked path is classified governed or internal); CLAUDE.md was born in commit 0ce7de0 (2026-09-16) AFTER the last green suite run, with no GOVERNED_ENTRIES row; the tripwire (test_zones + test_trace_registry, 2 pins) caught it on tonight's full run |
| claims | src/zones.py GOVERNED_ENTRIES — CLAUDE.md joins README.md / CHANGELOG.md / LICENSE as a governed top-level doc (it is the harness-loaded session contract) |
| impacts (computed) | ONE line in src/zones.py; no registry, no served data, no export, no generated doc (generate_docs.py does not read zones.py — verified); the 2 red pins flip green, no new test needed (the existing pins ARE the acceptance test) |
| ambiguities | none — "governed" is the only sensible class for a checked-in root doc; under the retired P3 lane this would have skipped the brief, H2(c) requires it |
| debt declared | none |
| Sunny's approval | **"yes"** — 2026-09-16 late (combined word with the TEST_MAP list amendment) |
| closing check | **BALANCED** — files changed == the two declared (src/zones.py one line; this brief). The 2 red pins (test_zones + test_trace_registry) flipped green; no generated doc moved (verified) |

## Files declared

    src/zones.py
    AIVIA_Design/briefs/Brief_Zone_CLAUDE_md.md
