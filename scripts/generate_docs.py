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


TRACE_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "TRACE_MAP.md"


def build_trace_map() -> str:
    """TRACE_MAP.md — the trace registry projected as a readable map
    (ADR 0048 item 2): open any ADR, see its axioms, code, tests."""
    from src.trace_registry import ARCHITECTURE_COMPONENTS, TRACE_REGISTRY

    lines = [
        "# Trace Map — decision → component → axioms → code → tests "
        "(generated)",
        "",
        "Generated from `src/trace_registry.py` (ADR 0048).",
        "Regenerate: `python scripts/generate_docs.py`. Closure checks:",
        "`tests/test_trace_registry.py` (totality / existence / hierarchy /",
        "single classification).",
        "",
        "## The dependency hierarchy",
        "",
        "Decisions map **first to an architecture component, and then "
        "upward to the axioms** (Sunny's ruling, 2026-09-01). A decision "
        "is an engineering choice about a system component; routing "
        "through the blueprint says *where* in the system it lives, and "
        "keeps decision logs free of repeated philosophical preamble.",
        "",
        "```",
        "  ROOT       docs/AI_VIA_AXIOMS.md      the constitution (axm:*)",
        "    ^",
        "  BLUEPRINT  docs/architecture/*.md     topology + boundaries",
        "    ^                                   (declares axiom GROUPS)",
        "  EXECUTION  docs/decisions/*.md        one component each",
        "```",
        "",
        "Two citation handles, because the axiom systems are distinct and "
        "their group letters (B, D, R) collide: **`axm:M5`** = the "
        "framework in `docs/AI_VIA_AXIOMS.md`; **`spec:C1`** = Φ_AIVIA in "
        "`docs/architecture/SPEC.md`.",
        "",
        "### The blueprint tier",
        "",
        "| Component | File | Satisfies | Governs |",
        "|---|---|---|---|",
    ]
    for key in sorted(ARCHITECTURE_COMPONENTS):
        c = ARCHITECTURE_COMPONENTS[key]
        groups = ", ".join(f"axm:{g}" for g in c["satisfies"])
        # TRACE_MAP.md lives in docs/architecture/, so a doc path
        # "docs/architecture/X.md" is a sibling and "docs/product/X.md"
        # is one level up.
        rel = c["doc"].replace("docs/architecture/", "").replace(
            "docs/", "../")
        lines.append(
            f"| `{key}` | [{c['doc'].split('/')[-1]}]"
            f"({rel}) | {groups} | {c['governs']} |")
    lines.append("")
    lines.append("### The execution tier")
    lines.append("")

    for adr in sorted(TRACE_REGISTRY):
        e = TRACE_REGISTRY[adr]
        lines.append(f"## ADR {adr} — {e['title']}")
        lines.append("")
        lines.append(f"- **Category:** {e['category']}")
        comp = ARCHITECTURE_COMPONENTS[e["component"]]
        groups = ", ".join(f"axm:{g}" for g in comp["satisfies"])
        lines.append(
            f"- **Component:** `{e['component']}` → "
            f"`{comp['doc']}` → {groups}")
        if e["axioms"]:
            axioms = ", ".join(f"spec:{a}" for a in e["axioms"])
            lines.append(f"- **Grounds:** {axioms}")
        for label, kind in (("Implemented by", "modules"),
                            ("Enforced by", "tests"),
                            ("Summarized in", "docs")):
            if e[kind]:
                lines.append(f"- **{label}:**")
                lines.extend(f"  - `{p}`" for p in e[kind])
        lines.append("")
    return "\n".join(lines)


