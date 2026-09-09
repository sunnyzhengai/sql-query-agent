"""Outward stage 3: LAND — accepted artifacts -> the customer's catalog.

File-first (the ruled transport order); target-native forms ONLY, the
column sets bound as data by A15 (export_headers.json) — a rendered
row's keys must BE the bound set, nothing custom, mechanically
(LAND-4). Attribution is the prefix in the text, never a schema
footprint.

The B4 clause: a send is an outward, IRREVERSIBLE act — it requires
an accepting disposition on the artifact AND a named human
confirmation of the send itself; no autonomy mode exempts it
(LAND-1). The sent event lands BEFORE transport (LAND-3); every later
look lands an observed event (LAND-5, append-only); anti-repeat reads
the current-outcome lens (LAND-2). Look-before-write is the observe
act itself (R3).
"""
import json
import pathlib
from typing import Any, Callable, Dict

from aivia.graph import kg3_artifacts, phi_gate
from aivia.lenses import derivation

HEADERS = json.loads((pathlib.Path(__file__).parent /
                      "export_headers.json").read_text())


class LandRefusal(Exception):
    def __init__(self, rule: str, message: str):
        self.rule = rule
        super().__init__(f"{rule}: {message}")


def render(read, artifact_id: str, target_system: str) -> Dict[str, Any]:
    """Native payload, pure (no writes). LAND-4: keys == the bound set."""
    binding = HEADERS["targets"].get(target_system, {}).get("description")
    if binding is None:
        raise LandRefusal("A15", f"no header binding for target "
                          f"'{target_system}' — headers bind as data, "
                          "never improvised")
    current = derivation.lens_current(read, None)["yield"][artifact_id]
    text = phi_gate.egress_redact(current["text"]).text  # leaving tenant
    if str(current.get("author", "")).startswith("agent:"):
        text = HEADERS["attribution_prefix"] + text
    scope_key = current["about"][0]
    accepters = sorted({
        d.properties["author"]
        for d in read.nodes("disposition")
        if d.properties["ruling"] == "accept"
        and d.properties["about"] in (artifact_id, current["version_id"])})
    row = dict(binding["constants"])
    # literal: frame landing CSV contract
    row.update({"Name": scope_key.rsplit("::", 1)[-1],
                "Full Name": scope_key,
                "Description": text,
                "Stewards": ", ".join(accepters)})
    assert set(row) == set(binding["columns"]), \
        "LAND-4: zero custom attributes — the bound set IS the row"
    return {col: row[col] for col in binding["columns"]}


def send(store, read, artifact_id: str, target_system: str,
         human_confirmation: str,
         transport: Callable[[Dict[str, Any]], Any]):
    standing = derivation.lens_standing(read, None)["yield"].get(artifact_id)
    if standing != "accepted":
        raise LandRefusal("LAND-1", f"no send without an accepting "
                          f"disposition — standing is '{standing}' (B4)")
    if not human_confirmation.startswith("person:"):
        raise LandRefusal("LAND-1", "a send requires a NAMED HUMAN "
                          "confirmation; no autonomy mode exempts it (B4)")
    current = derivation.lens_current(read, None)["yield"][artifact_id]
    version_id = current["version_id"]
    outcomes = derivation.lens_current_outcome(read, None)["yield"]
    for p in read.nodes("proposal"):
        if p.properties.get("kind") == "sent" \
                and p.properties["about"] == version_id \
                and outcomes.get(p.identity) == "denied":
            raise LandRefusal("LAND-2", f"current outcome for "
                              f"{version_id} is denied — no re-send "
                              "unless a new version exists")
    payload = render(read, artifact_id, target_system)
    sent = kg3_artifacts.append_proposal(  # LAND-3: BEFORE transport
        store, kind="sent", about=version_id,
        author=human_confirmation, occurred_at=current["created_at"],
        target_system=target_system)
    receipt = transport(payload)
    return sent, receipt


def observe(store, sent_id: str, outcome: str, author: str,
            occurred_at: str):
    """LAND-5: observations append-only; what was seen lands as an
    event — look-before-write made durable."""
    return kg3_artifacts.append_proposal(
        store, kind="observed", about=sent_id, author=author,
        occurred_at=occurred_at, outcome=outcome)
