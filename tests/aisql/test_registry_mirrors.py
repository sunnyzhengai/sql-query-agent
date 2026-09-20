"""E3 LOCK 2 — THE MIRROR-CHECKS (the literal law; the
USAGE_ACTIONS clarify-bug is the standing reason: a ruled set lived
in code, a second writer extended it elsewhere, nothing forced the
homes to agree). Every importable schema-mirror constant is
asserted EQUAL to its registry Closed_Sets row — extending a set
now requires the registry bump first, or this fails.

Proves: contract:aisql-design-to-code
"""
from aisql.graph import metamodel


def _closed(registry: str, name: str) -> set:
    sheet = metamodel.load(registry).sheets["Closed_Sets"]
    row = next(r for r in sheet if r["Set"] == name)
    return set(row["Members"].split("|"))


# ---- kg3: the seven ruled sets ---------------------------------------
def test_kg3_sets_mirror_the_registry():
    from aisql.graph import kg3_artifacts as k
    assert set(k.STATE_CLASSES) == _closed("kg3_artifacts",
                                           "STATE_CLASSES")
    assert set(k.EVENT_CLASSES) == _closed("kg3_artifacts",
                                           "EVENT_CLASSES")
    assert set(k.DESCRIPTION_STATUS) == _closed("kg3_artifacts",
                                                "DESCRIPTION_STATUS")
    assert set(k.RULINGS) == _closed("kg3_artifacts", "RULINGS")
    assert set(k.USAGE_ACTIONS) == _closed("kg3_artifacts",
                                           "USAGE_ACTIONS")
    assert set(k.ASKED_OUTCOMES) == _closed("kg3_artifacts",
                                            "ASKED_OUTCOMES")
    assert set(k.OBSERVED_OUTCOMES) == _closed("kg3_artifacts",
                                               "OBSERVED_OUTCOMES")


def test_derivation_lens_state_classes_mirror():
    from aisql.lenses import derivation
    assert set(derivation.STATE_CLASSES) == _closed("kg3_artifacts",
                                                    "STATE_CLASSES")


# ---- ask console -----------------------------------------------------
def test_display_modes_mirror_ask_views():
    from aisql.flows import ask
    assert set(ask.DISPLAY_MODES) == _closed("lenses", "ASK_VIEWS")


def test_gap_census_keys_mirror():
    from aisql.graph import kg1_intake
    from aisql.graph.read_api import ReadApi
    from aisql.lenses import census
    read = ReadApi(kg1_intake.new_store())
    keys = set(census.lens_gap_census(read, None)) \
        - {"completeness", "stamp"}
    assert keys == _closed("lenses", "GAP_CENSUS_KEYS")


# ---- kind library ----------------------------------------------------
def test_pred_roles_mirror():
    from aisql.graph import kg2_translator
    assert set(kg2_translator._PRED_ROLES) == _closed(
        "kg2_kind_library", "PRED_ROLES")


def test_comparison_kind_values_are_predicate_kinds():
    from aisql.graph import kg2_mapper
    declared = {r["Kind"] for r in metamodel.load(
        "kg2_kind_library").sheets["Predicate_Kinds"]}
    assert set(kg2_mapper.COMPARISON_KINDS.values()) <= declared


def test_op_symbols_cover_the_order_family():
    from aisql.lenses import decisions
    fam = _closed("kg2_kind_library", "COMPARATOR_ORDER_FAMILY")
    assert fam <= set(decisions.OP_SYMBOL)


# ---- speech / lenses -------------------------------------------------
def test_sheet_kinds_values_are_speech_source_rows():
    from aisql.flows import speech
    labels = {r["Label"] for r in metamodel.load(
        "lenses").sheets["Speech_Sources"]}
    assert set(speech.SHEET_KINDS.values()) <= labels


def test_registry_names_mirror_the_disk():
    import pathlib

    from aisql.graph.metamodel import REGISTRY_DIR, REGISTRY_NAMES
    disk = {p.stem for p in
            pathlib.Path(REGISTRY_DIR).glob("*.json")}
    assert set(REGISTRY_NAMES) == disk


def test_v1_lenses_mirror_the_catalog():
    from aisql.lenses import registry
    names = {r["Lens"] for r in metamodel.load(
        "lenses").sheets["Catalog_v1"] if r.get("Lens")
        and r["Lens"] != "_ruling"}
    assert set(registry.V1_LENSES) <= names


# ---- the generator guard (echo law): a duplicate registry key in a
# converter dict silently discards the earlier entry — the exact trap
# that ate the kg3 Closed_Sets sheet on first landing (2026-09-09)
def test_converter_dicts_carry_no_duplicate_keys():
    import ast
    import pathlib

    from aisql.graph.metamodel import REGISTRY_DIR
    src = (pathlib.Path(REGISTRY_DIR)
           / "convert_from_xlsx.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(
                node.value, ast.Dict) and getattr(
                node.targets[0], "id", "") in (
                "TWIN_SHEETS", "ADD_SHEETS", "SOURCES"):
            keys = [ast.literal_eval(k) for k in node.value.keys]
            dupes = {k for k in keys if keys.count(k) > 1}
            assert not dupes, (
                f"{node.targets[0].id} holds duplicate keys "
                f"{dupes} — the later entry silently wins")
