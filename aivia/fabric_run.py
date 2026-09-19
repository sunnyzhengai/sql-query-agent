"""THE FABRIC DRIVER (Brief_Fabric_Resident FR5; Sunny's turn-key
ruling 2026-09-19: "treat this Fabric build as a test run for any
future microsoft marketplace customers … all that can be packaged
into .wheel, must be packaged. reduce the manual work to the
maximum"). The thin-shell notebook's whole vocabulary — three
one-line cells, zero logic outside the wheel:

    import aivia.fabric_run as f
    f.dry_run("/lakehouse/default/Files/<estate folder>")
    f.scribe("/lakehouse/default/Files/<estate folder>")   # paid, LAST

dry_run — boot from the explicit path (FR4), speak the node census
and every governance text (technical definitions + the AI-generated
descriptions). No key, no network: the deterministic layer exactly
as the console boots it.

scribe — the paid seat. REFUSES without a key BEFORE any boot or
spend (the AIVIA_RECORD posture). The driver core that
devtools/scribe_draft.py carried moved here so the wheel owns it
(the turn-key ruling); that script is now a shim over this module.
Drafts land in <estate>/descriptions_draft.json and print for the
cage review; descriptions.json is NEVER written here — landing
approved text stays a human act.
"""
import datetime
import json
import pathlib
import sys

MODEL = "gpt-4o-mini"  # the M6/M7 basis precedent


def _base(estate: str) -> pathlib.Path:
    from aivia import console
    base = console._estate_base(estate)
    if not (base / "registration.json").is_file():
        print(f"not an estate folder (no registration.json): {base}",
              file=sys.stderr)
        raise SystemExit(2)
    return base


def dry_run(estate: str):
    """Boot the estate, speak the census + every governance text.
    Returns the store so later cells can keep asking it."""
    from aivia import console
    base = _base(estate)
    print(f"building the graph from {base} …")
    store, base = console.build_store(
        str(base), journal_path=base / "governance" / "journal.jsonl")
    nodes = list(store.current_nodes())
    census = {}
    for n in nodes:
        census[n.label] = census.get(n.label, 0) + 1
    print("node census: " + " · ".join(
        f"{label} {census[label]}" for label in sorted(census)))
    spoken = 0
    for n in sorted(nodes, key=lambda n: n.identity):
        td = n.properties.get("technical_definition")
        desc = n.properties.get("description")
        if not td and not desc:
            continue
        spoken += 1
        print(f"\n— {n.identity}")
        if td:
            print(f"  technical definition: {td}")
        if desc:
            print(f"  description: {desc}")
    print(f"\n{spoken} node(s) carry governance text · "
          f"{len(nodes)} nodes total")
    return store


def scribe(estate: str, key=None):
    """The paid Scribe run — one call per undescribed node, the seat
    prompt READ FROM THE REGISTRY (lenses.Seat_Prompts, the literal
    law). Refusal first, boot second, spend last."""
    from aivia import console
    if key is None:
        key = console._env_key()
    if not key:
        print("no OPENAI_API_KEY — the Scribe is a paid seat and "
              "never runs without the key at hand", file=sys.stderr)
        raise SystemExit(2)
    base = _base(estate)
    from aivia.flows import describe
    from aivia.graph import metamodel
    from aivia.graph.read_api import ReadApi
    print(f"building the graph from {base} …")
    store, base = console.build_store(str(base))
    read = ReadApi(store)
    targets = describe.scan_undescribed(read)
    if not targets:
        print("nothing undescribed — every described-label node "
              "already carries text")
        return None
    sheet = metamodel.load("lenses").sheets["Seat_Prompts"]
    row = next(r for r in sheet if r["Seat"] == "scribe")
    prompt, prompt_version = row["Prompt"], row["Version"]

    def _scribe(evidence_by_id):
        out = {}
        for ident in sorted(evidence_by_id):
            # literal: shape
            resp = console._openai("chat/completions", {
                "model": MODEL, "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": evidence_by_id[ident]}],
                "max_tokens": 200}, key)
            raw = json.loads(resp["choices"][0]["message"]["content"])
            out[ident] = (raw.get("description") or "").strip()
            print(f"  {ident}\n    -> {out[ident]}")
        return out

    drafts = describe.draft(read, targets, _scribe)
    payload = {  # literal: shape — the draft-file form scribe_draft.py established
        "_comment": ("Scribe DRAFTS (aivia.fabric_run.scribe) — "
                     "review per the cage, then land the accepted "
                     "texts in descriptions.json with approval "
                     "statuses (your act; this tool never writes "
                     "descriptions.json)"),
        "basis": {  # literal: shape — the M6/M7 basis form
            "evidence": "R13 technical definition (the catch-all)",
            "model": MODEL,
            "prompt_version": prompt_version},
        "created_at": datetime.datetime.now(
            datetime.timezone.utc).isoformat(),
        "descriptions": drafts}
    out_path = base / "descriptions_draft.json"
    out_path.write_text(json.dumps(payload, indent=1) + "\n")
    print(f"{len(drafts)} draft(s) -> {out_path}")
    return out_path
