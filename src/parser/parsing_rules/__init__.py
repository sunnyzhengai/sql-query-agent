"""Parsing rule registry -- regex-based SQL preprocessing rules.

Ported from sql-business-logic-extractor. Each rule is one T-SQL
construct sqlglot can't parse natively; the rule transforms the SQL
into something sqlglot can handle without changing semantics.
"""

from .ast_rule import AstRule, apply_all_ast
from .ast_rules import AST_RULES
from .rule import Rule, apply_all
from .rules import PARSING_RULES

__all__ = [
    "Rule", "PARSING_RULES", "apply_all",
    "AstRule", "AST_RULES", "apply_all_ast",
]
