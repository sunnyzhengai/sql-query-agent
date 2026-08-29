"""Endpoint hygiene — no tenant endpoint ever lives in this repo.

Origin (2026-08-20, Sunny's ruling: "set up gates for this to not
happen to any future customers"): the demo dashboard's git sync copied
its SQL connection — a real Fabric SQL endpoint host + database name —
into the PUBLIC repo inside TMDL partition definitions, and a stray
paste file carried the same address. Both were scrubbed from history;
this gate makes the class impossible to reintroduce, for us and for
every customer who ever git-syncs a workspace against this codebase.

The check scans EVERY text file in the tree (no extension allowlist —
the original leak lived in .tmdl, which an earlier scan skipped) for
host-shaped tenant endpoints. Documented placeholders (<server>.…,
example.…) and the bare AAD token audience pass by construction:
the pattern requires a real-looking host label.

Proves: law:endpoint-hygiene
"""

import re
from pathlib import Path

REPO = Path(__file__).parent.parent

# A real tenant endpoint host: a long host label directly in front of
# a Fabric/Azure SQL domain. Placeholders like "<server>." or
# "example." are too short / non-matching by design.
_ENDPOINT = re.compile(
    r"[a-z0-9][a-z0-9-]{9,}\."
    r"(?:database|datawarehouse|api)\."
    r"(?:fabric\.microsoft\.com|windows\.net)",
    re.IGNORECASE,
)

_SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}
_SKIP_SUFFIXES = {".whl", ".png", ".jpg", ".jpeg", ".gif", ".dll",
                  ".pyc", ".zip"}


def _text_files():
    # Scope = every file that IS in git or COULD enter it (tracked +
    # untracked-not-ignored). Gitignored files are exempt BY MECHANISM,
    # not by name: gitignore is what keeps them out of the public repo,
    # and org_config.yaml is the SANCTIONED local home for tenant
    # values (the run layer's `run:` block lives there by design —
    # live find 2026-08-29, the first sanctioned local endpoint this
    # gate met). Un-ignoring such a file puts it straight back in
    # scope, so the leak class stays impossible.
    import subprocess
    out = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        path = REPO / line
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        yield path


def test_no_tenant_endpoint_anywhere_in_the_tree():
    offenders = []
    for path in _text_files():
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        for m in _ENDPOINT.finditer(text):
            offenders.append(f"{path.relative_to(REPO)}: …{m.group(0)[:24]}…")
    assert not offenders, (
        "tenant endpoint(s) in the repo — connections belong in "
        "WORKSPACE settings (semantic-model parameters), never in git:\n  "
        + "\n  ".join(offenders[:10])
    )


def test_semantic_model_sources_are_parameterized():
    """The demo model's partitions must reference the parameter
    expressions, never literal connection strings."""
    tables = REPO / "ED Sepsis Screening Dashboard.SemanticModel" / \
        "definition" / "tables"
    if not tables.exists():
        return  # model not present in this checkout
    for tmdl in tables.glob("*.tmdl"):
        text = tmdl.read_text(errors="replace")
        for m in re.finditer(r"Sql\.Database\(([^,]+),", text):
            first_arg = m.group(1).strip()
            assert not first_arg.startswith('"'), (
                f"{tmdl.name}: Sql.Database called with a literal server "
                f"string — use the DemoSqlServer parameter expression"
            )


def test_the_sanctioned_local_config_is_actually_ignored():
    """The scope exemption in _text_files is EARNED, not assumed: the
    file holding tenant values must be gitignored, or the scan above
    would rightly see it again."""
    import subprocess
    rc = subprocess.run(["git", "check-ignore", "-q", "org_config.yaml"],
                        cwd=REPO).returncode
    assert rc == 0, ("org_config.yaml is not gitignored — tenant "
                     "values would enter the repo")
