"""Tests for the Collibra adapter's failure honesty.

Audit 2026-08-15 found three lies in this adapter:
1. publish() sent name-only payloads — descriptions/owners silently dropped,
   SUCCESS reported.
2. _find_asset() swallowed every error into None ("absent"), so a transient
   503 caused a duplicate asset to be CREATED.
3. Publisher.publish_all() turned a raising adapter into an empty
   BulkPublishResult — "total failure" and "nothing to publish" were the
   same number.

These tests pin the honest behavior. All use a fake session — no network.
"""

from src.adapters.base import MetadataRecord, PublishStatus
from src.adapters.collibra import CollibraAdapter, CollibraConfig
from src.adapters.publisher import Publisher


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Routes requests to canned responses; records every call."""

    def __init__(self, routes):
        # routes: list of (method, url_substring, response_or_exception)
        self.routes = list(routes)
        self.calls = []

    def _dispatch(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for m, fragment, outcome in self.routes:
            if m == method and fragment in url:
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
        raise AssertionError(f"unexpected {method} {url}")

    def get(self, url, **kwargs):
        return self._dispatch("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._dispatch("POST", url, **kwargs)

    def patch(self, url, **kwargs):
        return self._dispatch("PATCH", url, **kwargs)


def make_adapter(routes):
    adapter = CollibraAdapter(CollibraConfig(base_url="https://x/rest/2.0"))
    adapter._session = FakeSession(routes)
    return adapter


RECORD = MetadataRecord(
    asset_id="canonical:ER_LOS", asset_type="metric", name="ER Length of Stay",
    description="Average ER length of stay in hours.", owner="Dr. Smith",
)


class TestPublishCarriesDescription:
    def test_create_path_writes_description_attribute(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": []})),
            ("POST", "/assets/", AssertionError("bulk not expected")),
            ("POST", "/assets", FakeResponse(201, {"id": "abc-123"})),
            ("GET", "/attributes", FakeResponse(200, {"results": []})),
            ("POST", "/attributes", FakeResponse(201, {"id": "attr-1"})),
        ])
        result = adapter.publish(RECORD)
        assert result.status == PublishStatus.SUCCESS
        attr_posts = [c for c in adapter._session.calls
                      if c[0] == "POST" and "/attributes" in c[1]]
        assert attr_posts, "description attribute was never written"
        assert attr_posts[0][2]["json"]["value"] == RECORD.description

    def test_update_path_writes_description_attribute(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": [{"id": "abc-123"}]})),
            ("PATCH", "/assets/abc-123", FakeResponse(200, {"id": "abc-123"})),
            ("GET", "/attributes", FakeResponse(200, {"results": [{"id": "attr-1"}]})),
            ("PATCH", "/attributes/attr-1", FakeResponse(200, {})),
        ])
        result = adapter.publish(RECORD)
        assert result.status == PublishStatus.SUCCESS
        patches = [c for c in adapter._session.calls
                   if c[0] == "PATCH" and "/attributes/" in c[1]]
        assert patches and patches[0][2]["json"]["value"] == RECORD.description

    def test_description_write_failure_is_not_success(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": []})),
            ("POST", "/assets", FakeResponse(201, {"id": "abc-123"})),
            ("GET", "/attributes", FakeResponse(200, {"results": []})),
            ("POST", "/attributes", FakeResponse(500, text="boom")),
        ])
        result = adapter.publish(RECORD)
        assert result.status == PublishStatus.FAILED

    def test_empty_description_skips_attribute_write(self):
        bare = MetadataRecord(asset_id="t:1", asset_type="table", name="T1")
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": []})),
            ("POST", "/assets", FakeResponse(201, {"id": "abc-123"})),
        ])
        result = adapter.publish(bare)
        assert result.status == PublishStatus.SUCCESS
        assert not any("/attributes" in c[1] for c in adapter._session.calls)


class TestLookupFailureDoesNotCreate:
    def test_lookup_exception_fails_without_creating(self):
        adapter = make_adapter([
            ("GET", "/assets", ConnectionError("503 from proxy")),
        ])
        result = adapter.publish(RECORD)
        assert result.status == PublishStatus.FAILED
        assert "lookup" in result.message.lower()
        assert not any(c[0] == "POST" for c in adapter._session.calls), \
            "a failed lookup must never fall through to CREATE (duplicates)"

    def test_lookup_http_error_fails_without_creating(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(503, text="unavailable")),
        ])
        result = adapter.publish(RECORD)
        assert result.status == PublishStatus.FAILED
        assert not any(c[0] == "POST" for c in adapter._session.calls)

    def test_confirmed_absent_still_creates(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": []})),
            ("POST", "/assets", FakeResponse(201, {"id": "new-1"})),
            ("GET", "/attributes", FakeResponse(200, {"results": []})),
            ("POST", "/attributes", FakeResponse(201, {})),
        ])
        assert adapter.publish(RECORD).status == PublishStatus.SUCCESS


class TestPublishBulkPerRecord:
    def test_bulk_carries_descriptions(self):
        adapter = make_adapter([
            ("GET", "/assets", FakeResponse(200, {"results": []})),
            ("POST", "/assets", FakeResponse(201, {"id": "id-1"})),
            ("GET", "/attributes", FakeResponse(200, {"results": []})),
            ("POST", "/attributes", FakeResponse(201, {})),
        ])
        result = adapter.publish_bulk([RECORD, RECORD])
        assert result.total == 2 and result.succeeded == 2
        attr_posts = [c for c in adapter._session.calls
                      if c[0] == "POST" and "/attributes" in c[1]]
        assert len(attr_posts) == 2


class RaisingAdapter:
    def test_connection(self):
        return True

    def publish(self, record):
        raise ConnectionError("catalog unreachable")

    def publish_bulk(self, records):
        raise ConnectionError("catalog unreachable")


class TestPublishAllHonesty:
    def test_raising_adapter_yields_per_record_failures_not_empty(self):
        publisher = Publisher()
        publisher.add_adapter("collibra", RaisingAdapter())
        records = [
            MetadataRecord(asset_id="a", asset_type="metric", name="A"),
            MetadataRecord(asset_id="b", asset_type="metric", name="B"),
        ]
        results = publisher.publish_all(records)
        r = results["collibra"]
        # "total failure" must be distinguishable from "nothing to publish"
        assert r.total == 2 and r.failed == 2 and r.succeeded == 0
        assert all(x.status == PublishStatus.FAILED for x in r.results)
        assert all("unreachable" in x.message for x in r.results)
