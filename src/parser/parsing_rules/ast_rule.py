"""AST-level rule registry -- transforms run on the parsed tree.

Text-level Rules run BEFORE parse (coax raw SQL into parseable form).
AstRules run AFTER parse (normalize the tree, strip noise).

Ported from sql-business-logic-extractor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from sqlglot import exp


@dataclass(frozen=True)
class AstRule:
    """One declarative AST transform."""
    id: str
    description: str
    transform: Callable[[exp.Expression], exp.Expression]

    def apply(self, tree: exp.Expression) -> exp.Expression:
        return self.transform(tree)


def apply_all_ast(tree: exp.Expression,
                  rules: Iterable[AstRule] | None = None) -> tuple[exp.Expression, list[str]]:
    """Apply AST rules in order. Returns (transformed_tree, fired_rule_ids)."""
    if rules is None:
        from .ast_rules import AST_RULES
        rules = AST_RULES

    fired: list[str] = []
    for rule in rules:
        before_sql = tree.sql()
        tree = rule.apply(tree)
        after_sql = tree.sql()
        if before_sql != after_sql:
            fired.append(rule.id)
    return tree, fired
