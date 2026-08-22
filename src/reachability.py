"""The reachability contract (ADR 0052) — spec:C1 applied to the
ask-surface.

Sunny's ruling (2026-08-21): the graph held 6,528 nodes and the
ask-surface reached 472 — 7% — and NOBODY DECIDED THAT. It happened
layer by layer: decisions, columns, report edges landed in the graph
with no op to the ask-surface and no exclusion row — an undeclared
frontier discovered by a human tripping over it ("how is IP_SEPSIS
defined"), the EMR-joins incident recurring one level up.

The contract: every graph payload — each NodeLayer, each EdgeType,
each catalog kind — carries exactly one row here, and each row is one
of two honest things:

  reachable  — names the engine op(s) and the query constant or op
               source that touches it, with a MARKER string the test
               verifies against the actual implementation text; a row
               that claims reach the code doesn't implement fails CI.
  excluded   — names the reason and (where ruled) the queue position.
               An exclusion is a decision on record, never an
               accident.

Adding a NodeLayer, EdgeType, or catalog kind without a row here
fails the totality test — a layer can no longer land in the graph
invisible by accident. The audit that found the 7% is now a query
that cannot rot.
"""

# Each row:
#   payload  unique key: "node:<layer>[:<subkind>]", "edge:<type>",
#            or "catalog:<kind>"
#   status   "reachable" | "excluded"
#   via      human sentence: how the ask-surface reaches it (reachable)
#   ops      op/function names in src.orchestrator.{ops,tools} whose
#            SOURCE must contain the marker (reachable; optional)
#   queries  query-constant names in src.orchestrator.tools whose TEXT
#            must contain the marker (reachable; optional)
#   marker   the discriminating string tied to this payload
#   reason   why not, and what's queued (excluded)

REACHABILITY = (
    # --- nodes --------------------------------------------------------
    {"payload": "node:canonical", "status": "reachable",
     "via": "catalog search/census (kind metric) + full retrieve",
     "ops": ("op_retrieve",), "queries": (),
     "marker": "assemble_metric"},
    {"payload": "node:transformation", "status": "reachable",
     "via": "catalog search/census (kind step) + step retrieve with "
            "fragments",
     "ops": ("op_retrieve",), "queries": (),
     "marker": "transform:"},
    {"payload": "node:technical:table", "status": "reachable",
     "via": "source-table identity stamped on any honest-empty result "
            "holding a table-like phrase (1.50.7); no first-class "
            "census yet",
     "ops": (), "queries": ("TABLE_USED_BY_QUERY",),
     "marker": "tech:"},
    {"payload": "node:technical:column", "status": "excluded",
     "reason": "queued third in Sunny's 2026-08-21 order — the "
               "blast-radius op ('which metrics touch PATIENTMRN'); "
               "columns appear today only inside displayed SQL "
               "fragments"},
    {"payload": "node:decision", "status": "reachable",
     "via": "INLINE on metric records (top sites + exact total, M2 "
            "design pass 2026-08-21) and full sites on step retrieve "
            "— context, predicate count, PHI-redacted expression",
     "ops": ("_shape_decision",),
     "queries": ("DECISIONS_OF_METRIC_QUERY", "DECISIONS_OF_STEP_QUERY"),
     "marker": "decision"},
    {"payload": "node:report", "status": "reachable",
     "via": "catalog search/census + full retrieve with parsed TMDL "
            "links (ADR 0052 backfill item 2, landed 2026-08-21)",
     "ops": ("op_retrieve",), "queries": ("LINKS_OF_REPORT_QUERY",),
     "marker": "report"},
    {"payload": "node:measure", "status": "reachable",
     "via": "catalog search/census + full record retrieve (DAX "
            "expression, PHI-gated at export per ADR 0040)",
     "ops": ("op_retrieve",), "queries": (),
     "marker": "measure:"},

    # --- edges --------------------------------------------------------
    {"payload": "edge:canonical_to_transform", "status": "reachable",
     "via": "metric retrieve lists its steps; step census carries "
            "of_metric",
     "ops": ("op_retrieve",), "queries": ("STEPS_OF_QUERY",),
     "marker": "step"},
    {"payload": "edge:transform_to_transform", "status": "excluded",
     "reason": "step lineage chains (which steps feed step X) have no "
               "traversal op; not yet queued — surface with the "
               "column work if Sunny orders it"},
    {"payload": "edge:transform_to_technical", "status": "reachable",
     "via": "source-table identity resolution (1.50.7)",
     "ops": (), "queries": ("TABLE_USED_BY_QUERY",),
     "marker": "transform_to_technical"},
    {"payload": "edge:table_to_column", "status": "excluded",
     "reason": "queued with the column work (third in Sunny's "
               "2026-08-21 order)"},
    {"payload": "edge:step_to_decision", "status": "reachable",
     "via": "step retrieve traverses it to attach decision sites",
     "ops": (), "queries": ("DECISIONS_OF_STEP_QUERY",),
     "marker": "step_to_decision"},
    {"payload": "edge:decision_to_column", "status": "excluded",
     "reason": "decision→column blast radius; queued with the column "
               "work"},
    {"payload": "edge:decision_to_step", "status": "excluded",
     "reason": "decision→step filter-through lineage; queued with the "
               "column work"},
    {"payload": "edge:report_to_canonical", "status": "reachable",
     "via": "both directions: metric retrieve lists reports; report "
            "retrieve lists executed metrics",
     "ops": ("op_retrieve",),
     "queries": ("REPORTS_OF_METRIC_QUERY", "LINKS_OF_REPORT_QUERY"),
     "marker": "report_to_canonical"},
    {"payload": "edge:report_to_technical", "status": "reachable",
     "via": "report retrieve lists DirectLake-read tables",
     "ops": (), "queries": ("LINKS_OF_REPORT_QUERY",),
     "marker": "report_to_technical"},
    {"payload": "edge:report_to_measure", "status": "reachable",
     "via": "report retrieve lists its measures",
     "ops": (), "queries": ("LINKS_OF_REPORT_QUERY",),
     "marker": "report_to_measure"},
    {"payload": "edge:measure_to_column", "status": "excluded",
     "reason": "measure→column lineage; queued with the column work"},
    {"payload": "edge:uses_table", "status": "excluded",
     "reason": "materialized metric→table closure unused by the "
               "ask-surface — table identity resolves live via "
               "transform_to_technical instead (1.50.7)"},

    # --- catalog kinds ------------------------------------------------
    {"payload": "catalog:metric", "status": "reachable",
     "via": "search all modes, census, retrieve", "ops": (),
     "queries": (), "marker": ""},
    {"payload": "catalog:step", "status": "reachable",
     "via": "search all modes, census (of_metric filter), retrieve",
     "ops": (), "queries": (), "marker": ""},
    {"payload": "catalog:term", "status": "reachable",
     "via": "search/census (kind legal; 0 rows in this corpus)",
     "ops": (), "queries": (), "marker": ""},
    {"payload": "catalog:report", "status": "reachable",
     "via": "search/census; depth queued (see node:report)",
     "ops": (), "queries": (), "marker": ""},
    {"payload": "catalog:measure", "status": "reachable",
     "via": "search/census; depth queued (see node:measure)",
     "ops": (), "queries": (), "marker": ""},
)


def rows_for(prefix: str) -> "list[dict]":
    return [r for r in REACHABILITY if r["payload"].startswith(prefix)]
