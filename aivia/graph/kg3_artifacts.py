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

STATE_CLASSES = ("description", "term", "responsibility")
EVENT_CLASSES = ("disposition", "usage", "proposal", "redaction",
                 "run_event")
RUN_OUTCOMES = ("completed", "aborted")
DESCRIPTION_STATUS = ("gate_passed", "skeleton_floor", "flagged")
RULINGS = ("accept", "reject", "revoke", "acknowledge")
USAGE_ACTIONS = ("asked", "ran", "confirmed")
ASKED_OUTCOMES = ("matched", "ambiguous", "no-match")
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
            if n.kind in STATE_CLASSES
            and n.properties.get("artifact_id") == artifact_id]


def _append_version(store: Store, kind: str, artifact_id: str,
                    about: List[str], author: str, created_at: str,
                    basis: Optional[Dict[str, Any]],
                    payload: Dict[str, Any]) -> NodeVersion:
    _check_identity(author)
    if not about:
        raise RefusalKG3("KG3-7", "spine incomplete: about needs >=1 target")
    if is_machine(author) and not basis:
        raise RefusalKG3("KG3-3", "machine-authored version carries no "
                         "basis — the witness chain is mandatory")
    prior = _versions_of(store, artifact_id)
    seq = len(prior) + 1
    version_id = artifact_id if seq == 1 else f"{artifact_id}#v{seq}"
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
                       created_at: str) -> NodeVersion:
    if not (text or "").strip():
        raise RefusalKG3("LC3-F5", "no empty shells — a description "
                         "version must carry text")
    payload: Dict[str, Any] = {"text": text}
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
                parent: Optional[str] = None) -> NodeVersion:
    if not (definition or "").strip():
        raise RefusalKG3("LC3-F5", "no empty shells")
    payload = {"name": name, "definition": definition}
    if parent:
        payload["parent"] = parent
    return _append_version(store, "term", artifact_id, [name], author,
                           created_at, basis, payload)


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
    if is_machine(author):
        raise RefusalKG3("LC3-C3", "dispositions are HUMAN-ONLY — machines "
                         "never rule; machine findings are lenses")
    if ruling not in RULINGS:
        raise RefusalKG3("KG3-7", f"ruling '{ruling}' outside {RULINGS}")
    seq = len(store.current_nodes("disposition")) + 1
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
    if prior.kind not in STATE_CLASSES:
        raise RefusalKG3("LC3-S3", f"{prior.kind} is an event — events "
                         "refuse supersede; the ledger only grows")
    props = dict(prior.properties)
    props.update(fields)
    if prior.kind == "description":
        return append_description(
            store, props["artifact_id"], props["about"], props["text"],
            fields.get("status"), author, fields.get("basis"), created_at)
    return _append_version(store, prior.kind, props["artifact_id"],
                           props["about"], author, created_at,
                           fields.get("basis"),
                           {k: v for k, v in props.items()
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
                      {"about": version_id, "field": field, "why": why,
                       "author": human_confirmation},
                      "redaction", f"kg3@redaction:{seq}")
