"""Unit tests for graph builder."""

from src.graph.builder import GraphBuilder
from src.models import NodeLayer
from src.parser.sql_parser import parse_sql


class TestGraphBuilder:
    def test_add_technical_node(self):
        gb = GraphBuilder()
        node_id = gb.add_technical_node("encounter", "admit_dt", "Admission date")
        assert node_id == "tech:DBO.ENCOUNTER.ADMIT_DT"
        assert gb.nodes[node_id].layer == NodeLayer.TECHNICAL
        assert gb.nodes[node_id].properties["schema"] == "dbo"

    def test_add_technical_node_with_schema(self):
        gb = GraphBuilder()
        node_id = gb.add_technical_node("encounter", schema="reporting", description="Encounters")
        assert node_id == "tech:REPORTING.ENCOUNTER"
        assert gb.nodes[node_id].properties["schema"] == "reporting"

    def test_column_nodes_are_wired_to_their_table(self):
        """Column nodes must be reachable by traversal, not just by name."""
        gb = GraphBuilder()
        col_id = gb.add_technical_node("encounter", "admit_dt", "Admission date")
        edge_pairs = [(e.source_id, e.target_id, e.edge_type.value) for e in gb.edges]
        assert ("tech:DBO.ENCOUNTER", col_id, "table_to_column") in edge_pairs
        # Parent table node was auto-created
        assert "tech:DBO.ENCOUNTER" in gb.nodes
        # Re-adding the column must not duplicate the edge
        gb.add_technical_node("encounter", "admit_dt")
        assert len(gb.edges) == 1

    def test_case_variants_resolve_to_one_node(self):
        """Dictionary case and SQL case must meet at the same node (ADR 0016)."""
        gb = GraphBuilder()
        dict_id = gb.add_technical_node("ENCOUNTER", description="Patient encounters")
        sql_id = gb.add_technical_node("encounter")
        assert dict_id == sql_id == "tech:DBO.ENCOUNTER"
        # First writer's description survives; display name preserved
        assert gb.nodes[dict_id].description == "Patient encounters"
        assert gb.nodes[dict_id].name == "ENCOUNTER"

    def test_add_canonical_node(self):
        gb = GraphBuilder()
        node_id = gb.add_canonical_node("ER_LOS", "ER Length of Stay", steward="Dr. Smith")
        assert node_id == "canonical:ER_LOS"
        assert gb.nodes[node_id].properties["steward"] == "Dr. Smith"

    def test_build_from_parsed_sql(self):
        gb = GraphBuilder()

        # Set up prerequisite nodes
        gb.add_canonical_node("ER_LOS", "ER Length of Stay")
        gb.add_technical_node("encounter")
        gb.add_technical_node("department")

        sql = """
        WITH er_visits AS (
            SELECT e.encounter_id, e.admit_dt
            FROM encounter e
            INNER JOIN department d ON e.department_id = d.department_id
        ),
        los_calc AS (
            SELECT encounter_id, DATEDIFF(MINUTE, admit_dt, discharge_dt) / 60.0 AS los_hours
            FROM er_visits
        )
        SELECT AVG(los_hours) FROM los_calc
        """
        parsed = parse_sql(sql)
        gb.build_from_parsed_sql("ER_LOS", parsed)

        # Should have transformation nodes for both CTEs
        assert "transform:ER_LOS:er_visits" in gb.nodes
        assert "transform:ER_LOS:los_calc" in gb.nodes

        # Declaration order persists as the customer-facing step number
        # (T-SQL declares CTEs before use, so this IS the logical order)
        assert gb.nodes["transform:ER_LOS:er_visits"].properties["step_no"] == 1
        assert gb.nodes["transform:ER_LOS:los_calc"].properties["step_no"] == 2

        # Should have edges
        assert len(gb.edges) > 0


class TestProjectionEdges:
    """ADR 0053 (ordered by Sunny, 2026-08-22): projection-grain
    column lineage — transform→column edges minted resolved-only,
    every ref conserved into minted or a counted drop reason."""

    def _builder(self):
        from src.graph.builder import GraphBuilder
        b = GraphBuilder()
        b.add_technical_node("IP_SEPSIS", schema="dbo")
        b.add_technical_node("IP_SEPSIS", column="PATIENTMRN",
                             schema="dbo")
        b.add_technical_node("IP_SEPSIS", column="SepsisDX",
                             schema="dbo")
        b.add_technical_node("ADT_EVENTS", schema="dbo")
        b.add_technical_node("ADT_EVENTS", column="SepsisDX",
                             schema="dbo")
        return b

    def _refs(self, *pairs):
        from src.parser.sql_parser import ColumnRef
        return [ColumnRef(table=t, column=c) for t, c in pairs]

    def _tables(self, *names):
        from src.parser.sql_parser import TableRef
        return [TableRef(table=n, schema="dbo") for n in names]

    def test_qualified_ref_mints_one_edge(self):
        from src.models import EdgeType
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("IP_SEPSIS", "PATIENTMRN")),
            self._tables("IP_SEPSIS"))
        edges = [e for e in b.edges
                 if e.edge_type == EdgeType.TRANSFORM_TO_COLUMN]
        assert len(edges) == 1
        assert edges[0].target_id.endswith(".PATIENTMRN")
        assert b.projection_minted == 1 and b.projection_refs == 1

    def test_unqualified_unique_resolves(self):
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs((None, "PATIENTMRN")),
            self._tables("IP_SEPSIS", "ADT_EVENTS"))
        assert b.projection_minted == 1     # only IP_SEPSIS has it

    def test_ambiguous_unqualified_drops_counted(self):
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs((None, "SepsisDX")),
            self._tables("IP_SEPSIS", "ADT_EVENTS"))
        assert b.projection_minted == 0
        assert b.projection_dropped == {"ambiguous": 1}

    def test_alias_qualifier_drops_counted(self):
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("X", "PATIENTMRN")),
            self._tables("IP_SEPSIS"))
        assert b.projection_dropped == {"unresolved_qualifier": 1}


