from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CITEKEY_LINE = re.compile(r"(?im)^\s*citation\s*key\s*:\s*(\S+)\s*$")


def year_from_date(value: str) -> str:
    match = re.search(r"\d{4}", value or "")
    return match.group(0) if match else ""


def citekey_from_data(data: dict[str, Any]) -> str:
    direct = data.get("citationKey") or data.get("citekey")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    extra = data.get("extra") or ""
    found = _CITEKEY_LINE.search(str(extra))
    return found.group(1) if found else ""


def format_authors(creators: list[Any], *, max_names: int = 2) -> str:
    names: list[str] = []
    for creator in creators:
        if not isinstance(creator, dict):
            continue
        last = str(creator.get("lastName") or "").strip()
        first = str(creator.get("firstName") or "").strip()
        name = str(creator.get("name") or "").strip()
        if last and first:
            names.append(last)
        elif last:
            names.append(last)
        elif name:
            names.append(name)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2 and max_names >= 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


@dataclass
class Item:
    key: str
    item_type: str
    title: str
    date: str
    year: str
    authors: str
    citekey: str
    parent_key: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Item":
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        data = data if isinstance(data, dict) else {}
        key = str(payload.get("key") or data.get("key") or "")
        date = str(data.get("date") or data.get("dateAdded") or "")
        creators = data.get("creators") if isinstance(data.get("creators"), list) else []
        return cls(
            key=key,
            item_type=str(data.get("itemType") or payload.get("itemType") or ""),
            title=str(data.get("title") or data.get("filename") or "").strip(),
            date=date,
            year=year_from_date(date),
            authors=format_authors(creators),
            citekey=citekey_from_data(data),
            parent_key=str(data.get("parentItem") or ""),
            data=data,
        )

    def row(self) -> str:
        cite = self.citekey or "-"
        year = self.year or "-"
        authors = self.authors or "-"
        title = self.title or "(untitled)"
        return f"{self.key}  {cite}  {year}  {authors}  {title}"


@dataclass
class Collection:
    key: str
    name: str
    parent_key: str = ""
    path: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Collection":
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        data = data if isinstance(data, dict) else {}
        return cls(
            key=str(payload.get("key") or data.get("key") or ""),
            name=str(data.get("name") or ""),
            parent_key=str(data.get("parentCollection") or ""),
        )


@dataclass
class Tag:
    name: str
    count: int = 0

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Tag":
        if isinstance(payload, str):
            return cls(name=payload)
        data = payload.get("tag") or payload.get("data") or payload
        if isinstance(data, dict):
            name = str(data.get("tag") or data.get("name") or "")
            meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            count = int(meta.get("numItems") or data.get("numItems") or 0)
            return cls(name=name, count=count)
        return cls(name=str(payload))
