"""Pre-flight validation for a deployment root — fail before the pipeline does.

Checks the customer-provided deployment folder (lakehouse
Files/sql-query-agent locally mirrored or mounted) against everything the
pipeline will assume: config parses, the mandatory data dictionary is
present and shaped right (ADR 0014), SQL sources exist, the ScriptDom DLL
is where 02 looks, and 07's llm block points at a reachable-looking
endpoint with a readable key. Every failure states the fix, not just the
problem — the goal is "supportable at a distance."

Usage:
    python scripts/validate_deployment.py [--root PATH]

In Fabric (notebook cell):
    from scripts.validate_deployment import validate, print_report
    print_report(validate(Path("/lakehouse/default/Files/sql-query-agent")))

Exit code 0 = deploy-ready (warnings allowed), 1 = at least one failure.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml  # noqa: E402

from src.schemas import DICT_COLUMNS, DICT_TABLES  # noqa: E402

SCRIPTDOM_DLL = "Microsoft.SqlServer.TransactSql.ScriptDom.dll"


@dataclass
class CheckResult:
    name: str
    level: str  # ok | warn | fail
    message: str


def _ok(name: str, msg: str) -> CheckResult:
    return CheckResult(name, "ok", msg)


def _warn(name: str, msg: str) -> CheckResult:
    return CheckResult(name, "warn", msg)


def _fail(name: str, msg: str) -> CheckResult:
    return CheckResult(name, "fail", msg)


def check_python() -> CheckResult:
    v = sys.version_info
    if (v.major, v.minor) >= (3, 9):
        return _ok("python", f"Python {v.major}.{v.minor}.{v.micro}")
    return _fail("python", f"Python {v.major}.{v.minor} < 3.9 — use a Fabric "
                           "runtime or venv with Python 3.9+")


def check_root(root: Path) -> CheckResult:
    if root.is_dir():
        return _ok("root", f"deployment root: {root}")
    return _fail("root", f"{root} does not exist — pass --root or upload the "
                         "deployment package to Files/sql-query-agent")


def check_org_config(root: Path) -> "tuple[CheckResult, dict]":
    path = root / "org_config.yaml"
    if not path.is_file():
        return _fail("org_config", f"{path.name} missing — copy "
                     "org_config.example.yaml and fill in org values"), {}
    try:
        cfg = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        return _fail("org_config", f"{path.name} does not parse: {e}"), {}
    name = (cfg.get("org") or {}).get("name", "")
    if not name or name == "Example Health System":
        return _warn("org_config", f"{path.name} parses but org.name is "
                     f"{name!r} — set the customer's real org name"), cfg
    return _ok("org_config", f"org.name = {name!r}"), cfg


def check_llm(root: Path, cfg: dict) -> "list[CheckResult]":
    llm = cfg.get("llm") or {}
    if not llm:
        return [_warn("llm", "no llm: block in org_config.yaml — "
                      "600_generate_descriptions will refuse to run. Add "
                      "endpoint/model/api_key_file (see 07's docstring)")]
    results = []
    endpoint = (llm.get("endpoint") or "").strip()
    if not endpoint:
        results.append(_fail("llm.endpoint", "llm block present but endpoint "
                             "is empty"))
    elif not endpoint.startswith("https://"):
        results.append(_fail("llm.endpoint", f"{endpoint!r} is not https — "
                             "keys must never travel over plaintext"))
    else:
        results.append(_ok("llm.endpoint", endpoint))
        if "openai.azure.com" in endpoint and "api-version" not in endpoint:
            results.append(_warn("llm.endpoint", "Azure OpenAI endpoint "
                                 "without api-version — Azure requires "
                                 "?api-version=... on chat completions"))
    key_file = root / (llm.get("api_key_file") or "llm_api_key.txt")
    if not key_file.is_file():
        results.append(_fail("llm.api_key", f"{key_file.name} not found next "
                             "to org_config.yaml — one line, raw key only"))
    elif not key_file.read_text().strip():
        results.append(_fail("llm.api_key", f"{key_file.name} is empty"))
    elif "=" in key_file.read_text():
        results.append(_fail("llm.api_key", f"{key_file.name} contains '=' — "
                             "it must be the raw key, not KEY=value form"))
    else:
        results.append(_ok("llm.api_key", f"{key_file.name} present"))
    return results


def _check_csv(path: Path, required: "list[str]", label: str) -> CheckResult:
    if not path.is_file():
        return _fail(label, f"{path.name} missing — the data dictionary is "
                     "MANDATORY (ADR 0014): without it the agent gives "
                     "incomplete answers. See DATA_DICTIONARY_REQUIREMENTS.md")
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = [h.strip() for h in (reader.fieldnames or [])]
            missing = [c for c in required if c not in headers]
            if missing:
                return _fail(label, f"{path.name} lacks required columns "
                             f"{missing} (has {headers})")
            rows = sum(1 for _ in reader)
    except (csv.Error, UnicodeDecodeError) as e:
        return _fail(label, f"{path.name} unreadable as CSV: {e}")
    if rows == 0:
        return _fail(label, f"{path.name} has headers but zero rows")
    return _ok(label, f"{path.name}: {rows} rows")


def check_dictionary(root: Path) -> "list[CheckResult]":
    dict_dir = root / "dictionary"
    tables_cols = [c[0] for c in DICT_TABLES["columns"] if not c[2]]
    columns_cols = [c[0] for c in DICT_COLUMNS["columns"] if not c[2]]
    return [
        _check_csv(dict_dir / "dict_tables.csv", tables_cols, "dict_tables"),
        _check_csv(dict_dir / "dict_columns.csv", columns_cols, "dict_columns"),
    ]


def check_sql_input(root: Path) -> CheckResult:
    sql_dir = root / "sql_input"
    if not sql_dir.is_dir():
        return _fail("sql_input", "sql_input/ folder missing — upload the "
                     "customer's .sql files (procs and views)")
    n = len(list(sql_dir.glob("*.sql")))
    if n == 0:
        return _fail("sql_input", "sql_input/ contains no .sql files")
    return _ok("sql_input", f"{n} .sql files")


def check_scriptdom(root: Path) -> CheckResult:
    for candidate in (root / "libs" / SCRIPTDOM_DLL, root / SCRIPTDOM_DLL):
        if candidate.is_file():
            return _ok("scriptdom", f"{SCRIPTDOM_DLL} at {candidate.parent.name}/")
    return _warn("scriptdom", f"{SCRIPTDOM_DLL} not found under libs/ — "
                 "200_parse falls back to sqlparse (lower fidelity). Upload "
                 "the DLL for production parse rates")


def check_package() -> CheckResult:
    try:
        import src  # noqa: F401
        version = getattr(src, "__version__", "unknown")
        return _ok("package", f"sql-query-agent {version} importable")
    except ImportError as e:
        return _fail("package", f"library not importable ({e}) — publish the "
                     "environment with the wheel, or %pip install it")


def validate(root: Path) -> "list[CheckResult]":
    results = [check_python(), check_root(root)]
    if results[-1].level == "fail":
        return results
    org_result, cfg = check_org_config(root)
    results.append(org_result)
    results.extend(check_llm(root, cfg))
    results.extend(check_dictionary(root))
    results.append(check_sql_input(root))
    results.append(check_scriptdom(root))
    results.append(check_package())
    return results


def print_report(results: "list[CheckResult]") -> bool:
    icons = {"ok": "[+]", "warn": "[!]", "fail": "[X]"}
    for r in results:
        print(f"{icons[r.level]} {r.name}: {r.message}")
    fails = [r for r in results if r.level == "fail"]
    warns = [r for r in results if r.level == "warn"]
    print(f"\n{len(results) - len(fails) - len(warns)} ok, "
          f"{len(warns)} warnings, {len(fails)} failures")
    if fails:
        print("NOT deploy-ready — fix the failures above and re-run.")
    else:
        print("Deploy-ready." + (" Review warnings before customer handoff."
                                 if warns else ""))
    return not fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/lakehouse/default/Files/sql-query-agent",
                    help="deployment root (default: Fabric lakehouse Files path)")
    args = ap.parse_args()
    ok = print_report(validate(Path(args.root)))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
