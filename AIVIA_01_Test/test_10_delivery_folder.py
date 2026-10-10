"""THE DELIVERY FOLDER locks (her ruling 2026-10-06: one
catch-all bucket for everything a new customer needs; shape-
matched extraction SQL instead of a smart converter).

RED until AIVIA_01_Delivery/ exists with its allowlist. The
folder's law: everything in it may land on a customer tenant —
so the wheel's hygiene locks extend to it (no brand string, no
census canary, no keys), and the queries' SELECT aliases must
BE the engine's json keys (shape-matched by test, not by hope).
"""

import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERY = REPO_ROOT / "AIVIA_01_Delivery"

CANARY = ("CCMC EMERGENCY", "CCMC IR IMAGING", "CCMC CATH LAB",
          "CCMC MAIN OR", "CCMC SPA OR", "CCMC PHP PSYCHIATRY",
          "CCMC CARDIOVASCULAR OR", "DSC OR")

# the intake sheet's field labels — every value a deployment
# needs, whoever owns it; dropping one from the sheet is a
# refused build (her ruling 2026-10-06: "so we don't miss any
# item, whether it's customer's responsibility or not")
INTAKE_FIELDS = (
    "workspace id", "lakehouse id", "environment item name",
    "provider + model", "key stored as",
    "WRITTEN approval for metadata-only",
    "SQL input folder", "TMDL source",
    "Clarity database name", "who blesses term names",
    "instance base URL", "service account / API token",
    "Business Term DOMAIN id", "Business Term ASSET TYPE id",
    "description ATTRIBUTE TYPE id",
    "technical-definition ATTRIBUTE TYPE id",
    "Power BI report ASSET TYPE id", "SANDBOX/test domain id",
    "RELATION TYPE id", "capacity/run approval",
    "the wall acknowledged", "sandbox-first acknowledged",
)

REQUIRED = (
    "README_prereqs.md",
    "work_wheel_runbook.md",
    "tenant_intake.md",
    "collibra_publish_notebook.md",
    "dictionary_extraction/dict_extract_table.sql",
    "dictionary_extraction/dict_extract_column.sql",
    "dictionary_extraction/dict_extract_join.sql",
    "dictionary_extraction/dict_extract_value.sql",
    "dictionary_extraction/dict_extract_value_generator.sql",
    "tools/csv_to_json.py",  # packed copy; source in AIVIA_01_Code
)

# the engine's json keys per file (from the real 02 jsons,
# embeddings excluded) — each must appear as a SELECT alias
SHAPES = {
    "dict_extract_table.sql": (
        "table_id", "table_name", "table_description",
        "deprecated_yn"),
    "dict_extract_column.sql": (
        "column_id", "table_id", "table_name", "column_name",
        "data_type", "column_description", "deprecated_yn",
        "database_name", "schema_name", "is_primary_key",
        "key_ordinal", "column_ini", "column_item"),
    "dict_extract_join.sql": (
        "join_id", "ordinal", "source_table_id",
        "source_table_name", "source_column_id",
        "source_column_name", "destin_table_id",
        "destin_table_name", "destin_column_id",
        "destin_column_name", "conditional_c", "may_be_stale_c",
        "is_current_data_model_yn", "is_supplemental_yn",
        "destin_in_scope"),
    "dict_extract_value.sql": ("table_name", "code", "meaning"),
}


def test_delivery_folder_structure():
    for rel in REQUIRED:
        assert (DELIVERY / rel).exists(), rel


def test_intake_sheet_carries_every_field():
    text = (DELIVERY / "tenant_intake.md").read_text()
    for field in INTAKE_FIELDS:
        assert field in text, field


