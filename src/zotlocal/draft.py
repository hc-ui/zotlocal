from __future__ import annotations

from .models import Item


def render_draft(item: Item) -> str:
    cite = item.citekey or "（无 Better BibTeX 引用键）"
    authors = item.authors or "（无作者）"
    year = item.year or "（无年份）"
    pub = item.publication or "（无期刊/书名）"
    doi = item.doi or "（无 DOI）"
    abstract = item.abstract.strip() if item.abstract else "（本地条目无摘要，需打开 PDF 或条目页）"
    lines = [
        f"# {item.title or '（无标题）'}",
        "",
        f"- 条目：`{item.key}`",
        f"- 引用键：`{cite}`",
        f"- 作者：{authors}",
        f"- 年份：{year}",
        f"- 出处：{pub}",
        f"- DOI：{doi}",
        f"- Zotero：`zotero://select/library/items/{item.key}`",
        "",
        "> 只读摘录。theme / methodology 等字段不自动编造，留给精读。",
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


def render_drafts(items: list[Item]) -> str:
    blocks = [render_draft(item) for item in items]
    return "\n---\n\n".join(blocks)
