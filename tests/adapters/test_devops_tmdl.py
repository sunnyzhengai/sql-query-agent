"""Tests for TMDL parser — extracts SQL sources and DAX expressions."""


from src.extractor.devops_tmdl import (
    parse_tmdl_dax,
    parse_tmdl_partition,
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
                    ClarityDB_Database = Source{[Name="ClarityDB",Kind="Database"]}[Data],
                    Reporting_Schema = ClarityDB_Database{[Name="Reporting",Kind="Schema"]}[Data],
                    V_ACME_Executive_Dashboard_Claims_PBI_View = Reporting_Schema{[Name="V_ACME_Executive_Dashboard_Claims_PBI",Kind="View"]}[Data]
                in
                    V_ACME_Executive_Dashboard_Claims_PBI_View

    annotation PBI_ResultType = Exception
"""

ODBC_QUERY_TMDL = """table Anesthesia
    lineageTag: abc123

    column SurgeonName
        dataType: string
        sourceColumn: SurgeonName

    partition Anesthesia-566cedeb = m
        mode: import
        source =
                let
                    Source = Odbc.Query("dsn=Clarity", "exec [ClarityDB].[RPT].[USP_ACME_ANESTHESIA_STAFFING_PBI]")
                in
                    Source

    annotation PBI_ResultType = Table
"""

ODBC_QUERY_LF_TMDL = """table EmployeeInfo
    lineageTag: abc123

    partition 'Employee Info-0f78c2fc' = m
        mode: import
        source =
                let
                    Source = Odbc.Query("dsn=HrDb", "exec hrdb.rpt.usp_employee_info#(lf)")
                in
                    Source

    annotation PBI_ResultType = Table
"""

SQL_DATABASE_VAR_TMDL = """table AdmitDischarge
    lineageTag: abc123

    partition AdmitDischarge = m
        mode: import
        source =
                let
                    Source = Sql.Database(WarehouseServer, "WarehouseDW", [Query="SET NOCOUNT ON;#(lf)EXEC dbo.USP_AdmitDischarge_PBI"])
                in
                    Source

    annotation PBI_ResultType = Table
"""

SQL_INLINE_TMDL = """table Membership
    lineageTag: abc123

    partition Membership = m
        mode: import
        source =
                let
                    Source = Sql.Database(WarehouseServer, "warehousedw", [Query="SELECT DISTINCT MemberNo, MemberName FROM Members"])
                in
                    Source

    annotation PBI_ResultType = Table
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
        assert result.database == "ClarityDB"
        assert result.schema == "Reporting"
        assert result.sql_object == "V_ACME_Executive_Dashboard_Claims_PBI"
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

    def test_odbc_query_with_exec(self):
        result = parse_tmdl_partition(ODBC_QUERY_TMDL, "Anesthesia")
        assert result is not None
        assert result.table_name == "Anesthesia"
        assert result.database == "ClarityDB"
        assert result.schema == "RPT"
        assert result.sql_object == "USP_ACME_ANESTHESIA_STAFFING_PBI"
        assert result.sql_object_type == "StoredProcedure"
        assert result.server == "dsn=Clarity"

    def test_odbc_query_with_lf_escape(self):
        result = parse_tmdl_partition(ODBC_QUERY_LF_TMDL, "EmployeeInfo")
        assert result is not None
        assert result.sql_object == "usp_employee_info"
        assert result.schema == "rpt"
        assert result.database == "hrdb"
        assert result.sql_object_type == "StoredProcedure"

    def test_sql_database_variable_server(self):
        result = parse_tmdl_partition(SQL_DATABASE_VAR_TMDL, "AdmitDischarge")
        assert result is not None
        assert result.server == "WarehouseServer"
        assert result.database == "WarehouseDW"
        assert result.sql_object == "USP_AdmitDischarge_PBI"
        assert result.sql_object_type == "StoredProcedure"
        assert result.schema == "dbo"

    def test_inline_sql_marked(self):
        result = parse_tmdl_partition(SQL_INLINE_TMDL, "Membership")
        assert result is not None
        assert result.sql_object == "InlineQuery"
        assert result.sql_object_type == "InlineSQL"
        assert result.database == "warehousedw"


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


# --- Field pattern-breakers (HANDOFF_TMDL_PATTERN_GAPS, 2026-08-18) ---
# One live sample carried all three: parameter as server argument,
# bracketed EXEC identifiers, string-concatenated Query. 277 SQL-shaped
# sources were missed on a real estate; these fixtures mirror the shapes.

SQL_DB_PARAM_CONCAT_TMDL = """table SepsisTrend
    partition SepsisTrend = m
        mode: import
        source =
                let
                    Source = Sql.Database(@ServerParam, "AnalyticsDb",
                        [Query="exec [SCHEMA_X].USP_Sepsis_Trend '"& StartDate &"' , '"& EndDate &"' "])
                in
                    Source

    annotation PBI_ResultType = Table
"""

SQL_DB_QUOTED_PARAM_TMDL = """table Census
    partition Census = m
        mode: import
        source =
                let
                    Source = Sql.Database(#"Server Param", "AnalyticsDb", [Query="EXEC rpt.USP_Census_PBI"])
                in
                    Source
"""

SQL_DB_THREE_PART_EXEC_TMDL = """table Falls
    partition Falls = m
        mode: import
        source =
                let
                    Source = Sql.Database("srv.example.corp", "AnalyticsDb", [Query="EXEC [AnalyticsDb].[rpt].[USP_Falls_PBI]"])
                in
                    Source
"""

SQL_DB_QUERY_AFTER_OPTION_TMDL = """table Meds
    partition Meds = m
        mode: import
        source =
                let
                    Source = Sql.Database("srv.example.corp", "AnalyticsDb", [CommandTimeout=#duration(0,0,30,0), Query="EXEC rpt.USP_Meds_PBI"])
                in
                    Source
"""

ODBC_QUERY_PARAM_DSN_TMDL = """table FluVax
    partition FluVax = m
        mode: import
        source =
                let
                    Source = Odbc.Query(DsnParam, "exec rpt.USP_Flu_Vaccinations_PBI")
                in
                    Source
"""

ODBC_QUERY_CONCAT_TMDL = """table Readmits
    partition Readmits = m
        mode: import
        source =
                let
                    Source = Odbc.Query("dsn=Analytics", "exec [rpt].[USP_Readmit_Rate] '"& RunDate &"' ")
                in
                    Source
"""


class TestPatternBreakers:
    """The three field variants, for Sql.Database AND Odbc.Query."""

    def test_param_server_bracket_concat_all_at_once(self):
        # the live sample: all three breakers in one partition
        result = parse_tmdl_partition(SQL_DB_PARAM_CONCAT_TMDL, "SepsisTrend")
        assert result is not None
        assert result.server == "ServerParam"
        assert result.database == "AnalyticsDb"
        assert result.schema == "SCHEMA_X"
        assert result.sql_object == "USP_Sepsis_Trend"
        assert result.sql_object_type == "StoredProcedure"

    def test_quoted_identifier_server(self):
        result = parse_tmdl_partition(SQL_DB_QUOTED_PARAM_TMDL, "Census")
        assert result is not None
        assert result.server == "Server Param"
        assert result.sql_object == "USP_Census_PBI"

    def test_three_part_bracketed_exec_in_query(self):
        result = parse_tmdl_partition(SQL_DB_THREE_PART_EXEC_TMDL, "Falls")
        assert result is not None
        assert result.database == "AnalyticsDb"
        assert result.schema == "rpt"
        assert result.sql_object == "USP_Falls_PBI"

    def test_query_field_not_first_in_record(self):
        result = parse_tmdl_partition(SQL_DB_QUERY_AFTER_OPTION_TMDL, "Meds")
        assert result is not None
        assert result.sql_object == "USP_Meds_PBI"

    def test_odbc_query_parameter_dsn(self):
        result = parse_tmdl_partition(ODBC_QUERY_PARAM_DSN_TMDL, "FluVax")
        assert result is not None
        assert result.server == "DsnParam"
        assert result.schema == "rpt"
        assert result.sql_object == "USP_Flu_Vaccinations_PBI"

    def test_odbc_query_concatenated_query_string(self):
        result = parse_tmdl_partition(ODBC_QUERY_CONCAT_TMDL, "Readmits")
        assert result is not None
        assert result.schema == "rpt"
        assert result.sql_object == "USP_Readmit_Rate"
        assert result.sql_object_type == "StoredProcedure"


# --- Fallout classification (HANDOFF_TMDL_PATTERN_GAPS item 2) ---

CALCULATED_TMDL = """table DateDim
    partition DateDim = calculated
        mode: import
        source = CALENDAR(DATE(2020,1,1), DATE(2030,12,31))
"""

TABLE_FROMROWS_TMDL = """table Params
    partition Params = m
        mode: import
        source =
                let
                    Source = Table.FromRows({{"a", 1}}, {"Name", "Value"})
                in
                    Source
"""

SNOWFLAKE_TMDL = """table Fin
    partition Fin = m
        mode: import
        source =
                let
                    Source = Snowflake.Databases("acct.snowflakecomputing.com", "WH")
                in
                    Source
"""

CUSTOM_REF_TMDL = """table Blended
    partition Blended = m
        mode: import
        source =
                let
                    Source = SomeSharedQuery
                in
                    Source
"""


class TestFalloutClassification:
    def _cls(self, content, table):
        from src.extractor.devops_tmdl import classify_partition_fallout
        return classify_partition_fallout(content, table)

    def test_calculated_table(self):
        code, text = self._cls(CALCULATED_TMDL, "DateDim")
        assert code == "calculated_table"

    def test_non_sql_source_names_the_function(self):
        code, _ = self._cls(TABLE_FROMROWS_TMDL, "Params")
        assert code == "non_sql_source:Table.FromRows"

    def test_snowflake_is_recognized_not_unknown(self):
        code, _ = self._cls(SNOWFLAKE_TMDL, "Fin")
        assert code == "non_sql_source:Snowflake.Databases"

    def test_measures_only_file_is_no_partition(self):
        code, _ = self._cls(NO_PARTITION_TMDL, "Measures")
        assert code == "no_partition"

    def test_unrecognized_shape_is_the_residue_class(self):
        code, _ = self._cls(CUSTOM_REF_TMDL, "Blended")
        assert code == "unrecognized_shape"

    def test_every_parse_miss_classifies(self):
        # total classification: anything parse_tmdl_partition returns
        # None for must yield a reason (the 174-silent-models rule)
        for content, table in [
            (CALCULATED_TMDL, "DateDim"), (TABLE_FROMROWS_TMDL, "Params"),
            (SNOWFLAKE_TMDL, "Fin"), (NO_PARTITION_TMDL, "Measures"),
            (CUSTOM_REF_TMDL, "Blended"),
        ]:
            assert parse_tmdl_partition(content, table) is None
            code, text = self._cls(content, table)
            assert code and text


SQL_DB_SCHEMA_ITEM_NAV_TMDL = """table Falls
    partition Falls = m
        mode: import
        source =
                let
                    Source = Sql.Database("srv.example.corp", "AnalyticsDb"),
                    T = Source{[Schema="rpt",Item="V_Falls_PBI"]}[Data]
                in
                    T
"""


class TestSchemaItemNavigation:
    def test_schema_item_navigator_extracted(self):
        result = parse_tmdl_partition(SQL_DB_SCHEMA_ITEM_NAV_TMDL, "Falls")
        assert result is not None
        assert result.schema == "rpt"
        assert result.sql_object == "V_Falls_PBI"
        assert result.database == "AnalyticsDb"
        # Kind unstated in this form — membership decides downstream
        assert result.sql_object_type == "Table"
