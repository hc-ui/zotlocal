import pytest

from zotlocal.errors import ZotlocalError
from zotlocal.limits import require_positive_limit


def test_require_positive_limit():
    assert require_positive_limit(1) == 1
    assert require_positive_limit(25) == 25
    with pytest.raises(ZotlocalError, match="positive"):
        require_positive_limit(0)
    with pytest.raises(ZotlocalError, match="positive"):
        require_positive_limit(-3)


def test_cli_limit_rejects_non_positive(
    install_opener,
    library_opener,
    capsys,
):
    from zotlocal.cli import main

    install_opener(library_opener)
    assert main(["--limit", "0", "search", "attention"]) == 2
    err = capsys.readouterr().err
    assert "positive" in err
    assert main(["--limit", "-3", "search", "attention"]) == 2
    assert "positive" in capsys.readouterr().err
