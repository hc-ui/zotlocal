import pytest

from conftest import DownOpener, FakeOpener, TEST_PORT
from zotlocal.client import Client, attach_paths
from zotlocal.errors import ZoteroDown, ZoteroHttpError
from zotlocal.models import Collection


def test_attach_paths_builds_parent_child() -> None:
    cols = [
        Collection(key="AAA11111", name="A", parent_key=""),
        Collection(key="BBB22222", name="B", parent_key="AAA11111"),
    ]
    attach_paths(cols)
    assert cols[0].path == "A"
    assert cols[1].path == "A / B"


def test_attach_paths_from_fixture(collections_payload: list) -> None:
    cols = attach_paths([Collection.from_api(row) for row in collections_payload])
    by_name = {col.name: col for col in cols}
    assert by_name["B"].path == "A / B"


def test_items_parses_fixture(client: Client) -> None:
    items = client.items(query="attention")
    paper = next(item for item in items if item.key == "PXW99EKT")
    assert paper.title == "Attention Is All You Need"
    assert paper.citekey == "vaswani_attention_2017"
    assert paper.year == "2017"
    assert paper.authors == "Vaswani et al."


def test_connection_error_raises_zotero_down() -> None:
    client = Client(port=TEST_PORT, timeout=0.2, opener=DownOpener())
    with pytest.raises(ZoteroDown):
        client.items()


def test_http_404_raises_zotero_http_error() -> None:
    opener = FakeOpener(
        {("GET", "/api/users/0/items/MISSING"): (404, "text/plain", "Not found")}
    )
    client = Client(port=TEST_PORT, timeout=0.2, opener=opener)
    with pytest.raises(ZoteroHttpError) as excinfo:
        client.item("MISSING")
    assert excinfo.value.status == 404
