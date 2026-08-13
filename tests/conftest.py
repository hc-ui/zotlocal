"""Shared fakes and fixtures. Never talks to a live Zotero."""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from zotlocal import DEFAULT_PORT, DEFAULT_TIMEOUT
from zotlocal.client import Client

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

# Unused local port: a forgotten opener must not hit Desktop's default listener.
TEST_PORT = 9

BIBTEX = """@article{vaswani_attention_2017,
  title = {Attention Is All You Need},
  year = {2017}
}
"""

PDF_URL = "http://127.0.0.1:9/fake/Attention-Is-All-You-Need.pdf"


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, body: bytes, status: int, content_type: str) -> None:
        self._body = body
        self.status = status
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


class FakeOpener:
    """Map ``(method, path_prefix)`` → ``(status, content_type, body)``.

    ``body`` may be ``str``, ``bytes``, ``dict``, ``list``, or a
    ``callable(request)`` that returns a body or a status triple.
    Longest matching prefix wins; an exact path is preferred.
    """

    def __init__(self, routes: dict[tuple[str, str], Any] | None = None) -> None:
        self.routes: dict[tuple[str, str], Any] = {}
        if routes:
            for (method, path), value in routes.items():
                self.add(method, path, value)

    def add(self, method: str, path_prefix: str, value: Any) -> None:
        self.routes[(method.upper(), path_prefix)] = value

    def open(
        self,
        request: urllib.request.Request,
        timeout: float | None = None,
    ) -> FakeResponse:
        del timeout
        method = request.get_method().upper()
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        path = urllib.parse.urlsplit(url).path
        value = self._lookup(method, path)
        if value is None:
            raise urllib.error.URLError(f"no fake route for {method} {path}")
        if callable(value):
            value = value(request)
        if isinstance(value, tuple) and len(value) == 3 and isinstance(value[0], int):
            status, content_type, body = value
        else:
            status, content_type, body = 200, "application/json", value
        if isinstance(body, (dict, list)):
            raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
            content_type = content_type or "application/json"
        elif isinstance(body, bytes):
            raw = body
        else:
            raw = str(body).encode("utf-8")
        if status >= 400:
            raise urllib.error.HTTPError(
                url,
                status,
                f"HTTP Error {status}",
                hdrs=None,
                fp=io.BytesIO(raw),
            )
        return FakeResponse(raw, status, content_type)

    def _lookup(self, method: str, path: str) -> Any | None:
        exact = self.routes.get((method, path))
        if exact is not None:
            return exact
        matches = [
            (prefix, value)
            for (route_method, prefix), value in self.routes.items()
            if route_method == method and path.startswith(prefix)
        ]
        if not matches:
            return None
        matches.sort(key=lambda item: len(item[0]), reverse=True)
        return matches[0][1]


class DownOpener:
    """Fails the way a closed local API port fails."""

    def open(
        self,
        request: urllib.request.Request,
        timeout: float | None = None,
    ) -> FakeResponse:
        del request, timeout
        raise urllib.error.URLError("Connection refused")


def library_routes(
    items: list[Any] | None = None,
    collections: list[Any] | None = None,
) -> dict[tuple[str, str], Any]:
    items = items if items is not None else load_fixture("items.json")
    collections = (
        collections if collections is not None else load_fixture("collections.json")
    )
    by_key = {row.get("key"): row for row in items}
    parent = by_key["PXW99EKT"]
    attachment = by_key["PDFATT01"]
    children = [
        row for row in items if (row.get("data") or {}).get("parentItem") == "PXW99EKT"
    ]
    top_level = [
        row
        for row in items
        if (row.get("data") or {}).get("itemType") != "attachment"
    ]

    def items_top(request: urllib.request.Request) -> Any:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        if query.get("format", [""])[0] == "bibtex":
            return 200, "application/x-bibtex", BIBTEX
        return 200, "application/json", top_level

    def items_list(request: urllib.request.Request) -> Any:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        if query.get("format", [""])[0] == "bibtex":
            return 200, "application/x-bibtex", BIBTEX
        return 200, "application/json", items

    return {
        ("GET", "/api/"): (200, "application/json", {}),
        ("GET", "/connector/ping"): (200, "text/plain", "Zotero is running"),
        ("GET", "/api/users/0/items/top"): items_top,
        ("GET", "/api/users/0/items/PXW99EKT/children"): (
            200,
            "application/json",
            children,
        ),
        ("GET", "/api/users/0/items/PXW99EKT"): (200, "application/json", parent),
        ("GET", "/api/users/0/items/PDFATT01/file/view/url"): (
            200,
            "application/json",
            {"url": PDF_URL},
        ),
        ("GET", "/api/users/0/items/PDFATT01"): (200, "application/json", attachment),
        ("GET", "/api/users/0/items"): items_list,
        ("GET", "/api/users/0/collections"): (200, "application/json", collections),
        ("GET", "/api/users/0/tags"): (200, "application/json", []),
    }


@pytest.fixture
def items_payload() -> list[Any]:
    return load_fixture("items.json")


@pytest.fixture
def collections_payload() -> list[Any]:
    return load_fixture("collections.json")


@pytest.fixture
def library_opener(
    items_payload: list[Any],
    collections_payload: list[Any],
) -> FakeOpener:
    return FakeOpener(library_routes(items_payload, collections_payload))


@pytest.fixture
def client(library_opener: FakeOpener) -> Client:
    return Client(port=TEST_PORT, timeout=0.2, opener=library_opener)


@pytest.fixture
def install_opener(monkeypatch: pytest.MonkeyPatch) -> Callable[[Any], None]:
    def _install(fake_opener: Any) -> None:
        real_init = Client.__init__

        def wrapped(
            self: Client,
            port: int = DEFAULT_PORT,
            timeout: float = DEFAULT_TIMEOUT,
            opener: Any | None = None,
        ) -> None:
            real_init(
                self,
                port=port,
                timeout=timeout,
                opener=fake_opener if opener is None else opener,
            )

        monkeypatch.setattr(Client, "__init__", wrapped)

    return _install


@pytest.fixture(autouse=True)
def block_live_http(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("tests must not contact a live Zotero or the network")

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)
