from __future__ import annotations

from collections import Counter
from typing import Any

from .models import Item


def summarize(items: list[Item]) -> dict[str, Any]:
    types = Counter(item.item_type or "unknown" for item in items)
    years = Counter(item.year or "unknown" for item in items)
    langs = Counter(item.language or "unknown" for item in items)
    with_doi = sum(1 for item in items if item.doi)
    with_citekey = sum(1 for item in items if item.citekey)
    with_abstract = sum(1 for item in items if item.abstract)
    return {
        "items": len(items),
        "withDoi": with_doi,
        "withCitekey": with_citekey,
        "withAbstract": with_abstract,
        "types": dict(types.most_common()),
        "years": dict(sorted(years.items())),
        "languages": dict(langs.most_common()),
    }


def print_stats(summary: dict[str, Any]) -> str:
    lines = [
        f"items:        {summary['items']}",
        f"with citekey: {summary['withCitekey']}",
        f"with DOI:     {summary['withDoi']}",
        f"with abstract: {summary['withAbstract']}",
        "",
        "types:",
    ]
    for name, count in summary["types"].items():
        lines.append(f"  {count:>4}  {name}")
    lines.append("years:")
    for name, count in summary["years"].items():
        lines.append(f"  {count:>4}  {name}")
    lines.append("languages:")
    for name, count in summary["languages"].items():
        lines.append(f"  {count:>4}  {name}")
    return "\n".join(lines) + "\n"
