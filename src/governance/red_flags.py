"""ADR 0054 — the governance red-flag sweep (governed plurality).

Names are claims; parsed logic is truth. The sweep detects machine
contradictions between identity claims and normalized parsed logic:

- MISNOMER: one claim, many truths — same name, divergent hashes.
- DUPLICATE: many claims, one truth — different names, same hash.
- COUSIN CONFLICT: near-claims (strict token-containment families —
  'Sepsis Patient Timeline' ⊂ 'Sepsis Patient Timeline (Legacy v1)'),
  divergent hashes. Containment tokenization only — no similarity
  metrics, no lexicons (M4).

Hash provenance: the compare kernel's `_content_key` (ADR 0036,
ScriptDom-normalized fragment) IMPORTED, never re-implemented. Metric
grain hashes the ordered step keys. Deterministic and replayable
(spec:E2) — flag ids are pure functions of class+grain+identity; NO
LLM anywhere in the decision path.

Conservation (principle 7, total-or-lying): every swept item lands in
exactly one of clean ⊎ flagged ⊎ excluded(reason); the partition is
asserted by the build step and re-asserted by the live audit.

Flags disclose, never gate (principle 6). Severity per the RATIFIED
boundary table: step names are proc-local claims → INFO; shared-scope
identities (business names, certified metrics) → CONFLICT on
divergence; duplicates are INFO everywhere (nothing contradicts — the
debt is the missing link); cousins CONFLICT when hashes diverge, INFO
when aligned.

Dispositions are APPEND-ONLY events (ADR 0023): certify /
label-variant / retire / accept; reason MANDATORY on accept and
retire (RATIFIED). apply_dispositions folds events into flag states
and mints the typed edges (variant_of / supersedes / duplicate_of)
and official-for-scope properties — the write SURFACE that emits
events plan-confirms per ADR 0050 and ships separately.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from src.orchestrator.tools import _content_key
from src.parser.identity import fold_identifier

FLAG_CLASSES = ("misnomer", "duplicate", "cousin_conflict",
                # D7 grain (ratified 2026-08-25): same name, mixed
                # DISTINCT-ness — "counts patients vs counts visits"
                "grain_shift")
SEVERITIES = ("INFO", "CONFLICT")
DISPOSITIONS = ("certify", "label-variant", "retire", "accept")
# reason is MANDATORY on these (RATIFIED 2026-08-23)
_REASON_REQUIRED = ("retire", "accept")
_TOKEN = re.compile(r"[A-Za-z0-9]+")


@dataclass
class SweepResult:
    flags_rows: "list[dict]" = field(default_factory=list)
    # ADR 0057 "Clusters are nodes" (Sunny's demo law, 2026-08-25):
    # the GRAPH is the sole flag truth — reified name_cluster and
    # logic_group nodes with member_of edges, emitted by the sweep
    # and merged into graph_nodes/graph_edges by build_graph_step
    # (fold-into-300; single writer). flags_rows above is the SAME
    # verdict set in row form — derived representation for summaries
    # and the disposition fold, never a second store.
    cluster_nodes_rows: "list[dict]" = field(default_factory=list)
    cluster_edges_rows: "list[dict]" = field(default_factory=list)
    # conservation partition, per grain
    swept: int = 0
    flagged: int = 0
    clean: int = 0
    excluded: "dict[str, int]" = field(default_factory=dict)

    def assert_conservation(self) -> None:
        total = self.flagged + self.clean + sum(self.excluded.values())
        assert total == self.swept, (
            f"red-flag sweep conservation broken: swept {self.swept} "
            f"!= flagged {self.flagged} + clean {self.clean} + "
            f"excluded {self.excluded}")
        # cluster reification conservation: one cluster node per flag,
        # one logic_group per distinct content key, one member_of per
        # member + one per group
        n_clusters = sum(
            1 for n in self.cluster_nodes_rows
            if json.loads(n["properties"]).get("kind") == "name_cluster")
        assert n_clusters == len(self.flags_rows), (
            f"cluster reification broken: {n_clusters} cluster nodes "
            f"!= {len(self.flags_rows)} flags")


def _props(row: dict) -> dict:
    p = row.get("properties") or {}
    if isinstance(p, str):
        p = json.loads(p or "{}")
    return p or {}


def _fold_name(name: str) -> str:
    return fold_identifier(str(name).replace(" ", "_"))


def _tokens(name: str) -> "frozenset[str]":
    return frozenset(t.casefold() for t in _TOKEN.findall(str(name))
                     if len(t) >= 2)


def _flag_id(flag_class: str, grain: str, identity: str) -> str:
    tail = hashlib.sha256(
        f"{flag_class}|{grain}|{identity.casefold()}".encode()
    ).hexdigest()[:12]
    return f"cluster:{flag_class}:{grain}:{tail}"


def _drill(flag_id: str) -> str:
    # graph-native (ADR 0057): the drill traverses membership edges
    return (f"graph_edges | where target_id == '{flag_id}' "
            "and edge_type == 'member_of' "
            "| join kind=inner (graph_edges "
            "| where edge_type == 'member_of') "
            "on $left.source_id == $right.target_id")


# D7 grain (ratified 2026-08-25): machine-detectable, structural —
# SELECT DISTINCT on the output. "Counts patients vs counts visits"
# is a DISTINCT-ness difference between same-named definitions; no
# column lexicon, no domain knowledge (M4 holds).
_DISTINCT = re.compile(r"(?is)\bSELECT\s+DISTINCT\b")


def _grain_signature(fragment: str) -> str:
    return "distinct" if _DISTINCT.search(fragment or "") else "row"


def _row(flag_class: str, grain: str, identity: str, severity: str,
         scope: str, members: "list[dict]", blast: int,
         blast_basis: str) -> dict:
    fid = _flag_id(flag_class, grain, identity)
    distinct = len({m["content_key"] for m in members})
    return {
        "flag_id": fid,
        "flag_class": flag_class,
        "grain": grain,
        "identity": identity,
        "severity": severity,
        "scope": scope,
        "member_count": len(members),
        "distinct_logics": distinct,
        "members": json.dumps(sorted(
            members, key=lambda m: str(m.get("id")))[:50]),
        "members_total": len(members),
        "blast_radius": blast,
        "blast_basis": blast_basis,
        "drill_query": _drill(fid),
        "disposition": "open",
        "disposition_reason": "",
    }


def sweep(nodes_rows: "list[dict]",
          edges_rows: "list[dict]") -> SweepResult:
    """The sweep at CATALOG grain, a pure read over the built graph
    (no new parse). Two artifact classes per the ADR's §3b inventory:
    transformation steps and canonical metrics."""
    res = SweepResult()

    # ---- inputs ------------------------------------------------------
    steps: "list[dict]" = []
    metrics: "list[dict]" = []
    for n in nodes_rows:
        nid = str(n.get("node_id") or "")
        if nid.startswith("transform:"):
            steps.append(n)
        elif nid.startswith("canonical:"):
            metrics.append(n)

    reports_of: "dict[str, int]" = {}
    for e in edges_rows:
        if str(e.get("edge_type")) == "report_to_canonical":
            ref = str(e.get("target_id", "")).split(":", 1)[-1]
            reports_of[ref] = reports_of.get(ref, 0) + 1

    # ---- step grain --------------------------------------------------
    step_items: "list[dict]" = []          # id, name, ref, content_key
    res.swept += len(steps)
    for n in steps:
        p = _props(n)
        frag = str(p.get("sql_fragment") or "")
        if not frag.strip():
            res.excluded["no_fragment"] = (
                res.excluded.get("no_fragment", 0) + 1)
            continue
        step_items.append({
            "id": str(n["node_id"]),
            "name": str(n.get("name") or ""),
            "ref": str(p.get("metric_id") or ""),
            "content_key": _content_key(frag),
        })

    by_step_name: "dict[str, list[dict]]" = {}
    for it in step_items:
        by_step_name.setdefault(_fold_name(it["name"]), []).append(it)
    flagged_ids: "set[str]" = set()
    for _fold, group in sorted(by_step_name.items()):
        if len({g["content_key"] for g in group}) > 1:
            parents = sorted({g["ref"] for g in group if g["ref"]})
            res.flags_rows.append(_row(
                "misnomer", "step", group[0]["name"], "INFO",
                "proc-local", group, len(parents),
                f"{len(parents)} parent metric(s) share the step name"))
            flagged_ids.update(g["id"] for g in group)

    by_step_hash: "dict[str, list[dict]]" = {}
    for it in step_items:
        by_step_hash.setdefault(it["content_key"], []).append(it)
    for key, group in sorted(by_step_hash.items()):
        names = {_fold_name(g["name"]) for g in group}
        if len(names) > 1:
            parents = sorted({g["ref"] for g in group if g["ref"]})
            res.flags_rows.append(_row(
                "duplicate", "step",
                " / ".join(sorted({g["name"] for g in group})[:4]),
                "INFO", "proc-local", group, len(parents),
                f"{len(parents)} parent metric(s) hold identical logic "
                "under different step names"))
            flagged_ids.update(g["id"] for g in group)

    # ---- metric grain ------------------------------------------------
    steps_of: "dict[str, list[tuple]]" = {}
    for n in steps:
        p = _props(n)
        ref = str(p.get("metric_id") or "")
        frag = str(p.get("sql_fragment") or "")
        if ref and frag.strip():
            steps_of.setdefault(ref, []).append(
                (int(p.get("step_no") or 0), _content_key(frag)))

    metric_items: "list[dict]" = []
    res.swept += len(metrics)
    for n in metrics:
        ref = str(n["node_id"]).split(":", 1)[-1]
        keys = [k for _, k in sorted(steps_of.get(ref, []))]
        if not keys:
            res.excluded["unparsed"] = (
                res.excluded.get("unparsed", 0) + 1)
            continue
        p = _props(n)
        display = str(p.get("business_name") or n.get("name") or ref)
        metric_items.append({
            "id": ref,
            "name": display,
            "ref": ref,
            "content_key": hashlib.sha256(
                "|".join(keys).encode()).hexdigest()[:16],
        })

    by_metric_name: "dict[str, list[dict]]" = {}
    for it in metric_items:
        by_metric_name.setdefault(_fold_name(it["name"]), []).append(it)
    for _fold, group in sorted(by_metric_name.items()):
        if len(group) > 1 and len({g["content_key"] for g in group}) > 1:
            blast = sum(reports_of.get(g["ref"], 0) for g in group)
            res.flags_rows.append(_row(
                "misnomer", "metric", group[0]["name"], "CONFLICT",
                "catalog", group, blast,
                f"{blast} linked report(s) across the colliding "
                "metrics"))
            flagged_ids.update(g["id"] for g in group)

    by_metric_hash: "dict[str, list[dict]]" = {}
    for it in metric_items:
        by_metric_hash.setdefault(it["content_key"], []).append(it)
    for key, group in sorted(by_metric_hash.items()):
        if len({_fold_name(g["name"]) for g in group}) > 1:
            blast = sum(reports_of.get(g["ref"], 0) for g in group)
            res.flags_rows.append(_row(
                "duplicate", "metric",
                " / ".join(sorted({g["name"] for g in group})[:4]),
                "INFO", "catalog", group, blast,
                f"{blast} linked report(s) across the duplicates"))
            flagged_ids.update(g["id"] for g in group)

    # cousins: strict token-containment families (A's tokens a proper
    # subset of B's — the Legacy-v1 shape), grouped under the minimal
    # (root) name
    fams: "dict[str, list[dict]]" = {}
    for a in metric_items:
        ta = _tokens(a["name"])
        for b in metric_items:
            if a is b:
                continue
            tb = _tokens(b["name"])
            if ta and ta < tb:
                fams.setdefault(a["name"], []).append(b)
    for root_name, cousins in sorted(fams.items()):
        root = next(i for i in metric_items if i["name"] == root_name)
        group = [root] + sorted(cousins, key=lambda m: m["name"])
        diverge = len({g["content_key"] for g in group}) > 1
        blast = sum(reports_of.get(g["ref"], 0) for g in group)
        res.flags_rows.append(_row(
            "cousin_conflict", "metric", root_name,
            "CONFLICT" if diverge else "INFO", "catalog", group, blast,
            f"{blast} linked report(s) across the name family"))
        flagged_ids.update(g["id"] for g in group)

    all_items = step_items + metric_items
    res.flagged = sum(1 for i in all_items if i["id"] in flagged_ids)
    res.clean = len(all_items) - res.flagged
    res.assert_conservation()
    return res


# ---- dispositions (append-only fold; the write surface plan-confirms
# per ADR 0050 and ships separately) ----------------------------------

@dataclass
class DispositionOutcome:
    flags_rows: "list[dict]"
    minted_edges: "list[tuple]" = field(default_factory=list)
    official_props: "list[dict]" = field(default_factory=list)
    rejected: "list[dict]" = field(default_factory=list)


def apply_dispositions(flags_rows: "list[dict]",
                       events: "list[dict]") -> DispositionOutcome:
    """Fold append-only disposition events (in order) into flag
    states. Rejections are DATA, never silent: unknown flag, unknown
    kind, or a missing mandatory reason each yields a rejected row
    with its reason."""
    by_id = {r["flag_id"]: dict(r) for r in flags_rows}
    out = DispositionOutcome(flags_rows=[])
    for ev in events:
        fid = str(ev.get("flag_id") or "")
        kind = str(ev.get("kind") or "")
        reason = str(ev.get("reason") or "").strip()
        if fid not in by_id:
            out.rejected.append({**ev, "rejected": "unknown flag_id"})
            continue
        if kind not in DISPOSITIONS:
            out.rejected.append({**ev, "rejected":
                                 f"unknown disposition {kind!r}"})
            continue
        if kind in _REASON_REQUIRED and not reason:
            out.rejected.append({**ev, "rejected":
                                 f"reason is MANDATORY on {kind}"})
            continue
        row = by_id[fid]
        row["disposition"] = kind
        row["disposition_reason"] = reason
        if kind == "certify":
            out.official_props.append({
                "node_ref": str(ev.get("member") or ""),
                "official_for_scope": str(ev.get("scope") or "catalog"),
                "steward": str(ev.get("actor") or ""),
                "at": str(ev.get("at") or ""),
            })
        elif kind == "label-variant":
            out.minted_edges.append((str(ev.get("member") or ""),
                                     str(ev.get("official") or ""),
                                     "variant_of"))
        elif kind == "retire":
            out.minted_edges.append((str(ev.get("official") or ""),
                                     str(ev.get("member") or ""),
                                     "supersedes"))
            out.minted_edges.append((str(ev.get("member") or ""),
                                     str(ev.get("official") or ""),
                                     "duplicate_of"))
    out.flags_rows = list(by_id.values())
    return out
