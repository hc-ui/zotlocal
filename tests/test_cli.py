from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

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


def test_no_args_runs_doctor(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
) -> None:
    install_opener(library_opener)
    assert run_cli([]) == 0


def test_desk_lists_missing_citekey(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("desk"))
    text = capsys.readouterr().out
    assert code == 0
    assert "工作台" in text
    assert "BERT0001" in text


def test_draft_item_does_not_invent_theme(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("draft", "PXW99EKT"))
    text = capsys.readouterr().out
    assert code == 0
    assert "Attention Is All You Need" in text
    assert "vaswani_attention_2017" in text
    assert "We propose a new simple network architecture" in text
    assert "theme：" in text
    assert "zotero_key:" in text
    assert "不编造" in text or "不自动编造" in text
    assert "zotero://open-pdf" in text or "未找到附件" in text


def test_draft_collection_by_name(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("draft", "B"))
    text = capsys.readouterr().out
    assert code == 0
    assert "PXW99EKT" in text


def test_desk_collection_scope(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("desk", "--collection", "B"))
    text = capsys.readouterr().out
    assert code == 0
    assert "范围：" in text
    assert "B" in text


def test_citekeys_marks_missing(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("citekeys"))
    text = capsys.readouterr().out
    assert code == 1
    assert "MISSING" in text
    assert "BERT0001" in text


def test_next_picks_gap(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("next"))
    text = capsys.readouterr().out
    assert code == 1
    assert "下一步" in text
    assert "zotlocal draft" in text


def test_select_json(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("select", "PXW99EKT", "--json"))
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["uri"].endswith("PXW99EKT")


def test_draft_writes_directory(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    tmp_path: Path,
) -> None:
    install_opener(library_opener)
    dest = tmp_path / "notes"
    dest.mkdir()
    assert run_cli(_args("draft", "PXW99EKT", "-o", str(dest))) == 0
    assert (dest / "vaswani_attention_2017.md").is_file()


def test_desk_writes_report(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    tmp_path: Path,
) -> None:
    install_opener(library_opener)
    out = tmp_path / "desk.md"
    assert run_cli(_args("desk", "-o", str(out))) == 0
    assert "工作台" in out.read_text(encoding="utf-8")


def test_collection_by_name(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("collection", "B"))
    text = capsys.readouterr().out
    assert code == 0
    assert "PXW99EKT" in text


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


def test_show_prints_card(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("show", "PXW99EKT"))
    text = capsys.readouterr().out
    assert code == 0
    assert "Attention Is All You Need" in text
    assert "10.5555/3295222.3295349" in text


def test_csl_prints_formatted_citation(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    code = run_cli(_args("csl", "PXW99EKT", "--style", "apa"))
    text = capsys.readouterr().out
    assert code == 0
    assert "Vaswani" in text
    assert "2017" in text


def test_stats_and_types(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    assert run_cli(_args("stats")) == 0
    out = capsys.readouterr().out
    assert "journalArticle" in out
    assert run_cli(_args("types")) == 0
    assert "journalArticle" in capsys.readouterr().out


def test_notes_and_doi(
    install_opener: Callable[[object], None],
    library_opener: FakeOpener,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_opener(library_opener)
    assert run_cli(_args("notes", "PXW99EKT")) == 0
    notes = capsys.readouterr().out
    assert "NOTE0001" in notes
    assert "attention" in notes.lower()
    assert run_cli(_args("doi", "PXW99EKT")) == 0
    assert "10.5555" in capsys.readouterr().out
