# chat_bot.py — PSEUDO CODE ONLY, awaiting Sunny's review.
# Real code will be written directly below these comments after approval.
#
# Design:   AIVIA_01_Design/03_chat_bot.md (all ten decisions; L05)
# Contract: AIVIA_01_Design/03_chat_bot_data_contract.md
# Tests:    AIVIA_01_Test/test_03_chat_bot_data_contract.py (grows a
#           chat section, RED first)
#           Sunny's twelve shapes (her md) run against the page by hand.
#
# PURPOSE. The phase 03 chat: a technical user asks in natural
# language; the LLM segments, the DATA classifies, the user confirms,
# the answer is the stored detail of what was confirmed — and the whole
# estate is drawn as a map that search lights up. No traversal.
#
# ---------------------------------------------------------------------
# LAYER 0 — assets at startup (loaded ONCE)
# ---------------------------------------------------------------------
#   - phase 02 sheets via dictionary_graph.load_sheets; the graph via
#     build_graph (for the map and the join lookups — connect() is
#     never called).
#   - the terms file 03_chat_technical_terms.md: parsed from the
#     markdown table -> keyword rows {keyword, maps_to, kind,
#     synonyms[]}. A malformed row fails loudly naming its line.
#   - the abstract list 03_chat_abstract_names.json. ABSENT = lane 2
#     skipped LOUDLY in the startup census (the contract's posture).
#   - LEXICAL INDEXES, all keys folded (casefold + underscore/space
#     collapsed):
#       names:     table_name -> table; column_name and
#                  table.column -> column(s); value meaning -> value
#       abstracts: every synonym + sunny_synonym (and sunny_abstract
#                  override text) -> its object
#       keywords:  keyword + its synonyms -> the keyword row
#   - THE MAP LAYOUT, deterministic (decision 4): tables start on a
#     circle in table-name order, then a FIXED number of plain-Python
#     force iterations (no randomness anywhere — same picture every
#     session); columns sit as satellite dots on a ring around their
#     table. Edges collapse to one line per table pair with a count.
#   - startup census printed: node/edge/index counts, lanes ready,
#     acceptance defaults in force.
#
# ---------------------------------------------------------------------
# LAYER 1 — segmentation (the ONLY LLM step; decision 2)
# ---------------------------------------------------------------------
#   SEGMENT_PROMPT_TEMPLATE + build_segment_prompt(terms):
#     the prompt teaches the JOB abstractly — split the question into
#     meaning-bearing tokens; tag tokens that are technical KEYWORDS
#     (the terms list rides in the prompt AS DATA: keyword, kind,
#     synonyms); associate each keyword with the token it modifies;
#     everything else is noise. It carries NO example objects and NO
#     example questions (test-locked, same law as L03).
#   segment(question, llm) -> [{text, role: keyword|term|noise,
#     keyword? (canonical), modifies? (index of the associated term)}]
#     - gpt-5-mini, json response, one call per question.
#     - validation, loud: every token text must appear in the question
#       (case-insensitive); roles from the closed set; a keyword tag
#       must name a keyword from the terms file. The LLM NEVER says
#       name-or-value — the data decides that in layer 2.
#
# ---------------------------------------------------------------------
# LAYER 2 — the funnel, per term token (pure; decision 2)
# ---------------------------------------------------------------------
#   resolve(term_tokens, indexes, sheets, embedder, params):
#     lane 1 LEXICAL:  folded term vs names index. Hit(s) -> matches
#       with mechanism "lexical"; category = whatever the data says
#       (table / column / value). Funnel STOPS for this term.
#       One hit -> pre-selected. SEVERAL hits (DEPARTMENT_ID x10) ->
#       ALL shown grouped by owning table, NONE pre-selected — exact
#       ambiguity is the user's call, never assumed.
#     lane 2 ABSTRACT: folded term vs abstracts index. Same stop, same
#       ambiguity rule; mechanism "abstract".
#     lane 3 EMBEDDING: every term still unresolved is embedded in ONE
#       batched call; per-term scores vs ALL stored embeddings
#       (score_rows); the acceptance DEFAULTS (per population,
#       lane-3 only) pick what comes pre-selected; below-floor is not
#       shown; mechanism "embedding".
#     KEYWORD ASSOCIATION (decision 2 + Q2 ruling): a keyword tied to
#       a term SORTS that population's hits first and favors them for
#       pre-selection — it never hides the other populations. A
#       population keyword with no associated term (bare "tables")
#       just orders the display.
#     Every match carries: mechanism, category, owning table, scores
#       (lane 3 only), pre_selected flag.
#
# ---------------------------------------------------------------------
# LAYER 3 — the strict answer (decisions 3, 4, 6, 7)
# ---------------------------------------------------------------------
#   answer(confirmed_items, graph, sheets) — detail of the confirmed,
#   NOTHING else:
#     table  -> description verbatim; its columns (name, data_type,
#               pk, ini/item); its join rows verbatim (joins are
#               first-class lookup data).
#     column -> description, data_type, pk flags, ini/item, owner;
#               the join rows that touch it.
#     value  -> code, meaning, category table; filter captions from
#               the join sheet (fact_column = code).
#     TWO+ confirmed tables -> the join rows DIRECTLY between each
#               pair; a pair with none gets the honest line "no direct
#               join recorded between X and Y" — the map shows the
#               neighborhood; multi-hop is a later phase.
#     nothing confirmed -> "Nothing confirmed; the candidates shown
#               are the closest this dictionary has." Never padded.
#   no-match notes (shape 8): the question is scanned (folded
#   substring) for names in 02_no_dictionary_match.json; hits are
#   reported verbatim with their sql files.
#
# ---------------------------------------------------------------------
# LAYER 4 — the map display (decision 4's spec, version one pinned)
# ---------------------------------------------------------------------
#   GET /map -> the precomputed layout json: tables (x, y, name),
#   columns (x, y, name, table), collapsed edges (pair, kind, count).
#   The page draws hand-rolled SVG: dim gray estate; solid FK lines;
#   dashed rule lines OFF by default behind a toggle; pan (drag) and
#   zoom (wheel, viewBox); table labels always, column labels only
#   when zoomed past a threshold or when lit.
#   HIGHLIGHT: /segment's response carries the found object ids ->
#   lit; /answer's response carries the confirmed ids -> bold. A found
#   column lights its dot AND its table. Clicking an edge or node
#   opens its verbatim detail in the side panel (informational only —
#   click-to-confirm is explicitly NOT in version one).
#   No animation. No new packages.
#
# ---------------------------------------------------------------------
# LAYER 5 — the page and endpoints (stdlib http.server, port 8703)
# ---------------------------------------------------------------------
#   GET  /         the page: question box; the map; per-population
#                  result sections (TABLES / COLUMNS grouped by owning
#                  table / VALUES with filter captions visible at
#                  choice time); checkboxes with pre-selections;
#                  a Confirm button; the answer panel; mechanism shown
#                  on every match in words (lexical / abstract /
#                  embedding) — fidelity provenance.
#   POST /segment  {question} -> segmentation + funnel results +
#                  map-highlight ids. One gpt-5-mini call + at most
#                  one batched embedding call (zero if every term
#                  resolves in lanes 1-2).
#   POST /answer   {confirmed: [ids]} -> the strict answer + map-bold
#                  ids. No LLM, no embeddings — pure lookup.
#   Errors land in the page as text, never a dead server (the
#   standing pattern).
#   Startup (the command Sunny runs; lands in the contract + her md):
#     /opt/homebrew/bin/python3.11 AIVIA_01_Code/chat_bot.py \
#         AIVIA_01_Data/02_emr_data_dictionary \
#         AIVIA_01_Data/03_chat_bot [port] \
#         [--floor=] [--match=] [--margin=]
#
# ---------------------------------------------------------------------
# CLAUDE'S TESTS (red first, the chat section of test_03; synthetic
# assets keep paid calls at pennies; real-asset tests structural only)
# ---------------------------------------------------------------------
#   - terms parser: rows load with synonyms; a malformed row fails
#     naming its line; unknown kind fails.
#   - folding: "pat enc hsp" finds PAT_ENC_HSP; "department id" with
#     two synthetic owners returns BOTH grouped, none pre-selected.
#   - funnel stop: a lane-1 term makes no abstract lookup and no
#     embedding call (forbidden embedder); a lane-2 term skips lane 3.
#   - keyword ordering: keyword "table" tied to a term puts table hits
#     first and pre-selects the top table hit over a same-score column.
#   - segmentation (real gpt-5-mini, mechanism-level): valid structure;
#     token texts appear in the question; "table" tagged keyword; no
#     exact-split pinning (nondeterminism accepted).
#   - build_segment_prompt: carries a synthetic keyword as data;
#     contains NO object names, NO example questions (grep).
#   - strict answer: a confirmed table's answer holds its verbatim
#     description + join rows; an unconfirmed value appears nowhere;
#     nothing confirmed -> the honest sentence; two joined tables ->
#     their rows; two unjoined -> "no direct join recorded".
#   - value captions come off the join sheet.
#   - map layout: two computes are byte-identical; every table and
#     column has coordinates; parallel joins collapse with counts.
#   - real assets smoke (no API): terms + abstracts + sheets load,
#     indexes count 38 tables / 1,618 columns / 1,656 abstract rows.
#
# After build: the startup command lands in the contract's "How to
# test" and Sunny's md; her twelve shapes (5-7 reshaped) run by hand.

