"""THE CI-LINT PATH TRIPWIRE (Brief_CI_Lint, ruled 2026-09-20
"agree with all three, build it"): every path the CI lint step
names must be TRACKED in the repo. A path that exists only on a
local disk lints green here and E902s in CI (F13's `notebooks/`);
a glob for retired folders passes through literally (F13's
`./*.Notebook/`). And the three retired eval corpses stay gone —
they imported the retired src.orchestrator/src.parser and could
not run at all.

Proves: contract:aisql-design-to-code
(the Proves line landed 2026-09-20 during Brief_Pilot_Build_2's
full-suite gate — Brief_CI_Lint's close missed it; a field fix
to that brief's file, Sunny's word recorded in the ledger)"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _lint_paths():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    line = next(ln for ln in text.splitlines()
                if "ruff check" in ln and not ln.strip().startswith("#"))
    args = line.split()
    return [a for a in args[args.index("check") + 1:]
            if not a.startswith("-")]


def test_every_ci_lint_path_is_tracked_and_glob_free():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True,
        text=True, check=True).stdout.splitlines()
    paths = _lint_paths()
    assert paths, "no paths found on the ci.yml ruff line"
    for p in paths:
        clean = p.lstrip("./").rstrip("/")
        assert not re.search(r"[*?\[]", clean), (
            f"glob on the lint line: {p} — a retired folder's glob "
            "passes through literally and E902s (F13)")
        assert any(t == clean or t.startswith(clean + "/")
                   for t in tracked), (
            f"CI lints {p} but the repo does not track it — green "
            "locally, E902 in the checkout (F13)")


def test_the_retired_eval_corpses_stay_gone():
    for name in ("answer_evals.py", "grounding_evals.py",
                 "local_llm.py"):
        assert not (ROOT / "devtools" / name).exists(), (
            f"devtools/{name} is retired (Brief_CI_Lint, 2026-09-20 "
            "— it imports modules retired 2026-09-19 and cannot run)")
