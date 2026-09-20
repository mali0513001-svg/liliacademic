# liliacademic - 学术研究仓库

心理学、管理学、教育学、统计学、英语领域的学术研究工作区。

## 目录结构

```
academic/
├── experiments/     # Jupyter 数据分析 notebook
├── notes/          # Obsidian 笔记
├── papers/         # 论文 PDF
├── references/     # 参考文献
└── scripts/        # 工具脚本
```

## 工具配置

- **Jupyter** - 数据分析环境 (pandas, numpy, scipy, statsmodels, seaborn, sklearn)
- **Zotero** - 文献管理 (用户ID: 21741514)
- **PubMed** - 英文医学/心理学文献搜索
- **CrossRef** - 英文文献元数据

## 使用说明

### 启动 Jupyter
```bash
python3 scripts/start_jupyter.py
```

### 搜索 PubMed 文献
```bash
python3 scripts/pubmed_search.py "关键词" --max 20
```

### 搜索 Zotero 文献
```bash
python3 scripts/zotero_search.py "关键词"
```

---

*由 Hermes Agent 初始化生成*
