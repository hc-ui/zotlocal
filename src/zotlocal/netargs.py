"""Guards for ``--port`` and ``--timeout``."""

from __future__ import annotations

import math
import sys

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


def install() -> None:
    """Patch the CLI client so bad ``--port`` / ``--timeout`` exit 2."""
    from . import DEFAULT_PORT, DEFAULT_TIMEOUT, cli
    from .client import Client as OrigClient

    if getattr(cli, "_netargs_installed", False):
        return

    class GuardedClient(OrigClient):
        def __init__(self, port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, opener=None):
            super().__init__(
                port=require_tcp_port(port),
                timeout=require_positive_timeout(timeout),
                opener=opener,
            )

    orig_main = cli.main

    def main(argv=None):
        try:
            return orig_main(argv)
        except ZotlocalError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    cli.Client = GuardedClient
    cli.main = main
    cli._netargs_installed = True
