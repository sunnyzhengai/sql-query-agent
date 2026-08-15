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
INSTALL_GUIDE = REPO_ROOT / "docs" / "deployment" / "INSTALLATION_GUIDE.md"

LINK = re.compile(r"\]\(([^)#\s]+\.md)\)")


def test_every_relative_doc_link_resolves():
    broken = []
    for doc in DOCS:
        for match in LINK.finditer(doc.read_text()):
            target = match.group(1)
            if target.startswith("http"):
                continue
            if not (doc.parent / target).resolve().exists():
                broken.append(f"{doc.relative_to(REPO_ROOT)} -> {target}")
    assert not broken, "broken doc links:\n  " + "\n  ".join(broken)


def test_install_guide_covers_every_pipeline_notebook():
    guide = INSTALL_GUIDE.read_text()
    stems = [
        p.name.removesuffix(".Notebook")
        for p in sorted(REPO_ROOT.glob("[0-9][0-9]_*.Notebook"))
    ]
    assert stems, "no pipeline notebooks found at repo root"
    missing = [s for s in stems if s not in guide]
    assert not missing, f"INSTALLATION_GUIDE.md never mentions: {missing}"


def test_install_guide_references_no_ghost_notebooks():
    guide = INSTALL_GUIDE.read_text()
    stems = {
        p.name.removesuffix(".Notebook")
        for p in REPO_ROOT.glob("[0-9][0-9]_*.Notebook")
    }
    referenced = set(re.findall(r"\b(\d{2}_[a-z_]+)\b", guide))
    ghosts = {r for r in referenced if r not in stems}
    assert not ghosts, f"INSTALLATION_GUIDE.md references nonexistent notebooks: {ghosts}"


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


def test_install_guide_does_not_hardcode_package_version():
    guide = INSTALL_GUIDE.read_text()
    assert not re.search(r"sql_query_agent-\d+\.\d+\.\d+", guide), (
        "INSTALLATION_GUIDE.md hardcodes a wheel version; use "
        "sql_query_agent-<version>-py3-none-any.whl so releases don't stale it"
    )


def test_install_guide_documents_every_optional_input_remediation():
    """Handoff item 3 (2026-08-15): optional inputs are contract state, and
    the guide's post-install steps must not drift from the registry. Every
    active optional_input table must appear in INSTALLATION_GUIDE.md along
    with its remediation utility."""
    from src.schemas import TABLE_REGISTRY

    guide = INSTALL_GUIDE.read_text()
    missing = []
    for name, contract in TABLE_REGISTRY.items():
        if contract.get("status") != "active" or not contract.get("optional_input"):
            continue
        remediation = contract.get("remediation", "")
        assert remediation, f"{name}: optional_input without a remediation field"
        util = remediation.split()[1] if " " in remediation else remediation
        if name not in guide or util.split("/")[-1] not in guide:
            missing.append(f"{name} (remediation: {remediation})")
    assert not missing, (
        f"INSTALLATION_GUIDE.md lacks post-install coverage for: {missing}"
    )
