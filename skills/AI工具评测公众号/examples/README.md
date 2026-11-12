# 2.0 标杆样板间（`examples/sample-topic/`）

本目录展示 **AI 工具评测公众号 Skill 2.0** 的标准输入与输出物：

1. `01-topic-card.example.md` — 选题与压测方案卡样例
2. `02-evidence-ledger.example.md` — 本机实测取证与官网核价台账样例
3. `03-review-article.example.md` — 符合「五幕高密度结构 + ≥2 个原件块 + 2–3 行自然短段（零电报碎句）」的评测正文样稿
4. `article.ticket.example.json` — 经 `markdown_to_wechat_article.py` 转换并由 `apply_theme_shell.py --theme ticket` 注入汇芯红票据外壳、且通过 `validate_review_article.py` 硬闸校验的草稿 JSON 样例
