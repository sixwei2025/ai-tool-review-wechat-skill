# 汇芯红六套骨架（2号排版主题）

默认主色 **`#C8102E`（汇芯红）**，六套骨架按天轮换，不必每次问用哪套。使用者可改主色，但建议整套统一替换，避免混色。

## 三条原则

1. **汇芯红六套骨架**（本目录）— 主色可配置，默认 `#C8102E`
2. **乱码硬闸** — 推箱前消毒：`&quot;`→`"`、去反引号、禁 `*-gradient`（改纯色如 `#FCA5A5`）
3. **只进草稿箱** — 禁止群发；群发须负责人批准

**已废弃**：黑金 heijin / hongjin / moyured 作为默认排版。

## 目录

```
themes/
  README.md
  palette.md
  rotation.md
  references/
    theme-index.md
    common-components.md
    theme-magazine-card.md
    theme-classic-edit.md
    theme-minimal-line.md
    theme-zen-space.md
    theme-ticket.md
    theme-journal.md
```

上游开源骨架提供六套版式差异（开篇组件/密度/装饰/字号）；本目录主色与强调色为汇芯红系。**禁止把六套排成同一套红白。**

## 轮换

见 `rotation.md`：一周约 5～7 篇，一天一骨架。

## 乱码硬闸检查清单（可执行）

推箱前对 HTML 自检，任一项失败则不推：

1. 文本节点不得出现字面量 `&quot;` / `&amp;quot;` → 换成真正的 `"`
2. 正文 HTML 不得残留 Markdown 反引号 `` ` ``
3. 禁止 `linear-` / `radial-` / `conic-gradient` → 改为纯色背景（如 `#FCA5A5`）
4. 图说：12px（或≤13）+ 灰色（`#A3A3A3` / `#9CA3AF`）+ 居中；禁止正文色（15px+#444）当图说
5. 金句标红：汇芯红 `#C8102E` + `font-weight:600`；每篇 3～6 处，勿满篇红
6. 推后用草稿预览确认无乱码

使用者可自备 sanitize/gate 脚本；本开源包不附带含密钥的推箱脚本。
