"""Slice 0: the planks — the import law and banned constructs as physics.

Every rule here is structural (AST over aisql/), so it binds all future
slices automatically: a module added in slice 4 that imports an LLM
client fails THIS suite, written before that module existed. Rules:

- import law (doc Level 1-3 + Import_Law sheet): lenses import
  graph.read_api ONLY; flows import lenses + graph lifecycle APIs,
  never store; graph imports downward only (no lenses/flows).
- store primitives callable only by lifecycle modules + read_api.
- parser authority (CHECK-KG2-1): parser machinery importable only
  inside graph/kg2_mapper.
- no LLM client anywhere in graph/* or lenses/* (the L3 LLM_Seats
  sheet: the three seats live in flows; NOWHERE ELSE is a plank).
- imports-nothing-deferred (MVP ruling): the deferred inward/usage
  modules neither exist in aisql/ nor are imported by it.

Proves: contract:aisql-design-to-code
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
AISQL = ROOT / "aisql"

LLM_TOKENS = {"openai", "anthropic", "llm_client"}
PARSER_TOKENS = {"sqlglot", "clr", "pythonnet", "src.parser"}
DEFERRED_MODULES = {"match", "ground", "generate", "usage"}


def _modules():
    for path in sorted(AISQL.rglob("*.py")):
        rel = path.relative_to(ROOT)
        tree = ast.parse(path.read_text(), filename=str(rel))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.update(f"{node.module}.{a.name}" for a in node.names)
                imports.add(node.module)
        yield rel.as_posix(), imports


def _violations(rule):
    out = []
    for mod, imports in _modules():
        for imp in sorted(imports):
            why = rule(mod, imp)
            if why:
                out.append(f"{mod} imports {imp}: {why}")
    return out


def test_plank_skeleton_exists():
    for pkg in ("graph", "lenses", "flows"):
        assert (AISQL / pkg / "__init__.py").is_file(), f"aisql/{pkg} missing"


def test_plank_import_law():
    def rule(mod, imp):
        if not imp.startswith("aisql."):
            return None
        if mod.startswith("aisql/lenses/"):
            allowed = imp == "aisql.graph.read_api" \
                or imp.startswith("aisql.lenses") \
                or (mod == "aisql/lenses/registry.py"
                    and imp.startswith("aisql.graph.metamodel"))
            if not allowed:
                return ("lenses may import graph.read_api ONLY "
                        "(+ metamodel in registry.py — design data, "
                        "not graph state)")
        if mod.startswith("aisql/flows/"):
            if imp.startswith("aisql.graph.store"):
                return "flows use lifecycle APIs, never the store"
        if mod.startswith("aisql/graph/"):
            if imp.startswith(("aisql.lenses", "aisql.flows")):
                return "graph imports downward only"
        return None
    assert _violations(rule) == []


def test_plank_store_writers():
    lifecycle = {"aisql/graph/kg1_intake.py",
                 "aisql/graph/kg2_mapper/__init__.py",
                 # Phase B (ADR 0077): the translator is the second
                 # derived-layer builder — KG2b's ONE writer
                 "aisql/graph/kg2_translator/__init__.py",
                 "aisql/graph/kg3_artifacts.py", "aisql/graph/kg4_concepts.py",
                 "aisql/graph/read_api.py"}

    def rule(mod, imp):
        if imp.startswith("aisql.graph.store") and mod not in lifecycle:
            return "store primitives are lifecycle-only (plank)"
        return None
    assert _violations(rule) == []


def test_plank_parser_authority():
    def rule(mod, imp):
        root = imp.split(".")[0]
        hit = root in PARSER_TOKENS or imp in PARSER_TOKENS
        if hit and not mod.startswith("aisql/graph/kg2_mapper/"):
            return "parser machinery lives in kg2_mapper ONLY (CHECK-KG2-1)"
        return None
    assert _violations(rule) == []


def test_plank_no_llm_in_graph_or_lenses():
    def rule(mod, imp):
        caged = mod.startswith(("aisql/graph/", "aisql/lenses/"))
        if caged and any(tok in imp for tok in LLM_TOKENS):
            return "no LLM client in graph/* or lenses/* (LLM_Seats plank)"
        return None
    assert _violations(rule) == []


def test_plank_imports_nothing_deferred():
    present = [p.relative_to(ROOT).as_posix() for p in AISQL.rglob("*.py")
               if p.stem in DEFERRED_MODULES]
    assert present == [], f"deferred modules exist in v1: {present}"

    def rule(mod, imp):
        if imp.startswith("aisql.") and imp.split(".")[-1] in DEFERRED_MODULES:
            return "v1 imports nothing deferred (MVP ruling)"
        return None
    assert _violations(rule) == []
