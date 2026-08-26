from __future__ import annotations

import pytest

from zotlocal.errors import ZotlocalError
from zotlocal.netargs import require_positive_timeout, require_tcp_port


def test_require_tcp_port():
    assert require_tcp_port(1) == 1
    assert require_tcp_port(23119) == 23119
    assert require_tcp_port(65535) == 65535
    with pytest.raises(ZotlocalError, match="1-65535"):
        require_tcp_port(0)
    with pytest.raises(ZotlocalError, match="1-65535"):
        require_tcp_port(-1)
    with pytest.raises(ZotlocalError, match="1-65535"):
        require_tcp_port(65536)


def test_require_positive_timeout():
    assert require_positive_timeout(0.2) == 0.2
    assert require_positive_timeout(5) == 5.0
    for bad in (0, -1, float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ZotlocalError, match="positive"):
            require_positive_timeout(bad)


def test_cli_rejects_bad_port(capsys: pytest.CaptureFixture[str]) -> None:
    from zotlocal.cli import main

    assert main(["--port", "0", "doctor"]) == 2
    assert "1-65535" in capsys.readouterr().err
    assert main(["--port", "70000", "doctor"]) == 2
    assert "1-65535" in capsys.readouterr().err


def test_cli_rejects_bad_timeout(capsys: pytest.CaptureFixture[str]) -> None:
    from zotlocal.cli import main

    assert main(["--timeout", "0", "doctor"]) == 2
    assert "positive" in capsys.readouterr().err
    assert main(["--timeout", "nan", "doctor"]) == 2
    assert "positive" in capsys.readouterr().err
    assert main(["--timeout", "inf", "doctor"]) == 2
    assert "positive" in capsys.readouterr().err
