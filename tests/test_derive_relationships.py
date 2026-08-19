"""dict_relationships derivation (ADR 0046 join map, corpus-evidence).

Provenance is the point under test: every relationship row must be
deducible from our own de-dialected corpus — base tables only, no
temp/CTE names, no phantom quoted identifiers — and the committed CSV
must match a fresh derivation (no hand edits, no drift)."""

import csv
from collections import Counter
from pathlib import Path

from scripts.derive_dict_relationships import (
    alias_map,
    join_pairs,
    split_statements,
)

REPO = Path(__file__).parent.parent

CSV_PATH = REPO / "data" / "synthetic" / "dict_relationships.csv"
SQL_DIR = REPO / "data" / "synthetic" / "sql"
DICT_TABLES = REPO / "data" / "synthetic" / "dict_tables.csv"


class TestUnits:
    def test_statement_heads_inside_parens_do_not_split(self):
        sql = ("SELECT a,\nSTUFF((\nSELECT b FROM t2\nWHERE t2.id = t.id\n"
               "FOR XML PATH('')\n), 1, 1, '')\nINTO #x\nFROM t\n"
               "SELECT * FROM #x")
        stmts = split_statements(sql)
        assert len(stmts) == 2, "inner SELECT at depth>0 must not split"

    def test_bracketed_aliases_resolve_without_phantom_quotes(self):
        sql = ('SELECT 1 FROM [dbo].[HOSPITAL_ENCOUNTERS] HE '
               'INNER JOIN dbo.PATIENTS AS [PAT] '
               'ON [PAT].PATIENT_ID = HE.PATIENT_ID')
        m = alias_map(sql)
        assert m.get("PAT") == "PATIENTS"
        assert m.get("HE") == "HOSPITAL_ENCOUNTERS"
        assert not any('"' in k or "[" in k for k in m), m

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


class TestCommittedFileIsDerived:
    def _derive(self):
        base = {row["TABLE_NAME"].upper()
                for row in csv.DictReader(open(DICT_TABLES))}
        counts = Counter()
        for path in sorted(SQL_DIR.rglob("*.sql")):
            for stmt in split_statements(path.read_text(encoding="utf-8-sig")):
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
            assert '"' not in r["SOURCE_COLUMN"] + r["DEST_COLUMN"]
            assert r["EVIDENCE"] == "corpus"
            assert int(r["EVIDENCE_COUNT"]) >= 1
