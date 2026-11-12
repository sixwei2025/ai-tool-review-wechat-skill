#!/usr/bin/env python3
from __future__ import annotations
"""
Markdown → 公众号草稿 JSON 转换器（AI评测公众号 2.0 · 汇芯红六套骨架版）

核心能力：
1. 内置汇芯红 `#C8102E` 六套骨架 token（ticket / magazine-card / classic-edit / journal / minimal-line / zen-space）。
2. 原生支持 Markdown 表格（渲染为微信兼容的内联斑马纹数据表）、代码围栏（`white-space:pre-wrap` 原件块）、引用块、红点列表、图片与 12px 居中灰图说。
3. 转换后配合 `apply_theme_shell.py` 注入各主题专属开篇卡、目录、编号章节头与 END 尾件。

用法：
    python3 markdown_to_wechat_article.py --md 03-review.md --title "标题" --theme ticket --out article.base.json
    python3 markdown_to_wechat_article.py --list-themes
"""
import argparse
import html
import json
import re
from pathlib import Path

FONT_SANS = (
    "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB',"
    "'Microsoft YaHei',sans-serif"
)
FONT_SERIF = "'Noto Serif SC',Georgia,'Times New Roman','Songti SC',serif"

THEMES = {
    "ticket": {
        "name": "汇芯红·票据",
        "scene": "单品深度实测、首发快评、避坑打假（纸感＋硬阴影＋撕票线）",
        "font": FONT_SANS,
        "title_font": FONT_SANS,
        "body": "14px",
        "lh": "1.9",
        "ls": "0.5px",
        "ink": "#555555",
        "ink_lead": "#1a1a1a",
        "ink_title": "#1a1a1a",
        "grey": "#999999",
        "bg": "#fffef8",
        "pad": "20px",
        "red": "#C8102E",
        "red_deep": "#8B0A1F",
        "red_soft": "#FEF2F2",
        "hair": "#FECACA",
        "card_bg": "#FBF7EC",
        "card_bd": "#1a1a1a",
        "radius": "4px",
        "h2": "ticket",
        "quote_bg": "#FEF2F2",
        "quote_bd": "border-left:4px solid {red};",
        "quote_radius": "border-radius:0 4px 4px 0;",
        "img_bd": "#1a1a1a",
        "img_radius": "4px",
        "code_bg": "#F3F4F6",
    },
    "magazine-card": {
        "name": "汇芯红·杂志卡",
        "scene": "多模型/多工具横评、榜单盘点、选型路由（高密度卡片＋横向目录）",
        "font": FONT_SANS,
        "title_font": FONT_SANS,
        "body": "14px",
        "lh": "1.9",
        "ls": "0.5px",
        "ink": "#374151",
        "ink_lead": "#111827",
        "ink_title": "#111827",
        "grey": "#9CA3AF",
        "bg": "#ffffff",
        "pad": "20px",
        "red": "#C8102E",
        "red_deep": "#991B1B",
        "red_soft": "#FEF2F2",
        "hair": "#FECACA",
        "card_bg": "#F9FAFB",
        "card_bd": "#E5E7EB",
        "radius": "8px",
        "h2": "pill",
        "quote_bg": "#FEF2F2",
        "quote_bd": "border-left:3px solid {red};",
        "quote_radius": "border-radius:0 8px 8px 0;",
        "img_bd": "#E5E7EB",
        "img_radius": "8px",
        "code_bg": "#F3F4F6",
    },
    "classic-edit": {
        "name": "汇芯红·经典编辑",
        "scene": "Agent Skill 深扒、架构拆解、重度教程（引言卡＋看点＋编号章节）",
        "font": FONT_SANS,
        "title_font": FONT_SANS,
        "body": "15px",
        "lh": "1.8",
        "ls": "0.5px",
        "ink": "#374151",
        "ink_lead": "#1C1917",
        "ink_title": "#1C1917",
        "grey": "#9CA3AF",
        "bg": "#ffffff",
        "pad": "10px",
        "red": "#C8102E",
        "red_deep": "#991B1B",
        "red_soft": "#FEF2F2",
        "hair": "#FECACA",
        "card_bg": "#FAFAFA",
        "card_bd": "#E5E7EB",
        "radius": "6px",
        "h2": "bar",
        "quote_bg": "#FEF2F2",
        "quote_bd": "border-left:4px solid {red};",
        "quote_radius": "border-radius:0 8px 8px 0;",
        "img_bd": "#E5E7EB",
        "img_radius": "6px",
        "code_bg": "#F7F7F7",
    },
    "journal": {
        "name": "汇芯红·内刊手记",
        "scene": "工作流复盘、长周期追踪、企业落地算账（内刊头图＋对照表）",
        "font": FONT_SANS,
        "title_font": FONT_SANS,
        "body": "14px",
        "lh": "1.9",
        "ls": "0.2px",
        "ink": "#4d4f46",
        "ink_lead": "#23251d",
        "ink_title": "#23251d",
        "grey": "#9ea096",
        "bg": "#fdfdf8",
        "pad": "8px",
        "red": "#C8102E",
        "red_deep": "#8B0A1F",
        "red_soft": "#F7F5EF",
        "hair": "#bfc1b7",
        "card_bg": "#eeefe9",
        "card_bd": "#bfc1b7",
        "radius": "6px",
        "h2": "journal",
        "quote_bg": "#F7F5EF",
        "quote_bd": "border-left:3px solid {red};",
        "quote_radius": "border-radius:0 6px 6px 0;",
        "img_bd": "#bfc1b7",
        "img_radius": "6px",
        "code_bg": "#f0f1ea",
    },
    "minimal-line": {
        "name": "汇芯红·极简细线",
        "scene": "极客短评、技术边界剖析（细线＋大留白，红点睛 ≤3 处）",
        "font": FONT_SANS,
        "title_font": FONT_SANS,
        "body": "15px",
        "lh": "1.8",
        "ls": "0.3px",
        "ink": "#52525B",
        "ink_lead": "#27272A",
        "ink_title": "#27272A",
        "grey": "#A1A1AA",
        "bg": "#FFFFFF",
        "pad": "10px",
        "red": "#C8102E",
        "red_deep": "#3F3F46",
        "red_soft": "#FAFAFA",
        "hair": "#E4E4E7",
        "card_bg": "#FAFAFA",
        "card_bd": "#E4E4E7",
        "radius": "4px",
        "h2": "hairline",
        "quote_bg": "#FAFAFA",
        "quote_bd": "border-left:3px solid {hair};",
        "quote_radius": "",
        "img_bd": "#E4E4E7",
        "img_radius": "4px",
        "code_bg": "#FAFAFA",
    },
    "zen-space": {
        "name": "汇芯红·禅意留白",
        "scene": "AI 行业深度随笔（衬线金句，图少文精）",
        "font": FONT_SANS,
        "title_font": FONT_SERIF,
        "body": "15px",
        "lh": "1.9",
        "ls": "0.3px",
        "ink": "#525252",
        "ink_lead": "#2B2B2B",
        "ink_title": "#2B2B2B",
        "grey": "#A3A3A3",
        "bg": "#FFFFFF",
        "pad": "16px",
        "red": "#C8102E",
        "red_deep": "#2B2B2B",
        "red_soft": "#FFFFFF",
        "hair": "#E8E8E8",
        "card_bg": "#FAFAFA",
        "card_bd": "#E8E8E8",
        "radius": "2px",
        "h2": "serif",
        "quote_bg": "",
        "quote_bd": "border-top:1px solid {hair};border-bottom:1px solid {hair};",
        "quote_radius": "",
        "img_bd": "#E8E8E8",
        "img_radius": "2px",
        "code_bg": "#FAFAFA",
    },
}

