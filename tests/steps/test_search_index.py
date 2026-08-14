"""Tests for the search-index refresh (notebook 11's code half)."""

import pytest

from src.steps.search_index import (
    COPY_COMMAND,
    COVERAGE_QUERY,
    REFUSAL_PROBE,
    SearchIndexError,
    embed_command,
    refresh_search_index,
)

ENDPOINT = "https://x.openai.azure.com/openai/deployments/e/embeddings?api-version=v"


class TestCommands:
    def test_copy_maps_columns_by_name_and_nulls_emb(self):
        # positional copy bit us live 2026-08-09 — the project list IS the fix
        assert "| project node_id" in COPY_COMMAND
        assert "emb = dynamic(null)" in COPY_COMMAND
        assert COPY_COMMAND.startswith(".set-or-replace semantic_catalog")

    def test_embed_command_pays_only_for_missing_and_impersonates(self):
        cmd = embed_command(ENDPOINT)
        assert "array_length(emb) == 0" in cmd          # todo = missing only
        assert f"'{ENDPOINT};impersonate'" in cmd       # caller's identity
        assert "union done, embedded" in cmd            # keeps paid vectors


class TestRefresh:
    def run(self, missing_after=0, refusal_rows=0):
        calls = []

        def mgmt(cmd):
            calls.append(("mgmt", cmd))
            return []

        def query(q):
            calls.append(("query", q))
            if q == COVERAGE_QUERY:
                return [{"Count": missing_after}]
            if q == REFUSAL_PROBE:
                return [{"node_id": f"junk{i}"} for i in range(refusal_rows)]
            return [{"Count": 441}]
        return calls, mgmt, query

    def test_copy_then_embed_then_verify(self):
        calls, mgmt, query = self.run()
        report = refresh_search_index(mgmt, query, ENDPOINT)
        assert calls[0] == ("mgmt", COPY_COMMAND)
        assert calls[1][0] == "mgmt" and "ai_embeddings" in calls[1][1]
        assert report == {"rows": 441, "missing_embeddings": 0,
                          "refusal_probe_rows": 0, "threshold_ok": True}

    def test_partial_embedding_is_a_loud_failure(self):
        _, mgmt, query = self.run(missing_after=17)
        with pytest.raises(SearchIndexError, match="17 of 441"):
            refresh_search_index(mgmt, query, ENDPOINT)

    def test_refusal_probe_reported_never_acted_on(self):
        # nonzero junk matches = threshold needs recalibration; the
        # refresh still succeeds and REPORTS it — a judgment call
        _, mgmt, query = self.run(refusal_rows=2)
        report = refresh_search_index(mgmt, query, ENDPOINT)
        assert report["refusal_probe_rows"] == 2
        assert report["threshold_ok"] is False
