"""M mini-parser + shape census (HANDOFF_SHAPE_CENSUS).

Three mechanical guarantees:
1. Every `supported` registry shape has a fixture that classifies to it
   AND yields a source through parse_tmdl_partition (a supported claim
   without a passing fixture fails CI).
2. Signatures carry argument KINDS (parameter vs literal vs concat) —
   the field-proven discriminator.
3. The leak test: no customer identifier can appear in an emitted
   signature (whitelist anonymization, amendment 2).
"""

from __future__ import annotations

from src.extractor.devops_tmdl import parse_tmdl_partition
from src.mquery.census import census_file, census_files, coverage_lines
from src.mquery.parser import Call, Let, Lit, Opaque, Rec, Ref, parse_m
from src.mquery.registry import SHAPE_REGISTRY, classify_shape
from src.mquery.signature import partition_shape


def _tmdl(m_body: str, table: str = "T") -> str:
    indented = "\n".join("\t\t\t\t" + line for line in m_body.splitlines())
    return (f"table {table}\n\tpartition {table} = m\n\t\tmode: import\n"
            f"\t\tsource =\n{indented}\n\n\tannotation PBI_ResultType = Table\n")


# --- fixtures: one per supported shape, field-realistic -------------

FIXTURES = {
    "odbc_datasource_navigation": _tmdl(
        'let\n'
        '    Source = Odbc.DataSource("dsn=Analytics", [HierarchicalNavigation=true]),\n'
        '    DB = Source{[Name="AnalyticsDb",Kind="Database"]}[Data],\n'
        '    Sch = DB{[Name="rpt",Kind="Schema"]}[Data],\n'
        '    V = Sch{[Name="V_Sepsis_Screening_PBI",Kind="View"]}[Data]\n'
        'in\n'
        '    V'
    ),
    "odbc_query": _tmdl(
        'let\n'
        '    Source = Odbc.Query(DsnParam, "exec [rpt].[USP_Readmit_Rate] \'"& RunDate &"\' ")\n'
        'in\n'
        '    Source'
    ),
    "sql_database_query": _tmdl(
        'let\n'
        '    Source = Sql.Database(@ServerParam, "AnalyticsDb",\n'
        '        [Query="exec [SCHEMA_X].USP_Sepsis_Trend \'"& StartDate &"\' , \'"& EndDate &"\' "])\n'
        'in\n'
        '    Source'
    ),
    "sql_database_navigation": _tmdl(
        'let\n'
        '    Source = Sql.Database("srv.example.corp", "AnalyticsDb"),\n'
        '    T = Source{[Schema="rpt",Item="V_Falls_PBI"]}[Data]\n'
        'in\n'
        '    T'
    ),
    "sql_databases_navigation": _tmdl(
        'let\n'
        '    Source = Sql.Databases("srv.example.corp"),\n'
        '    DB = Source{[Name="AnalyticsDb"]}[Data],\n'
        '    V = DB{[Schema="rpt",Item="V_Census_PBI"]}[Data]\n'
        'in\n'
        '    V'
    ),
}


class TestParser:
    def test_let_call_record_parse(self):
        ast = parse_m('let\n  Source = Sql.Database("s", "d", [Query="EXEC x.y"])\nin\n  Source')
        assert isinstance(ast, Let)
        call = ast.bindings[0][1]
        assert isinstance(call, Call) and call.name == "Sql.Database"
        assert isinstance(call.args[0], Lit)
        assert isinstance(call.args[2], Rec)

    def test_doubled_quote_escape(self):
        ast = parse_m('"say ""hi"" now"')
        assert isinstance(ast, Lit) and ast.value == 'say "hi" now'

    def test_quoted_identifier(self):
        ast = parse_m('#"Server Param"')
        assert isinstance(ast, Ref) and ast.name == "Server Param"

    def test_never_raises_on_garbage(self):
        for junk in ("", "((((", "let x = in", "1 + + )", "@#$%^"):
            assert parse_m(junk) is not None

    def test_outside_subset_is_opaque_not_wrong(self):
        # a lambda is beyond the subset — must degrade honestly
        ast = parse_m("(x) => x + 1")
        assert isinstance(ast, Opaque)