import itertools
import json
import math
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import dictionary_graph
from build_abstract_names import CHAT_MODEL
from local_chat import load_openai_key, real_embedder

DEFAULT_PORT = 8703
SHOWN_PER_POPULATION = 12
# Display DEFAULTS, not gates (03 contract). Calibration RULED
# 2026-09-30 from Sunny's twelve-shape run (all passed): match is PER
# POPULATION; floor and margin stay global (no per-population evidence).
CANDIDATE_FLOOR = 0.25
MATCH_DEFAULTS = {"table": 0.40, "column": 0.50, "value": 0.60}
UNIQUE_MARGIN = 0.1


def _match_for(params, kind):
    m = params["match"]
    return m[kind] if isinstance(m, dict) else m

POPULATIONS = ["table", "column", "value"]
TERM_KINDS = {"population", "operation", "property"}


VALUES_SHOWN = 50


def _fold(text):
    # F2 (Echo Law, 2026-09-30): edge punctuation must not knock a term
    # out of the certainty lane — strip it per word, keep inner marks.
    words = []
    for w in text.replace("_", " ").casefold().split():
        w = w.strip("".join(c for c in w if not c.isalnum()))
        if w:
            words.append(w)
    return " ".join(words)


# --------------------------------------------------------------------------
# The terms file
# --------------------------------------------------------------------------


def parse_terms(text):
    rows = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= {"-", " "} for c in cells):
            continue  # the separator row
        if cells and cells[0].casefold() == "keyword":
            continue  # the header row
        if len(cells) != 5:
            raise ValueError(
                f"terms row at line {lineno}: expected 5 cells, "
                f"found {len(cells)}: {stripped}")
        keyword, maps_to, kind, synonyms, ruled = cells
        if kind not in TERM_KINDS:
            raise ValueError(
                f"terms row at line {lineno}: unknown kind {kind!r}")
        rows.append({"keyword": keyword, "maps_to": maps_to,
                     "kind": kind,
                     "synonyms": [s.strip() for s in synonyms.split(",")
                                  if s.strip()],
                     "ruled": ruled})
    if not rows:
        raise ValueError("terms file has no rows")
    return rows


# --------------------------------------------------------------------------
# Segmentation — the one LLM step
# --------------------------------------------------------------------------

SEGMENT_INSTRUCTIONS = (
    "You segment ONE user question about a technical data dictionary. "
    "Return JSON {\"tokens\": [ ... ]} where each token is "
    "{\"text\": exact words copied from the question, "
    "\"role\": keyword or term or noise, "
    "\"keyword\": the canonical keyword when role is keyword, "
    "\"modifies\": the index (into your tokens array) of the term "
    "token that keyword modifies, when that is clear}.\n"
    "A keyword is a word or phrase from the keyword list below — "
    "synonyms count, and you report the canonical keyword. A term is "
    "a meaning-bearing word or phrase that could name or describe "
    "data; keep a multi-word phrase together when it carries one "
    "meaning. Noise is everything else. Do NOT classify terms any "
    "further — never guess whether a term is a table, a column or a "
    "value; the data decides that, not you.\n"
    "The keyword list (data):\n"
)


