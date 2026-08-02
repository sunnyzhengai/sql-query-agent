"""Build the customer deployment package.

Assembles everything INSTALLATION_GUIDE.md tells the customer to expect into a
single zip, using a strict allowlist. Internal content (docs/internal/, the
real org_config.yaml, tests, strategy docs) can never ship because nothing is
included that isn't explicitly listed here — and verify_package() re-scans the
finished zip as a second line of defense.

Usage:
    python scripts/build_deployment_package.py [--output-dir dist]
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path


class PackagingError(Exception):
    """The package could not be built or failed verification."""


# Customer-facing docs shipped under docs/ inside the package.
SHIPPED_DOCS = [
    "docs/deployment/INSTALLATION_GUIDE.md",
    "docs/deployment/DATA_DICTIONARY_REQUIREMENTS.md",
    "docs/product/SECURITY_WHITEPAPER.md",
]

# Nothing matching these may ever appear in the finished zip.
FORBIDDEN = re.compile(
    r"internal|ROADMAP|POSITIONING|MARKETPLACE|LAUNCH_PLAN|DEMO_SCRIPT"
    r"|DEPLOYMENT_CHECKLIST|REVIEWER_GUIDE|test_one_metric|tests/|\.git",
    re.IGNORECASE,
)

README_TXT = """AIVIA — SQL Intelligence Agent for Fabric
Deployment package v{version}

START HERE: docs/INSTALLATION_GUIDE.md

Contents:
  sql_query_agent-{version}-py3-none-any.whl   Product library (upload to Fabric Environment)
  org_config.yaml                              Configuration defaults (set your org name)
  libs/                                        ScriptDom DLL (upload to Lakehouse Files/sql-query-agent/libs/)
  environment/requirements.txt                 Pinned packages for the Fabric Environment
  notebooks/                                   Pipeline notebooks (import in numbered order) + Data Agent instructions
  docs/                                        Installation guide, data dictionary requirements, security whitepaper

Support: support@aiviaapp.com
"""


def read_version(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    if not match:
        raise PackagingError("could not read version from pyproject.toml")
    return match.group(1)


def collect_contents(repo_root: Path, version: str) -> "dict[str, Path]":
    """Map of archive name -> source file, built as a strict allowlist."""
    wheel = repo_root / "dist" / f"sql_query_agent-{version}-py3-none-any.whl"
    if not wheel.exists():
        raise PackagingError(
            f"wheel not found: {wheel}\n"
            f"pyproject.toml says version {version} — build it first: "
            f"python -m build --wheel"
        )

    contents = {
        wheel.name: wheel,
        # Ship the example as the defaults file; the real org_config.yaml is
        # gitignored and must never leave this machine.
        "org_config.yaml": repo_root / "org_config.example.yaml",
        "libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll": (
            repo_root / "libs" / "Microsoft.SqlServer.TransactSql.ScriptDom.dll"
        ),
        "environment/requirements.txt": repo_root / "environment" / "requirements.txt",
        "notebooks/data_agent_instructions.md": (
            repo_root / "notebooks" / "data_agent_instructions.md"
        ),
    }

    # Pipeline notebooks: NN_name.Notebook/notebook-content.py -> notebooks/NN_name.py
    # (Fabric's "Import notebook" accepts .py files.) Only numbered pipeline
    # notebooks ship; test/utility notebooks never do.
    for nb_dir in sorted(repo_root.glob("[0-9][0-9]_*.Notebook")):
        source = nb_dir / "notebook-content.py"
        if not source.exists():
            raise PackagingError(f"notebook content missing: {source}")
        stem = nb_dir.name.removesuffix(".Notebook")
        contents[f"notebooks/{stem}.py"] = source
    if not any(name.startswith("notebooks/0") for name in contents):
        raise PackagingError("no pipeline notebooks found at repo root")

    for doc in SHIPPED_DOCS:
        contents[f"docs/{Path(doc).name}"] = repo_root / doc

    missing = [str(src) for src in contents.values() if not src.exists()]
    if missing:
        raise PackagingError("missing package inputs:\n  " + "\n  ".join(missing))
    return contents


def verify_package(zip_path: Path) -> None:
    """Second line of defense: scan the finished zip for internal content."""
    with zipfile.ZipFile(zip_path) as zf:
        leaked = [n for n in zf.namelist() if FORBIDDEN.search(n)]
    if leaked:
        raise PackagingError(f"internal content leaked into package: {leaked}")


def build_package(repo_root: Path, output_dir: Path) -> Path:
    version = read_version(repo_root)
    contents = collect_contents(repo_root, version)

    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"aivia-deployment-package-v{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", README_TXT.format(version=version))
        for arcname, source in sorted(contents.items()):
            zf.write(source, arcname)

    verify_package(zip_path)
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the customer deployment package")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("dist"),
        help="Directory for the zip (default: dist/)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    try:
        zip_path = build_package(repo_root, args.output_dir)
    except PackagingError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    size_mb = zip_path.stat().st_size / 1_048_576
    print(f"Built {zip_path} ({size_mb:.1f} MB, {len(names)} files)")
    for name in sorted(names):
        print(f"  {name}")


if __name__ == "__main__":
    main()
