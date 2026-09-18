"""KG layer 3 — the artifact layer. NOT regenerable: human judgment +
gated machine output existing nowhere else; append-only ledger.

Under the one law there is no update and no delete — and in THIS layer
no retire either: ending is done BY WRITING (revoking dispositions,
superseding versions). Every version is its own node (unique identity,
all forever readable); current/ownership/standing/version are DERIVED by the
derivation lenses, never stored (the ledger law, CHECK-KG3-1).

Spine per the ratified registry: about (>=1 target) · author (identity
string, kind-prefixed: person:|role:|agent:) · basis (machine-authored
only, REQUIRED — the witness chain) · supersedes edges · status only
where authorship cannot say it (description, machine versions only).

The ONE destruction path in the codebase is redaction_act — human-
ruled, tombstoned, evented (SAFE-3).
"""
import re
from typing import Any, Dict, List, Optional

from aivia.graph import phi_gate
from aivia.graph.store import NodeVersion, Store

# literal: schema-mirror kg3_artifacts.Classes
STATE_CLASSES = ("description", "term", "responsibility")
# literal: schema-mirror kg3_artifacts.Classes
EVENT_CLASSES = ("disposition", "usage", "proposal", "redaction",
                 "run_event")
RUN_OUTCOMES = ("completed", "aborted")
# literal: schema-mirror kg3_artifacts.Classes description row
DESCRIPTION_STATUS = ("gate_passed", "skeleton_floor", "flagged",
                      "drafted", "approved")
# E1: Scribe aboutness pre-bless; "approved" landed at M6 (Sunny's
# "APPROVED" 2026-09-17 — the speech contract's drafted→approved
# gate reached its second state for the first time; registry
# 1.47.0 same breath)
# literal: schema-mirror kg3_artifacts.Classes disposition row
RULINGS = ("accept", "reject", "revoke", "acknowledge")
# literal: schema-mirror kg3_artifacts.Usage_Actions
USAGE_ACTIONS = ("asked", "ran", "confirmed",
                 "clarify-picked", "clarify-retyped")
# clarify-picked/retyped joined BY RULING (L3-D3, the clarify-miss
# counter; the literal review's critical find — the console wrote
# them against a closed set). This tuple becomes a registry
# mirror-check in the literal-census build (step F).
# literal: schema-mirror kg3_artifacts.Usage_Actions outcomes
ASKED_OUTCOMES = ("matched", "ambiguous", "no-match")
# literal: schema-mirror kg3_artifacts.Usage_Actions outcomes
OBSERVED_OUTCOMES = ("published", "denied", "edited", "missing")
_IDENTITY = re.compile(r"^(person|role|agent):\S+$")


class RefusalKG3(Exception):
    def __init__(self, rule: str, message: str):
        self.rule = rule
        super().__init__(f"{rule}: {message}")


def is_machine(author: str) -> bool:
    return author.startswith("agent:")


def _check_identity(author: str) -> None:
    if not _IDENTITY.match(author or ""):
        raise RefusalKG3("KG3-7", f"author '{author}' is not a kind-prefixed "
                         "identity (person:|role:|agent:)")


def _versions_of(store: Store, artifact_id: str) -> List[NodeVersion]:
    return [n for n in store.current_nodes()
            if n.label in STATE_CLASSES
            and n.properties.get("artifact_id") == artifact_id]


def _mint_actor(store: Store, author: str, created_at: str) -> None:
    """STEP 3 (the birth-edge law): actors are MINTED ON FIRST ACT —
    the author string becomes a real node (person/agent/role by its
    own prefix), idempotent. The acts' —by→ edges give the user tree
    its trunk; the actor's own birth edge IS being acted-by."""
    kind = author.split(":", 1)[0]
    for n in store.current_nodes(kind):
        if n.identity == author:
            return
    store.append_node(kind, author, {"identity": author},
                      created_at, extract_id=f"kg3@{created_at}")


def _append_version(store: Store, kind: str, artifact_id: str,
                    about: List[str], author: str, created_at: str,
                    basis: Optional[Dict[str, Any]],
                    payload: Dict[str, Any]) -> NodeVersion:
    _check_identity(author)
    _mint_actor(store, author, created_at)
    if not about:
        raise RefusalKG3("KG3-7", "spine incomplete: about needs >=1 target")
    if is_machine(author) and not basis:
        raise RefusalKG3("KG3-3", "machine-authored version carries no "
                         "basis — the witness chain is mandatory")
    prior = _versions_of(store, artifact_id)
    seq = len(prior) + 1
    version_id = artifact_id if seq == 1 else f"{artifact_id}#v{seq}"
    # literal: shape
    props = {"artifact_id": artifact_id, "about": list(about),
             "author": author, "created_at": created_at, **payload}
    if basis:
        props["basis"] = dict(basis)
    node = store.append_node(kind, version_id, props, created_at,
                             extract_id=f"kg3@{created_at}")
    if prior:
        store.append_edge("supersedes", version_id, prior[-1].identity, {},
                          created_at, f"kg3@{created_at}")
    return node


