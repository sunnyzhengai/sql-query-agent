"""OPERATIONS ARE THE PRODUCT — the methodology manifest (ADR 0036).

This module is the machine-readable constitution. The methodology
tests (tests/test_methodology.py) enforce it against the CODE on every
run — the same mechanism as the table contracts, aimed at the failure
mode this project hit three times: pattern predefinition sneaking back
into the control path in a new disguise.

AMENDMENT RULE: changing ANYTHING in this file is a methodology
amendment. It requires (a) an ADR reference in the entry itself and
(b) Sunny's explicit approval — Claude must never modify this file
silently as a side effect of making a test pass. The tests make
bypasses LOUD; the regulator makes them legitimate. (No guard fully
binds its own author — the root of trust is the loop itself:
translated by LLM, regulated by human, applied to this repo.)
"""

FOUR_LINES = (
    "Data can be operated on three ways: search (semantic|exact), "
    "retrieve, update — plus three compare kernels over results.\n"
    "The LLM translates questions into plans of those operations.\n"
    "The human regulates — every decision visible, confirmable, "
    "interceptable.\n"
    "Everything displays — results are the answer; prose is the caption."
)

# --- the closed operation registry ------------------------------------
# Adding an operation REQUIRES an entry here with a data-shaped
# justification and an ADR. The test fails on any op_* function in the
# control path that is not registered — additions are loud by design.

PRIMITIVES = {
    "op_search": {
        "kind": "primitive",
        "data_shaped_because": "the store admits lookup by meaning "
                               "(vector) and by literal identity — two "
                               "modes of one find operation",
        "adr": "0036",
    },
    "op_retrieve": {
        "kind": "primitive",
        "data_shaped_because": "the store admits reading a record by id",
        "adr": "0036",
    },
    "op_census": {
        # AMENDMENT 2026-08-20 (field find, web-UI test): "how many
        # metrics" was planned as a name-search for the word "metrics" —
        # kind words are categories; enumeration is its own primitive.
        "kind": "primitive",
        "data_shaped_because": "the store partitions the catalog by a "
                               "closed kind column; enumerating one kind "
                               "is a complete, exact-count scan",
        "adr": "0036",
    },
    "op_lineage": {
        # AMENDMENT 2026-08-21 (walk find 4, Sunny's verdicts file):
        # 'using' is the READER relation — lineage questions were
        # routing to a mention-census. Promoted from the reachability
        # roadmap with a walk corpse attached.
        "kind": "primitive",
        "data_shaped_because": "the graph materializes the uses "
                               "relation as transform_to_technical "
                               "edges; readers-of-table is a complete, "
                               "exact-count scan of parsed lineage, "
                               "never name matching",
        "adr": "0052",
    },
    "op_compare": {
        "kind": "kernel-dispatch",
        "data_shaped_because": "comparisons range over exactly four "
                               "data types (text bodies, sets, scalars, "
                               "ordered step sequences) — one kernel "
                               "per type, typed by data not by question",
        # AMENDMENT 2026-08-18 (ADR 0043): the step-alignment kernel
        # joins the dispatch — approved via HANDOFF_COMPARISON_SHAPE
        # (Question Map gap 1, Layer 0 approved by Sunny) and Sunny's
        # go-ahead on the implementation order the same day.
        "adr": "0036, 0043",
    },
    "op_traverse": {
        "kind": "primitive",
        "data_shaped_because": "the store admits following edges; join "
                               "and transitive closure are the depth-1 "
                               "and depth-* cases of one operation",
        "adr": "0037",   # approved by Sunny 2026-08-13; not yet built
    },
    "op_resultset_kernels": {
        "kind": "kernel-dispatch",
        "data_shaped_because": "full local relational algebra (filter/"
                               "project/sort/group/set-join) over "
                               "DISPLAYED result sets only — operates "
                               "on visible data, never fetches",
        "adr": "0037",   # approved by Sunny 2026-08-13; not yet built
    },
    # "op_update": ADR 0036/0038 — always plan-confirmed, never
    # autonomous; first use case: proposed_by_user definitions.
    # GATED on the access-control ADR (0038 §4) before implementation.
}

