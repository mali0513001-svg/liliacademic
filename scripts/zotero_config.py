#!/usr/bin/env python3
"""
Zotero Web API 配置脚本
用法: python3 zotero_config.py <user_id> <api_key>
"""
import sys
import json
import os
from pyzotero import zotero

def main():
    if len(sys.argv) != 3:
        print("用法: python3 zotero_config.py <user_id> <api_key>")
        print("获取方式: https://www.zotero.org/settings -> Your user ID -> Create new key")
        sys.exit(1)

    user_id = sys.argv[1]
    api_key = sys.argv[2]

    # 测试连接
    try:
        zot = zotero.Zotero(user_id, 'user', api_key)
        user_info = zot.test_user()
        print(f"✅ 连接成功: {user_info['username']} (ID: {user_info['userID']})")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        sys.exit(1)

    # 保存配置
    config = {
        "zotero_user_id": user_id,
        "zotero_api_key": api_key
    }
    config_path = os.path.join(os.path.dirname(__file__), '../../config/zotero.json')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ 配置已保存到: {config_path}")

    # 获取前5条文献测试
    print("\n📚 最近5条文献:")
    items = zot.items(limit=5)
    for item in items:
        title = item['data'].get('title', '无标题')
        item_type = item['data'].get('itemType', 'unknown')
        print(f"  - [{item_type}] {title[:60]}")

if __name__ == '__main__':
    main()
