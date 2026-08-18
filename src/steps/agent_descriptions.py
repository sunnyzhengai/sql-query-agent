"""Step 07b: Data-Agent description generation (split out of 08, 2026-08-18).

Generation is derivation; publishing is egress. 08 (Collibra) and 13
(PBI) consume ops_agent_descriptions; only this step writes it.

Field-note design decisions (2026-08-18 work run):
- REJECTED (agent non-answer) rows PERSIST with status="rejected" so
  retry/inspection is a query, not a stdout scrollback. Rejected rows
  are re-attempted on the next run (they are failures, not cache).
- Per-batch and final tallies are visually distinct: batch lines are
  emitted through the progress callback; the final summary comes from
  RunResult (including the rejected metric ids).
- Resume-by-rerun survives: every save persists the FULL row set
  (existing + new + rejected), so a dead session resumes by re-running
  and the plan skips everything already current.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Iterable

STATUS_OK = "ok"
STATUS_REJECTED = "rejected"

# Agent responses that are phrased as answers but are non-answers.
REJECT_PHRASES = (
    "wasn't able to find",
    "couldn't find",
    "not found",
    "hasn't been",
    "i'm happy to help",
)

SAVE_EVERY = 25  # persist to Delta every N successful generations


def sql_hash(logic: str) -> str:
    return hashlib.sha256((logic or "").encode()).hexdigest()[:16]


def is_rejection(answer: str) -> bool:
    lowered = (answer or "").lower()
    return any(phrase in lowered for phrase in REJECT_PHRASES)


@dataclass
class GenerationPlan:
    needs_generation: "list[str]"
    reused: "list[str]"
    retrying_rejected: "list[str]"


def plan_generation(
    metric_names: "Iterable[str]",
    current_hashes: "dict[str, str]",
    existing_records: "Iterable[dict]",
) -> GenerationPlan:
    """Hash-based incremental plan.

    A metric needs generation when it has no OK description, or its SQL
    hash changed. Rejected rows always retry (failures are not cache);
    they are listed separately so the run report can say so.
    """
    ok_hashes: "dict[str, str]" = {}
    rejected: "set[str]" = set()
    for r in existing_records:
        if r.get("status", STATUS_OK) == STATUS_OK:
            ok_hashes[r["metric_name"]] = r.get("sql_hash", "")
        else:
            rejected.add(r["metric_name"])

    needs, reused, retrying = [], [], []
    for name in metric_names:
        if name in ok_hashes and ok_hashes[name] == current_hashes.get(name, ""):
            reused.append(name)
        elif name in rejected and name not in ok_hashes:
            retrying.append(name)
            needs.append(name)
        else:
            needs.append(name)
    return GenerationPlan(needs_generation=needs, reused=reused,
                          retrying_rejected=retrying)


@dataclass
class RunResult:
    succeeded: "list[str]" = field(default_factory=list)
    rejected: "list[str]" = field(default_factory=list)
    failed: "list[tuple[str, str]]" = field(default_factory=list)  # (metric, error)
    saves: int = 0

    def summary_lines(self) -> "list[str]":
        lines = [
            "=== FINAL TALLY (this run) ===",
            f"  generated: {len(self.succeeded)}",
            f"  rejected (agent non-answer): {len(self.rejected)}",
            f"  failed (errors): {len(self.failed)}",
        ]
        if self.rejected:
            lines.append("  rejected metric_ids (persisted with status=rejected, "
                         "will retry next run):")
            for name in self.rejected:
                lines.append(f"    {name}")
        if self.failed:
            lines.append("  errors:")
            for name, err in self.failed[:10]:
                lines.append(f"    {name}: {err}")
        return lines


def run_generation(
    needs_generation: "list[str]",
    generate: "Callable[[str], tuple[str, str]]",
    rows: "dict[str, dict]",
    current_hashes: "dict[str, str]",
    save: "Callable[[list[dict]], None]",
    progress: "Callable[[str], None]" = print,
    save_every: int = SAVE_EVERY,
) -> RunResult:
    """Drive generation with incremental full-set saves.

    generate(name) -> (status, text): status "success" with the answer,
    or anything else with an error message. `rows` is the full row set
    (metric_name -> row dict) mutated in place and passed WHOLE to
    `save` — the resume property depends on full-set persistence.
    Batch lines go through `progress`; the caller prints
    result.summary_lines() at the end — the two tallies stay distinct.
    """
    result = RunResult()
    unsaved = 0
    total = len(needs_generation)

    def persist() -> None:
        save(list(rows.values()))
        result.saves += 1

    for i, name in enumerate(needs_generation):
        status, text = generate(name)
        if status == "success" and text and not is_rejection(text):
            rows[name] = {
                "metric_name": name, "description": text,
                "sql_hash": current_hashes.get(name, ""), "status": STATUS_OK,
            }
            result.succeeded.append(name)
            unsaved += 1
        elif status == "success" and text:
            rows[name] = {
                "metric_name": name, "description": text,
                "sql_hash": current_hashes.get(name, ""),
                "status": STATUS_REJECTED,
            }
            result.rejected.append(name)
            unsaved += 1
        else:
            result.failed.append((name, text or "no answer"))

        if unsaved >= save_every:
            persist()
            unsaved = 0
            progress(
                f"  [batch {result.saves} | {i + 1}/{total}] saved — running "
                f"totals this run: {len(result.succeeded)} generated, "
                f"{len(result.rejected)} rejected, {len(result.failed)} failed")
        elif (i + 1) % 10 == 0:
            progress(f"  [{i + 1}/{total}] in progress...")

    if unsaved > 0 or result.saves == 0 and rows:
        persist()
    return result
