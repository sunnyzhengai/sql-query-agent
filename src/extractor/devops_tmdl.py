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
    server: str = ""         # e.g., "clarity-host.example.corp" or DSN name
    database: str = ""       # e.g., "ClarityDB"
    schema: str = ""         # e.g., "Reporting"
    sql_object: str = ""     # e.g., "V_ACME_Executive_Dashboard_Claims_PBI"
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


# An M argument that names a server/DSN: a string literal, a parameter
# reference (@Scoped or plain identifier), or a quoted identifier
# (#"Server Param"). Field find 2026-08-18: real estates pass servers as
# PARAMETERS at scale (277 pattern misses) — literal-only matching was
# the dominant fallout.
_M_SOURCE_ARG = r'(?:"([^"]*)"|@([A-Za-z_]\w*)|#"([^"]+)"|([A-Za-z_]\w*))'


def _first_group(*groups: "str | None") -> str:
    return next((g for g in groups if g), "")


def _parse_exec_target(query: str) -> "tuple[str, str, str] | None":
    """(database, schema, object) from an EXEC statement, any of:
    EXEC proc | EXEC schema.proc | EXEC db.schema.proc — each part
    bracketed or bare. The query may be the FIRST literal chunk of a
    concatenated M string ("exec [S].P '" & Param & ...): the target
    always lives in that first chunk, so a trailing fragment is fine.
    """
    m = re.search(
        r"\bEXEC(?:UTE)?\s+"
        r"(?:\[?(\w+)\]?\s*\.\s*)?"  # optional database
        r"(?:\[?(\w+)\]?\s*\.\s*)?"  # optional schema
        r"\[?(\w+)\]?",              # object name
        query, re.IGNORECASE,
    )
    if not m:
        return None
    parts = [p for p in m.groups() if p]
    obj = parts[-1]
    schema = parts[-2] if len(parts) >= 2 else ""
    database = parts[-3] if len(parts) >= 3 else ""
    return database, schema, obj


