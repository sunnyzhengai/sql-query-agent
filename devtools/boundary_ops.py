"""The boundary echo contract (ordered 2026-08-27; the Echo Law's
third silent-ignore instance made the class general).

"An acknowledgment is a claim; only the postcondition is a fact."

Every devtool operation that crosses the tenant boundary — create,
publish, override, rename, load, delete — is enumerated here and
PAIRED with a declared, observable postcondition, or is
exempt-with-reason. The 0052 pattern applied to SIDE EFFECTS:
totality + fidelity live in tests/test_boundary_ops.py (a new
boundary op without a row is a red build; a row claiming a witness
the source doesn't implement is a red build). Runners refuse to
advance past an unwitnessed postcondition — the three hand-made
verifies that proved the class (shortcut create-then-verify, the
chain lakehouse tripwire, the write read-back) are entries here,
not specials. This registry is the updater's skeleton.
"""

from __future__ import annotations

# modules whose every tenant-crossing op must carry a row below
BOUNDARY_MODULES = (
    "devtools.create_kql_shortcut",
    "devtools.shapes_tenant_load",
    "devtools.run_shapes_chain",
    "devtools.publish_environment",
)

BOUNDARY_OPS = (
    {"module": "devtools.create_kql_shortcut",
     "op": "create_and_verify", "kind": "create",
     "postcondition": "the QUERY PATH answers a count (mount "
                      "witnessed); on timeout the ghost is DELETED "
                      "and the failure is loud",
     "witness_marker": "now VERIFYING the query path"},
    {"module": "devtools.shapes_tenant_load",
     "op": "ol_write", "kind": "load",
     "postcondition": "read-back length equals written length (the "
                      "flush 200 alone once left a file untouched)",
     "witness_marker": "read back"},
    {"module": "devtools.run_shapes_chain",
     "op": "run_notebook", "kind": "override",
     "postcondition": "job status polled to Completed; the lakehouse "
                      "override is witnessed by the post-first-write "
                      "tripwire (a silent-ignore ran 4 notebooks "
                      "against the wrong store)",
     "witness_marker": "Completed"},
    {"module": "devtools.run_shapes_chain",
     "op": "assert_profile_took", "kind": "override",
     "postcondition": "the written table exists in the TARGET "
                      "lakehouse or the chain aborts",
     "witness_marker": "TRIPWIRE"},
    {"module": "devtools.run_shapes_chain",
     "op": "load_tables", "kind": "load",
     "postcondition": "load operation polled to Completed; capacity "
                      "rate limits retried, never silently dropped",
     "witness_marker": "Completed"},
    {"module": "devtools.run_shapes_chain",
     "op": "verify", "kind": "create",
     "postcondition": "the four-way store verification (flat "
                      "columns, cluster count, semantic_search, the "
                      "W4 link) — the chain's own exit gate",
     "witness_marker": "flat surface incomplete"},
    {"module": "devtools.publish_environment",
     "op": "main", "kind": "publish",
     "postcondition": "EXEMPT-WITH-REASON: the publish state machine "
                      "is printed for a human watcher, and the "
                      "publish CLICK itself is Sunny's (classifier-"
                      "blocked for dev); the wheel's arrival is "
                      "witnessed downstream by every notebook's "
                      "REQUIRES_ENGINE floor — a stale publish dies "
                      "loudly at the next run's first cell",
     "witness_marker": None},
)
