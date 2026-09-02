"""The trace registry's three closure checks (ADR 0048 item 2).

totality — every src/ module traces to ≥1 decision (the ghost rule
mechanized; ADR 0049 was this check's first live find). existence —
every cited path and axiom exists (the failure class the spec audit
caught by hand: a cited test that didn't exist). single classification
— governed ⊎ internal covers the repo (with tests/test_zones.py).
"""

from pathlib import Path

from src.trace_registry import (
    ARCHITECTURE_COMPONENTS,
    AXM_GROUPS,
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
        "0012",  # "build on the existing repo, no rewrite" — a
                 # decision NOT to act; the whole repo is its artifact,
                 # so no module can be cited (recategorized from
                 # product 2026-09-01: it is a build choice, not an
                 # offer choice)
        "0029",  # design pass, explicitly unimplemented (status line)
        "0034",  # superseded in part by 0035; its artifacts were deleted
        "0058",  # ACCEPTED 2026-08-29 (types-only C2, creator-
                 # release C4) — build still lands WITH Pro
        "0057",  # design record by construction — binds design, never
                 # the build queue; no modules ever expected
    }
    empty = [
        adr for adr, e in TRACE_REGISTRY.items()
        if e["category"] == "architecture" and not e["modules"] and not e["tests"]
        and adr not in sanctioned
    ]
    assert not empty, f"architecture ADR(s) with no code and no tests: {empty}"


def test_hierarchy_every_decision_names_one_architecture_component():
    """The DOWNWARD edge (Sunny's ruling, 2026-09-01): a decision is an
    engineering choice about a system COMPONENT, so every ADR names
    exactly one — never zero, never a list. This is what routes an ADR's
    authority up through the blueprint tier instead of straight to the
    axioms."""
    bad = []
    for adr, entry in TRACE_REGISTRY.items():
        comp = entry.get("component")
        if not comp:
            bad.append(f"{adr}: no component — which architecture file "
                       f"does this decision modify?")
        elif comp not in ARCHITECTURE_COMPONENTS:
            bad.append(f"{adr}: component {comp!r} is not in "
                       f"ARCHITECTURE_COMPONENTS")
    assert not bad, ("decision(s) not grounded in the blueprint tier:\n  "
                     + "\n  ".join(bad))


def test_hierarchy_every_component_declares_its_axiom_groups():
    """The UPWARD edge: each architecture file declares which
    AI_VIA_AXIOMS groups it translates into topology. A blueprint that
    satisfies nothing is either mis-scoped or not a blueprint."""
    bad = []
    for key, comp in ARCHITECTURE_COMPONENTS.items():
        if not (REPO / comp["doc"]).exists():
            bad.append(f"{key}: doc {comp['doc']} does not exist")
        if not comp["satisfies"]:
            bad.append(f"{key}: declares no axiom group")
        for g in comp["satisfies"]:
            if g not in AXM_GROUPS:
                bad.append(f"{key}: {g!r} is not an AI_VIA_AXIOMS group")
    assert not bad, "blueprint tier defect(s):\n  " + "\n  ".join(bad)


def test_blueprints_are_reconciled_through_their_newest_decision():
    """The staleness stamp (Sunny's ruling, 2026-09-02). Narrative
    blueprints have no mechanical drift guard — every drift the
    2026-09-01 audit fixed (sqlglot in ARCHITECTURE, the execute story
    in USER_FLOW) was found by reading, not CI. This check makes
    acknowledgment mandatory: each component carries current_through,
    and landing an ADR on component X with a higher number than X's
    stamp is a red build until the stamp is bumped. Bumping it is an
    ATTESTATION that the blueprint was reconciled against the decision
    — the handoff-verdicts law applied to blueprints: the doc
    acknowledges the change the moment it lands, or the build is red."""
    bad = []
    for key, comp in ARCHITECTURE_COMPONENTS.items():
        stamp = comp.get("current_through")
        if not stamp:
            bad.append(f"{key}: no current_through stamp")
            continue
        if stamp not in TRACE_REGISTRY:
            bad.append(f"{key}: current_through {stamp!r} is not an ADR")
            continue
        newer = sorted(
            adr for adr, e in TRACE_REGISTRY.items()
            if e["component"] == key and adr > stamp
        )
        if newer:
            bad.append(
                f"{key}: ADR(s) {newer} landed after its stamp "
                f"({stamp}) — reconcile {comp['doc']} against them, "
                f"then bump current_through (the bump IS the "
                f"attestation)")
    assert not bad, ("blueprint(s) not reconciled with their newest "
                     "decision:\n  " + "\n  ".join(bad))


def test_product_and_architecture_stay_separated():
    """Sunny's ruling, 2026-09-01: the product offering lives in its own
    folder. A category=product decision may not claim an architecture
    file as its blueprint — 'what we sell' and 'what we built' are
    different questions, and mixing them is how pricing language ends
    up in a topology document."""
    misfiled = []
    for adr, entry in TRACE_REGISTRY.items():
        doc = ARCHITECTURE_COMPONENTS[entry["component"]]["doc"]
        if entry["category"] == "product" and doc.startswith(
                "docs/architecture/"):
            misfiled.append(
                f"{adr} ({entry['title'][:40]}) -> {doc}: a product "
                f"decision must route through a docs/product/ blueprint")
    assert not misfiled, ("product/architecture separation violated:\n  "
                          + "\n  ".join(misfiled))


def test_hierarchy_is_acyclic_and_totally_covered():
    """No cycles by construction (the tiers are distinct file sets), and
    every axiom group is reached by at least one blueprint — an
    unreachable group means the framework declares law the architecture
    never translates."""
    architecture_docs = {c["doc"] for c in ARCHITECTURE_COMPONENTS.values()}
    decision_docs = {f"docs/decisions/{p.name}"
                     for p in (REPO / "docs" / "decisions").glob("0*.md")}
    assert not (architecture_docs & decision_docs), (
        "tier violation: a file is both blueprint and execution tier")

    covered = {g for c in ARCHITECTURE_COMPONENTS.values()
               for g in c["satisfies"]}
    missing = sorted(AXM_GROUPS - covered)
    assert not missing, (
        f"axiom group(s) no architecture file claims to satisfy: {missing} "
        f"— either a blueprint is missing the declaration, or the group is "
        f"aspirational and should say so in docs/AI_VIA_AXIOMS.md")


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
