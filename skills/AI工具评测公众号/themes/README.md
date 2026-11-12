# 汇芯红六套骨架（AI 评测公众号排版唯一来源）

默认主色 **`#C8102E`（汇芯红）**。六套骨架**按评测内容结构与题材选型**（见 `rotation.md`），一篇一套，绝不混搭。

## 三条铁律

1. **按内容选骨架，必跑外壳装配** — 转换后必跑 `scripts/apply_theme_shell.py --theme <id>` 装配主题专属开篇卡、目录短标（每格 3–6 字）、编号章节与 END。
2. **乱码与排版硬闸** — 推箱前由 `scripts/validate_review_article.py` 强制拦截：禁 `<div>`/`class`/`id`、禁双重转义 `&amp;quot;`、禁残留反引号、禁渐变 `*-gradient`、段落 ≤80 字（段均 35–55 字，零电报碎句）、至少 2 个可复制原件块（`white-space:pre-wrap`）。
3. **只进草稿箱** — 默认投递 **2号（`--account hao2`）**，主号（`--account main`）按需切换；只存草稿预览，绝不自动群发。

## 目录结构

```
themes/
  README.md                  ← 本说明
  palette.md                 ← 汇芯红主色板定义
  rotation.md                ← 按评测内容结构选骨架决策表
  references/
    theme-index.md           ← 六套骨架索引与下划线 CSS 权威表
    common-components.md     ← 跨主题通用组件（代码块/图片/GIF/对比表）
    theme-ticket.md          ← 单品评测/避坑首选：票据凭证风
    theme-magazine-card.md   ← 多工具横评/清单首选：杂志快讯卡
    theme-classic-edit.md    ← Skill深扒/深度观点首选：经典编辑风
    theme-journal.md         ← 工作流复盘/长测首选：内刊手记风
    theme-minimal-line.md    ← 极客短评/设计评论：极简细线风
    theme-zen-space.md       ← 行业随笔：禅意留白风
```
