# zotlocal spec (v0.1)

Read-only CLI for **Zotero Desktop's local API** on `http://127.0.0.1:23119`.

No Zotero Web API key. No `prefs.js` parsing. No library writes in v0.1.

## Why

Zotero Desktop already has a local Web API v3. Agents and humans still
copy-paste titles by hand. `zotlocal` is a zero-dependency CLI that talks
only to the running desktop app.

## Non-goals (v0.1)

- Import / save / connector writes
- Reading `prefs.js` or printing API keys
- Cloud `api.zotero.org`

## Commands

| Command | Behavior |
|---------|----------|
| `doctor` | Ping `/api/` and `/connector/ping`. Exit 1 if Zotero is down. |
| `search QUERY` | `GET /api/users/0/items?q=&itemType=-attachment` (top-level when possible) |
| `item KEY` | One item + optional children |
| `collections` | List; `--tree` prints paths |
| `collection KEY` | Items in a collection |
| `tags` | List tags |
| `bib [KEY...]` | `format=bibtex` (all or selected keys) |
| `pdf KEY` | Find child attachments; print local file URL/path when asked |
| `recent` | Newest items by dateModified |
| `cite QUERY` | Print a markdown/pandoc citation from BBT key or title search |

Global: `--json`, `--port`, `--timeout`, `--limit`

## Citekey extraction

1. `data.citationKey` if present (some BBT versions)
2. First `Citation Key: ...` line in `data.extra`
3. Else empty (show Zotero item key only)

Never invent citekeys.

## HTTP

- Base: `http://127.0.0.1:{port}` (default 23119)
- Header: `Zotero-API-Version: 3`
- Pagination: `limit` + `start` until empty or `--limit` reached
- Timeouts: default 5s
- Errors: connection refused → "Is Zotero Desktop running? Enable Settings → Advanced → Allow other applications to communicate with Zotero."

## Item row (text)

```
PXW99EKT  vaswani_attention_2017  2017  Vaswani et al.  Attention Is All You Need
```

## Privacy

Do not print file contents unless `pdf`/`fulltext` was requested.
Do not dump prefs or credentials.
Default `pdf` prints the attachment path/URL only.

## Tests

Mock HTTP. Never require a live Zotero in CI.
