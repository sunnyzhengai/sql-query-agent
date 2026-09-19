"""Brief_Work_Dryrun (Sunny's "approved, both proposals stand",
2026-09-18): the Scribe draft driver — his paid run as ONE
command, for the work dry run and any estate here.

The posture: REFUSES cheaply (no estate arg or no key = exit 2
before any boot, spend, or network — the AIVIA_RECORD posture:
the paid call happens only at his hand). Drafts are written to
<estate>/descriptions_draft.json and printed; LANDING them in
descriptions.json with approval statuses stays HIS act — this
tool never touches descriptions.json. The scribe seat prompt is
READ FROM THE REGISTRY (lenses.Seat_Prompts, the literal law) —
never a code copy; the basis records model + prompt version.
"""
import datetime
import json
import sys

MODEL = "gpt-4o-mini"  # the M6/M7 basis precedent


def _env_key() -> str:
    from aivia.console import _env_key as key
    return key()


def _scribe_prompt():
    from aivia.graph import metamodel
    sheet = metamodel.load("lenses").sheets["Seat_Prompts"]
    row = next(r for r in sheet if r["Seat"] == "scribe")
    return row["Prompt"], row["Version"]


def main(argv) -> None:
    if not argv:
        print("usage: python3.11 devtools/scribe_draft.py "
              "<estate>  (the estate folder name under "
              "AIVIA_Product/estates/)", file=sys.stderr)
        raise SystemExit(2)
    key = _env_key()
    if not key:
        print("no OPENAI_API_KEY (repo .env or environment) — "
              "the Scribe is a paid seat and never runs without "
              "the key at hand", file=sys.stderr)
        raise SystemExit(2)
    estate = argv[0]
    from aivia.console import _openai, build_store
    from aivia.flows import describe
    from aivia.graph.read_api import ReadApi
    print(f"building the {estate} graph …")
    store, base = build_store(estate)
    read = ReadApi(store)
    targets = describe.scan_undescribed(read)
    if not targets:
        print("nothing undescribed — every described-label node "
              "already carries text")
        return
    prompt, prompt_version = _scribe_prompt()

    def scribe(evidence_by_id):
        out = {}
        for ident in sorted(evidence_by_id):
            # literal: shape
            resp = _openai("chat/completions", {
                "model": MODEL, "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user",
                     "content": evidence_by_id[ident]}],
                "max_tokens": 200}, key)
            raw = json.loads(
                resp["choices"][0]["message"]["content"])
            out[ident] = (raw.get("description") or "").strip()
            print(f"  {ident}\n    -> {out[ident]}")
        return out

    drafts = describe.draft(read, targets, scribe)
    payload = {
        "_comment": ("Scribe DRAFTS (scribe_draft.py) — review "
                     "per the cage, then land the accepted texts "
                     "in descriptions.json with approval "
                     "statuses (your act; this tool never "
                     "writes descriptions.json)"),
        "basis": {"evidence":
                  "R13 technical definition (the catch-all)",
                  "model": MODEL,
                  "prompt_version": prompt_version},
        "created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "descriptions": drafts}
    out_path = base / "descriptions_draft.json"
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"{len(drafts)} draft(s) -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
