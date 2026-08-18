"""semantic_models_step + the consumption layer, end to end (ADR 0040).

Uses recorded TMDL content (same fixtures style as tests/adapters/
test_devops_tmdl.py) through the full chain: TMDL files -> step rows ->
build_graph_step -> export_step. Proves report/measure nodes land, edges
resolve deterministically, ambiguity is skipped not guessed, and the
exports carry the new tables.
"""

from __future__ import annotations

from src.extractor.tmdl_source import TmdlFile
from src.steps.build_graph import build_graph_step
from src.steps.export import export_step
from src.steps.semantic_models import (
    extract_dax_column_refs,
    semantic_models_step,
)

# A semantic model whose partition EXECs a proc in the corpus, with one
# measure referencing a table-qualified column and one calc column.
SEPSIS_TMDL = """table SepsisData
\tmeasure 'Compliance Rate' = DIVIDE(SUM(SepsisData[compliant_count]), COUNTROWS(SepsisData))
\t\tformatString: 0.00%
\t\tlineageTag: aaa-bbb

\tcolumn 'encounter_id'
\t\tdataType: string
\t\tsourceColumn: encounter_id

\tpartition SepsisData-abc123 = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Odbc.Query("dsn=Clarity", "exec [ClarityDB].[reporting].[USP_IP_SepsisDates]")
\t\t\t\tin
\t\t\t\t    Source

\tannotation PBI_ResultType = Table
"""

# A model that EXECs two different procs — no business name derivable.
TWO_SOURCE_TMDL_A = """table TableA
\tpartition TableA-p = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Odbc.Query("dsn=Clarity", "exec [DB].[reporting].[USP_IP_SepsisEncounters]")
\t\t\t\tin
\t\t\t\t    Source
"""
TWO_SOURCE_TMDL_B = """table TableB
\tpartition TableB-p = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Odbc.Query("dsn=Clarity", "exec [DB].[reporting].[USP_IP_SepsisDetails]")
\t\t\t\tin
\t\t\t\t    Source
"""

# DirectLake (pattern 5): reads a warehouse table directly — no M, no EXEC
DIRECTLAKE_TMDL = """table Encounters
\tcolumn 'encounter_id'
\t\tdataType: string
\t\tsourceColumn: encounter_id

\tpartition Encounters = entity
\t\tmode: directLake
\t\tsource
\t\t\tentityName: encounter
\t\t\tschemaName: dbo
\t\t\texpressionSource: DatabaseQuery

\tannotation PBI_ResultType = Table
"""


def _files():
    return [
        TmdlFile("Sepsis Compliance Dashboard", "SepsisData", SEPSIS_TMDL),
        TmdlFile("Sepsis Ops Overview", "TableA", TWO_SOURCE_TMDL_A),
        TmdlFile("Sepsis Ops Overview", "TableB", TWO_SOURCE_TMDL_B),
    ]


def _parse_results():
    # Minimal parse-result rows honoring the 02->03 payload contract
    def row(metric_id, name):
        return {"metric_id": metric_id, "name": name, "ctes_json": "[]",
                "final_select_tables": "[]", "final_select_cte_refs": "[]"}
    return [
        row("reporting.USP_IP_SepsisDates", "USP_IP_SepsisDates"),
        row("reporting.USP_IP_SepsisEncounters", "USP_IP_SepsisEncounters"),
        row("reporting.USP_IP_SepsisDetails", "USP_IP_SepsisDetails"),
    ]


