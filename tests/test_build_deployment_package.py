"""Tests for scripts/build_deployment_package.py.

The deployment package is what a customer receives. These tests enforce two
contracts: everything the INSTALLATION_GUIDE promises is present, and nothing
internal (strategy docs, real config, tests) ever ships.
"""

import importlib.util
import re
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "build_deployment_package",
    REPO_ROOT / "scripts" / "build_deployment_package.py",
)
bdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bdp)


@pytest.fixture(scope="module")
def built_zip(tmp_path_factory):
    output_dir = tmp_path_factory.mktemp("package")
    return bdp.build_package(REPO_ROOT, output_dir)


@pytest.fixture(scope="module")
def zip_names(built_zip):
    with zipfile.ZipFile(built_zip) as zf:
        return zf.namelist()


def test_zip_name_carries_pyproject_version(built_zip):
    version = bdp.read_version(REPO_ROOT)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert built_zip.name == f"aivia-deployment-package-v{version}.zip"


def test_ships_everything_installation_guide_promises(zip_names, built_zip):
    version = bdp.read_version(REPO_ROOT)
    expected = [
        f"sql_query_agent-{version}-py3-none-any.whl",
        "org_config.yaml",
        "libs/Microsoft.SqlServer.TransactSql.ScriptDom.dll",
        "environment/requirements.txt",
        "notebooks/data_agent_instructions.md",
        "docs/INSTALLATION_GUIDE.md",
        "docs/DATA_DICTIONARY_REQUIREMENTS.md",
        "docs/SECURITY_WHITEPAPER.md",
        "README.txt",
    ]
    for name in expected:
        assert name in zip_names, f"missing from package: {name}"


def test_ships_all_pipeline_notebooks_as_importable_py(zip_names):
    notebook_stems = sorted(
        n.removeprefix("notebooks/").removesuffix(".py")
        for n in zip_names
        if re.fullmatch(r"notebooks/\d{2}_\w+\.py", n)
    )
    expected = sorted(
        p.name.removesuffix(".Notebook")
        for p in REPO_ROOT.glob("[0-9][0-9]_*.Notebook")
    )
    assert notebook_stems == expected
    assert len(expected) >= 6, "pipeline notebooks disappeared from repo root?"


def test_never_ships_internal_docs_or_tests(zip_names):
    forbidden = re.compile(
        r"internal|ROADMAP|POSITIONING|MARKETPLACE|LAUNCH_PLAN|DEMO_SCRIPT"
        r"|DEPLOYMENT_CHECKLIST|REVIEWER_GUIDE|test_one_metric|tests/|\.git",
        re.IGNORECASE,
    )
    leaked = [n for n in zip_names if forbidden.search(n)]
    assert not leaked, f"internal content leaked into package: {leaked}"


def test_shipped_config_is_the_example_not_the_real_one(built_zip):
    example = (REPO_ROOT / "org_config.example.yaml").read_bytes()
    with zipfile.ZipFile(built_zip) as zf:
        shipped = zf.read("org_config.yaml")
    assert shipped == example, "shipped org_config.yaml must be the example defaults"


def test_verify_rejects_zip_with_internal_content(tmp_path):
    bad_zip = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("docs/PRODUCT_POSITIONING.md", "pricing anchors")
    with pytest.raises(bdp.PackagingError, match="POSITIONING"):
        bdp.verify_package(bad_zip)


def test_missing_wheel_fails_loudly(tmp_path):
    skeleton = tmp_path / "repo"
    (skeleton / "dist").mkdir(parents=True)
    (skeleton / "pyproject.toml").write_text('version = "9.9.9"\n')
    with pytest.raises(bdp.PackagingError, match="wheel"):
        bdp.build_package(skeleton, tmp_path)
