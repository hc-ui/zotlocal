# zotlocal

面向 [Zotero](https://www.zotero.org/) Desktop **本地 API** 的只读命令行工具。

[English](README.md) | 简体中文

## 运行条件

必须先打开 Zotero Desktop，并开启本地 API：

**设置 → 高级 → 允许此计算机上的其他应用程序与 Zotero 通信**

（英文界面：Settings → Advanced → Allow other applications on this computer to communicate with Zotero）

保持桌面端在运行。`zotlocal` 只跟这个进程对话。

- 不需要 Zotero Web API key
- 不读取 `prefs.js`
- 不写入文库

## 安装

尚未发布到 PyPI。在本仓库目录中：

```bash
pip install -e .
```

包名：`zotlocal`。需要 Python 3.10+，无第三方依赖。

## 用法

```text
zotlocal doctor
zotlocal search "attention"
zotlocal item PXW99EKT
zotlocal collections --tree
zotlocal bib PXW99EKT
zotlocal pdf PXW99EKT
zotlocal cite "attention"
```

检索结果每条一行：

```text
PXW99EKT  vaswani_attention_2017  2017  Vaswani et al.  Attention Is All You Need
```

列依次为：Zotero item key、citekey（没有则为 `-`）、年份、作者、标题。

### doctor

探测本地 API 与 connector。Zotero 未启动时退出码为 `1`。

```bash
zotlocal doctor
```

### search

检索顶层条目（尽可能排除附件）：

```bash
zotlocal search "attention"
zotlocal search "attention" --limit 10
```

### item

显示单条条目；若有子条目（笔记、附件）会一并给出。

```bash
zotlocal item PXW99EKT
```

### collections

列出分类。`--tree` 打印完整路径（`父分类 / 子分类`）。

```bash
zotlocal collections
zotlocal collections --tree
zotlocal collection AB12CD34
```

### bib

从正在运行的文库导出 BibTeX（`format=bibtex`）。不传 key 时导出最近的一批顶层条目。

```bash
zotlocal bib
zotlocal bib PXW99EKT
zotlocal bib PXW99EKT Q7K2LM9N
```

### pdf

查找条目下的 PDF 附件（若该 key 本身就是附件则查它自己）。只打印本地文件 URL 或路径，不输出文件内容。

```bash
zotlocal pdf PXW99EKT
```

### cite

按 Better BibTeX citekey 或标题检索，打印 Pandoc/Markdown 引用：

```bash
zotlocal cite vaswani_attention_2017
zotlocal cite "Attention Is All You Need"
```

```text
[@vaswani_attention_2017]
```

文库里没有 citekey 时退回 item key（`[@PXW99EKT]`）。**不会编造** citekey。

### 其他只读命令

```bash
zotlocal tags
zotlocal recent
```

没有导入、保存或任何写入文库的命令。

## Citekey 与 Zotero item key

| | 示例 | 含义 |
|---|---|---|
| **Item key** | `PXW99EKT` | Zotero 的 8 位条目 id。给 `item`、`pdf`、`bib`、`collection` 用。 |
| **Citekey** | `vaswani_attention_2017` | Better BibTeX 引用键。`cite` 使用它，检索行里也会显示。 |

citekey 只在 Zotero 里已经存在时才会读出：

1. `data.citationKey`（部分 Better BibTeX 版本）
2. Extra 字段中第一行 `Citation Key: …`
3. 否则为空，改用 item key

## JSON

所有命令都支持 `--json`，方便脚本解析：

```bash
zotlocal doctor --json
zotlocal search "attention" --json
zotlocal item PXW99EKT --json
zotlocal collections --tree --json
```

## 选项

| 参数 | 默认 | |
|---|---|---|
| `--json` | 关 | 输出结构化 JSON |
| `--port` | `23119` | 本地 API 端口 |
| `--timeout` | `5` | HTTP 超时（秒） |
| `--limit` | 因命令而异 | 分页结果上限 |

## 隐私

只向 `127.0.0.1:23119`（或 `--port`）发本地 HTTP。不会访问 `api.zotero.org` 或其他主机。不读 `prefs.js`，不打印凭据，不倾倒附件字节。`pdf` 只返回路径或 `file://` URL。

## 许可

[MIT](LICENSE)
