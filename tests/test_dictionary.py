"""Tests for case-insensitive dictionary matching (ADR 0016)."""

from src.dictionary import DataDictionary, find_cross_schema_collisions


class TestCaseInsensitiveLookups:
    def test_lookup_folds_case_both_directions(self):
        d = DataDictionary()
        d.add_table("ENCOUNTER", "Patient encounters")
        assert d.get_table_description("encounter") == "Patient encounters"
        assert d.get_table_description("Encounter") == "Patient encounters"

        d.add_table("PatientDim", "Caboodle patient dimension")  # PascalCase source
        assert d.get_table_description("PATIENTDIM") == "Caboodle patient dimension"

    def test_display_case_is_preserved(self):
        d = DataDictionary()
        d.add_table("PatientDim", "Caboodle patient dimension")
        infos = list(d.tables.values())
        assert infos[0].table_name == "PatientDim"

    def test_column_lookup_is_case_insensitive(self):
        d = DataDictionary()
        d.add_column("ENCOUNTER", "ADMIT_DT", "Admission date/time")
        assert d.get_column_description("encounter", "admit_dt") == "Admission date/time"
        assert d.get_columns_for_table("Encounter")[0].column_name == "ADMIT_DT"


class TestCrossSchemaCollisions:
    def test_same_table_name_in_two_schemas_is_flagged(self):
        collisions = find_cross_schema_collisions([
            ("reporting", "Encounter"),
            ("staging", "ENCOUNTER"),
            ("dbo", "PATIENT"),
        ])
        assert collisions == {"ENCOUNTER": ["REPORTING", "STAGING"]}

    def test_unique_names_produce_no_collisions(self):
        assert find_cross_schema_collisions([
            ("dbo", "PATIENT"), ("dbo", "ENCOUNTER"),
        ]) == {}

    def test_same_schema_repeated_is_not_a_collision(self):
        assert find_cross_schema_collisions([
            ("dbo", "PATIENT"), ("DBO", "patient"),
        ]) == {}


class TestPreviewTableReferences:
    def test_harvests_from_and_join_targets(self):
        from src.dictionary import preview_table_references
        refs = preview_table_references([
            "SELECT * FROM dbo.PAT_ENC JOIN [rpt].[ENC_DX] ON 1=1",
            "SELECT 1 FROM #temp",  # temp tables excluded
            "SELECT CASE WHEN a THEN b END FROM Orders",
        ])
        assert refs == {"PAT_ENC", "ENC_DX", "ORDERS"}

    def test_keywords_never_count_as_tables(self):
        from src.dictionary import preview_table_references
        assert preview_table_references(["DELETE FROM WHERE x"]) == set()
