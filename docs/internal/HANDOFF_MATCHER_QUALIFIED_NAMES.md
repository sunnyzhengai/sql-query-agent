# Handoff — matcher must key on bare names (schema-qualified ids broke it)

**From:** review session, 2026-08-18 (live work failure). **To:** dev
session — flagged while you are mid-flight on the 07b split; this is a
separate small fix in collibra_lineage_match.

## Field failure

metric_ids are schema-qualified since the 00b identity fix (2026-08-17).
extract_match_key() assumes bare object names: at work,
"COOK_RPT.USP_AMB_NHC_BH_APPT_PBI" produced key 'rpt.usp amb nhc bh appt'
→ 128 unmatched reports, and junk keys fed the fuzzy scorer garbage
matches with implausible 1.00 scores (ComplexCarePDN → "Admission
Documentation Report"). Sunny's cell-5 review caught it pre-publish.

## Wanted

1. In extract_match_key: `name = name.rsplit(".", 1)[-1]` before suffix
   logic (key = bare object name, ADR 0020 bareName).
2. Test: qualified and bare forms of the same name produce identical
   keys; qualified non-_PBI returns None. (Draft test text exists in this
   file's git history sibling — or just write:
   extract_match_key("COOK_RPT.USP_X_PBI") == extract_match_key("USP_X_PBI").)
3. While in there: investigate why the fuzzy scorer emitted 1.00 for
   unrelated names when fed junk keys — a score ceiling/normalization bug
   may be hiding independently of the qualification issue.

## Also confirmed live (context for the 07b work in flight)

- Data Agent refusal phrasing "I don't have information about" evaded
  REJECT_PHRASES — structural refusal detection / the status=rejected
  contract you are building is the right cure, plus the CANARY gate
  (one known-metric probe before an N-hundred-call run; refuse to start
  on a refusal). Root cause at work was agent DATA SOURCES stale while
  instructions were fresh — the canary catches exactly that class.
