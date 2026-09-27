#!/usr/bin/env bash
# Zotero → Obsidian 自动同步
# 用法: ./sync_zotero.sh
# 建议加入 cron 每天自动运行一次

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/home/17635852864/AI/academic/zotero_sync.log"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') 开始同步 =====" >> "$LOG_FILE"

if python3 "$SCRIPT_DIR/zotero_to_obsidian.py" >> "$LOG_FILE" 2>&1; then
    echo "✅ 同步成功" >> "$LOG_FILE"
else
    echo "❌ 同步失败" >> "$LOG_FILE"
    exit 1
fi
