"""The diff kernel — step-aligned comparison of metric decompositions.

Family F of the Question Map ("are these definitions the same? WHY do
A and B disagree?") is the founding demo question and was the least-
served shape: the content-hash partition kernel says THAT two metrics
differ; this kernel says WHERE — aligned step pairs, missing steps,
differing fragments, differing source tables. Deterministic; composes
as search -> retrieve xN -> diff (ADR 0037/0043); the LLM captions the
result and NEVER judges equivalence itself — the kernel's output IS
the evidence (ADR 0032).

Alignment strategy (HANDOFF_COMPARISON_SHAPE): steps match by folded
NAME first; then by identical fragment CONTENT (a renamed-but-identical
step is a match, not two findings); then by TABLE-SET similarity
(Jaccard) where table sets are known. Unmatched steps are themselves
findings, never noise.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecompStep:
    name: str
    fragment: str = ""
    tables: "frozenset[str]" = frozenset()


@dataclass
class Decomposition:
    entity_id: str
    steps: "list[DecompStep]" = field(default_factory=list)


def _content_key(text: str) -> str:
    """Whitespace/case-forgiven content identity (same forgiveness as
    the partition kernel — the two kernels must never disagree on
    'identical')."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _jaccard(a: "frozenset[str]", b: "frozenset[str]") -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _fragment_diff(a: str, b: str, cap: int = 14) -> "list[str]":
    lines = list(difflib.unified_diff(
        (a or "").splitlines(), (b or "").splitlines(),
        lineterm="", n=1))[2:]  # drop ---/+++ headers
    if len(lines) > cap:
        lines = lines[:cap] + [f"... ({len(lines) - cap} more diff lines)"]
    return lines


@dataclass
class AlignedPair:
    a_name: str
    b_name: str
    matched_by: str            # "name" | "content" | "tables"
    fragment_identical: bool
    tables_only_in_a: "list[str]"
    tables_only_in_b: "list[str]"
    fragment_diff: "list[str]"

    @property
    def divergent(self) -> bool:
        return (not self.fragment_identical or bool(self.tables_only_in_a)
                or bool(self.tables_only_in_b))


@dataclass
class DiffResult:
    a_id: str
    b_id: str
    aligned: "list[AlignedPair]"
    only_in_a: "list[str]"     # step names with no counterpart
    only_in_b: "list[str]"

    @property
    def identical(self) -> bool:
        return (not self.only_in_a and not self.only_in_b
                and all(not p.divergent for p in self.aligned))

    def rows(self) -> "list[dict]":
        """Display-shaped evidence rows (the answer; prose captions it)."""
        divergent = [p for p in self.aligned if p.divergent]
        out: "list[dict]" = [{
            "verdict": "identical" if self.identical else "divergent",
            "aligned_steps": len(self.aligned),
            "divergent_steps": len(divergent),
            "steps_only_in": {self.a_id: self.only_in_a,
                              self.b_id: self.only_in_b},
        }]
        for p in divergent:
            row = {"step": {self.a_id: p.a_name, self.b_id: p.b_name},
                   "matched_by": p.matched_by,
                   "fragment_identical": p.fragment_identical}
            if p.tables_only_in_a or p.tables_only_in_b:
                row["tables_only_in"] = {self.a_id: p.tables_only_in_a,
                                         self.b_id: p.tables_only_in_b}
            if p.fragment_diff:
                row["fragment_diff"] = p.fragment_diff
            out.append(row)
        return out

    def summary_line(self) -> str:
        if self.identical:
            return (f"{self.a_id} and {self.b_id}: identical decomposition "
                    f"({len(self.aligned)} aligned steps)")
        divergent = sum(1 for p in self.aligned if p.divergent)
        bits = []
        if divergent:
            bits.append(f"{divergent} divergent step(s)")
        if self.only_in_a:
            bits.append(f"only in {self.a_id}: {', '.join(self.only_in_a)}")
        if self.only_in_b:
            bits.append(f"only in {self.b_id}: {', '.join(self.only_in_b)}")
        return f"{self.a_id} vs {self.b_id}: " + "; ".join(bits)


_TABLE_MATCH_FLOOR = 0.5  # below half-overlap, a table match is a guess


