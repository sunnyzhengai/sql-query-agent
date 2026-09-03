"""TERM-PROPOSE-1/2 — a name family becomes a term HIERARCHY
proposal (built 2026-09-04, answer-key-first; the P1 items of the
2026-08-31 build queue).

TERM-PROPOSE-1: one cluster (an OPEN conflict-class flag over
same-named metrics) -> one PARENT CONCEPT term with no proc behind
it + N child terms with distinct names and definitions. The data
contract is landing_registry's `organize_hierarchy` row (A2+A3):
this module adds NOTHING that row does not record.

TERM-PROPOSE-2: the proposal payload = assets + relationships
(term<->proc `governs`, term<->report, steward responsibility per
child, parent-child hierarchy), rendered to the stage-1 FILE-FIRST
shapes (ADR 0063 §2). Attribution is the definition PREFIX from the
zero-schema-footprint ruling — never a column that would become a
custom attribute in the customer's catalog.

Naming is DETERMINISTIC (no LLM anywhere in this module): parent =
the family's shared identity; a child keeps its OWN distinct
business name, and qualifies with its ref when the name collides
with a sibling or the parent concept (the BR-1 mechanism — the
family's whole point is that bare names collide). Definitions are
composed from counted facts plus the
member's own certified description; the only generated sentences
are templates over those facts, self-checked (child count must
equal the count the text claims — the XR-1 reconcile law).

Open items stay open (landing_registry OPEN_ITEMS): Collibra
relation TYPE names here are the registry row's own words
('hierarchical', 'governs', 'responsible') pending Sunny's
operating-model call; canonical-child marking is not proposed.
"""

from __future__ import annotations

from src.branding import product_name
from src.landing_registry import ZERO_SCHEMA_FOOTPRINT

# The native column sets, as data — every rendered row is checked
# against these (zero custom attributes, mechanically). Purview:
# the glossary import CSV's own header. Collibra: Data Intake
# columns; NO Provenance column — attribution rides the prefix.
PURVIEW_TERM_COLUMNS = (
    "Name", "Status", "Definition", "Acronym", "Experts", "Stewards",
    "Parent Term Name", "IsDefinitionRichText")
COLLIBRA_ASSET_COLUMNS = (
    "Name", "Full Name", "Asset Type", "Domain", "Description",
    "Stewards")
COLLIBRA_RELATION_COLUMNS = (
    "Head", "Head Full Name", "Relation", "Tail", "Tail Asset Type")

# organize_hierarchy applies to name families: the conflict classes
# whose flags mean 'this one name carries several meanings' (the
# same frontier BR-1's disclosure cites).
CONFLICT_CLASSES = ("cousin_conflict", "misnomer", "grain_shift")


def attribution_prefix() -> str:
    """The ruled prefix, rendered from the ONE registry record."""
    return ZERO_SCHEMA_FOOTPRINT["attribution_prefix"].format(
        product=product_name())


def _ref(member_id: str) -> str:
    return str(member_id).split(":", 1)[-1]


def propose_hierarchy(cluster: dict, metrics: "dict[str, dict]",
                      reports: "dict[str, list[str]] | None" = None,
                      ) -> dict:
    """TERM-PROPOSE-1: cluster -> the hierarchy proposal payload.

    cluster: {id, identity, flag_class, disposition, member_ids}.
    metrics: ref -> its output_metric_logic row (description,
    steward, developer — the certified graph; this function never
    authors a member's definition).
    reports: ref -> report names (REPORT_TO_CANONICAL edges).
    """
    identity = str(cluster.get("identity") or "")
    refs = [_ref(m) for m in cluster.get("member_ids") or []]
    n = len(refs)
    prefix = attribution_prefix()
    disclosure = (f"One of {n} distinct definitions sharing the "
                  f"name '{identity}'.")
    children = []
    relationships: "list[dict]" = []
    parent_name = identity
    # Deterministic child naming (the _display_names rule at family
    # grain): a member keeps its OWN distinct business name; a name
    # that collides with a sibling OR with the parent concept
    # qualifies with the ref (BR-1).
    bnames = {r: str((metrics.get(r) or {}).get("business_name")
                     or identity) for r in refs}
    counts: "dict[str, int]" = {}
    for b in bnames.values():
        counts[b] = counts.get(b, 0) + 1
    for ref in refs:
        m = metrics.get(ref) or {}
        bare = bnames[ref]
        child_name = (f"{bare} ({ref})"
                      if counts[bare] > 1 or bare == parent_name
                      else bare)
        desc = str(m.get("description") or "").strip()
        children.append({
            "name": child_name,
            "ref": ref,
            "definition": prefix + disclosure + (f" {desc}" if desc
                                                 else ""),
            "steward": str(m.get("steward") or ""),
            "expert": str(m.get("developer") or ""),
        })
        relationships.append({"kind": "parent_child",
                              "term": parent_name,
                              "asset": child_name})
        relationships.append({"kind": "governs", "term": child_name,
                              "asset": ref})
        for report in (reports or {}).get(ref, []):
            relationships.append({"kind": "report",
                                  "term": child_name,
                                  "asset": str(report)})
    parent_definition = (
        prefix + f"Parent concept for {n} distinct definitions "
        f"sharing the name '{identity}'. Each child term is one "
        "variant, linked to its own procedure.")
    payload = {
        "cluster_id": str(cluster.get("id") or ""),
        "parent": {"name": parent_name, "ref": None,
                   "definition": parent_definition},
        "children": children,
        "relationships": relationships,
    }
    _self_check(payload)
    return payload


