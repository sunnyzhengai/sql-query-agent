"""Phase 03 contract tests (AIVIA_01_Design/03_chat_bot_data_contract.md).

This file grows with each phase-03 code file. Current section: the
name-abstract list builder (AIVIA_01_Code/build_abstract_names.py,
design L03, contract Output File 2).

Written test-first: RED until build_abstract_names.py exposes
    build_abstracts(sheets_dir, out_dir, llm) -> census, PROMPT,
    real_llm.

Paid-call law: the LLM calls are real (gpt-5-mini) on tiny synthetic
sheets — pennies. The full-corpus run is Sunny's hand.

The three laws under test (design L03, fingerprint SKIPPED by ruling):
    REUSE by key — existing rows reused verbatim, only new objects
    generate; SUNNY PRESERVATION — sunny_* fields survive every
    rebuild; COVERAGE — every table and column has exactly one row,
    dropped objects are counted with their sunny_* content echoed.
"""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "AIVIA_01_Code"

sys.path.insert(0, str(CODE_DIR))
import build_abstract_names  # noqa: E402

OUT_NAME = "03_chat_abstract_names.json"


def _mini_sheets(root):
    """Two tables, three columns — enough to exercise every law with
    ONE batched LLM call. Distinctive synthetic names so the
    no-examples prompt test can grep for them."""
    (root / "02_emr_data_dictionary_extraction_table.json").write_text(
        json.dumps([
            {"table_id": "T1", "table_name": "SYNTH_ENCOUNTER_TBL",
             "table_description": "Synthetic encounter records."},
            {"table_id": "T2", "table_name": "SYNTH_STATUS_CAT",
             "table_description": "Synthetic status categories."},
        ]), encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_column.json").write_text(
        json.dumps([
            {"column_id": "C1", "table_id": "T1", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
             "table_name": "SYNTH_ENCOUNTER_TBL",
             "column_name": "SYNTH_ENC_ID", "data_type": "VARCHAR",
             "column_description": "The synthetic encounter id."},
            {"column_id": "C2", "table_id": "T1", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
             "table_name": "SYNTH_ENCOUNTER_TBL",
             "column_name": "SYNTH_STATUS_C", "data_type": "INTEGER",
             "column_description": "The synthetic status code."},
            {"column_id": "C3", "table_id": "T2", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
             "table_name": "SYNTH_STATUS_CAT",
             "column_name": "NAME", "data_type": "VARCHAR",
             "column_description": "The status meaning."},
        ]), encoding="utf-8")
    (root / "02_emr_data_dictionary_extraction_join.json").write_text(
        "[]", encoding="utf-8")


def _forbidden_llm(batch):
    raise AssertionError(f"LLM called for reused objects: {batch[:2]}")


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    root = tmp_path_factory.mktemp("abstracts")
    _mini_sheets(root)
    out = root / "out"
    out.mkdir()
    census = build_abstract_names.build_abstracts(
        root, out, build_abstract_names.real_llm)
    rows = json.loads((out / OUT_NAME).read_text(encoding="utf-8"))
    return root, out, census, rows


def test_abstracts_cover_every_object(built):
    _, _, census, rows = built
    assert len(rows) == 5  # 2 tables + 3 columns
    assert census["generated_new"] == 5 and census["reused"] == 0
    kinds = {(r["object_kind"], r["object_name"]) for r in rows}
    assert ("table", "SYNTH_ENCOUNTER_TBL") in kinds
    assert ("column", "SYNTH_ENCOUNTER_TBL.SYNTH_ENC_ID") in kinds
    for r in rows:
        # the contract's exact field list, nothing more, nothing less
        assert set(r) == {"object_kind", "object_id", "object_name",
                          "abstract", "synonyms",
                          "sunny_abstract", "sunny_synonyms"}
        assert isinstance(r["abstract"], str) and r["abstract"].strip()
        assert isinstance(r["synonyms"], list)
        assert all(isinstance(s, str) for s in r["synonyms"])
        assert r["sunny_abstract"] == "" and r["sunny_synonyms"] == []


def test_reuse_by_key_makes_zero_llm_calls(built):
    root, out, _, _ = built
    census = build_abstract_names.build_abstracts(
        root, out, _forbidden_llm)
    assert census["generated_new"] == 0
    assert census["reused"] == 5


