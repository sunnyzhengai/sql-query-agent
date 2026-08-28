"""Paraphrase-robustness suite — the readiness gate's grader (ADR 0032).

Drives the orchestrator core (the real product spine, not a simulation)
with canonical questions plus LLM-generated paraphrases, and grades
outcomes mechanically against a certified answer key:

    hit@k        expected target appears in the top-k candidates
    top1         expected target is the first candidate
    refusal      nonsense questions return zero candidates
    consistency  across a canonical's paraphrases: top1 agreement and
                 top5 Jaccard overlap vs the canonical's own result
    replay       same token twice -> identical candidate list (tests
                 embedding determinism end to end)

Usage:
    python devtools/robustness_suite.py            # full run (live)
    python devtools/robustness_suite.py --smoke    # canonicals only

Requires: az CLI logged in; capacity active; OPENAI key in .env for the
token-production edge (dev). Costs cents; minutes.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from devtools.grounding_evals import _load_dotenv  # noqa: E402
from devtools.local_llm import chat_completion  # noqa: E402
from src.graph.templates import _fold  # noqa: E402
from src.orchestrator.core import produce_search_token, resolve  # noqa: E402
from src.orchestrator.kusto import KustoClient, az_cli_token_provider  # noqa: E402

QUERY_URI = "https://trd-uzdu1yhqrmqtutkej8.z7.kusto.fabric.microsoft.com"
DATABASE = "semantic_catalog"
PARAPHRASES_PER_QUESTION = 5
TOP_K_FOR_HIT = 5

# Answer key — expectations derived from the certified corpus
# (tests/fixtures/recorded + REMATCH_SCORECARD). `any_of` entries are
# case-folded substrings matched against candidate ref, name, and
# business_name.
CANONICALS = [
    {"id": "ed_screening",
     "q": "How is ED Sepsis Screening calculated?",
     "any_of": ["REPORTING.USP_ED_SEPSIS"], "top_k": TOP_K_FOR_HIT},
    {"id": "readmit",
     "q": "Which patients came back to the emergency room within a day?",
     "any_of": ["ED_READMIT"], "top_k": TOP_K_FOR_HIT},
    {"id": "severe_episodes",
     "q": "How do we track severe sepsis episodes?",
     "any_of": ["USP_SEVERE_SEPSIS", "SEVERE SEPSIS"], "top_k": TOP_K_FOR_HIT},
    {"id": "bundle_compliance",
     "q": "How is sepsis bundle compliance measured?",
     "any_of": ["COMPLIANCE"], "top_k": TOP_K_FOR_HIT},
    {"id": "blood_cultures",
     "q": "When do we order blood cultures for sepsis patients?",
     "any_of": ["BLOODCULTURE", "BLOOD CULTURE"], "top_k": TOP_K_FOR_HIT},
    {"id": "refusal_unicorn",
     "q": "What is the average unicorn readmission velocity?",
     "refusal": True},
    {"id": "refusal_cafeteria",
     "q": "How satisfied are staff with the cafeteria menu this quarter?",
     "refusal": True},
]

PARAPHRASE_PROMPT = (
    "Rewrite the following question {n} different ways a hospital analyst "
    "might naturally ask it. Vary vocabulary and sentence shape; keep the "
    "meaning. Output ONLY the {n} questions, one per line, no numbering.\n\n"
    "Question: {q}"
)


def match(candidate, needles) -> bool:
    hay = " | ".join(
        _fold(x) for x in (candidate.ref, candidate.name, candidate.business_name)
    )
    return any(_fold(n) in hay for n in needles)


def grade(result, spec) -> dict:
    """Group-aware since the stratified-plurality amendment (ADR 0032,
    2026-08-10): the product shows labeled kind groups, so absolute
    position 1 is meaningless across groups. hit = expected target is
    anywhere on the SHOWN list; top1 = expected target LEADS ITS KIND
    GROUP (what a user scanning that group sees first)."""
    if spec.get("refusal"):
        ok = len(result.candidates) == 0
        return {"refused_correctly": ok, "hit": ok, "top1": ok}
    shown = result.candidates
    hit = any(match(c, spec["any_of"]) for c in shown)
    top1 = False
    for i, c in enumerate(shown):
        if match(c, spec["any_of"]):
            top1 = all(prev.kind != c.kind for prev in shown[:i])
            break
    return {"hit": hit, "top1": top1, "refused_correctly": None}


def jaccard(a, b) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb) if (sa or sb) else 1.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="canonicals only")
    args = ap.parse_args()
    _load_dotenv()

    client = KustoClient(QUERY_URI, DATABASE, az_cli_token_provider(QUERY_URI))
    report = {"canonicals": [], "totals": {}}
    latencies = []

    for spec in CANONICALS:
        variants = [spec["q"]]
        if not args.smoke:
            raw = chat_completion(
                "You rewrite questions faithfully.",
                PARAPHRASE_PROMPT.format(n=PARAPHRASES_PER_QUESTION, q=spec["q"]),
            )
            variants += [v.strip() for v in raw.splitlines() if v.strip()][
                :PARAPHRASES_PER_QUESTION
            ]

        runs = []
        for i, question in enumerate(variants):
            token = produce_search_token(question, chat_completion)
            t0 = time.time()
            result = resolve(token, client.run)
            latency = time.time() - t0
            latencies.append(latency)
            runs.append({
                "question": question, "token": token,
                "top5": [c.node_id for c in result.candidates[:5]],
                "shown": [c.node_id for c in result.candidates],
                "total_matches": result.total_matches,
                "latency_s": round(latency, 2),
                **grade(result, spec),
            })
            print(f"[{spec['id']}] v{i} token={token!r} "
                  f"hit={runs[-1]['hit']} top1={runs[-1]['top1']} "
                  f"({latency:.1f}s)")

        # Replay: canonical token twice. Two levels: RANKING stability
        # (node order — the product-visible outcome) and closeness
        # jitter (embedding APIs have tiny run-to-run float noise).
        token0 = runs[0]["token"]
        ra = resolve(token0, client.run).candidates
        rb = resolve(token0, client.run).candidates
        replay_equal = [c.node_id for c in ra] == [c.node_id for c in rb]
        jitter = max(
            (abs(a.closeness - b.closeness)
             for a, b in zip(ra, rb) if a.node_id == b.node_id),
            default=0.0,
        )

        base_top5 = runs[0]["top5"]
        base_top1 = base_top5[0] if base_top5 else None
        para = runs[1:]
        consistency = {
            "top1_agreement": (
                sum(1 for r in para if (r["top5"][0] if r["top5"] else None) == base_top1)
                / len(para) if para else 1.0
            ),
            "top5_jaccard_mean": (
                statistics.mean(jaccard(r["top5"], base_top5) for r in para)
                if para else 1.0
            ),
        }
        report["canonicals"].append({
            "id": spec["id"], "runs": runs,
            "replay_ranking_stable": replay_equal,
            "replay_closeness_jitter": round(jitter, 6),
            **consistency,
        })

    all_runs = [r for c in report["canonicals"] for r in c["runs"]]
    ref_runs = [r for r in all_runs if r["refused_correctly"] is not None]
    ans_runs = [r for r in all_runs if r["refused_correctly"] is None]
    report["totals"] = {
        "questions_run": len(all_runs),
        "hit_at_5": (round(sum(r["hit"] for r in ans_runs) / len(ans_runs), 3)
                     if ans_runs else None),
        "top1": (round(sum(r["top1"] for r in ans_runs) / len(ans_runs), 3)
                 if ans_runs else None),
        "refusal_correct": (round(sum(r["refused_correctly"] for r in ref_runs)
                                  / len(ref_runs), 3) if ref_runs else None),
        "top1_agreement_mean": round(statistics.mean(
            c["top1_agreement"] for c in report["canonicals"]), 3),
        "top5_jaccard_mean": round(statistics.mean(
            c["top5_jaccard_mean"] for c in report["canonicals"]), 3),
        "replay_ranking_stable_all": all(
            c["replay_ranking_stable"] for c in report["canonicals"]),
        "replay_jitter_max": max(
            c["replay_closeness_jitter"] for c in report["canonicals"]),
        "latency_p50_s": round(statistics.median(latencies), 2),
        "latency_max_s": round(max(latencies), 2),
    }
    out = PROJECT_ROOT / "docs" / "internal" / "robustness_baseline.json"
    out.write_text(json.dumps(report, indent=1))
    print("\n=== TOTALS ===")
    for k, v in report["totals"].items():
        print(f"  {k}: {v}")
    print(f"\nreport -> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
