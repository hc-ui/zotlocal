from __future__ import annotations

from typing import Any

from .client import Client
from .doctor import doctor
from .models import Item
from .reports import duplicate_citekeys, missing_pdfs
from .resolve import missing_citekeys, parent_items


def desk_report(client: Client, items: list[Item]) -> dict[str, Any]:
    ping = doctor(client)
    parents = parent_items(items)
    missing = missing_pdfs(client, parents)
    dups = duplicate_citekeys(parents)
    no_key = missing_citekeys(parents)
    return {
        "ok": bool(ping.get("ok")),
        "doctor": ping,
        "items": len(parents),
        "missing_pdfs": [item.key for item in missing],
        "duplicate_citekeys": {key: [item.key for item in rows] for key, rows in dups.items()},
        "missing_citekeys": [item.key for item in no_key],
        "missing_pdf_items": missing,
        "missing_citekey_items": no_key,
        "dup_groups": dups,
    }


def render_desk(report: dict[str, Any]) -> str:
    lines = ["# zotlocal 工作台", ""]
    if report["ok"]:
        lines.append("Zotero 本地 API：通。只读，不写文库。")
    else:
        lines.append("Zotero 本地 API：不通。先开桌面端并打开本地 API。")
    lines.append(f"抽查条目：{report['items']}（不含附件/笔记）")
    lines.append(f"缺 PDF：{len(report['missing_pdfs'])}")
    lines.append(f"缺引用键：{len(report['missing_citekeys'])}")
    lines.append(f"重复引用键：{len(report['duplicate_citekeys'])} 组")
    lines.append("")
    if report["missing_pdf_items"]:
        lines.append("## 缺 PDF")
        for item in report["missing_pdf_items"][:20]:
            lines.append(f"- {item.row()}")
        lines.append("")
    if report["missing_citekey_items"]:
        lines.append("## 缺引用键")
        for item in report["missing_citekey_items"][:20]:
            lines.append(f"- {item.row()}")
        lines.append("")
    if report["dup_groups"]:
        lines.append("## 重复引用键")
        for key, rows in report["dup_groups"].items():
            lines.append(f"- `{key}`")
            for item in rows:
                lines.append(f"  - {item.row()}")
        lines.append("")
    lines.append("下一步：`zotlocal draft KEY` 出中文草稿；`zotlocal missing-pdfs` / `citekeys` 看全表。")
    return "\n".join(lines) + "\n"
