"""The ordered AST-rule registry.

Each entry normalizes the parsed tree. Runs AFTER sqlglot produces a
parse tree. Used for semantic cleanup (table hints, optimizer hints).

Ported from sql-business-logic-extractor.
"""

from sqlglot import exp

from .ast_rule import AstRule


def _drop_table_hints(tree: exp.Expression) -> exp.Expression:
    """Strip T-SQL table hints (WITH (NOLOCK) etc.) from every Table."""
    def visit(node: exp.Expression) -> exp.Expression:
        if isinstance(node, exp.Table) and node.args.get("hints"):
            node.set("hints", None)
        return node
    return tree.transform(visit)


AST_RULES: list[AstRule] = [
    AstRule(
        id="drop_table_hints",
        description=(
            "T-SQL WITH (NOLOCK) / WITH (HOLDLOCK) etc. table hints "
            "affect locking but not column lineage. Strip them."
        ),
        transform=_drop_table_hints,
    ),
]
