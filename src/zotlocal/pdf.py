from __future__ import annotations

from .client import Client
from .errors import ZotlocalError
from .models import Item


def find_pdfs(client: Client, key: str) -> list[dict[str, str]]:
    item = client.item(key)
    candidates: list[Item] = []
    if item.item_type == "attachment":
        candidates = [item]
    else:
        candidates = [
            child
            for child in client.children(key)
            if child.item_type == "attachment" or _looks_pdf(child)
        ]
    found: list[dict[str, str]] = []
    for child in candidates:
        if not _looks_pdf(child) and child.data.get("contentType") not in {
            "application/pdf",
            "application/x-pdf",
        }:
            if child.item_type == "attachment" and not child.data.get("contentType"):
                pass
            elif not _looks_pdf(child):
                continue
        url = ""
        try:
            url = client.file_url(child.key)
        except ZotlocalError:
            url = ""
        found.append(
            {
                "key": child.key,
                "title": child.title,
                "contentType": str(child.data.get("contentType") or ""),
                "url": url,
            }
        )
    return found


def _looks_pdf(item: Item) -> bool:
    name = (item.title or "").lower()
    path = str(item.data.get("path") or item.data.get("filename") or "").lower()
    ctype = str(item.data.get("contentType") or "").lower()
    return name.endswith(".pdf") or path.endswith(".pdf") or "pdf" in ctype