class TestSignatures:
    def test_argument_kinds_discriminate(self):
        """Amendment 1: same function, different arg kinds -> different
        signatures. Function-name-only signatures are useless."""
        _, lit_sig, lit_args = partition_shape(
            'let\n  S = Sql.Database("srv", "db", [Query="EXEC r.p"])\nin\n  S')
        _, par_sig, par_args = partition_shape(
            'let\n  S = Sql.Database(@Srv, "db", [Query="EXEC r.p"])\nin\n  S')
        assert lit_args[0] == "literal"
        assert par_args[0] == "parameter"
        assert lit_sig != par_sig

    def test_concat_kind_captured(self):
        _, _, args = partition_shape(
            'let\n  S = Odbc.Query("dsn", "exec r.p \'" & D & "\'")\nin\n  S')
        assert args[1].startswith("concat(literal")

    def test_leak_whitelist_only(self):
        """Amendment 2: customer identifiers CANNOT reach a signature.
        Every name below is customer-defined; none may be emitted."""
        secrets = ["SecretRevenueForecast", "MySecretServer",
                   "Contoso_Internal_Query", "Secret Param Name"]
        m = ('let\n'
             '    Source = SecretRevenueForecast,\n'
             '    Joined = Table.NestedJoin(Source, "k", MySecretServer, "k", "j"),\n'
             '    Final = Contoso_Internal_Query(Joined, #"Secret Param Name")\n'
             'in\n'
             '    Final')
        family, sig, args = partition_shape(m)
        emitted = " ".join([family, sig] + args)
        for secret in secrets:
            assert secret not in emitted, f"leaked: {secret} in {emitted}"

    def test_stdlib_names_pass_verbatim(self):
        family, sig, _ = partition_shape(
            'let\n  S = Table.FromRows({{"a"}}, {"c"})\nin\n  S')
        assert family == "Table.FromRows"
        assert "Table.FromRows" in sig


class TestRegistryCoverage:
    def test_every_supported_shape_has_a_passing_fixture(self):
        supported = {s.name for s in SHAPE_REGISTRY if s.status == "supported"}
        assert supported == set(FIXTURES), (
            "supported shapes and fixtures must stay 1:1 — a supported "
            "claim without a fixture is unenforced")
        for shape_name, tmdl in FIXTURES.items():
            row = census_file("R", "T", tmdl)
            assert row.shape == shape_name, (
                f"fixture for {shape_name} classified as {row.shape} "
                f"({row.signature})")
            assert row.status == "supported"
            # the extractor must actually deliver on the claim
            source = parse_tmdl_partition(tmdl, "T")
            assert source is not None and source.sql_object, (
                f"{shape_name}: census says supported but the extractor "
                f"yields nothing")

    def test_directlake_counts_supported(self):
        content = ("table T\n\tpartition T = entity\n\t\tmode: directLake\n"
                   "\t\tsource\n\t\t\tentityName: enc\n")
        assert census_file("R", "T", content).status == "supported"

    def test_non_sql_recognized_never_unknown(self):
        row = census_file("R", "T", _tmdl(
            'let\n  S = Snowflake.Databases("acct", "wh")\nin\n  S'))
        assert row.status == "recognized_unsupported"
        assert row.shape == "non_sql:Snowflake.Databases"

    def test_custom_reference_recognized(self):
        row = census_file("R", "T", _tmdl("let\n  S = SomeSharedQuery\nin\n  S"))
        assert row.status == "recognized_unsupported"
        assert row.shape == "custom_reference"

    def test_unknown_carries_anonymized_signature(self):
        row = census_file("R", "T", _tmdl(
            'let\n  S = CustomFn("x", SecretParam)\nin\n  S'))
        assert row.status == "unknown"
        assert "SecretParam" not in row.signature
        assert "CustomFn" not in row.signature

    def test_classify_defaults_unknown(self):
        assert classify_shape("weird", "weird", []) == ("unknown", "unknown")


class TestCoverageReport:
    def test_file_grain_and_percentages(self):
        class F:
            def __init__(self, r, t, c):
                self.report_name, self.table_name, self.content = r, t, c
        files = [
            F("R1", "A", FIXTURES["odbc_query"]),
            F("R1", "B", _tmdl('let\n  S = Table.FromRows({{"a"}}, {"c"})\nin\n  S')),
            F("R2", "C", _tmdl('let\n  S = CustomFn(SecretParam)\nin\n  S')),
        ]
        rows = census_files(files)
        assert len(rows) == 3  # per (report, pbi_table), not per report
        lines = coverage_lines(rows)
        assert "3 partition files" in lines[0]
        assert any("unknown signatures" in ln for ln in lines)
        assert not any("SecretParam" in ln for ln in lines)