def test_publish_notebook_carries_the_laws():
    """AMENDED 2026-10-10 (Brief_Notebook_Import_Law, her rule:
    importable, never copy-paste): the code laws live in the
    versioned .py; the .ipynb twin is GENERATED from it and
    stays in step; the .md keeps the runbook prose."""
    text = (DELIVERY / "collibra_publish_notebook.py").read_text()
    assert "DRY_RUN  = True" in text          # dry-first
    assert "SANDBOX  = True" in text          # sandbox-first
    assert 'bt_name_status") == "blessed"' in text  # blessed-only
    assert "nameMatchMode" in text            # by-name, idempotent
    assert "census" in text                   # the counted census
    for cfg in ("BT_DOMAIN_ID", "BT_TYPE_ID", "DESC_ATTR_ID",
                "TECHDEF_ATTR_ID", "REPORT_TYPE_ID",
                "SANDBOX_DOMAIN", "TOKEN_SECRET"):
        assert cfg in text, cfg               # intake-fed CONFIG
    # the ipynb twin is generated from the .py — never drifts
    import json as _json
    import sys as _sys
    _sys.path.insert(0, str(DELIVERY.parent / "AIVIA_01_Code"))
    from sync_notebook import split_cells
    nb = _json.loads(
        (DELIVERY / "collibra_publish_notebook.ipynb").read_text())
    nb_cells = ["".join(c["source"]).strip()
                for c in nb["cells"]]
    assert nb_cells == split_cells(text)
    # the md is prose only — import steps, no fenced code
    md = (DELIVERY / "collibra_publish_notebook.md").read_text()
    assert "Import notebook" in md
    assert "```" not in md                    # no code to drift


def test_delivery_folder_is_clean():
    """No brand string, no census canary, no key shapes — in
    any file name or any byte of the bucket."""
    for p in DELIVERY.rglob("*"):
        if p.is_dir():
            continue
        assert "aivia" not in p.name.lower(), p
        blob = p.read_bytes()
        assert b"aivia" not in blob.lower(), p
        assert not re.search(rb"sk-[A-Za-z0-9_-]{16,}", blob), p
        for canary in CANARY:
            assert canary.encode() not in blob, (p, canary)


def test_queries_are_shape_matched_and_unscoped():
    for fname, keys in SHAPES.items():
        text = (DELIVERY / "dictionary_extraction" / fname
                ).read_text()
        low = text.lower()
        for k in keys:
            assert f"as {k}" in low, (fname, k)
        # unscoped: the corpus table list must NOT ride
        assert "table_name in (" not in low.replace("  ", " "), \
            fname


def test_pack_items_match_their_sources():
    """The pack-time copies (the gate carve-out keeps sources
    in AIVIA_01_Code): the packed converter must be
    byte-identical to its source — drift refused; the wheel
    folder holds exactly ONE wheel (the one-wheel law at
    rest)."""
    src = REPO_ROOT / "AIVIA_01_Code" / "csv_to_json.py"
    packed = DELIVERY / "tools" / "csv_to_json.py"
    assert src.exists() and packed.exists()
    assert packed.read_bytes() == src.read_bytes()
    wheels = list((DELIVERY / "wheel").glob("*.whl"))
    assert len(wheels) == 1, wheels


def test_csv_to_json_is_a_dumb_faithful_converter(tmp_path):
    # no bytecode in the bucket: a __pycache__ here would trip
    # the clean lock on the NEXT run (it carries the old bytes)
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "csv_to_json", DELIVERY / "tools" / "csv_to_json.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["csv_to_json"] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = False
    src = tmp_path / "dict_extract_value.csv"
    with open(src, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["table_name", "code", "meaning"])
        w.writerow(["ZC_FIX", "7", "Lucky"])
    out = tmp_path / "out"
    written = mod.convert(tmp_path, out)
    assert any("extraction_value.json" in str(p)
               for p in written)
    rows = json.loads(
        (out / "02_emr_data_dictionary_extraction_value.json")
        .read_text())
    assert rows == [{"table_name": "ZC_FIX", "code": "7",
                     "meaning": "Lucky"}]
