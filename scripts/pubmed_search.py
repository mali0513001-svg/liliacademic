#!/usr/bin/env python3
"""
PubMed 文献搜索工具
基于 NCBI E-utilities API，无需 API key，免费使用。

用法:
  python3 pubmed_search.py "关键词"                    # 基本搜索
  python3 pubmed_search.py "关键词" --max 20           # 指定数量
  python3 pubmed_search.py "关键词" --export bibtex    # 导出 BibTeX
  python3 pubmed_search.py "关键词" --export ris       # 导出 RIS
  python3 pubmed_search.py --fetch 33549739            # 获取单篇详情
"""
import sys
import urllib.request
import urllib.parse
import json
import argparse

def pubmed_search(query, max_results=10, export_format=None):
    """搜索 PubMed 文献"""
    # Search
    search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=' + urllib.parse.quote(query) + f'&retmax={max_results}&retmode=json&sort=relevance'
    try:
        with urllib.request.urlopen(search_url, timeout=20) as r:
            search_data = json.loads(r.read())
    except Exception as e:
        print(f"搜索失败: {e}")
        return []
    
    ids = search_data['esearchresult']['idlist']
    if not ids:
        print(f'未找到关于 "{query}" 的结果')
        return []
    
    print(f'🔍 找到 {len(ids)} 条结果 (关键词: "{query}")\n')
    
    # Fetch summaries
    ids_str = ','.join(ids)
    summary_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={ids_str}&retmode=json'
    with urllib.request.urlopen(summary_url, timeout=20) as r:
        summary_data = json.loads(r.read())
    
    results = []
    for uid in ids:
        result = summary_data['result'][uid]
        title = result.get('title', '无标题')
        authors = ', '.join([a['name'] for a in result.get('authors', [])[:4]])
        if len(result.get('authors', [])) > 4:
            authors += ' et al.'
        source = result.get('source', '')
        pubdate = result.get('pubdate', '')[:4]
        doi = result.get('elocationid', '').replace('doi: ', '')
        abstract = result.get('abstract', '')
        
        item = {
            'uid': uid,
            'title': title,
            'authors': authors,
            'source': source,
            'pubdate': pubdate,
            'doi': doi,
            'abstract': abstract
        }
        results.append(item)
        
        print(f'[{uid}] {title}')
        print(f'  📝 {authors} ({pubdate})')
        print(f'  📖 {source}')
        if doi:
            print(f'  🔗 DOI: {doi}')
        print()
    
    # Export if requested
    if export_format == 'bibtex':
        export_bibtex(results)
    elif export_format == 'ris':
        export_ris(results)
    
    return results

def pubmed_fetch(uid):
    """获取单篇文献详细信息"""
    fetch_url = f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={uid}&retmode=xml'
    with urllib.request.urlopen(fetch_url, timeout=20) as r:
        content = r.read().decode('utf-8')
    # 简单解析
    print(content[:3000])

def export_bibtex(results, output_path='pubmed_references.bib'):
    """导出为 BibTeX 格式"""
    lines = []
    for r in results:
        uid = r['uid']
        title = r['title']
        authors = r['authors'].replace(' et al.', '').replace(' and ', ' and ')
        year = r['pubdate']
        journal = r['source']
        doi = r['doi']
        
        first_author = authors.split(',')[0].split(' and ')[0].strip() if authors else 'Unknown'
        bibkey = f"PubMed{year}_{uid}"
        
        lines.append(f"@article{{{bibkey},")
        lines.append(f"  title = {{{title}}},")
        if authors: lines.append(f"  author = {{{authors}}},")
        if year: lines.append(f"  year = {{{year}}},")
        if journal: lines.append(f"  journal = {{{journal}}},")
        if doi: lines.append(f"  doi = {{{doi}}},")
        lines.append(f"  pmid = {{{uid}}},")
        lines.append("}")
        lines.append("")
    
    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ 已导出 {len(results)} 条到 {output_path}")

def export_ris(results, output_path='pubmed_references.ris'):
    """导出为 RIS 格式"""
    lines = []
    for r in results:
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {r['title']}")
        for author in r['authors'].split(', '):
            if author and author != 'et al.':
                lines.append(f"AU  - {author}")
        lines.append(f"PY  - {r['pubdate']}")
        lines.append(f"JO  - {r['source']}")
        if r['doi']: lines.append(f"DO  - {r['doi']}")
        lines.append(f"UR  - https://pubmed.ncbi.nlm.nih.gov/{r['uid']}/")
        lines.append("ER  - ")
        lines.append("")
    
    content = '\n'.join(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ 已导出 {len(results)} 条到 {output_path}")

def main():
    parser = argparse.ArgumentParser(description='PubMed 文献搜索工具')
    parser.add_argument('query', nargs='?', help='搜索关键词')
    parser.add_argument('--max', type=int, default=10, help='最大结果数 (默认10)')
    parser.add_argument('--export', choices=['bibtex', 'ris'], help='导出格式')
    parser.add_argument('--fetch', help='获取单篇 PMID 详情')
    parser.add_argument('--save', help='保存结果到 JSON 文件')
    
    args = parser.parse_args()
    
    if args.fetch:
        print(f"📄 获取 PMID: {args.fetch}\n")
        pubmed_fetch(args.fetch)
        return
    
    if not args.query:
        print("用法: python3 pubmed_search.py '关键词' [--max 20] [--export bibtex|ris]")
        sys.exit(1)
    
    results = pubmed_search(args.query, max_results=args.max, export_format=args.export)
    
    if args.save and results:
        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到 {args.save}")

if __name__ == '__main__':
    main()
