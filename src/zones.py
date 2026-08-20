"""Declared zones (Sunny's verdict, 2026-08-20): everything we ship is
governed; everything unshipped lives in one declared zone.

The repo partitions into governed ⊎ internal — every top-level path is
either a governed, registered artifact or lives under `internal/`; an
unclassified path fails CI (tests/test_zones.py). The deployment
package's allowlist (scripts/build_deployment_package.py) remains the
shipped-boundary truth: zones govern the REPO, the allowlist governs
the ZIP, and `internal` stays in the package's FORBIDDEN pattern so
nothing in the internal zone can ever ship.

Local-only material (learning/, presentation/, private/) also lives
under internal/ but is gitignored — the zone law is checked over
TRACKED paths, which is exactly what customers and CI can see.
"""

from __future__ import annotations

# Fabric workspace items, git-synced by the workspace connection.
GOVERNED_SUFFIXES = (
    ".Notebook", ".Report", ".SemanticModel", ".DataAgent",
    ".SQLDatabase", ".Lakehouse", ".Environment", ".Eventhouse",
    ".KQLQueryset", ".GraphModel",
)

# Every non-Fabric top-level entry must be declared here to be governed.
GOVERNED_ENTRIES = frozenset({
    ".github",
    ".gitignore",
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "pyproject.toml",
    "org_config.example.yaml",
    "data",
    "devtools",
    "dist",
    "docs",
    "environment",
    "libs",
    "marketplace_host",
    "notebooks",
    "scripts",
    "src",
    "tests",
    "website",
})

INTERNAL_ZONE = "internal"


def classify(entry: str) -> "str | None":
    """Zone of a top-level entry: 'governed', 'internal', or None
    (unclassified — a CI failure, never a silent third state)."""
    if entry == INTERNAL_ZONE:
        return "internal"
    if entry in GOVERNED_ENTRIES or entry.endswith(GOVERNED_SUFFIXES):
        return "governed"
    return None
