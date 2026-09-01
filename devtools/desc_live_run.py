"""P0-c (DESC-LIVE-1, ruled 2026-08-31 — option (a)): generation over
OUR OWN corpus, honestly rated.

Corpus (no wall crossing — the work estate stays where it belongs):
  · data/synthetic/sql — the 28 de-dialected synthetic procs, parsed
    HERE by ScriptDom into their real CTE steps;
  · optionally the shapes estate's metric compositions (--with-shapes).

Reports aggregate gate behaviour by violation class, the retry
recovery rate, the surgical-fallback rate, and the empty rate; and
writes a SAMPLE FILE — description beside its fragment and its
PARSED FACTS (tables, grain) — for Sunny's hand grading. She is the
acceptance for accuracy; the rates are only the shape of the risk.

THE CAVEAT (ruled, must ride any quoted rate): this corpus spans
both ends — Clarity-shaped sepsis procs AND clean governance
shapes — so DIFFICULTY is real; only SCALE is limited (28 procs,
not an enterprise). Rates are measured, never extrapolated.

Usage:
  python devtools/desc_live_run.py            # parse + generate
  python devtools/desc_live_run.py --dry      # parse only, no calls
  python devtools/desc_live_run.py --limit 40 # cap the steps
Writes: internal/docs/DESC_LIVE_REPORT.md
        internal/docs/DESC_LIVE_SAMPLE.md
"""

from __future__ import annotations

import os.path as _op
import sys as _sys

_sys.path.insert(0, _op.dirname(_op.dirname(_op.abspath(__file__))))

import glob  # noqa: E402
import random  # noqa: E402
from collections import Counter  # noqa: E402

from src.descriptions import (  # noqa: E402
    _grounded_describe,
    grounding_violations,
    parsed_grain,
    parsed_tables,
    subject_for,
)

HONEST_FLOOR = (
    "**Scale caveat (ruled 2026-08-31, corrected same day):** this "
    "corpus spans both ends of the difficulty range — the "
    "de-dialected CLARITY-SHAPED sepsis procs (14,114 lines across "
    "21 procs in reporting/, including the 43-step USP_ED_SEPSIS "
    "whose invented flowsheet IDs created this gate) AND clean "
    "adversarial governance shapes. Difficulty is REAL; what is "
    "limited is SCALE: a 28-proc estate, not a multi-thousand-proc "
    "enterprise. These rates are MEASURED, not extrapolated, and "
    "any place we quote them must carry this sentence."
)

_PROMPT = """You are describing ONE step of a certified metric for a
business audience.

SQL:
{sql}

Write 1-3 bullet lines for a STEWARD, not a developer.
Name the subject as "{subject}" — say "{subject} are included
when …", never "membership" or "the dataset". Never mention
tables, temp tables, joins, queries, columns or datasets: the
source objects are recorded elsewhere. Never expand an acronym
unless this SQL expands it — print it as written. Never invent
values or a counted entity the SQL does not support."""


def harvest_steps(limit: int = 0) -> "list[dict]":
    """Every CTE step in the synthetic corpus, via the REAL parser
    (ScriptDom) — the same path the pipeline uses; no regex."""
    from src.parser.scriptdom_loader import parse_tsql
    steps: "list[dict]" = []
    for path in sorted(glob.glob("data/synthetic/sql/**/*.sql",
                                 recursive=True)):
        sql = open(path).read()
        fragment, errors = parse_tsql(sql)
        if errors or fragment is None:
            steps.append({"proc": _op.basename(path), "name": "(unparsed)",
                          "sql": "", "error": str(errors[:1])})
            continue
        # BEGIN...END wraps most procs' bodies, and a one-level walk
        # missed 25 of 28 procs' CTEs entirely (P0-c coverage find —
        # a "23/23 clean" that silently covered 3 procs). Descend
        # through every statement container the parser exposes.
        def descend(node, depth=0):
            if depth > 6 or node is None:
                return []
            out = [node]
            body = getattr(node, "StatementList", None)
            if body is not None:
                for i in range(body.Statements.Count):
                    out.extend(descend(body.Statements[i], depth + 1))
            for attr in ("Statements",):
                coll = getattr(node, attr, None)
                if coll is not None and hasattr(coll, "Count"):
                    for i in range(coll.Count):
                        out.extend(descend(coll[i], depth + 1))
            return out

        for b in range(fragment.Batches.Count):
            batch = fragment.Batches[b]
            for s in range(batch.Statements.Count):
                inner = descend(batch.Statements[s])
                for st in inner:
                    we = getattr(st, "WithCtesAndXmlNamespaces", None)
                    if we is None:
                        continue
                    names = [str(we.CommonTableExpressions[c]
                                 .ExpressionName.Value)
                             for c in range(
                                 we.CommonTableExpressions.Count)]
                    for c in range(we.CommonTableExpressions.Count):
                        cte = we.CommonTableExpressions[c]
                        text = sql[cte.StartOffset:
                                   cte.StartOffset + cte.FragmentLength]
                        steps.append({
                            "proc": _op.basename(path),
                            "name": str(cte.ExpressionName.Value),
                            # the proc's OTHER CTEs are upstream steps,
                            # not base tables (a step reading them is
                            # reading OUR graph, not the warehouse)
                            "siblings": [n for n in names
                                         if n != str(
                                             cte.ExpressionName.Value)],
                            "sql": text})
    if limit:
        steps = steps[:limit]
    return steps


