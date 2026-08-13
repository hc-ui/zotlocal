from __future__ import annotations

from collections import defaultdict

from .client import Client
from .models import Item
from .pdf import find_pdfs


def duplicate_citekeys(items: list[Item]) -> dict[str, list[Item]]:
    groups: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        if item.citekey:
            groups[item.citekey].append(item)
    return {key: rows for key, rows in groups.items() if len(rows) > 1}


def missing_pdfs(client: Client, items: list[Item]) -> list[Item]:
    missing: list[Item] = []
    for item in items:
        if item.item_type in {"attachment", "note"}:
            continue
        found = find_pdfs(client, item.key)
        if not found:
            missing.append(item)
    return missing
