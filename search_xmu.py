import requests
from bs4 import BeautifulSoup
import json

query = '厦门大学 郭一蓉'
url = f'https://cn.bing.com/search?q={requests.utils.quote(query)}'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')

results = []
for item in soup.select('li.b_algo')[:10]:
    title_el = item.select_one('h2 a')
    snippet_el = item.select_one('p')
    link = ''
    if title_el:
        link = title_el.get('href', '')
        results.append({
            'title': title_el.get_text(),
            'link': link,
            'snippet': snippet_el.get_text() if snippet_el else ''
        })

print(f"Found {len(results)} results")
print(json.dumps(results, ensure_ascii=False, indent=2))
