from __future__ import annotations

from collections.abc import Callable

import pytest

from conftest import TEST_PORT, DownOpener, FakeOpener


def run_cli(argv: list[str]) -> int:
    from zotlocal.cli import main

    try:
        code = main(argv)
    except SystemExit as exc:
        code = exc.code
    return 0 if code is None else int(code)


def _args(*parts: str) -> list[str]:
    return ["--port", str(TEST_PORT), "--timeout", "0.2", *parts]


def test_search_prints_item_key_and_title(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("search", "attention"))
    text = capsys.readouterr().out
    assert code == 0
    assert "PXW99EKT" in text
    assert "Attention Is All You Need" in text


def test_cite_prints_citekey(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("cite", "attention"))
    text = capsys.readouterr().out
    assert code == 0
    assert "[@vaswani_attention_2017]" in text


def test_doctor_ok_when_api_returns_empty_object(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
) -> None:
    install_opener(library_opener)
    assert run_cli(_args("doctor")) == 0


def test_doctor_exit_1_when_connection_fails(
    install_opener: Callable[[object], None],
) -> None:
    install_opener(DownOpener())
    assert run_cli(_args("doctor")) == 1


def test_bib_prints_mocked_bibtex(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("bib", "PXW99EKT"))
    text = capsys.readouterr().out
    assert code == 0
    assert "@article" in text
    assert "vaswani_attention_2017" in text
