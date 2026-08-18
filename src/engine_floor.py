"""Version binding between notebooks and the engine wheel (ADR 0042).

The field week's recurring failure class: a notebook synced ahead of
the wheel (or a stale wheel behind the notebooks) fails somewhere deep
with an AttributeError that looks like a product bug. Every notebook's
cell 0 declares REQUIRES_ENGINE and calls require_engine — skew dies
loudly, at the top, with the remediation in the message.
"""

from __future__ import annotations


def _version_tuple(version: str) -> "tuple[int, ...]":
    parts = []
    for p in version.strip().split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else (0,)


def require_engine(current: str, floor: str, notebook: str) -> None:
    """Fail LOUDLY when the installed engine is older than the notebook
    requires. Compares major.minor(.patch) numerically."""
    if _version_tuple(current) < _version_tuple(floor):
        raise SystemExit(
            f"[X] ENGINE TOO OLD for {notebook}: installed v{current}, "
            f"requires >= {floor}.\n"
            f"    The notebook and the wheel are out of sync. Update the "
            f"sql-logic-env Environment to the current wheel (or sync the "
            f"workspace to the matching release) and re-run."
        )
