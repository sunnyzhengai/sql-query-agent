"""Slice 0: the registry loader — code consumes ratified registries only.

Protocol step 5's enforcement point: aivia code never sees the doc's
prose; it sees these loaded, stamped, ratified registries. The loader
refuses anything unratified — a draft registry cannot feed a build.
"""
import dataclasses

import pytest

from aivia.graph import metamodel

SEVEN = {"kg1_technical", "kg2_kind_library", "kg2_logic",
         "kg3_artifacts", "kg4_concepts", "lenses", "flows"}


def test_load_all_returns_exactly_the_seven():
    regs = metamodel.load_all()
    assert set(regs) == SEVEN


def test_every_loaded_registry_is_ratified_v1():
    for reg in metamodel.load_all().values():
        assert reg.ratified is True
        assert reg.version == "1.0.0"


def test_load_single_exposes_sheets_and_stamp():
    kl = metamodel.load("kg2_kind_library")
    assert kl.name == "kg2_kind_library"
    assert "Predicate_Kinds" in kl.sheets
    kinds = {r["Kind"] for r in kl.sheets["Predicate_Kinds"]}
    assert "IN_SELECTION" in kinds
    assert kl.doc_section.startswith("Level 1")


def test_unknown_registry_refused_by_name():
    with pytest.raises(metamodel.UnknownRegistryError) as exc:
        metamodel.load("kg9_imaginary")
    assert "kg9_imaginary" in str(exc.value)


def test_unratified_registry_refused(tmp_path, monkeypatch):
    draft = {"registry": "kg1_technical",
             "stamp": {"version": "0.9-draft", "doc_section": "x",
                       "doc_stamp": "x", "ratified": False,
                       "converted_on": "x", "converted_from": "x"},
             "sheets": {}}
    p = tmp_path / "kg1_technical.json"
    p.write_text(__import__("json").dumps(draft))
    monkeypatch.setattr(metamodel, "REGISTRY_DIR", tmp_path)
    with pytest.raises(metamodel.UnratifiedRegistryError) as exc:
        metamodel.load("kg1_technical")
    assert "kg1_technical" in str(exc.value)


def test_registry_is_frozen():
    reg = metamodel.load("lenses")
    with pytest.raises(dataclasses.FrozenInstanceError):
        reg.version = "2.0.0"


def test_v1_lens_scope_readable_as_data():
    cat = metamodel.load("lenses").sheets["Catalog_v1"]
    v1 = [r["Lens"] for r in cat if r["v1"] == "yes"]
    assert len(v1) == 14  # +current, the A6 row landed at slice 4
    assert "referenced-keys" in v1 and "current" in v1
    deferred = [r for r in cat if r["v1"].startswith("deferred (")]
    assert len(v1) + len(deferred) == len(cat)
