"""RW-18d — measure the iteration card's latency split for real.

The blank-screen echo gets a MEASURED cause, never a guessed one:
times (1) the az-cli token fetch, (2) a cold + warm exact-tier
store query, (3) a semantic-tier query, (4) the LLM parse call when
OPENAI creds are present. Read-only throughout. Prints one line per
leg; the RESULTS entry records the numbers.

Run:  python devtools/measure_card_latency.py
"""

from __future__ import annotations

import time


def leg(label: str, fn):
    t0 = time.monotonic()
    try:
        fn()
        ms = int((time.monotonic() - t0) * 1000)
        print(f"  {label}: {ms} ms")
        return ms
    except Exception as e:              # noqa: BLE001 — typed report
        ms = int((time.monotonic() - t0) * 1000)
        print(f"  {label}: UNAVAILABLE after {ms} ms "
              f"({type(e).__name__}: {str(e)[:120]})")
        return None


def main() -> None:
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    from src.webapp.main import resolve_store

    uri, db, source = resolve_store()
    print(f"store: {db} @ {uri} (from {source})")

    provider = az_cli_token_provider(uri)
    leg("az-cli token (cold)", provider)
    leg("az-cli token (cached)", provider)

    client = KustoClient(uri, db, provider)
    leg("graph_nodes probe (cold)",
        lambda: client.run("graph_nodes | take 1", {}))

    def ground(entity):
        from src.orchestrator.ops import OpsSession
        from src.orchestrator.parse_plan import _ground_one
        def run():
            _ground_one(entity, client.run, OpsSession())
        return run

    leg("ground one entity, REAL tier path (cold)",
        ground("Diabetic Codeset"))
    leg("ground one entity, REAL tier path (warm)",
        ground("Diabetic Codeset"))
    leg("ground a MISS (both tiers + containment)",
        ground("weather today"))

    def parse_call():
        from src.orchestrator.agent import azure_chat_api
        from src.orchestrator.parse_plan import parse_question
        parse_question("are the two Diabetic Codesets the same?",
                       azure_chat_api())

    leg("LLM parse call (cold)", parse_call)
    leg("LLM parse call (warm)", parse_call)


if __name__ == "__main__":
    # standalone entry (FUZZ-FINDINGS-1 item 1): running the
    # file directly must work — bootstrap the repo root
    import os.path as _op
    import sys as _sys
    _sys.path.insert(0, _op.dirname(_op.dirname(
        _op.abspath(__file__))))
    main()