def build_segment_prompt(terms):
    payload = json.dumps(
        [{"keyword": r["keyword"], "kind": r["kind"],
          "synonyms": r["synonyms"]} for r in terms])
    return SEGMENT_INSTRUCTIONS + payload


def real_chat(system, user):
    from openai import OpenAI

    client = OpenAI(api_key=load_openai_key())
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return json.loads(response.choices[0].message.content)


def segment(question, terms, llm):
    data = llm(build_segment_prompt(terms), question)
    tokens = data.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise ValueError(f"segmentation returned no tokens: {data}")
    known = {r["keyword"] for r in terms}
    qfold = question.casefold()
    for i, t in enumerate(tokens):
        if (not isinstance(t, dict) or not isinstance(t.get("text"), str)
                or not t["text"].strip()):
            raise ValueError(f"malformed token {i}: {t}")
        if t["text"].casefold() not in qfold:
            raise ValueError(
                f"token text not in the question: {t['text']!r}")
        if t.get("role") not in ("keyword", "term", "noise"):
            raise ValueError(f"token {i} has unknown role: {t}")
        if t["role"] == "keyword" and t.get("keyword") not in known:
            raise ValueError(
                f"token {i} names an unknown keyword: {t}")
        mi = t.get("modifies")
        if mi is not None and (not isinstance(mi, int)
                               or not 0 <= mi < len(tokens)):
            raise ValueError(f"token {i} modifies out of range: {t}")
    return tokens


def associate(tokens, terms):
    """Keyword association (decision 2): a population keyword tied to a
    term sets that term's population; a bare population keyword becomes
    a global display hint only."""
    pop_by_keyword = {r["keyword"]: r["maps_to"].split()[0]
                      for r in terms if r["kind"] == "population"}
    entries, by_index = [], {}
    for i, t in enumerate(tokens):
        if t["role"] == "term":
            entry = {"text": t["text"], "population": None}
            entries.append(entry)
            by_index[i] = entry
    global_pop = None
    for t in tokens:
        if t["role"] != "keyword":
            continue
        pop = pop_by_keyword.get(t.get("keyword"))
        if pop is None:
            continue
        mi = t.get("modifies")
        if mi is not None and mi in by_index:
            by_index[mi]["population"] = pop
        elif global_pop is None:
            global_pop = pop
    return entries, global_pop


def with_composite(terms):
    """Ruled 2026-09-30 (the shape-2 live run): when segmentation
    yields 2+ terms, their joined text is searched as ONE extra term in
    the same batch — the whole-phrase meaning survives any split,
    deterministically, at zero extra LLM cost."""
    if len(terms) < 2:
        return terms
    joined = " ".join(t["text"] for t in terms)
    return terms + [{"text": joined, "population": None,
                     "composite": True}]


# --------------------------------------------------------------------------
# Assets — loaded once at startup
# --------------------------------------------------------------------------


def load_assets(sheets_dir, data03_dir):
    """The LOCAL frontend — reads the json sheets + terms md +
    abstracts json, then builds. The Fabric frontend lives in
    fabric_assets.load_assets_fabric; both call _build_assets (M04:
    the source is a parameter, never a fork)."""
    sheets = dictionary_graph.load_sheets(sheets_dir)
    data03_dir = Path(data03_dir)
    terms = parse_terms(
        (data03_dir / "03_chat_technical_terms.md")
        .read_text(encoding="utf-8"))
    abstracts_path = data03_dir / "03_chat_abstract_names.json"
    abstract_rows = (json.loads(abstracts_path.read_text(encoding="utf-8"))
                     if abstracts_path.exists() else None)
    return _build_assets(sheets, terms, abstract_rows)


def _build_assets(sheets, terms, abstract_rows):
    """Source-blind construction — identical behavior for local json
    and Fabric Delta rows."""
    graph = dictionary_graph.build_graph(sheets)

    names_index = {}

    def add(key, match):
        names_index.setdefault(_fold(key), []).append(match)

    column_id_by_name = {}
    for r in sheets["tables"]:
        add(r["table_name"], {"category": "table", "id": r["table_id"],
                              "name": r["table_name"],
                              "table_name": r["table_name"]})
    for r in sheets["columns"]:
        full = f"{r['table_name']}.{r['column_name']}"
        column_id_by_name[full] = r["column_id"]
        match = {"category": "column", "id": r["column_id"],
                 "name": full, "table_name": r["table_name"]}
        add(r["column_name"], match)
        add(f"{r['table_name']} {r['column_name']}", match)
        add(full, match)
    for r in (sheets["values"] or []):
        add(r["meaning"], {
            "category": "value",
            "id": f"{r['table_name']}:{r['code']}",
            "name": f"{r['table_name']}:{r['code']}",
            "table_name": r["table_name"], "code": r["code"],
            "meaning": r["meaning"]})

    abstracts_index = {}
    lane2_ready = abstract_rows is not None
    if lane2_ready:
        for row in abstract_rows:
            if row["object_kind"] == "table":
                match = {"category": "table", "id": row["object_id"],
                         "name": row["object_name"],
                         "table_name": row["object_name"]}
            else:
                match = {"category": "column", "id": row["object_id"],
                         "name": row["object_name"],
                         "table_name": row["object_name"].split(".")[0]}
            keys = list(row["synonyms"]) + list(row["sunny_synonyms"])
            if row["sunny_abstract"].strip():
                keys.append(row["sunny_abstract"])
            for key in keys:
                abstracts_index.setdefault(_fold(key), []).append(match)

    census = {"tables": len(sheets["tables"]),
              "columns": len(sheets["columns"]),
              "values": len(sheets["values"] or []),
              "value_search": sheets["value_embeddings"] is not None,
              "abstract_rows": len(abstract_rows) if lane2_ready else 0,
              "lane2_ready": lane2_ready,
              "no_match": len(sheets["no_match"]),
              "keywords": len(terms)}

    assets = {"sheets": sheets, "graph": graph, "terms": terms,
              "names_index": names_index,
              "abstracts_index": abstracts_index,
              "column_id_by_name": column_id_by_name,
              "census": census}
    assets["layout"] = compute_layout(graph)
    return assets


