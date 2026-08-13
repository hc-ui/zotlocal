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
        "doi": item.doi,
        "url": item.url,
        "language": item.language,
        "publication": item.publication,
        "tags": list(item.tags),
        "collections": list(item.collection_keys),
        "abstract": item.abstract,
    }


def print_card(item: Item) -> str:
    lines = [
        f"key:        {item.key}",
        f"citekey:    {item.citekey or '-'}",
        f"type:       {item.item_type or '-'}",
        f"title:      {item.title or '-'}",
        f"authors:    {item.authors or '-'}",
        f"year:       {item.year or '-'}",
        f"publication: {item.publication or '-'}",
        f"doi:        {item.doi or '-'}",
        f"url:        {item.url or '-'}",
        f"language:   {item.language or '-'}",
        f"tags:       {', '.join(item.tags) if item.tags else '-'}",
    ]
    if item.abstract:
        lines.append("")
        lines.append(item.abstract)
    return "\n".join(lines) + "\n"


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
