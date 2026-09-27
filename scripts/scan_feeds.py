#!/usr/bin/env python3
"""
blogwatcher 定期扫描脚本
用法: python3 scan_feeds.py
建议通过 cron 定期执行，每天1-2次
"""
import subprocess
import os
import json
from datetime import datetime

BLOGWATCHER = "/home/hermeswebui/.hermes/home/.local/bin/blogwatcher-cli"
ACADEMIC_DIR = "/home/17635852864/AI/academic"
STATE_FILE = os.path.join(os.path.dirname(__file__), '../config/feed_state.json')

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_blogwatcher(args):
    cmd = f'export PATH="/home/hermeswebui/.hermes/home/.local/bin:$PATH" && {BLOGWATCHER} {" ".join(args)}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def main():
    print(f"🔍 学术 RSS 扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 扫描所有订阅
    out, err, rc = run_blogwatcher(['scan'])
    print(out)
    
    if 'new article' in out.lower() or 'found' in out.lower():
        # 获取新文章列表
        art_out, _, _ = run_blogwatcher(['articles', '--all'])
        
        # 保存扫描结果
        state = load_state()
        state['last_scan'] = datetime.now().isoformat()
        state['last_output'] = art_out[:5000]  # 保留最近5000字符
        save_state(state)
        
        print(f"\n📬 新文章已记录，上次扫描: {state['last_scan']}")
    else:
        print("\n📭 暂无新文章")

if __name__ == '__main__':
    main()
