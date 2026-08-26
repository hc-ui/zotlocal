from __future__ import annotations

import os
from pathlib import Path

import pytest

from zotlocal.cli import _open_path, _path_from_file_url
from zotlocal.errors import ZotlocalError


def test_path_from_file_url_posix() -> None:
    assert _path_from_file_url("file:///home/me/paper.pdf") == "/home/me/paper.pdf"
    assert _path_from_file_url("file://localhost/tmp/a%20b.pdf") == "/tmp/a b.pdf"


def test_path_from_file_url_windows_drive() -> None:
    path = _path_from_file_url("file:///C:/Users/me/paper.pdf")
    if os.name == "nt":
        assert path == "C:\\Users\\me\\paper.pdf"
    else:
        assert path == "/C:/Users/me/paper.pdf"


def test_path_from_file_url_passthrough() -> None:
    assert _path_from_file_url("/already/a/path.pdf") == "/already/a/path.pdf"
    assert _path_from_file_url("") == ""


def test_open_path_missing_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.name == "nt":
        pytest.skip("Windows uses os.startfile")

    def boom(args, **kwargs):
        raise FileNotFoundError(args[0])

    monkeypatch.setattr("zotlocal.cli.subprocess.Popen", boom)
    with pytest.raises(ZotlocalError, match="not found"):
        _open_path(str(Path("/tmp/missing-helper.pdf")))