def append_description(store: Store, artifact_id: str, about: List[str],
                       text: str, status: Optional[str], author: str,
                       basis: Optional[Dict[str, Any]],
                       created_at: str,
                       anchor: Optional[Dict[str, Any]] = None
                       ) -> NodeVersion:
    if not (text or "").strip():
        raise RefusalKG3("LC3-F5", "no empty shells — a description "
                         "version must carry text")
    payload: Dict[str, Any] = {"description": text}
    if anchor:
        # THE ANCHOR RULE (twin-graph ruling 2f, Phase D): about
        # targets a MEANING IDENTITY — a KG2b content_key at a scope
        # path — never a syntax node, never a node instance. Same key
        # after regeneration -> the artifact survives silently (S1);
        # changed key -> flagged orphan (S2, the drift finding).
        payload["anchor"] = dict(anchor)
    if is_machine(author):
        if status not in DESCRIPTION_STATUS:
            raise RefusalKG3("PROD-3", f"status '{status}' outside the "
                             f"closed vocabulary {DESCRIPTION_STATUS}")
        payload["status"] = status
    elif status is not None:
        raise RefusalKG3("KG3-1", "human versions declare no status — "
                         "authorship says it (no stored summary may exist)")
    return _append_version(store, "description", artifact_id, about,
                           author, created_at, basis, payload)


def append_term(store: Store, artifact_id: str, name: str, definition: str,
                author: str, created_at: str,
                basis: Optional[Dict[str, Any]] = None,
                parent: Optional[str] = None,
                derived_from: Optional[List[str]] = None,
                about: Optional[List[str]] = None) -> NodeVersion:
    if not (definition or "").strip():
        raise RefusalKG3("LC3-F5", "no empty shells")
    # THE BIRTH-EDGE LAW (step 2, Sunny's overrule): a term is
    # DEDUCED from something — the act/event that deduced it is
    # required at birth. The junk self-about died with this.
    if not derived_from:
        raise RefusalKG3("LC3-F6", "no node is alone — a term cites "
                         "the act it was deduced from (derived_from)")
    # literal: shape
    payload = {"name": name, "definition": definition,
               "derived_from": list(derived_from)}
    if about:
        payload["about"] = list(about)
    if parent:
        payload["parent"] = parent
    # the KG3 spine (about >=1) is satisfied by REAL targets: the
    # entities the term describes, else the origin act itself —
    # never the term's own name (the dead junk)
    return _append_version(store, "term", artifact_id,
                           list(about or derived_from), author,
                           created_at, basis, payload)


def append_acronym(store: Store, name: str, expansions: List[str],
                   approved_by: str, approved_at: str) -> NodeVersion:
    """THE ONE-VOCABULARY LAW (2026-09-08): a blessed acronym —
    {name, expansions[], approved_by, approved_at}; the approver is
    the birth edge (direct to the person, timestamp as data, no
    ceremony event); used_by edges derive at graph build. Journals
    (kg3@ family): blessings survive rebirth."""
    _check_identity(approved_by)
    if not expansions or not [e for e in expansions
                              if (e or "").strip()]:
        raise RefusalKG3("VOC-1", "an acronym carries at least one "
                         "expansion — no empty shells")
    _mint_actor(store, approved_by, approved_at)
    return store.append_node(
        "acronym", f"acronym::{name.strip().upper()}",
        # literal: shape
        {"name": name, "expansions": [e.strip() for e in expansions],
         "approved_by": approved_by, "approved_at": approved_at},
        approved_at, extract_id=f"kg3@{approved_at}")


def append_blessed_name(store: Store, target: str, words: str,
                        description_hash: str, approved_by: str,
                        approved_at: str) -> NodeVersion:
    """R5.b THE BLESSED NAME (Grammar_Floor v2.8.0): a column's or
    table's short human name, SELECTED from the vendor's own words
    and blessed by a human — {target: KG1 identity, words,
    description_hash (ties the words to the dictionary text they
    were selected from), approved_by, approved_at}. Journals (kg3@
    family): blessings survive rebirth. Never exported (the
    EXPORT_LABELS allowlist)."""
    _check_identity(approved_by)
    if is_machine(approved_by):
        raise RefusalKG3("LC3-C3", "blessings are HUMAN acts — the "
                         "proposer proposes, it never blesses")
    if not (words or "").strip():
        raise RefusalKG3("VOC-1", "a blessed name carries words — "
                         "no empty shells")
    # NO actor mint here (the 2026-09-13 journal-containment find):
    # blessed names seed PRE-journal (they must exist before the
    # estate voices), and a pre-journal person mint swallowed the
    # approver's line from the acronym seed's journaled act. The
    # registry file is this act's durable record (approved_by rides
    # as data); the person node first-mints at their first
    # JOURNALED act, keeping the journal self-contained for replay.
    return store.append_node(
        "blessed_name", f"blessed_name::{target}",
        # literal: shape
        {"target": target, "words": words.strip(),
         "description_hash": description_hash,
         "approved_by": approved_by, "approved_at": approved_at},
        approved_at, extract_id=f"kg3@{approved_at}")