class TestSemanticModelsStep:
    def test_rows_extracted(self):
        out = semantic_models_step(_files(), scan_timestamp="2026-08-16T00:00:00Z")
        assert len(out.report_source_rows) == 3
        assert len(out.dax_rows) == 1
        assert out.dax_rows[0]["name"] == "Compliance Rate"
        assert out.dax_rows[0]["expression_type"] == "measure"

    def test_names_are_proc_keyed_not_report_keyed(self):
        """Inversion (HANDOFF_NAME_DERIVATION_DIRECTION): a proc consumed
        by exactly ONE report inherits that report's title — even when
        the report reads several procs. The old report-keyed rule named
        only single-source reports (228/601 at a live estate)."""
        out = semantic_models_step(_files(), scan_timestamp="t")
        by_id = {r["metric_id"]: r for r in out.metric_name_rows}
        assert by_id["reporting.USP_IP_SepsisDates"]["business_name"] == \
            "Sepsis Compliance Dashboard"
        # BOTH procs of the two-source report now inherit its title
        assert by_id["reporting.USP_IP_SepsisEncounters"]["business_name"] == \
            "Sepsis Ops Overview"
        assert by_id["reporting.USP_IP_SepsisDetails"]["business_name"] == \
            "Sepsis Ops Overview"
        assert out.names_skipped == []
        assert all(r["source"] == "pbi_report" for r in out.metric_name_rows)

    def test_source_column_not_extracted_as_dax(self):
        out = semantic_models_step(_files())
        names = [d["name"] for d in out.dax_rows]
        assert "encounter_id" not in names

    def test_proc_consumed_by_two_different_reports_refuses(self):
        """Refuse-over-guess (amends the 1.16.0 first-workspace verdict,
        per HANDOFF_NAME_DERIVATION_DIRECTION): two DIFFERENT reports
        consuming one proc is genuine ambiguity — list both, name
        nothing, emit a fallout row."""
        files = [
            TmdlFile("Sepsis_Dashboard", "SepsisData", SEPSIS_TMDL),
            TmdlFile("Exec_Overview", "SepsisData", SEPSIS_TMDL),
        ]
        out = semantic_models_step(files)
        assert out.metric_name_rows == []
        assert len(out.names_skipped) == 1
        skip = out.names_skipped[0]
        assert "reporting.USP_IP_SepsisDates" in skip
        assert "Sepsis_Dashboard" in skip and "Exec_Overview" in skip
        fallout = [f for f in out.fallout_rows
                   if f["stage"] == "060_name_derivation"]
        assert len(fallout) == 1
        assert fallout[0]["reason_code"] == "multi_report_consumer"
        assert fallout[0]["entity_id"] == "reporting.USP_IP_SepsisDates"

    def test_same_title_consumers_are_not_ambiguous(self):
        """Every candidate name identical (prod/dev copies of one
        dashboard) — there is nothing to guess, so the name lands and
        all consumers stay listed for steward review."""
        files = [
            TmdlFile("Sepsis Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-prod/m1"),
            TmdlFile("Sepsis Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-dev/m2"),
        ]
        out = semantic_models_step(files)
        assert len(out.metric_name_rows) == 1
        assert out.metric_name_rows[0]["business_name"] == "Sepsis Dashboard"

    def test_case_variant_spellings_count_as_one_proc(self):
        """Amendment 1: the same proc spelled differently across
        partitions (case) must not fake a second consumer/identity."""
        upper = SEPSIS_TMDL.replace(
            "[reporting].[USP_IP_SepsisDates]", "[REPORTING].[USP_IP_SEPSISDATES]")
        files = [
            TmdlFile("Sepsis Compliance Dashboard", "SepsisData", SEPSIS_TMDL),
            TmdlFile("Sepsis Compliance Dashboard", "SepsisData2", upper),
        ]
        out = semantic_models_step(files)
        assert len(out.metric_name_rows) == 1
        assert out.names_skipped == []

    def test_corpus_membership_replaces_kind_filter(self):
        """Amendment 2: connectors reach VIEWS as Kind='Table' — trust
        corpus membership, not the TMDL Kind. A source matching a corpus
        metric_id can name it; casing comes from the corpus."""
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)],
            corpus_metric_ids={"DBO.Encounter"},
        )
        assert len(out.metric_name_rows) == 1
        row = out.metric_name_rows[0]
        assert row["metric_id"] == "DBO.Encounter"  # corpus casing wins
        assert row["business_name"] == "Encounter Explorer"

    def test_non_corpus_sources_never_name(self):
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)],
            corpus_metric_ids={"reporting.USP_Something_Else"},
        )
        assert out.metric_name_rows == []


class TestFalloutRows:
    """HANDOFF_FUNNEL_AND_FALLOUT: every dropped entity leaves a row."""

    NON_SQL_TMDL = """table Params
\tpartition Params = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = Table.FromRows({{"a", 1}}, {"Name", "Value"})
\t\t\t\tin
\t\t\t\t    Source
"""

    def test_parse_miss_writes_classified_fallout_row(self):
        out = semantic_models_step(
            [TmdlFile("Config Report", "Params", self.NON_SQL_TMDL)]
        )
        assert out.report_source_rows == []
        assert len(out.fallout_rows) == 1
        f = out.fallout_rows[0]
        assert f["stage"] == "060_partition_parse"
        assert f["entity_id"] == "Config Report/Params"
        assert f["reason_code"] == "non_sql_source:Table.FromRows"
        assert f["contract_id"] == "contract:input_report_sources"

    def test_parsed_files_leave_no_fallout(self):
        out = semantic_models_step(_files())
        assert [f for f in out.fallout_rows
                if f["stage"] == "060_partition_parse"] == []

    def test_every_file_yields_source_or_fallout(self):
        """The 174-silent-models rule: sources + partition fallout rows
        account for every collected file, always."""
        files = _files() + [TmdlFile("Config Report", "Params", self.NON_SQL_TMDL)]
        out = semantic_models_step(files)
        partition_fallout = [f for f in out.fallout_rows
                             if f["stage"] == "060_partition_parse"]
        assert len(out.report_source_rows) + len(partition_fallout) == len(files)


