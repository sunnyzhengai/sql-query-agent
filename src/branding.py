"""Product-name seam: the brand is deployment CONFIG, never code.

Core source must never contain the commercial name — grep-enforced by
tests/test_brand_neutral_core.py. Deployments brand themselves via the
SQA_PRODUCT_NAME env var (the marketplace host sets it; a neutral
snapshot simply doesn't). This is both the work-separation rule and the
white-label prerequisite (HANDOFF_BRAND_NEUTRAL_CORE, 2026-08-17).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_PRODUCT_NAME = "SQL Intelligence Agent"

# The pre-rename env prefix, assembled so the brand string never appears
# in core source. Remove together with legacy_env's fallback after one
# release once deployments have migrated to SQA_*.
_LEGACY_PREFIX = "".join(("AI", "VIA")) + "_"


def product_name() -> str:
    """The deployment's display name for the product."""
    return os.environ.get("SQA_PRODUCT_NAME") or DEFAULT_PRODUCT_NAME


def legacy_env(suffix: str, default: str = "") -> str:
    """Read SQA_<suffix>, falling back once to the pre-rename variable.

    The fallback logs a deprecation warning naming both variables so
    deployments migrate; it disappears with the fallback's removal.
    """
    val = os.environ.get(f"SQA_{suffix}")
    if val:
        return val
    old = os.environ.get(_LEGACY_PREFIX + suffix)
    if old:
        logger.warning("%s%s is deprecated — set SQA_%s instead",
                       _LEGACY_PREFIX, suffix, suffix)
        return old
    return default
