from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from urllib.request import Request

from . import DEFAULT_PORT, DEFAULT_TIMEOUT
from .errors import ZoteroDown, ZoteroHttpError, ZotlocalError
from .models import Collection, Item, Tag

LOCAL_USER = "/api/users/0"
API_HEADERS = {"Zotero-API-Version": "3", "Accept": "application/json"}


class Client:
    def __init__(
        self,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        opener: Any | None = None,
    ) -> None:
        self.base = f"http://127.0.0.1:{int(port)}"
        self.timeout = float(timeout)
        self._opener = opener

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        text, status, content_type = self._request("GET", path, params=params)
        if "json" in content_type or text[:1] in "[{":
            try:
                return json.loads(text) if text else None
            except json.JSONDecodeError as exc:
                raise ZotlocalError(f"invalid JSON from {path}: {exc}") from exc
        return text

    def get_text(self, path: str, params: dict[str, Any] | None = None) -> str:
        text, _status, _ctype = self._request("GET", path, params=params)
        return text

    def ping(self) -> dict[str, Any]:
        api_ok = False
        connector_ok = False
        api_error = ""
        try:
            payload = self.get_json("/api/")
            api_ok = True
        except ZoteroDown as exc:
            api_error = str(exc)
            payload = None
        except ZotlocalError as exc:
            api_error = str(exc)
            payload = None
        try:
            self._request("GET", "/connector/ping")
            connector_ok = True
        except ZotlocalError:
            connector_ok = False
        return {
            "base": self.base,
            "api": api_ok,
            "connector": connector_ok,
            "error": api_error,
            "info": payload if isinstance(payload, dict) else None,
        }

    def items(
        self,
        *,
        query: str = "",
        collection: str = "",
        item_type: str = "",
        tag: str = "",
        year: str = "",
        limit: int = 25,
        sort: str = "dateModified",
        direction: str = "desc",
        top: bool = True,
        trash: bool = False,
    ) -> list[Item]:
        if trash:
            path = f"{LOCAL_USER}/items/trash"
        elif collection:
            path = f"{LOCAL_USER}/collections/{collection}/items"
            if top:
                path += "/top"
        elif top:
            path = f"{LOCAL_USER}/items/top"
        else:
            path = f"{LOCAL_USER}/items"
        params: dict[str, Any] = {
            "sort": sort,
            "direction": direction,
        }
        if query:
            params["q"] = query
        if item_type:
            params["itemType"] = item_type
        if tag:
            params["tag"] = tag
        fetch_limit = limit
        if year:
            fetch_limit = max(limit, min(500, limit * 10))
        raw = self._paginate(path, params, limit=fetch_limit)
        items = [Item.from_api(row) for row in raw if isinstance(row, dict)]
        if year:
            want = str(year).strip()
            items = [item for item in items if item.year == want]
        return items[:limit]

    def item(self, key: str) -> Item:
        payload = self.get_json(f"{LOCAL_USER}/items/{key}")
        if not isinstance(payload, dict):
            raise ZotlocalError(f"unexpected item payload for {key}")
        return Item.from_api(payload)

    def children(self, key: str) -> list[Item]:
        raw = self.get_json(f"{LOCAL_USER}/items/{key}/children")
        if not isinstance(raw, list):
            return []
        return [Item.from_api(row) for row in raw if isinstance(row, dict)]

    def collections(self) -> list[Collection]:
        raw = self._paginate(f"{LOCAL_USER}/collections", {}, limit=10000)
        cols = [Collection.from_api(row) for row in raw if isinstance(row, dict)]
        return attach_paths(cols)

    def tags(self, limit: int = 200) -> list[Tag]:
        raw = self._paginate(f"{LOCAL_USER}/tags", {}, limit=limit)
        return [Tag.from_api(row) for row in raw]

    def bibtex(self, keys: list[str] | None = None, limit: int = 200) -> str:
        params: dict[str, Any] = {"format": "bibtex"}
        if keys:
            params["itemKey"] = ",".join(keys)
            return self.get_text(f"{LOCAL_USER}/items", params)
        return self.get_text(f"{LOCAL_USER}/items/top", {**params, "limit": min(limit, 100)})

    def item_types(self) -> list[dict[str, str]]:
        raw = self.get_json("/api/itemTypes")
        if not isinstance(raw, list):
            return []
        out: list[dict[str, str]] = []
        for row in raw:
            if isinstance(row, dict) and row.get("itemType"):
                out.append(
                    {
                        "itemType": str(row.get("itemType") or ""),
                        "localized": str(row.get("localized") or ""),
                    }
                )
        return out

    def trash(self, limit: int = 25) -> list[Item]:
        return self.items(limit=limit, trash=True, top=False)

    def citation(self, key: str, style: str = "apa") -> str:
        payload = self.get_json(
            f"{LOCAL_USER}/items/{key}",
            {"include": "citation", "style": style},
        )
        if isinstance(payload, dict):
            value = payload.get("citation")
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, dict):
                return str(value.get("citation") or value.get("text") or "").strip()
        return ""

    def note_html(self, key: str) -> str:
        item = self.item(key)
        if item.item_type == "note":
            return str(item.data.get("note") or "")
        return ""

    def child_notes(self, key: str) -> list[Item]:
        return [child for child in self.children(key) if child.item_type == "note"]

    def file_url(self, attachment_key: str) -> str:
        payload = self.get_json(f"{LOCAL_USER}/items/{attachment_key}/file/view/url")
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            return str(payload.get("url") or payload.get("href") or "")
        return str(payload or "")

    def _paginate(self, path: str, params: dict[str, Any], limit: int) -> list[Any]:
        out: list[Any] = []
        start = 0
        page = min(100, max(1, limit))
        while len(out) < limit:
            chunk_limit = min(page, limit - len(out))
            query = dict(params)
            query["limit"] = chunk_limit
            query["start"] = start
            payload = self.get_json(path, query)
            if not isinstance(payload, list) or not payload:
                break
            out.extend(payload)
            if len(payload) < chunk_limit:
                break
            start += len(payload)
        return out[:limit]

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[str, int, str]:
        url = self.base + path
        if params:
            clean = {k: str(v) for k, v in params.items() if v is not None and v != ""}
            if clean:
                url += "?" + urllib.parse.urlencode(clean, doseq=True)
        request = Request(url, method=method, headers=API_HEADERS)
        try:
            if self._opener is not None:
                response = self._opener.open(request, timeout=self.timeout)
            else:
                response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            raise ZoteroHttpError(int(exc.code), path, body) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as exc:
            raise ZoteroDown(_down_message(self.base, exc)) from exc
        with response:
            raw = response.read()
            status = int(getattr(response, "status", 200) or 200)
            headers = {k: v for k, v in response.headers.items()} if response.headers else {}
        text = raw.decode("utf-8", errors="replace")
        return text, status, headers.get("Content-Type", "")


def attach_paths(collections: list[Collection]) -> list[Collection]:
    by_key = {col.key: col for col in collections}
    for col in collections:
        parts = [col.name or col.key]
        parent = col.parent_key
        seen: set[str] = {col.key}
        while parent and parent not in seen and parent in by_key:
            seen.add(parent)
            node = by_key[parent]
            parts.append(node.name or node.key)
            parent = node.parent_key
        col.path = " / ".join(reversed(parts))
    return collections


def _down_message(base: str, exc: BaseException) -> str:
    return (
        f"cannot reach Zotero at {base} ({exc}). "
        "Is Zotero Desktop running? Enable Settings → Advanced → "
        "Allow other applications to communicate with Zotero."
    )
