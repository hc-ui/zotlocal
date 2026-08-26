from __future__ import annotations

import argparse
import sys

import os
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import DEFAULT_PORT, DEFAULT_TIMEOUT, __version__
from .client import Client
from .doctor import doctor
from .errors import ZoteroDown, ZoteroHttpError, ZotlocalError
from .limits import require_positive_limit
from .format import (
    dumps,
    item_payload,
    markdown_cite,
    print_card,
    print_collections,
    print_items,
    print_tags,
)
from .models import Item
from .pdf import find_pdfs
from .desk import desk_report, render_desk
from .draft import render_drafts, write_drafts
from .reports import duplicate_citekeys, missing_pdfs
from .resolve import missing_citekeys, parent_items, resolve_collection
from .stats import print_stats, summarize
from .textutil import html_to_text

DEFAULT_LIMIT = 25


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8()
    argv = sys.argv[1:] if argv is None else list(argv)
    parser = build_parser()
    if not argv:
        argv = ["doctor"]
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
        description="本机 Zotero 只读助手：检索、缺 PDF、引用键、中文草稿。不上云、不写文库。",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command")

    p_doctor = sub.add_parser("doctor", parents=[common], help="ping local API and connector")
    p_doctor.set_defaults(func=_cmd_doctor)

    p_search = sub.add_parser("search", parents=[common], help="search library items")
    p_search.add_argument("query", metavar="QUERY")
    p_search.add_argument("--type", dest="item_type", default="", metavar="TYPE")
    p_search.add_argument("--tag", default="", metavar="TAG")
    p_search.add_argument("--year", default="", metavar="YYYY")
    p_search.set_defaults(func=_cmd_search)

    p_item = sub.add_parser("item", parents=[common], help="show one item")
    p_item.add_argument("key", metavar="KEY")
    p_item.set_defaults(func=_cmd_item)

    p_cols = sub.add_parser("collections", parents=[common], help="list collections")
    p_cols.add_argument("--tree", action="store_true", help="print collection paths")
    p_cols.set_defaults(func=_cmd_collections)

    p_col = sub.add_parser("collection", parents=[common], help="list items in a collection")
    p_col.add_argument("key", metavar="名|KEY")
    p_col.set_defaults(func=_cmd_collection)

    p_tags = sub.add_parser("tags", parents=[common], help="list tags")
    p_tags.set_defaults(func=_cmd_tags)

    p_bib = sub.add_parser("bib", parents=[common], help="export BibTeX")
    p_bib.add_argument("keys", nargs="*", metavar="KEY")
    p_bib.add_argument("-o", "--out", default=None, metavar="FILE")
    p_bib.set_defaults(func=_cmd_bib)

    p_pdf = sub.add_parser("pdf", parents=[common], help="find PDF attachments")
    p_pdf.add_argument("key", metavar="KEY")
    p_pdf.set_defaults(func=_cmd_pdf)

    p_recent = sub.add_parser("recent", parents=[common], help="recently modified items")
    p_recent.set_defaults(func=_cmd_recent)

    p_cite = sub.add_parser("cite", parents=[common], help="print [@citekey] or [@itemKey]")
    p_cite.add_argument("query", metavar="QUERY")
    p_cite.set_defaults(func=_cmd_cite)

    p_show = sub.add_parser("show", parents=[common], help="print a full item card")
    p_show.add_argument("key", metavar="KEY")
    p_show.set_defaults(func=_cmd_show)

    p_abstract = sub.add_parser("abstract", parents=[common], help="print abstractNote")
    p_abstract.add_argument("key", metavar="KEY")
    p_abstract.set_defaults(func=_cmd_abstract)

    p_doi = sub.add_parser("doi", parents=[common], help="print DOI")
    p_doi.add_argument("key", metavar="KEY")
    p_doi.set_defaults(func=_cmd_doi)

    p_csl = sub.add_parser("csl", parents=[common], help="formatted citation via Zotero CSL")
    p_csl.add_argument("key", metavar="KEY")
    p_csl.add_argument("--style", default="apa", metavar="STYLE")
    p_csl.set_defaults(func=_cmd_csl)

    p_notes = sub.add_parser("notes", parents=[common], help="print child notes")
    p_notes.add_argument("key", metavar="KEY")
    p_notes.set_defaults(func=_cmd_notes)

    p_types = sub.add_parser("types", parents=[common], help="list Zotero item types")
    p_types.set_defaults(func=_cmd_types)

    p_stats = sub.add_parser("stats", parents=[common], help="library counts by type/year")
    p_stats.set_defaults(func=_cmd_stats)

    p_trash = sub.add_parser("trash", parents=[common], help="list trashed items")
    p_trash.set_defaults(func=_cmd_trash)

    p_missing = sub.add_parser("missing-pdfs", parents=[common], help="top items with no PDF")
    p_missing.add_argument("--collection", default="", metavar="名|KEY")
    p_missing.set_defaults(func=_cmd_missing)

    p_dups = sub.add_parser("dups", parents=[common], help="duplicate Better BibTeX citekeys")
    p_dups.set_defaults(func=_cmd_dups)

    p_open = sub.add_parser("open", parents=[common], help="open the first PDF in the OS")
    p_open.add_argument("key", metavar="KEY")
    p_open.set_defaults(func=_cmd_open)

    p_select = sub.add_parser("select", parents=[common], help="在 Zotero 里定位这条目")
    p_select.add_argument("key", metavar="KEY")
    p_select.set_defaults(func=_cmd_select)

    p_next = sub.add_parser("next", parents=[common], help="下一条该处理：缺 PDF 或缺引用键")
    p_next.add_argument("--collection", default="", metavar="名|KEY")
    p_next.set_defaults(func=_cmd_next)

    p_export = sub.add_parser("export", parents=[common], help="write a collection (or library) to a .bib file")
    p_export.add_argument("--collection", default="", metavar="KEY")
    p_export.add_argument("-o", "--out", required=True, metavar="FILE")
    p_export.set_defaults(func=_cmd_export)

    p_desk = sub.add_parser("desk", parents=[common], help="工作台：API、缺 PDF、缺引用键、重复键")
    p_desk.add_argument(
        "--collection",
        default="",
        metavar="名|KEY",
        help="只看这个收藏夹",
    )
    p_desk.add_argument("-o", "--out", default=None, metavar="FILE")
    p_desk.set_defaults(func=_cmd_desk)

    p_draft = sub.add_parser("draft", parents=[common], help="中文精读草稿（只摘本地字段，不编造）")
    p_draft.add_argument("target", metavar="KEY|收藏夹")
    p_draft.add_argument(
        "--collection",
        action="store_true",
        help="把 target 当成收藏夹名或 key",
    )
    p_draft.add_argument("-o", "--out", default=None, metavar="FILE")
    p_draft.set_defaults(func=_cmd_draft)

    p_keys = sub.add_parser("citekeys", parents=[common], help="列出有/无 Better BibTeX 引用键的条目")
    p_keys.add_argument("--missing", action="store_true", help="只列出缺引用键的")
    p_keys.add_argument("--collection", default="", metavar="名|KEY")
    p_keys.set_defaults(func=_cmd_citekeys)

    return parser