class TestProjectionResolverW13:
    """W13a (walk 1562, ED_DEPARTURE_TIME false empty): the resolver's
    two new classes — alias resolution (qualifiers are aliases in real
    SQL, not table names) and the step-projection chase (a ref
    qualified through a temp/CTE step attributes to the source column
    that step projected, when unique)."""

    _builder = TestProjectionEdges._builder
    _refs = TestProjectionEdges._refs
    _tables = TestProjectionEdges._tables

    def test_alias_resolves_to_dictionary_table(self):
        # HE.PATIENTMRN with HE aliased to IP_SEPSIS — the exact
        # corpse shape (qual matched table NAMES only, dropped)
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("HE", "PATIENTMRN")),
            self._tables("IP_SEPSIS"),
            aliases={"HE": ("dbo", "IP_SEPSIS")})
        assert b.projection_minted == 1
        assert b.projection_dropped == {}

    def test_alias_to_table_outside_step_refs_still_resolves(self):
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("A", "SepsisDX")),
            self._tables("IP_SEPSIS"),          # ADT not in step refs
            aliases={"A": ("dbo", "ADT_EVENTS")})
        assert b.projection_minted == 1
        [e] = [e for e in b.edges
               if str(e.edge_type).endswith("TRANSFORM_TO_COLUMN")]
        assert "ADT_EVENTS" in e.target_id

    def test_step_chase_attributes_source_column(self):
        # step s1 projects PATIENTMRN from IP_SEPSIS; a later step's
        # bp.PATIENTMRN (bp -> #Base_Pop = s1) chases to the source
        b = self._builder()
        sbf = {"BASE_POP": "transform:m:Base_Pop"}
        b.mint_projection_edges(
            "transform:m:Base_Pop",
            self._refs(("IP_SEPSIS", "PATIENTMRN")),
            self._tables("IP_SEPSIS"), step_by_fold=sbf)
        b.mint_projection_edges(
            "transform:m:s2",
            self._refs(("BP", "PATIENTMRN")),
            self._tables(), aliases={"BP": ("dbo", "#Base_Pop")},
            step_by_fold=sbf)
        assert b.projection_minted == 2
        assert b.projection_minted_via_step == 1
        targets = {e.target_id for e in b.edges
                   if e.source_id == "transform:m:s2"}
        assert any(t.endswith(".PATIENTMRN") for t in targets)

    def test_step_chase_untracked_and_ambiguous_are_counted(self):
        b = self._builder()
        sbf = {"BASE_POP": "transform:m:Base_Pop"}
        # untracked: the step never projected the column
        b.mint_projection_edges(
            "transform:m:s2", self._refs(("#Base_Pop", "SepsisDX")),
            self._tables(), step_by_fold=sbf)
        assert b.projection_dropped == {"step_projection_untracked": 1}
        # ambiguous: the step projected the fold from TWO sources
        b.projection_by_step["transform:m:Base_Pop"] = {
            "SEPSISDX": {"tech:DBO.IP_SEPSIS.SEPSISDX",
                         "tech:DBO.ADT_EVENTS.SEPSISDX"}}
        b.mint_projection_edges(
            "transform:m:s3", self._refs(("#Base_Pop", "SepsisDX")),
            self._tables(), step_by_fold=sbf)
        assert b.projection_dropped["step_projection_ambiguous"] == 1

    def test_conservation_holds_across_new_buckets(self):
        b = self._builder()
        sbf = {"BASE_POP": "transform:m:Base_Pop"}
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("HE", "PATIENTMRN"), ("X", "SepsisDX"),
                       ("#Base_Pop", "SepsisDX"), (None, "SepsisDX")),
            self._tables("IP_SEPSIS", "ADT_EVENTS"),
            aliases={"HE": ("dbo", "IP_SEPSIS")}, step_by_fold=sbf)
        assert b.projection_refs == 4
        assert (b.projection_minted
                + sum(b.projection_dropped.values())) == 4

    def test_duplicate_and_unknown_column_conserve(self):
        b = self._builder()
        b.mint_projection_edges(
            "transform:m:s1",
            self._refs(("IP_SEPSIS", "PATIENTMRN"),
                       ("IP_SEPSIS", "PATIENTMRN"),
                       ("IP_SEPSIS", "NOPE")),
            self._tables("IP_SEPSIS"))
        assert b.projection_refs == 3
        assert b.projection_minted == 1
        assert b.projection_dropped == {"duplicate": 1,
                                        "no_dictionary_column": 1}
        assert b.projection_refs == (b.projection_minted
                                     + sum(b.projection_dropped.values()))
