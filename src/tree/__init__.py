"""The decision tree (ADR 0044) — faithful, counted, persisted.

TREE_CONTRACT_VERSION participates in every description cache key once
phase 2 lands (the PROMPT_VERSION mechanism): tightening the contract
regenerates everything it governs.
"""

# "2": DESC-LEAF-1 — leaves carry the principal-side function
# (func/func_distinct); the composer voices the full leaf frontier.
# "3": EXPR-IR-1 — leaves carry role-ordered captured expression
# trees (exprs); the composer interprets them compositionally.
# "4": report-review 3b (09-04) — EXISTS leaves carry the subquery's
# first FROM table (inner_table) so the composer names the missing
# record by its dictionary meaning.
TREE_CONTRACT_VERSION = "4"