def parse_tmdl_partition(tmdl_content: str, table_name: str) -> SqlSource | None:
    """Extract the SQL source from a TMDL partition block.

    Looks for partition blocks with M expressions like:
        partition TableName-xxx = m
            source =
                let
                    Source = Odbc.DataSource("dsn=Clarity", ...),
                    DB = Source{[Name="ClarityDB",Kind="Database"]}[Data],
                    Schema = DB{[Name="Reporting",Kind="Schema"]}[Data],
                    View = Schema{[Name="V_ACME_...",Kind="View"]}[Data]
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
        # Pattern 5: DirectLake has no M expression at all
        return _parse_directlake_partition(tmdl_content, table_name)

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

    # Pattern 2: Odbc.Query(<server-arg>, "exec [db].[schema].[proc] ...")
    # Server arg: literal, parameter, or quoted identifier (_M_SOURCE_ARG).
    # Query capture stops at the first closing quote — for concatenated
    # queries ("exec ... '" & Param & ...) that IS the first literal
    # chunk, which always carries the exec target.
    odbc_query_match = re.search(
        r"Odbc\.Query\(\s*" + _M_SOURCE_ARG + r'\s*,\s*"([^"]*)', m_expr
    )
    if odbc_query_match:
        source.server = _first_group(*odbc_query_match.groups()[:4])
        query = odbc_query_match.group(5)
        # Clean Power Query escape sequences
        query = query.replace("#(lf)", " ").replace("#(cr)", " ").replace("#(tab)", " ")
        target = _parse_exec_target(query)
        if target:
            source.database, source.schema, source.sql_object = target
            source.sql_object_type = "StoredProcedure"

    # Pattern 3: Sql.Database(<server-arg>, "database", [..., Query="..."])
    sql_db_match = re.search(
        r"Sql\.Database\(\s*" + _M_SOURCE_ARG + r'\s*,\s*"([^"]+)"', m_expr
    )
    if sql_db_match:
        source.server = _first_group(*sql_db_match.groups()[:4])
        source.database = sql_db_match.group(5)

    # Extract stored proc or inline SQL from the Query record field. The
    # field need not open the record ([CommandTimeout=..., Query="..."])
    # and the value may be a concatenation — first literal chunk again.
    query_match = re.search(r'[\[,]\s*Query\s*=\s*"([^"]*)', m_expr)
    if query_match and not source.sql_object:
        query = query_match.group(1)
        query = query.replace("#(lf)", " ").replace("#(cr)", " ").replace("#(tab)", " ")
        target = _parse_exec_target(query)
        if target:
            database, source.schema, source.sql_object = target
            source.sql_object_type = "StoredProcedure"
            if database:
                source.database = database
        else:
            # Inline SQL — mark as InlineQuery with a summary
            source.sql_object = "InlineQuery"
            source.sql_object_type = "InlineSQL"

    # Sql.Database Schema/Item navigation: Source{[Schema="rpt",
    # Item="V_X"]}[Data] — the common navigator form when no Query is
    # used (census guard caught this as claimed-but-unextractable).
    nav_si = re.search(
        r'\{\s*\[\s*Schema\s*=\s*"([^"]+)"\s*,\s*Item\s*=\s*"([^"]+)"\s*\]\s*\}',
        m_expr,
    )
    if nav_si and not source.sql_object:
        source.schema = nav_si.group(1)
        source.sql_object = nav_si.group(2)
        # Kind is unstated in this form — corpus membership decides what
        # it really is downstream (Table is the neutral claim).
        source.sql_object_type = "Table"

    # Pattern 4: Sql.Databases("server") with navigation
    sql_dbs_match = re.search(r'Sql\.Databases\(\s*"([^"]+)"', m_expr)
    if sql_dbs_match and not source.server:
        source.server = sql_dbs_match.group(1)

    return source if source.sql_object else None


def _parse_directlake_partition(tmdl_content: str, table_name: str) -> SqlSource | None:
    """Pattern 5: DirectLake partitions (Fabric-native default).

    DirectLake reads a warehouse/lakehouse TABLE directly — there is no
    M query and no EXEC (DirectLake cannot call procs; views fall back
    to DirectQuery). Shape:

        partition Foo = entity
            mode: directLake
            source
                entityName: dimension_customer
                schemaName: dbo            (optional)
                expressionSource: DatabaseQuery
    """
    block = re.search(
        r"partition\s+[^\n]+=\s*entity\s*\n"
        r"\s+mode:\s*directLake\s*\n"
        r"(.*?)(?=\n\s*\n|\n\s+annotation|\Z)",
        tmdl_content, re.DOTALL,
    )
    if not block:
        return None
    body = block.group(1)
    entity = re.search(r"entityName:\s*([^\s]+)", body)
    if not entity:
        return None
    schema = re.search(r"schemaName:\s*([^\s]+)", body)
    return SqlSource(
        table_name=table_name,
        schema=schema.group(1) if schema else "",
        sql_object=entity.group(1),
        sql_object_type="Table",
        raw_m_expression=body.strip(),
    )


# M functions that are legitimately not SQL sources — files built on
# these are CORRECT to skip, but the skip must be a recorded reason, not
# a silent absence (174 models vanished silently on a live estate,
# 2026-08-18). Order matters only for reporting: first hit names the row.
_NON_SQL_SOURCE_FNS = (
    "Snowflake.Databases",
    "Folder.Files",
    "Excel.Workbook",
    "SharePoint.Files",
    "SharePoint.Tables",
    "Web.Contents",
    "ActiveDirectory.Domains",
    "Table.FromRows",
    "Table.Combine",
    "Table.NestedJoin",
    "DateTime.LocalNow",
    "DateTime.FixedLocalNow",
    "List.Dates",
    "#table",
)


def classify_partition_fallout(
    tmdl_content: str, table_name: str
) -> "tuple[str, str]":
    """Why a table file yielded no SQL source row: (reason_code, reason_text).

    Total classification — every parse miss gets a reason
    (HANDOFF_TMDL_PATTERN_GAPS item 2; the silent-absence rule). Codes:
      calculated_table       DAX-defined table, no external source
      no_partition           measures-only / annotation-only table file
      directlake_entity      entity partition without an entityName
      non_sql_source:<fn>    recognized non-SQL M source (correct skip)
      unrecognized_shape     M partition no pattern understood (the
                             product signal — file a shape)
    """
    if re.search(r"partition\s+[^\n]+=\s*calculated\b", tmdl_content):
        return ("calculated_table",
                "calculated table (DAX-defined) — no external SQL source")
    part = re.search(r"partition\s+[^\n]+=\s*(m|entity)\b", tmdl_content)
    if not part:
        return ("no_partition",
                "no partition block (measures-only or annotation-only file)")
    if part.group(1) == "entity":
        return ("directlake_entity",
                "directLake entity partition without a resolvable entityName")
    for fn in _NON_SQL_SOURCE_FNS:
        if fn in tmdl_content:
            return (f"non_sql_source:{fn}",
                    f"recognized non-SQL M source ({fn}) — correctly skipped")
    return ("unrecognized_shape",
            "M partition matched no known SQL source pattern — report this "
            "shape so a handler can ship")


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
        except Exception as e:  # noqa: BLE001 — logged warning; record-and-continue per repo item
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
            except Exception as e:  # noqa: BLE001 — logged warning; record-and-continue per repo item
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
