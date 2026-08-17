# zotlocal

Read-only CLI for [Zotero](https://www.zotero.org/) Desktop’s local API. No Web API key. No cloud. Does not write your library.

English | [简体中文](README.zh-CN.md)

Zotero must be running, with:

**Settings → Advanced → Allow other applications on this computer to communicate with Zotero**

`zotlocal` talks only to `127.0.0.1`. It does not read `prefs.js`.

## Install

Python 3.10+, zero third-party dependencies. Not on PyPI yet:

```bash
pip install git+https://github.com/hc-ui/zotlocal.git
```

Then: `zotlocal doctor`

## Usage

```text
zotlocal doctor
zotlocal search "attention" --year 2017 --type journalArticle
zotlocal show PXW99EKT
zotlocal csl PXW99EKT --style apa
zotlocal notes PXW99EKT
zotlocal stats
zotlocal missing-pdfs
zotlocal dups
zotlocal bib PXW99EKT -o refs.bib
zotlocal export -o library.bib
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
zotlocal search "attention" --limit 10 --type journalArticle --tag survey --year 2024
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

### Library reports

```bash
zotlocal show PXW99EKT
zotlocal abstract PXW99EKT
zotlocal doi PXW99EKT
zotlocal csl PXW99EKT --style apa
zotlocal notes PXW99EKT
zotlocal stats
zotlocal types
zotlocal trash
zotlocal missing-pdfs
zotlocal dups
zotlocal open PXW99EKT
zotlocal bib PXW99EKT -o refs.bib
zotlocal export -o library.bib --collection AB12CD34
```

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
