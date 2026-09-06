"""Shared run accounting — open/close with outcome (REWORK of the
proven run layer, gaining H10's abort semantics).

A run that dies mid-flight closes ABORTED with whatever accounting it
accumulated — resume is just the staleness lens's next reading (the
worklist self-heals; per-artifact atomicity means nothing half-exists).
"""
from dataclasses import dataclass, field
from typing import Any, Dict

from aivia.graph import kg3_artifacts


@dataclass
class Run:
    author: str
    basis: Dict[str, Any]
    occurred_at: str
    accounting: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def open_run(author: str, basis: Dict[str, Any], occurred_at: str) -> Run:
    return Run(author=author, basis=basis, occurred_at=occurred_at)


def close_run(store, run: Run, outcome: str):
    return kg3_artifacts.append_run_event(
        store, author=run.author, basis=run.basis,
        accounting=run.accounting, outcome=outcome,
        occurred_at=run.occurred_at)