def test_new_object_generates_only_that_row(tmp_path, built):
    root, out, _, old_rows = built
    _mini_sheets(tmp_path)
    out2 = tmp_path / "out"
    out2.mkdir()
    (out2 / OUT_NAME).write_text(json.dumps(old_rows), encoding="utf-8")
    cols = json.loads(
        (tmp_path / "02_emr_data_dictionary_extraction_column.json")
        .read_text(encoding="utf-8"))
    cols.append({"column_id": "C4", "table_id": "T2",
                 "database_name": "synth", "schema_name": "dbo",
                 "deprecated_yn": "N",
                 "table_name": "SYNTH_STATUS_CAT",
                 "column_name": "SYNTH_ABBR", "data_type": "VARCHAR",
                 "column_description": "The synthetic abbreviation."})
    (tmp_path / "02_emr_data_dictionary_extraction_column.json").write_text(
        json.dumps(cols), encoding="utf-8")
    census = build_abstract_names.build_abstracts(
        tmp_path, out2, build_abstract_names.real_llm)
    assert census["generated_new"] == 1 and census["reused"] == 5
    rows = json.loads((out2 / OUT_NAME).read_text(encoding="utf-8"))
    new = [r for r in rows if r["object_id"] == "C4"]
    assert len(new) == 1 and new[0]["abstract"].strip()


def test_sunny_fields_survive_every_rebuild(tmp_path, built):
    root, _, _, old_rows = built
    _mini_sheets(tmp_path)
    out2 = tmp_path / "out"
    out2.mkdir()
    rows = json.loads(json.dumps(old_rows))
    target = next(r for r in rows if r["object_id"] == "C2")
    target["sunny_abstract"] = "Sunny's own words stand."
    target["sunny_synonyms"] = ["sunny-term"]
    (out2 / OUT_NAME).write_text(json.dumps(rows), encoding="utf-8")
    build_abstract_names.build_abstracts(tmp_path, out2, _forbidden_llm)
    rebuilt = json.loads((out2 / OUT_NAME).read_text(encoding="utf-8"))
    kept = next(r for r in rebuilt if r["object_id"] == "C2")
    assert kept["sunny_abstract"] == "Sunny's own words stand."
    assert kept["sunny_synonyms"] == ["sunny-term"]


def test_dropped_object_is_counted_with_sunny_echo(tmp_path, built):
    root, _, _, old_rows = built
    _mini_sheets(tmp_path)
    out2 = tmp_path / "out"
    out2.mkdir()
    rows = json.loads(json.dumps(old_rows))
    doomed = next(r for r in rows if r["object_id"] == "C3")
    doomed["sunny_abstract"] = "do not lose me silently"
    (out2 / OUT_NAME).write_text(json.dumps(rows), encoding="utf-8")
    cols = json.loads(
        (tmp_path / "02_emr_data_dictionary_extraction_column.json")
        .read_text(encoding="utf-8"))
    cols = [c for c in cols if c["column_id"] != "C3"]
    (tmp_path / "02_emr_data_dictionary_extraction_column.json").write_text(
        json.dumps(cols), encoding="utf-8")
    census = build_abstract_names.build_abstracts(
        tmp_path, out2, _forbidden_llm)
    rebuilt = json.loads((out2 / OUT_NAME).read_text(encoding="utf-8"))
    assert not any(r["object_id"] == "C3" for r in rebuilt)
    [dropped] = census["dropped"]
    assert dropped["object_name"] == "SYNTH_STATUS_CAT.NAME"
    assert dropped["sunny_abstract"] == "do not lose me silently"


