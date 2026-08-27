"""TEST_MAP totality (morning order 1, 2026-08-27): every test module
declares what it proves — via a TRACE_REGISTRY claim (ADR linkage, one
writer) or a docstring `Proves:` line (law/contract linkage, one
writer). The generated map stays fresh in CI (PIPELINE_MAP pattern).

Proves: contract:suite-legibility
"""

from pathlib import Path

from devtools.suite_map import (
    KNOWN_CONTRACTS,
    KNOWN_LAWS,
    accounting,
    build_test_map,
    parse_proves,
    registry_claims,
    scan_suite,
)

REPO = Path(__file__).resolve().parent.parent


# --- the docstring grammar --------------------------------------------


def test_parse_proves_reads_tags():
    assert parse_proves("Blah.\n\nProves: law:live-probe, "
                        "contract:toolchain\n") == [
        "law:live-probe", "contract:toolchain"]


def test_parse_proves_absent_is_empty():
    assert parse_proves("Just a docstring.") == []


def test_adr_tags_are_forbidden_in_docstrings():
    # ADR linkage has ONE writer: src/trace_registry.py. A docstring
    # adr: tag would be a second truth that can drift.
    _, invalid = accounting(
        [{"path": "tests/test_x.py", "first_line": "x",
          "tags": ["adr:0040"], "n_tests": 1}], {})
    assert invalid and "adr:" in invalid[0]


def test_unknown_slug_is_invalid():
    _, invalid = accounting(
        [{"path": "tests/test_x.py", "first_line": "x",
          "tags": ["law:no-such-law"], "n_tests": 1}], {})
    assert invalid


def test_undeclared_module_is_unaccounted():
    unaccounted, _ = accounting(
        [{"path": "tests/test_x.py", "first_line": "x",
          "tags": [], "n_tests": 1}], {})
    assert unaccounted == ["tests/test_x.py"]


# --- totality over the REAL suite -------------------------------------


def test_every_test_module_declares_what_it_proves():
    mods = scan_suite(REPO)
    unaccounted, invalid = accounting(mods, registry_claims())
    assert not invalid, "invalid Proves tags:\n  " + "\n  ".join(invalid)
    assert not unaccounted, (
        "test modules proving nothing on record — claim them in "
        "TRACE_REGISTRY or add a docstring Proves: line:\n  "
        + "\n  ".join(unaccounted))


def test_law_and_contract_registries_have_titles():
    for reg in (KNOWN_LAWS, KNOWN_CONTRACTS):
        for slug, title in reg.items():
            assert slug and title, (slug, title)


def test_every_declared_law_and_contract_is_used():
    # a slug nothing proves is a dead registry row
    used = {t for m in scan_suite(REPO) for t in m["tags"]}
    for kind, reg in (("law", KNOWN_LAWS), ("contract", KNOWN_CONTRACTS)):
        for slug in reg:
            assert f"{kind}:{slug}" in used, f"unused {kind}:{slug}"


# --- freshness (the PIPELINE_MAP pattern) ------------------------------


def test_test_map_on_disk_is_fresh():
    on_disk = (REPO / "docs" / "architecture" / "TEST_MAP.md").read_text()
    assert on_disk == build_test_map(), (
        "TEST_MAP.md is stale — run: python scripts/generate_docs.py")
