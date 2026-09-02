"""The decision tree (ADR 0044) — faithful, counted, persisted.

TREE_CONTRACT_VERSION participates in every description cache key once
phase 2 lands (the PROMPT_VERSION mechanism): tightening the contract
regenerates everything it governs.
"""

# "2": DESC-LEAF-1 — leaves carry the principal-side function
# (func/func_distinct); the composer voices the full leaf frontier.
TREE_CONTRACT_VERSION = "2"
