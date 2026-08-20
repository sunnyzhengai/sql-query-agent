# Answer-key re-certification — 1.30.0 (for Sunny's sign-off)

**What changed:** two parser-walker fixes in `scriptdom_fabric.py`
(1b item 8): (a) .NET indexer properties excluded from reflection
(the 13,156-suppression counter was pure indexer noise — measured:
ZERO structural change from this fix alone); (b) the generic walker's
depth cap raised 15 → 60 **and cutoffs now counted** — the old cap was
an uncounted third bucket that silently dropped deeply nested
subtrees.

**Why you can trust the new numbers:**
1. **All gains, zero losses** — every changed proc strictly adds reads;
   nothing previously asserted was retracted (6 of 28 procs changed).
2. **The trace validates it**: TRACE_USP_ED_SEPSIS.md's independently
   hand-derived expectation was 48 reads; the old extractor found 45
   (the 3 misses were filed as a known gap). The fixed extractor finds
   exactly the 48 — including MED_MIX_COMPONENTS and both
   SEPSIS_STAGING tables. The gap class is CLOSED.
3. Fixtures re-recorded LOCALLY via the native parser (full fragments,
   0 truncated of 417; anonymization scan clean) — legal because the
   native-parser law makes local parse == Fabric parse.

**Oracle deltas (REMATCH answer key):**

| Oracle | Old | New | Cause |
|---|---|---|---|
| readers of HOSPITAL_ENCOUNTERS | 13 | 13 | unchanged |
| readers of MEDICATION_ORDERS | 7 | 8 | a deep mixture-subquery read recovered |
| tables of reports.USP_Severe_Sepsis | 32 | 35 | +DM_ICU_STAY, +MED_MIX_COMPONENTS (+schema variant) |
| tables of reporting.USP_ED_Sepsis | 38 | 47 | deep dep-chains recovered (the trace's 3 named misses among them) |
| tables of reports.USP_ED_Sepsis | 29 | 47 | same class — 18 gained targets, 0 lost (list verified) |
| CALCULATED_BY steps, Severe_Sepsis | 88 | 121 | step closure now reaches subtrees the depth cap cut |

**Also surfaced (newly-seen reads → dictionary check):** run 500's
leaf grounding after sync; newly recovered reads may include
undictionaried tables (e.g. DM_ICU_STAY) — the C4 verdict will name
them.

**Sign-off:** if any delta looks wrong to your read of the SQL, say so
and the specific oracle reverts pending investigation.
