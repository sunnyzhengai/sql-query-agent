# build_abstract_names.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/03_chat_bot.md L03 (the name-abstract list)
# Contract: AIVIA_01_Design/03_chat_bot_data_contract.md (Output File 2:
#           03_chat_abstract_names.json)
# Tests:    AIVIA_01_Test/test_03_chat_bot_data_contract.py (born with
#           this build, RED first)
#           Sunny's gap-check of the real output is the acceptance gate.
#
# PURPOSE. Build lane 2's data asset: for EVERY table and EVERY column
# in the phase 02 sheets, an LLM-written short abstract and synonym
# list — searched lexically by the funnel, never embedded (ruled).
#
# ---------------------------------------------------------------------
# INPUTS AND OUTPUT
# ---------------------------------------------------------------------
#   in:  the phase 02 sheets dir (table.json, column.json — name and
#        stored description; read through dictionary_graph.load_sheets,
#        the one door to the sheets)
#   out: AIVIA_01_Data/03_chat_bot/03_chat_abstract_names.json
#        rows (contract): object_kind (table|column), object_id,
#        object_name, abstract, synonyms[],
#        sunny_abstract (blank = script's stands),
#        sunny_synonyms[] (additions, never removed by the script)
#
#   FINGERPRINT SKIPPED (Sunny's ruling, 2026-09-30): no
#        source_fingerprint field for now. Consequence, ruled-for-now
#        posture: REUSE IS BY KEY — a row that exists for
#        (object_kind, object_id) is reused verbatim; only NEW objects
#        generate. A changed description does NOT regenerate its
#        abstract until the fingerprint (or another mechanism) is
#        ruled in later. This keeps reruns cheap and Sunny's
#        gap-checked abstracts stable; the staleness risk is accepted
#        and recorded here. Full regeneration remains available by
#        deleting the output file and rerunning (~83 calls, under a
#        dollar).
#
# ---------------------------------------------------------------------
# THE LLM CALLS (gpt-5-mini, the pinned CHAT_MODEL constant)
# ---------------------------------------------------------------------
#   - batched: ~20 objects per call, structured JSON output (the API's
#     json response format), validated per object: non-empty abstract,
#     synonyms a list of strings; a malformed object fails loudly
#     naming it, never silently skipped.
#   - per object the call carries: kind, full name (columns as
#     TABLE.COLUMN so the table context informs the abstract), and the
#     stored description (truncated at a ruled length, e.g. 1,000
#     chars — the long DATE_DIMENSION-style descriptions don't need
#     full text to abstract).
#   - the prompt teaches the SHAPE abstractly — what an abstract and a
#     synonym are for a data-dictionary object — and carries NO example
#     objects (prompt-examples-are-data law; no hardcoded examples).
#   - full first run: 38 + 1,618 = 1,656 objects, ~83 calls — an
#     announced cost (gpt-5-mini: well under a dollar), Sunny's hand.
#
# ---------------------------------------------------------------------
# THE THREE LAWS (test-locked)
# ---------------------------------------------------------------------
#   REUSE (by key, per the fingerprint skip): existing rows keyed
#     (object_kind, object_id) are reused verbatim; only new objects
#     generate. Census prints generated-new vs reused.
#   SUNNY PRESERVATION: sunny_abstract / sunny_synonyms[] are carried
#     over by key on EVERY rebuild, including when the script's own
#     fields regenerate. A rebuild that loses one is a test failure
#     (the contract's exact words).
#   COVERAGE (completion integrity): after the build, every table and
#     column in the sheets has exactly one row. Missing = counted and
#     named, build fails loudly. Rows for objects no longer in the
#     sheets are DROPPED and counted in the census (with their sunny_*
#     content echoed in the census so nothing vanishes silently).
#
# ---------------------------------------------------------------------
# ENTRY POINT + CLI (the command Sunny runs)
# ---------------------------------------------------------------------
#   /opt/homebrew/bin/python3.11 AIVIA_01_Code/build_abstract_names.py \
#       AIVIA_01_Data/02_emr_data_dictionary \
#       AIVIA_01_Data/03_chat_bot
#   Both paths are parameters (the law). Prints the census: rows per
#   kind, generated vs reused, dropped objects, sunny_* rows carried,
#   coverage OK/failures. The LLM client reads OPENAI_API_KEY from
#   .env, same door as the embedder.
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (red first, in NEW test_03_chat_bot_data_contract.py;
# tiny synthetic sheets so the paid calls stay pennies)
# ---------------------------------------------------------------------
#   - coverage: every synthetic table/column gets a row with a
#     non-empty abstract and list-typed synonyms; a sheet object the
#     LLM response omits fails loudly.
#   - reuse: a second run with unchanged sheets makes ZERO LLM calls
#     (forbidden-caller embedder pattern, carried over).
#   - new object: adding one synthetic column generates THAT row only;
#     the census counts 1 new, rest reused. (Description-change
#     regeneration is deferred with the fingerprint — no test pins it;
#     this comment is the recorded debt.)
#   - sunny preservation: hand-writing sunny_abstract/sunny_synonyms
#     into the output, then rebuilding, keeps the sunny_* fields
#     verbatim.
#   - drop: removing a synthetic column from the sheets drops its row
#     and counts it; its sunny_* content appears in the census echo.
#   - the prompt contains no object examples (a test greps the prompt
#     constant for the synthetic names — none may appear).

import json
import sys
from pathlib import Path

import dictionary_graph
from local_chat import load_openai_key

CHAT_MODEL = "gpt-5-mini"
BATCH_SIZE = 20
DESCRIPTION_LIMIT = 1000
OUT_NAME = "03_chat_abstract_names.json"

# The prompt teaches the SHAPE abstractly — it carries no example
# objects (prompt-examples-are-data law; test-locked).
PROMPT = (
    "You write search aids for a healthcare data dictionary. For each "
    "object you receive (a database object of a given kind, with its "
    "stored name and stored description), write:\n"
    "- abstract: one short plain sentence saying what the object holds "
    "or means, grounded ONLY in the given name and description — never "
    "invented knowledge.\n"
    "- synonyms: a list of up to 8 short words or phrases a technical "
    "user might type when looking for this object (expansions of "
    "abbreviations in the name, common alternate words from the "
    "description). Lowercase. Empty list if none apply.\n"
    "Return JSON: {\"rows\": [{\"abstract\": ..., \"synonyms\": [...]}"
    "]} with EXACTLY one entry per input object, in the same order."
)


def real_llm(batch):
    """One paid gpt-5-mini call for a batch of objects. Returns the
    parsed rows list, length-checked against the batch."""
    from openai import OpenAI

    client = OpenAI(api_key=load_openai_key())
    payload = json.dumps([{"kind": o["kind"], "name": o["name"],
                           "description": o["description"]}
                          for o in batch])
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": PROMPT},
                  {"role": "user", "content": payload}])
    rows = json.loads(response.choices[0].message.content)["rows"]
    if len(rows) != len(batch):
        raise ValueError(
            f"LLM returned {len(rows)} rows for {len(batch)} objects")
    return rows


