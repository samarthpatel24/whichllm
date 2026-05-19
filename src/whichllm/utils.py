from __future__ import annotations

import os
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path


def _current_version() -> str:
    """Return installed package version."""
    try:
        return version("whichllm")
    except PackageNotFoundError:
        return "unknown"


def _cache_dir() -> Path:
    """Return the whichllm cache directory, respecting XDG_CACHE_HOME."""
    base = os.environ.get("XDG_CACHE_HOME")
    if base and Path(base).is_absolute():
        return Path(base) / "whichllm"
    return Path.home() / ".cache" / "whichllm"