def append_responsibility(store: Store, artifact_id: str, kind: str,
                          holder: str, target: str, author: str,
                          created_at: str) -> NodeVersion:
    return _append_version(store, "responsibility", artifact_id, [target],
                           author, created_at, None,
                           {"kind": kind, "holder": holder})


def append_disposition(store: Store, about: str, ruling: str, author: str,
                       occurred_at: str,
                       reason: Optional[str] = None) -> NodeVersion:
    _check_identity(author)
    _mint_actor(store, author, occurred_at)
    if is_machine(author):
        raise RefusalKG3("LC3-C3", "dispositions are HUMAN-ONLY — machines "
                         "never rule; machine findings are lenses")
    if ruling not in RULINGS:
        raise RefusalKG3("KG3-7", f"ruling '{ruling}' outside {RULINGS}")
    seq = len(store.current_nodes("disposition")) + 1
    # literal: shape
    props: Dict[str, Any] = {"about": about, "ruling": ruling,
                             "author": author, "occurred_at": occurred_at,
                             "seq": seq}
    if reason:
        props["reason"] = reason
    versions = _versions_of(store, about)
    if versions:  # artifact-level ruling pins the version it judged
        props["accepted_version"] = versions[-1].identity
    return store.append_node("disposition", f"disposition:{seq}:{about}",
                             props, occurred_at, f"kg3@{occurred_at}")


def append_usage(store: Store, action: str, author: str, occurred_at: str,
                 payload: str = "", outcome: Optional[str] = None,
                 about: Optional[str] = None) -> NodeVersion:
    _check_identity(author)
    if action not in USAGE_ACTIONS:
        raise RefusalKG3("KG3-7", f"action '{action}' outside "
                         f"{USAGE_ACTIONS}")
    _mint_actor(store, author, occurred_at)
    # literal: shape
    props: Dict[str, Any] = {"action": action, "author": author,
                             "occurred_at": occurred_at}
    if action == "asked":
        if outcome not in ASKED_OUTCOMES:
            raise RefusalKG3("H5", "asked carries an outcome from "
                             f"{ASKED_OUTCOMES}")
        if outcome != "matched" and about is not None:
            raise RefusalKG3("H5", f"no about edge on {outcome} — the "
                             "inquiry touched nothing (A5)")
        props["outcome"] = outcome
    if about is not None:
        props["about"] = about
    if payload:
        props["payload"] = phi_gate.door2_redact(payload).text  # door 2
    seq = len(store.current_nodes("usage")) + 1
    return store.append_node("usage", f"usage:{seq}", props, occurred_at,
                             f"kg3@{occurred_at}")


def append_proposal(store: Store, kind: str, about: str, author: str,
                    occurred_at: str, target_system: Optional[str] = None,
                    outcome: Optional[str] = None) -> NodeVersion:
    _check_identity(author)
    _mint_actor(store, author, occurred_at)
    # literal: shape
    props: Dict[str, Any] = {"kind": kind, "about": about, "author": author,
                             "occurred_at": occurred_at}
    if kind == "sent":
        if not target_system:
            raise RefusalKG3("KG3-7", "sent names its target_system")
        props["target_system"] = target_system
    elif kind == "observed":
        if outcome not in OBSERVED_OUTCOMES:
            raise RefusalKG3("KG3-7", f"observed outcome outside "
                             f"{OBSERVED_OUTCOMES}")
        props["outcome"] = outcome
    else:
        raise RefusalKG3("KG3-7", f"proposal kind '{kind}' unknown")
    seq = len(store.current_nodes("proposal")) + 1
    return store.append_node("proposal", f"proposal:{seq}", props,
                             occurred_at, f"kg3@{occurred_at}")


