# F1 — minimal estate (the first fixture of the build)

Two synthetic dictionary snapshots (sources `simemr` and `org`,
sharing one db) plus the HAND-AUTHORED expected graph — written
before any builder exists (protocol step 4; the answer-key law).

What F1 witnesses, by check:
- LC-C1 (create from extract), LC-C2 (keyless tables -> gap rows),
  LC-S3 / CHECK-TL-3 (idempotent rebuild)
- INTAKE-0..7 pass on both snapshots; the dedup assertion
- Contract §6 join grouping: fk_num groups, ordinal orders — one
  single join, one composite, one DEDUPED double-declared value
  link, one legal cross-source join (INTAKE-6)
- Contract §4 phrase rules, opportunistic: three tables hit
  (business_name + grain + pk, incl. a composite pk from prose),
  four gap-listed — never guessed
- Values via the declared join to a value table; keys as strings
- A1 witness: one db node, registration-owned, though two extracts
  declare it
- A2 witness: identities are (source, schema, table[, column]);
  the db name appears in no identity

Format note: this fixture PINS extract file format v0.1
(manifest.json + tables/columns/joins/values CSVs with these
headers) — the deferred "file-format minutiae" now has its first
binding, decided by the fixture as intended.
