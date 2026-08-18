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
\t\t\t\t    Source = Odbc.Query("dsn=Clarity", "exec [CookClarity].[reporting].[USP_IP_SepsisDates]")
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

    def test_business_name_derived_only_for_single_source_reports(self):
        out = semantic_models_step(_files(), scan_timestamp="t")
        assert len(out.metric_name_rows) == 1
        row = out.metric_name_rows[0]
        assert row["metric_id"] == "reporting.USP_IP_SepsisDates"
        assert row["business_name"] == "Sepsis Compliance Dashboard"
        assert row["source"] == "pbi_report"
        # the two-source report is skipped with a reason, never guessed
        assert len(out.names_skipped) == 1
        assert "Sepsis Ops Overview" in out.names_skipped[0]

    def test_source_column_not_extracted_as_dax(self):
        out = semantic_models_step(_files())
        names = [d["name"] for d in out.dax_rows]
        assert "encounter_id" not in names

    def test_two_reports_same_metric_emit_one_row(self):
        """input_metric_names has a unique metric_id invariant: a metric
        fed by two reports gets ONE row — first report names it, the
        rest are listed for steward review, never guessed."""
        files = [
            TmdlFile("Sepsis_Dashboard", "SepsisData", SEPSIS_TMDL),
            TmdlFile("Exec_Overview", "SepsisData", SEPSIS_TMDL),
        ]
        out = semantic_models_step(files)
        assert len(out.metric_name_rows) == 1
        row = out.metric_name_rows[0]
        assert row["metric_id"] == "reporting.USP_IP_SepsisDates"
        assert row["business_name"] == "Sepsis Dashboard"  # friendly-cased
        assert row["report_name"] == "Sepsis_Dashboard; Exec_Overview"


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
        assert graph.business_names_applied == 1

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
    """Multi-workspace rule (2026-08-18): the FIRST report in workspace
    order names a shared metric; the rest are listed, never deduped."""

    def test_first_workspace_report_names_shared_metric(self):
        files = [
            TmdlFile("Prod Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-prod/m1"),
            TmdlFile("Dev Dashboard", "SepsisData", SEPSIS_TMDL,
                     semantic_model_path="workspace:ws-dev/m2"),
        ]
        out = semantic_models_step(files)
        assert len(out.metric_name_rows) == 1
        row = out.metric_name_rows[0]
        assert row["business_name"] == "Prod Dashboard"
        assert row["report_name"] == "Prod Dashboard; Dev Dashboard"
