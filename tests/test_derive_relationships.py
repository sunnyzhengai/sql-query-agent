"""dict_relationships derivation (ADR 0046 join map) — NATIVE parser.

Provenance is the point under test: every relationship row must be
deducible from our own de-dialected corpus — base tables only, no
temp/CTE names — and the committed CSV must match a fresh derivation
(no hand edits, no drift). Statement splitting and alias resolution
come from ScriptDom (native-parser law, ADR 0001); the sqlglot
bootstrap's blind spot (192 unevidenced JOINs) is structurally gone.
"""

import csv
from collections import Counter
from pathlib import Path

from scripts.derive_dict_relationships import alias_map, join_pairs
from src.tree.extract import statement_texts

REPO = Path(__file__).parent.parent
CSV_PATH = REPO / "data" / "synthetic" / "dict_relationships.csv"
SQL_DIR = REPO / "data" / "synthetic" / "sql"
DICT_TABLES = REPO / "data" / "synthetic" / "dict_tables.csv"


class TestNativeParserLawHolds:
    def test_deriver_is_sqlglot_free(self):
        source = (REPO / "scripts" / "derive_dict_relationships.py").read_text()
        assert "sqlglot" not in source.replace(
            "sqlglot banned", "").replace("sqlglot bootstrap", ""), \
            "the join-map deriver must use the native parser only"


class TestUnits:
    def test_bracketed_aliases_resolve_and_temp_keeps_marker(self):
        sql = ('SELECT 1 FROM [dbo].[HOSPITAL_ENCOUNTERS] HE '
               'INNER JOIN #Base_Pop AS [BP] '
               'ON [BP].ENCOUNTER_ID = HE.ENCOUNTER_ID')
        m = alias_map(sql)
        assert m.get("HE") == "HOSPITAL_ENCOUNTERS"
        assert m.get("BP") == "#BASE_POP", \
            "ScriptDom keeps the temp marker — a temp must never masquerade as a base table"

    def test_join_pair_is_canonicalized_and_resolved(self):
        sql = ("SELECT 1 FROM dbo.PATIENTS PAT "
               "INNER JOIN dbo.HOSPITAL_ENCOUNTERS HE "
               "ON PAT.PATIENT_ID = HE.PATIENT_ID")
        pairs = [(a, b) for a, b, r in join_pairs(sql) if r is None]
        assert pairs == [(("HOSPITAL_ENCOUNTERS", "PATIENT_ID"),
                          ("PATIENTS", "PATIENT_ID"))]

    def test_temp_side_and_same_table_are_counted_not_paired(self):
        sql = ("SELECT 1 FROM #Base_Pop BP "
               "INNER JOIN dbo.HOSPITAL_ENCOUNTERS HE "
               "ON BP.ENCOUNTER_ID = HE.ENCOUNTER_ID "
               "WHERE HE.IN_DTTM = HE.OUT_DTTM")
        reasons = [r for _, _, r in join_pairs(sql) if r]
        assert "temp_side" in reasons
        assert "self_join_or_same_table" in reasons
        assert not [1 for _, _, r in join_pairs(sql) if r is None]

    def test_cte_statement_joins_are_evidenced(self):
        # The sqlglot bootstrap's blind spot class — must contribute now.
        sql = ("WITH abx AS (SELECT m.MEDICATION_ID FROM dbo.MEDICATIONS m "
               "INNER JOIN dbo.GROUPER_MED_RECORDS g "
               "ON g.EXP_MEDS_LIST_ID = m.MEDICATION_ID) "
               "SELECT * INTO #abx FROM abx")
        pairs = [(a, b) for a, b, r in join_pairs(sql) if r is None]
        assert (("GROUPER_MED_RECORDS", "EXP_MEDS_LIST_ID"),
                ("MEDICATIONS", "MEDICATION_ID")) in pairs


class TestCommittedFileIsDerived:
    def _derive(self):
        base = {row["TABLE_NAME"].upper()
                for row in csv.DictReader(open(DICT_TABLES))}
        counts = Counter()
        for path in sorted(SQL_DIR.rglob("*.sql")):
            for stmt in statement_texts(path.read_text(encoding="utf-8-sig")):
                for a, b, reason in join_pairs(stmt):
                    if reason is None and a[0] in base and b[0] in base:
                        counts[(a, b)] += 1
        return counts

    def test_csv_matches_fresh_derivation(self):
        derived = self._derive()
        committed = {
            ((r["SOURCE_TABLE"], r["SOURCE_COLUMN"]),
             (r["DEST_TABLE"], r["DEST_COLUMN"])): int(r["EVIDENCE_COUNT"])
            for r in csv.DictReader(open(CSV_PATH))
        }
        assert committed == dict(derived), (
            "dict_relationships.csv drifted from the corpus — rerun "
            "scripts/derive_dict_relationships.py"
        )

    def test_every_row_is_base_table_evidence(self):
        base = {row["TABLE_NAME"].upper()
                for row in csv.DictReader(open(DICT_TABLES))}
        rows = list(csv.DictReader(open(CSV_PATH)))
        assert len(rows) > 40, "join map shrank unexpectedly"
        for r in rows:
            assert r["SOURCE_TABLE"] in base and r["DEST_TABLE"] in base
            assert not r["SOURCE_TABLE"].startswith("#")
            assert "/*" not in r["SOURCE_COLUMN"] + r["DEST_COLUMN"], \
                "comment leakage in a column name (the sqlglot-era corruption)"
            assert r["EVIDENCE"] == "corpus"
            assert int(r["EVIDENCE_COUNT"]) >= 1
