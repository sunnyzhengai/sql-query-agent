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
