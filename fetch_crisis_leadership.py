import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

# Try authors' institutional repositories / Google Scholar
print("=== Google Scholar search ===")
gs_url = 'https://scholar.google.com/scholar?q=Leading+Through+the+Crisis+Crisis+Leadership+Scale+Development+AOM+2023'
r = requests.get(gs_url, headers=headers, timeout=15)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    for item in soup.select('div.gs_r')[:5]:
        title = item.select_one('h3')
        link = item.select_one('a')
        snippet = item.select_one('div.rs_a')
        if title:
            print(f"Title: {title.get_text()}")
        if link:
            print(f"Link: {link.get('href', '')}")
        if snippet:
            print(f"Snippet: {snippet.get_text()}")
        print("---")

# Try researchgate direct
print("\n=== ResearchGate author page ===")
rg_urls = [
    'https://www.researchgate.net/profile/Yi-Jie-Zhang-2',
    'https://www.researchgate.net/profile/Yirong-Guo',
]
for url in rg_urls:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"URL: {url} -> {r.status_code}")

# Try SSRN (often has preprints)
print("\n=== SSRN ===")
ssrn = requests.get(
    'https://papers.ssrn.com/sol3/search_result?SearchKey=Crisis+Leadership+Scale+Development+AOM',
    headers=headers, timeout=15
)
print(f"SSRN: {ssrn.status_code}")
if ssrn.status_code == 200:
    soup = BeautifulSoup(ssrn.text, 'html.parser')
    for item in soup.select('div.result')[:3]:
        print(item.get_text()[:200])
        print("---")

# Try arXiv
print("\n=== arXiv ===")
arxiv = requests.get(
    'https://export.arxiv.org/api/query?search_query=all:crisis+leadership+scale+development&start=0&max_results=5',
    headers=headers, timeout=15
)
print(f"arXiv: {arxiv.status_code}")
if arxiv.status_code == 200:
    print(arxiv.text[:1000])

# Try Bing search for direct PDF link
print("\n=== Bing PDF search ===")
bing = requests.get(
    'https://cn.bing.com/search?q=%22Leading+Through+the+Crisis%22+%22Crisis+Leadership%22+filetype%3Apdf',
    headers=headers, timeout=15
)
print(f"Bing: {bing.status_code}")
if bing.status_code == 200:
    soup = BeautifulSoup(bing.text, 'html.parser')
    for item in soup.select('li.b_algo')[:5]:
        link = item.select_one('a')
        if link:
            href = link.get('href', '')
            if href:
                print(f"Link: {href}")