def _self_check(payload: dict) -> None:
    """The gate on generated text (XR-1 reconcile law): a count the
    template claims must equal the payload's own facts, and child
    names must be distinct — a proposal that disagrees with itself
    never leaves the house."""
    n = len(payload["children"])
    claimed = f"{n} distinct definitions"
    if claimed not in payload["parent"]["definition"]:
        raise ValueError(
            f"parent definition does not state its own child count "
            f"({n}): {payload['parent']['definition']!r}")
    names = [c["name"] for c in payload["children"]]
    if len(set(names)) != len(names):
        raise ValueError(f"child names collide: {sorted(names)}")


def hierarchy_purview_rows(payloads: "list[dict]") -> "list[dict]":
    """TERM-PROPOSE-2, Purview leg: terms only — the glossary import
    CSV has no term-assignment surface, so term<->proc/report links
    stay in the payload for stage 2 (a stated file-first limit, not
    a silent drop). Status=Draft always: their workflow owns
    promotion."""
    from src.adapters.file_export import assert_unique_names
    rows = []
    for p in payloads:
        rows.append({
            "Name": p["parent"]["name"], "Status": "Draft",
            "Definition": p["parent"]["definition"], "Acronym": "",
            "Experts": "", "Stewards": "", "Parent Term Name": "",
            "IsDefinitionRichText": "false"})
        for c in p["children"]:
            rows.append({
                "Name": c["name"], "Status": "Draft",
                "Definition": c["definition"], "Acronym": "",
                "Experts": c["expert"], "Stewards": c["steward"],
                "Parent Term Name": p["parent"]["name"],
                "IsDefinitionRichText": "false"})
    assert_unique_names(rows, "purview_term_hierarchy")
    return rows


def hierarchy_collibra_asset_rows(payloads: "list[dict]",
                                  domain: str = "") -> "list[dict]":
    from src.adapters.file_export import assert_unique_names
    rows = []
    for p in payloads:
        rows.append({
            "Name": p["parent"]["name"],
            "Full Name": p["parent"]["name"],
            "Asset Type": "Business Term", "Domain": domain,
            "Description": p["parent"]["definition"],
            "Stewards": ""})
        for c in p["children"]:
            rows.append({
                "Name": c["name"], "Full Name": c["ref"],
                "Asset Type": "Business Term", "Domain": domain,
                "Description": c["definition"],
                "Stewards": c["steward"]})
    assert_unique_names(rows, "collibra_term_hierarchy")
    return rows


def hierarchy_collibra_relation_rows(payloads: "list[dict]",
                                     ) -> "list[dict]":
    """The registry row's three relations: hierarchical (parent ->
    child), governs (child -> its proc), responsible (child ->
    steward). Relation TYPE names are the registry's own words —
    the operating-model mapping is an OPEN registry item."""
    rows = []
    for p in payloads:
        for c in p["children"]:
            rows.append({
                "Head": p["parent"]["name"],
                "Head Full Name": p["parent"]["name"],
                "Relation": "hierarchical", "Tail": c["name"],
                "Tail Asset Type": "Business Term"})
            rows.append({
                "Head": c["name"], "Head Full Name": c["ref"],
                "Relation": "governs", "Tail": c["ref"],
                "Tail Asset Type": "Data Asset"})
            if c["steward"]:
                rows.append({
                    "Head": c["name"], "Head Full Name": c["ref"],
                    "Relation": "responsible", "Tail": c["steward"],
                    "Tail Asset Type": "User"})
    return rows


# --- the store-driven leg (same query surfaces as file_export) -----

REPORTS_EXPORT_QUERY = (
    "graph_edges\n"
    "| where edge_type == 'report_to_canonical'\n"
    "| extend ['ref'] = tostring(split(target_id, ':')[1]),\n"
    "         report = tostring(split(source_id, ':')[1])\n"
    "| distinct ['ref'], report\n"
    "| order by ['ref'] asc, report asc"
)


def clusters_for_hierarchy(run_kql) -> "list[dict]":
    """OPEN conflict-class flags with their member ids — the
    organize_hierarchy work list, from the same census surface the
    X-Ray and BR-1 disclosure read."""
    from src.orchestrator.ops import OpsSession, op_census
    from src.orchestrator.tools import GOV_FLAG_MEMBER_NAMES_QUERY
    members = {str(r.get("cluster")): [
        str(m) for m in (r.get("member_ids") or [])]
        for r in run_kql(GOV_FLAG_MEMBER_NAMES_QUERY, {})}
    out = []
    for f in op_census("flag", run_kql, OpsSession()).rows:
        if str(f.get("flag_class")) not in CONFLICT_CLASSES:
            continue
        if str(f.get("disposition") or "open") != "open":
            continue
        if str(f.get("grain") or "") != "metric":
            # terms govern PROCS: a step-grain misnomer family is
            # console rename work, not a glossary hierarchy
            continue
        out.append({
            "id": str(f.get("id")),
            "identity": str(f.get("identity")),
            "flag_class": str(f.get("flag_class")),
            "disposition": "open",
            "member_ids": members.get(str(f.get("id")), []),
        })
    return sorted(out, key=lambda c: c["identity"])


def term_hierarchy_payloads(run_kql) -> "list[dict]":
    from src.adapters.file_export import _metric_rows
    metrics = {str(r.get("metric_id")): r for r in _metric_rows(run_kql)}
    reports: "dict[str, list[str]]" = {}
    for e in run_kql(REPORTS_EXPORT_QUERY, {}):
        reports.setdefault(str(e.get("ref")), []).append(
            str(e.get("report")))
    return [propose_hierarchy(c, metrics, reports)
            for c in clusters_for_hierarchy(run_kql)
            if c["member_ids"]]
