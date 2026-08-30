"""X-RAY-1 (0063 §1, the wedge): the Estate X-Ray report — real
counts, flags with code-level basis, and a deterministic
AI-readiness verdict; no model authors a sentence.

Proves: contract:suite-legibility
"""

from src.xray import compose_xray
from tests.orchestrator.test_tools import fake_kql


class TestXrayReport:
    def test_counts_flags_and_verdict_from_the_store(self):
        r = compose_xray(fake_kql, "Demo Health")
        assert "Estate X-Ray — Demo Health" in r
        assert "certified metrics discovered:" in r
        # the sweep's flags render with identity + members + basis
        assert "misnomer" in r and "cousin_conflict" in r
        assert "distinct logics:" in r and "blast radius:" in r
        # conflict classes present → the hallucination sentence +
        # the NOT-AI-READY verdict
        assert "more than one meaning" in r
        assert "Copilot hallucinates" in r
        assert "NOT AI-READY" in r
        # the order-form page (0063 pitch line)
        assert "makes your expensive catalog true" in r

    def test_deterministic_for_a_store(self):
        assert compose_xray(fake_kql, "X") == compose_xray(fake_kql, "X")

    def test_clean_estate_reads_ready(self):
        from src.orchestrator.tools import (
            GOV_FLAGS_QUERY,
            GOV_SWEEP_META_QUERY,
        )

        def kql(query, params):
            if query == GOV_FLAGS_QUERY:
                return []
            if query == GOV_SWEEP_META_QUERY:
                return [{"swept": 5, "flagged": 0, "clean": 5,
                         "run_at": "2026-08-30T00:00:00"}]
            return fake_kql(query, params)
        r = compose_xray(kql, "Clean Co")
        assert "AI-READY on the surfaces measured" in r
        assert "NOT AI-READY" not in r

    def test_absent_surface_disclosed_never_zero(self):
        def kql(query, params):
            raise ConnectionError("no store")
        r = compose_xray(kql, "X")
        assert "surface not present" in r
        assert "disclosed, not zero" in r

    def test_brand_neutral_core(self):
        r = compose_xray(fake_kql, "X")
        assert "AIVIA" not in r or "AIVIA" in __import__(
            "src.branding", fromlist=["product_name"]).product_name()
