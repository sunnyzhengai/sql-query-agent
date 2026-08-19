"""replan: the registry-derived re-run advisor. The acceptance case is
the real 2026-08-18 incident — the hand-derived list omitted 600 and
wiped the demo tenant's descriptions; replan must never repeat it."""

from src.replan import replan, replan_lines


def _names(changed):
    return [a.notebook for a in replan(changed)]


class TestTheIncident:
    def test_metric_names_change_includes_600(self):
        """The exact miss: names -> graph rebuild -> 600's enrichment
        wiped -> 600 MUST run (near-free via cache, but must run)."""
        nbs = _names({"input_metric_names"})
        for required in ("300_build_graph", "400_build_metric_logic",
                         "500_validate", "600_generate_descriptions",
                         "700_refresh_search_index",
                         "800_export_graph_tables"):
            assert required in nbs, f"missing {required}"

    def test_parse_not_required_for_a_names_change(self):
        assert "200_parse" not in _names({"input_metric_names"})

    def test_enrichment_reason_is_stated(self):
        advice = {a.notebook: a for a in replan({"input_metric_names"})}
        a600 = advice["600_generate_descriptions"]
        # 600 is pulled either as consumer or via enrichment-wipe — the
        # reason must name a concrete cause, never be empty
        assert a600.reason


class TestPropagation:
    def test_corpus_change_starts_at_parse(self):
        nbs = _names({"input_sql_sources"})
        assert "200_parse" in nbs
        assert "300_build_graph" in nbs        # transitive via parse outputs
        assert "800_export_graph_tables" in nbs

    def test_dictionary_change_skips_parse(self):
        nbs = _names({"input_dict_tables"})
        assert "200_parse" not in nbs
        assert "300_build_graph" in nbs

    def test_ordering_is_execution_order(self):
        nbs = _names({"input_sql_sources"})
        assert nbs == sorted(nbs)  # century scheme: lexicographic = run order

    def test_publishers_are_listed_not_hidden(self):
        nbs = _names({"input_sql_sources"})
        assert any(n.startswith("9") for n in nbs), (
            "publishers consume dirty outputs — the advisory must list "
            "them (annotated), never silently drop them")

    def test_no_consumers_is_honest(self):
        lines = replan_lines({"nonexistent_table"})
        assert "no notebook consumes" in lines[0]

    def test_deterministic(self):
        assert _names({"input_sql_sources"}) == _names({"input_sql_sources"})