# --- the control path --------------------------------------------------
# Files whose code DECIDES what answers contain. The vocabulary and
# import rules below apply to these files. Adding a control file is an
# amendment (register it here).

CONTROL_PATH_FILES = (
    "src/orchestrator/ops.py",
    # AMENDMENT 2026-08-21 (ADR 0051): protocol.py DELETED — the
    # three-call plan protocol's minds retired; the one-mind engine
    # (below) is the read-path control surface. agent.py remains the
    # ADR 0035 MCP-surface loop pending its adoption of the engine.
    "src/orchestrator/agent.py",
    # AMENDMENT 2026-08-20: the caption gate (spec:E6 mechanical) —
    # control-path by nature (it floors captions), subject to the same
    # no-lexicon scan; its checks are single regex patterns, the
    # description-gate idiom.
    "src/orchestrator/caption_gate.py",
    # AMENDMENT 2026-08-21 (ADR 0051): the one-mind turn engine — THE
    # control path for the read surfaces; invariants-only prompt,
    # subject to the no-casebook scan like everything above it.
    "src/orchestrator/turn_engine.py",
)

# --- system vocabulary -------------------------------------------------
# The ONLY literal string collections allowed in control-path code:
# names of OUR system's parts (modes, ops, aspects, edge types, tool
# names). Collections of USER-ENGLISH (phrase lexicons, quantifier
# lists, filler words) are pattern predefinition and are banned — the
# methodology test fails on any control-path literal collection whose
# elements are not registered here. Registering English phrases here
# to "make the test pass" is a silent amendment — forbidden above.

SYSTEM_VOCAB = frozenset({
    # search modes (ADR 0036)
    "semantic", "exact",
    # compare aspects that name SYSTEM fields/kernels, not user phrasings
    # ("steps": ADR 0043 amendment 2026-08-18 — the step-alignment kernel)
    "logic", "definition", "sql", "content", "tables", "source_tables",
    "steps",
    # edge types (graph contract)
    "canonical_to_transform", "transform_to_transform",
    "transform_to_technical",
    # AMENDMENT 2026-08-22 (ADR 0053): projection-grain column edges
    "transform_to_column",
    # tool/op names appearing in dispatch tables and basis stamping
    # ("census"/"list_catalog": AMENDMENT 2026-08-20 — the enumeration
    # primitive; catalog kinds are SYSTEM vocabulary, not user phrasing)
    # "lineage": AMENDMENT 2026-08-21 (walk find 4) — the readers-of-
    # table primitive; an op name, not user phrasing
    "search", "retrieve", "update", "compare", "explain", "census",
    "lineage",
    "search_catalog", "find_by_name", "get_facts", "list_steps",
    "check_same_logic", "list_catalog",
    "metric", "step", "term", "report", "measure",
    # catalog row FIELD names scanned by the row_mentions predicate
    # (AMENDMENT 2026-08-21, 1.50.4: the topic-filtered census must
    # scan exactly the fields its stamped universe sentence names —
    # these are OUR schema's column names, not user phrasings;
    # of_metric joined 1.50.7 — a step's parent ref is part of its
    # identity, and the universe sentence names it)
    "name", "business_name", "description", "of_metric",
})

# --- the prompt budget -------------------------------------------------
# Instruction creep is pattern predefinition in prose. The system
# prompt is capped; raising the budget is an amendment. Quoted example
# phrasings inside the prompt are capped separately — examples steer,
# casebooks predict.

PROMPT_LINE_BUDGET = 60
PROMPT_QUOTED_EXAMPLES_BUDGET = 12

# --- observation is not control ----------------------------------------
# Language lexicons are permitted ONLY in observation modules (they
# watch, they never decide an answer). This list is the exhaustive set
# of modules allowed to hold user-English word collections.

OBSERVATION_FILES = (
    "src/orchestrator/events.py",      # decision_shape telemetry
)
