"""SQL Intelligence Agent — Core Library."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("sql-query-agent")
except PackageNotFoundError:  # running from a bare source tree, not installed
    __version__ = "0.0.0+source"
