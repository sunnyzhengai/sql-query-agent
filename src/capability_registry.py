"""CAPABILITY_REGISTRY — mechanism uniqueness (spec:G1–G3).

The end of "two tools for one job", as data. Each powerful capability
has exactly ONE owner (a module or package prefix) and a set of
sanctioned primitives (import roots). CI computes every
(module, primitive) pair actually present in src/ and asserts

    Uses ∖ S = ∅        (spec:G2 — sanctioned powers only)

where S is the union of (owner, prim) pairs below. Adding a capability
row IS the review — friction by design (the 0042 pattern; generalizes
tests/test_native_parser_law.py, whose sqlglot/sqlparse ban remains
the standing example of a primitive with NO owner at all).

Fifth peer registry: TABLE / NOTEBOOK / SHAPE / EXTRACTION / CAPABILITY.

G1 (one owner per capability) holds by construction: dict keys are
unique and each row names one owner prefix.
G3 (no undeclared power): a primitive in POWER_PRIMS with no sanctioned
pair fails CI at the site of use.

Honest residue (spec §11): innocent pure-Python duplication carries no
powerful primitive and is invisible to this check — mitigated by review
and by owning primitive operations in single modules.
"""

# Import roots that count as powerful. sqlglot/sqlparse are listed with
# no owner anywhere: banned absolutely (ADR 0001 total law).
POWER_PRIMS = ("pythonnet", "clr", "requests", "httpx",
               "sqlglot", "sqlparse")

CAPABILITY_REGISTRY = {
    "native_sql_parsing": {
        "owner": "src/parser/scriptdom_loader.py",
        "prims": ["pythonnet", "clr"],
        "why": "the ONLY parser initialization home (ADR 0001 total law); "
               "every other module reaches ScriptDom through it",
    },
    "llm_generation": {
        "owner": "src/llm_client.py",
        "prims": ["requests"],
        "why": "the one HTTP door to the customer's Azure OpenAI endpoint "
               "(descriptions, ADR 0019/0044); keys never ship",
    },
    "catalog_publishing": {
        "owner": "src/adapters/",
        "prims": ["requests"],
        "why": "optional catalog adapters (Collibra/Purview/PBI/Fabric, "
               "ADR 0009) — the outbound-governance HTTP surface",
    },
    "semantic_model_ingestion": {
        "owner": "src/extractor/",
        "prims": ["requests"],
        "why": "TMDL/DevOps ingestion (ADR 0040) — Fabric + DevOps APIs",
    },
    "graph_read_model_queries": {
        "owner": "src/graph/gql_client.py",
        "prims": ["requests"],
        "why": "Fabric Graph GQL read model (ADR 0033 projection; "
               "deterministic templates only, ADR 0046)",
    },
    "workbench_runtime": {
        "owner": "src/orchestrator/",
        "prims": ["requests"],
        "why": "the agentic workbench surface (ADR 0036): Eventhouse "
               "queries, event capture, the interpret/confirm loop",
    },
}
