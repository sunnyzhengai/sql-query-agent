"""Docs-vs-reality consistency checks.

Documentation drift is a turn-key killer: the install guide once referenced
deleted files, a superseded notebook numbering, and a config path the code
never reads. These tests pin the docs to repo ground truth so drift fails CI
instead of reaching a customer.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = sorted((REPO_ROOT / "docs").rglob("*.md")) + [REPO_ROOT / "README.md"]
# INSTALL_GUIDE retired with era 1 (Brief_Retirement, 2026-09-19)

LINK = re.compile(r"\]\(([^)#\s]+\.md)\)")


def _retired_paths():
    """The retirement ledger (Brief_Retirement, 2026-09-19, "B,
    reconcile it"): docs are RECORDS and keep their citations; a
    reference into the retired era resolves against the committed
    manifest instead of the tree. Anything else broken is real."""
    manifest = (REPO_ROOT / "AIVIA_Design" / "briefs"
                / "Brief_Retirement_manifest.txt")
    return set(manifest.read_text().splitlines())


def test_every_relative_doc_link_resolves():
    retired = _retired_paths()
    broken = []
    for doc in DOCS:
        for match in LINK.finditer(doc.read_text()):
            target = match.group(1)
            if target.startswith("http"):
                continue
            resolved = (doc.parent / target).resolve()
            if resolved.exists():
                continue
            try:
                rel = resolved.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                rel = target
            if rel in retired or rel.rstrip("/") in {
                    p.split("/")[0] for p in retired}:
                continue
            broken.append(f"{doc.relative_to(REPO_ROOT)} -> {target}")
    assert not broken, "broken doc links:\n  " + "\n  ".join(broken)


def test_spec_binding_citations_resolve():
    """Every src/tests path SPEC.md cites in its Binding: lines must
    exist. Closes the failure class the v0.3 spec audit caught BY HAND
    ("A1's cited test did not exist") — an axiom's ENFORCED status is
    only as good as the file it points at. (Seam-tightening ruled by
    Sunny 2026-09-02; TRACE_REGISTRY's existence check covers the
    registry's citations, but SPEC's inline prose citations had no
    guard until this test.)"""
    spec = (REPO_ROOT / "docs" / "architecture" / "SPEC.md").read_text()
    cited = sorted(set(re.findall(r"\b(?:tests|src|devtools)/[\w/]+\.py\b",
                                  spec)))
    assert cited, "SPEC.md cites no code paths — the regex broke"
    retired = _retired_paths()
    dangling = [p for p in cited
                if not (REPO_ROOT / p).exists() and p not in retired]
    assert not dangling, (
        "SPEC.md Binding: citation(s) name files that do not exist "
        "(the A1 failure class):\n  " + "\n  ".join(dangling))


# The five INSTALLATION_GUIDE tests retired WITH the guide and the
# 21 pipeline notebooks it documented (Brief_Retirement, 2026-09-19,
# "B, reconcile it") — the era-2 install story is the wheel + the
# runbook's five-step census (pilots/work_dryrun/README_Runbook.md).


def test_docs_agree_with_code_on_config_location():
    """src/config.py reads org_config.yaml from the project root — no doc may
    claim it lives in a config/ subfolder."""
    offenders = []
    for doc in DOCS:
        if "internal/MARKETPLACE_PIVOT" in str(doc):  # frozen snapshot
            continue
        if re.search(r"config/org_config\.yaml", doc.read_text()):
            offenders.append(str(doc.relative_to(REPO_ROOT)))
    assert not offenders, f"docs claim config/ subfolder location: {offenders}"


def test_pipeline_map_is_freshly_generated():
    """The generated-tier check: regenerating must produce zero diff.
    If this fails, run: python scripts/generate_docs.py"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_docs", REPO_ROOT / "scripts" / "generate_docs.py"
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    on_disk = (REPO_ROOT / "docs" / "architecture" / "PIPELINE_MAP.md").read_text()
    assert on_disk == gen.build_pipeline_map(), (
        "PIPELINE_MAP.md is stale — run: python scripts/generate_docs.py"
    )


def test_integration_map_is_freshly_generated():
    """Same generated-tier check for the connector landscape projection."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_docs", REPO_ROOT / "scripts" / "generate_docs.py"
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    on_disk = (REPO_ROOT / "docs" / "architecture" / "INTEGRATION_MAP.md").read_text()
    assert on_disk == gen.build_integration_map(), (
        "INTEGRATION_MAP.md is stale — run: python scripts/generate_docs.py"
    )


def test_notebook_map_is_freshly_generated():
    """Generated-tier check for the notebook contract projection."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_docs", REPO_ROOT / "scripts" / "generate_docs.py"
    )
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)

    on_disk = (REPO_ROOT / "docs" / "architecture" / "NOTEBOOK_MAP.md").read_text()
    assert on_disk == gen.build_notebook_map(), (
        "NOTEBOOK_MAP.md is stale — run: python scripts/generate_docs.py"
    )