def _limit(args: argparse.Namespace) -> int:
    return require_positive_limit(int(getattr(args, "limit", DEFAULT_LIMIT)))


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
    items = client.items(
        query=args.query,
        item_type=getattr(args, "item_type", "") or "",
        tag=getattr(args, "tag", "") or "",
        year=getattr(args, "year", "") or "",
        limit=_limit(args),
    )
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
    col = resolve_collection(client, args.key)
    items = client.items(collection=col.key, limit=_limit(args))
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
    if text and not text.endswith("\n"):
        text += "\n"
    out = getattr(args, "out", None)
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path} ({text.count('@')} entries)")
        return 0
    if _json(args):
        sys.stdout.write(dumps({"bibtex": text}))
        return 0
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


def _cmd_show(args: argparse.Namespace, client: Client) -> int:
    item = client.item(args.key)
    if _json(args):
        sys.stdout.write(dumps(item_payload(item)))
        return 0
    sys.stdout.write(print_card(item))
    return 0


def _cmd_abstract(args: argparse.Namespace, client: Client) -> int:
    item = client.item(args.key)
    text = item.abstract
    if _json(args):
        sys.stdout.write(dumps({"key": item.key, "abstract": text}))
        return 0
    if not text:
        print("no abstract")
        return 1
    print(text)
    return 0


def _cmd_doi(args: argparse.Namespace, client: Client) -> int:
    item = client.item(args.key)
    if _json(args):
        sys.stdout.write(dumps({"key": item.key, "doi": item.doi}))
        return 0
    if not item.doi:
        print("no doi", file=sys.stderr)
        return 1
    print(item.doi)
    return 0


