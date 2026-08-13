from __future__ import annotations

import json
from typing import Any

from .models import Collection, Item, Tag


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def item_payload(item: Item) -> dict[str, Any]:
    return {
        "key": item.key,
        "citekey": item.citekey,
        "itemType": item.item_type,
        "title": item.title,
        "year": item.year,
        "authors": item.authors,
        "date": item.date,
        "parentKey": item.parent_key,
    }


def print_items(items: list[Item]) -> str:
    if not items:
        return "no items\n"
    return "".join(item.row() + "\n" for item in items)


def print_collections(collections: list[Collection], *, tree: bool) -> str:
    if not collections:
        return "no collections\n"
    lines: list[str] = []
    for col in collections:
        label = col.path if tree else col.name
        lines.append(f"{col.key}  {label}")
    return "\n".join(lines) + "\n"


def print_tags(tags: list[Tag]) -> str:
    if not tags:
        return "no tags\n"
    return "".join(
        f"{tag.count:>5}  {tag.name}\n" if tag.count else f"      {tag.name}\n"
        for tag in tags
    )


def markdown_cite(item: Item) -> str:
    key = item.citekey or item.key
    return f"[@{key}]"
