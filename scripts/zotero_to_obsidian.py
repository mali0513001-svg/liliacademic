#!/usr/bin/env python3
"""
Zotero → Obsidian 同步工具

把 Zotero 文献库中的条目同步为 Obsidian 笔记，每条文献一个 .md 文件。

用法:
  python3 zotero_to_obsidian.py              # 全量同步
  python3 zotero_to_obsidian.py --dry-run    # 只看会做什么，不写入
  python3 zotero_to_obsidian.py --collection "马立"  # 只同步某个分类

特性:
  - 每条文献生成一个 Markdown 笔记，含 YAML frontmatter（可被 Dataview 查询）
  - 自动生成 BibTeX 引用块
  - 已有笔记不会被覆盖（保留你手动写的内容）
  - 生成/更新索引页
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from pyzotero import zotero
except ImportError:
    print("错误: 需要 pyzotero。请运行: pip install pyzotero")
    sys.exit(1)

# 注意: 脚本在容器内运行，Path.home() 会解析到 /home/hermeswebui/.hermes/home
# 实际配置在宿主机路径，需按顺序探测
_CFG_CANDIDATES = [
    Path("/home/hermeswebui/.hermes/config/zotero.json"),
    Path.home() / ".hermes" / "config" / "zotero.json",
    Path("/home/hermeswebui/.hermes/home/.hermes/config/zotero.json"),
]
ZOTERO_CONFIG = next((p for p in _CFG_CANDIDATES if p.exists()), _CFG_CANDIDATES[0])
VAULT = Path("/home/17635852864/AI/Obsidian")
NOTES_DIR = VAULT / "文献笔记"
INDEX_FILE = VAULT / "学术索引.md"

# Zotero 条目类型 → 中文标签
TYPE_MAP = {
    "journalArticle": "期刊论文",
    "book": "书籍",
    "bookSection": "书籍章节",
    "conferencePaper": "会议论文",
    "thesis": "学位论文",
    "report": "报告",
    "webpage": "网页",
    "manuscript": "手稿",
    "preprint": "预印本",
}


def load_client():
    cfg = json.loads(ZOTERO_CONFIG.read_text())
    return zotero.Zotero(cfg["zotero_user_id"], "user", cfg["zotero_api_key"])


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """把标题转成安全的文件名"""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip() + "…"
    return name or "untitled"


def format_creators(creators: list) -> tuple:
    """返回 (作者字符串, 第一作者姓)"""
    names = []
    for c in creators:
        if c.get("creatorType") not in ("author", "editor", None, ""):
            continue
        if c.get("name"):
            names.append(c["name"])
        else:
            last = c.get("lastName", "")
            first = c.get("firstName", "")
            names.append(f"{last}, {first}".strip(", "))
    if not names:
        return "", ""
    first_last = names[0].split(",")[0].strip()
    return "; ".join(names), first_last


def build_bibtex(item: dict) -> str:
    """生成 BibTeX 条目"""
    d = item["data"]
    key = d.get("citationKey") or d.get("key", "unknown")
    itype = {
        "journalArticle": "article",
        "book": "book",
        "bookSection": "incollection",
        "conferencePaper": "inproceedings",
        "thesis": "phdthesis",
        "report": "techreport",
        "webpage": "online",
        "manuscript": "unpublished",
        "preprint": "misc",
    }.get(d.get("itemType", ""), "misc")

    lines = [f"@{itype}{{{key},"]
    if d.get("title"):
        lines.append(f"  title = {{{d['title']}}},")
    authors, _ = format_creators(d.get("creators", []))
    if authors:
        lines.append(f"  author = {{{authors.replace('; ', ' and ')}}},")
    if d.get("publicationTitle"):
        lines.append(f"  journal = {{{d['publicationTitle']}}},")
    if d.get("bookTitle"):
        lines.append(f"  booktitle = {{{d['bookTitle']}}},")
    if d.get("volume"):
        lines.append(f"  volume = {{{d['volume']}}},")
    if d.get("issue"):
        lines.append(f"  number = {{{d['issue']}}},")
    if d.get("pages"):
        lines.append(f"  pages = {{{d['pages']}}},")
    if d.get("date"):
        lines.append(f"  year = {{{d['date'][:4]}}},")
    if d.get("publisher"):
        lines.append(f"  publisher = {{{d['publisher']}}},")
    if d.get("DOI"):
        lines.append(f"  doi = {{{d['DOI']}}},")
    if d.get("url"):
        lines.append(f"  url = {{{d['url']}}},")
    if d.get("language"):
        lines.append(f"  language = {{{d['language']}}},")
    lines.append("}")
    return "\n".join(lines)


def build_note(item: dict) -> str:
    """生成 Obsidian Markdown 笔记"""
    d = item["data"]
    authors, first_last = format_creators(d.get("creators", []))
    title = d.get("title", "无标题")
    year = (d.get("date") or "")[:4]
    itype = TYPE_MAP.get(d.get("itemType", ""), d.get("itemType", ""))
    tags = d.get("tags", [])
    tag_list = [t["tag"] for t in tags] if tags else []
    doi = d.get("DOI", "")
    url = d.get("url", "")

    # YAML frontmatter
    fm = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"authors: {json.dumps(authors, ensure_ascii=False)}" if authors else "authors: []",
        f"year: {year}" if year else "year:",
        f"type: {itype}",
        f"zotero_key: {d.get('key', '')}",
    ]
    if doi:
        fm.append(f"doi: {doi}")
    if d.get("publicationTitle"):
        fm.append(f'journal: "{d["publicationTitle"]}"')
    if tag_list:
        fm.append(f"tags: {json.dumps(tag_list, ensure_ascii=False)}")
    else:
        fm.append("tags: []")
    fm.append(f"synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    fm.append("---")

    # 正文
    body = [
        "",
        f"# {title}",
        "",
        f"> {authors if authors else '未知作者'} · {year if year else '年份未知'} · {itype}",
        "",
    ]

    # 摘要
    abstract = d.get("abstractNote", "").strip()
    if abstract:
        body += ["## 摘要", "", abstract, ""]

    # 我的笔记区（人工填写，同步不覆盖）
    body += [
        "## 我的笔记",
        "",
        "> 这一区域由你手动填写，同步时不会覆盖。",
        "",
        "- ",
        "",
        "## 关键要点",
        "",
        "- ",
        "",
        "## 方法论",
        "",
        "",
        "## 与我研究的关联",
        "",
        "",
        "## 值得引用的句子",
        "",
        "> ",
        "",
    ]

    # BibTeX
    body += ["## BibTeX", "", "```bibtex", build_bibtex(item), "```", ""]

    # 链接
    links = []
    if doi:
        links.append(f"- [DOI](https://doi.org/{doi})")
    if url:
        links.append(f"- [原文链接]({url})")
    links.append(f"- Zotero Key: `{d.get('key', '')}`")
    if links:
        body += ["## 链接", ""] + links + [""]

    return "\n".join(fm + body)


def sync(dry_run=False, collection_name=None):
    z = load_client()
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    # 获取条目
    if collection_name:
        cols = z.collections()
        target = next((c for c in cols if c["data"]["name"] == collection_name), None)
        if not target:
            print(f"❌ 未找到分类: {collection_name}")
            print("   可用分类:", [c["data"]["name"] for c in cols])
            return
        items = z.collection_items(target["key"])
        print(f"📂 分类「{collection_name}」: {len(items)} 条文献")
    else:
        items = z.items()
        print(f"📚 全库: {len(items)} 条文献")

    if not items:
        print("⚠️  文献库为空，请先在 Zotero 添加文献。")
        return

    created, skipped = 0, 0
    index_rows = []

    for item in items:
        d = item["data"]
        if d.get("itemType") in ("attachment", "note", "annotation"):
            continue

        authors, first_last = format_creators(d.get("creators", []))
        year = (d.get("date") or "")[:4]
        title = d.get("title", "无标题")

        # 文件名: 第一作者姓 + 年份 + 标题
        fn_parts = [p for p in [first_last, year] if p]
        fname = " ".join(fn_parts + [title]) if fn_parts else title
        fname = sanitize_filename(fname) + ".md"
        fpath = NOTES_DIR / fname

        if fpath.exists():
            skipped += 1
            print(f"  ⏭️  已存在，跳过: {fname}")
        else:
            if not dry_run:
                fpath.write_text(build_note(item), encoding="utf-8")
            created += 1
            print(f"  ✅ 创建: {fname}")

        index_rows.append((first_last, year, title, fname))

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}完成: 新建 {created}, 跳过 {skipped}")

    # 更新索引
    if not dry_run and index_rows:
        update_index(index_rows)


def update_index(rows: list):
    """更新学术索引页"""
    rows_sorted = sorted(rows, key=lambda r: (r[0] or "zzz", r[1] or "0"))

    lines = [
        "# 学术索引",
        "",
        f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 共 {len(rows)} 篇文献",
        ">",
        "> 手动编辑本文件的内容会在下次同步时被覆盖。",
        "",
        "## 文献列表",
        "",
        "| 作者 | 年份 | 标题 | 笔记 |",
        "|------|------|------|------|",
    ]
    for first_last, year, title, fname in rows_sorted:
        link = f"[[{fname[:-3]}]]"
        lines.append(f"| {first_last or '—'} | {year or '—'} | {title} | {link} |")

    lines += [
        "",
        "---",
        "",
        "## 目录说明",
        "",
        "- `文献笔记/` — 每条 Zotero 文献自动生成的笔记",
        "- `研究专题/` — 按主题整理的研究综述",
        "- `读书笔记/` — 书籍和长篇阅读笔记",
        "- `灵感速记/` — 碎片想法",
        "- `模板/` — 笔记模板",
        "",
    ]
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"📑 索引已更新: {INDEX_FILE}")


def main():
    ap = argparse.ArgumentParser(description="Zotero → Obsidian 同步")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不写入")
    ap.add_argument("--collection", help="只同步指定分类")
    args = ap.parse_args()
    sync(dry_run=args.dry_run, collection_name=args.collection)


if __name__ == "__main__":
    main()