# --------------------------------------------------------------------------
# The funnel (decision 2) — lanes stop at the first hit
# --------------------------------------------------------------------------


def _pop_rank(population, keyword_pop):
    order = list(POPULATIONS)
    if keyword_pop in order:
        order.remove(keyword_pop)
        order.insert(0, keyword_pop)
    return order.index(population)


def _match_id(entry, assets):
    if entry["kind"] == "table":
        return assets["graph"]["tables_by_name"][entry["table_name"]]
    if entry["kind"] == "column":
        return assets["column_id_by_name"][entry["name"]]
    return f"{entry['table_name']}:{entry['code']}"


def resolve(terms, assets, embedder, params=None):
    p = {"floor": CANDIDATE_FLOOR, "match": dict(MATCH_DEFAULTS),
         "margin": UNIQUE_MARGIN}
    if params:
        p.update(params)
    no_match_names = [_fold(r["table_name"])
                      for r in assets["sheets"]["no_match"]
                      if r["table_name"]]
    results = [{"term": t["text"], "population": t["population"],
                "composite": t.get("composite", False),
                "mechanism": None, "matches": [], "totals": {},
                "no_match": any(n and n in _fold(t["text"])
                                for n in no_match_names)}
               for t in terms]

    unresolved = []
    for t, res in zip(terms, results):
        folded = _fold(t["text"])
        hits, lane = assets["names_index"].get(folded), "lexical"
        if not hits:
            hits, lane = assets["abstracts_index"].get(folded), "abstract"
        if hits:
            res["mechanism"] = lane
            pre = len(hits) == 1  # exact ambiguity is the user's call
            for h in hits:
                match = dict(h)
                match["mechanism"] = lane
                match["pre_selected"] = pre
                res["matches"].append(match)
            res["matches"].sort(key=lambda m: (
                _pop_rank(m["category"], t["population"]), m["name"]))
        else:
            unresolved.append((t, res))

    if unresolved:
        vectors = embedder([t["text"] for t, _ in unresolved])
        for (t, res), vector in zip(unresolved, vectors):
            res["mechanism"] = "embedding"
            scored = dictionary_graph.score_rows(vector, assets["sheets"])
            for e in scored:
                e["best"] = max(e["scores"].values())
                e["rank"] = sum(s for s in e["scores"].values()
                                if s >= p["floor"])
            shown = [e for e in scored if e["best"] >= p["floor"]]
            pop_best = {}
            for e in shown:
                pop_best[e["kind"]] = max(pop_best.get(e["kind"], 0.0),
                                          e["best"])
            for e in shown:
                pre = (e["best"] >= _match_for(p, e["kind"])
                       and e["best"] >= pop_best[e["kind"]] - p["margin"])
                if t["population"] and e["kind"] != t["population"]:
                    pre = False  # the keyword favors — it never hides
                if res["no_match"]:
                    pre = False  # F3: the no-match note IS the answer
                e["pre_selected"] = pre
            shown.sort(key=lambda e: (
                _pop_rank(e["kind"], t["population"]),
                -e["rank"], e["name"]))
            per_pop = {}
            for e in shown:
                res["totals"][e["kind"]] = res["totals"].get(
                    e["kind"], 0) + 1
                kept = per_pop.setdefault(e["kind"], 0)
                if kept >= SHOWN_PER_POPULATION:
                    continue
                per_pop[e["kind"]] = kept + 1
                res["matches"].append({
                    "category": e["kind"],
                    "id": _match_id(e, assets),
                    "name": e["name"], "table_name": e["table_name"],
                    **({"code": e["code"], "meaning": e["meaning"]}
                       if e["kind"] == "value" else {}),
                    "mechanism": "embedding",
                    "pre_selected": e["pre_selected"],
                    "best": round(e["best"], 4),
                    "scores": {k: round(v, 4)
                               for k, v in e["scores"].items()}})
    return results


def scan_no_match(question, assets):
    qfold = _fold(question)
    return [r for r in assets["sheets"]["no_match"]
            if r["table_name"] and _fold(r["table_name"]) in qfold]


# --------------------------------------------------------------------------
# The strict answer (decisions 3, 4, 6, 7)
# --------------------------------------------------------------------------


def _edge_row(e):
    columns = " AND ".join(
        f"{p['source_column_name']} = {p['destin_column_name']}"
        for p in e["column_pairs"])
    return {"join_id": e["edge_key"], "kind": e["kind"],
            "from": e["source_table_name"], "to": e["destin_table_name"],
            "columns": columns, "owner": e["source_table_name"]}


def _joins_touching_table(table_id, graph):
    return [_edge_row(e) for e in graph["edges"].values()
            if table_id in (e["source_table_id"], e["destin_table_id"])]


