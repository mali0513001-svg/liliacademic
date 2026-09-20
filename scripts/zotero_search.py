#!/usr/bin/env python3
"""
Zotero 文献搜索工具
用法:
  python3 zotero_search.py                    # 显示所有文献
  python3 zotero_search.py "关键词"           # 按标题/作者搜索
  python3 zotero_search.py --tag 心理学       # 按标签筛选
  python3 zotero_search.py --type journal     # 按类型筛选 (journal/book/chapter)
  python3 zotero_search.py --export bibtex    # 导出为 BibTeX
"""
import sys
import json
import os
from pyzotero import zotero

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../config/zotero.json')

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_zotero():
    cfg = load_config()
    return zotero.Zotero(cfg['zotero_user_id'], 'user', cfg['zotero_api_key'])

def format_item(item, verbose=False):
    data = item['data']
    title = data.get('title', '无标题')
    itype = data.get('itemType', '?')
    authors = ', '.join([c.get('lastName', '') or c.get('name', '') for c in data.get('creators', [])[:3]])
    year = data.get('publicationYear', data.get('date', '?'))[:4]
    doi = data.get('DOI', '')
    tags = ', '.join(data.get('tags', [])) or ''
    
    line = f"  [{itype}] {title[:60]}"
    if authors: line += f"\n    作者: {authors}"
    line += f"\n    年份: {year}"
    if doi: line += f" | DOI: {doi}"
    if tags and verbose: line += f"\n    标签: {tags}"
    return line

def search_items(query, limit=20):
    zot = get_zotero()
    items = zot.items(limit=limit, q=query)
    return items

def list_all(limit=50):
    zot = get_zotero()
    return zot.items(limit=limit)

def filter_by_tag(tag, limit=50):
    zot = get_zotero()
    return zot.items(limit=limit, tag=tag)

def filter_by_type(item_type, limit=50):
    all_items = zot.items(limit=limit)
    return [i for i in all_items if i['data'].get('itemType') == item_type]

def export_bibtex(items, output_path=None):
    lines = []
    for item in items:
        data = item['data']
        key = item['key']
        itype = data.get('itemType', 'article')
        title = data.get('title', '')
        authors = ' and '.join([c.get('lastName', '') or c.get('name', '') for c in data.get('creators', [])])
        year = data.get('publicationYear', data.get('date', ''))[:4]
        doi = data.get('DOI', '')
        journal = data.get('publicationTitle', data.get('bookTitle', ''))
        
        # BibTeX key
        first_author = data.get('creators', [{}])[0].get('lastName', 'Unknown') if data.get('creators') else 'Unknown'
        bibkey = f"{first_author}{year}_{key[:8]}"
        
        lines.append(f"@article{{{bibkey},")
        lines.append(f"  title = {{{title}}},")
        if authors: lines.append(f"  author = {{{authors}}},")
        if year: lines.append(f"  year = {{{year}}},")
        if journal: lines.append(f"  journal = {{{journal}}},")
        if doi: lines.append(f"  doi = {{{doi}}},")
        lines.append("}")
        lines.append("")
    
    content = '\n'.join(lines)
    if output_path:
        with open(output_path, 'w') as f:
            f.write(content)
        print(f"✅ 已导出 {len(items)} 条到 {output_path}")
    return content

def main():
    args = sys.argv[1:]
    
    if '--help' in args or not args:
        print(__doc__)
        sys.exit(0)
    
    zot = get_zotero()
    total = zot.num_items()
    print(f"📚 Zotero 文献库共 {total} 条\n")
    
    if '--export' in args:
        idx = args.index('--export')
        items = zot.items(limit=500)
        output = args[idx+1] if idx+1 < len(args) else 'references.bib'
        export_bibtex(items, output)
        return
    
    if '--tag' in args:
        idx = args.index('--tag')
        tag = args[idx+1] if idx+1 < len(args) else ''
        print(f"🏷️  标签: {tag}\n")
        items = zot.items(limit=50, tag=tag)
    elif '--type' in args:
        idx = args.index('--type')
        item_type = args[idx+1] if idx+1 < len(args) else ''
        print(f"📋 类型: {item_type}\n")
        all_items = zot.items(limit=100)
        items = [i for i in all_items if i['data'].get('itemType') == item_type]
    else:
        query = ' '.join(args)
        print(f"🔍 搜索: {query}\n")
        items = zot.items(limit=50, q=query)
    
    if not items:
        print("未找到结果")
        return
    
    for item in items:
        print(format_item(item, verbose=True))
        print()

if __name__ == '__main__':
    main()
