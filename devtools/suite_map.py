"""TEST_MAP — the suite's proof ledger (morning order 1, 2026-08-27).

Every test module declares what it proves, with ONE WRITER per
linkage kind:

  ADR linkage      src/trace_registry.py `tests` lists (already the
                   registry of decision → test; the map derives from
                   it — an `adr:` tag in a docstring would be a
                   second truth that can drift, so it is INVALID)
  law/contract     a `Proves:` line in the module docstring, tags
                   validated against the registries below
  spec axioms      derived transitively: axiom → grounding ADRs →
                   their claimed tests (no per-test duplication)

Totality (tests/test_suite_map.py): every tests/**/test_*.py module
is registry-claimed ⊎ docstring-declared; the generated map is
freshness-pinned in CI (the PIPELINE_MAP pattern). Purpose: the
suite stays legible to Sunny as it grows.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# standing laws with mechanical teeth, slug -> what holding means
KNOWN_LAWS = {
    "live-probe": "no ops/tools surface ships without the smoke "
                  "harness passing against the live store (P0.4)",
    "walk-finds": "corpses from Sunny's live walks are mechanized "
                  "same-session (Echo Law)",
    "brand-separation": "the product name is a seam; the core stays "
                        "brand-neutral",
    "endpoint-hygiene": "no tenant endpoint ever lives in this repo",
    "honesty-floor": "honesty 1.00 is a build-stopper, never a metric",
}

# executable contracts that are not ADR-born, slug -> what it pins
KNOWN_CONTRACTS = {
    "toolchain": "every third-party dependency is declared and "
                 "pinned (Sunny's ruling, 2026-08-19)",
    "suite-integrity": "answer_evals grades describe the engine or "
                       "the run aborts (INFRA-SKIP contract)",
    "suite-legibility": "the suite explains itself to Sunny — the "
                        "proof ledger and the run transcript "
                        "(morning orders, 2026-08-27)",
    "org-config": "org_config referential integrity, LOCAL and "
                  "TENANT copies together",
    "round4-scorecard": "the Round-4 record's fact accounting and "
                        "mitigation verifiers",
    "web-surface": "the served page works AS SERVED",
}

_PROVES = re.compile(r"^Proves:\s*(.+)$", re.M)
_TAG = re.compile(r"^(law|contract|spec|family):[\w.-]+$")


def parse_proves(docstring: str) -> "list[str]":
    m = _PROVES.search(docstring or "")
    if not m:
        return []
    return [t.strip() for t in m.group(1).split(",") if t.strip()]


def scan_suite(repo_root: Path) -> "list[dict]":
    """Every test module: path, docstring first line, Proves tags,
    test count (functions + methods named test_*)."""
    out = []
    for p in sorted((repo_root / "tests").rglob("test_*.py")):
        tree = ast.parse(p.read_text())
        doc = ast.get_docstring(tree) or ""
        n = sum(1 for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef,
                                     ast.AsyncFunctionDef))
                and node.name.startswith("test_"))
        out.append({"path": str(p.relative_to(repo_root)),
                    "first_line": doc.split("\n")[0],
                    "tags": parse_proves(doc), "n_tests": n})
    return out


def registry_claims() -> "dict[str, list[str]]":
    """module path -> claiming ADR ids, from the one ADR writer."""
    from src.trace_registry import TRACE_REGISTRY
    claims: "dict[str, list[str]]" = {}
    for adr in sorted(TRACE_REGISTRY):
        for t in TRACE_REGISTRY[adr].get("tests", []):
            path = t.split("::")[0]
            if path.startswith("tests/") and path.endswith(".py"):
                claims.setdefault(path, []).append(adr)
    return claims


def accounting(mods: "list[dict]",
               claims: "dict[str, list[str]]"
               ) -> "tuple[list[str], list[str]]":
    """(unaccounted modules, invalid tags) — both empty = totality."""
    from src.trace_registry import SPEC_AXIOMS
    unaccounted, invalid = [], []
    for m in mods:
        for tag in m["tags"]:
            kind, _, slug = tag.partition(":")
            if tag.startswith("adr:"):
                invalid.append(
                    f"{m['path']}: {tag} — adr: linkage has one "
                    "writer (src/trace_registry.py); claim the "
                    "module there instead")
            elif not _TAG.match(tag):
                invalid.append(f"{m['path']}: malformed tag {tag!r}")
            elif kind == "law" and slug not in KNOWN_LAWS:
                invalid.append(f"{m['path']}: unknown law {slug!r}")
            elif kind == "contract" and slug not in KNOWN_CONTRACTS:
                invalid.append(
                    f"{m['path']}: unknown contract {slug!r}")
            elif kind == "spec" and slug not in SPEC_AXIOMS:
                invalid.append(f"{m['path']}: unknown axiom {slug!r}")
        if not m["tags"] and m["path"] not in claims:
            unaccounted.append(m["path"])
    return unaccounted, invalid


def build_test_map() -> str:
    from src.trace_registry import TRACE_REGISTRY
    repo_root = Path(__file__).resolve().parent.parent
    mods = scan_suite(repo_root)
    claims = registry_claims()
    by_path = {m["path"]: m for m in mods}
    total_tests = sum(m["n_tests"] for m in mods)

    lines = [
        "<!-- GENERATED FILE — do not edit.",
        "     Sources: src/trace_registry.py claims + docstring",
        "     Proves: lines (devtools/suite_map.py grammar).",
        "     Regenerate: python scripts/generate_docs.py",
        "     CI fails if stale or if any module proves nothing",
        "     on record (tests/test_suite_map.py). -->",
        "",
        "# Test Map — what every test proves",
        "",
        f"{len(mods)} modules, {total_tests} tests, every module "
        "accounted: claimed by an ADR in the trace registry or "
        "declaring a law/contract in its docstring (`Proves:` line).",
        "",
        "## By ADR",
        "",
        "| ADR | Title | Test modules |",
        "|---|---|---|",
    ]
    for adr in sorted(TRACE_REGISTRY):
        paths = sorted(p for p, adrs in claims.items() if adr in adrs)
        if not paths:
            continue
        cells = ", ".join(
            f"`{p}` ({by_path[p]['n_tests']})" for p in paths
            if p in by_path)
        lines.append(
            f"| {adr} | {TRACE_REGISTRY[adr]['title']} | {cells} |")

    lines += ["", "## By standing law", ""]
    for slug, title in KNOWN_LAWS.items():
        lines.append(f"### law:{slug} — {title}")
        lines.append("")
        for m in mods:
            if f"law:{slug}" in m["tags"]:
                lines.append(f"- `{m['path']}` ({m['n_tests']}): "
                             f"{m['first_line']}")
        lines.append("")

    lines += ["## By executable contract", ""]
    for slug, title in KNOWN_CONTRACTS.items():
        lines.append(f"### contract:{slug} — {title}")
        lines.append("")
        for m in mods:
            if f"contract:{slug}" in m["tags"]:
                lines.append(f"- `{m['path']}` ({m['n_tests']}): "
                             f"{m['first_line']}")
        lines.append("")

    lines += [
        "## By spec axiom (derived: axiom → grounding ADRs → tests)",
        "",
        "| Axiom | ADRs | Test modules |",
        "|---|---|---|",
    ]
    axiom_adrs: "dict[str, list[str]]" = {}
    for adr in sorted(TRACE_REGISTRY):
        for ax in TRACE_REGISTRY[adr].get("axioms", []):
            axiom_adrs.setdefault(ax, []).append(adr)
    for ax in sorted(axiom_adrs):
        adrs = axiom_adrs[ax]
        paths = sorted({p for p, cl in claims.items()
                        for a in cl if a in adrs})
        cells = ", ".join(f"`{p}`" for p in paths) or "(spec gate only)"
        lines.append(f"| spec:{ax} | {', '.join(adrs)} | {cells} |")
    lines.append("")
    return "\n".join(lines)
