#!/usr/bin/env python3
"""
PDF 阅读工具 - 从本地 PDF 或 Zotero 条目提取文本

用法:
  python3 read_pdf.py <pdf路径>                    # 读本地 PDF
  python3 read_pdf.py --zotero <item_key>         # 从 Zotero 下载并读取
  python3 read_pdf.py <pdf路径> --pages 1-5       # 只读指定页
  python3 read_pdf.py <pdf路径> --info            # 只显示元信息

依赖: pymupdf (已安装)
"""
import sys
import os
import json
import argparse
import urllib.request

CONFIG_PATH = "/home/hermeswebui/.hermes/config/zotero.json"


def load_zotero_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def download_from_zotero(item_key, out_path):
    """从 Zotero 下载附件到本地"""
    cfg = load_zotero_config()
    uid, key = cfg["zotero_user_id"], cfg["zotero_api_key"]
    # 注意: /file 端点用 Authorization 头会间歇性返回 400,
    # 必须改用 ?key= 查询参数 (2026-09 实测)
    url = f"https://api.zotero.org/users/{uid}/items/{item_key}/file?key={key}"
    req = urllib.request.Request(url, headers={
        "Zotero-API-Version": "3",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data)


def parse_pages(spec):
    """解析 '1-5' 或 '1,3,5' 形式的页码"""
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return pages


def main():
    ap = argparse.ArgumentParser(description="PDF 文本提取工具")
    ap.add_argument("path", nargs="?", help="PDF 文件路径")
    ap.add_argument("--zotero", metavar="ITEM_KEY", help="从 Zotero 获取附件")
    ap.add_argument("--pages", help="页码范围, 如 1-5 或 1,3,5")
    ap.add_argument("--info", action="store_true", help="只显示元信息")
    ap.add_argument("--out", help="输出文本到指定文件")
    args = ap.parse_args()

    import pymupdf

    # 获取 PDF 路径
    path = args.path
    if args.zotero:
        path = path or f"/tmp/zotero_{args.zotero}.pdf"
        if not os.path.exists(path):
            try:
                size = download_from_zotero(args.zotero, path)
                print(f"✅ 已从 Zotero 下载: {size} bytes -> {path}", file=sys.stderr)
            except Exception as e:
                print(f"❌ Zotero 下载失败: {e}", file=sys.stderr)
                return 1
    if not path or not os.path.exists(path):
        print(f"❌ 文件不存在: {path}", file=sys.stderr)
        return 1

    doc = pymupdf.open(path)
    meta = doc.metadata or {}

    if args.info:
        print(f"文件: {path}")
        print(f"页数: {doc.page_count}")
        for k in ("title", "author", "subject", "creationDate"):
            if meta.get(k):
                print(f"{k}: {meta[k]}")
        return 0

    # 提取正文
    if args.pages:
        idxs = [p - 1 for p in parse_pages(args.pages)
                if 1 <= p <= doc.page_count]
    else:
        idxs = range(doc.page_count)

    chunks = []
    for i in idxs:
        txt = doc[i].get_text()
        if len(idxs) > 1 or args.pages:
            chunks.append(f"\n===== 第 {i+1} 页 =====\n{txt}")
        else:
            chunks.append(txt)
    text = "\n".join(chunks)

    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"✅ 已写入 {args.out} ({len(text)} 字符)", file=sys.stderr)
    else:
        print(text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
