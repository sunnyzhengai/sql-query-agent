"""THE FABRIC DRIVER (Brief_Fabric_Resident FR5; Sunny's turn-key
ruling 2026-09-19: "treat this Fabric build as a test run for any
future microsoft marketplace customers … all that can be packaged
into .wheel, must be packaged. reduce the manual work to the
maximum"). The thin-shell notebook's whole vocabulary — three
one-line cells, zero logic outside the wheel:

    import aisql.fabric_run as f
    f.dry_run("/lakehouse/default/Files/<estate folder>")
    f.scribe("/lakehouse/default/Files/<estate folder>")   # paid, LAST

dry_run — boot from the explicit path (FR4), speak the node census
and every governance text (technical definitions + the AI-generated
descriptions). No key, no network: the deterministic layer exactly
as the console boots it.

scribe — the paid seat. REFUSES without a key BEFORE any boot or
spend (the AISQL_RECORD posture). The driver core that
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
    from aisql import console
    base = console._estate_base(estate)
    if not (base / "registration.json").is_file():
        print(f"not an estate folder (no registration.json): {base}",
              file=sys.stderr)
        raise SystemExit(2)
    return base


def _pack_dir() -> pathlib.Path:
    """The clarity pack's home: the repo layout when present, the
    wheel's package copy otherwise (the registry pattern —
    build_wheel.py copies AIVIA_Product/source_packs/clarity in as
    aisql/_source_packs/clarity, never tracked)."""
    repo = (pathlib.Path(__file__).resolve().parents[1]
            / "AIVIA_Product" / "source_packs" / "clarity")
    if repo.is_dir():
        return repo
    return (pathlib.Path(__file__).resolve().parent
            / "_source_packs" / "clarity")


def _collect_table_refs(node, out):
    if isinstance(node, dict):
        ref = node.get("table_ref")
        if isinstance(ref, str) and ref and not ref.startswith("#"):
            out.add(ref.split(".")[-1].upper())
        for v in node.values():
            _collect_table_refs(v, out)
    elif isinstance(node, list):
        for v in node:
            _collect_table_refs(v, out)


def extract_scripts(estate: str):
    """THE DERIVED-LIST LAW (Brief_Extract_Autogen, Sunny
    2026-09-19: "i don't want to keep manually writing and
    maintaining these lists and files"): parse every
    estate_snapshot/*.sql through the ONE parse door (map_tree),
    derive the batch table list, and write the pack scripts with
    the list filled to <estate>/extract_scripts/. Unparseable
    files are counted and named, never fatal (EA2); stray names
    (CTEs, temp survivors) match nothing in the dictionary and
    are harmless. Returns the sorted table list."""
    from aisql.graph.kg2_mapper import map_tree
    base = _base(estate)
    sql_dir = base / "estate_snapshot"
    files = sorted(sql_dir.glob("*.sql"))
    if not files:
        print(f"no .sql files in {sql_dir} — the estate's SQL batch "
              "is the list's source of truth", file=sys.stderr)
        raise SystemExit(2)
    tables, unparseable = set(), []
    for f in files:
        try:
            tree = map_tree(f.name, f.read_text(encoding="utf-8-sig",
                                                errors="replace"))
        except Exception as err:  # noqa: BLE001 — EA2: counted, named
            unparseable.append(f"{f.name} ({type(err).__name__})")
            continue
        _collect_table_refs(tree, tables)
    names = sorted(tables)
    print(f"parsed {len(files) - len(unparseable)} of {len(files)} "
          f"files · {len(names)} tables referenced · "
          f"{len(unparseable)} unparseable")
    for line in unparseable:
        print(f"  unparseable: {line}")
    _write_manifest_template(base, sql_dir)
    quoted = ",\n    ".join(f"'{n}'" for n in names)
    out_dir = base / "extract_scripts"
    out_dir.mkdir(exist_ok=True)
    for template in sorted(_pack_dir().glob("*.sql")):
        text = template.read_text().replace(
            "'PASTE_YOUR_BATCH_TABLES_HERE'", quoted)
        (out_dir / template.name).write_text(text)
        print(f"  -> {out_dir / template.name}")
    print("copy each script into your SQL client, run, save the "
          "grids as the six extract files")
    return names


def _write_manifest_template(base, sql_dir):
    """Ruling (5) (Brief_Pilot_Findings_R1, "i agree with option c"):
    the wheel writes estate_snapshot/manifest.json with location
    (from the folder) and default_schema (from the source pack — a
    vendor fact, pack.json) filled and as_of EMPTY; intake refuses
    by name on the empty as_of (INTAKE-17) — the template's tripwire
    per the placeholder law. A manifest already present is the
    human's data: NEVER overwritten."""
    path = sql_dir / "manifest.json"
    if path.is_file():
        return
    # literal: shape — the estate manifest's three ruled fields
    template = {"location": f"estate://{base.name}/",
                "as_of": "", "default_schema": ""}
    pack_facts = _pack_dir() / "pack.json"
    if pack_facts.is_file():
        template["default_schema"] = json.loads(
            pack_facts.read_text(encoding="utf-8-sig")
        ).get("default_schema", "")
    path.write_text(json.dumps(template, indent=1) + "\n")
    print(f"  -> {path} (template — fill in as_of: the date this "
          "estate SQL was captured)")


def dry_run(estate: str):
    """Boot the estate, speak the census + every governance text.
    Returns the store so later cells can keep asking it."""
    from aisql import console
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
    # Brief_Dryrun_Order (Sunny, 2026-09-20: "i can't find the scope
    # descriptions or statement or sql file's … show these
    # descriptions first"): the COMPOSED texts speak first — file,
    # scope, statement — then every remaining label under its own
    # counted header, so the dictionary flood is skippable
    speaking = [n for n in nodes
                if n.properties.get("technical_definition")
                or n.properties.get("description")]
    # Q5 (Brief_Pilot_Build_3): statement lines borrow the built
    # scope's head clause at RENDER — derivable, stored never
    from aisql.flows import produce
    heads = {}
    for n in speaking:
        if n.label != "scope" or "::" not in n.identity:
            continue
        head = produce.scope_head(n.properties.get("description"))
        if head:
            fid, name = n.identity.rsplit("::", 1)
            heads.setdefault(fid, {})[produce._squash(name)] = head
    # literal: frame — the ruled speaking order (Brief_Dryrun_Order)
    first = ("file", "scope", "statement")
    labels = list(first) + sorted(
        {n.label for n in speaking} - set(first))
    spoken = 0
    for label in labels:
        group = sorted((n for n in speaking if n.label == label),
                       key=lambda n: n.identity)
        if not group:
            continue
        print(f"\n=== {label} ({len(group)}) ===")
        for n in group:
            spoken += 1
            print(f"\n— {n.identity}")
            td = n.properties.get("technical_definition")
            desc = n.properties.get("description")
            if td:
                print(f"  technical definition: {td}")
            if desc:
                if label == "statement" and "::" in n.identity:
                    fid = n.identity.rsplit("::", 1)[0]
                    desc = produce.statement_display(
                        desc, heads.get(fid, {}))
                print(f"  description: {desc}")
    print(f"\n{spoken} node(s) carry governance text · "
          f"{len(nodes)} nodes total")
    return store


def scribe(estate: str, key=None):
    """The paid Scribe run — one call per undescribed node, the seat
    prompt READ FROM THE REGISTRY (lenses.Seat_Prompts, the literal
    law). Refusal first, boot second, spend last."""
    from aisql import console
    if key is None:
        key = console._env_key()
    if not key:
        print("no OPENAI_API_KEY — the Scribe is a paid seat and "
              "never runs without the key at hand", file=sys.stderr)
        raise SystemExit(2)
    base = _base(estate)
    from aisql.flows import describe
    from aisql.graph import metamodel
    from aisql.graph.read_api import ReadApi
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
        "_comment": ("Scribe DRAFTS (aisql.fabric_run.scribe) — "
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
