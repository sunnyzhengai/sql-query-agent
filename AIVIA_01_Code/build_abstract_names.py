# build_abstract_names.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/03_chat_bot.md L03 (the name-abstract list)
# Contract: AIVIA_01_Design/03_chat_bot_data_contract.md (Output File 2:
#           03_chat_abstract_names.json)
# Tests:    AIVIA_01_Test/test_03_chat_bot_data_contract.py (born with
#           this build, RED first)
#           Sunny's gap-check of the real output is the acceptance gate.
#
# PURPOSE. Build lane 2's data asset: for EVERY table and EVERY column
# in the phase 02 sheets, an LLM-written short abstract and synonym
# list — searched lexically by the funnel, never embedded (ruled).
#
# ---------------------------------------------------------------------
# INPUTS AND OUTPUT
# ---------------------------------------------------------------------
#   in:  the phase 02 sheets dir (table.json, column.json — name and
#        stored description; read through dictionary_graph.load_sheets,
#        the one door to the sheets)
#   out: AIVIA_01_Data/03_chat_bot/03_chat_abstract_names.json
#        rows (contract): object_kind (table|column), object_id,
#        object_name, abstract, synonyms[],
#        sunny_abstract (blank = script's stands),
#        sunny_synonyms[] (additions, never removed by the script)
#
#   FINGERPRINT SKIPPED (Sunny's ruling, 2026-09-30): no
#        source_fingerprint field for now. Consequence, ruled-for-now
#        posture: REUSE IS BY KEY — a row that exists for
#        (object_kind, object_id) is reused verbatim; only NEW objects
#        generate. A changed description does NOT regenerate its
#        abstract until the fingerprint (or another mechanism) is
#        ruled in later. This keeps reruns cheap and Sunny's
#        gap-checked abstracts stable; the staleness risk is accepted
#        and recorded here. Full regeneration remains available by
#        deleting the output file and rerunning (~83 calls, under a
#        dollar).
#
# ---------------------------------------------------------------------
# THE LLM CALLS (gpt-5-mini, the pinned CHAT_MODEL constant)
# ---------------------------------------------------------------------
#   - batched: ~20 objects per call, structured JSON output (the API's
#     json response format), validated per object: non-empty abstract,
#     synonyms a list of strings; a malformed object fails loudly
#     naming it, never silently skipped.
#   - per object the call carries: kind, full name (columns as
#     TABLE.COLUMN so the table context informs the abstract), and the
#     stored description (truncated at a ruled length, e.g. 1,000
#     chars — the long DATE_DIMENSION-style descriptions don't need
#     full text to abstract).
#   - the prompt teaches the SHAPE abstractly — what an abstract and a
#     synonym are for a data-dictionary object — and carries NO example
#     objects (prompt-examples-are-data law; no hardcoded examples).
#   - full first run: 38 + 1,618 = 1,656 objects, ~83 calls — an
#     announced cost (gpt-5-mini: well under a dollar), Sunny's hand.
#
# ---------------------------------------------------------------------
# THE THREE LAWS (test-locked)
# ---------------------------------------------------------------------
#   REUSE (by key, per the fingerprint skip): existing rows keyed
#     (object_kind, object_id) are reused verbatim; only new objects
#     generate. Census prints generated-new vs reused.
#   SUNNY PRESERVATION: sunny_abstract / sunny_synonyms[] are carried
#     over by key on EVERY rebuild, including when the script's own
#     fields regenerate. A rebuild that loses one is a test failure
#     (the contract's exact words).
#   COVERAGE (completion integrity): after the build, every table and
#     column in the sheets has exactly one row. Missing = counted and
#     named, build fails loudly. Rows for objects no longer in the
#     sheets are DROPPED and counted in the census (with their sunny_*
#     content echoed in the census so nothing vanishes silently).
#
# ---------------------------------------------------------------------
# ENTRY POINT + CLI (the command Sunny runs)
# ---------------------------------------------------------------------
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/build_abstract_names.py \
#       AIVIA_01_Data/02_emr_data_dictionary \
#       AIVIA_01_Data/03_chat_bot
#   Both paths are parameters (the law). Prints the census: rows per
#   kind, generated vs reused, dropped objects, sunny_* rows carried,
#   coverage OK/failures. The LLM client reads OPENAI_API_KEY from
#   .env, same door as the embedder.
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (red first, in NEW test_03_chat_bot_data_contract.py;
# tiny synthetic sheets so the paid calls stay pennies)
# ---------------------------------------------------------------------
#   - coverage: every synthetic table/column gets a row with a
#     non-empty abstract and list-typed synonyms; a sheet object the
#     LLM response omits fails loudly.
#   - reuse: a second run with unchanged sheets makes ZERO LLM calls
#     (forbidden-caller embedder pattern, carried over).
#   - new object: adding one synthetic column generates THAT row only;
#     the census counts 1 new, rest reused. (Description-change
#     regeneration is deferred with the fingerprint — no test pins it;
#     this comment is the recorded debt.)
#   - sunny preservation: hand-writing sunny_abstract/sunny_synonyms
#     into the output, then rebuilding, keeps the sunny_* fields
#     verbatim.
#   - drop: removing a synthetic column from the sheets drops its row
#     and counts it; its sunny_* content appears in the census echo.
#   - the prompt contains no object examples (a test greps the prompt
#     constant for the synthetic names — none may appear).
