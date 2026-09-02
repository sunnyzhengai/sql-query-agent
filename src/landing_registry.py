"""LANDING_REGISTRY — the decision landing matrix as data (ADR 0068).

The ninth peer registry: every governance action, mapped to what it
creates in each DG tool (Purview Unified Catalog / Collibra) and what
stays home. Converted from docs/architecture/DECISION_LANDING_MATRIX.md
(DRAFT v3, Sunny's four rulings of 2026-08-31) under the ADR 0067
ratchet — that document is now the GENERATED projection of this file.

Two invariants from ADR 0063 §3, mechanized by
tests/test_landing_registry.py:
- no action without a landing (every record lands somewhere or is
  explicitly own_only);
- no landing without a grade (every record carries provenance).

Brand discipline: the core is brand-neutral (law:brand-separation), so
attribution text uses the "{product}" placeholder — the generator
renders it via src.branding.product_name().

Content status mirrors the source document: rulings 1–4 are RULED
(2026-08-31); the matrix as a whole awaits Bridge-build ratification.
"""

from __future__ import annotations

# Legend used verbatim in cells: [native] ships in the tool,
# [config] needs a configured attribute/relation/workflow,
# [absent] the tool has no surface — we hold it.
SUPPORT = ("native", "config", "absent")

WORKFLOW_RULES = (
    ("R1", "We act only when a PARSE SOURCE changes — SQL, TMDL, or "
           "the dictionary. No change, no proposal, no noise."),
    ("R2", "We never repeat a proposal we have already made — the "
           "OUTBOX is keyed by logic-hash, not by name."),
    ("R3", "We look before we write — at write time we read the ONE "
           "object we are about to touch, never the catalog at large."),
    ("R4", "We do not police their catalog between engagements — "
           "divergence is an X-Ray finding, not a live subsystem."),
)

ZERO_SCHEMA_FOOTPRINT = {
    # Sunny's ruling, 2026-08-31: NO custom attributes in the
    # customer's catalog. These replace every custom field earlier
    # drafts proposed.
    "source_is_a_relationship": (
        "the term-to-asset link (Collibra `governs` / Purview term "
        "assignment) IS the statement 'this definition comes from that "
        "procedure' — no source field, no code fragment, no frozen "
        "line pointer"),
    "attribution_prefix": "{product} agent generated: ",
    "attribution_note": (
        "machine-authored descriptions begin with the prefix; a "
        "steward rewriting the text and dropping it is itself the "
        "signal of human authorship"),
    "logic_hash_stays_home": (
        "the parse hash (normalized fingerprint of a logical unit) "
        "lives only in the OUTBOX — we are the party proposing, so we "
        "are the party that must remember"),
    "accepted_limit": (
        "with no marker in their catalog, a lost outbox means our "
        "artifacts are recognisable only by the prefix text — so the "
        "outbox is a BACKED-UP asset and the prefix is the fallback"),
}

OUTBOX_FIELDS = ("logic_hash", "proposal_kind", "target_system",
                 "target_object_id", "proposed_at",
                 "last_seen_outcome", "outcome_seen_at")
OUTBOX_OUTCOMES = ("published", "denied", "edited", "missing")
OUTBOX_NOTE = ("NOT a copy of their catalog: no term text, no "
               "relationships, no status stream — only what WE "
               "asserted and what we last observed at write time; "
               "outcomes refresh only when rule R3 fires or during "
               "an X-Ray")

TARGET_SYSTEMS = ("purview", "collibra")

