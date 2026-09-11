"""Slice 0: the registry loader — code consumes ratified registries only.

Protocol step 5's enforcement point: aivia code never sees the doc's
prose; it sees these loaded, stamped, ratified registries. The loader
refuses anything unratified — a draft registry cannot feed a build.

Proves: contract:aivia-design-to-code
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
    # 1.1.0 = the twin-graph ruling amendments (ADR 0077, 2026-09-06)
    # 1.2.0 = the Phase A metamodel bump (PROJECTION, same day)
    # 1.3.0 = the Phase B composite-kinds correction (same day)
    # 1.4.0 = the T-2 operational-statements ruling (same day)
    # 1.5.0 = the gap taxonomy (Sunny: ruled-silent vs open, same day)
    # 1.6.0 = the plug-all-holes sweep (same day)
    # 1.7.0 = the ledger close (same day)
    # 1.8.0 = the ask-the-graph console (ADR 0078, same day)
    # 1.9.0 = the list op (Sunny live-ask ruling, same day)
    # 1.10.0 = kind vocabulary as registry law (same day)
    # 1.11.0 = ADR 0079 interpreter + speaking graph (same day)
    # 1.12.0 = Tier A build data: ranking weights (same day)
    # 1.13.0 = the seat-failure law (live find 6, same day)
    # 1.14.0 = follow-up context is data (live find 7, 09-07)
    # 1.15.0 = anaphor vocabulary as registry data (same day);
    # 1.16.0 = the conversation surface (find #7 second leg);
    # 1.17.0 = the path tier + the report floor (finds #8/#9);
    # 1.18.0 = the center + three censuses (ADR 0080);
    # 1.19.0 = Grounding_Thresholds (the 0080 build; cliffs die);
    # 1.20.0 = the nine-law dig build (vocab tables die; shapes +
    # ladder as data; kind self-descriptions);
    # 1.21.0 = the Connection Ledger (birth-edge law; census 1's
    # successor); 1.22.0 = term origins (step 2); 1.23.0 = person
    # nodes (step 3); 1.24.0 = part edges (step 4); 1.25.0 = root
    # edges (step 5); 1.26.0 = seat prompts; 1.27.0 = the PBI layer;
    # 1.28.0 = acronym enrichment; 1.29.0 = the Scribe seat prompt
    # (E1, the speech contract); 1.29.1 = prompt 1.1.0 (shape
    # requirement — the v1.0.0 live run broke both bans) + the
    # 'drafted' description status; 1.30.0 = the literal law locks
    # (Closed_Sets sheets, drift text as registry data, the
    # contract-era Speech_Sources rows); 1.31.0 = the derivation
    # ruling (report speech derives from its procs' descriptions);
    # 1.32.0 = THE SHAPE CONTRACT: the Shape_Ledger sheet (battery
    # #13 — Q1/Q2/Q3 as failure gates; the blob corpse's lock);
    # 1.33.0 = the reserved-word renames (Sunny: contains->has_part,
    # by->performed_by, derived_column, pbi_report — GQL needs no
    # backticks); 1.35.0 = M2 scope
    # descriptions STORED (the shape contract lands on scopes);
    # 1.36.0 = joins_to declared (the census blind spot + M2 export); 1.34.0 = round 2 from the OFFICIAL reserved list:
    # schema->db_schema, parameter->param, kg3 text->description;
    # 1.37.0 = THE JOIN-NODE RULING (Sunny 2026-09-10): join label +
    # left_side/right_side in the Shape_Ledger, clauseProvenance
    # retired, joins_to dictionary-only; 1.38.0 = M2 THE JOIN LAYER
    # BUILT: join/left_side/right_side PRESENT, join census rows,
    # reads = the remainder; 1.39.0 = M3 THE CONDITION LAYER:
    # condition/param/resolves_to PRESENT, uses_param, joinType closed
    for reg in metamodel.load_all().values():
        assert reg.ratified is True
        assert reg.version == "1.39.0"


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
