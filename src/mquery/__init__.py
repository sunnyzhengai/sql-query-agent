"""Minimal M (Power Query) expression parser + shape census.

HANDOFF_SHAPE_CENSUS (2026-08-18), Sunny's challenge upheld: the TMDL
regex patterns ARE the disease — 277 SQL-shaped sources missed on one
live estate because argument variants (parameter server, concatenated
query, bracketed identifiers) defeat text patterns. This package applies
the native-parsers doctrine to layer three: tokenize + parse the needed
M subset (let, application, concatenation, records, identifiers), then
classify ASTs into SHAPE SIGNATURES with argument KINDS.

Signatures are WHITELIST-anonymized: only recognized M standard-library
names appear verbatim; every other identifier is emitted as a kind
(parameter / ref(query) / ref(function)). Strip-based anonymization
fails on the unrecognized by definition; whitelist-based cannot leak —
safe for customers to send, safe to aggregate (repeats across customers
= product signal).
"""

from src.mquery.census import CensusRow, census_files, coverage_lines
from src.mquery.parser import parse_m
from src.mquery.signature import partition_shape

__all__ = ["parse_m", "partition_shape", "census_files", "coverage_lines",
           "CensusRow"]
