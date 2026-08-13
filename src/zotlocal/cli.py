from __future__ import annotations

import argparse
import sys

from . import DEFAULT_PORT, DEFAULT_TIMEOUT, __version__
from .client import Client
from .doctor import doctor
from .errors import ZoteroDown, ZoteroHttpError, ZotlocalError
from .format import dumps, item_payload, markdown_cite, print_collections, print_items, print_tags
from .models import Item
from .pdf import find_pdfs

DEFAULT_LIMIT = 25


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8()
    argv = sys.argv[1:] if argv is None else list(argv)
    parser = build_parser()
    if not argv:
        parser.print_help()
        return 2
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if not exc.code else int(exc.code)
    if not getattr(args, "command", None):
        parser.print_help()
        return 2

    client = Client(
        port=getattr(args, "port", DEFAULT_PORT),
        timeout=getattr(args, "timeout", DEFAULT_TIMEOUT),
    )
    try:
        return int(args.func(args, client))
    except ZoteroDown as exc:
        if getattr(args, "command", None) == "doctor":
            return _doctor_down(exc, bool(getattr(args, "json", False)))
        print(str(exc), file=sys.stderr)
        return 2
    except (ZoteroHttpError, ZotlocalError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="machine-readable JSON output",
    )
    common.add_argument(
        "--port",
        type=int,
        default=argparse.SUPPRESS,
        metavar="N",
        help=f"Zotero local API port (default: {DEFAULT_PORT})",
    )
    common.add_argument(
        "--timeout",
        type=float,
        default=argparse.SUPPRESS,
        metavar="SEC",
        help=f"HTTP timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    common.add_argument(
        "--limit",
        type=int,
        default=argparse.SUPPRESS,
        metavar="N",
        help=f"max items to return (default: {DEFAULT_LIMIT})",
    )
    common.add_argument(
        "--version",
        action="version",
        version=f"zotlocal {__version__}",
    )

    parser = argparse.ArgumentParser(
        prog="zotlocal",
        description="Read-only CLI for Zotero Desktop's local API.",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command")

    p_doctor = sub.add_parser("doctor", parents=[common], help="ping local API and connector")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_search = sub.add_parser("search", parents=[common], help="search library items")
    p_search.add_argument("query", metavar="QUERY")
    p_search.set_defaults(func=_cmd_search)

    p_item = sub.add_parser("item", parents=[common], help="show one item")
    p_item.add_argument("key", metavar="KEY")
    p_item.set_defaults(func=_cmd_item)

    p_cols = sub.add_parser("collections", parents=[common], help="list collections")
    p_cols.add_argument("--tree", action="store_true", help="print collection paths")
    p_cols.set_defaults(func=_cmd_collections)

    p_col = sub.add_parser("collection", parents=[common], help="list items in a collection")
    p_col.add_argument("key", metavar="KEY")
    p_col.set_defaults(func=_cmd_collection)

    p_tags = sub.add_parser("tags", parents=[common], help="list tags")
    p_tags.set_defaults(func=_cmd_tags)

    p_bib = sub.add_parser("bib", parents=[common], help="export BibTeX")
    p_bib.add_argument("keys", nargs="*", metavar="KEY")
    p_bib.set_defaults(func=_cmd_bib)

    p_pdf = sub.add_parser("pdf", parents=[common], help="find PDF attachments")
    p_pdf.add_argument("key", metavar="KEY")
    p_pdf.set_defaults(func=_cmd_pdf)

    p_recent = sub.add_parser("recent", parents=[common], help="recently modified items")
    p_recent.set_defaults(func=_cmd_recent)

    p_cite = sub.add_parser("cite", parents=[common], help="print [@citekey] or [@itemKey]")
    p_cite.add_argument("query", metavar="QUERY")
    p_cite.set_defaults(func=_cmd_cite)

    return parser


def _limit(args: argparse.Namespace) -> int:
    return int(getattr(args, "limit", DEFAULT_LIMIT))


def _json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


def _cmd_doctor(args: argparse.Namespace, client: Client) -> int:
    report = doctor(client)
    if _json(args):
        sys.stdout.write(dumps(report))
    else:
        for tip in report["tips"]:
            print(tip)
    return 0 if report["ok"] else 1


def _doctor_down(exc: ZoteroDown, json_mode: bool) -> int:
    tip = (
        "Zotero local API did not respond. Start Zotero Desktop and enable "
        "Settings → Advanced → Allow other applications to communicate with Zotero."
    )
    if json_mode:
        sys.stdout.write(
            dumps(
                {
                    "ok": False,
                    "api": False,
                    "connector": False,
                    "error": str(exc),
                    "tips": [tip],
                }
            )
        )
    else:
        print(tip)
    return 1


def _cmd_search(args: argparse.Namespace, client: Client) -> int:
    items = client.items(query=args.query, limit=_limit(args))
    return _emit_items(items, _json(args))


def _cmd_item(args: argparse.Namespace, client: Client) -> int:
    item = client.item(args.key)
    try:
        children = client.children(args.key)
    except ZotlocalError:
        children = []
    child_keys = [child.key for child in children]
    if _json(args):
        payload = item_payload(item)
        payload["children"] = child_keys
        sys.stdout.write(dumps(payload))
        return 0
    print(item.row())
    if child_keys:
        print("children: " + " ".join(child_keys))
    return 0


def _cmd_collections(args: argparse.Namespace, client: Client) -> int:
    collections = client.collections()
    if _json(args):
        sys.stdout.write(
            dumps(
                [
                    {
                        "key": col.key,
                        "name": col.name,
                        "parentKey": col.parent_key,
                        "path": col.path,
                    }
                    for col in collections
                ]
            )
        )
        return 0
    sys.stdout.write(print_collections(collections, tree=bool(args.tree)))
    return 0


def _cmd_collection(args: argparse.Namespace, client: Client) -> int:
    items = client.items(collection=args.key, limit=_limit(args))
    return _emit_items(items, _json(args))


def _cmd_tags(args: argparse.Namespace, client: Client) -> int:
    tags = client.tags(limit=_limit(args))
    if _json(args):
        sys.stdout.write(dumps([{"name": tag.name, "count": tag.count} for tag in tags]))
        return 0
    sys.stdout.write(print_tags(tags))
    return 0


def _cmd_bib(args: argparse.Namespace, client: Client) -> int:
    keys = list(args.keys) if args.keys else None
    text = client.bibtex(keys, limit=_limit(args))
    if _json(args):
        sys.stdout.write(dumps({"bibtex": text}))
        return 0
    if text and not text.endswith("\n"):
        text += "\n"
    sys.stdout.write(text)
    return 0


def _cmd_pdf(args: argparse.Namespace, client: Client) -> int:
    found = find_pdfs(client, args.key)
    if _json(args):
        sys.stdout.write(dumps(found))
        return 0
    if not found:
        sys.stdout.write("no pdfs\n")
        return 0
    for row in found:
        print(f"{row['key']}  {row['title']}  {row['url']}")
    return 0


def _cmd_recent(args: argparse.Namespace, client: Client) -> int:
    items = client.items(query="", limit=_limit(args), sort="dateModified")
    return _emit_items(items, _json(args))


def _cmd_cite(args: argparse.Namespace, client: Client) -> int:
    items = client.items(query=args.query, limit=_limit(args))
    if not items:
        print("no items", file=sys.stderr)
        return 1
    picked = next((item for item in items if item.citekey), items[0])
    cite = markdown_cite(picked)
    if _json(args):
        sys.stdout.write(dumps({"cite": cite}))
        return 0
    print(cite)
    return 0


def _emit_items(items: list[Item], json_mode: bool) -> int:
    if json_mode:
        sys.stdout.write(dumps([item_payload(item) for item in items]))
    else:
        sys.stdout.write(print_items(items))
    return 0


def _ensure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if encoding not in {"cp936", "gbk", "gb2312", "mbcs", "charmap", "cp1252"}:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, AttributeError):
            continue
