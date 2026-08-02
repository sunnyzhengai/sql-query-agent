"""Mock GQL client for local testing of FabricGraphBackend.

Returns canned GQL-shaped responses derived from the sample data golden
output. Use this instead of hitting the real Fabric Graph API in unit tests.
"""

from __future__ import annotations

from src.graph.gql_client import GQLResult


class MockGQLClient:
    """GQLClient substitute that returns pre-recorded responses.

    Matches queries by looking for key patterns (node_id values, labels)
    and returns the corresponding canned result. This avoids depending
    on exact GQL string formatting.
    """

    def __init__(self, responses: dict[str, GQLResult] | None = None) -> None:
        self._responses = responses or {}
        self._call_log: list[str] = []

    def execute(self, gql_query: str) -> GQLResult:
        self._call_log.append(gql_query)

        # Check for exact pattern matches first
        for pattern, result in self._responses.items():
            if pattern in gql_query:
                return result

        # Default: empty result
        return GQLResult()

    @property
    def call_count(self) -> int:
        return len(self._call_log)


def build_er_los_mock() -> MockGQLClient:
    """Build a mock client pre-loaded with ER_LOS sample data responses.

    These responses match what the DeltaBackend produces from the
    seed_sample_data fixtures, encoded as GQL API response format.
    """
    responses = {
        # Query 1: Canonical + transforms for ER_LOS
        "canonical:ER_LOS": GQLResult(
            columns=[
                {"name": "c_id", "gqlType": "STRING"},
                {"name": "c_name", "gqlType": "STRING"},
                {"name": "c_desc", "gqlType": "STRING"},
                {"name": "c_steward", "gqlType": "STRING"},
                {"name": "c_developer", "gqlType": "STRING"},
                {"name": "t1_id", "gqlType": "STRING"},
                {"name": "t1_name", "gqlType": "STRING"},
                {"name": "t1_metric_id", "gqlType": "STRING"},
                {"name": "t1_fragment", "gqlType": "STRING"},
                {"name": "td_id", "gqlType": "STRING"},
                {"name": "td_name", "gqlType": "STRING"},
                {"name": "td_metric_id", "gqlType": "STRING"},
                {"name": "td_fragment", "gqlType": "STRING"},
            ],
            # Note: response aliases (c_id, t1_id, etc.) are set by our GQL queries,
            # not by the column names in the source tables. No camelCase change needed here.
            data=[
                {
                    "c_id": "canonical:ER_LOS",
                    "c_name": "ER Length of Stay",
                    "c_desc": "",
                    "c_steward": "Dr. Smith",
                    "c_developer": "jane.doe",
                    "t1_id": "transform:ER_LOS:los_calc",
                    "t1_name": "los_calc",
                    "t1_metric_id": "ER_LOS",
                    "t1_fragment": (
                        "SELECT encounter_id, patient_id, department_id, "
                        "DATEDIFF(MINUTE, admit_dt, discharge_dt) / 60.0 AS los_hours "
                        "FROM er_visits"
                    ),
                    "td_id": "transform:ER_LOS:er_visits",
                    "td_name": "er_visits",
                    "td_metric_id": "ER_LOS",
                    "td_fragment": (
                        "SELECT e.encounter_id, e.patient_id, e.admit_dt, "
                        "e.discharge_dt, e.department_id "
                        "FROM encounter e "
                        "INNER JOIN department d ON e.department_id = d.department_id "
                        "WHERE d.department_name = 'Emergency'"
                    ),
                },
            ],
            status_code="00000",
        ),

        # Query 2: Technical nodes from transforms
        "TRANSFORM_TO_TECHNICAL": GQLResult(
            columns=[
                {"name": "nodeId", "gqlType": "STRING"},
                {"name": "name", "gqlType": "STRING"},
                {"name": "description", "gqlType": "STRING"},
                {"name": "tableName", "gqlType": "STRING"},
                {"name": "schemaName", "gqlType": "STRING"},
                {"name": "databaseName", "gqlType": "STRING"},
                {"name": "columnName", "gqlType": "STRING"},
            ],
            data=[
                {
                    "nodeId": "tech:DBO.ENCOUNTER",
                    "name": "encounter",
                    "description": "Patient encounter/visit records",
                    "tableName": "encounter",
                    "schemaName": "dbo",
                    "databaseName": "",
                    "columnName": "",
                },
                {
                    "nodeId": "tech:DBO.DEPARTMENT",
                    "name": "department",
                    "description": "Hospital departments and units",
                    "tableName": "department",
                    "schemaName": "dbo",
                    "databaseName": "",
                    "columnName": "",
                },
            ],
            status_code="00000",
        ),

        # Query 3: Dimension nodes (none for ER_LOS sample)
        "TECHNICAL_TO_DIMENSION": GQLResult(
            columns=[
                {"name": "nodeId", "gqlType": "STRING"},
                {"name": "name", "gqlType": "STRING"},
                {"name": "description", "gqlType": "STRING"},
                {"name": "tableName", "gqlType": "STRING"},
                {"name": "columnName", "gqlType": "STRING"},
            ],
            data=[],
            status_code="00000",
        ),

        # list_canonical_metrics
        "MATCH (c:Canonical)": GQLResult(
            columns=[{"name": "nodeId", "gqlType": "STRING"}],
            data=[{"nodeId": "canonical:ER_LOS"}],
            status_code="00000",
        ),
    }

    return MockGQLClient(responses)