def build_landing_matrix() -> str:
    """DECISION_LANDING_MATRIX.md — the landing registry projected
    (ADR 0068, an ADR 0067 ratchet turn). The registry is the truth;
    this doc is its human view."""
    # DEFAULT_PRODUCT_NAME, not product_name(): the committed artifact
    # must be replay-deterministic — product_name() reads an env var
    # and would make generation differ per machine (freshness CI).
    from src.branding import DEFAULT_PRODUCT_NAME
    brand = DEFAULT_PRODUCT_NAME
    from src.landing_registry import (
        CONSEQUENCES,
        LANDING_ACTIONS,
        OPEN_ITEMS,
        OUTBOX_FIELDS,
        OUTBOX_NOTE,
        OUTBOX_OUTCOMES,
        WORKFLOW_RULES,
        ZERO_SCHEMA_FOOTPRINT,
    )
    def r(text: str) -> str:
        return text.replace("{product}", brand)

    lines = [
        "<!-- GENERATED FILE — do not edit.",
        "     Source: LANDING_REGISTRY in src/landing_registry.py",
        "     Regenerate: python scripts/generate_docs.py",
        "     CI fails if stale (tests/test_landing_registry.py). -->",
        "",
        "<!-- TIER: BLUEPRINT — component key: landing",
        "     src/trace_registry.py ARCHITECTURE_COMPONENTS -->",
        "",
        f"# The decision landing matrix — {brand} · Purview · Collibra",
        "",
        "Converted to data by ADR 0068 (the ADR 0067 ratchet): the",
        "registry is the truth, this file is its projection. Content",
        "carries the source document's status — Sunny's four rulings",
        "of 2026-08-31 are RULED; the matrix as a whole awaits",
        "Bridge-build ratification. Rationale: the ADRs, never here.",
        "",
        "Support legend: `[native]` ships in the tool · `[config]`",
        f"needs configuration · `[absent]` no surface — {brand} holds",
        "it.",
        "",
        "## The four workflow rules",
        "",
    ]
    for rid, rule in WORKFLOW_RULES:
        lines.append(f"- **{rid}.** {rule}")
    lines += ["", "## Zero schema footprint (ruled 2026-08-31)", ""]
    zs = ZERO_SCHEMA_FOOTPRINT
    lines += [
        f"- **Source is a relationship, never a field** — "
        f"{zs['source_is_a_relationship']}.",
        f"- **Attribution is a prefix in the description text**: "
        f"`{zs['attribution_prefix']}` (rendered with the "
        f"deployment's product name) — {zs['attribution_note']}.",
        f"- **Logic identity stays home** — {zs['logic_hash_stays_home']}.",
        f"- **Accepted limit:** {zs['accepted_limit']}.",
        "",
        "## The OUTBOX (replaces \"sync\")",
        "",
        "One row per thing we ever proposed: "
        + " · ".join(f"`{f}`" for f in OUTBOX_FIELDS),
        "",
        "Outcomes: " + " | ".join(OUTBOX_OUTCOMES) + ".",
        "",
        OUTBOX_NOTE + ".",
        "",
        "## The landing matrix",
        "",
    ]
    for key, a in LANDING_ACTIONS.items():
        flag = " *(UNBUILT — no authoring surface today)*" \
            if a.get("unbuilt") else ""
        lines.append(f"### {a['title']}{flag}")
        lines.append("")
        lines.append(f"- **Grade:** {r(a['grade'])}")
        if a.get("own_only"):
            lines.append(f"- **Lands:** {brand} only — neither "
                         f"catalog has a surface for this")
        else:
            for system in ("purview", "collibra"):
                s = a[system]
                cells = []
                if s.get("assets"):
                    cells.append("assets: " + "; ".join(s["assets"]))
                if s.get("relationships"):
                    cells.append("relations: "
                                 + "; ".join(s["relationships"]))
                if s.get("status"):
                    cells.append("status: " + s["status"])
                for extra in ("reason", "rename_work"):
                    if s.get(extra):
                        cells.append(f"{extra}: {s[extra]}")
                lines.append(f"- **{system.capitalize()}:** "
                             + " · ".join(cells))
        lines.append(f"- **{brand} keeps:** {r(a['keeps'])}")
        lines.append("")
    lines += [
        "## Consequences",
        "",
        f"- **Console:** {CONSEQUENCES['console']}.",
        f"- **Divergence:** {CONSEQUENCES['divergence']}.",
        "",
        "## Open at ratification",
        "",
    ]
    for name, status, note in OPEN_ITEMS:
        lines.append(f"- **{name}** ({status}): {note}")
    lines.append("")
    return "\n".join(lines)


LANDING_MATRIX_PATH = (PROJECT_ROOT / "docs" / "architecture"
                       / "DECISION_LANDING_MATRIX.md")
TEST_MAP_PATH = PROJECT_ROOT / "docs" / "architecture" / "TEST_MAP.md"


def main() -> None:
    from devtools.suite_map import build_test_map
    PIPELINE_MAP_PATH.write_text(build_pipeline_map())
    print(f"Wrote {PIPELINE_MAP_PATH}")
    TEST_MAP_PATH.write_text(build_test_map())
    print(f"Wrote {TEST_MAP_PATH}")
    INTEGRATION_MAP_PATH.write_text(build_integration_map())
    print(f"Wrote {INTEGRATION_MAP_PATH}")
    NOTEBOOK_MAP_PATH.write_text(build_notebook_map())
    print(f"Wrote {NOTEBOOK_MAP_PATH}")
    TRACE_MAP_PATH.write_text(build_trace_map())
    print(f"Wrote {TRACE_MAP_PATH}")
    LANDING_MATRIX_PATH.write_text(build_landing_matrix())
    print(f"Wrote {LANDING_MATRIX_PATH}")


if __name__ == "__main__":
    main()
