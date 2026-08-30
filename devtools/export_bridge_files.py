"""BRIDGE-1 stage-1 CLI: export the file-first review set against
a live store — Collibra assets + relations CSVs and the Purview
glossary CSV, every row provenance-graded. Hands Sunny real files
for her Purview import experiments.

Usage: python devtools/export_bridge_files.py <approver> [out_dir]
Defaults: out_dir=internal/docs/bridge_exports
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.adapters.file_export import export_bridge_files
    from src.orchestrator.kusto import KustoClient, az_cli_token_provider
    from src.webapp.main import resolve_store

    approver = sys.argv[1] if len(sys.argv) > 1 else "unreviewed"
    out_dir = (sys.argv[2] if len(sys.argv) > 2
               else "internal/docs/bridge_exports")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    uri, db, _src = resolve_store()
    client = KustoClient(uri, db, az_cli_token_provider(uri))
    counts = export_bridge_files(client.run, approver, out_dir)
    for fname, n in counts.items():
        print(f"  {fname}: {n} row(s)")
    print(f"wrote {out_dir} (store: {db}, approver: {approver})")


if __name__ == "__main__":
    import os.path as _op
    import sys as _sys
    _sys.path.insert(0, _op.dirname(_op.dirname(_op.abspath(__file__))))
    main()