def run(steps, describe) -> dict:
    counts = Counter()
    classes = Counter()
    rows = []
    for st in steps:
        sql = st.get("sql") or ""
        if not sql.strip():
            counts["unparsed"] += 1
            continue
        prompt = _PROMPT.format(sql=sql, subject=subject_for(sql))
        first = describe(prompt).strip()
        first_v = grounding_violations(first, sql) if first else []
        for v in first_v:
            classes[v.split(":")[0]] += 1
        text, removed = _grounded_describe(describe, prompt, sql, None)
        if not first_v:
            outcome = "clean"
        elif text and not removed:
            outcome = "recovered"
        elif text:
            outcome = "salvaged"
        else:
            outcome = "emptied"
        counts[outcome] += 1
        rows.append({**st, "text": text, "outcome": outcome,
                     "first_violations": first_v,
                     "tables": sorted(
                         parsed_tables(sql)
                         - {s.lower() for s in st.get("siblings", [])}),
                     "grain": sorted(parsed_grain(sql))})
    return {"counts": counts, "classes": classes, "rows": rows}


def write_reports(result: dict, sample_n: int = 30) -> None:
    c, cls, rows = result["counts"], result["classes"], result["rows"]
    graded = sum(c[k] for k in
                 ("clean", "recovered", "salvaged", "emptied"))
    n = graded or 1
    pct = lambda k: f"{100 * c[k] / n:.0f}%"  # noqa: E731
    lines = [
        "# P0-c — description generation over our own corpus", "",
        HONEST_FLOOR, "",
        f"**{graded} description(s) generated** "
        f"(+{c['unparsed']} unparsed proc(s) skipped)", "",
        "**Coverage (stated, not implied):** the pipeline describes "
        "CTE STEPS, and only 5 of the corpus's 28 procs use CTEs — "
        "the other 23 stage through temp tables (15 of them "
        "explicitly). So this run covers every CTE step the estate "
        "HAS, which is not the same as every proc. Temp-table "
        "staging is a real Clarity pattern and describing it is a "
        "separate (unbuilt) capability, not a gap in these rates.",
        "",
        f"- clean (passed first try): {c['clean']} ({pct('clean')})",
        f"- recovered (corrective retry fixed it): {c['recovered']} "
        f"({pct('recovered')})",
        f"- salvaged (surgical fallback kept grounded lines): "
        f"{c['salvaged']} ({pct('salvaged')})",
        f"- emptied (absence over fabrication): {c['emptied']} "
        f"({pct('emptied')})", "",
        "## First-pass violations by class", "",
    ]
    if not cls:
        lines.append("- none")
    for klass, k in cls.most_common():
        lines.append(f"- {klass}: {k}")
    lines += ["", "## Reading these numbers", "",
              "A HIGH recovered/salvaged rate is a finding about "
              "GENERATION quality, not a gate failure — the gate is "
              "doing its job either way. An EMPTIED description is "
              "the honest floor: absence over fabrication.", ""]
    with open("internal/docs/DESC_LIVE_REPORT.md", "w") as f:
        f.write("\n".join(lines))

    rnd = random.Random(20260831)          # deterministic sample
    pick = rows if len(rows) <= sample_n else rnd.sample(rows, sample_n)
    pick.sort(key=lambda r: (r["proc"], r["name"]))
    sample = ["# P0-c sample — for Sunny's hand grading", "",
              HONEST_FLOOR, "",
              "For each: the generated description, the fragment it "
              "describes, and the PARSED FACTS the gate checked it "
              "against. Grade the DESCRIPTION, not the rates.", ""]
    for r in pick:
        sample += [
            f"## {r['proc']} · {r['name']}",
            f"*outcome: {r['outcome']}* · parsed tables: "
            f"{', '.join(r['tables']) or '—'} · parsed grain: "
            f"{', '.join(r['grain']) or '(unknown)'}", "",
            "**Description**", "",
            (r["text"] or "_(emptied — nothing grounded survived)_"),
            "", "**Fragment**", "", "```sql", r["sql"].strip(), "```",
        ]
        if r["first_violations"]:
            sample += ["", "first pass violated: "
                       + "; ".join(r["first_violations"])[:300]]
        sample.append("")
    with open("internal/docs/DESC_LIVE_SAMPLE.md", "w") as f:
        f.write("\n".join(sample))


def main() -> None:
    limit = 0
    if "--limit" in _sys.argv:
        limit = int(_sys.argv[_sys.argv.index("--limit") + 1])
    steps = harvest_steps(limit)
    parsed = [s for s in steps if s.get("sql")]
    print(f"harvested {len(parsed)} step(s) from "
          f"{len({s['proc'] for s in steps})} proc(s)")
    if "--dry" in _sys.argv:
        for s in parsed[:12]:
            print(f"  {s['proc']} · {s['name']}: "
                  f"tables={sorted(parsed_tables(s['sql']))} "
                  f"grain={sorted(parsed_grain(s['sql']))}")
        return
    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.agent import azure_chat_api
    api = azure_chat_api()

    def describe(prompt: str) -> str:
        msg = api([{"role": "user", "content": prompt}], [])
        return str(msg.get("content") or "")

    result = run(steps, describe)
    write_reports(result)
    c = result["counts"]
    print(f"clean {c['clean']} · recovered {c['recovered']} · "
          f"salvaged {c['salvaged']} · emptied {c['emptied']}")
    print("wrote internal/docs/DESC_LIVE_REPORT.md + _SAMPLE.md")


if __name__ == "__main__":
    main()
