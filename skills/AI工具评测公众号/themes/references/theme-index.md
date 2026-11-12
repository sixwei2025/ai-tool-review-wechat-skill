# 汇芯红主题索引（AI 评测号 · 2号/主号通用）

本表是 AI 评测公众号主题信息的单一来源。主色一律汇芯红 `#C8102E`；骨架**按评测题材与内容结构选用**（见 `../rotation.md`），禁止反问负责人「用哪套」。

## 已注册主题

| 中文名 | 英文 id | 评测适用场景 | 组件库文件 | 正文下划线 CSS |
|--------|---------|----------|-----------|---------------|
| 汇芯红·票据 | `ticket` | **单品深度实测、首发快评、避坑打假**（纸感+硬阴影+撕票线） | `references/theme-ticket.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·杂志卡 | `magazine-card` | **多模型/多工具横评、榜单盘点、选型路由**（高密度卡片+横向目录） | `references/theme-magazine-card.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·经典编辑 | `classic-edit` | **Skill/MCP 深扒、架构拆解、重度实操教程**（引言卡+看点+编号章节） | `references/theme-classic-edit.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·内刊手记 | `journal` | **工作流复盘、长周期实测、企业落地算账**（内刊头图+对照表） | `references/theme-journal.md` | `border-bottom:2px solid #C8102E;font-weight:600;` |
| 汇芯红·极简细线 | `minimal-line` | **极客短评、技术边界剖析**（细线+大留白，红点睛 ≤3 处） | `references/theme-minimal-line.md` | `border-bottom:2px solid #52525B;font-weight:600;` |
| 汇芯红·禅意留白 | `zen-space` | **AI 行业观察随笔**（衬线金句，图少文精；清单/横评禁选） | `references/theme-zen-space.md` | `border-bottom:1.5px solid #FECACA;font-weight:500;` |

## 选用与装配铁律

- 同一篇文章只用一套主题，绝不混搭。
- `markdown_to_wechat_article.py --theme <id>` 转换后，必须执行 `apply_theme_shell.py --theme <id>` 注入该主题专属的开篇卡、目录、章节头与 END 尾件。
- 正文段落统一遵循 **2–3 行自然短段（40–60 字，上限 ≤80 字）**，废除旧版「一句一段」碎句切法。
