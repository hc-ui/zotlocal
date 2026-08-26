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
