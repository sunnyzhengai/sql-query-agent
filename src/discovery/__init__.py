"""The discovery engine (ADR 0046): anchor → discover + match → rank →
the human picks. This package holds the DETERMINISTIC primitives —
path enumeration over the join map (spec:E1) and filter grounding
(spec:E5). Nothing stochastic lives here (spec:E2); the LLM's only
seat is anchoring, elsewhere."""
