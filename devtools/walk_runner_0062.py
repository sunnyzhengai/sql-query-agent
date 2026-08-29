"""TESTPLAN_0062 section E — the headless walk-runner.

Runs the B-battery (Sunny's real phrasings) + the DEMO_SCRIPT V2 QA
questions against a RUNNING workbench via the API; per question
records the card (matches / proposal / no_match / latency split),
then confirms runnable cards and records the outputs, conclusion
verdict, and execute latency. Writes the transcript for review's
diff against the plan's expectations.

Run (workbench up on :8000):
    python devtools/walk_runner_0062.py [base_url] [out_path]
Defaults: http://127.0.0.1:8000  internal/docs/WALK_TRANSCRIPT_0062.md
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

B_BATTERY = [
    ("B1", "Are all the Diabetic codesets defined the same?"),
    ("B2", "are these 3 metrics using the same definition: High ED "
           "Utilizers Without PCP High ED Utilizers "
           "(reporting.USP_High_ED_Utilizers) High ED Utilizers "
           "(reports.USP_High_ED_Utilizers)"),
    ("B3", "what does Active Diabetic Patients "
           "(reporting.USP_Active_Diabetics) use to define the "
           "patient cohort"),
    ("B4", "which metrics use ENCOUNTERS?"),  # RW-BATCH-6 item 4: the seed store table name
    ("B5", "What governance red flags exist for Diabetic Patients?"),
    ("B6", "Which certified metrics feed the Diabetes Registry "
           "dashboard?"),
    ("B7", "is there another way of defining diabetic patient cohort "
           "other than the logic in the Dx_Path, Lab_Path, Med_Path"),
    ("B8", "Diabetic Codeset"),
    ("B9", "what is the weather today"),
    ("B10", "How many patients are currently in the Diabetic "
            "Patients cohort?"),
    # RW-BATCH-7 item 4: Sunny's three fresh questions verbatim +
    # a kind-only case + near-miss-name cases
    ("B11", "diabetes codeset"),
    ("B12", "diabetic patient cohort definition"),
    ("B13", "what metrics are there"),
    ("B14", "list all reports"),
    ("B15", "diabetics registry"),
    # RW-23: Sunny's verbatim tables question — the runner prints
    # card CONTENT so review asserts real table names, not kinds
    ("B16", "what tables does metric Active Diabetic Patients use"),
]

QA_V2 = [
    ("QA1", "What certified metrics do we have about diabetes?"),
    ("QA2", "How is the Diabetic Patients cohort defined?"),
    ("QA3", "Are all the Diabetic codesets defined the same?"),
    ("QA4", "Which reports read the Diabetes Registry?"),
    ("QA5", "What governance red flags exist for Diabetic Patients?"),
    ("QA6", "How many patients are in the registry right now?"),
]


def _post(base: str, path: str, payload: dict) -> "tuple[dict, int]":
    req = urllib.request.Request(
        base + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode()), r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return json.loads(raw or "{}"), e.code
        except json.JSONDecodeError:
            return {"error": raw[:300]}, e.code


def run(base: str, out_path: str) -> None:
    lines = ["# WALK TRANSCRIPT 0062 (headless battery)\n",
             f"Base: {base}\n"]
    for tag, q in B_BATTERY + QA_V2:
        t0 = time.monotonic()
        try:
            card, status = _post(base, "/api/ask", {"message": q})
        except Exception as e:  # noqa: BLE001 — battery must survive
            lines.append(f"\n## {tag}: {q}")
            lines.append(f"- BATTERY ERROR at ask: {type(e).__name__}: {e}")
            Path(out_path).write_text("\n".join(lines) + "\n")
            continue
        card_ms = int((time.monotonic() - t0) * 1000)
        lines.append(f"\n## {tag}: {q}")
        lines.append(f"- card status {status} in {card_ms} ms; "
                     f"latency split: {card.get('latency_ms')}")
        lines.append(f"- proposal: {card.get('parse_confirm')!r}")
        lines.append(f"- no_match: {card.get('no_match', False)}")
        for s in card.get("show") or []:
            names = ", ".join(m["name"] for m in s["matches"]) or "—"
            lines.append(f"  - matched {s['entity']!r}: {names}")
        if card.get("no_match") or "parse_confirm" not in card:
            continue
        t1 = time.monotonic()
        try:
            fin, status2 = _post(base, "/api/parse/confirm", {
                "conversation_id": card.get("conversation_id")})
        except Exception as e:  # noqa: BLE001
            lines.append(f"- BATTERY ERROR at confirm: {type(e).__name__}: {e}")
            Path(out_path).write_text("\n".join(lines) + "\n")
            continue
        exec_ms = int((time.monotonic() - t1) * 1000)
        lines.append(f"- confirm status {status2} in {exec_ms} ms; "
                     f"execute: {fin.get('latency_ms')}")
        if status2 != 200:
            lines.append(f"- refusal: {fin.get('message')!r}")
            continue
        ops = [o["component"]["op"] for o in fin.get("outputs") or []]
        lines.append(f"- ops: {ops}")
        concl = fin.get("conclusion") or {}
        lines.append(f"- conclusion kind: {concl.get('kind')} "
                     f"verdict: {concl.get('verdict', '')}")
        # RW-23 content assertions: the card FIELDS are on record
        for it in (concl.get("items") or [])[:6]:
            lines.append(f"  - item: {it.get('name')} · reads: "
                         f"{it.get('source_tables')} · steps: "
                         f"{it.get('steps')}")
        for fld in ("executes_metrics", "reads_tables", "measures"):
            if concl.get(fld):
                lines.append(f"  - {fld}: {concl[fld]}")
        if concl.get("count_line"):
            lines.append(f"  - count_line: {concl['count_line']}")
        for d in (concl.get("diff_lines") or [])[:3]:
            lines.append(f"  - diff: {d}")
        Path(out_path).write_text("\n".join(lines) + "\n")
    text = "\n".join(lines) + "\n"
    with open(out_path, "w") as f:
        f.write(text)
    print(f"wrote {out_path} ({len(B_BATTERY) + len(QA_V2)} questions)")


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    out = (sys.argv[2] if len(sys.argv) > 2
           else "internal/docs/WALK_TRANSCRIPT_0062.md")
    run(base, out)
