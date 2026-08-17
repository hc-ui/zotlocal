from __future__ import annotations

from .models import Item


def render_draft(
    item: Item,
    *,
    pdf_key: str = "",
    collection_names: list[str] | None = None,
) -> str:
    cite = item.citekey or ""
    authors = item.authors or ""
    year = item.year or ""
    pub = item.publication or ""
    doi = item.doi or ""
    tags = "、".join(item.tags) if item.tags else ""
    folders = "、".join(collection_names or [])
    abstract = item.abstract.strip() if item.abstract else "（本地条目无摘要，需打开 PDF 或条目页）"
    pdf_line = (
        f"- PDF：`zotero://open-pdf/library/items/{pdf_key}`"
        if pdf_key
        else "- PDF：（本地未找到附件）"
    )
    lines = [
        "---",
        f'title: "{_yaml_escape(item.title or "（无标题）")}"',
        f"citekey: {cite or ''}",
        f"zotero_key: {item.key}",
        "theme:",
        "study_area:",
        "data_source:",
        "methodology:",
        "key_finding:",
        "relevance:",
        "---",
        "",
        f"# {item.title or '（无标题）'}",
        "",
        f"- 条目：`{item.key}`",
        f"- 引用键：`{cite or '（无 Better BibTeX 引用键）'}`",
        f"- 作者：{authors or '（无作者）'}",
        f"- 年份：{year or '（无年份）'}",
        f"- 出处：{pub or '（无期刊/书名）'}",
        f"- DOI：{doi or '（无 DOI）'}",
        f"- 标签：{tags or '（无）'}",
        f"- 收藏夹：{folders or '（无）'}",
        f"- Zotero：`zotero://select/library/items/{item.key}`",
        pdf_line,
        "",
        "> 只读摘录。theme / methodology 等字段留空，不自动编造。",
        "",
        "## 原文摘要摘录",
        "",
        abstract,
        "",
        "## 待人工填写",
        "",
        "- theme：",
        "- study_area：",
        "- data_source：",
        "- methodology：",
        "- key_finding：",
        "- relevance：",
        "",
    ]
    return "\n".join(lines)


def render_drafts(
    items: list[Item],
    *,
    extras: dict[str, dict] | None = None,
) -> str:
    extras = extras or {}
    blocks = []
    for item in items:
        extra = extras.get(item.key) or {}
        blocks.append(
            render_draft(
                item,
                pdf_key=str(extra.get("pdf_key") or ""),
                collection_names=list(extra.get("collection_names") or []),
            )
        )
    return "\n---\n\n".join(blocks)


def _yaml_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')
