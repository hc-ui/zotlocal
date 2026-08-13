# Changelog

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
