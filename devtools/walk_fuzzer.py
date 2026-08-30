"""FUZZER-1 — the paraphrase fuzzer (the automated Sunny).

Per run, the LLM generates N fresh phrasings of the KNOWN intents;
every phrasing must yield a CARD (never silent), grounding must
include the expected names, and oracles must hold where planted
(DIFFERS / E11.80 / census / flags / the policy refusal). Every
miss is logged VERBATIM — a missed phrasing is exactly the lexicon
food the flywheel wants.

Standalone:  python devtools/walk_fuzzer.py [base_url] [N]
Battery:     invoked by devtools/nightly_battery.sh after the
             walk-runner; failures append to NIGHTLY_BATTERY.md.
"""

from __future__ import annotations

import json
import sys
import urllib.request

# Known intents with their planted oracles. TEST fixtures in
# devtools — never agent control path (P4 governs the agent's
# routing, not the harness that attacks it).
INTENTS = [
    {"name": "codeset_sameness",
     "seed": "Are all the Diabetic codesets defined the same?",
     "expect_ground": ["Diabetic Codeset"],
     "oracle": {"verdict": "DIFFERS", "diff_contains": "E11.80"}},
    {"name": "tables_of_metric",
     "seed": "what tables does metric Active Diabetic Patients use",
     "expect_ground": ["Active Diabetic Patients"],
     "oracle": {"content_contains": "DIAGNOSIS_CODES"}},
    {"name": "kind_census",
     "seed": "what metrics are there",
     "oracle": {"kind": "census"}},
    {"name": "flags_family",
     "seed": "What governance red flags exist for Diabetic Patients?",
     "oracle": {"kind": "flags"}},
    {"name": "count_refusal",
     "seed": "How many patients are currently in the Diabetic "
             "Patients cohort?",
     "oracle": {"proposal_contains":
                "patient rows never reach the model"}},
]

PARAPHRASE_PROMPT = (
    "Generate {n} natural paraphrases a business analyst might type "
    "for the question below — vary word order, morphology, and "
    "synonyms; keep the SAME intent and the same named things. "
    "Return ONLY a JSON array of strings.\nQuestion: {seed}")


def llm_paraphrases(chat_api, seed: str, n: int) -> "list[str]":
    msg = chat_api(
        [{"role": "user",
          "content": PARAPHRASE_PROMPT.format(n=n, seed=seed)}], [])
    text = str(msg.get("content") or "")
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        return []
    try:
        return [str(p) for p in json.loads(text[start:end + 1])][:n]
    except json.JSONDecodeError:
        return []


def _check(card: dict, fin: "dict | None", intent: dict,
           phrasing: str) -> "list[str]":
    """The assertions; every returned string is a logged finding."""
    finds: "list[str]" = []
    if "parse_confirm" not in card:
        return [f"NO CARD (silent!) for {phrasing!r}"]
    if intent.get("expect_ground"):
        shown = " ".join(
            m["name"] for s in card.get("show") or []
            for m in s["matches"])
        for name in intent["expect_ground"]:
            if name.lower() not in shown.lower():
                finds.append(f"grounding missed {name!r} for "
                             f"{phrasing!r} (lexicon food)")
    o = intent.get("oracle") or {}
    if "proposal_contains" in o and o["proposal_contains"] not in \
            str(card.get("parse_confirm")):
        finds.append(f"proposal oracle missed for {phrasing!r}")
    if fin is not None:
        concl = fin.get("conclusion") or {}
        if "kind" in o and concl.get("kind") != o["kind"]:
            finds.append(f"card kind {concl.get('kind')!r} != "
                         f"{o['kind']!r} for {phrasing!r}")
        if "verdict" in o and o["verdict"] not in \
                str(concl.get("verdict") or ""):
            finds.append(f"verdict oracle missed for {phrasing!r}")
        blob = json.dumps(concl)
        for key in ("diff_contains", "content_contains"):
            if key in o and o[key] not in blob:
                finds.append(f"{key} {o[key]!r} missed for "
                             f"{phrasing!r}")
    return finds


def fuzz(post, chat_api, n: int = 3,
         intents: "list[dict] | None" = None) -> "dict":
    """Run the fuzzer. `post(path, payload) -> (dict, status)`;
    returns {phrasings, findings} — findings empty = PASS."""
    findings: "list[str]" = []
    total = 0
    for intent in (intents if intents is not None else INTENTS):
        phrasings = llm_paraphrases(chat_api, intent["seed"], n)
        if not phrasings:
            findings.append(
                f"paraphraser returned nothing for {intent['name']} "
                "(LLM unavailable?) — intent unfuzzed")
            continue
        for p in phrasings:
            total += 1
            try:
                card, status = post("/api/ask", {"message": p})
            except Exception as e:  # noqa: BLE001 — a finding, not a crash
                findings.append(f"ask failed ({type(e).__name__}) "
                                f"for {p!r}")
                continue
            fin = None
            if status == 200 and not card.get("no_match") \
                    and "parse_confirm" in card:
                try:
                    fin, s2 = post("/api/parse/confirm", {
                        "conversation_id": card.get("conversation_id")})
                    if s2 != 200:
                        fin = None
                        findings.append(
                            f"confirm refused ({s2}) for {p!r}: "
                            f"{str(card.get('parse_confirm'))[:80]}")
                except Exception as e:  # noqa: BLE001
                    findings.append(f"confirm failed "
                                    f"({type(e).__name__}) for {p!r}")
            findings.extend(_check(card, fin, intent, p))
    return {"phrasings": total, "findings": findings}


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    def post(path: str, payload: dict) -> "tuple[dict, int]":
        req = urllib.request.Request(
            base + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode()), r.status
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode() or "{}"), e.code

    from devtools.grounding_evals import _load_dotenv
    _load_dotenv()
    from src.orchestrator.agent import azure_chat_api
    result = fuzz(post, azure_chat_api(), n)
    verdict = "PASS" if not result["findings"] else "FAIL"
    print(f"fuzzer: {verdict} — {result['phrasings']} phrasings, "
          f"{len(result['findings'])} finding(s)")
    for f in result["findings"]:
        print(f"  - {f}")
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    # standalone entry (FUZZ-FINDINGS-1 item 1): running the
    # file directly must work — bootstrap the repo root
    import os.path as _op
    import sys as _sys
    _sys.path.insert(0, _op.dirname(_op.dirname(
        _op.abspath(__file__))))
    main()
