"""Ops flow: materialize — runs a lens and lands its stamped surface.

OPS-1: materialized surfaces are REGENERABLE + STAMPED — a cache with
a witness, never a second truth. The surface node carries the lens
name, version stamp, graph-state stamp, and the result; regenerating
it is calling the same pure lens again. Retire-and-replace on rerun
(the technical-layer supersede pattern; the store keeps the history).
"""
from typing import Any, Dict

from aivia.lenses import registry


def run(store, read, lens_name: str, occurred_at: str,
        params: Dict[str, Any] = None) -> Dict[str, Any]:
    fn = registry.V1_LENSES.get(lens_name)
    if fn is None:
        raise KeyError(f"'{lens_name}' is not a v1 catalog lens — "
                       "materialization follows the catalog, not code")
    result = fn(read, params)
    # literal: shape
    surface = {"lens": lens_name, "result": result,
               "graph_stamp": list(read.stamp()),
               "occurred_at": occurred_at}
    store.append_node("report_surface", f"surface:{lens_name}", surface,
                      occurred_at, f"materialize@{occurred_at}")
    return surface
