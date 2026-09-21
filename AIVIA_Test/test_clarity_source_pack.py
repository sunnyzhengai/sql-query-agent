"""Brief_Clarity_Source_Pack (Sunny, 2026-09-19: "we need contracts
for these tables. because every hospital customer who uses epic
would use the exact same scripts" -> "please solidify these queries
in the contract"): THE PACK-TO-INTAKE PIN. Every shipped pack
script must (a) parse under the SAME ScriptDom the engine ships and
(b) emit EXACTLY the intake contract's headers, in order — the pack
is proven by the parser, Epic-free, on every commit. Plus the
placeholder law's tripwire: 04_joins ships as the catalog interim
until his findings row names Epic's joins dictionary; the script's
marker and the contract's F-CP1 OPEN row flip in the same act.

Proves: contract:aisql-design-to-code
"""
import pathlib
import re

import pytest

from aisql.graph.kg2_mapper.scriptdom_loader import ScriptDomUnavailable, parse_tsql

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK = ROOT / "AIVIA_Product" / "source_packs" / "clarity"
CONTRACT = ROOT / "AIVIA_Design" / "Contract_Source_Packs.md"

# The intake contract's headers (kg1_intake REQUIRED_FILES shapes),
# one row per pack script — the contract this module enforces.
HEADERS = {
    "01_tables.sql": ["schema", "table", "description"],
    "02_columns.sql": ["schema", "table", "column", "description",
                       "data_type"],
    "03_pk.sql": ["schema", "table", "column", "ordinal"],
    "04_joins.sql": ["fk_num", "ordinal", "src_schema", "src_table",
                     "src_column", "dest_schema", "dest_table",
                     "dest_column"],
    "05_values.sql": ["table", "code", "meaning"],
    "06_manifest.sql": ["db_name", "server", "as_of"],
}
ALIAS = re.compile(r"AS \[(\w+)\]", re.I)


@pytest.mark.parametrize("name", sorted(HEADERS))
def test_script_parses_and_aliases_match_the_intake_contract(name):
    sql = (PACK / name).read_text()
    try:
        _, errors = parse_tsql(sql)
    except ScriptDomUnavailable:
        pytest.skip("ScriptDom unavailable in this interpreter")
    assert not errors, f"{name} does not parse: {errors[:3]}"
    assert ALIAS.findall(sql) == HEADERS[name], (
        f"{name}: aliases drifted from the intake contract")


def test_every_clarity_tbl_touch_carries_the_dedupe_law():
    """Sunny's field ruling (2026-09-19): CLARITY_TBL carries
    duplicate rows per table; the descriptor-override IS NOT NULL
    filter is the dedupe — REQUIRED at every CLARITY_TBL touch or
    every downstream file doubles."""
    for name in ("01_tables.sql", "02_columns.sql", "03_pk.sql",
                 "04_joins.sql"):
        sql = (PACK / name).read_text().upper()
        bare = sql.replace("CLARITY_TBL_PK", "").replace(
            "CLARITY_TBL_FK", "")
        if "CLARITY_TBL" not in bare:
            continue
        assert "TBL_DESCRIPTOR_OVR IS NOT NULL" in sql, (
            f"{name} touches CLARITY_TBL without the dedupe filter")


def test_placeholder_04_is_tripwired():
    """THE PLACEHOLDER LAW: the marker in 04_joins.sql and the
    contract's F-CP1 OPEN row flip TOGETHER — landing the real
    joins-dictionary query without closing F-CP1 (or vice versa)
    fails here."""
    marker = "PLACEHOLDER-04" in (PACK / "04_joins.sql").read_text()
    f_cp1_open = bool(re.search(r"F-CP1.*\bOPEN\b",
                                CONTRACT.read_text()))
    assert marker == f_cp1_open, (
        "04_joins.sql's PLACEHOLDER-04 marker and Contract_Source_"
        "Packs.md's F-CP1 OPEN row must flip in the same act")


# ---- clarity-pack-1.2 (Brief_Pilot_Build_2, ruling (6) "i agree
# with option a"): the naming-conventions table lives IN the pack.
# RED before the pack bump. ----

def test_pack_version_is_1_2_everywhere():
    for name in list(HEADERS) + ["06_manifest.sql", "README.md"]:
        text = (PACK / name).read_text(encoding="utf-8")
        assert "clarity-pack-1.2" in text, name
        assert "clarity-pack-1.1" not in text, name


def test_pack_json_carries_the_naming_conventions():
    import json
    facts = json.loads((PACK / "pack.json").read_text(encoding="utf-8"))
    conv = facts.get("naming_conventions")
    assert isinstance(conv, list) and conv, "naming_conventions missing"
    suffixes = {c["suffix"] for c in conv}
    assert {"_C", "_YN", "_DTTM", "_DATE_REAL"} <= suffixes
    for c in conv:
        assert c.get("suffix") and c.get("rule"), c
