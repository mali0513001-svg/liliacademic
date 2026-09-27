import requests
from bs4 import BeautifulSoup
import json
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 1. Scholar@XMU 学者库
url = 'https://scholar.xmu.edu.cn/Authors/Index?id=GuoYiRong'
r = requests.get(url, headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')

print("=== Scholar@XMU ===")
print(soup.title.string if soup.title else 'No title')
print(soup.get_text(separator='\n', strip=True)[:5000])
