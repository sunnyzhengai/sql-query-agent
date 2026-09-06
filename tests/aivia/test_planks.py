"""Slice 0: the planks — the import law and banned constructs as physics.

Every rule here is structural (AST over aivia/), so it binds all future
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
  modules neither exist in aivia/ nor are imported by it.
"""
import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
AIVIA = ROOT / "aivia"

LLM_TOKENS = {"openai", "anthropic", "llm_client"}
PARSER_TOKENS = {"sqlglot", "clr", "pythonnet", "src.parser"}
DEFERRED_MODULES = {"match", "ground", "generate", "usage"}


def _modules():
    for path in sorted(AIVIA.rglob("*.py")):
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
        assert (AIVIA / pkg / "__init__.py").is_file(), f"aivia/{pkg} missing"


def test_plank_import_law():
    def rule(mod, imp):
        if not imp.startswith("aivia."):
            return None
        if mod.startswith("aivia/lenses/"):
            allowed = imp == "aivia.graph.read_api" \
                or imp.startswith("aivia.lenses") \
                or (mod == "aivia/lenses/registry.py"
                    and imp.startswith("aivia.graph.metamodel"))
            if not allowed:
                return ("lenses may import graph.read_api ONLY "
                        "(+ metamodel in registry.py — design data, "
                        "not graph state)")
        if mod.startswith("aivia/flows/"):
            if imp.startswith("aivia.graph.store"):
                return "flows use lifecycle APIs, never the store"
        if mod.startswith("aivia/graph/"):
            if imp.startswith(("aivia.lenses", "aivia.flows")):
                return "graph imports downward only"
        return None
    assert _violations(rule) == []


def test_plank_store_writers():
    lifecycle = {"aivia/graph/kg1_intake.py",
                 "aivia/graph/kg2_mapper/__init__.py",
                 "aivia/graph/kg3_artifacts.py", "aivia/graph/kg4_concepts.py",
                 "aivia/graph/read_api.py"}

    def rule(mod, imp):
        if imp.startswith("aivia.graph.store") and mod not in lifecycle:
            return "store primitives are lifecycle-only (plank)"
        return None
    assert _violations(rule) == []


def test_plank_parser_authority():
    def rule(mod, imp):
        root = imp.split(".")[0]
        hit = root in PARSER_TOKENS or imp in PARSER_TOKENS
        if hit and not mod.startswith("aivia/graph/kg2_mapper/"):
            return "parser machinery lives in kg2_mapper ONLY (CHECK-KG2-1)"
        return None
    assert _violations(rule) == []


def test_plank_no_llm_in_graph_or_lenses():
    def rule(mod, imp):
        caged = mod.startswith(("aivia/graph/", "aivia/lenses/"))
        if caged and any(tok in imp for tok in LLM_TOKENS):
            return "no LLM client in graph/* or lenses/* (LLM_Seats plank)"
        return None
    assert _violations(rule) == []


def test_plank_imports_nothing_deferred():
    present = [p.relative_to(ROOT).as_posix() for p in AIVIA.rglob("*.py")
               if p.stem in DEFERRED_MODULES]
    assert present == [], f"deferred modules exist in v1: {present}"

    def rule(mod, imp):
        if imp.startswith("aivia.") and imp.split(".")[-1] in DEFERRED_MODULES:
            return "v1 imports nothing deferred (MVP ruling)"
        return None
    assert _violations(rule) == []
