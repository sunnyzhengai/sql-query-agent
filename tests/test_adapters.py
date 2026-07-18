"""Tests for the catalog adapter pattern.

Tests the metadata generator, publisher orchestration, and adapter protocol
without requiring real API connections.
"""

from src.adapters.base import (
    BulkPublishResult,
    CatalogAdapter,
    MetadataRecord,
    PublishResult,
    PublishStatus,
)
from src.adapters.metadata_generator import (
    generate_all_records,
    generate_metric_records,
    generate_table_records,
)
from src.adapters.publisher import Publisher
from src.pipeline import build_graph


# -- Fixtures --

SAMPLE_DICT_TABLES = [
    {"TABLE_NAME": "encounter", "DESCRIPTION": "Patient encounters"},
    {"TABLE_NAME": "department", "DESCRIPTION": "Hospital departments"},
]

SAMPLE_DICT_COLUMNS = [
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "encounter_id", "DESCRIPTION": "Primary key"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "admit_dt", "DESCRIPTION": "Admission datetime"},
    {"TABLE_NAME": "encounter", "COLUMN_NAME": "discharge_dt", "DESCRIPTION": "Discharge datetime"},
    {"TABLE_NAME": "department", "COLUMN_NAME": "dept_id", "DESCRIPTION": "Department ID"},
    {"TABLE_NAME": "department", "COLUMN_NAME": "dept_name", "DESCRIPTION": "Department name"},
]

SAMPLE_SQL_SOURCES = [
    {
        "metric_id": "ER_LOS",
        "name": "ER Length of Stay",
        "sql": """
            WITH er_visits AS (
                SELECT encounter_id, admit_dt, discharge_dt, dept_id
                FROM encounter e
                JOIN department d ON e.dept_id = d.dept_id
                WHERE d.dept_name = 'Emergency'
            ),
            los_calc AS (
                SELECT encounter_id,
                       DATEDIFF(HOUR, admit_dt, discharge_dt) AS los_hours
                FROM er_visits
            )
            SELECT AVG(los_hours) AS avg_los FROM los_calc
        """,
        "steward": "Dr. Smith",
        "developer": "jane.doe",
    },
]


class FakeAdapter:
    """A fake adapter for testing the publisher pattern."""

    def __init__(self, should_fail: bool = False) -> None:
        self.published: list[MetadataRecord] = []
        self.should_fail = should_fail

    def test_connection(self) -> bool:
        return not self.should_fail

    def publish(self, record: MetadataRecord) -> PublishResult:
        if self.should_fail:
            return PublishResult(asset_id=record.asset_id, status=PublishStatus.FAILED, message="fake error")
        self.published.append(record)
        return PublishResult(asset_id=record.asset_id, status=PublishStatus.SUCCESS)

    def publish_bulk(self, records: list[MetadataRecord]) -> BulkPublishResult:
        result = BulkPublishResult()
        for record in records:
            result.add(self.publish(record))
        return result


# -- Tests: Protocol compliance --

def test_fake_adapter_implements_protocol():
    adapter = FakeAdapter()
    assert isinstance(adapter, CatalogAdapter)


# -- Tests: Metadata generator --

def test_generate_metric_records():
    builder = build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)
    records = generate_metric_records(builder)

    assert len(records) == 1
    record = records[0]
    assert record.asset_id == "canonical:ER_LOS"
    assert record.asset_type == "metric"
    assert record.name == "ER Length of Stay"
    assert record.owner == "Dr. Smith"
    assert "encounter" in record.properties["source_tables"]


def test_generate_table_records():
    builder = build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)
    records = generate_table_records(builder)

    table_names = [r.name for r in records]
    assert "encounter" in table_names
    assert "department" in table_names
    assert all(r.asset_type == "table" for r in records)


def test_generate_all_records():
    builder = build_graph(SAMPLE_DICT_TABLES, SAMPLE_DICT_COLUMNS, SAMPLE_SQL_SOURCES)
    records = generate_all_records(builder)

    types = {r.asset_type for r in records}
    assert "metric" in types
    assert "table" in types


# -- Tests: Publisher --

def test_publisher_single_adapter():
    adapter = FakeAdapter()
    publisher = Publisher()
    publisher.add_adapter("test", adapter)

    records = [MetadataRecord(asset_id="test:1", asset_type="metric", name="Test Metric")]
    results = publisher.publish_all(records)

    assert "test" in results
    assert results["test"].succeeded == 1
    assert len(adapter.published) == 1


def test_publisher_multiple_adapters():
    adapter_a = FakeAdapter()
    adapter_b = FakeAdapter()
    publisher = Publisher()
    publisher.add_adapter("purview", adapter_a)
    publisher.add_adapter("collibra", adapter_b)

    records = [
        MetadataRecord(asset_id="test:1", asset_type="metric", name="Metric 1"),
        MetadataRecord(asset_id="test:2", asset_type="metric", name="Metric 2"),
    ]
    results = publisher.publish_all(records)

    assert results["purview"].succeeded == 2
    assert results["collibra"].succeeded == 2
    assert len(adapter_a.published) == 2
    assert len(adapter_b.published) == 2


def test_publisher_handles_adapter_failure():
    good_adapter = FakeAdapter()
    bad_adapter = FakeAdapter(should_fail=True)
    publisher = Publisher()
    publisher.add_adapter("good", good_adapter)
    publisher.add_adapter("bad", bad_adapter)

    records = [MetadataRecord(asset_id="test:1", asset_type="metric", name="Test")]
    results = publisher.publish_all(records)

    assert results["good"].succeeded == 1
    assert results["bad"].failed == 1


def test_publisher_test_connections():
    good = FakeAdapter()
    bad = FakeAdapter(should_fail=True)
    publisher = Publisher()
    publisher.add_adapter("good", good)
    publisher.add_adapter("bad", bad)

    status = publisher.test_connections()
    assert status["good"] is True
    assert status["bad"] is False


def test_bulk_publish_result_counts():
    result = BulkPublishResult()
    result.add(PublishResult(asset_id="a", status=PublishStatus.SUCCESS))
    result.add(PublishResult(asset_id="b", status=PublishStatus.FAILED))
    result.add(PublishResult(asset_id="c", status=PublishStatus.SKIPPED))
    result.add(PublishResult(asset_id="d", status=PublishStatus.SUCCESS))

    assert result.total == 4
    assert result.succeeded == 2
    assert result.failed == 1
    assert result.skipped == 1
