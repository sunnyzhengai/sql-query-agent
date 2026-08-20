"""Term hygiene — no proprietary scan term on any fully-synthetic surface.

Origin (2026-08-20): the morning vendor-name scrub renamed the corpus
and dictionary, but residue survived in surfaces the wave missed — the
git-synced demo SQL database item, the demo seed supplement, and the
recorded-fixtures manifest notes. This gate runs the crosswalk's
_scan_terms over every surface that is DEFINED to be 100% synthetic,
so residue of that class can never ship again.

Deliberately scoped: the product legitimately says 'Clarity' in its
Clarity connector, the anonymization tooling must name what it scrubs,
and PHI tests need the real column names. Those functional mentions
are not leaks. The synthetic surfaces below, by contrast, must be
completely vendor-term-free — that is what 'synthetic' means.
"""

import subprocess
from pathlib import Path

from src.anonymization import get_scan_terms, load_crosswalk, scan_for_missed

REPO = Path(__file__).resolve().parent.parent
CROSSWALK = REPO / "data" / "synthetic" / "crosswalk.json"

# Tracked prefixes that must be 100% synthetic.
SYNTHETIC_SURFACES = (
    "aivia_demo_src.SQLDatabase/",
    "data/demo/",
    "data/synthetic/",
    "tests/fixtures/",
    "tests/golden/",
    "ED Sepsis Screening Dashboard.SemanticModel/",
    "ED Sepsis Screening Dashboard.Report/",
)

# Sanctioned exceptions inside those surfaces: the mapping itself and
# its paraphrase cache — they ARE the crosswalk (Sunny-directed).
_EXEMPT = {
    "data/synthetic/crosswalk.json",
    "data/synthetic/.paraphrase_cache.json",
}
_BINARY_SUFFIXES = {".whl", ".png", ".jpg", ".jpeg", ".gif", ".dll",
                    ".pyc", ".zip", ".pptx", ".pbix", ".ico"}


def _synthetic_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True,
        check=True,
    ).stdout
    for line in out.splitlines():
        if not line.startswith(SYNTHETIC_SURFACES):
            continue
        if line in _EXEMPT or Path(line).suffix.lower() in _BINARY_SUFFIXES:
            continue
        yield line


def test_synthetic_surfaces_carry_no_vendor_terms():
    terms = get_scan_terms(load_crosswalk(CROSSWALK))
    offenders = []
    for rel in _synthetic_files():
        try:
            text = (REPO / rel).read_text(errors="replace")
        except OSError:
            continue
        hits = scan_for_missed(text, terms)
        if hits:
            offenders.append(f"{rel}: {hits[:2]}")
    assert not offenders, (
        "vendor term(s) on a synthetic surface — rename via the "
        "crosswalk (data/synthetic/crosswalk.json):\n  "
        + "\n  ".join(offenders[:15])
    )


def test_scan_terms_cover_the_confirmed_vendor_views():
    """The three names Sunny confirmed as vendor (2026-08-20) must stay
    in the scan set — deleting them from the crosswalk would silently
    disarm this gate."""
    terms = set(get_scan_terms(load_crosswalk(CROSSWALK)))
    assert {"V_LOG_BASED", "DM_ICU_STAY", "V_ICU_STAY_METRICS"} <= terms
