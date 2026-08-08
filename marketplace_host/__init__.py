"""Azure Functions host for the Marketplace fulfillment integration.

NOT shipped in the product wheel — this is AIVIA's own service (the one
piece of the architecture that is ours to run), deployed when the offer
converts to transactable (ADR 0028 phase T2). All decisions live in
src/marketplace (pure, tested); this package is transport: HTTP in,
HTTP out, storage and token verification injected.
"""
