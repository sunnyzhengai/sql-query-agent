"""Generate documentation projections from the data contracts.

GENERATED-tier docs (truth hierarchy): the output files are compiled from
TABLE_REGISTRY — never edited by hand. tests/test_docs_consistency.py fails
if a generated file differs from regeneration.

Usage:
    python scripts/generate_docs.py          # writes the generated docs
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.schemas import TABLE_REGISTRY  # noqa: E402

PIPELINE_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "PIPELINE_MAP.md"

# Non-notebook consumers rendered as terminal actors.
ACTORS = {"data_agent", "admin", "collibra_adapter", "purview_adapter"}


def _mid(name: str) -> str:
    """Sanitize a name into a mermaid node id."""
    return re.sub(r"\W", "_", name)


def build_pipeline_map() -> str:
    """Project the dataflow DAG (writers -> tables -> consumers) to mermaid."""
    active = {
        n: c for n, c in sorted(TABLE_REGISTRY.items())
        if c["status"] == "active"
    }

    # Collapse the LPG export family into one node for readability;
    # the registry remains the precise source.
    lpg_tables = [n for n, c in active.items() if c["domain"] == "lpg_export"]
    LPG_NODE = f"LPG export ({len(lpg_tables)} typed tables)"

    lines: "list[str]" = []
    edges: "set[str]" = set()
    notebooks: "set[str]" = set()
    actors: "set[str]" = set()
    tables: "set[str]" = set()

    def table_node(name: str) -> str:
        if name in lpg_tables:
            return LPG_NODE
        return name

    for name, contract in active.items():
        display = table_node(name)
        tables.add(display)

        owner = (contract.get("owner") or {}).get("notebook")
        if owner:
            notebooks.add(owner)
            edges.add(f"  {_mid(owner)} --> {_mid(display)}")
        for enricher in contract.get("enrichers", []):
            notebooks.add(enricher)
            edges.add(f"  {_mid(enricher)} -->|enrich| {_mid(display)}")
        for writer in contract.get("utility_writers", []):
            notebooks.add(writer)
            edges.add(f"  {_mid(writer)} -.-> {_mid(display)}")

        for consumer in contract.get("consumers", []):
            base = consumer.split(" ")[0]
            if base in ACTORS:
                actors.add(base)
                edges.add(f"  {_mid(display)} --> {_mid(base)}")
            elif "(planned)" in consumer:
                continue
            elif base != owner or True:
                notebooks.add(base)
                edges.add(f"  {_mid(display)} --> {_mid(base)}")

    lines.append("flowchart LR")
    for nb in sorted(notebooks):
        lines.append(f'  {_mid(nb)}["{nb}"]:::notebook')
    for t in sorted(tables):
        lines.append(f'  {_mid(t)}[("{t}")]:::table')
    for a in sorted(actors):
        lines.append(f"  {_mid(a)}{{{{{a}}}}}:::actor")
    lines.extend(sorted(edges))
    lines.append("  classDef notebook fill:#e8f0fe,stroke:#4285f4")
    lines.append("  classDef table fill:#fef7e0,stroke:#f9ab00")
    lines.append("  classDef actor fill:#e6f4ea,stroke:#34a853")

    mermaid = "\n".join(lines)
    return f"""<!-- GENERATED FILE — do not edit.
     Source: TABLE_REGISTRY in src/schemas.py
     Regenerate: python scripts/generate_docs.py
     CI fails if this file differs from regeneration. -->

# Pipeline Dataflow Map

Every edge below is a declared, code-verified fact from the data contracts:
solid arrows into a table are its owner/enricher writes, dashed arrows are
sanctioned utility writers, and arrows out of a table are its declared
consumers (notebook reads are verified against code by the contract tests).

```mermaid
{mermaid}
```

Planned tables (contracts without writers) and per-table details — columns,
invariants, relations — live in `src/schemas.py`.
"""


def main() -> None:
    PIPELINE_MAP_PATH.write_text(build_pipeline_map())
    print(f"Wrote {PIPELINE_MAP_PATH}")


if __name__ == "__main__":
    main()