def _cmd_csl(args: argparse.Namespace, client: Client) -> int:
    text = client.citation(args.key, style=args.style)
    if _json(args):
        sys.stdout.write(dumps({"key": args.key, "style": args.style, "citation": text}))
        return 0
    if not text:
        print("no citation", file=sys.stderr)
        return 1
    print(text)
    return 0


def _cmd_notes(args: argparse.Namespace, client: Client) -> int:
    notes = client.child_notes(args.key)
    rows = []
    for note in notes:
        rows.append(
            {
                "key": note.key,
                "text": html_to_text(str(note.data.get("note") or "")),
            }
        )
    if _json(args):
        sys.stdout.write(dumps(rows))
        return 0
    if not rows:
        print("no notes")
        return 0
    for index, row in enumerate(rows):
        if index:
            print()
            print("---")
        print(f"{row['key']}")
        if row["text"]:
            print(row["text"])
    return 0


def _cmd_types(args: argparse.Namespace, client: Client) -> int:
    types = client.item_types()
    if _json(args):
        sys.stdout.write(dumps(types))
        return 0
    for row in types:
        label = row["localized"] or row["itemType"]
        print(f"{row['itemType']}  {label}")
    return 0


def _cmd_stats(args: argparse.Namespace, client: Client) -> int:
    items = client.items(limit=max(_limit(args), 500))
    summary = summarize(items)
    if _json(args):
        sys.stdout.write(dumps(summary))
        return 0
    sys.stdout.write(print_stats(summary))
    return 0


def _cmd_trash(args: argparse.Namespace, client: Client) -> int:
    items = client.trash(limit=_limit(args))
    return _emit_items(items, _json(args))


def _cmd_missing(args: argparse.Namespace, client: Client) -> int:
    items = _scoped_items(args, client)
    missing = missing_pdfs(client, items)
    return _emit_items(missing, _json(args))


def _cmd_dups(args: argparse.Namespace, client: Client) -> int:
    items = client.items(limit=max(_limit(args), 500))
    groups = duplicate_citekeys(items)
    if _json(args):
        payload = {
            key: [item_payload(item) for item in rows] for key, rows in groups.items()
        }
        sys.stdout.write(dumps(payload))
        return 0 if not groups else 1
    if not groups:
        print("no duplicate citekeys")
        return 0
    for key, rows in groups.items():
        print(key)
        for item in rows:
            print("  " + item.row())
    return 1


def _cmd_open(args: argparse.Namespace, client: Client) -> int:
    found = find_pdfs(client, args.key)
    if not found:
        print("no pdfs", file=sys.stderr)
        return 1
    url = found[0].get("url") or ""
    path = _path_from_file_url(url)
    if not path:
        print("no local file url", file=sys.stderr)
        return 1
    _open_path(path)
    print(path)
    return 0


def _cmd_select(args: argparse.Namespace, client: Client) -> int:
    item = client.item(args.key)
    uri = f"zotero://select/library/items/{item.key}"
    if _json(args):
        sys.stdout.write(dumps({"key": item.key, "uri": uri}))
        return 0
    _open_path(uri)
    print(uri)
    return 0


def _cmd_next(args: argparse.Namespace, client: Client) -> int:
    items = parent_items(_scoped_items(args, client, floor=200))
    missing = missing_pdfs(client, items)
    no_key = missing_citekeys(items)
    reason = ""
    picked = None
    if missing:
        picked = missing[0]
        reason = "缺 PDF"
    elif no_key:
        picked = no_key[0]
        reason = "缺引用键"
    if picked is None:
        if _json(args):
            sys.stdout.write(dumps({"item": None, "reason": "clean"}))
            return 0
        print("这批里没有缺 PDF / 缺引用键的条目。")
        return 0
    if _json(args):
        sys.stdout.write(dumps({"reason": reason, "item": item_payload(picked)}))
        return 1
    print(f"下一步（{reason}）")
    print(picked.row())
    print(f"zotlocal draft {picked.key}")
    print(f"zotlocal open {picked.key}")
    print(f"zotlocal select {picked.key}")
    return 1


def _cmd_export(args: argparse.Namespace, client: Client) -> int:
    if args.collection:
        col = resolve_collection(client, args.collection)
        items = client.items(collection=col.key, limit=max(_limit(args), 500))
        keys = [item.key for item in items]
        text = client.bibtex(keys or None, limit=max(_limit(args), 500)) if keys else ""
    else:
        text = client.bibtex(None, limit=max(_limit(args), 500))
    if text and not text.endswith("\n"):
        text += "\n"
    path = Path(args.out).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path} ({text.count('@')} entries)")
    return 0


