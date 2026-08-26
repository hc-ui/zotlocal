"""Guards for ``--port`` and ``--timeout``."""

from __future__ import annotations

import math

from .errors import ZotlocalError


def require_tcp_port(n: int) -> int:
    port = int(n)
    if not 1 <= port <= 65535:
        raise ZotlocalError("--port must be an integer 1-65535")
    return port


def require_positive_timeout(seconds: float) -> float:
    value = float(seconds)
    if not math.isfinite(value) or value <= 0:
        raise ZotlocalError("--timeout must be a positive number of seconds")
    return value