def answer_confirmed(confirmed, assets):
    graph, sheets = assets["graph"], assets["sheets"]
    items, confirmed_tables, bold = [], [], []
    for entry in confirmed:
        kind, _, rest = entry.partition(":")
        if kind == "table":
            t = graph["tables"][rest]
            table_values = [v for v in (sheets["values"] or [])
                            if v["table_name"] == t["table_name"]]
            columns = sorted(
                (graph["columns"][cid]
                 for cid in graph["table_columns"].get(rest, [])),
                key=lambda c: c["column_name"])
            items.append({
                "kind": "table", "name": t["table_name"],
                "description": t["table_description"],
                "deprecated_yn": t.get("deprecated_yn"),
                "columns": [{
                    "column_name": c["column_name"],
                    "data_type": c["data_type"],
                    "is_primary_key": c.get("is_primary_key"),
                    "column_ini": c.get("column_ini"),
                    "column_item": c.get("column_item")}
                    for c in columns],
                "joins": _joins_touching_table(rest, graph),
                # F1: a category table's values ride in its detail,
                # capped and counted — never silently truncated.
                "values": [{"code": v["code"], "meaning": v["meaning"]}
                           for v in table_values[:VALUES_SHOWN]],
                "values_total": len(table_values)})
            confirmed_tables.append(rest)
            bold.append(rest)
        elif kind == "column":
            c = graph["columns"][rest]
            joins = [_edge_row(e) for e in graph["edges"].values()
                     if any(rest in (p["source_column_id"],
                                     p["destin_column_id"])
                            for p in e["column_pairs"])]
            items.append({
                "kind": "column",
                "name": f"{c['table_name']}.{c['column_name']}",
                "description": c["column_description"],
                "data_type": c["data_type"],
                "is_primary_key": c.get("is_primary_key"),
                "key_ordinal": c.get("key_ordinal"),
                "column_ini": c.get("column_ini"),
                "column_item": c.get("column_item"),
                "deprecated_yn": c.get("deprecated_yn"),
                "owner": c["table_name"], "joins": joins})
            bold.append(rest)
            bold.append(c["table_id"])
        elif kind == "value":
            table_name, _, code = rest.rpartition(":")
            row = next(r for r in (sheets["values"] or [])
                       if r["table_name"] == table_name
                       and r["code"] == code)
            captions = []
            for e in graph["edges"].values():
                if (e["kind"] == "joins_by_fk"
                        and e["destin_table_name"] == table_name):
                    for pair in e["column_pairs"]:
                        captions.append(
                            f"{e['source_table_name']}"
                            f".{pair['source_column_name']} = {code}")
            table_id = graph["tables_by_name"].get(table_name)
            items.append({
                "kind": "value", "table_name": table_name,
                "code": code, "meaning": row["meaning"],
                "filter_captions": sorted(set(captions)),
                "table_joins": (_joins_touching_table(table_id, graph)
                                if table_id else [])})
            if table_id:
                bold.append(table_id)
        else:
            raise ValueError(f"unknown confirmed entry: {entry}")

    pairs = []
    for a, b in itertools.combinations(confirmed_tables, 2):
        joins = [_edge_row(e) for e in graph["edges"].values()
                 if {e["source_table_id"], e["destin_table_id"]} == {a, b}]
        pair = {"a": graph["tables"][a]["table_name"],
                "b": graph["tables"][b]["table_name"], "joins": joins}
        if not joins:
            pair["note"] = (
                f"no direct join recorded between {pair['a']} and "
                f"{pair['b']} — the map shows the neighborhood; "
                "multi-hop answers belong to a later phase")
        pairs.append(pair)

    if not items:
        return {"empty": True, "items": [], "pairs": [], "bold": [],
                "note": ("Nothing confirmed; the candidates shown are "
                         "the closest this dictionary has.")}
    return {"empty": False, "items": items, "pairs": pairs,
            "bold": sorted(set(bold)), "note": None}


# --------------------------------------------------------------------------
# The map layout (decision 4) — deterministic, no randomness anywhere
# --------------------------------------------------------------------------


def compute_layout(graph):
    tables = sorted(graph["tables"].values(),
                    key=lambda t: t["table_name"])
    n = max(len(tables), 1)
    cx = cy = 500.0
    pos = {}
    for i, t in enumerate(tables):
        angle = 2 * math.pi * i / n - math.pi / 2
        pos[t["table_id"]] = [cx + 380 * math.cos(angle),
                              cy + 380 * math.sin(angle)]

    pair_edges = {}
    for e in graph["edges"].values():
        key = tuple(sorted((e["source_table_id"], e["destin_table_id"])))
        agg = pair_edges.setdefault(
            key, {"count": 0, "fk": 0, "rule": 0, "joins": []})
        agg["count"] += 1
        agg["fk" if e["kind"] == "joins_by_fk" else "rule"] += 1
        agg["joins"].append(_edge_row(e))

    connected = {k: [] for k in pos}
    for a, b in pair_edges:
        if a != b:
            connected[a].append(b)
            connected[b].append(a)
    for _ in range(60):
        forces = {k: [0.0, 0.0] for k in pos}
        keys = sorted(pos)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]
                d2 = max(dx * dx + dy * dy, 1.0)
                d = math.sqrt(d2)
                rep = 60000.0 / d2
                fx, fy = rep * dx / d, rep * dy / d
                forces[a][0] -= fx
                forces[a][1] -= fy
                forces[b][0] += fx
                forces[b][1] += fy
        for a in keys:
            for b in connected[a]:
                dx = pos[b][0] - pos[a][0]
                dy = pos[b][1] - pos[a][1]
                d = max(math.sqrt(dx * dx + dy * dy), 1.0)
                pull = 0.002 * (d - 220.0)
                forces[a][0] += pull * dx / d
                forces[a][1] += pull * dy / d
        for k in keys:
            fx = max(min(forces[k][0], 15.0), -15.0)
            fy = max(min(forces[k][1], 15.0), -15.0)
            pos[k][0] = max(60.0, min(940.0, pos[k][0] + fx))
            pos[k][1] = max(60.0, min(940.0, pos[k][1] + fy))

    layout_tables = [{"id": t["table_id"], "name": t["table_name"],
                      "x": round(pos[t["table_id"]][0], 2),
                      "y": round(pos[t["table_id"]][1], 2)}
                     for t in tables]
    layout_columns = []
    for t in tables:
        cids = sorted(graph["table_columns"].get(t["table_id"], []),
                      key=lambda c: graph["columns"][c]["column_name"])
        for j, cid in enumerate(cids):
            angle = 2 * math.pi * j / max(len(cids), 1)
            layout_columns.append({
                "id": cid,
                "name": graph["columns"][cid]["column_name"],
                "table_id": t["table_id"],
                "x": round(pos[t["table_id"]][0]
                           + 28 * math.cos(angle), 2),
                "y": round(pos[t["table_id"]][1]
                           + 28 * math.sin(angle), 2)})
    layout_edges = [{"a": a, "b": b,
                     "kind": ("joins_by_fk" if agg["fk"]
                              else "joins_by_rule"),
                     "count": agg["count"], "fk": agg["fk"],
                     "rule": agg["rule"], "joins": agg["joins"]}
                    for (a, b), agg in sorted(pair_edges.items())]
    return {"tables": layout_tables, "columns": layout_columns,
            "edges": layout_edges}


# --------------------------------------------------------------------------
# The page and endpoints
# --------------------------------------------------------------------------

PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>AIVIA_01 chat — the EMR dictionary</title>
<style>
  body { font-family: -apple-system, sans-serif; margin: 1rem 2rem; }
  #question { width: 55%; padding: 0.5rem; font-size: 1rem; }
  button { padding: 0.5rem 1rem; font-size: 1rem; }
  #wrap { display: flex; gap: 1rem; margin-top: 1rem; }
  #mapbox { flex: 1.2; min-width: 420px; }
  #map { border: 1px solid #ccc; width: 100%; height: 520px;
         cursor: grab; }
  #side { flex: 1; }
  table { border-collapse: collapse; width: 100%; margin: 0.4rem 0 1rem; }
  td, th { border: 1px solid #ccc; padding: 0.25rem 0.45rem;
           text-align: left; font-size: 0.85rem; }
  h3 { margin: 0.9rem 0 0.2rem; } h4 { margin: 0.6rem 0 0.2rem; }
  .mech { color: #666; font-size: 0.8rem; }
  .gap { color: #a00; font-weight: bold; }
  .note { color: #a50; }
  #status { color: #666; margin-top: 0.4rem; }
  #detail { background: #f7f7f7; border: 1px solid #ddd;
            padding: 0.5rem; font-size: 0.85rem; max-height: 200px;
            overflow: auto; }
  svg .tnode { fill: #bbb; stroke: #888; }
  svg .cnode { fill: #ddd; }
  svg .edge { stroke: #ccc; stroke-width: 1.2; }
  svg .rule { stroke-dasharray: 5 4; }
  svg .lit  { fill: #7a5df0; stroke: #4b2fd6; }
  svg line.lit { stroke: #7a5df0; stroke-width: 2; }
  svg .bold { fill: #2f1a99; stroke: #000; stroke-width: 2; }
  svg text { font-size: 9px; fill: #444; pointer-events: none; }
  svg text.clabel { font-size: 6px; display: none; }
  svg text.clabel.show { display: block; }
</style>
</head>
<body>
<h2>AIVIA_01 chat — ask the dictionary</h2>
<input id="question" placeholder="which table contains inpatient admission data?">
<button onclick="ask()">Send</button>
<label style="margin-left:1rem"><input type="checkbox" id="rules"
 onchange="drawMap()"> show date-rule lines</label>
<div id="status"></div>
<div id="wrap">
  <div id="mapbox">
    <svg id="map" viewBox="0 0 1000 1000"></svg>
    <div id="detail">Click a table, column dot or join line for its
      stored detail.</div>
  </div>
  <div id="side">
    <div id="results"></div>
    <div id="answer"></div>
  </div>
</div>
<script>
let MAP = null, LIT = new Set(), BOLDS = new Set(), VB = [0,0,1000,1000];
function esc(s) { const d = document.createElement('div');
  d.textContent = String(s); return d.innerHTML; }
function mechWords(m) { return {lexical:'lexical (exact)',
  abstract:'abstract (curated)', embedding:'embedding (semantic)'}[m]||m; }

async function loadMap() {
  MAP = await (await fetch('/map')).json();
  drawMap();
}
function drawMap() {
  const svg = document.getElementById('map');
  const showRules = document.getElementById('rules').checked;
  const P = {};
  MAP.tables.forEach(t => P[t.id] = t);
  let out = '';
  MAP.edges.forEach(e => {
    if (e.kind === 'joins_by_rule' && !showRules) return;
    const a = P[e.a], b = P[e.b];
    if (!a || !b) return;
    const lit = LIT.has(e.a) && LIT.has(e.b) ? ' lit' : '';
    out += `<line class="edge ${e.kind==='joins_by_rule'?'rule':''}${lit}"
      x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"
      onclick="edgeDetail('${e.a}','${e.b}')"
      style="pointer-events:stroke"></line>`;
    if (e.count > 1) {
      out += `<text x="${(a.x+b.x)/2}" y="${(a.y+b.y)/2}">${e.count}</text>`;
    }
  });
  MAP.columns.forEach(c => {
    const cls = BOLDS.has(c.id) ? 'bold' : LIT.has(c.id) ? 'lit' : 'cnode';
    out += `<circle class="${cls}" cx="${c.x}" cy="${c.y}" r="2.6"
      onclick="nodeDetail('column','${c.id}')"></circle>`;
    out += `<text class="clabel ${LIT.has(c.id)||zoomed()?'show':''}"
      x="${c.x+4}" y="${c.y+2}">${esc(c.name)}</text>`;
  });
  MAP.tables.forEach(t => {
    const cls = BOLDS.has(t.id) ? 'bold' : LIT.has(t.id) ? 'lit' : 'tnode';
    out += `<circle class="${cls}" cx="${t.x}" cy="${t.y}" r="9"
      onclick="nodeDetail('table','${t.id}')"></circle>`;
    out += `<text x="${t.x+11}" y="${t.y+3}">${esc(t.name)}</text>`;
  });
  svg.innerHTML = out;
  svg.setAttribute('viewBox', VB.join(' '));
}
function zoomed() { return VB[2] < 450; }
const svgEl = () => document.getElementById('map');
let dragging = null;
window.addEventListener('load', () => {
  loadMap();
  const s = svgEl();
  s.addEventListener('mousedown', e => {
    dragging = [e.clientX, e.clientY]; });
  window.addEventListener('mouseup', () => dragging = null);
  window.addEventListener('mousemove', e => {
    if (!dragging) return;
    const sc = VB[2] / s.clientWidth;
    VB[0] -= (e.clientX - dragging[0]) * sc;
    VB[1] -= (e.clientY - dragging[1]) * sc;
    dragging = [e.clientX, e.clientY];
    s.setAttribute('viewBox', VB.join(' '));
  });
  s.addEventListener('wheel', e => {
    e.preventDefault();
    const f = e.deltaY > 0 ? 1.15 : 0.87;
    const nw = Math.min(2000, Math.max(80, VB[2] * f));
    VB[0] += (VB[2] - nw) / 2; VB[1] += (VB[3] - nw) / 2;
    VB[2] = nw; VB[3] = nw;
    drawMap();
  }, {passive: false});
  document.getElementById('question').addEventListener('keydown',
    e => { if (e.key === 'Enter') ask(); });
});
function edgeDetail(a, b) {
  const e = MAP.edges.find(x => (x.a===a&&x.b===b)||(x.a===b&&x.b===a));
  let html = `<b>${e.count} join(s)</b><br>`;
  e.joins.forEach(j => {
    html += `${esc(j.from)} → ${esc(j.to)} on ${esc(j.columns)} ` +
      `<span class="mech">[${j.kind==='joins_by_fk'?'dictionary FK':
      'date-dimension rule'}; FK owner ${esc(j.owner)}]</span><br>`;
  });
  document.getElementById('detail').innerHTML = html;
}
async function nodeDetail(kind, id) {
  const r = await fetch('/detail', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({kind, id})});
  document.getElementById('detail').innerHTML = await r.text();
}

async function ask() {
  const q = document.getElementById('question').value.trim();
  if (!q) return;
  document.getElementById('status').textContent =
    'segmenting + searching…';
  document.getElementById('answer').innerHTML = '';
  const resp = await fetch('/segment', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: q})});
  if (!resp.ok) {
    document.getElementById('status').textContent =
      'ERROR: ' + await resp.text();
    return;
  }
  const data = await resp.json();
  document.getElementById('status').textContent = '';
  LIT = new Set(data.highlight); BOLDS = new Set();
  drawMap();
  let html = '';
  data.no_match_notes.forEach(n => {
    html += `<p class="note">${esc(n.table_name)} is used in the sql
      files (${n.sql_file_names.map(esc).join(', ')}) but has NO
      dictionary match.</p>`;
  });
  data.results.forEach((res, ri) => {
    html += `<h3>“${esc(res.term)}”
      ${res.composite ? '<span class="mech">(the whole phrase)</span>' : ''}
      <span class="mech">via ${mechWords(res.mechanism)}</span></h3>`;
    if (res.no_match) {
      html += `<p class="note">matches a used-but-no-dictionary-match
        object — nothing pre-selected; the note above is the
        answer.</p>`;
    }
    if (!res.matches.length) {
      html += '<p class="mech">nothing at or above the floor</p>';
      return;
    }
    html += '<table><tr><th></th><th>kind</th><th>name</th>' +
            '<th>how</th><th>scores</th></tr>';
    res.matches.forEach((m, mi) => {
      const sc = m.scores ? Object.entries(m.scores).map(
        ([k,v]) => `${k} ${v.toFixed(3)}`).join(', ') : '';
      html += `<tr><td><input type="checkbox" class="pick"
        data-id="${m.category}:${m.id}" ${m.pre_selected?'checked':''}>
        </td><td>${esc(m.category)}</td><td>${esc(m.name)}</td>
        <td class="mech">${mechWords(m.mechanism)}</td>
        <td class="mech">${sc}</td></tr>`;
    });
    html += '</table>';
    const totals = Object.entries(res.totals || {});
    if (totals.length) {
      html += `<p class="mech">shown per population (of totals):
        ${totals.map(([k,v]) => `${k} ${v}`).join(', ')}</p>`;
    }
  });
  html += '<button onclick="confirmPicks()">Confirm</button>';
  document.getElementById('results').innerHTML = html;
}

async function confirmPicks() {
  const picked = [...document.querySelectorAll('.pick:checked')]
    .map(x => x.dataset.id);
  const resp = await fetch('/answer', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({confirmed: picked})});
  if (!resp.ok) {
    document.getElementById('status').textContent =
      'ERROR: ' + await resp.text();
    return;
  }
  const a = await resp.json();
  BOLDS = new Set(a.bold);
  drawMap();
  let html = '<h3>Answer</h3>';
  if (a.empty) { html += `<p>${esc(a.note)}</p>`; }
  a.items.forEach(it => {
    if (it.kind === 'table') {
      html += `<h4>${esc(it.name)} (table)</h4><p>${esc(it.description)}
        </p><h4>joins</h4><table><tr><th>from</th><th>to</th>
        <th>columns</th><th>how</th></tr>`;
      it.joins.forEach(j => {
        html += `<tr><td>${esc(j.from)}</td><td>${esc(j.to)}</td>
          <td>${esc(j.columns)}</td><td class="mech">
          ${j.kind==='joins_by_fk'?'dictionary FK':'date rule'}</td></tr>`;
      });
      html += '</table>';
      if (it.values_total) {
        html += `<h4>values (${it.values.length} of
          ${it.values_total})</h4><table><tr><th>code</th>
          <th>meaning</th></tr>`;
        it.values.forEach(v => {
          html += `<tr><td>${esc(v.code)}</td>
            <td>${esc(v.meaning)}</td></tr>`;
        });
        html += '</table>';
      }
      html += `<h4>columns (${it.columns.length})</h4>
        <table><tr><th>name</th><th>type</th><th>pk</th>
        <th>ini/item</th></tr>`;
      it.columns.forEach(c => {
        html += `<tr><td>${esc(c.column_name)}</td>
          <td>${esc(c.data_type)}</td><td>${c.is_primary_key?'pk':''}</td>
          <td class="mech">${c.column_ini?esc(c.column_ini)+' '+
          esc(c.column_item):''}</td></tr>`;
      });
      html += '</table>';
    } else if (it.kind === 'column') {
      html += `<h4>${esc(it.name)} (column)</h4>
        <p>${esc(it.description)}</p>
        <p class="mech">type ${esc(it.data_type)}
        ${it.is_primary_key?'· primary key':''}
        ${it.column_ini?'· '+esc(it.column_ini)+' '+esc(it.column_item):''}
        </p>`;
      if (it.joins.length) {
        html += '<table><tr><th>from</th><th>to</th><th>columns</th></tr>';
        it.joins.forEach(j => {
          html += `<tr><td>${esc(j.from)}</td><td>${esc(j.to)}</td>
            <td>${esc(j.columns)}</td></tr>`;
        });
        html += '</table>';
      }
    } else {
      html += `<h4>${esc(it.table_name)} value ${esc(it.code)} =
        “${esc(it.meaning)}” </h4>`;
      it.filter_captions.forEach(c => {
        html += `<p>filter: <b>${esc(c)}</b></p>`;
      });
    }
  });
  a.pairs.forEach(p => {
    if (p.joins.length) {
      html += `<h4>${esc(p.a)} ⇄ ${esc(p.b)}</h4><table>
        <tr><th>columns</th><th>FK owner</th></tr>`;
      p.joins.forEach(j => {
        html += `<tr><td>${esc(j.columns)}</td>
          <td>${esc(j.owner)}</td></tr>`;
      });
      html += '</table>';
    } else {
      html += `<p class="gap">${esc(p.note)}</p>`;
    }
  });
  document.getElementById('answer').innerHTML = html;
}
</script>
</body>
</html>
"""


def _detail_html(kind, obj_id, assets):
    graph = assets["graph"]
    if kind == "table":
        t = graph["tables"][obj_id]
        return (f"<b>{t['table_name']}</b><br>"
                f"{t['table_description'][:400]}")
    c = graph["columns"][obj_id]
    ini = (f" · {c.get('column_ini')} {c.get('column_item')}"
           if c.get("column_ini") else "")
    return (f"<b>{c['table_name']}.{c['column_name']}</b> "
            f"({c['data_type']}{ini})<br>"
            f"{c['column_description'][:400]}")


class ChatBotHandler(BaseHTTPRequestHandler):
    assets = None   # set by main() before the server starts
    params = None
    embedder = staticmethod(real_embedder)   # --azure swaps the pair
    chat_llm = staticmethod(real_chat)       # (M05: provider is a
    #                                          parameter, never a fork)

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload):
        self._send(200, json.dumps(payload).encode("utf-8"),
                   "application/json")

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE.encode("utf-8"),
                       "text/html; charset=utf-8")
        elif self.path == "/map":
            self._json(self.assets["layout"])
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            if self.path == "/segment":
                question = body["question"]
                tokens = segment(question, self.assets["terms"],
                                 self.chat_llm)
                terms, _global_pop = associate(tokens,
                                               self.assets["terms"])
                terms = with_composite(terms)
                results = resolve(terms, self.assets, self.embedder,
                                  self.params)
                highlight = set()
                for res in results:
                    for m in res["matches"]:
                        if m["category"] == "table":
                            highlight.add(m["id"])
                        elif m["category"] == "column":
                            highlight.add(m["id"])
                            highlight.add(self.assets["graph"][
                                "tables_by_name"][m["table_name"]])
                        else:
                            tid = self.assets["graph"][
                                "tables_by_name"].get(m["table_name"])
                            if tid:
                                highlight.add(tid)
                self._json({"tokens": tokens, "results": results,
                            "no_match_notes": scan_no_match(
                                question, self.assets),
                            "highlight": sorted(highlight)})
            elif self.path == "/answer":
                self._json(answer_confirmed(body["confirmed"],
                                            self.assets))
            elif self.path == "/detail":
                html = _detail_html(body["kind"], body["id"],
                                    self.assets)
                self._send(200, html.encode("utf-8"),
                           "text/html; charset=utf-8")
            else:
                self.send_error(404)
        except Exception as e:  # noqa: BLE001 — fail loudly INTO the page
            self._send(500, f"{type(e).__name__}: {e}".encode("utf-8"),
                       "text/plain")


def main(argv):
    positional = [a for a in argv[1:] if not a.startswith("--")]
    options = dict(a[2:].split("=", 1) for a in argv[1:]
                   if a.startswith("--") and "=" in a)
    fabric = "--fabric" in argv[1:]
    usage = ("usage: python3.11 AIVIA_01_Code/chat_bot.py "
             "<02 sheets dir> <03 data dir> [port] [flags]\n"
             "   or: ... chat_bot.py --fabric --workspace=<id> "
             "--lakehouse=<id> [--tenant=<id>] [port] [flags]\n"
             "flags: [--floor=] [--margin=] [--match=all | "
             "--match-table= --match-column= --match-value=]")
    if fabric:
        missing = [f"--{k}" for k in ("workspace", "lakehouse")
                   if k not in options]
        if missing:
            print(f"missing for --fabric: {' '.join(missing)}\n{usage}",
                  file=sys.stderr)
            return 2
    elif len(positional) < 2:
        print(usage, file=sys.stderr)
        return 2
    port_arg = positional[0] if fabric and positional else (
        positional[2] if len(positional) > 2 else None)
    port = int(port_arg) if port_arg else DEFAULT_PORT
    match = {pop: float(options.get(f"match-{pop}", default))
             for pop, default in MATCH_DEFAULTS.items()}
    if "match" in options:  # a bare --match= applies to all populations
        match = float(options["match"])
    params = {"floor": float(options.get("floor", CANDIDATE_FLOOR)),
              "match": match,
              "margin": float(options.get("margin", UNIQUE_MARGIN))}

    if fabric:
        from fabric_assets import load_assets_fabric
        from sync_files import STORAGE_SCOPE
        from sync_wheel import sign_in

        print("loading assets FROM FABRIC (stage A) — browser "
              "sign-in, then the Delta reads…")
        token = sign_in(options.get("tenant", "organizations"),
                        scope=STORAGE_SCOPE)
        assets = load_assets_fabric(options["workspace"],
                                    options["lakehouse"], token)
    else:
        print(f"loading assets from {positional[0]} + {positional[1]} "
              "— the column sheet is large, one moment…")
        assets = load_assets(positional[0], positional[1])
    azure = "--azure" in argv[1:]
    if azure:
        from azure_models import AZURE_ENDPOINT, azure_chat, azure_embedder

        ChatBotHandler.embedder = staticmethod(azure_embedder)
        ChatBotHandler.chat_llm = staticmethod(azure_chat)
    census = assets["census"]
    print("chat startup census:")
    print(f"  assets: {'fabric' if fabric else 'local'}")
    print("  models: " + (f"azure ({AZURE_ENDPOINT})" if azure
                          else "openai"))
    for k in ("tables", "columns", "values", "value_search",
              "abstract_rows", "keywords", "no_match"):
        print(f"  {k}: {census[k]}")
    if not census["lane2_ready"]:
        print("  LANE 2 SKIPPED — no abstract list; run "
              "build_abstract_names.py to enable it")
    print(f"  acceptance defaults: floor {params['floor']} / match "
          f"{params['match']} / margin {params['margin']}")
    print(f"  per question: one {CHAT_MODEL} call + at most one "
          "batched embedding call")

    ChatBotHandler.assets = assets
    ChatBotHandler.params = params
    server = HTTPServer(("127.0.0.1", port), ChatBotHandler)
    print(f"AIVIA_01 chat: http://localhost:{port}")
    print("Ctrl+C to stop")
    server.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