def _cmd_desk(args: argparse.Namespace, client: Client) -> int:
    col_token = str(getattr(args, "collection", "") or "").strip()
    scope = "全库抽查"
    if col_token:
        col = resolve_collection(client, col_token)
        items = client.items(collection=col.key, limit=max(_limit(args), 200))
        scope = col.path or col.name or col.key
    else:
        items = client.items(limit=max(_limit(args), 200))
    report = desk_report(client, items)
    report["collection"] = scope
    text = render_desk(report)
    out = getattr(args, "out", None)
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path}")
        return 0 if report["ok"] else 1
    if _json(args):
        payload = {
            "ok": report["ok"],
            "collection": scope,
            "items": report["items"],
            "missing_pdfs": report["missing_pdfs"],
            "missing_citekeys": report["missing_citekeys"],
            "duplicate_citekeys": report["duplicate_citekeys"],
            "doctor": report["doctor"],
        }
        sys.stdout.write(dumps(payload))
        return 0 if report["ok"] else 1
    sys.stdout.write(text)
    return 0 if report["ok"] else 1


def _cmd_draft(args: argparse.Namespace, client: Client) -> int:
    target = args.target.strip()
    items: list[Item]
    use_collection = bool(args.collection) or not _looks_item_key(target)
    if use_collection:
        col = resolve_collection(client, target)
        items = parent_items(client.items(collection=col.key, limit=max(_limit(args), 200)))
    else:
        items = [client.item(target)]
        if items[0].item_type in {"attachment", "note"}:
            raise ZotlocalError(f"{target} is {items[0].item_type}, not a parent item")
    if not items:
        print("no items", file=sys.stderr)
        return 1
    names = _collection_name_map(client)
    extras: dict[str, dict] = {}
    for item in items:
        pdf_key = ""
        if len(items) == 1:
            found = find_pdfs(client, item.key)
            if found:
                pdf_key = str(found[0].get("key") or "")
        extras[item.key] = {
            "pdf_key": pdf_key,
            "collection_names": [names.get(key, key) for key in item.collection_keys],
        }
    text = render_drafts(items, extras=extras)
    if not text.endswith("\n"):
        text += "\n"
    out = getattr(args, "out", None)
    if out:
        path = Path(out).expanduser()
        as_dir = path.exists() and path.is_dir() or str(out).endswith(("/", "\\")) or (
            not path.suffix and len(items) > 1
        )
        if as_dir:
            written = write_drafts(items, path, extras)
            print(f"wrote {len(written)} file(s) in {path}")
            return 0
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path}")
        return 0
    if _json(args):
        sys.stdout.write(
            dumps(
                {
                    "count": len(items),
                    "keys": [item.key for item in items],
                    "markdown": text,
                }
            )
        )
        return 0
    sys.stdout.write(text)
    return 0


def _cmd_citekeys(args: argparse.Namespace, client: Client) -> int:
    items = parent_items(_scoped_items(args, client, floor=200))
    missing = missing_citekeys(items)
    if getattr(args, "missing", False):
        rows = missing
    else:
        rows = items
    if _json(args):
        sys.stdout.write(
            dumps(
                [
                    {
                        "key": item.key,
                        "citekey": item.citekey,
                        "title": item.title,
                        "missing": not bool(item.citekey),
                    }
                    for item in rows
                ]
            )
        )
        return 0 if not missing else 1
    if not rows:
        print("no items")
        return 0
    for item in rows:
        mark = "MISSING" if not item.citekey else "OK"
        print(f"{mark}  {item.row()}")
    return 0 if not missing else 1


def _looks_item_key(token: str) -> bool:
    return len(token) == 8 and token.isalnum()


def _scoped_items(
    args: argparse.Namespace,
    client: Client,
    *,
    floor: int = 200,
) -> list[Item]:
    token = str(getattr(args, "collection", "") or "").strip()
    limit = max(_limit(args), floor)
    if not token:
        return client.items(limit=limit)
    col = resolve_collection(client, token)
    return client.items(collection=col.key, limit=limit)


def _collection_name_map(client: Client) -> dict[str, str]:
    return {col.key: (col.path or col.name or col.key) for col in client.collections()}


def _path_from_file_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("file:"):
        parsed = urlparse(url)
        path = unquote(parsed.path or "")
        if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
            path = path[1:]
        return path.replace("/", os.sep) if os.name == "nt" else path
    return url


def _open_path(path: str) -> None:
    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
