from __future__ import annotations

from typing import Any

from .client import Client


def doctor(client: Client) -> dict[str, Any]:
    ping = client.ping()
    tips: list[str] = []
    if not ping["api"]:
        tips.append(
            "Zotero local API did not respond. Start Zotero Desktop and enable "
            "Settings → Advanced → Allow other applications to communicate with Zotero."
        )
    elif not ping["connector"]:
        tips.append("Local API is up; connector ping failed. Search still works.")
    else:
        tips.append("Zotero local API is reachable. This CLI is read-only.")
    return {
        "ok": bool(ping["api"]),
        "base": ping["base"],
        "api": ping["api"],
        "connector": ping["connector"],
        "error": ping["error"],
        "tips": tips,
    }