def append_run_event(store: Store, author: str, basis: Dict[str, Any],
                     accounting: Dict[str, Any], outcome: str,
                     occurred_at: str) -> NodeVersion:
    """The GENERATION-RUN EVENT — the ONLY production ledger (PROD-1).
    Quality numbers are lenses over run events, never separate
    bookkeeping. Author is the agent identity; basis is the witness
    chain (grammar/lens/metamodel versions + the worklist)."""
    _check_identity(author)
    _mint_actor(store, author, occurred_at)
    if not is_machine(author):
        raise RefusalKG3("PROD-1", "the run event's author is the produce "
                         "pipeline's AGENT identity")
    if not basis:
        raise RefusalKG3("KG3-3", "a run event carries its basis")
    if outcome not in RUN_OUTCOMES:
        raise RefusalKG3("OPS-3", f"outcome '{outcome}' outside "
                         f"{RUN_OUTCOMES}")
    seq = len(store.current_nodes("run_event")) + 1
    return store.append_node(
        "run_event", f"run:{seq}",
        # literal: shape
        {"author": author, "basis": dict(basis),
         "accounting": dict(accounting), "outcome": outcome,
         "occurred_at": occurred_at},
        occurred_at, f"kg3@{occurred_at}")


def supersede(store: Store, prior_version_id: str,
              fields: Dict[str, Any], author: str,
              created_at: str) -> NodeVersion:
    versions, _ = store.read(prior_version_id, mode="all")
    if not versions:
        raise RefusalKG3("KG3-7", f"unknown version {prior_version_id}")
    prior = versions[-1]
    if prior.label not in STATE_CLASSES:
        raise RefusalKG3("LC3-S3", f"{prior.label} is an event — events "
                         "refuse supersede; the ledger only grows")
    props = dict(prior.properties)
    props.update(fields)
    if prior.label == "description":
        return append_description(
            store, props["artifact_id"], props["about"], props["description"],
            fields.get("status"), author, fields.get("basis"), created_at)
    return _append_version(store, prior.label, props["artifact_id"],
                           props["about"], author, created_at,
                           fields.get("basis"),
                           {k: v for k, v in props.items()
                            # literal: shape
                            if k not in ("artifact_id", "about", "author",
                                         "created_at", "basis")})


def redaction_act(store: Store, version_id: str, field: str, why: str,
                  human_confirmation: str) -> None:
    """SAFE-3: the ONE destruction path in the codebase. Human-ruled,
    tombstoned, evented. This is the only place stored content is ever
    overwritten — by design, exactly here, nowhere else."""
    _check_identity(human_confirmation)
    if is_machine(human_confirmation):
        raise RefusalKG3("SAFE-3", "redaction requires a HUMAN ruling")
    versions, _ = store.read(version_id, mode="all")
    if not versions:
        raise RefusalKG3("KG3-7", f"unknown version {version_id}")
    for version in versions:
        if field in version.properties:
            version.properties[field] = "<REDACTED>"  # the tombstone
    seq = len(store.current_nodes("redaction")) + 1
    store.append_node("redaction", f"redaction:{seq}",
                      # literal: shape
                      {"about": version_id, "field": field, "why": why,
                       "author": human_confirmation},
                      "redaction", f"kg3@redaction:{seq}")


# ---- Phase D (twin-graph ruling 2f): the anchor migration ----------
def _is_human_owned(store: Store, artifact_id: str) -> bool:
    versions = _versions_of(store, artifact_id)
    if any(not is_machine(v.properties["author"]) for v in versions):
        return True
    version_ids = {v.identity for v in versions} | {artifact_id}
    return any(d.properties.get("ruling") == "accept"
               and d.properties.get("about") in version_ids
               for d in store.current_nodes("disposition"))


def migrate_anchors(store: Store, selection_keys: Dict[str, str],
                    occurred_at: str) -> Dict[str, Any]:
    """One-time Phase D act: every current description without an
    anchor gains one — a new version citing the migration basis,
    anchored to its scope's selection content_key. The equation is
    the acceptance: migrated + orphaned + human_held == candidates.
    Orphans (about-target absent from the twins) are FINDINGS, never
    errors; human-owned artifacts are never touched by a pipeline —
    they surface for the steward instead."""
    latest: Dict[str, NodeVersion] = {}
    for v in store.current_nodes("description"):
        latest[v.properties["artifact_id"]] = v
    # literal: shape
    report: Dict[str, Any] = {"candidates": 0, "migrated": 0,
                              "orphaned": [], "human_held": []}
    for artifact_id, version in sorted(latest.items()):
        if version.properties.get("anchor"):
            continue
        report["candidates"] += 1
        target = version.properties["about"][0]
        key = selection_keys.get(target)
        if key is None:
            report["orphaned"].append(target)
            continue
        if _is_human_owned(store, artifact_id):
            report["human_held"].append(target)
            continue
        _append_version(
            store, "description", artifact_id,
            version.properties["about"], "agent:anchor-migration",
            occurred_at,
            {"migration": "phase-d anchor (ADR 0077)",
             "from_version": version.identity},
            # literal: shape
            {"description": version.properties["description"],
             "status": version.properties.get("status"),
             "anchor": {"scope": target, "content_key": key}})
        report["migrated"] += 1
    assert (report["migrated"] + len(report["orphaned"])
            + len(report["human_held"]) == report["candidates"])
    return report