class TestDaxColumnRefs:
    def test_qualified_refs_extracted(self):
        refs = extract_dax_column_refs(
            "DIVIDE(SUM(SepsisData[compliant_count]), SUM('Other Table'[total]))"
        )
        assert ("SepsisData", "compliant_count") in refs
        assert ("Other Table", "total") in refs

    def test_bare_measure_ref_not_extracted(self):
        # [Total Sales] alone is ambiguous (measure or same-table column)
        assert extract_dax_column_refs("[Total Sales] * 2") == []


class TestConsumptionLayerEndToEnd:
    def _build(self):
        out = semantic_models_step(_files(), scan_timestamp="t")
        return build_graph_step(
            _parse_results(), [], [],
            metric_name_records=out.metric_name_rows,
            report_source_records=out.report_source_rows,
            dax_records=out.dax_rows,
        )

    def test_report_and_measure_nodes_land(self):
        graph = self._build()
        assert graph.reports_added == 2
        assert graph.measures_added == 1
        layers = {r["layer"] for r in graph.nodes_rows}
        assert "report" in layers and "measure" in layers

    def test_report_to_canonical_edges_resolve(self):
        graph = self._build()
        r2c = [e for e in graph.edges_rows if e["edge_type"] == "report_to_canonical"]
        # dashboard -> SepsisDates; overview -> Encounters AND Details
        assert len(r2c) == 3
        targets = {e["target_id"] for e in r2c}
        assert "canonical:reporting.USP_IP_SepsisDates" in targets

    def test_business_name_applied_via_lineage(self):
        graph = self._build()
        # proc-keyed inversion: all three procs carry a report title
        assert graph.business_names_applied == 3

    def test_exports_carry_consumption_tables(self):
        graph = self._build()
        exported = export_step(graph.nodes_rows, graph.edges_rows)
        assert len(exported["graph_report"]) == 2
        assert len(exported["graph_measure"]) == 1
        assert len(exported["graph_edge_report2canonical"]) == 3
        assert len(exported["graph_edge_report2measure"]) == 1


class TestDirectLake:
    """Pattern 5 (ADR 0040): the Fabric-native default partition mode."""

    def test_directlake_partition_parsed(self):
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)]
        )
        assert len(out.report_source_rows) == 1
        row = out.report_source_rows[0]
        assert row["sql_object"] == "encounter"
        assert row["schema_name"] == "dbo"
        assert row["sql_object_type"] == "Table"

    def test_directlake_source_never_names_a_metric(self):
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)]
        )
        assert out.metric_name_rows == []

    def test_directlake_report_attaches_to_technical_table(self):
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)]
        )
        graph = build_graph_step(
            _parse_results(),
            [{"TABLE_NAME": "encounter", "DESCRIPTION": "Encounters"}], [],
            report_source_records=out.report_source_rows,
        )
        r2t = [e for e in graph.edges_rows if e["edge_type"] == "report_to_technical"]
        assert len(r2t) == 1
        assert r2t[0]["target_id"] == "tech:DBO.ENCOUNTER"
        exported = export_step(graph.nodes_rows, graph.edges_rows)
        assert len(exported["graph_edge_report2technical"]) == 1

    def test_directlake_table_missing_from_dictionary_is_skipped(self):
        out = semantic_models_step(
            [TmdlFile("Encounter Explorer", "Encounters", DIRECTLAKE_TMDL)]
        )
        graph = build_graph_step(
            _parse_results(), [], [],
            report_source_records=out.report_source_rows,
        )
        assert any("not in the dictionary" in s for s in graph.consumption_skipped)


class TestCrossWorkspaceNamingPriority:
    """AMENDED 2026-08-18 (HANDOFF_NAME_DERIVATION_DIRECTION supersedes
    the 1.16.0 first-workspace verdict): differently-titled reports
    consuming one metric REFUSE — refuse-over-guess. Only same-title
    consumers (true workspace copies) still name it."""

    def test_differently_titled_workspace_reports_refuse(self):
        files = [
            TmdlFile("Prod Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-prod/m1"),
            TmdlFile("Dev Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-dev/m2"),
        ]
        out = semantic_models_step(files)
        assert out.metric_name_rows == []
        assert len(out.names_skipped) == 1
        assert "Prod Dashboard" in out.names_skipped[0]
        assert "Dev Dashboard" in out.names_skipped[0]


def test_unrecognized_shape_fallout_carries_signature():
    """SHAPE_CENSUS x FUNNEL: the unknown-shape fallout row carries the
    whitelist-anonymized signature — support sees the shape, never the
    customer's M."""
    weird = """table Blend
\tpartition Blend = m
\t\tmode: import
\t\tsource =
\t\t\t\tlet
\t\t\t\t    Source = SecretCustomFn("x", SecretParam)
\t\t\t\tin
\t\t\t\t    Source
"""
    out = semantic_models_step([TmdlFile("R", "Blend", weird)])
    f = out.fallout_rows[0]
    assert f["reason_code"] == "unrecognized_shape"
    assert "[signature:" in f["reason_text"]
    assert "SecretCustomFn" not in f["reason_text"]
    assert "SecretParam" not in f["reason_text"]
