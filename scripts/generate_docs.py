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

from src.integration_registry import INTEGRATION_REGISTRY  # noqa: E402
from src.notebook_registry import NOTEBOOK_REGISTRY, QUESTION_FAMILIES  # noqa: E402
from src.schemas import TABLE_REGISTRY  # noqa: E402

PIPELINE_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "PIPELINE_MAP.md"
INTEGRATION_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "INTEGRATION_MAP.md"
NOTEBOOK_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "NOTEBOOK_MAP.md"

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


def build_integration_map() -> str:
    """Project INTEGRATION_REGISTRY to mermaid + table.

    Deliberately SEPARATE from PIPELINE_MAP: this answers "what tools do
    we connect to and how", for roadmap/marketplace audiences; the
    pipeline map answers "how does data flow inside an installation".
    """
    style = {"shipped": "shipped", "planned": "planned", "watchlist": "watchlist"}
    lines = ["flowchart LR", '  AIVIA(("AIVIA<br/>knowledge graph")):::core']
    for i, row in enumerate(INTEGRATION_REGISTRY):
        other = row["to_tool"] if row["from_tool"] == "AIVIA" else row["from_tool"]
        node = f"T{i}"
        lines.append(f'  {node}["{other}"]:::{style[row["status"]]}')
        label = row["status"] if row["status"] != "shipped" else row["direction"]
        if row["from_tool"] == "AIVIA":
            lines.append(f"  AIVIA -->|{label}| {node}")
        else:
            lines.append(f"  {node} -->|{label}| AIVIA")
    lines.append("  classDef core fill:#e8f0fe,stroke:#4285f4,stroke-width:2px")
    lines.append("  classDef shipped fill:#e6f4ea,stroke:#34a853")
    lines.append("  classDef planned fill:#fef7e0,stroke:#f9ab00")
    lines.append("  classDef watchlist fill:#fce8e6,stroke:#ea4335,stroke-dasharray: 4")
    mermaid = "\n".join(lines)

    header = (
        "| From | To | Artifact parsed | Mechanism | Status | Tier | Direction |\n"
        "|---|---|---|---|---|---|---|"
    )
    rows = [
        f"| {r['from_tool']} | {r['to_tool']} | {r['artifact_parsed']} | "
        f"{r['mechanism']} | {r['status']} | {r['tier']} | {r['direction']} |"
        for r in INTEGRATION_REGISTRY
    ]
    notes = [
        f"- **{r['from_tool']} → {r['to_tool']}**: {r['notes']}"
        for r in INTEGRATION_REGISTRY if r["notes"]
    ]

    return f"""<!-- GENERATED FILE — do not edit.
     Source: INTEGRATION_REGISTRY in src/integration_registry.py
     Regenerate: python scripts/generate_docs.py
     CI fails if this file differs from regeneration. -->

# Integration Map

The tool/connector landscape as data: what AIVIA parses on the way in
(always via each layer's native parser) and what it publishes on the way
out. Supersedes the ROADMAP connector table (2026-08-07) and the
REFERENCE_ARCHITECTURE tier table as source of truth.

```mermaid
{mermaid}
```

{header}
{chr(10).join(rows)}

## Notes

{chr(10).join(notes)}
"""



FAMILY_TITLES = {
    "A": "Meaning", "B": "Provenance", "C": "Impact", "D": "Discovery",
    "E": "Trust", "F": "Consistency", "G": "Health",
}


def build_notebook_map() -> str:
    """Project NOTEBOOK_REGISTRY: the notebook contract table + the
    QUESTION_MAP layer-4 coverage (family -> notebooks) — generated,
    never hand-edited (ADR 0042)."""
    lines = [
        "# Notebook Map",
        "",
        "**GENERATED from `src/notebook_registry.py` — do not edit.**",
        "Regenerate: `python scripts/generate_docs.py`. The contract is",
        "enforced by tests/test_notebook_contract.py (ADR 0042).",
        "",
        "## The notebook contract",
        "",
        "| Notebook | Family | Serves | Engine | Purpose |",
        "|---|---|---|---|---|",
    ]
    for nb, e in sorted(NOTEBOOK_REGISTRY.items()):
        lines.append(
            f"| {nb} | {e['family']} | {', '.join(e['serves'])} | "
            f">={e['requires_engine']} | {e['purpose']} |"
        )
    lines += [
        "",
        "## Question-family coverage (QUESTION_MAP layer 4, generated)",
        "",
        "| Family | Served by |",
        "|---|---|",
    ]
    for fam in QUESTION_FAMILIES:
        served_by = [nb for nb, e in sorted(NOTEBOOK_REGISTRY.items())
                     if fam in e["serves"]]
        lines.append(
            f"| {fam}. {FAMILY_TITLES[fam]} | {', '.join(served_by) or '(GAP)'} |"
        )
    lines += [
        "",
        "Every notebook must serve >=1 family — a notebook serving none",
        "is by definition a ghost (traceability rule, QUESTION_MAP.md).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    PIPELINE_MAP_PATH.write_text(build_pipeline_map())
    print(f"Wrote {PIPELINE_MAP_PATH}")
    INTEGRATION_MAP_PATH.write_text(build_integration_map())
    print(f"Wrote {INTEGRATION_MAP_PATH}")
    NOTEBOOK_MAP_PATH.write_text(build_notebook_map())
    print(f"Wrote {NOTEBOOK_MAP_PATH}")


if __name__ == "__main__":
    main()
