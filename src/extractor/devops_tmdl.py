"""Parse TMDL files from Azure DevOps to extract PBI report lineage.

Reads .SemanticModel/definition/tables/*.tmdl files from DevOps repos
to extract:
1. Partition sources — M expressions that reference SQL views/procs (deterministic lineage)
2. DAX measures — business logic defined in the PBI layer
3. DAX calculated columns — transformations defined in the PBI layer

Usage:
    from src.extractor.devops_tmdl import DevOpsTmdlClient
    client = DevOpsTmdlClient(org, project, pat)
    reports = client.extract_all_reports(repo_name)
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)


@dataclass
class SqlSource:
    """A SQL data source extracted from a TMDL partition."""
    table_name: str          # PBI table name (e.g., "Claims")
    server: str = ""         # e.g., "claritytstdb.cchcs.ldap" or DSN name
    database: str = ""       # e.g., "CookClarity"
    schema: str = ""         # e.g., "Reporting"
    sql_object: str = ""     # e.g., "V_CCHP_Executive_Dashboard_Claims_PBI"
    sql_object_type: str = ""  # "View", "Table", "Function", or "StoredProcedure"
    raw_m_expression: str = ""  # the full M/Power Query source


@dataclass
class DaxExpression:
    """A DAX measure or calculated column from a TMDL file."""
    name: str
    expression: str
    expression_type: str  # "measure" or "calculated_column"
    table_name: str = ""  # which PBI table it belongs to


@dataclass
class ReportLineage:
    """Complete lineage for a single PBI report."""
    report_name: str
    repo_name: str
    semantic_model_path: str
    sql_sources: list[SqlSource] = field(default_factory=list)
    dax_expressions: list[DaxExpression] = field(default_factory=list)

    @property
    def sql_object_names(self) -> list[str]:
        return [s.sql_object for s in self.sql_sources if s.sql_object]

    def __str__(self) -> str:
        return (
            f"{self.report_name}: "
            f"{len(self.sql_sources)} SQL sources, "
            f"{len(self.dax_expressions)} DAX expressions"
        )


def parse_tmdl_partition(tmdl_content: str, table_name: str) -> SqlSource | None:
    """Extract the SQL source from a TMDL partition block.

    Looks for partition blocks with M expressions like:
        partition TableName-xxx = m
            source =
                let
                    Source = Odbc.DataSource("dsn=Clarity", ...),
                    DB = Source{[Name="CookClarity",Kind="Database"]}[Data],
                    Schema = DB{[Name="Reporting",Kind="Schema"]}[Data],
                    View = Schema{[Name="V_CCHP_...",Kind="View"]}[Data]
                in
                    View

    Also handles:
        Odbc.Query("dsn=Clarity", "exec [DB].[Schema].[USP_Proc]")
        Sql.Database("server", "database", [Query="EXEC dbo.USP_..."])
    """
    # Find partition blocks with M expressions
    # Partition names can be bare or quoted: partition Name = m  OR  partition 'Name' = m
    partition_pattern = re.compile(
        r"""partition\s+[^\n]+=\s*m\s*\n"""
        r"""\s+mode:\s*\w+\s*\n"""
        r"""\s+source\s*=\s*\n(.*?)(?=\n\s*\n|\n\s+annotation|\Z)""",
        re.DOTALL
    )

    match = partition_pattern.search(tmdl_content)
    if not match:
        return None

    m_expr = match.group(1).strip()
    source = SqlSource(table_name=table_name, raw_m_expression=m_expr)

    # Pattern 1: Odbc.DataSource with navigation
    # Extract database name
    db_match = re.search(r'\[Name="([^"]+)",\s*Kind="Database"\]', m_expr)
    if db_match:
        source.database = db_match.group(1)

    # Extract schema
    schema_match = re.search(r'\[Name="([^"]+)",\s*Kind="Schema"\]', m_expr)
    if schema_match:
        source.schema = schema_match.group(1)

    # Extract object name and type
    obj_match = re.search(r'\[Name="([^"]+)",\s*Kind="(\w+)"\](?!\[Data\]\s*,)', m_expr)
    # Get the LAST Kind match (the actual object, not intermediate navigation)
    obj_matches = re.findall(r'\[Name="([^"]+)",\s*Kind="(\w+)"\]', m_expr)
    if obj_matches:
        # Last match is the actual SQL object
        source.sql_object = obj_matches[-1][0]
        source.sql_object_type = obj_matches[-1][1]

    # Extract DSN/server from Odbc.DataSource
    dsn_match = re.search(r'Odbc\.DataSource\("([^"]+)"', m_expr)
    if dsn_match:
        source.server = dsn_match.group(1)

    # Pattern 2: Odbc.Query("dsn", "exec [db].[schema].[proc]")
    # Query string may contain #(lf) (Power Query line feed escape)
    odbc_query_match = re.search(r'Odbc\.Query\(\s*"([^"]+)"\s*,\s*"([^"]+)"', m_expr)
    if odbc_query_match:
        source.server = odbc_query_match.group(1)
        query = odbc_query_match.group(2)
        # Clean Power Query escape sequences
        query = query.replace("#(lf)", " ").replace("#(cr)", " ").replace("#(tab)", " ")
        # Parse "exec [CookClarity].[COOK_RPT].[USP_CCMC_ANESTHESIA_CRNA_PBI]"
        # or "exec dbo.USP_Something" or "exec db.schema.proc"
        exec_match = re.search(
            r'exec\s+'
            r'(?:\[?(\w+)\]?\.)?' # optional database
            r'(?:\[?(\w+)\]?\.)?' # optional schema
            r'\[?(\w+)\]?',       # object name
            query, re.IGNORECASE
        )
        if exec_match:
            parts = [p for p in exec_match.groups() if p]
            source.sql_object = parts[-1]  # last part is always the object
            source.sql_object_type = "StoredProcedure"
            if len(parts) >= 2:
                source.schema = parts[-2]
            if len(parts) >= 3:
                source.database = parts[-3]

    # Pattern 3: Sql.Database("server", "database", [Query="..."])
    # Server can be a string literal or a variable/parameter name
    sql_db_match = re.search(
        r'Sql\.Database\(\s*"([^"]+)"\s*,\s*"([^"]+)"', m_expr
    )
    if sql_db_match:
        source.server = sql_db_match.group(1)
        source.database = sql_db_match.group(2)

    # Sql.Database with variable server: Sql.Database(ServerParam, "database", ...)
    if not sql_db_match:
        sql_db_var_match = re.search(
            r'Sql\.Database\(\s*(\w+)\s*,\s*"([^"]+)"', m_expr
        )
        if sql_db_var_match:
            source.server = sql_db_var_match.group(1)  # parameter name
            source.database = sql_db_var_match.group(2)

    # Extract stored proc or inline SQL from Query parameter
    # Query value may span multiple lines with #(lf) escapes
    query_match = re.search(r'\[Query\s*=\s*"((?:[^"\\]|\\.)*)"\s*\]', m_expr, re.DOTALL)
    if query_match and not source.sql_object:
        query = query_match.group(1)
        query = query.replace("#(lf)", " ").replace("#(cr)", " ").replace("#(tab)", " ")
        # Try to extract proc name from "EXEC [schema].[proc]" or "EXEC schema.proc"
        proc_match = re.search(
            r'EXEC\s+'
            r'(?:\[?(\w+)\]?\.)?' # optional schema
            r'\[?(\w+)\]?',       # proc name
            query, re.IGNORECASE
        )
        if proc_match:
            source.schema = proc_match.group(1) or ""
            source.sql_object = proc_match.group(2)
            source.sql_object_type = "StoredProcedure"
        else:
            # Inline SQL — mark as InlineQuery with a summary
            source.sql_object = "InlineQuery"
            source.sql_object_type = "InlineSQL"

    # Pattern 4: Sql.Databases("server") with navigation
    sql_dbs_match = re.search(r'Sql\.Databases\(\s*"([^"]+)"', m_expr)
    if sql_dbs_match and not source.server:
        source.server = sql_dbs_match.group(1)

    return source if source.sql_object else None


def parse_tmdl_dax(tmdl_content: str, table_name: str) -> list[DaxExpression]:
    """Extract DAX measures and calculated columns from a TMDL file.

    Measures:  measure 'Name' = DAX_EXPRESSION
    Calc cols: column 'Name' = DAX_EXPRESSION
    Regular columns (with sourceColumn) are skipped.
    """
    expressions = []

    # DAX measures: measure 'Name' = expression (may be multiline)
    measure_pattern = re.compile(
        r"^\s+measure\s+'([^']+)'\s*=\s*(.+?)(?=\n\s+(?:measure|column|partition|annotation|changedProperty|formatString|lineageTag|displayFolder)\b|\Z)",
        re.MULTILINE | re.DOTALL
    )
    for match in measure_pattern.finditer(tmdl_content):
        name = match.group(1)
        expr = match.group(2).strip()
        # Clean up: remove trailing metadata lines
        expr = _clean_dax_expression(expr)
        if expr:
            expressions.append(DaxExpression(
                name=name,
                expression=expr,
                expression_type="measure",
                table_name=table_name,
            ))

    # Calculated columns: column 'Name' = DAX_EXPRESSION (no sourceColumn)
    col_pattern = re.compile(
        r"^\s+column\s+'([^']+)'\s*=\s*(.+?)(?=\n\s+(?:measure|column|partition|annotation|changedProperty|formatString|lineageTag|displayFolder|summarizeBy)\b|\Z)",
        re.MULTILINE | re.DOTALL
    )
    for match in col_pattern.finditer(tmdl_content):
        name = match.group(1)
        expr = match.group(2).strip()
        expr = _clean_dax_expression(expr)
        # Only include if it's actually a DAX expression (not just a column reference)
        if expr and not _is_source_column_reference(tmdl_content, name):
            expressions.append(DaxExpression(
                name=name,
                expression=expr,
                expression_type="calculated_column",
                table_name=table_name,
            ))

    return expressions


def _clean_dax_expression(expr: str) -> str:
    """Remove trailing TMDL metadata lines from a DAX expression."""
    lines = expr.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        # Stop at metadata lines
        if stripped.startswith(("formatString:", "lineageTag:", "displayFolder:",
                                "annotation ", "changedProperty")):
            break
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def _is_source_column_reference(tmdl_content: str, col_name: str) -> bool:
    """Check if a column has a sourceColumn property (meaning it's not calculated)."""
    # Find the column block and check if sourceColumn appears before the next column/measure/partition
    pattern = re.compile(
        rf"column\s+'{re.escape(col_name)}'[^\n]*\n(.*?)(?=\n\s+(?:column|measure|partition)\s|\Z)",
        re.DOTALL
    )
    match = pattern.search(tmdl_content)
    if match:
        block = match.group(1)
        return "sourceColumn:" in block
    return False


class DevOpsTmdlClient:
    """Client for reading TMDL files from Azure DevOps Git repos.

    Args:
        org: Azure DevOps organization (e.g., "CookChildrens").
        project: DevOps project name.
        pat: Personal Access Token with Code (Read) scope.
    """

    def __init__(self, org: str, project: str, pat: str) -> None:
        self.org = org
        self.project = project
        self._auth = base64.b64encode(f":{pat}".encode()).decode()
        self._base_url = (
            f"https://dev.azure.com/{org}/{requests.utils.quote(project)}"
            f"/_apis/git/repositories"
        )
        self._headers = {"Authorization": f"Basic {self._auth}"}

    def _get(self, url: str, params: dict | None = None) -> requests.Response:
        resp = requests.get(url, headers=self._headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp

    def list_repos(self) -> list[dict]:
        """List all Git repos in the project."""
        resp = self._get(f"{self._base_url}?api-version=7.1")
        return resp.json().get("value", [])

    def list_items(self, repo_name: str, path: str = "/",
                   recursion: str = "oneLevel") -> list[dict]:
        """List files/folders in a repo path."""
        url = (
            f"{self._base_url}/{requests.utils.quote(repo_name)}"
            f"/items?api-version=7.1"
        )
        resp = self._get(url, params={
            "scopePath": path,
            "recursionLevel": recursion,
        })
        return resp.json().get("value", [])

    def get_file(self, repo_name: str, path: str) -> str:
        """Read a file's contents from a repo."""
        url = (
            f"{self._base_url}/{requests.utils.quote(repo_name)}"
            f"/items?api-version=7.1"
        )
        resp = self._get(url, params={"path": path})
        return resp.text

    def find_semantic_models(self, repo_name: str) -> list[dict]:
        """Find all .SemanticModel folders in a repo.

        Returns list of dicts with 'report_name' and 'path'.
        """
        # Get full tree
        items = self.list_items(repo_name, "/", recursion="full")
        models = []
        seen = set()

        for item in items:
            path = item.get("path", "")
            if ".SemanticModel/definition/tables/" in path and path.endswith(".tmdl"):
                # Extract the semantic model path
                sm_path = path.split("/definition/tables/")[0]
                if sm_path not in seen:
                    seen.add(sm_path)
                    # Report name from folder name
                    folder_name = sm_path.rsplit("/", 1)[-1]
                    report_name = folder_name.replace(".SemanticModel", "")
                    models.append({
                        "report_name": report_name,
                        "path": sm_path,
                    })

        logger.info("Found %d semantic models in %s", len(models), repo_name)
        return models

    def extract_report_lineage(self, repo_name: str,
                                semantic_model: dict) -> ReportLineage:
        """Extract full lineage for a single report's semantic model.

        Args:
            repo_name: Git repo name.
            semantic_model: Dict with 'report_name' and 'path'.
        """
        report_name = semantic_model["report_name"]
        sm_path = semantic_model["path"]
        tables_path = f"{sm_path}/definition/tables"

        lineage = ReportLineage(
            report_name=report_name,
            repo_name=repo_name,
            semantic_model_path=sm_path,
        )

        # Get all TMDL files in the tables directory
        try:
            items = self.list_items(repo_name, tables_path)
        except Exception as e:
            logger.warning("Could not list tables for %s: %s", report_name, e)
            return lineage

        for item in items:
            path = item.get("path", "")
            if not path.endswith(".tmdl"):
                continue
            # Skip auto-generated date tables
            if "LocalDateTable_" in path or "DateTableTemplate_" in path:
                continue

            table_name = path.rsplit("/", 1)[-1].replace(".tmdl", "")

            try:
                content = self.get_file(repo_name, path)
            except Exception as e:
                logger.warning("Could not read %s: %s", path, e)
                continue

            # Extract SQL source
            sql_source = parse_tmdl_partition(content, table_name)
            if sql_source:
                lineage.sql_sources.append(sql_source)

            # Extract DAX expressions
            dax_exprs = parse_tmdl_dax(content, table_name)
            lineage.dax_expressions.extend(dax_exprs)

        logger.info(
            "Extracted %s: %d SQL sources, %d DAX expressions",
            report_name, len(lineage.sql_sources), len(lineage.dax_expressions),
        )
        return lineage

    def extract_all_reports(self, repo_name: str) -> list[ReportLineage]:
        """Extract lineage for all reports in a repo.

        Args:
            repo_name: Git repo name (e.g., "BI-TST-Health Plan").

        Returns:
            List of ReportLineage objects.
        """
        models = self.find_semantic_models(repo_name)
        results = []

        for model in models:
            lineage = self.extract_report_lineage(repo_name, model)
            results.append(lineage)
            print(f"  {lineage}")

        return results