_T = THEMES["ticket"]


def _style(tpl: str) -> str:
    return tpl.format(**_T).strip()


def resolve_theme(name: str) -> str:
    if not name or name.lower() == "auto":
        return "ticket"
    if name not in THEMES:
        raise SystemExit(f"未知主题: {name}\n可选：{', '.join(THEMES)}")
    return name


def p_base() -> str:
    return f"font-family:{_T['font']};"


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        rf'<a href="\2" style="color:{_T["red"]};">\1</a>',
        escaped,
    )
    escaped = re.sub(
        r"`([^`]+)`",
        rf'<span style="background:{_T["code_bg"]};color:{_T["ink_lead"]};padding:2px 6px;border-radius:4px;font-size:13px;font-weight:600;">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"==(.+?)==",
        rf'<span style="background:{_T["hair"]};padding:1px 5px;border-radius:3px;font-weight:600;color:{_T["ink_lead"]};">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"\+\+(.+?)\+\+",
        rf'<span style="border-bottom:2px solid {_T["hair"]};font-weight:600;">\1</span>',
        escaped,
    )
    return re.sub(
        r"\*\*(.+?)\*\*",
        rf'<strong style="color:{_T["red"]};font-weight:600;">\1</strong>',
        escaped,
    )


def body_lines(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() in {"## 正文", "# 正文"}:
            return lines[index + 1 :]
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return lines[index + 1 :]
        raise ValueError("Unclosed YAML frontmatter")
    return lines


def p_style(lead: bool = False) -> str:
    color = _T["ink_lead"] if lead else _T["ink"]
    return (
        f"{p_base()}font-size:{_T['body']};color:{color};line-height:{_T['lh']};"
        f"letter-spacing:{_T['ls']};margin:0 {_T['pad']} 16px;text-align:justify;"
    )


def h2_wrap_style() -> str:
    pad = _T["pad"]
    if _T["h2"] == "serif":
        return f"margin:64px {pad} 20px;padding:0;text-align:center;"
    return f"margin:40px {pad} 18px;padding:0;"


def key_style() -> str:
    bg = _T["quote_bg"]
    bg_css = f"background:{bg};" if bg else ""
    return (
        f"{p_base()}font-size:{_T['body']};color:{_T['ink']};line-height:1.85;"
        f"margin:20px {_T['pad']} 18px;padding:14px 16px;{bg_css}"
        f"{_style(_T['quote_bd'])}{_T['quote_radius']}"
    )


def card_style() -> str:
    return (
        f"{p_base()}font-size:{_T['body']};color:{_T['ink']};line-height:1.8;"
        f"margin:0 {_T['pad']} 10px;padding:13px 15px;background:{_T['card_bg']};"
        f"border:1px solid {_T['card_bd']};border-radius:{_T['radius']};"
    )


def code_style() -> str:
    mono = "'SF Mono',Consolas,Monaco,monospace"
    return (
        f"margin:20px {_T['pad']};padding:14px;background:{_T['code_bg']};"
        f"border:1px solid {_T['card_bd']};border-left:3px solid {_T['red']};border-radius:{_T['radius']};"
        f"font-family:{mono};font-size:13px;line-height:1.7;color:{_T['ink_lead']};"
        f"white-space:pre-wrap;"
    )


def caption_style() -> str:
    return (
        f"{p_base()}font-size:12px;color:{_T['grey']};text-align:center;"
        f"line-height:1.7;margin:8px {_T['pad']} 26px;"
    )


def table_html(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    body = rows[1:]
    th_cells = "".join(
        f'<th style="background:{_T["red"]};color:#ffffff;font-weight:700;padding:8px 10px;text-align:left;font-size:13px;">'
        f'<span leaf="">{inline(c)}</span></th>'
        for c in header
    )
    tr_rows = []
    for idx, r in enumerate(body):
        bg = f"background:{_T['red_soft']};" if idx % 2 == 1 else "background:#ffffff;"
        tds = "".join(
            f'<td style="padding:8px 10px;border-bottom:1px solid {_T["card_bd"]};color:{_T["ink"]};font-size:13px;{bg}">'
            f'<span leaf="">{inline(c)}</span></td>'
            for c in r
        )
        tr_rows.append(f"<tr>{tds}</tr>")
    return (
        f'<section style="margin:20px {_T["pad"]} 24px;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;{p_base()}">'
        f"<thead><tr>{th_cells}</tr></thead>"
        f"<tbody>{''.join(tr_rows)}</tbody></table></section>"
    )


def quote_card_html(sentence: str) -> str:
    return (
        f'<section style="margin:24px {_T["pad"]};padding:18px 20px;'
        f'background:{_T["red_deep"]};border-radius:{_T["radius"]};">'
        f'<p style="margin:0;{p_base()}font-size:16px;line-height:1.8;color:#ffffff;'
        f'font-weight:700;">{inline(sentence)}</p></section>'
    )


def stat_card_html(num: str, desc: str) -> str:
    return (
        f'<section style="margin:20px {_T["pad"]};padding:18px;background:{_T["card_bg"]};'
        f'border:1px solid {_T["card_bd"]};border-radius:{_T["radius"]};'
        f'display:flex;align-items:baseline;">'
        f'<p style="margin:0;flex:none;white-space:nowrap;{p_base()}font-size:32px;'
        f'font-weight:800;color:{_T["red"]};">{inline(num)}</p>'
        f'<p style="margin:0 0 0 12px;{p_base()}font-size:14px;color:{_T["grey"]};'
        f'line-height:1.6;">{inline(desc)}</p></section>'
    )


def compare_card_html(left: tuple, right: tuple) -> str:
    lt, lc = left if left else ("", "")
    rt, rc = right if right else ("", "")
    return (
        f'<section style="margin:20px {_T["pad"]};display:flex;gap:12px;{p_base()}">'
        f'<section style="flex:1;padding:14px;background:{_T["card_bg"]};'
        f'border:1px solid {_T["card_bd"]};border-radius:{_T["radius"]};">'
        f'<p style="margin:0 0 6px;font-size:14px;font-weight:800;color:{_T["grey"]};">{inline(lt)}</p>'
        f'<p style="margin:0;font-size:13px;color:{_T["ink"]};line-height:1.7;">{inline(lc)}</p></section>'
        f'<section style="flex:1;padding:14px;background:{_T["red_soft"]};'
        f'border:1px solid {_T["hair"]};border-radius:{_T["radius"]};">'
        f'<p style="margin:0 0 6px;font-size:14px;font-weight:800;color:{_T["red"]};">{inline(rt)}</p>'
        f'<p style="margin:0;font-size:13px;color:{_T["ink"]};line-height:1.7;">{inline(rc)}</p></section></section>'
    )


def step_card_html(items: list[str]) -> str:
    blocks = []
    for i, item in enumerate(items, 1):
        blocks.append(
            f'<section style="display:flex;align-items:flex-start;margin-bottom:10px;">'
            f'<span style="flex:none;width:24px;height:24px;background:{_T["red"]};'
            f'color:#FFFFFF;font-size:13px;font-weight:800;border-radius:50%;'
            f'text-align:center;line-height:24px;margin-right:10px;{p_base()}">{i}</span>'
            f'<p style="margin:0;flex:1;{p_base()}font-size:{_T["body"]};color:{_T["ink"]};'
            f'line-height:1.7;">{inline(item)}</p></section>'
        )
    return f'<section style="margin:16px {_T["pad"]};{p_base()}">{"".join(blocks)}</section>'


def render_container(ctype: str, lines: list[str]) -> str:
    text = "\n".join(lines).strip()
    if ctype == "quote":
        return quote_card_html(" ".join(l.strip() for l in lines if l.strip()))
    if ctype == "stat":
        first = lines[0].strip() if lines else ""
        num, desc = first.split("|", 1) if "|" in first else (first, "")
        return stat_card_html(num.strip(), desc.strip())
    if ctype == "compare":
        rows = [l for l in lines if l.strip()]
        left = tuple(x.strip() for x in rows[0].split("|", 1)) if rows and "|" in rows[0] else ("", "")
        right = tuple(x.strip() for x in rows[1].split("|", 1)) if len(rows) >= 2 and "|" in rows[1] else ("", "")
        return compare_card_html(left, right)
    if ctype == "step":
        items = [re.sub(r"^\d+\.\s+", "", l).strip() for l in lines if re.match(r"^\d+\.\s+", l.strip())]
        return step_card_html(items)
    return paragraph_html(text)


def h2_html(title: str, index: int) -> str:
    match = re.match(r"^(\d{2})\s*(.+)$", title)
    number, text = match.groups() if match else (f"{index:02d}", title)
    wrap = h2_wrap_style()
    return f'<h2 style="{wrap}">{html.escape(number)} {inline(text)}</h2>'


def h3_html(title: str) -> str:
    return (
        f'<p style="{p_base()}font-size:15px;font-weight:800;color:{_T["ink_title"]};'
        f'margin:26px {_T["pad"]} 12px;padding-left:10px;border-left:3px solid {_T["red"]};line-height:1.4;">'
        f'<span leaf="">{inline(title)}</span></p>'
    )


def image_html(image: str) -> str:
    escaped = html.escape(image)
    return (
        f'<p style="text-align:center;margin:22px {_T["pad"]} 0;">'
        f'<img src="{escaped}" alt="" '
        f'style="max-width:100%;height:auto;border-radius:{_T["img_radius"]};display:block;'
        f'margin:0 auto;border:1px solid {_T["img_bd"]};" /></p>'
    )


def paragraph_html(text: str, *, lead: bool = False) -> str:
    return f'<p style="{p_style(lead)}"><span leaf="">{inline(text)}</span></p>'


def bullet_row_html(text: str, margin: str) -> str:
    return (
        f'<p style="{p_base()}font-size:{_T["body"]};color:{_T["ink"]};line-height:1.85;'
        f'letter-spacing:{_T["ls"]};margin:{margin};padding-left:18px;text-indent:-18px;">'
        f'<span style="color:{_T["red"]};font-size:11px;font-weight:800;">●</span>&nbsp;'
        f'<span leaf="">{inline(text)}</span></p>'
    )


def bullets_html(items: list[str]) -> str:
    rows = []
    for index, item in enumerate(items):
        top = 14 if index == 0 else 0
        bottom = 0 if index == len(items) - 1 else 8
        rows.append(bullet_row_html(item, f"{top}px {_T['pad']} {bottom}px"))
    return "\n".join(rows)


def quote_block_html(values: list[str]) -> str:
    items: list[str] = []
    for value in values:
        match = re.match(r"^[-*]\s+(.+)$", value.strip())
        if not match:
            items = []
            break
        items.append(match.group(1))
    if items:
        rows = []
        for index, item in enumerate(items):
            bottom = 0 if index == len(items) - 1 else 8
            rows.append(bullet_row_html(item, f"0 0 {bottom}px"))
        return f'<section style="{key_style()}">' + "".join(rows) + "</section>"
    lines = [v.strip() for v in values if v.strip()]
    rows = []
    for index, line in enumerate(lines):
        bottom = 0 if index == len(lines) - 1 else 10
        rows.append(
            f'<p style="margin:0 0 {bottom}px;{p_base()}font-size:{_T["body"]};'
            f'color:{_T["ink"]};line-height:1.85;"><span leaf="">{inline(line)}</span></p>'
        )
    return f'<section style="{key_style()}">' + "".join(rows) + "</section>"


def code_block_html(values: list[str]) -> str:
    return f'<section style="{code_style()}">' + html.escape("\n".join(values)) + "</section>"


def container_html() -> str:
    return (
        f'<section style="max-width:677px;margin:0 auto;background:{_T["bg"]};'
        f'font-family:{_T["font"]};color:{_T["ink"]};font-size:{_T["body"]};'
        f'line-height:{_T["lh"]};letter-spacing:{_T["ls"]};overflow-x:hidden;">'
    )


def convert_markdown(lines: list[str], images: list[str] | None) -> str:
    parts = [container_html()]
    images = images or []
    section_count = 0
    in_intro = True
    buffer: list[str] = []
    quote: list[str] = []
    code: list[str] = []
    bullets: list[str] = []
    table_rows: list[list[str]] = []
    in_code = False
    placed: set[str] = set()
    in_container = False
    container_type: str | None = None
    container_lines: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if not buffer:
            return
        text = "".join(buffer).strip()
        buffer.clear()
        if not text:
            return
        if text == "---":
            parts.append(
                f'<hr style="border:none;border-top:1px solid {_T["hair"]};margin:32px {_T["pad"]};">'
            )
            return
        parts.append(paragraph_html(text, lead=in_intro))

    def flush_quote() -> None:
        if quote:
            parts.append(quote_block_html(quote))
            quote.clear()

    def flush_code() -> None:
        if code:
            parts.append(code_block_html(code))
            code.clear()

    def flush_bullets() -> None:
        if bullets:
            parts.append(bullets_html(bullets))
            bullets.clear()

    def flush_table() -> None:
        if table_rows:
            parts.append(table_html(table_rows))
            table_rows.clear()

    def flush_all() -> None:
        flush()
        flush_bullets()
        flush_quote()
        flush_table()

    for raw in lines:
        line = raw.strip()
        if line.startswith(":::"):
            if in_container:
                rendered = render_container(container_type or "", container_lines)
                if rendered:
                    parts.append(rendered)
                container_lines = []
                in_container = False
                container_type = None
                continue
            flush_all()
            in_container = True
            container_type = line[3:].strip().lower()
            container_lines = []
            continue
        if in_container:
            container_lines.append(raw)
            continue
        if line.startswith("```"):
            flush_all()
            if in_code:
                flush_code()
            in_code = not in_code
            continue
        if in_code:
            code.append(raw)
            continue
        # Markdown Table
        if line.startswith("|") and line.endswith("|"):
            flush()
            flush_bullets()
            flush_quote()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
                continue
            table_rows.append(cells)
            continue
        flush_table()

        if line.startswith(">"):
            flush()
            flush_bullets()
            quote.append(line[1:].lstrip())
            continue
        flush_quote()

        pic = re.fullmatch(r"!\[([^\]]*)\]\(([^\s)]+)\)|\[\[img:([^\]]+)\]\]", line)
        if pic:
            flush_all()
            caption, source, legacy = pic.groups()
            source = source or legacy
            parts.append(image_html(source))
            placed.add(source)
            if caption:
                parts.append(f'<p style="{caption_style()}"><span leaf="">— {inline(caption)}</span></p>')
            continue
        if re.fullmatch(r"（[^）]{2,45}）|\([^)]{2,45}\)", line) and parts and "<img " in parts[-1]:
            cap_txt = line[1:-1].strip()
            parts.append(f'<p style="{caption_style()}"><span leaf="">— {inline(cap_txt)}</span></p>')
            continue
        if not line or line.startswith("- ["):
            flush_all()
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flush_all()
            in_intro = False
            section_count += 1
            parts.append(h2_html(line[3:].strip(), section_count))
            continue
        if line.startswith("### "):
            flush_all()
            parts.append(h3_html(line[4:].strip()))
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_all()
            parts.append(f'<p style="{card_style()}"><span leaf="">{inline(line)}</span></p>')
            continue
        if re.match(r"^[-*]\s+", line):
            flush()
            bullets.append(re.sub(r"^[-*]\s+", "", line))
            continue
        buffer.append(line)

    flush_all()
    if in_code:
        raise ValueError("Unclosed code fence")
    unplaced = [
        src for src in images
        if src not in placed and Path(src).name not in {Path(p).name for p in placed}
    ]
    if unplaced:
        raise ValueError("Images need explicit Markdown placement: " + ", ".join(unplaced))
    parts.append("</section>")
    return "\n".join(parts)


def print_themes() -> None:
    print(f"{'id':<16}{'中文名':<16}{'评测适用场景'}")
    print("-" * 72)
    for tid, t in THEMES.items():
        print(f"{tid:<16}{t['name']:<16}{t['scene']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert review Markdown into WeChat draft JSON.")
    parser.add_argument("--md")
    parser.add_argument("--title")
    parser.add_argument("--author", default="袁六伟")
    parser.add_argument("--digest", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--content-image", action="append", default=[])
    parser.add_argument("--out")
    parser.add_argument("--theme", default="ticket", help="ticket | magazine-card | classic-edit | journal | minimal-line | zen-space")
    parser.add_argument("--list-themes", action="store_true")
    args = parser.parse_args()

    if args.list_themes:
        print_themes()
        return
    if not args.md or not args.title or not args.out:
        parser.error("--md / --title / --out 必填")

    global _T
    tid = resolve_theme(args.theme)
    _T = THEMES[tid]

    article = {
        "title": args.title,
        "author": args.author,
        "digest": args.digest[:120],
        "content": convert_markdown(body_lines(Path(args.md)), args.content_image),
        "content_source_url": args.source_url,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
        "pic_crop_235_1": "0_0_1_1",
        "pic_crop_1_1": "0.574468_0_1_1",
    }
    Path(args.out).write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "theme": tid, "theme_name": _T["name"], "out": args.out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
