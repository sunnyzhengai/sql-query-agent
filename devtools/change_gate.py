"""THE HARD GATE — refuses code edits not covered by an APPROVED brief.

Brief_Hard_Gate_Hook (P2 "hard gate", all six ambiguities ruled
2026-09-16). Wired as a Claude Code PreToolUse hook on
Edit|Write|NotebookEdit in .claude/settings.json.

Stdin: the hook JSON ({"tool_input": {"file_path": ...}}).
Exit 0 allows the edit; exit 2 blocks it with the reason on stderr.
H6: stdlib only; any internal error BLOCKS (fails closed).
"""
import json
import os
import re
import sys
from pathlib import Path

COVERED_ROOTS = ("aisql/", "src/", "devtools/", "tests/",
                 "AIVIA_Test/", "services/", "AIVIA_Product/")
GATE_FILES = (".claude/settings.json", "devtools/change_gate.py")
UNLOCKING = ("APPROVED", "BUILT")


def declared_paths(briefs_dir: Path) -> set:
    """Every exact path listed under `## Files declared` in a brief
    whose status unlocks the gate (H3: APPROVED/BUILT only; H5: one
    path per line, no wildcards)."""
    declared = set()
    for brief in sorted(briefs_dir.glob("*.md")):
        text = brief.read_text(errors="replace")
        status = re.search(r"\*\*Status:\s*([A-Z]+)", text)
        if not status or status.group(1) not in UNLOCKING:
            continue
        section = re.split(r"^## Files declared\s*$", text,
                           maxsplit=1, flags=re.M)
        if len(section) < 2:
            continue
        body = re.split(r"^## ", section[1], maxsplit=1, flags=re.M)[0]
        for line in body.splitlines():
            candidate = line.strip()
            if candidate and re.fullmatch(r"[\w./-]+", candidate):
                declared.add(candidate)
    return declared


def decide(payload: dict, project: Path):
    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw:
        return 2, "THE HARD GATE: no file path in the tool input."
    try:
        rel = Path(raw).resolve().relative_to(project.resolve()).as_posix()
    except ValueError:
        return 0, None  # outside the project — not ours to gate

    if rel.startswith("AIVIA_Design/") or rel.endswith(".md") \
            or rel == ".claude/settings.local.json":
        return 0, None  # verdicts always land

    covered = (rel.startswith(COVERED_ROOTS) or rel in GATE_FILES
               or rel.endswith((".py", ".ipynb")))
    if not covered:
        return 0, None

    if rel in declared_paths(project / "AIVIA_Design" / "briefs"):
        return 0, None

    return 2, (
        f"THE HARD GATE (Ruling_Change_Process P2): '{rel}' is a "
        "covered code path and no APPROVED/BUILT brief in "
        "AIVIA_Design/briefs/ declares it. The change process: "
        "classify -> query the contracts -> brief -> Sunny rules "
        "every ambiguity -> build. Present a brief and get Sunny's "
        "approval before touching this file."
    )


def main() -> int:
    try:
        project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        code, message = decide(json.load(sys.stdin), project)
        if message:
            print(message, file=sys.stderr)
        return code
    except Exception as exc:  # noqa: BLE001 — H6: ANY failure blocks
        print(f"THE HARD GATE: internal error, blocking (fails "
              f"closed): {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
