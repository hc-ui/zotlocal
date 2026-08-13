# zotlocal

Read-only CLI for [Zotero](https://www.zotero.org/) Desktop’s local API.

English | [简体中文](README.zh-CN.md)

## Requirements

Zotero Desktop must be running. Enable the local API in:

**Settings → Advanced → Allow other applications on this computer to communicate with Zotero**

Then keep the desktop app open. `zotlocal` talks only to that process.

- No Zotero Web API key
- Does not read `prefs.js`
- Does not write the library

## Install

Not on PyPI yet. From a clone of this repo:

```bash
pip install -e .
```

Package name: `zotlocal`. Requires Python 3.10+. No third-party dependencies.

## Usage

```text
zotlocal doctor
zotlocal search "attention"
zotlocal item PXW99EKT
zotlocal collections --tree
zotlocal bib PXW99EKT
zotlocal pdf PXW99EKT
zotlocal cite "attention"
```

Search results are one row per item:

```text
PXW99EKT  vaswani_attention_2017  2017  Vaswani et al.  Attention Is All You Need
```

Columns: Zotero item key, citekey (or `-`), year, authors, title.

### doctor

Ping the local API and the connector. Exit status `1` if Zotero is down.

```bash
zotlocal doctor
```

### search

Find top-level items (attachments excluded when possible):

```bash
zotlocal search "attention"
zotlocal search "attention" --limit 10
```

### item

Show one item. Children (notes, attachments) are included when present.

```bash
zotlocal item PXW99EKT
```

### collections

List collections. `--tree` prints the full path (`Parent / Child`).

```bash
zotlocal collections
zotlocal collections --tree
zotlocal collection AB12CD34
```

### bib

Export BibTeX from the running library (`format=bibtex`). Omit keys for a recent top-level slice.

```bash
zotlocal bib
zotlocal bib PXW99EKT
zotlocal bib PXW99EKT Q7K2LM9N
```

### pdf

Find PDF attachments under an item (or the item itself if it is an attachment). Prints the local file URL or path only — not file contents.

```bash
zotlocal pdf PXW99EKT
```

### cite

Print a Pandoc/Markdown citation from a Better BibTeX citekey or a title search:

```bash
zotlocal cite vaswani_attention_2017
zotlocal cite "Attention Is All You Need"
```

```text
[@vaswani_attention_2017]
```

If no citekey is stored, the Zotero item key is used (`[@PXW99EKT]`). Citekeys are never invented.

### Other read-only commands

```bash
zotlocal tags
zotlocal recent
```

There are no import, save, or other write commands.

## Citekey vs Zotero item key

| | Example | What it is |
|---|---|---|
| **Item key** | `PXW99EKT` | Zotero’s 8-character id. Use it with `item`, `pdf`, `bib`, `collection`. |
| **Citekey** | `vaswani_attention_2017` | Better BibTeX citation key. Used by `cite` and shown in search rows. |

A citekey is read only if Zotero already has one:

1. `data.citationKey` (some Better BibTeX versions)
2. The first `Citation Key: …` line in Extra
3. Otherwise empty — the item key is shown / used instead

## JSON

Every command accepts `--json` for machine-readable output:

```bash
zotlocal doctor --json
zotlocal search "attention" --json
zotlocal item PXW99EKT --json
zotlocal collections --tree --json
```

## Options

| Flag | Default | |
|---|---|---|
| `--json` | off | Structured JSON instead of text |
| `--port` | `23119` | Local API port |
| `--timeout` | `5` | HTTP timeout in seconds |
| `--limit` | command-specific | Cap paginated results |

## Privacy

Traffic is local HTTP to `127.0.0.1:23119` only (or `--port`). Nothing is sent to `api.zotero.org` or any other host. The CLI does not read `prefs.js`, does not print credentials, and does not dump attachment bytes. `pdf` returns a path or `file://` URL.

## License

[MIT](LICENSE)