LANDING_ACTIONS = {
    "certify": {
        "title": "certify one definition",
        "grade": "steward-certified, approver named",
        "purview": {
            "assets": ["[native] glossary term (name + definition)",
                       "[native] data asset (proc/view)"],
            "relationships": ["[native] term -> data asset (term "
                              "assignment)",
                              "[native] term -> steward/expert "
                              "(contacts)",
                              "[native] term -> report asset"],
            "status": "[native] Draft -> Published via publish "
                      "workflow",
        },
        "collibra": {
            "assets": ["[native] Business Term",
                       "[native] Data Asset (proc/view)"],
            "relationships": ["[native] term `governs` asset",
                              "[native] term `responsible` steward",
                              "[native] term -> report relation"],
            "status": "[native] Candidate -> Certified (configurable "
                      "statuses)",
        },
        "keeps": "outbox row only",
    },
    "organize_hierarchy": {
        # supersedes "designate official" and "differentiate all":
        # the steward's real act is the PARENT CONCEPT + distinct
        # children, optionally one marked canonical.
        "title": "organize a name family into hierarchy",
        "grade": "steward-certified per child",
        "purview": {
            "assets": ["[native] parent glossary term (concept, no "
                       "proc behind it)",
                       "[native] N child terms (one per variant)"],
            "relationships": ["[native] parent-child term hierarchy",
                              "[native] each child -> its proc",
                              "[native] child -> report/steward"],
            "status": "[native] hierarchy + description wording — no "
                      "native 'official one', no custom field added",
            "rename_work": "[absent] no native task -> console work "
                           "list",
        },
        "collibra": {
            "assets": ["[native] parent Business Term",
                       "[native] N child Business Terms"],
            "relationships": ["[native] hierarchical relation",
                              "[native] child `governs` its proc",
                              "[native] steward responsibility per "
                              "child"],
            "status": "[config] `is preferred term` relation where "
                      "the estate has one",
            "rename_work": "[native] workflow task assignment",
        },
        "keeps": "outbox rows + open rename list where the tool has "
                 "no task surface",
    },
    "deny": {
        "title": "deny with reason",
        "grade": "asserted (testimony; disposition recorded)",
        "purview": {
            "assets": ["[native] the term (stays, not published)"],
            "relationships": [],
            "status": "[native] workflow rejection — the rejection IS "
                      "the record; no field added",
            "reason": "[native] workflow rejection comment",
        },
        "collibra": {
            "assets": ["[native] the term"],
            "relationships": [],
            "status": "[native] Rejected/Denied (configurable)",
            "reason": "[native] comment / workflow reason",
        },
        "keeps": "outbox row outcome=denied — rule R2 then prevents "
                 "re-proposal for that logic-hash",
    },
    "approve_technical": {
        # approval happens in THEIR workflow: Bridge proposes Draft;
        # author -> steward -> expert -> owner -> published.
        "title": "approve technical write",
        "grade": "parsed-by-{product}, approved-by developer",
        "purview": {
            "assets": ["[native] data asset description",
                       "[native] column descriptions",
                       "[native] glossary term (Draft)"],
            "relationships": ["[native] lineage (process entities)",
                              "[native] term -> asset"],
            "status": "[native] workflow roles "
                      "(steward/expert/owner) approve",
        },
        "collibra": {
            "assets": ["[native] asset attributes",
                       "[native] Business Term (Candidate)"],
            "relationships": ["[native] `is derived from` / lineage",
                              "[native] term `governs` asset"],
            "status": "[native] workflow roles + responsibilities",
        },
        "keeps": "outbox row (proposed -> published/denied as last "
                 "seen)",
    },
    "fork": {
        "title": "fork (developer authors a variant)",
        "grade": "asserted, owner = creator",
        "unbuilt": True,  # no authoring surface today
        "purview": {
            "assets": ["[native] the new proc becomes an asset once "
                       "parsed", "[native] its term Draft"],
            "relationships": ["[native] lineage child -> parent proc",
                              "[native] term hierarchy under the "
                              "concept parent"],
            "status": "[native] as certify, once parsed",
        },
        "collibra": {
            "assets": ["[native] same"],
            "relationships": ["[native] same"],
            "status": "[native] same",
        },
        "keeps": "the draft ONLY until it re-enters through the "
                 "parser (0058-C4: claimed = parsed)",
    },
    "reopen": {
        # under the outbox model: simply a NEW proposal cycle (the SQL
        # changed, rule R1, or a human reopens in their tool).
        "title": "reopen a ruling",
        "grade": "new cycle — inherits the fresh proposal's grade",
        "purview": {
            "assets": [],
            "relationships": [],
            "status": "[native] term returns to Draft via workflow",
        },
        "collibra": {
            "assets": [],
            "relationships": [],
            "status": "[native] back to Candidate; native history",
        },
        "keeps": "outbox row updated at next write-time read (R3)",
    },
    "delegate": {
        "title": "delegate to citizen steward",
        "grade": "delegate's answer returns as testimony; the STEWARD "
                 "lands the conclusion",
        "purview": {
            "assets": [],
            "relationships": [],
            "status": "[native] workflow assignment (publish workflow "
                      "roles)",
        },
        "collibra": {
            "assets": [],
            "relationships": [],
            "status": "[native] workflow task",
        },
        "keeps": "queue only where the tool lacks one",
    },
    "escalate": {
        "title": "escalate — none of these is right",
        "grade": "demand artifact; the conversation attaches",
        "own_only": True,  # neither tool is a demand system
        "keeps": "the demand queue (+ optional ticketing export "
                 "later)",
    },
    "machine_signals": {
        "title": "machine signals (never leave)",
        "grade": "machine weights (0056 w3/w8); rung stamps",
        "own_only": True,
        "keeps": "user confirms (usage weight) - run telemetry + rung "
                 "stamps - parse corrections / lexicon growth - sweep "
                 "state - the outbox itself. A catalog cannot consume "
                 "these.",
    },
}

CONSEQUENCES = {
    "console": ("decided cards are HANDOFF RECEIPTS: state chip + "
                "approver + 'proposed to <tool> - <last seen outcome> "
                "- [open in catalog]'; they sink beneath open work "
                "with a Resolved (N) filter — governance is reviewed "
                "IN THE CATALOG; the console proves the handoff"),
    "divergence": ("catalog text vs parsed truth is NOT a live "
                   "subsystem: it is an X-Ray finding — at engagement "
                   "time we read the objects in our outbox and report "
                   "the mismatch count. A paid diagnostic (rule R4)."),
}

OPEN_ITEMS = (
    ("attribute names", "closed",
     "CLOSED 2026-08-31 by zero schema footprint — no names to "
     "decide; v1 transport file-first (ruled), Unified Catalog API "
     "evaluated at stage 2"),
    ("collibra relation types", "open",
     "operating-model relation types on the target estates (Sunny's "
     "expertise)"),
    ("canonical-child marking", "open",
     "attribute vs configured Collibra relation type — cosmetic, "
     "decide at build"),
    ("outbox retention", "open",
     "keep forever (recommended: small, and it is the anti-repeat "
     "memory) vs prune with the estate"),
)
