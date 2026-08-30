"""X-RAY-1 CLI: generate the Estate X-Ray report against a live
store (the workbench store lever applies — SQA_KUSTO_DB or
org_config search.kusto_db).

Usage: python devtools/run_xray.py [org_name] [out_path]
Defaults: org from org_config; internal/docs/XRAY_REPORT.md
"""

from __future__ import annotations

import datetime
import sys


def main() -> None:
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    from src.webapp.main import resolve_store
    from src.xray import compose_xray

    org = sys.argv[1] if len(sys.argv) > 1 else ""
    out = (sys.argv[2] if len(sys.argv) > 2
           else "internal/docs/XRAY_REPORT.md")
    if not org:
        try:
            import yaml
            org = str(((yaml.safe_load(open("org_config.yaml").read())
                        or {}).get("org") or {}).get("name") or "the estate")
        except Exception:  # noqa: BLE001
            org = "the estate"
    uri, db, _src = resolve_store()
    client = KustoClient(uri, db, az_cli_token_provider(uri))
    stamp = datetime.datetime.now(datetime.timezone.utc
                                  ).strftime("%Y-%m-%d %H:%M UTC")
    report = compose_xray(client.run, org, generated_at=stamp)
    with open(out, "w") as f:
        f.write(report)
    print(f"wrote {out} (store: {db})")


if __name__ == "__main__":
    import os.path as _op
    import sys as _sys
    _sys.path.insert(0, _op.dirname(_op.dirname(_op.abspath(__file__))))
    main()
