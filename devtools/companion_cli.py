"""Try the admin companion locally (ADR 0048 item 4).

Usage:
    python devtools/companion_cli.py explain 300_build_graph
    python devtools/companion_cli.py diagnose '{"reason_text": "...", \
        "contract_id": "contract:input_dict_tables"}'

Facts come from the registries; the diagnosis walks a locally-built
admin graph (same projection 500 writes on Fabric). No LLM involved —
this is the deterministic core the narrated surface wraps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.admin_graph import build_admin_graph  # noqa: E402
from src.companion import (  # noqa: E402
    diagnose,
    explain_step,
    step_explanation_lines,
)


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in ("explain", "diagnose"):
        print(__doc__)
        raise SystemExit(2)
    if sys.argv[1] == "explain":
        try:
            print("\n".join(step_explanation_lines(explain_step(sys.argv[2]))))
        except KeyError as err:
            print(err.args[0])
            raise SystemExit(1) from None
        return
    row = json.loads(sys.argv[2])
    g = build_admin_graph(error_rows=[row])
    d = diagnose(row, g.nodes_rows, g.edges_rows)
    print("\n".join(d["caption_lines"]))
    if d["hops"]:
        print("Path walked:")
        for src, kind, dst in d["hops"]:
            print(f"  {src} —{kind}→ {dst}")


if __name__ == "__main__":
    main()
