import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 主页
r = requests.get('https://faculty.xmu.edu.cn/GYR/zh_CN/index.htm', headers=headers, timeout=15)
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')

# 提取主要信息
info = {}

# 头像
avatar = soup.select_one('div.photo img')
if avatar:
    info['avatar'] = avatar.get('src', '')

# 姓名、职称
name_title = soup.select_one('div.name-title')
if name_title:
    info['name_title'] = name_title.get_text(strip=True)

# 基本信息区
for row in soup.select('div.info-list div.row, div.info-row'):
    cells = row.select('div')
    if len(cells) >= 2:
        key = cells[0].get_text(strip=True)
        val = cells[1].get_text(strip=True)
        info[key] = val

# 研究方向
research = soup.select_one('div.research-area, div.research-interests, div.zjly')
if research:
    info['research'] = research.get_text(strip=True)

# 个人简介
bio = soup.select_one('div.bio, div.intro, div.profile')
if bio:
    info['bio'] = bio.get_text(strip=True)

# 打印所有文本内容用于调试
print("=== PAGE TEXT ===")
print(soup.get_text(separator='\n', strip=True)[:3000])

print("\n=== INFO ===")
print(json.dumps(info, ensure_ascii=False, indent=2))