def test_checkpoint_survives_midrun_failure(tmp_path, monkeypatch):
    # Echo Law build (2026-09-30, from Sunny's live billing_not_active
    # failure): the output writes after EVERY batch, so an interruption
    # loses nothing paid — the rerun reuses the partial file and pays
    # only for the remainder. First batch is a real call; the second
    # raises, simulating the mid-run death.
    _mini_sheets(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    monkeypatch.setattr(build_abstract_names, "BATCH_SIZE", 2)
    calls = {"n": 0}

    def flaky(batch):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("simulated mid-run billing failure")
        return build_abstract_names.real_llm(batch)

    with pytest.raises(RuntimeError, match="billing"):
        build_abstract_names.build_abstracts(tmp_path, out, flaky)
    partial = json.loads((out / OUT_NAME).read_text(encoding="utf-8"))
    assert len(partial) == 2  # the paid first batch survived
    assert all(r["abstract"].strip() for r in partial)
    census = build_abstract_names.build_abstracts(
        tmp_path, out, build_abstract_names.real_llm)
    assert census["reused"] == 2 and census["generated_new"] == 3


def test_prompt_carries_no_example_objects():
    # The prompt teaches the SHAPE abstractly — no object examples
    # (prompt-examples-are-data law). Neither our synthetic names nor
    # canonical demo-table names may appear in it.
    prompt = build_abstract_names.PROMPT
    for name in ("SYNTH_ENCOUNTER_TBL", "SYNTH_STATUS_CAT",
                 "SYNTH_ENC_ID", "PATIENT", "CUSTOMER", "ORDERS"):
        assert name not in prompt.upper(), f"example object in PROMPT: {name}"


# ---------------------------------------------------------------------------
# Section 2 — the chat (AIVIA_01_Code/chat_bot.py, design L05, all ten
# decisions). RED until the real code lands. Synthetic assets with REAL
# embeddings (pennies); segmentation tests are mechanism-level (LLM
# nondeterminism accepted); real-asset tests are structural, no API.
# ---------------------------------------------------------------------------

import chat_bot  # noqa: E402
from test_01_subject_sql_files_data_contract import real_embedder  # noqa: E402

DATA02 = REPO_ROOT / "AIVIA_01_Data" / "02_emr_data_dictionary"
DATA03 = REPO_ROOT / "AIVIA_01_Data" / "03_chat_bot"

SYNTH_TERMS_MD = """03_chat_technical_terms — synthetic
Structure: keyword | maps_to | kind | synonyms | ruled

| keyword | maps_to      | kind       | synonyms        | ruled      |
|---------|--------------|------------|-----------------|------------|
| table   | table nodes  | population | tables, entity  | 2026-09-30 |
| column  | column nodes | population | field, fields   | 2026-09-30 |
| value   | value rows   | population | code, lookup    | 2026-09-30 |
| join    | join edges   | operation  | link, FK        | 2026-09-30 |
"""


def _mini_chat_assets(root):
    """The mini estate with REAL embeddings: two joined tables, an
    island, a duplicated column name for the ambiguity rule, a value
    with sidecar, a terms file and an abstract list."""
    tables = [
        {"table_id": "T1", "table_name": "SYNTH_ENCOUNTER_TBL",
         "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_description": "Synthetic encounter records."},
        {"table_id": "T2", "table_name": "SYNTH_STATUS_CAT",
         "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_description": "Synthetic status categories."},
        {"table_id": "T3", "table_name": "SYNTH_ISLAND_TBL",
         "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_description": "A synthetic island."},
    ]
    columns = [
        {"column_id": "C1", "table_id": "T1", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_name": "SYNTH_ENCOUNTER_TBL", "column_name": "SYNTH_ENC_ID",
         "data_type": "VARCHAR",
         "column_description": "The synthetic encounter id."},
        {"column_id": "C2", "table_id": "T1", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_name": "SYNTH_ENCOUNTER_TBL",
         "column_name": "SYNTH_STATUS_C", "data_type": "INTEGER",
         "column_description": "The synthetic status code."},
        {"column_id": "C3", "table_id": "T2", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_name": "SYNTH_STATUS_CAT", "column_name": "NAME",
         "data_type": "VARCHAR", "column_description": "The status meaning."},
        {"column_id": "C5", "table_id": "T2", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_name": "SYNTH_STATUS_CAT", "column_name": "SYNTH_STATUS_C",
         "data_type": "INTEGER",
         "column_description": "The category id column."},
        {"column_id": "C6", "table_id": "T3", "database_name": "synth", "schema_name": "dbo", "deprecated_yn": "N",
         "table_name": "SYNTH_ISLAND_TBL", "column_name": "SYNTH_ISLAND_ID",
         "data_type": "VARCHAR", "column_description": "The island id."},
    ]
    texts, plans = [], []
    for t in tables:
        for field, text in (("table_name_embedding", t["table_name"]),
                            ("table_description_embedding",
                             t["table_description"])):
            plans.append((t, field))
            texts.append(text)
    for c in columns:
        for field, text in (("column_name_embedding", c["column_name"]),
                            ("column_description_embedding",
                             c["column_description"])):
            plans.append((c, field))
            texts.append(text)
    values = [{"table_name": "SYNTH_STATUS_CAT", "code": "1",
               "meaning": "Active"}]
    plans.append((values[0], "meaning_embedding"))
    texts.append("Active")
    vectors = real_embedder(texts)
    for (row, field), vec in zip(plans, vectors):
        row[field] = vec
    sidecar = [dict(values[0])]
    values = [{k: v for k, v in values[0].items()
               if k != "meaning_embedding"}]

    joins = [{"join_id": "T1:1", "ordinal": 1,
              "source_table_id": "T1",
              "source_table_name": "SYNTH_ENCOUNTER_TBL",
              "source_column_id": "C2", "source_column_name": "SYNTH_STATUS_C",
              "destin_table_id": "T2", "destin_table_name": "SYNTH_STATUS_CAT",
              "destin_column_id": "C5", "destin_column_name": "SYNTH_STATUS_C",
              "conditional_c": "3", "may_be_stale_c": "2",
              "is_current_data_model_yn": "Y", "is_supplemental_yn": "N",
              "destin_in_scope": True}]
    base = "02_emr_data_dictionary_extraction_"
    for name, doc in (("table", tables), ("column", columns),
                      ("join", joins), ("value", values),
                      ("value_embeddings", sidecar)):
        (root / f"{base}{name}.json").write_text(
            json.dumps(doc), encoding="utf-8")
    (root / "02_no_dictionary_match.json").write_text(json.dumps(
        [{"database_name": "clarity", "schema_name": "dbo",
          "table_name": "SYNTH_GHOST_TBL", "column_name": "",
          "sql_file_names": ["f1"]}]), encoding="utf-8")
    (root / "03_chat_technical_terms.md").write_text(
        SYNTH_TERMS_MD, encoding="utf-8")
    (root / "03_chat_abstract_names.json").write_text(json.dumps([
        {"object_kind": "table", "object_id": "T1",
         "object_name": "SYNTH_ENCOUNTER_TBL",
         "abstract": "Synthetic encounters.",
         "synonyms": ["synthetic visits"],
         "sunny_abstract": "", "sunny_synonyms": []},
        {"object_kind": "column", "object_id": "C2",
         "object_name": "SYNTH_ENCOUNTER_TBL.SYNTH_STATUS_C",
         "abstract": "The status code.", "synonyms": ["status flag"],
         "sunny_abstract": "", "sunny_synonyms": ["sunnyism"]},
    ]), encoding="utf-8")


@pytest.fixture(scope="module")
def chat_assets(tmp_path_factory):
    root = tmp_path_factory.mktemp("chat")
    _mini_chat_assets(root)
    return chat_bot.load_assets(root, root)


def _forbidden_embedder(texts):
    raise AssertionError(f"embedded lane-1/2 terms: {texts[:2]}")


LOOSE = {"floor": 0.1, "match": 0.2, "margin": 0.5}


def test_terms_parser_loads_and_fails_loudly(tmp_path):
    rows = chat_bot.parse_terms(SYNTH_TERMS_MD)
    kw = {r["keyword"]: r for r in rows}
    assert kw["table"]["kind"] == "population"
    assert "entity" in kw["table"]["synonyms"]
    bad = SYNTH_TERMS_MD + "| broken | only three | cells |\n"
    with pytest.raises(ValueError, match="line"):
        chat_bot.parse_terms(bad)
    worse = SYNTH_TERMS_MD.replace("population", "poplation", 1)
    with pytest.raises(ValueError, match="kind"):
        chat_bot.parse_terms(worse)


def test_lexical_folding_and_ambiguity(chat_assets):
    [res] = chat_bot.resolve(
        [{"text": "synth encounter tbl", "population": None}],
        chat_assets, _forbidden_embedder, LOOSE)
    [m] = res["matches"]
    assert m["mechanism"] == "lexical" and m["category"] == "table"
    assert m["pre_selected"] is True
    # SYNTH_STATUS_C exists in TWO tables: both shown, NONE pre-selected
    [res] = chat_bot.resolve(
        [{"text": "synth status c", "population": None}],
        chat_assets, _forbidden_embedder, LOOSE)
    assert len(res["matches"]) == 2
    assert {m["table_name"] for m in res["matches"]} == {
        "SYNTH_ENCOUNTER_TBL", "SYNTH_STATUS_CAT"}
    assert not any(m["pre_selected"] for m in res["matches"])


def test_funnel_stops_at_first_hit(chat_assets):
    # lane 1 (a value meaning) and lane 2 (an abstract synonym + a
    # sunny synonym) resolve with NO embedding call.
    results = chat_bot.resolve(
        [{"text": "Active", "population": None},
         {"text": "status flag", "population": None},
         {"text": "sunnyism", "population": None}],
        chat_assets, _forbidden_embedder, LOOSE)
    assert results[0]["matches"][0]["mechanism"] == "lexical"
    assert results[0]["matches"][0]["category"] == "value"
    assert results[1]["matches"][0]["mechanism"] == "abstract"
    assert results[1]["matches"][0]["name"] == (
        "SYNTH_ENCOUNTER_TBL.SYNTH_STATUS_C")
    assert results[2]["matches"][0]["mechanism"] == "abstract"


def test_lane3_keyword_orders_and_favors(chat_assets):
    # no lexical/abstract hit -> lane 3 embeds; the keyword population
    # sorts first and is the only one pre-selected. Never hides others.
    [res] = chat_bot.resolve(
        [{"text": "status information", "population": "table"}],
        chat_assets, real_embedder, LOOSE)
    assert all(m["mechanism"] == "embedding" for m in res["matches"])
    assert res["matches"][0]["category"] == "table"
    assert any(m["category"] != "table" for m in res["matches"])
    assert all(m["category"] == "table"
               for m in res["matches"] if m["pre_selected"])
    # without the keyword, other populations may pre-select too
    [free] = chat_bot.resolve(
        [{"text": "status information", "population": None}],
        chat_assets, real_embedder, LOOSE)
    assert any(m["pre_selected"] for m in free["matches"])


def test_segment_prompt_is_data_only():
    rows = chat_bot.parse_terms(SYNTH_TERMS_MD)
    prompt = chat_bot.build_segment_prompt(rows)
    assert "entity" in prompt  # the terms ride as data
    for name in ("SYNTH_ENCOUNTER_TBL", "PATIENT", "CUSTOMER",
                 "for example", "e.g."):
        assert name.upper() not in prompt.upper(), (
            f"example content in prompt: {name}")


def test_segmentation_real_call_mechanism_level(chat_assets):
    tokens = chat_bot.segment("which table has the synth status?",
                              chat_assets["terms"], chat_bot.real_chat)
    assert any(t["role"] == "keyword" and t["keyword"] == "table"
               for t in tokens)
    assert any(t["role"] == "term" for t in tokens)
    for t in tokens:
        assert t["text"].casefold() in "which table has the synth status?"


def test_answer_is_strict(chat_assets):
    ans = chat_bot.answer_confirmed(["table:T1"], chat_assets)
    [item] = ans["items"]
    assert item["description"] == "Synthetic encounter records."
    assert any(j["join_id"] == "T1:1" for j in item["joins"])
    assert "Active" not in json.dumps(ans)  # unconfirmed value absent
    empty = chat_bot.answer_confirmed([], chat_assets)
    assert empty["empty"] and "Nothing confirmed" in empty["note"]
    both = chat_bot.answer_confirmed(["table:T1", "table:T2"], chat_assets)
    [pair] = both["pairs"]
    assert pair["joins"] and pair["joins"][0]["join_id"] == "T1:1"
    apart = chat_bot.answer_confirmed(["table:T1", "table:T3"], chat_assets)
    [gap] = apart["pairs"]
    assert not gap["joins"] and "no direct join recorded" in gap["note"]


def test_value_confirmed_carries_caption(chat_assets):
    ans = chat_bot.answer_confirmed(
        ["value:SYNTH_STATUS_CAT:1"], chat_assets)
    [item] = ans["items"]
    assert item["meaning"] == "Active" and item["code"] == "1"
    assert any("SYNTH_ENCOUNTER_TBL.SYNTH_STATUS_C = 1" in c
               for c in item["filter_captions"])


def test_confirmed_table_carries_its_values(chat_assets):
    # F1 (ruled 2026-09-30, from the shape 10/11 run): a confirmed
    # category table's detail includes its value rows, capped and
    # counted; a table without values shows an honest empty list.
    ans = chat_bot.answer_confirmed(["table:T2"], chat_assets)
    [item] = ans["items"]
    assert item["values"] == [{"code": "1", "meaning": "Active"}]
    assert item["values_total"] == 1
    ans2 = chat_bot.answer_confirmed(["table:T1"], chat_assets)
    assert ans2["items"][0]["values"] == []
    assert ans2["items"][0]["values_total"] == 0


def test_fold_strips_edge_punctuation(chat_assets):
    # F2 (Echo Law, from the live S5 run): a trailing period must not
    # knock a term out of the certainty lane.
    assert chat_bot._fold("SYNTH_ENCOUNTER_TBL.") == "synth encounter tbl"
    assert chat_bot._fold("(synth enc id)") == "synth enc id"
    assert chat_bot._fold("patient's race") == "patient's race"
    [res] = chat_bot.resolve(
        [{"text": "SYNTH_ENCOUNTER_TBL.", "population": None}],
        chat_assets, _forbidden_embedder, LOOSE)
    assert res["mechanism"] == "lexical"
    assert res["matches"][0]["pre_selected"] is True


def test_no_match_term_never_preselects(chat_assets):
    # F3 (from the live S8 run): a term naming a no-dictionary-match
    # object still shows its lane-3 matches, but nothing pre-selects —
    # the no-match note is the answer.
    [res] = chat_bot.resolve(
        [{"text": "SYNTH_GHOST_TBL", "population": None}],
        chat_assets, real_embedder, LOOSE)
    assert res["no_match"] is True
    assert res["matches"], "matches still shown, never hidden"
    assert not any(m["pre_selected"] for m in res["matches"])


def test_per_population_match_defaults(chat_assets):
    # Calibration RULED 2026-09-30 (the twelve-shape run, all passed):
    # match is per population — table 0.40 / column 0.50 / value 0.60;
    # floor and margin stay global. A float match still applies to all
    # populations (the calibration flags keep working).
    assert chat_bot.MATCH_DEFAULTS == {"table": 0.40, "column": 0.50,
                                       "value": 0.60}
    per_pop = {"floor": 0.1, "margin": 0.5,
               "match": {"table": 0.0, "column": 9.0, "value": 9.0}}
    [res] = chat_bot.resolve(
        [{"text": "status information", "population": None}],
        chat_assets, real_embedder, per_pop)
    pre = {m["category"] for m in res["matches"] if m["pre_selected"]}
    assert pre == {"table"}  # only the population whose bar is clearable
    all_high = dict(per_pop, match=9.0)
    [res2] = chat_bot.resolve(
        [{"text": "status information", "population": None}],
        chat_assets, real_embedder, all_high)
    assert not any(m["pre_selected"] for m in res2["matches"])


def test_composite_term_rescues_a_bad_split(chat_assets):
    # Ruled 2026-09-30 (from the live shape-2 run): with 2+ terms, the
    # joined text is searched as one extra term — the whole-phrase
    # meaning survives ANY segmentation split, deterministically. Here
    # the split even broke an exact NAME; the composite rejoins it and
    # lands in the certainty lane.
    terms = chat_bot.with_composite([
        {"text": "synth encounter", "population": None},
        {"text": "tbl", "population": None}])
    assert terms[-1]["composite"] is True
    assert terms[-1]["text"] == "synth encounter tbl"
    results = chat_bot.resolve(terms, chat_assets, real_embedder, LOOSE)
    comp = results[-1]
    assert comp["composite"] is True
    assert comp["mechanism"] == "lexical"
    assert comp["matches"][0]["name"] == "SYNTH_ENCOUNTER_TBL"
    # a single term gains no composite
    solo = [{"text": "anything", "population": None}]
    assert chat_bot.with_composite(list(solo)) == solo


def test_map_layout_deterministic_and_complete(chat_assets):
    a = chat_bot.compute_layout(chat_assets["graph"])
    b = chat_bot.compute_layout(chat_assets["graph"])
    assert json.dumps(a) == json.dumps(b)
    assert len(a["tables"]) == 3 and len(a["columns"]) == 5
    [edge] = a["edges"]
    assert edge["count"] == 1 and edge["kind"] == "joins_by_fk"


def test_real_assets_smoke():
    if not (DATA03 / "03_chat_abstract_names.json").exists():
        pytest.skip("abstract list not built yet")
    assets = chat_bot.load_assets(DATA02, DATA03)
    census = assets["census"]
    # Re-based 2026-10-02: the CR_STAT_EXECUTION supplemental entry.
    assert census["tables"] == 39 and census["columns"] == 1621
    assert census["abstract_rows"] >= 1660
    assert census["lane2_ready"] is True
