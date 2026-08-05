"""Deterministic traversal templates over the LPG export tables (ADR 0017).

The pre-shaped path templates the resolve-then-traverse architecture routes
to after anchor resolution. Pure functions over export_step() output — the
reference semantics for what each question shape MEANS, testable against
the certified answer key with no LLM and no Fabric. When a platform agent
disagrees with these, the platform layer is at fault.

All lookups fold case (ADR 0016); user-facing keys come from resolution,
but a correct key in the wrong case must still land.
"""

from __future__ import annotations


def _fold(value: "str | None") -> str:
    return (value or "").upper()


class GraphView:
    """Query view over the exported LPG tables (plain dict rows, no engine)."""

    def __init__(self, tables: "dict[str, list[dict]]") -> None:
        self._canonical = tables["graph_canonical"]
        self._transformation = tables["graph_transformation"]
        self._technical = tables["graph_technical"]
        self._uses = tables["graph_edge_uses_table"]
        self._c2t = tables["graph_edge_c2t"]
        self._t2t = tables["graph_edge_t2t"]
        self._tab2col = tables["graph_edge_tab2col"]
        self._canonical_by_id = {r["nodeId"]: r for r in self._canonical}
        self._tech_by_id = {r["nodeId"]: r for r in self._technical}
        self._transform_by_id = {r["nodeId"]: r for r in self._transformation}

    # ---- catalogs: resolution inputs. No user string ever filters these ----

    def metric_catalog(self) -> "list[dict]":
        return sorted(
            (
                {k: r.get(k) for k in ("metricId", "name", "description")}
                for r in self._canonical
            ),
            key=lambda r: _fold(r["metricId"]),
        )

    def table_catalog(self) -> "list[dict]":
        seen: set = set()
        out = []
        for r in self._technical:
            if r.get("columnName"):
                continue
            key = (_fold(r.get("schemaName")), _fold(r["tableName"]))
            if key in seen:
                continue
            seen.add(key)
            out.append({"schemaName": r.get("schemaName"), "tableName": r["tableName"]})
        return sorted(out, key=lambda r: (_fold(r["schemaName"]), _fold(r["tableName"])))

    def transformation_catalog(self) -> "list[dict]":
        return sorted(
            ({"metricId": r["metricId"], "name": r["name"]} for r in self._transformation),
            key=lambda r: (_fold(r["metricId"]), _fold(r["name"])),
        )

    # ---- resolution helpers (fold-exact; semantic matching is the LLM's job) ----

    def find_metrics(self, reference: str) -> "list[dict]":
        """All catalog rows whose metricId OR bare name fold-matches the
        reference. A qualified reference hits one row; a bare name may hit
        several schemas — the caller surfaces ambiguity, never guesses."""
        folded = _fold(reference)
        return [
            r for r in self.metric_catalog()
            if _fold(r["metricId"]) == folded or _fold(r["name"]) == folded
        ]

    def _metric_node_id(self, metric_id: str) -> "str | None":
        folded = _fold(metric_id)
        for r in self._canonical:
            if _fold(r["metricId"]) == folded:
                return r["nodeId"]
        return None

    def _table_node_ids(self, table_name: str) -> "set[str]":
        folded = _fold(table_name)
        return {
            r["nodeId"] for r in self._technical
            if not r.get("columnName") and _fold(r["tableName"]) == folded
        }

    # ---- templates ----

    def tables_of_metric(self, metric_id: str) -> "list[dict]":
        """Which tables does metric M use? — USES_TABLE closure, single hop."""
        node_id = self._metric_node_id(metric_id)
        if node_id is None:
            return []
        rows = [
            self._tech_by_id[e["targetId"]]
            for e in self._uses if e["sourceId"] == node_id
        ]
        return sorted(rows, key=lambda r: (_fold(r.get("schemaName")), _fold(r["tableName"])))

    def metrics_of_table(self, table_name: str) -> "list[dict]":
        """Which metrics read table T? — USES_TABLE reversed, single hop."""
        targets = self._table_node_ids(table_name)
        sources = {e["sourceId"] for e in self._uses if e["targetId"] in targets}
        rows = [self._canonical_by_id[s] for s in sources]
        return sorted(rows, key=lambda r: _fold(r["metricId"]))

    def shared_source_metrics(self, metric_id: str) -> "list[dict]":
        """Which metrics share source tables with M? — two USES_TABLE hops."""
        node_id = self._metric_node_id(metric_id)
        if node_id is None:
            return []
        mine = {e["targetId"] for e in self._uses if e["sourceId"] == node_id}
        counts: "dict[str, int]" = {}
        for e in self._uses:
            if e["sourceId"] != node_id and e["targetId"] in mine:
                counts[e["sourceId"]] = counts.get(e["sourceId"], 0) + 1
        rows = [
            {**self._canonical_by_id[s], "sharedTables": n}
            for s, n in counts.items()
        ]
        return sorted(rows, key=lambda r: (-r["sharedTables"], _fold(r["metricId"])))

    def columns_of_table(self, table_name: str) -> "list[dict]":
        """Which columns does table T have? — HAS_COLUMN from the table node."""
        tables = self._table_node_ids(table_name)
        cols = [
            self._tech_by_id[e["targetId"]]
            for e in self._tab2col if e["sourceId"] in tables
        ]
        return sorted(cols, key=lambda r: _fold(r.get("columnName")))

    def steps_of_metric(self, metric_id: str) -> "list[dict]":
        """How is M calculated? — root steps, then the DEPENDS_ON closure
        in breadth-first order (roots first, assembly before detail)."""
        node_id = self._metric_node_id(metric_id)
        if node_id is None:
            return []
        frontier = [e["targetId"] for e in self._c2t if e["sourceId"] == node_id]
        seen: "set[str]" = set()
        ordered: "list[str]" = []
        while frontier:
            nxt: "list[str]" = []
            for step in frontier:
                if step in seen:
                    continue
                seen.add(step)
                ordered.append(step)
                nxt.extend(e["targetId"] for e in self._t2t if e["sourceId"] == step)
            frontier = nxt
        return [self._transform_by_id[s] for s in ordered if s in self._transform_by_id]

    def most_read_metrics(self, top: int = 3) -> "list[dict]":
        """Which metric reads the most tables? — aggregation over USES_TABLE."""
        counts: "dict[str, int]" = {}
        for e in self._uses:
            counts[e["sourceId"]] = counts.get(e["sourceId"], 0) + 1
        rows = [
            {**self._canonical_by_id[s], "tableCount": n} for s, n in counts.items()
        ]
        rows.sort(key=lambda r: (-r["tableCount"], _fold(r["metricId"])))
        return rows[:top]
