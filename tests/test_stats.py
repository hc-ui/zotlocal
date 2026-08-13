from zotlocal.models import Item
from zotlocal.reports import duplicate_citekeys
from zotlocal.stats import summarize
from zotlocal.textutil import html_to_text


def test_summarize_counts(items_payload: list) -> None:
    items = [Item.from_api(row) for row in items_payload if row["data"].get("itemType") != "attachment"]
    summary = summarize([item for item in items if item.item_type != "note"])
    assert summary["items"] >= 2
    assert summary["withCitekey"] >= 1
    assert "journalArticle" in summary["types"]


def test_duplicate_citekeys() -> None:
    a = Item.from_api({"key": "A", "data": {"title": "one", "citationKey": "dup"}})
    b = Item.from_api({"key": "B", "data": {"title": "two", "citationKey": "dup"}})
    c = Item.from_api({"key": "C", "data": {"title": "three", "citationKey": "uniq"}})
    groups = duplicate_citekeys([a, b, c])
    assert list(groups) == ["dup"]
    assert {item.key for item in groups["dup"]} == {"A", "B"}


def test_html_to_text_strips_tags() -> None:
    assert html_to_text("<p>Read the attention section.</p>") == "Read the attention section."
