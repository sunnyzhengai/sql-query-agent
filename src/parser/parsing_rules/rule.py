"""Rule dataclass + ordered-application helper.

A Rule is a declarative regex transformation: pattern + replacement +
flags. It's "fired" when the substitution actually changes the input
(>= 1 match). Apply order matters -- later rules see SQL that earlier
rules already transformed.

Ported from sql-business-logic-extractor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    """One regex-based preprocessing rule."""
    id: str
    description: str
    pattern: str
    replacement: str
    flags: int = 0

    def apply(self, sql: str) -> tuple[str, int]:
        """Run the substitution. Returns (new_sql, n_substitutions)."""
        return re.subn(self.pattern, self.replacement, sql, flags=self.flags)


def apply_all(sql: str, rules: Iterable[Rule] | None = None) -> tuple[str, list[str]]:
    """Apply rules in order. Returns (clean_sql, fired_rule_ids)."""
    if rules is None:
        from .rules import PARSING_RULES
        rules = PARSING_RULES

    fired: list[str] = []
    for rule in rules:
        sql, n = rule.apply(sql)
        if n > 0:
            fired.append(rule.id)
    return sql, fired
