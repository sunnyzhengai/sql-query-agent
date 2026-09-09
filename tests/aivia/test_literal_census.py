"""E3 LOCK 1 — THE LITERAL CENSUS (the literal law, ratified
2026-09-07; build ordered 2026-09-09). The standing gate: every
literal collection of 3+ strings in aivia/ carries a marker naming
its ruled class — shape · mechanical · frame · schema-mirror ·
grammar. The two BANNED classes (vocabulary, ruling) have NO
marker: there is no comment that legalizes them; their only home is
the registry via the converter. Unmarked = this test fails = the
diff shows a classified decision or the list does not enter.

Marker form: a comment `# literal: <class>` on the collection's
first line or the line directly above it. schema-mirror markers
must also name their sheet (`# literal: schema-mirror <registry.sheet>`)
— test_registry_mirrors asserts each cited equality.

Proves: contract:aivia-design-to-code
"""
import ast
import pathlib

AIVIA = pathlib.Path(__file__).resolve().parents[2] / "aivia"
CLASSES = ("shape", "mechanical", "frame", "schema-mirror",
           "grammar")  # literal: shape — the census's own marker set


def _collections(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            strings = [e for e in node.elts
                       if isinstance(e, ast.Constant)
                       and isinstance(e.value, str)]
            if len(strings) >= 3:
                yield node
        elif isinstance(node, ast.Dict):
            strings = [k for k in node.keys
                       if isinstance(k, ast.Constant)
                       and isinstance(k.value, str)]
            if len(strings) >= 3:
                yield node


def _marked(lines, lineno):
    for ln in (lineno - 1, lineno - 2):
        if 0 <= ln < len(lines) and "# literal:" in lines[ln]:
            tag = lines[ln].split("# literal:", 1)[1].strip()
            return tag.split()[0] if tag else ""
    return None


def scan():
    unmarked, badclass = [], []
    for py in sorted(AIVIA.rglob("*.py")):
        src = py.read_text()
        lines = src.splitlines()
        tree = ast.parse(src)
        for node in _collections(tree):
            tag = _marked(lines, node.lineno)
            where = f"{py.relative_to(AIVIA.parent)}:{node.lineno}"
            if tag is None:
                unmarked.append(where)
            elif tag not in CLASSES:
                badclass.append(f"{where} ({tag})")
    return unmarked, badclass


def test_every_literal_collection_is_classified():
    unmarked, badclass = scan()
    assert not badclass, (
        "markers outside the ruled class set (vocabulary/ruling "
        f"have NO marker by law): {badclass}")
    assert not unmarked, (
        f"{len(unmarked)} unmarked literal collection(s) — classify "
        f"each with '# literal: <class>' or move it to the "
        f"registry:\n" + "\n".join(unmarked))
