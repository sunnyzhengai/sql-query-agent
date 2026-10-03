"""Phase 07 — business descriptions, THE ELOQUENT MACHINE.

Contract: AIVIA_01_Design/07_business_descriptions_data_contract.md
(APPROVED 2026-10-03). The second of the two machines: an LLM
PROPOSES, a NO-MODEL MECHANICAL GATE verifies every claim against
stored rows, Sunny BLESSES. The floor (the 06 technical sentence)
ships whenever nothing blessed or gate-passed exists — stiff is
allowed, lying is not.

Dry-run evidence: AIVIA_01_Design/dryruns/phase_II_uses_phase_I.md
(14 real calls, 5 rounds, converged round 5). The style grammar
S1-S11 and the gate checks G-1..G-7 are ruled design law.
"""

# ==== L03/L04 PSEUDO CODE — awaiting Sunny's approval ===============
# (standing process: real code lands below only after her stamp;
# the tests are red now. L02's registry seed is staged separately
# for her ratifying hand.)
#
# BASIS_VERSION = "07.1.0" — the 07 grammar constant: the S-rule
#   wording, the plain-word lexicon, the budgets. Any change bumps
#   and re-pins.
#
# THE DOCKET (per node — everything the proposer may know, and
# the ONLY thing the whitelist trusts):
#   file grain:  the 06 file sentence + its scope sentences + the
#     file's ledger slice (the boundary of the known) + the
#     parameter lines.
#   scope grain: the 06 scope sentence + its condition rows.
#   field grain: the owning scope sentence + the field's defining
#     phrase via the IMPORTABLE 06 renderers (G2a — 06 stays
#     closed).
#
# THE GATE (G-1..G-7, contract law, zero model):
#   G-1 LEXICAL WHITELIST: lowercase word tokens of audience_text;
#     every CONTENT token must appear in docket text, 02 words,
#     the blessing registry, or THE PLAIN-WORD LEXICON — a CLOSED,
#     versioned list in this file (function words + ruled business
#     words like report/data/shows); growth is a ruled row, never
#     silent. Numbers and quoted literals must appear in the
#     docket verbatim. Fail NAMES the token (the semicolon
#     killer).
#   G-2 BANNED (S2): join select query table temp column
#     procedure parameter, @tokens, raw codes (digit tokens not
#     in the docket).
#   G-3 BUDGETS (S8): per-grain sentence counts and <=15 words
#     per sentence; max one parenthetical; no nesting.
#   G-4 TEMPLATE (S7): file grain = exactly the four labeled
#     lines (Who's in it / Each row shows / Time window /
#     Excludes), nothing else.
#   G-5 ANCHORS (S4): restriction verbs (only/excludes/limited/
#     restricted) must anchor to Population or WHERE docket
#     lines; attachment claims to attachment lines.
#   G-6 MUST-SAY (three members): the gap echo (files whose
#     ledger slice carries dynamic_sql_gap), the window (files
#     whose docket carries population-shaping parameters), the
#     Excludes line (files whose docket carries exclusions).
#   G-7 S10 UNBOUND CODES: no bare code in prose; every sighting
#     RECORDED to 07_code_sightings.json (table.column + code +
#     node) — the dictionary-growth flywheel's second engine.
#   gate(audience_text, docket, grain) -> findings list; empty ==
#   pass. Deterministic, byte-testable, fixtures = the dry run's
#   RECORDED REAL outputs.
#
# THE PROMPT CONSTRUCTOR (deterministic, byte-pinned): the ruled
#   SYSTEM text (truth rules + S-rules verbatim from the design)
#   + the per-grain instruction (S7 template for file; budgets
#   for scope/field) + the docket. Repair rounds append the
#   NAMED findings. No concrete example sentences ever ride in a
#   prompt (the prompt-examples-are-data law).
#
# THE PROPOSER LOOP (the only paid path; build-time only):
#   round 1 propose -> gate; findings -> repair round (budget 3,
#   ruled); still failing -> status floor, LAST findings kept on
#   the row. Local seat gpt-5-mini; production gpt-5.4-mini
#   (parity law at the move).
#
# THE EFFECTIVE LADDER (ported law): blessed (registry, Sunny's
#   hand) > gate_passed > floor (the 06 sentence verbatim).
#
# build07(dir05, dir06, out07, dir02, no_llm=False):
#   dockets for every file + scope + field node -> one sheet row
#   each (CONSERVATION: exactly one row per docket node, a test);
#   no_llm=True renders floor-only rows deterministically (the
#   suite's path; zero cost); writes 07_business_sheet.json, the
#   per-file texts (status marks per line), 07_code_sightings
#   .json. The registry is READ-ONLY to the build — a byte-
#   identity test enforces it.
# ====================================================================
