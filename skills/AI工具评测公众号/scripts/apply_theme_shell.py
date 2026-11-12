#!/usr/bin/env python3
from __future__ import annotations
"""
全主题专属外壳装配器（AI评测公众号 2.0 · 支持全六套汇芯红骨架）

功能：
把 `markdown_to_wechat_article.py` 产出的基础版式补全为带主题专属开篇封面、目录/三看短标、编号章节头、END 分割线与三连引导的完整公众号 HTML。

支持主题 (`--theme`)：
  - ticket         : 汇芯红·票据（门票凭证开篇 + 星级/等级/撕票线 + 黑底红标章节 + 票据三连区）
  - magazine-card  : 汇芯红·杂志卡（划掉旧认知 + 红黑大字开篇 + 横向滑动目录 + PART胶囊章节）
  - classic-edit   : 汇芯红·经典编辑（白底红光晕引言卡 + 三列看点短标 + 红底编号章节）
  - journal        : 汇芯红·内刊手记（内刊头图卡 + PART竖线编号章节 + 内刊三连区）
  - minimal-line   : 汇芯红·极简细线（上下细线引言 + 三列线框看点 + 48px超大水印数字章节）
  - zen-space      : 汇芯红·禅意留白（衬线居中金句 + 极简目录 + 衬线章节）

用法：
  python3 apply_theme_shell.py \
    --article article.base.json --theme ticket \
    --eyebrow "AI CODING BENCHMARK" --strike "跑分高就等于写代码强" \
    --cover-black "连测4款编程AI" --cover-red1 "最火的" --cover-red2 "被我退订了" \
    --cover-meta "3轮真实工程压测 · 10张实拍对比 · 2份可抄配置单" \
    --grade "A+" --issue-no "042" \
    --parts-short "省流总表|压测考卷|翻车抓包|终极站队" \
    --out article.local-images.json
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

LEAF = '<span leaf="">'
DEFAULT_FORBIDDEN_STRIKES = {"装个工具就能撒手不管", "默认占位旧认知"}


def _short_parts(parts_short: str, titles: list[str]) -> list[tuple[str, str]]:
    if parts_short.strip():
        shorts = [x.strip() for x in parts_short.split("|") if x.strip()]
    else:
        shorts = [re.sub(r"^[\d\s、.·:：]+", "", t)[:6] or f"要点{i+1}" for i, t in enumerate(titles)]
    while len(shorts) < max(len(titles), 3):
        shorts.append(f"看点{len(shorts)+1}")
    return [(s[:6], f"{i+1:02d}") for i, s in enumerate(shorts[: max(len(titles), 3)])]


# ==============================================================================
# 1. ticket（汇芯红·票据）
# ==============================================================================
def shell_ticket(a, parts: list[tuple[str, str]]) -> str:
    tags = [t.strip() for t in a.tags.split("|") if t.strip()] or ["#真实压测", "#避坑指南", "#算账对比"]
    tag_html = "".join(
        f'<section style="font-size:10px;color:#C8102E;border:1px solid #C8102E;padding:3px 9px;">{LEAF}{t}</span></section>'
        for t in tags[:3]
    )
    return (
        '<section style="margin:12px 20px 30px;background:#fffef8;border:2px solid #1a1a1a;box-shadow:4px 4px 0 #1a1a1a;">'
        '<section style="background:#C8102E;padding:10px 18px;display:flex;justify-content:space-between;align-items:center;">'
        f'<section style="color:#fffef8;font-size:11px;letter-spacing:3px;font-weight:700;">{LEAF}{a.eyebrow}</span></section>'
        f'<section style="color:#fffef8;font-size:11px;letter-spacing:2px;">{LEAF}{a.stars}</span></section>'
        '</section>'
        '<section style="display:flex;">'
        '<section style="flex:1;padding:22px 18px;border-right:2px dashed #FECACA;">'
        f'<p style="font-size:12px;color:#999999;margin:0 0 6px;text-decoration:line-through;">{LEAF}{a.strike}</span></p>'
        f'<p style="font-size:22px;font-weight:900;color:#1a1a1a;letter-spacing:0.5px;margin:0 0 4px;line-height:1.25;">{LEAF}{a.cover_black}</span><span style="color:#C8102E;">{LEAF}{a.cover_red1}</span></span></p>'
        f'<p style="font-size:20px;font-weight:900;color:#C8102E;margin:0 0 14px;line-height:1.25;">{LEAF}{a.cover_red2}</span></p>'
        f'<section style="border-top:1px dashed #FECACA;margin-bottom:14px;">{LEAF}<br></span></section>'
        '<section style="font-size:13px;color:#555555;line-height:1.75;padding:10px 12px;background:#FEF2F2;border:1px solid #FECACA;">'
        f'<p style="margin:0;">{LEAF}{a.cover_meta}</span></p>'
        '</section>'
        f'<section style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;">{tag_html}</section>'
        '</section>'
        '<section style="width:52px;padding:14px 4px;display:flex;flex-direction:column;align-items:center;justify-content:space-between;background:#FEF2F2;">'
        '<section style="text-align:center;">'
        f'<p style="font-size:8px;color:#999999;letter-spacing:1px;margin:0;">{LEAF}NO.</span></p>'
        f'<p style="font-size:16px;font-weight:900;color:#C8102E;margin:2px 0 0;">{LEAF}{a.issue_no}</span></p>'
        '</section>'
        f'<section style="font-size:10px;color:#888888;letter-spacing:2px;font-weight:700;text-align:center;line-height:1.3;">{LEAF}实测<br>凭证</span></section>'
        '<section style="text-align:center;">'
        f'<p style="font-size:8px;color:#999999;letter-spacing:1px;margin:0;">{LEAF}GRADE</span></p>'
        f'<p style="font-size:15px;font-weight:900;color:#C8102E;margin:2px 0 0;">{LEAF}{a.grade}</span></p>'
        '</section>'
        '</section>'
        '</section>'
        '<section style="display:flex;justify-content:space-between;align-items:center;padding:0 8px;">'
        f'<section style="flex:1;border-top:2px dashed #FECACA;">{LEAF}<br></span></section>'
        f'<section style="padding:0 8px;font-size:10px;color:#C8102E;">{LEAF}✂</span></section>'
        f'<section style="flex:1;border-top:2px dashed #FECACA;">{LEAF}<br></span></section>'
        '</section>'
        '<section style="padding:8px 18px;display:flex;justify-content:space-between;align-items:center;">'
        f'<p style="font-size:10px;color:#999999;letter-spacing:1px;margin:0;">{LEAF}{a.cover_foot}</span></p>'
        f'<p style="font-size:10px;color:#999999;letter-spacing:1px;margin:0;">{LEAF}{a.date} · VERIFIED</span></p>'
        '</section>'
        '</section>'
    )


def chapter_ticket(num: int, title: str, total: int) -> str:
    badge = f"{num:02d}" if num < total else "END"
    return (
        '<section style="margin:36px 20px 20px;">'
        '<section style="display:flex;align-items:center;gap:10px;padding-bottom:10px;border-bottom:2px solid #1a1a1a;">'
        f'<section style="background:#C8102E;color:#ffffff;font-size:12px;font-weight:800;padding:4px 10px;letter-spacing:1px;">{LEAF}PART {badge}</span></section>'
        f'<p style="font-size:18px;font-weight:800;color:#1a1a1a;letter-spacing:0.5px;margin:0;line-height:1.4;">{LEAF}{title}</span></p>'
        '</section></section>'
    )


# ==============================================================================
# 2. magazine-card（汇芯红·杂志卡）
# ==============================================================================
def shell_magazine(a, parts: list[tuple[str, str]]) -> str:
    toc = []
    for i, (short, sub) in enumerate(parts):
        first = i == 0
        bg = "#C8102E" if first else "#ffffff"
        bd = "none" if first else "1px solid #E5E7EB"
        c1 = "rgba(255,255,255,0.75)" if first else "#9CA3AF"
        c2 = "#ffffff" if first else "#111827"
        label = f"PART {i+1:02d}" if i < len(parts) - 1 else "PART ///"
        toc.append(
            f'<section style="display:inline-block;white-space:normal;vertical-align:top;width:126px;background:{bg};border:{bd};border-radius:12px;padding:12px;margin-right:8px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">'
            f'<p style="font-size:9px;font-weight:700;color:{c1};letter-spacing:1px;margin:0 0 5px;">{LEAF}{label}</span></p>'
            f'<p style="font-size:13px;font-weight:800;color:{c2};margin:0 0 3px;">{LEAF}{short}</span></p>'
            f'<p style="font-size:10px;color:{c1};margin:0;">{LEAF}{sub}</span></p></section>'
        )
    return (
        '<section style="margin:10px 20px 26px;background:#ffffff;border:1.5px solid rgba(200,16,46,0.18);border-radius:18px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.05);">'
        '<section style="padding:26px 24px 22px;">'
        '<section style="display:flex;align-items:center;gap:8px;margin-bottom:20px;">'
        f'<span style="width:6px;height:6px;background:#C8102E;border-radius:50%;">{LEAF}<br></span></span>'
        f'<span style="font-size:11px;font-weight:700;letter-spacing:2px;color:#C8102E;">{LEAF}{a.eyebrow}</span></span>'
        f'<section style="flex:1;height:1px;background:#FEE2E2;">{LEAF}<br></span></section>'
        f'<span style="font-size:10px;color:#9CA3AF;font-weight:600;">{LEAF}{a.date}</span></span></section>'
        f'<p style="font-size:14px;color:#9CA3AF;margin:0 0 6px;text-decoration:line-through;">{LEAF}{a.strike}</span></p>'
        f'<p style="font-size:23px;font-weight:900;color:#111827;margin:0;line-height:1.15;letter-spacing:-1px;">{LEAF}{a.cover_black}</span><span style="color:#C8102E;">{LEAF}{a.cover_red1}</span></span></p>'
        f'<p style="font-size:23px;font-weight:900;color:#C8102E;margin:0 0 14px;line-height:1.15;letter-spacing:-1px;">{LEAF}{a.cover_red2}</span></p>'
        f'<section style="width:44px;height:3px;background:#C8102E;border-radius:2px;margin-bottom:12px;">{LEAF}<br></span></section>'
        f'<p style="font-size:13px;color:#6B7280;margin:0;line-height:1.7;">{LEAF}{a.cover_meta}</span></p></section>'
        '<section style="background:#C8102E;padding:11px 24px;display:flex;align-items:center;justify-content:space-between;">'
        f'<p style="font-size:12px;color:#ffffff;margin:0;font-weight:600;">{LEAF}{a.cover_foot}</span></p>'
        f'<section style="display:flex;gap:6px;"><span style="background:rgba(255,255,255,0.2);padding:2px 7px;border-radius:3px;font-size:9px;color:#ffffff;font-weight:600;">{LEAF}{a.tag1}</span></span>'
        f'<span style="background:rgba(255,255,255,0.2);padding:2px 7px;border-radius:3px;font-size:9px;color:#ffffff;font-weight:600;">{LEAF}{a.tag2}</span></span></section></section></section>'
        '<section style="margin:0 20px 28px;">'
        '<section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">'
        f'<p style="font-size:10px;color:#9CA3AF;margin:0;letter-spacing:1.5px;font-weight:600;">{LEAF}{len(parts)} PARTS · BENCHMARK</span></p>'
        f'<p style="font-size:10px;color:#9CA3AF;margin:0;">{LEAF}横向滑动 →</span></p></section>'
        '<section style="overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap;padding-bottom:6px;">'
        + "".join(toc)
        + "</section></section>"
    )


def chapter_magazine(num: int, title: str, total: int) -> str:
    label = f"PART {num:02d}" if num < total else "PART ///"
    return (
        '<section style="margin:38px 20px 18px;">'
        '<section style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">'
        f'<span style="background:#C8102E;color:#ffffff;font-size:10px;font-weight:800;padding:3px 8px;border-radius:4px;letter-spacing:1px;">{LEAF}{label}</span></span>'
        f'<section style="flex:1;height:1px;background:#E5E7EB;">{LEAF}<br></span></section></section>'
        f'<p style="font-size:20px;font-weight:900;color:#111827;line-height:1.4;margin:0;">{LEAF}{title}</span></p></section>'
    )


# ==============================================================================
# 3. classic-edit（汇芯红·经典编辑）
# ==============================================================================
def shell_classic(a, parts: list[tuple[str, str]]) -> str:
    cards = []
    for i, (short, _) in enumerate(parts[:3]):
        mr = "margin-right:8px;" if i < 2 else ""
        cards.append(
            f'<section style="flex:1;background:#FEF2F2;border-radius:10px;padding:14px 10px;{mr}text-align:center;border:1px solid #FEE2E2;">'
            f'<p style="display:inline-block;background:#C8102E;color:#FFFFFF;font-size:11px;font-weight:800;padding:2px 9px;border-radius:4px;margin:0 0 6px;">{LEAF}{i+1:02d}</span></p>'
            f'<p style="font-size:13px;font-weight:700;color:#1C1917;margin:0;">{LEAF}{short}</span></p></section>'
        )
    return (
        '<section style="margin:10px 10px 26px;background:#ffffff;border-radius:12px;box-shadow:0 4px 24px -4px rgba(200,16,46,0.15);padding:24px 22px 20px;border:1px solid #FEE2E2;">'
        f'<p style="font-size:12px;color:#9CA3AF;margin:0 0 8px;text-decoration:line-through;">{LEAF}{a.strike}</span></p>'
        '<p style="font-size:16px;font-weight:800;color:#1C1917;margin:0 0 10px;line-height:1.75;">'
        f'<span style="background:#C8102E;color:#FFFFFF;padding:2px 8px;border-radius:4px;margin-right:6px;">{LEAF}{a.cover_black}</span></span>'
        f'{LEAF}{a.cover_red1}，</span>'
        f'<span style="color:#C8102E;">{LEAF}{a.cover_red2}</span></span>'
        '</p>'
        f'<p style="font-size:12px;color:#9CA3AF;margin:0;">{LEAF}{a.cover_meta}</span></p>'
        '</section>'
        '<section style="padding:0 10px 28px;">'
        f'<p style="font-size:12px;color:#9CA3AF;margin:0 0 10px;letter-spacing:1px;">{LEAF}📌 本期实测看点</span></p>'
        f'<section style="display:flex;justify-content:space-between;">{"".join(cards)}</section>'
        '</section>'
    )


def chapter_classic(num: int, title: str, total: int) -> str:
    badge = f"{num:02d}" if num < total else "∞"
    return (
        '<section style="margin:42px 10px 22px;">'
        '<section style="display:flex;align-items:center;padding-bottom:12px;border-bottom:3px solid #C8102E;">'
        f'<span style="display:inline-block;background:#C8102E;color:#FFFFFF;font-size:16px;font-weight:900;padding:4px 12px;border-radius:6px;margin-right:12px;">{LEAF}{badge}</span></span>'
        '<section>'
        f'<p style="font-size:10px;color:#C8102E;font-weight:700;letter-spacing:2px;margin:0 0 2px;">{LEAF}PART {num:02d}</span></p>'
        f'<p style="font-size:18px;font-weight:800;color:#1C1917;margin:0;line-height:1.35;">{LEAF}{title}</span></p>'
        '</section></section></section>'
    )


# ==============================================================================
# 4. journal（汇芯红·内刊手记）
# ==============================================================================
def shell_journal(a, parts: list[tuple[str, str]]) -> str:
    return (
        '<section style="margin:8px 8px 26px;background:#fdfdf8;border:1px solid #bfc1b7;border-radius:6px;overflow:hidden;">'
        '<section style="padding:24px 20px 18px;">'
        '<section style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
        f'<span style="width:8px;height:8px;background:#1e1f23;border-radius:50%;display:inline-block;">{LEAF}<br></span></span>'
        f'<span style="font-size:10px;font-weight:700;letter-spacing:2px;color:#65675e;">{LEAF}{a.eyebrow}</span></span>'
        f'<section style="flex:1;height:1px;background:#bfc1b7;">{LEAF}<br></span></section>'
        f'<span style="font-size:10px;color:#9ea096;">{LEAF}{a.date}</span></span>'
        '</section>'
        f'<p style="font-size:13px;color:#9ea096;margin:0 0 6px;text-decoration:line-through;">{LEAF}{a.strike}</span></p>'
        '<p style="font-size:22px;font-weight:800;color:#23251d;margin:0 0 10px;line-height:1.25;">'
        f'{LEAF}{a.cover_black} · </span><span style="border-bottom:3px solid #C8102E;">{LEAF}{a.cover_red1}{a.cover_red2}</span></span>'
        '</p>'
        f'<p style="font-size:13px;color:#65675e;margin:0;line-height:1.7;">{LEAF}{a.cover_meta}</span></p>'
        '</section>'
        '<section style="background:#1e1f23;padding:10px 20px;display:flex;align-items:center;justify-content:space-between;">'
        f'<p style="font-size:12px;color:#ffffff;margin:0;font-weight:600;">{LEAF}{a.cover_foot}</span></p>'
        f'<span style="background:#e5e7e0;color:#23251d;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700;">{LEAF}NO.{a.issue_no}</span></span>'
        '</section></section>'
    )


def chapter_journal(num: int, title: str, total: int) -> str:
    return (
        '<section style="margin:34px 8px 18px;">'
        '<section style="display:flex;align-items:center;gap:12px;padding-bottom:10px;border-bottom:1px solid #bfc1b7;">'
        '<section style="text-align:center;">'
        f'<p style="margin:0;font-size:22px;font-weight:800;color:#C8102E;line-height:1;">{LEAF}{num:02d}</span></p>'
        f'<p style="margin:0;font-size:8px;font-weight:700;color:#9ea096;letter-spacing:1.5px;">{LEAF}PART</span></p>'
        '</section>'
        f'<section style="width:1px;height:30px;background:#bfc1b7;">{LEAF}<br></span></section>'
        f'<p style="margin:0;font-size:17px;font-weight:800;color:#23251d;line-height:1.35;">{LEAF}{title}</span></p>'
        '</section></section>'
    )


# ==============================================================================
# 5. minimal-line & 6. zen-space
# ==============================================================================
def shell_minimal(a, parts: list[tuple[str, str]]) -> str:
    return (
        '<section style="margin:10px 10px 32px;padding:26px 20px 22px;border-top:1px solid #E4E4E7;border-bottom:1px solid #E4E4E7;background:#FFFFFF;">'
        f'<p style="font-size:11px;color:#A1A1AA;letter-spacing:2px;margin:0 0 12px;">{LEAF}{a.eyebrow} · {a.date}</span></p>'
        '<p style="font-size:18px;font-weight:700;color:#27272A;margin:0 0 10px;line-height:1.65;">'
        f'{LEAF}{a.cover_black}，</span><span style="border-bottom:2px solid #C8102E;">{LEAF}{a.cover_red1}{a.cover_red2}</span></span>'
        '</p>'
        f'<p style="font-size:12px;color:#A1A1AA;margin:0;">{LEAF}{a.cover_meta}</span></p>'
        '</section>'
    )


def chapter_minimal(num: int, title: str, total: int) -> str:
    return (
        '<section style="margin:44px 10px 22px;padding-bottom:14px;border-bottom:1px solid #E4E4E7;">'
        f'<p style="font-size:36px;font-weight:900;color:#E4E4E7;margin:0;line-height:1;">{LEAF}{num:02d}</span></p>'
        f'<p style="font-size:18px;font-weight:800;color:#27272A;margin:4px 0 0;line-height:1.4;">{LEAF}{title}</span></p>'
        '</section>'
    )


def footer_block(theme: str, include_cta: bool = True) -> str:
    end_line = (
        '<section style="margin:40px 20px 20px;text-align:center;">'
        '<section style="display:flex;align-items:center;justify-content:center;gap:12px;">'
        f'<span style="width:44px;height:1px;background:#D1D5DB;">{LEAF}<br></span></span>'
        f'<span style="font-size:10px;color:#C8102E;letter-spacing:4px;font-weight:700;">{LEAF}END</span></span>'
        f'<span style="width:44px;height:1px;background:#D1D5DB;">{LEAF}<br></span></span>'
        '</section></section>'
    )
    if not include_cta:
        return end_line
    cta = (
        '<section style="margin:0 20px 28px;padding:16px 18px;background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;text-align:center;">'
        '<p style="margin:0;font-size:14px;color:#374151;line-height:1.75;">'
        f'{LEAF}如果你觉得今天这篇实测帮你省了时间，欢迎</span>'
        f'<strong style="color:#C8102E;font-weight:700;">{LEAF}点赞、在看、转发</span></strong>'
        f'{LEAF}三连，我们下篇硬核实测见。</span>'
        '</p></section>'
    )
    return end_line + cta


def main() -> int:
    ap = argparse.ArgumentParser(description="为公众号草稿 JSON 装配汇芯红六套主题专属外壳")
    ap.add_argument("--article", required=True)
    ap.add_argument("--theme", default="ticket", choices=("ticket", "magazine-card", "classic-edit", "journal", "minimal-line", "zen-space"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default=datetime.date.today().strftime("%Y.%m.%d"))
    ap.add_argument("--eyebrow", default="AI 实测实验室")
    ap.add_argument("--strike", required=True, help="必填：划掉的一句旧认知或盲目吹捧（严禁使用默认词）")
    ap.add_argument("--cover-black", required=True, help="必填：开篇主标题前半句（黑字）")
    ap.add_argument("--cover-red1", required=True, help="必填：开篇核心反差词（红字1）")
    ap.add_argument("--cover-red2", required=True, help="必填：开篇核心结论句（红字2）")
    ap.add_argument("--cover-meta", default="本机真跑实测 · 附完整测试指令与选型路由表")
    ap.add_argument("--cover-foot", default="花真金白银踩坑 · 直接抄结论")
    ap.add_argument("--tag1", default="真跑实测")
    ap.add_argument("--tag2", default="避坑算账")
    ap.add_argument("--tags", default="#真实压测|#避坑指南|#算账对比")
    ap.add_argument("--grade", default="A")
    ap.add_argument("--issue-no", default="001")
    ap.add_argument("--stars", default="★★★★☆")
    ap.add_argument("--parts-short", default="", help="目录短标签（每格3-6字），用 | 分隔")
    ap.add_argument("--no-cta", action="store_true")
    a = ap.parse_args()

    if a.strike.strip() in DEFAULT_FORBIDDEN_STRIKES:
        print("错误：--strike 严禁使用默认占位词，必须按当篇核心反差定制", file=sys.stderr)
        return 2

    art = json.loads(Path(a.article).read_text(encoding="utf-8"))
    c = art["content"]
    if "PART 01" in c and "END" in c:
        print("已装配过主题外壳，跳过")
        return 0

    raw_titles = [
        re.sub(r"^\d+\s*", "", re.sub(r"<[^>]+>", "", m.group(2)).strip())
        for m in re.finditer(r"(<h2[^>]*>)(.*?)(</h2>)", c, flags=re.S)
    ]
    total_ch = max(len(raw_titles), 1)
    idx_counter = [0]

    def repl(m):
        idx_counter[0] += 1
        num = idx_counter[0]
        t = re.sub(r"^\d+\s*", "", re.sub(r"<[^>]+>", "", m.group(2)).strip())
        if a.theme == "ticket":
            return chapter_ticket(num, t, total_ch)
        if a.theme == "magazine-card":
            return chapter_magazine(num, t, total_ch)
        if a.theme == "classic-edit":
            return chapter_classic(num, t, total_ch)
        if a.theme == "journal":
            return chapter_journal(num, t, total_ch)
        return chapter_minimal(num, t, total_ch)

    c, n = re.subn(r"(<h2[^>]*>)(.*?)(</h2>)", repl, c, flags=re.S)
    parts = _short_parts(a.parts_short, raw_titles)

    if a.theme == "ticket":
        shell = shell_ticket(a, parts)
    elif a.theme == "magazine-card":
        shell = shell_magazine(a, parts)
    elif a.theme == "classic-edit":
        shell = shell_classic(a, parts)
    elif a.theme == "journal":
        shell = shell_journal(a, parts)
    else:
        shell = shell_minimal(a, parts)

    m = re.match(r"(<section[^>]*>)", c)
    if not m:
        print("找不到全局容器 <section>", file=sys.stderr)
        return 2
    c = m.group(1) + shell + c[m.end() :]

    idx = c.rfind("</section>")
    c = c[:idx] + footer_block(a.theme, include_cta=not a.no_cta) + c[idx:]
    art["content"] = c
    Path(a.out).write_text(json.dumps(art, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "theme": a.theme,
        "chapters": n,
        "leaf_count": c.count(LEAF),
        "out": a.out,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