def diff_decompositions(a: Decomposition, b: Decomposition) -> DiffResult:
    """Deterministic step alignment + divergence extraction."""
    b_free = list(range(len(b.steps)))
    pairs: "list[tuple[int, int, str]]" = []

    def take(bi: int) -> None:
        b_free.remove(bi)

    # pass 1: folded name
    for ai, a_step in enumerate(a.steps):
        for bi in b_free:
            if a_step.name.lower() == b.steps[bi].name.lower():
                pairs.append((ai, bi, "name"))
                take(bi)
                break
    matched_a = {p[0] for p in pairs}

    # pass 2: identical fragment content (renamed step)
    for ai, a_step in enumerate(a.steps):
        if ai in matched_a or not _content_key(a_step.fragment):
            continue
        for bi in b_free:
            if _content_key(a_step.fragment) == _content_key(b.steps[bi].fragment):
                pairs.append((ai, bi, "content"))
                take(bi)
                matched_a.add(ai)
                break

    # pass 3: table-set similarity, best-first, above the floor
    candidates = []
    for ai, a_step in enumerate(a.steps):
        if ai in matched_a or not a_step.tables:
            continue
        for bi in b_free:
            score = _jaccard(a_step.tables, b.steps[bi].tables)
            if score >= _TABLE_MATCH_FLOOR:
                candidates.append((-score, ai, bi))
    for _, ai, bi in sorted(candidates):
        if ai in matched_a or bi not in b_free:
            continue
        pairs.append((ai, bi, "tables"))
        take(bi)
        matched_a.add(ai)

    aligned = []
    for ai, bi, how in sorted(pairs):
        a_step, b_step = a.steps[ai], b.steps[bi]
        same_fragment = _content_key(a_step.fragment) == _content_key(b_step.fragment)
        aligned.append(AlignedPair(
            a_name=a_step.name, b_name=b_step.name, matched_by=how,
            fragment_identical=same_fragment,
            tables_only_in_a=sorted(a_step.tables - b_step.tables),
            tables_only_in_b=sorted(b_step.tables - a_step.tables),
            fragment_diff=([] if same_fragment
                           else _fragment_diff(a_step.fragment, b_step.fragment)),
        ))
    return DiffResult(
        a_id=a.entity_id, b_id=b.entity_id, aligned=aligned,
        only_in_a=[s.name for i, s in enumerate(a.steps) if i not in matched_a],
        only_in_b=[b.steps[i].name for i in b_free],
    )


def diff_many(decomps: "list[Decomposition]") -> "list[DiffResult]":
    """N-way: pairwise against the first (the base is explicit in every
    result — no hidden reference point)."""
    if len(decomps) < 2:
        return []
    base = decomps[0]
    return [diff_decompositions(base, other) for other in decomps[1:]]


# --- builders from the graph ----------------------------------------

def decompositions_from_graph(
    metric_ids: "list[str]",
    nodes_rows: "list[dict]",
    edges_rows: "list[dict]",
) -> "dict[str, Decomposition]":
    """Build step decompositions straight from graph rows: ordered
    transformations (traverser order = CTE chain order) with per-step
    source tables from transform_to_technical edges."""
    import json as _json

    from src.graph.serialization import rows_to_edges, rows_to_nodes
    from src.graph.traversal import GraphTraverser

    nodes = rows_to_nodes(nodes_rows)
    edges = rows_to_edges(edges_rows)
    traverser = GraphTraverser(nodes, edges)

    def _props(raw):
        return _json.loads(raw) if isinstance(raw, str) else (raw or {})

    tables_of: "dict[str, set[str]]" = {}
    node_table = {}
    for r in nodes_rows:
        props = _props(r.get("properties"))
        if r["node_id"].startswith("tech:") and props.get("table") \
                and not props.get("column"):
            node_table[r["node_id"]] = props["table"]
    for e in edges_rows:
        if e.get("edge_type") == "transform_to_technical" \
                and e["target_id"] in node_table:
            tables_of.setdefault(e["source_id"], set()).add(
                node_table[e["target_id"]].upper())

    out: "dict[str, Decomposition]" = {}
    for metric_id in metric_ids:
        sub = traverser.get_metric_subgraph(metric_id)
        steps = []
        for t in (sub.get("transformations") or []):
            steps.append(DecompStep(
                name=t.name,
                fragment=t.properties.get("sql_fragment", "") or "",
                tables=frozenset(tables_of.get(t.node_id, ())),
            ))
        out[metric_id] = Decomposition(entity_id=metric_id, steps=steps)
    return out


# --- doctrine level 3: cached divergence summaries for hot groups ----

def bare_name(metric_id: str) -> str:
    return metric_id.rsplit(".", 1)[-1].lower()


def twin_divergence_rows(
    nodes_rows: "list[dict]", edges_rows: "list[dict]", run_at: str
) -> "list[dict]":
    """Same-bare-name metric groups get a CACHED divergence summary —
    verifiable cache of the kernel (precomputation doctrine level 3),
    because same-name twins are the hot comparison (the founding demo
    question; 25 live pairs at one estate, 16 with different code)."""
    canonical_ids = [r["node_id"].removeprefix("canonical:")
                     for r in nodes_rows
                     if r.get("node_id", "").startswith("canonical:")]
    groups: "dict[str, list[str]]" = {}
    for mid in sorted(canonical_ids):
        groups.setdefault(bare_name(mid), []).append(mid)
    twins = {k: v for k, v in groups.items() if len(v) >= 2}
    if not twins:
        return []

    all_ids = [m for members in twins.values() for m in members]
    decomps = decompositions_from_graph(all_ids, nodes_rows, edges_rows)

    rows: "list[dict]" = []
    for key, members in sorted(twins.items()):
        results = diff_many([decomps[m] for m in members])
        identical = all(r.identical for r in results)
        divergent_steps = sum(
            sum(1 for p in r.aligned if p.divergent) for r in results)
        missing_steps = sum(
            len(r.only_in_a) + len(r.only_in_b) for r in results)
        rows.append({
            "group_key": key,
            "metric_ids": ", ".join(members),
            "member_count": len(members),
            "verdict": "identical" if identical else "divergent",
            "divergent_steps": divergent_steps,
            "missing_steps": missing_steps,
            "summary": " | ".join(r.summary_line() for r in results),
            "computed_at": run_at,
        })
    return rows
