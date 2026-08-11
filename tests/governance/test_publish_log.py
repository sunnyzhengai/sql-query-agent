"""Tests for gov_publish_log row building (admin telemetry phase 1)."""

import pytest

from src.adapters.base import BulkPublishResult, PublishResult, PublishStatus
from src.governance.publish_log import publish_log_rows
from src.schemas import PUBLISH_LOG


def results():
    return [
        PublishResult("reporting.USP_ED_Sepsis", PublishStatus.SUCCESS,
                      "term abc123: 2 assets assigned"),
        PublishResult("ghost.metric", PublishStatus.FAILED, "HTTP 404"),
        PublishResult("skipped.metric", PublishStatus.SKIPPED, ""),
    ]


class TestPublishLogRows:
    def test_rows_match_schema_columns(self):
        rows = publish_log_rows(results(), "purview", "glossary_term",
                                "run-7", "2026-08-11T12:00:00Z")
        expected = {c[0] for c in PUBLISH_LOG["columns"]}
        assert all(set(r) == expected for r in rows)
        assert rows[0]["status"] == "success"
        assert rows[1]["status"] == "failed" and rows[1]["message"] == "HTTP 404"
        assert all(r["target"] == "purview" and r["run_id"] == "run-7"
                   for r in rows)

    def test_bulk_result_unwrapped(self):
        bulk = BulkPublishResult()
        for r in results():
            bulk.add(r)
        rows = publish_log_rows(bulk, "collibra", "asset", "run-1", "t")
        assert len(rows) == 3

    def test_invalid_target_and_kind_rejected(self):
        with pytest.raises(ValueError, match="target"):
            publish_log_rows([], "sharepoint", "asset", "r", "t")
        with pytest.raises(ValueError, match="kind"):
            publish_log_rows([], "purview", "poem", "r", "t")
