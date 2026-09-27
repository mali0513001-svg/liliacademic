#!/usr/bin/env python3
"""
万方数据搜索 - 通过静态HTML解析获取论文列表
依赖: requests, BeautifulSoup4
注意: 部分内容需要登录才能访问
"""
import sys, os, argparse, urllib.parse, re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ 需要安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www.wanfangdata.com.cn"
SEARCH_URL = f"{BASE_URL}/search/search.do"

def search_wanfang(query, search_type="all", max_results=10):
    """搜索万方数据
    
    Args:
        query: 搜索关键词
        search_type: all/perio/conf/paper/patent/standard/digital
        max_results: 最大结果数
    """
    params = {
        "query": query,
        "searchWord": query,
        "searchType": "all" if search_type == "all" else search_type,
        "page": 1,
        "pageSize": min(max_results, 20),
        "sortType": "rel",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    print(f"🔍 搜索万方: {query} (类型: {search_type})")
    
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=headers, timeout=20)
        resp.encoding = "utf-8"
        html = resp.text
        
        if "登录" in html and "请登录" in html:
            print("⚠️ 需要登录才能获取完整结果，尝试解析页面...")
        
        results = parse_html(html, max_results)
        
        if results:
            print(f"✅ 找到 {len(results)} 条结果\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. {r['title']}")
                if r.get("authors"):
                    print(f"   作者: {r['authors']}")
                if r.get("source"):
                    print(f"   来源: {r['source']}")
                if r.get("date"):
                    print(f"   日期: {r['date']}")
                print(f"   链接: {r['url']}")
                print()
            return results
        else:
            print("⚠️ 未解析到结果，可能是需要登录或页面结构变化")
            print(f"   页面长度: {len(html)} 字节")
            return []
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return []

def parse_html(html, max_results):
    """解析万方搜索结果 HTML"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # 万方数据搜索结果在多种元素中，尝试多种选择器
    # 1. 论文标题通常在 class 包含 "title" 或 "name" 的元素中
    for item in soup.find_all(["div", "li", "tr"], class_=re.compile(r"result|item|title", re.I))[:max_results]:
        title_elem = item.find(class_=re.compile(r"title|name", re.I))
        if not title_elem:
            title_elem = item.find("a")
        if title_elem:
            title = title_elem.get_text(strip=True)
            if len(title) > 5 and title not in ["hot", "论文冲刺加油包"]:
                link = title_elem.get("href", "")
                if link and not link.startswith("http"):
                    link = BASE_URL + link
                
                # 找作者
                author_elem = item.find(class_=re.compile(r"author|writer", re.I))
                authors = author_elem.get_text(strip=True) if author_elem else ""
                
                # 找来源
                source_elem = item.find(class_=re.compile(r"source|journal|perio", re.I))
                source = source_elem.get_text(strip=True) if source_elem else ""
                
                # 找日期
                date_elem = item.find(class_=re.compile(r"date|time|year", re.I))
                date = date_elem.get_text(strip=True) if date_elem else ""
                
                results.append({
                    "title": title,
                    "authors": authors,
                    "source": source,
                    "date": date,
                    "url": link
                })
    
    return results[:max_results]

def main():
    parser = argparse.ArgumentParser(description="万方数据搜索工具")
    parser.add_argument("query", nargs="?", help="搜索关键词")
    parser.add_argument("-t", "--type", default="all", 
                        choices=["all", "perio", "conf", "paper"],
                        help="资源类型 (默认: all)")
    parser.add_argument("-m", "--max", type=int, default=10, help="最大结果数 (默认: 10)")
    parser.add_argument("--export", action="store_true", help="导出为 BibTeX")
    args = parser.parse_args()
    
    if not args.query:
        parser.print_help()
        print("\n示例:")
        print("  python3 wanfang_search.py 心理学 心理健康")
        print("  python3 wanfang_search.py 教育学 -t perio -m 20")
        sys.exit(1)
    
    results = search_wanfang(args.query, args.type, args.max)
    
    if results and args.export:
        bibtex = []
        for i, r in enumerate(results, 1):
            key = f"wanfang_{i}"
            bibtex.append(f"@misc{{{key},")
            bibtex.append(f"  title = {{{r['title']}}},")
            if r.get("authors"):
                bibtex.append(f"  author = {{{r['authors']}}},")
            if r.get("source"):
                bibtex.append(f"  journal = {{{r['source']}}},")
            if r.get("date"):
                bibtex.append(f"  year = {{{r['date']}}},")
            if r.get("url"):
                bibtex.append(f"  url = {{{r['url']}}},")
            bibtex.append("}\n")
        
        fname = "wanfang_references.bib"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("\n".join(bibtex))
        print(f"📚 已导出 BibTeX 到 {fname}")

if __name__ == "__main__":
    main()
