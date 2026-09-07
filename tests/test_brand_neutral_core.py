"""Brand-neutral core contract (HANDOFF_BRAND_NEUTRAL_CORE, 2026-08-17).

The commercial name must not appear anywhere in src/ or the numbered
notebooks: the brand is deployment CONFIG (SQA_PRODUCT_NAME / org_config),
never code. Two motives: (1) home->work snapshots are allowed only for
files that never mention the brand; (2) white-label/OEM tiers need a
brand-free engine. Enforcement is a grep, so the name cannot creep back.

Branded-by-design surfaces (website/, presentation/, marketplace_host/,
docs/, CHANGELOG, Fabric item folders like the admin telemetry report)
are deliberately out of scope — see docs/deployment/BRAND_NEUTRAL_SNAPSHOT.md.

Proves: law:brand-separation
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BRAND = re.compile("aivia", re.IGNORECASE)

# Files allowed to contain the brand, with reasons. Keep EMPTY if possible.
ALLOWLIST: "dict[str, str]" = {
    # Both entries are FILESYSTEM PATH references to the branded-by-
    # design top-level folders (AIVIA_Design/, AIVIA_Product/, aivia/),
    # which the brand law already scopes out. The zone law requires
    # every tracked top-level path be declared; the trace registry
    # names the modules/tests an ADR governs. Neither uses the brand
    # as a product string — product naming stays config (2026-09-06,
    # the zone-gate collision found at the Phase A build).
    "src/zones.py": "governed-entries list must name tracked paths",
    "src/trace_registry.py": "ADR entries cite module/test paths",
    "src/spec_registry.py": "axiom checks cite test paths (Group W)",
}


def _core_files():
    yield from REPO.glob("src/**/*.py")
    yield from REPO.glob("*.Notebook/notebook-content.py")


def test_core_contains_no_brand_strings():
    offenders = []
    for path in _core_files():
        rel = str(path.relative_to(REPO))
        if rel in ALLOWLIST:
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if BRAND.search(line):
                offenders.append(f"{rel}:{lineno}: {line.strip()[:80]}")
    assert not offenders, (
        "brand strings in the core (use src/branding.py product_name() or "
        "config instead):\n  " + "\n  ".join(offenders)
    )