def _write_rows(out_path, rows):
    rows = sorted(rows, key=lambda r: (r["object_kind"], r["object_name"]))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def _objects_from_sheets(sheets):
    objects = []
    for r in sheets["tables"]:
        objects.append({
            "object_kind": "table", "object_id": r["table_id"],
            "object_name": r["table_name"],
            "kind": "table", "name": r["table_name"],
            "description": r["table_description"][:DESCRIPTION_LIMIT]})
    for r in sheets["columns"]:
        objects.append({
            "object_kind": "column", "object_id": r["column_id"],
            "object_name": f"{r['table_name']}.{r['column_name']}",
            "kind": "column",
            "name": f"{r['table_name']}.{r['column_name']}",
            "description": r["column_description"][:DESCRIPTION_LIMIT]})
    return objects


def build_abstracts(sheets_dir, out_dir, llm):
    sheets = dictionary_graph.load_sheets(sheets_dir)
    objects = _objects_from_sheets(sheets)
    out_path = Path(out_dir) / OUT_NAME

    existing = {}
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for row in json.load(f):
                existing[(row["object_kind"], row["object_id"])] = row

    census = {"tables": sum(1 for o in objects
                            if o["object_kind"] == "table"),
              "columns": sum(1 for o in objects
                             if o["object_kind"] == "column"),
              "generated_new": 0, "reused": 0, "dropped": []}

    rows, to_generate = [], []
    for o in objects:
        key = (o["object_kind"], o["object_id"])
        prior = existing.get(key)
        row = {"object_kind": o["object_kind"],
               "object_id": o["object_id"],
               "object_name": o["object_name"],
               "abstract": "", "synonyms": [],
               "sunny_abstract": "", "sunny_synonyms": []}
        if prior is not None:
            # REUSE by key (fingerprint skipped by ruling) + SUNNY
            # PRESERVATION — both carried verbatim.
            row["abstract"] = prior["abstract"]
            row["synonyms"] = prior["synonyms"]
            row["sunny_abstract"] = prior.get("sunny_abstract", "")
            row["sunny_synonyms"] = prior.get("sunny_synonyms", [])
            census["reused"] += 1
        else:
            to_generate.append((o, row))
        rows.append(row)

    for start in range(0, len(to_generate), BATCH_SIZE):
        chunk = to_generate[start:start + BATCH_SIZE]
        results = llm([o for o, _ in chunk])
        for (o, row), result in zip(chunk, results):
            abstract = result.get("abstract")
            synonyms = result.get("synonyms")
            if (not isinstance(abstract, str) or not abstract.strip()
                    or not isinstance(synonyms, list)
                    or not all(isinstance(s, str) for s in synonyms)):
                raise ValueError(
                    f"malformed LLM row for {o['object_name']}: {result}")
            row["abstract"] = abstract
            row["synonyms"] = synonyms
            census["generated_new"] += 1
        # CHECKPOINT after every batch (Echo Law build, 2026-09-30, from
        # the live billing_not_active death): an interruption leaves a
        # valid partial file; the rerun's reuse-by-key pays only for
        # the remainder.
        _write_rows(out_path, [r for r in rows if r["abstract"].strip()])

    # DROPPED objects: counted, sunny_* content echoed — never silent.
    current_keys = {(o["object_kind"], o["object_id"]) for o in objects}
    for key, prior in sorted(existing.items()):
        if key not in current_keys:
            census["dropped"].append({
                "object_name": prior["object_name"],
                "sunny_abstract": prior.get("sunny_abstract", ""),
                "sunny_synonyms": prior.get("sunny_synonyms", [])})

    # COVERAGE (completion integrity): exactly one row per object.
    keys = [(r["object_kind"], r["object_id"]) for r in rows]
    if len(rows) != len(objects) or len(set(keys)) != len(keys):
        raise ValueError(
            f"coverage broken: {len(objects)} objects, {len(rows)} rows")

    _write_rows(out_path, rows)

    census["sunny_abstract_rows"] = sum(
        1 for r in rows if r["sunny_abstract"])
    census["sunny_synonyms_rows"] = sum(
        1 for r in rows if r["sunny_synonyms"])
    return census


def main(argv):
    if len(argv) < 3:
        print("usage: python3.11 AIVIA_01_Code/build_abstract_names.py "
              "<02 sheets dir> <03 out dir>", file=sys.stderr)
        return 2
    census = build_abstracts(argv[1], argv[2], real_llm)
    print("abstract names census:")
    for k in ("tables", "columns", "generated_new", "reused",
              "sunny_abstract_rows", "sunny_synonyms_rows"):
        print(f"  {k}: {census[k]}")
    for d in census["dropped"]:
        print(f"  DROPPED: {d['object_name']}"
              + (f" (sunny content echoed: {d['sunny_abstract']!r} "
                 f"{d['sunny_synonyms']})"
                 if d["sunny_abstract"] or d["sunny_synonyms"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
