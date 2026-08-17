from __future__ import annotations

from .client import Client
from .errors import ZotlocalError
from .models import Collection, Item


def resolve_collection(client: Client, token: str) -> Collection:
    token = (token or "").strip()
    if not token:
        raise ZotlocalError("collection is empty")
    collections = client.collections()
    for col in collections:
        if col.key == token:
            return col
    lowered = token.lower()
    hits = [col for col in collections if col.name.lower() == lowered]
    if len(hits) == 1:
        return hits[0]
    path_hits = [col for col in collections if col.path.lower() == lowered]
    if len(path_hits) == 1:
        return path_hits[0]
    contains = [col for col in collections if lowered in col.name.lower()]
    if len(contains) == 1:
        return contains[0]
    if not hits and not contains:
        raise ZotlocalError(f"no collection named or keyed {token!r}")
    names = ", ".join(f"{col.path or col.name} ({col.key})" for col in (hits or contains)[:8])
    raise ZotlocalError(f"collection {token!r} is ambiguous: {names}")


def parent_items(items: list[Item]) -> list[Item]:
    return [
        item
        for item in items
        if item.item_type not in {"attachment", "note"}
    ]


def missing_citekeys(items: list[Item]) -> list[Item]:
    return [item for item in parent_items(items) if not item.citekey]
