"""Tests for TMDL parser — extracts SQL sources and DAX expressions."""

import pytest

from src.adapters.devops_tmdl import (
    parse_tmdl_partition,
    parse_tmdl_dax,
)


ODBC_TMDL = """table Claims
    lineageTag: abc123

    measure 'CHIP Timely Count' = CALCULATE(DISTINCTCOUNT(Claims[Claim ID]),FILTER(Claims,Claims[CHIP Timely Claim] = 1))
        formatString: 0
        lineageTag: def456

    column 'CHIP Net Pay' = IF('Claims'[Member Group ID] = "1641800011",'Claims'[Total Net Payable],0)
        formatString: $#,0
        lineageTag: ghi789
        summarizeBy: sum

    column 'Claim ID'
        dataType: string
        lineageTag: jkl012
        summarizeBy: none
        sourceColumn: Claim ID

    partition Claims-f29b9baf = m
        mode: import
        source =
                let
                    Source = Odbc.DataSource("dsn=Clarity", [HierarchicalNavigation=true]),
                    CookClarity_Database = Source{[Name="CookClarity",Kind="Database"]}[Data],
                    Reporting_Schema = CookClarity_Database{[Name="Reporting",Kind="Schema"]}[Data],
                    V_CCHP_Executive_Dashboard_Claims_PBI_View = Reporting_Schema{[Name="V_CCHP_Executive_Dashboard_Claims_PBI",Kind="View"]}[Data]
                in
                    V_CCHP_Executive_Dashboard_Claims_PBI_View

    annotation PBI_ResultType = Exception
"""

SQL_DATABASE_TMDL = """table PatientData
    lineageTag: abc123

    column PatientID
        dataType: string
        sourceColumn: PatientID

    partition PatientData-123 = m
        mode: import
        source =
                let
                    Source = Sql.Database("sqlserver.corp.local", "ClarityDB", [Query="EXEC dbo.USP_Patient_Detail_PBI"])
                in
                    Source

    annotation PBI_ResultType = Table
"""

NO_PARTITION_TMDL = """table Measures
    lineageTag: abc123

    measure 'Total Revenue' = SUM(Sales[Amount])
        formatString: $#,0
        lineageTag: def456

    measure 'YTD Revenue' = TOTALYTD([Total Revenue], 'Date'[Date])
        formatString: $#,0
        lineageTag: ghi789
"""


class TestParseTmdlPartition:
    def test_odbc_source(self):
        result = parse_tmdl_partition(ODBC_TMDL, "Claims")
        assert result is not None
        assert result.table_name == "Claims"
        assert result.database == "CookClarity"
        assert result.schema == "Reporting"
        assert result.sql_object == "V_CCHP_Executive_Dashboard_Claims_PBI"
        assert result.sql_object_type == "View"

    def test_sql_database_with_exec(self):
        result = parse_tmdl_partition(SQL_DATABASE_TMDL, "PatientData")
        assert result is not None
        assert result.table_name == "PatientData"
        assert result.server == "sqlserver.corp.local"
        assert result.database == "ClarityDB"
        assert result.sql_object == "USP_Patient_Detail_PBI"
        assert result.sql_object_type == "StoredProcedure"
        assert result.schema == "dbo"

    def test_no_partition_returns_none(self):
        result = parse_tmdl_partition(NO_PARTITION_TMDL, "Measures")
        assert result is None

    def test_dsn_extracted(self):
        result = parse_tmdl_partition(ODBC_TMDL, "Claims")
        assert result.server == "dsn=Clarity"


class TestParseTmdlDax:
    def test_measures_extracted(self):
        exprs = parse_tmdl_dax(ODBC_TMDL, "Claims")
        measures = [e for e in exprs if e.expression_type == "measure"]
        assert len(measures) == 1
        assert measures[0].name == "CHIP Timely Count"
        assert "CALCULATE" in measures[0].expression

    def test_calculated_columns_extracted(self):
        exprs = parse_tmdl_dax(ODBC_TMDL, "Claims")
        calc_cols = [e for e in exprs if e.expression_type == "calculated_column"]
        assert len(calc_cols) == 1
        assert calc_cols[0].name == "CHIP Net Pay"
        assert "IF(" in calc_cols[0].expression

    def test_source_columns_not_included(self):
        exprs = parse_tmdl_dax(ODBC_TMDL, "Claims")
        names = [e.name for e in exprs]
        assert "Claim ID" not in names

    def test_multiple_measures(self):
        exprs = parse_tmdl_dax(NO_PARTITION_TMDL, "Measures")
        measures = [e for e in exprs if e.expression_type == "measure"]
        assert len(measures) == 2
        names = {m.name for m in measures}
        assert names == {"Total Revenue", "YTD Revenue"}

    def test_table_name_set(self):
        exprs = parse_tmdl_dax(ODBC_TMDL, "Claims")
        for expr in exprs:
            assert expr.table_name == "Claims"
