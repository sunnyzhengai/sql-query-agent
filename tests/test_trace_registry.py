"""The trace registry's three closure checks (ADR 0048 item 2).

totality — every src/ module traces to ≥1 decision (the ghost rule
mechanized; ADR 0049 was this check's first live find). existence —
every cited path and axiom exists (the failure class the spec audit
caught by hand: a cited test that didn't exist). single classification
— governed ⊎ internal covers the repo (with tests/test_zones.py).
"""

from pathlib import Path

from src.trace_registry import (
    CATEGORIES,
    SPEC_AXIOMS,
    TRACE_REGISTRY,
    decisions_for_module,
    modules_cited,
)
from src.zones import classify

REPO = Path(__file__).resolve().parent.parent


def test_every_adr_file_has_an_entry_and_vice_versa():
    files = {p.name.split("-")[0] for p in (REPO / "docs" / "decisions").glob("0*.md")}
    assert files == set(TRACE_REGISTRY), (
        f"registry/ADR-file mismatch: only-in-files={sorted(files - set(TRACE_REGISTRY))} "
        f"only-in-registry={sorted(set(TRACE_REGISTRY) - files)}"
    )


def test_totality_every_module_traces_to_a_decision():
    all_modules = {
        str(p.relative_to(REPO))
        for p in (REPO / "src").rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    }
    ghosts = sorted(all_modules - modules_cited())
    assert not ghosts, (
        f"ghost module(s) — no decision cites them: {ghosts}. Record the "
        f"decision (an ADR) and add the lineage to src/trace_registry.py"
    )


def test_existence_every_cited_path_exists():
    dangling = []
    for adr, entry in TRACE_REGISTRY.items():
        for kind in ("modules", "tests", "docs"):
            for rel in entry[kind]:
                if not (REPO / rel).exists():
                    dangling.append(f"{adr}: {rel}")
        for axiom in entry["axioms"]:
            if axiom not in SPEC_AXIOMS:
                dangling.append(f"{adr}: axiom {axiom} not in SPEC_AXIOMS")
        if entry["category"] not in CATEGORIES:
            dangling.append(f"{adr}: category {entry['category']!r}")
    assert not dangling, "dangling citation(s):\n  " + "\n  ".join(dangling)


def test_architecture_decisions_carry_code_or_tests():
    """A category=architecture entry with neither modules nor tests is
    either miscategorized or an unimplemented design pass — the only
    sanctioned exceptions are recorded here with their reason."""
    sanctioned = {
        "0029",  # design pass, explicitly unimplemented (status line)
        "0034",  # superseded in part by 0035; its artifacts were deleted
        "0056",  # ACCEPTED, sequenced AFTER CAPTURE — modules land
                 # with its build order
        "0058",  # DRAFT — Pro-pillar contracts; build lands WITH Pro
        "0057",  # design record by construction — binds design, never
                 # the build queue; no modules ever expected
        "0062",  # DRAFT under the DEVELOPMENT HOLD — modules land
                 # only after Sunny ratifies and lifts the hold
    }
    empty = [
        adr for adr, e in TRACE_REGISTRY.items()
        if e["category"] == "architecture" and not e["modules"] and not e["tests"]
        and adr not in sanctioned
    ]
    assert not empty, f"architecture ADR(s) with no code and no tests: {empty}"


def test_single_classification_governed_or_internal():
    import subprocess
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                         text=True, check=True).stdout
    tops = {line.split("/", 1)[0] for line in out.splitlines() if line}
    unclassified = sorted(t for t in tops if classify(t) is None)
    assert not unclassified, f"unclassified top-level path(s): {unclassified}"


def test_reverse_lookup_answers_who_claims_this_module():
    assert "0044" in decisions_for_module("src/tree/diff.py")
    assert decisions_for_module("src/parser/scriptdom_loader.py") == ["0001"]


def test_trace_map_is_freshly_generated():
    """The generated-tier check (NOTEBOOK_MAP pattern): regenerating
    must produce zero diff."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gd", REPO / "scripts" / "generate_docs.py")
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    on_disk = (REPO / "docs" / "architecture" / "TRACE_MAP.md").read_text()
    assert gd.build_trace_map() == on_disk, (
        "TRACE_MAP.md is stale — run: python scripts/generate_docs.py"
    )
