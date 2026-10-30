# 汇芯红主题索引（2号排版）

本表是评测号 **2号排版** 主题信息的单一来源。主色一律汇芯红 `#C8102E`；骨架按天轮换（见 `../rotation.md`），**禁止再问用哪套**。

每个主题英文 id = 文件名去掉 `theme-` 与 `.md`。

## 已注册主题

| 中文名 | 英文 id | 适用场景 | 组件库文件 | 正文下划线 CSS |
|--------|---------|----------|-----------|---------------|
| 汇芯红·杂志卡 | `magazine-card` | 教程、测评、清单、工具盘点（高密度卡片） | `references/theme-magazine-card.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·经典编辑 | `classic-edit` | 深度分析、观点、力量感话题（引言卡+编号章节） | `references/theme-classic-edit.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·极简细线 | `minimal-line` | 设计、科技评论、专业观点（细线+大留白） | `references/theme-minimal-line.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·禅意留白 | `zen-space` | 深度随笔、留白气质稿（衬线金句） | `references/theme-zen-space.md` | `border-bottom:1.5px solid #FECACA;font-weight:500;` |
| 汇芯红·票据 | `ticket` | 测评、工具对比（纸感+硬阴影+撕票线） | `references/theme-ticket.md` | `border-bottom:2px solid #FECACA;font-weight:600;` |
| 汇芯红·内刊手记 | `journal` | 深度评测、案例复盘、系统性说明（内刊头图） | `references/theme-journal.md` | `border-bottom:2px solid #C8102E;font-weight:600;` |

## 轮换与选用

- 默认按 `../rotation.md` 取当天骨架；同日第二篇起在剩余骨架里换。
- **禁止**再问负责人「用哪套」；题材极不匹配时可换相邻骨架，在 STATUS 写一句理由。
- 同一篇文章只用一套主题，不混搭。
- 上游 vendor（摸鱼绿/石墨等原色）只读对照，产物只读本目录。

## 下划线权威

正文关键词下划线一律用上表「正文下划线 CSS」列（红系）。组件库浅色变体可选；以本表为准。

## 与上游关系

骨架源自 `gzh-design` 六套组件库；色板由汇芯改造为 `#C8102E` 系。勿把 upstream vendor 当评测号唯一源。
