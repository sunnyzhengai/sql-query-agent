"""Generate CTE + metric descriptions locally over the recorded fixtures.

Usage:
    python devtools/describe_local.py            # incremental (cache-aware)
    python devtools/describe_local.py --limit 5  # first N metrics' steps only (smoke run)

The first pass of ADR 0019: live OpenAI-compatible calls (OPENAI_API_KEY in
.env), leak-gated before anything is written. Outputs, both gitignore-safe
derived data from the ALREADY-ANONYMIZED fixtures:

    tests/fixtures/recorded/description_cache.json  (content-hash cache)
    tests/fixtures/recorded/descriptions.json       (node_id -> description)

ask_graph.py picks descriptions.json up automatically — the local agent's
resolution payload then includes the calculation-step catalog.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from devtools.local_llm import chat_completion  # noqa: E402
from src.anonymization import get_scan_terms, load_crosswalk, scan_for_missed  # noqa: E402
from src.descriptions import generate_descriptions  # noqa: E402
from src.phi_scan import redact_node_fragments, scan_sql  # noqa: E402
from src.steps.build_graph import build_graph_step  # noqa: E402

FIXTURES = PROJECT_ROOT / "tests" / "fixtures" / "recorded"
CROSSWALK = PROJECT_ROOT / "data" / "synthetic" / "crosswalk.json"
CACHE_PATH = FIXTURES / "description_cache.json"
DESCRIPTIONS_PATH = FIXTURES / "descriptions.json"


def main() -> None:
    _load_dotenv()
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    spec = importlib.util.spec_from_file_location(
        "run_pipeline_local", PROJECT_ROOT / "scripts" / "run_pipeline_local.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    parse_results, tables, columns = mod.load_recorded(FIXTURES)
    if limit:
        parse_results = parse_results[:limit]
    graph = build_graph_step(parse_results, tables, columns)

    # PHI gate (ADR 0025), mirroring production: scan whole sources (02's
    # job), redact fragments before prompts (07's job). Redaction changes
    # content hashes, so affected steps regenerate — the point, not a bug.
    phi_findings = []
    for pr in parse_results:
        phi_findings.extend(scan_sql(pr["metric_id"], pr.get("normalized_sql") or ""))
    changed = redact_node_fragments(graph.nodes_rows, phi_findings)
    if phi_findings:
        by_rule: dict = {}
        for f in phi_findings:
            by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
        print(f"PHI scan: {len(phi_findings)} findings {by_rule}; "
              f"{changed} fragments redacted before prompting")

    cache: dict = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text())
    existing: dict = {}
    if DESCRIPTIONS_PATH.exists():
        existing = json.loads(DESCRIPTIONS_PATH.read_text())

    calls = {"n": 0}
    def describe(prompt: str) -> str:
        calls["n"] += 1
        if calls["n"] % 25 == 0:
            print(f"  ...{calls['n']} LLM calls")
        return chat_completion("You write terse, faithful business documentation.", prompt)

    result = generate_descriptions(graph.nodes_rows, graph.edges_rows, describe, cache=cache)
    print(f"Generated {result.generated}, cache hits {result.cache_hits}, failed {len(result.failed)}")

    # Leak gate — defense in depth even though fixtures are anonymized
    terms = get_scan_terms(load_crosswalk(CROSSWALK))
    all_text = "\n".join(result.descriptions.values()) + "\n" + "\n".join(cache.values())
    leaks = scan_for_missed(all_text, terms)
    if leaks:
        # Quarantine (gitignored) so a false-positive gate doesn't discard
        # the paid LLM calls — inspect, fix the gate or the text, re-run.
        quarantine = CACHE_PATH.with_suffix(".quarantine.json")
        quarantine.write_text(
            json.dumps({"cache": cache, "descriptions": result.descriptions},
                       indent=1, sort_keys=True)
        )
        print(f"[X] LEAK GATE FAILED — nothing published; raw output quarantined in {quarantine.name}:")
        for line in leaks[:10]:
            print(f"    {line}")
        raise SystemExit(1)

    existing.update(result.descriptions)
    CACHE_PATH.write_text(json.dumps(cache, indent=1, sort_keys=True))
    DESCRIPTIONS_PATH.write_text(json.dumps(existing, indent=1, sort_keys=True))
    print(f"Wrote {len(cache)} cache entries, {len(existing)} descriptions")

    for nid, text in list(result.descriptions.items())[:3]:
        print(f"\n{nid}\n  {text[:180]}")


if __name__ == "__main__":
    main()
