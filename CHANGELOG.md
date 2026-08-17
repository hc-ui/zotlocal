# Changelog

## 0.3.0 — 2026-08-17

- `zotlocal desk`：工作台（API、缺 PDF、缺引用键、重复键）
- `zotlocal draft KEY|收藏夹`：中文精读草稿，只摘本地字段，不编造 theme/methodology
- `zotlocal citekeys`：列出有/无 Better BibTeX 引用键

## 0.2.1 — 2026-08-17

- No arguments now runs `doctor` instead of printing help
- Doctor tips are bilingual (en / 中文)

## 0.2.0 — 2026-08-13

- `show`, `abstract`, `doi`, `csl`, `notes`, `types`, `stats`, `trash`
- `missing-pdfs`, `dups`, `open`, `export -o`
- `search --type --tag --year`
- `bib -o FILE`
- Item cards include DOI, abstract, tags, publication

## 0.1.1 — 2026-08-13

- Parse Zotero Desktop tag objects (`tag` + `meta.numItems`) so `tags` prints names, not raw dicts

## 0.1.0 — 2026-08-13

First release.

- Read-only CLI for Zotero Desktop’s local API on `127.0.0.1:23119`
- Commands: `doctor`, `search`, `item`, `collections`, `collection`, `tags`, `bib`, `pdf`, `recent`, `cite`
- Global flags: `--json`, `--port`, `--timeout`, `--limit`
- Citekeys taken from Better BibTeX (`citationKey` or Extra); never invented
- No Web API key, no `prefs.js`, no library writes
