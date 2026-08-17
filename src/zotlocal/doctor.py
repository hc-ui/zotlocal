from __future__ import annotations

from typing import Any

from .client import Client


def doctor(client: Client) -> dict[str, Any]:
    ping = client.ping()
    tips: list[str] = []
    if not ping["api"]:
        tips.append(
            "Zotero local API did not respond. Start Zotero Desktop and enable "
            "Settings → Advanced → Allow other applications to communicate with Zotero. "
            "中文：设置 → 高级 → 允许此计算机上的其他应用程序与 Zotero 通信。"
        )
    elif not ping["connector"]:
        tips.append(
            "Local API is up; connector ping failed. Search still works. "
            "本地 API 已通，连接器 ping 失败，检索仍可用。"
        )
    else:
        tips.append(
            "Zotero local API is reachable. This CLI is read-only. "
            "本地 API 可用。本工具只读，不写文库。"
        )
    return {
        "ok": bool(ping["api"]),
        "base": ping["base"],
        "api": ping["api"],
        "connector": ping["connector"],
        "error": ping["error"],
        "tips": tips,
    }
