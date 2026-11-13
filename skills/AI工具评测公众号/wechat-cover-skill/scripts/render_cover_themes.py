#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多主题多构图封面渲染器 V4 —— 6 套完全不同空间构图的封面版式，人像必留 + IP 强露出。

6 种空间构图（layout）：
  1. editorial-right   经典左文右人（左侧标题 + 右侧贴底人像 + 汇芯 IP 印章）
  2. portrait-left     左人右文反转（左侧贴底人像 + 右侧大标题 + 品牌铭牌）
  3. bento-grid        Bento 三格拼贴（左上主标题卡 / 左下结论与 IP 卡 + 右侧圆角人像卡）
  4. center-hero       居中刊头 C 位（顶部居中刊头 + 人物正中 + 左主标 / 右结论数字卡）
  5. card-black-split  左档案卡 + 右纯黑大字（左侧米白人像档案卡 + 右侧 62% 纯黑超大白字）
  6. diagonal-cut      斜切杂志海报（12° 斜切双色背景：左上大字标题 + 右下人像特写）

用法：
  python3 render_cover_themes.py --brief brief.json --out out/
  python3 render_cover_themes.py --demo            # 6 种不同空间构图全出
  python3 render_cover_themes.py --list            # 列主题与默认构图
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CUTOUT = ASSETS / "owner_cutout_hd.png"
FACE_BOX = json.loads((ASSETS / "owner_cutout_hd.json").read_text(encoding="utf-8"))["face_box"]

W, H = 2350, 1000
SW = 1080
SQUARE_X = W - H
TEXT_X = 128
SAFE_R = SQUARE_X - 16

SERIF = '"Songti SC","STSong","Source Han Serif SC","Noto Serif CJK SC",serif'
SANS = '"PingFang SC","Noto Sans CJK SC","Helvetica Neue",sans-serif'
LATIN = '"Helvetica Neue","Inter","Arial",sans-serif'

DEFAULT_AUTHOR = "袁六伟 · 台州汇芯"
DEFAULT_IP_TAG = "一人 AI 公司实战派"

LAYOUTS = (
    "editorial-right",
    "portrait-left",
    "bento-grid",
    "center-hero",
    "card-black-split",
    "diagonal-cut",
)

# 兼容旧 layout 名称映射
LAYOUT_ALIAS = {
    "editorial": "editorial-right",
    "masthead": "portrait-left",
    "swiss-grid": "bento-grid",
    "cinema": "center-hero",
    "archive-card": "card-black-split",
    "duotone-split": "diagonal-cut",
}

THEMES = {
    "brand": dict(
        name="汇芯红",
        layout="editorial-right",
        paper="#FAF7F4", paper2="#F2ECE7", ink="#1A1A1A",
        accent="#C8102E", accent_on="#FFFFFF",
        muted="rgba(26,26,26,.54)", hair="rgba(26,26,26,.16)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="normal", grain=False,
        use="经典左文右人 · 通用主力（与正文汇芯红一致）",
    ),
    "paper": dict(
        name="纸本墨",
        layout="portrait-left",
        paper="#F1EFEA", paper2="#E7E3DA", ink="#0A0A0B",
        accent="#C8102E", accent_on="#F1EFEA",
        muted="rgba(10,10,11,.54)", hair="rgba(10,10,11,.20)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="muted", grain=True,
        use="左人右文反转 · 方法论 / 观点 / 教程",
    ),
    "swiss": dict(
        name="瑞士蓝",
        layout="bento-grid",
        paper="#EFF1F5", paper2="#FFFFFF", ink="#0A0A0A",
        accent="#002FA7", accent_on="#FFFFFF",
        card_dark="#111318", card_dark_ink="#F7F8FA",
        muted="rgba(10,10,10,.52)", hair="rgba(10,10,10,.14)",
        family=SANS, weight=500, track="-0.01em",
        brand_family=LATIN, brand_weight=400, brand_track="0.10em",
        small_family=LATIN, small_weight=600, small_track="0.16em",
        portrait="muted", grain=False,
        use="Bento 三格拼贴 · 产品发布 / 工具测评 / 清单",
    ),
    "midnight": dict(
        name="午夜墨",
        layout="center-hero",
        paper="#0B0B0D", paper2="#171410", ink="#ECE2CF",
        accent="#D4A04A", accent_on="#0B0B0D",
        muted="rgba(236,226,207,.54)", hair="rgba(236,226,207,.20)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="warm_dark", grain=True,
        use="居中刊头 C 位 · 重磅复盘 / 搞钱算账 / 深度长文",
    ),
    "kraft": dict(
        name="牛皮纸",
        layout="card-black-split",
        paper="#0E0E10", paper2="#19191D", ink="#F5F2EB",
        accent="#C8102E", accent_on="#FFFFFF",
        card_bg="#F3E7D3", card_ink="#261B11",
        muted="rgba(245,242,235,.58)", hair="rgba(245,242,235,.20)",
        family=SERIF, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.12em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="warm_muted", grain=False,
        use="左档案卡 + 右纯黑大字 · 个人经历 / 案例拆解",
    ),
    "indigo": dict(
        name="靛蓝瓷",
        layout="diagonal-cut",
        paper="#F3F5F8", paper2="#E3E9EF", ink="#0A1F3D",
        accent="#C8102E", accent_on="#FFFFFF",
        split_bg="#132A4A", split_ink="#F3F5F8",
        muted="rgba(10,31,61,.54)", hair="rgba(10,31,61,.18)",
        family=SANS, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.11em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="cool", grain=False,
        use="斜切杂志海报 · AI 工具 / 爆款观点 / 技术拆解",
    ),
}

SHADOW = {
    "midnight": "drop-shadow(0 12px 60px rgba(0,0,0,.75))",
    "paper":    "drop-shadow(18px 8px 40px rgba(0,0,0,.10))",
    "kraft":    "drop-shadow(-14px 6px 36px rgba(60,40,20,.14))",
    "indigo":   "drop-shadow(-24px 8px 46px rgba(0,0,0,.28))",
    "swiss":    "drop-shadow(-12px 4px 28px rgba(0,0,0,.10))",
    "brand":    "drop-shadow(-22px 6px 46px rgba(0,0,0,.12))",
}


# ============================================================ 人像处理
def trim_alpha(im: Image.Image, pad: int = 2) -> Image.Image:
    bb = im.split()[-1].getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def treat_portrait(src: Path, dst: Path, mode: str):
    im = trim_alpha(Image.open(src).convert("RGBA"))
    arr = np.asarray(im).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3:4]
    g = (rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114) / 255.0

    if mode == "warm_dark":
        f = (1.04 - 0.40 * g).clip(0.58, 1.04)[..., None]
        out = rgb * f
        out[..., 0] *= 1.10
        out[..., 2] *= 0.86
    elif mode == "muted":
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = (rgb * 0.72 + gray * 0.28) * 1.01
    elif mode == "warm_muted":
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = (rgb * 0.70 + gray * 0.30) * np.array([1.06, 1.00, 0.92])
    elif mode == "cool":
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = (rgb * 0.58 + gray * 0.42) * np.array([0.95, 0.99, 1.06])
    elif mode == "normal":
        out = rgb * 0.94
    else:
        out = rgb

    merged = np.concatenate([np.clip(out, 0, 255), alpha], axis=-1).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(merged, "RGBA")
    img = ImageEnhance.Sharpness(img).enhance(1.12)
    img.save(dst)
    return dst, im.size


# ============================================================ 公共组件
def _rgba(hexv: str, a: float) -> str:
    h = hexv.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"


def _parse_brief(brief: dict, theme_key: str) -> dict:
    lines = [html.escape(x) for x in brief.get("title_lines", []) if x.strip()]
    raw_layout = brief.get("layout") or THEMES[theme_key]["layout"]
    layout = LAYOUT_ALIAS.get(raw_layout, raw_layout)
    return dict(
        kicker=html.escape(brief.get("kicker", "")),
        brand=html.escape(brief.get("brand", "")),
        lines=lines,
        sub=html.escape(brief.get("subtitle", "")),
        author=html.escape(brief.get("author", DEFAULT_AUTHOR)),
        ip_tag=html.escape(brief.get("ip_tag", DEFAULT_IP_TAG)),
        layout=layout,
    )


def _titles_html(lines: list[str], weight: int, fs_normal: int = 144, fs_accent: int = 176) -> str:
    out = []
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1
        cls = "accent" if last else ""
        w = 400 if last else weight
        fs = fs_accent if last else fs_normal
        out.append(f'<div class="tl {cls}" style="font-size:{fs}px"><span style="font-weight:{w}">{ln}</span></div>')
    return "".join(out)


def _base_css(t: dict, theme_key: str) -> str:
    mix = "screen" if theme_key == "midnight" else "multiply"
    return f"""
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
.cv{{position:relative;width:{W}px;height:{H}px;background:{t['paper']};overflow:hidden;
  font-kerning:normal;-webkit-font-smoothing:antialiased}}
.paper2{{position:absolute;inset:0;
  background:radial-gradient(120% 90% at 22% 18%, {t['paper2']} 0%, transparent 62%)}}
.grain{{position:absolute;inset:0;opacity:.45;mix-blend-mode:{mix};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px;pointer-events:none}}
.tl{{font-family:{t['family']};font-weight:{t['weight']};line-height:1.18;letter-spacing:{t['track']};
  color:{t['ink']};white-space:nowrap}}
.tl.accent{{line-height:1.10;color:{t['accent']}}}
.brand{{font-family:{t['brand_family']};font-weight:{t['brand_weight']};color:{t['ink']};
  letter-spacing:{t['brand_track']};line-height:1;white-space:nowrap}}
.kicker{{display:flex;align-items:center;gap:18px;font-family:{t['small_family']};font-weight:{t['small_weight']};
  font-size:28px;letter-spacing:{t['small_track']};color:{t['muted']};text-transform:uppercase}}
.kicker .sq{{width:11px;height:11px;background:{t['accent']};flex:0 0 auto}}
.sub{{font-family:{t['family']};font-weight:400;font-size:36px;letter-spacing:.08em;color:{t['muted']};white-space:nowrap}}
.ip-seal{{display:inline-flex;align-items:center;gap:14px;border:1.5px solid {t['accent']};
  padding:10px 20px;font-family:{SANS};font-size:23px;font-weight:600;letter-spacing:.10em;color:{t['ink']}}}
.ip-seal .dot{{width:10px;height:10px;background:{t['accent']}}}
"""


# ============================================================ 6 种真正不同的空间构图
def build_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    t = THEMES[theme_key]
    b = _parse_brief(brief, theme_key)
    layout = b["layout"]
    grain = '<div class="grain"></div>' if t["grain"] else ""
    pw_ratio = psize[0] / psize[1]

    # 1) editorial-right：经典左文右人
    if layout == "editorial-right":
        p_h = 1016
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w + 16
        titles = _titles_html(b["lines"], t["weight"], 146, 178)
        css = _base_css(t, theme_key) + f"""
.portrait{{position:absolute;left:{p_left}px;top:68px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,{t['paper']} 0%,{t['paper']} 34%,{_rgba(t['paper'],.96)} 44%,
    {_rgba(t['paper'],.78)} 55%,{_rgba(t['paper'],.35)} 66%,{_rgba(t['paper'],0)} 78%)}}
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1150px;height:{H}px;padding-bottom:96px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:30px}}
.brand{{font-size:98px;margin-bottom:16px}}
.rule{{width:420px;height:2px;background:{t['accent']};margin:36px 0 22px}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:48px;width:1180px;border-top:1px solid {t['hair']};
  padding-top:18px;display:flex;justify-content:space-between;align-items:center}}
.strip-tag{{font-family:{SANS};font-size:23px;letter-spacing:.14em;color:{t['muted']}}}
"""
        body = f"""
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip">
    <div class="ip-seal"><i class="dot"></i><span>{b['author']}</span></div>
    <span class="strip-tag">{b['ip_tag']}</span>
  </div>"""

    # 2) portrait-left：左人右文反转（左侧人像 + 右侧大字排版 + 顶通黑条报头）
    elif layout == "portrait-left":
        p_h = 950
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 144, 178)
        css = _base_css(t, theme_key) + f"""
.top-strip{{position:absolute;left:0;right:0;top:0;height:88px;background:{t['ink']};
  padding:0 96px;display:flex;justify-content:space-between;align-items:center;z-index:1}}
.top-strip .l{{font-family:{SERIF};font-size:32px;font-weight:700;letter-spacing:.18em;color:{t['paper']};
  display:flex;align-items:center;gap:18px}}
.top-strip .l i{{width:12px;height:32px;background:{t['accent']};display:inline-block}}
.top-strip .r{{font-family:{SANS};font-size:22px;letter-spacing:.16em;color:rgba(241,239,234,.75)}}
.portrait{{position:absolute;left:56px;top:98px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:2}}
.txt{{position:absolute;left:990px;top:110px;right:96px;height:780px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:28px}}
.brand{{font-size:92px;margin-bottom:16px}}
.rule{{width:320px;height:3px;background:{t['accent']};margin:34px 0 24px}}
.bottom-right{{position:absolute;left:990px;right:96px;bottom:48px;border-top:1px solid {t['hair']};
  padding-top:16px;display:flex;justify-content:space-between;align-items:center;z-index:3}}
"""
        body = f"""
  <div class="top-strip">
    <span class="l"><i></i><span>HUIXIN · {b['author']}</span></span>
    <span class="r">{b['ip_tag']}</span>
  </div>
  <img class="portrait" src="{portrait_uri}">
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="bottom-right">
    <div class="ip-seal"><i class="dot"></i><span>{b['author']}</span></div>
    <span class="sub" style="font-size:24px">{b['ip_tag']}</span>
  </div>"""

    # 3) bento-grid：现代 Bento 三格圆角卡片拼贴
    elif layout == "bento-grid":
        main_lines = b["lines"][:-1] if len(b["lines"]) > 1 else b["lines"]
        accent_line = b["lines"][-1] if len(b["lines"]) > 1 else ""
        main_html = _titles_html(main_lines, t["weight"], 124, 124)
        p_h = 840
        p_w = round(p_h * pw_ratio)
        css = _base_css(t, theme_key) + f"""
.paper2{{display:none}}
.bento{{position:absolute;inset:48px;display:grid;grid-template-columns:1380px 1fr;
  grid-template-rows:560px 1fr;gap:28px}}
.card-main{{background:#FFFFFF;border-radius:32px;border:1.5px solid {t['hair']};
  padding:56px 64px;display:flex;flex-direction:column;justify-content:center}}
.card-main .kicker{{margin-bottom:24px}}
.card-main .brand{{font-size:84px;margin-bottom:14px}}
.card-accent{{background:{t['accent']};border-radius:32px;padding:42px 64px;
  display:flex;justify-content:space-between;align-items:center;color:#FFFFFF}}
.card-accent .tl.accent{{color:#FFFFFF;font-size:132px;line-height:1}}
.card-accent .meta-r{{text-align:right;display:flex;flex-direction:column;align-items:flex-end;gap:16px}}
.card-accent .sub-w{{font-family:{SANS};font-size:28px;color:rgba(255,255,255,.88);letter-spacing:.08em}}
.card-accent .ip-w{{border:1.5px solid rgba(255,255,255,.55);padding:10px 20px;font-family:{SANS};
  font-size:22px;font-weight:600;letter-spacing:.10em;border-radius:10px}}
.card-person{{grid-column:2;grid-row:1 / span 2;background:#FFFFFF;border-radius:32px;
  border:1.5px solid {t['hair']};position:relative;overflow:hidden}}
.person-top{{position:absolute;left:36px;right:36px;top:32px;display:flex;justify-content:space-between;
  align-items:center;font-family:{SANS};font-size:22px;font-weight:600;color:{t['muted']};z-index:2}}
.person-top .tag{{color:{t['accent']};font-weight:700}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);bottom:-18px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.person-foot{{position:absolute;left:28px;right:28px;bottom:24px;background:rgba(255,255,255,.92);
  border:1.5px solid {t['hair']};border-radius:16px;padding:14px 24px;
  display:flex;justify-content:space-between;align-items:center;z-index:3}}
.person-foot strong{{font-family:{SANS};font-size:25px;color:{t['ink']}}}
.person-foot span{{font-family:{SANS};font-size:20px;color:{t['accent']};font-weight:600}}
"""
        body = f"""
  <div class="bento">
    <div class="card-main">
      <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
      <div class="brand">{b['brand']}</div>
      {main_html}
    </div>
    <div class="card-accent">
      <div class="tl accent"><span style="font-weight:600">{accent_line}</span></div>
      <div class="meta-r">
        <div class="sub-w">{b['sub']}</div>
        <div class="ip-w">{b['author']}</div>
      </div>
    </div>
    <div class="card-person">
      <div class="person-top"><span>FOUNDER</span><span class="tag">● {b['ip_tag']}</span></div>
      <img class="portrait" src="{portrait_uri}">
      <div class="person-foot"><strong>{b['author']}</strong><span>HUIXIN</span></div>
    </div>
  </div>"""

    # 4) center-hero：顶部居中刊头 + 人物坐镇 C 位 + 左侧主标题 / 右侧结论数字卡
    elif layout == "center-hero":
        main_lines = b["lines"][:-1] if len(b["lines"]) > 1 else b["lines"]
        accent_line = b["lines"][-1] if len(b["lines"]) > 1 else ""
        main_html = _titles_html(main_lines, t["weight"], 94, 94)
        p_h = 840
        p_w = round(p_h * pw_ratio)
        css = _base_css(t, theme_key) + f"""
.top-bar{{position:absolute;left:96px;right:96px;top:40px;height:74px;border-bottom:1px solid {t['hair']};
  display:flex;justify-content:space-between;align-items:center}}
.top-bar .center-title{{font-family:{SERIF};font-size:34px;letter-spacing:.26em;color:{t['ink']};font-weight:600}}
.top-bar .side{{font-family:{t['small_family']};font-size:21px;letter-spacing:.18em;color:{t['muted']}}}
.spot{{position:absolute;left:50%;transform:translateX(-50%);top:160px;width:760px;height:760px;border-radius:50%;
  background:radial-gradient(circle, rgba(212,160,74,.22) 0%, transparent 65%);pointer-events:none}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);bottom:-20px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:2}}
.left-col{{position:absolute;left:96px;top:210px;width:720px;height:630px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.left-col .kicker{{margin-bottom:24px}}
.left-col .brand{{font-size:80px;margin-bottom:18px}}
.left-col .tl{{white-space:normal;line-height:1.22}}
.right-col{{position:absolute;right:96px;top:240px;width:640px;height:560px;z-index:3;
  display:flex;flex-direction:column;justify-content:center;align-items:flex-end;text-align:right}}
.num-card{{border:1.5px solid {t['accent']};background:rgba(23,20,16,.88);padding:38px 44px;margin-bottom:28px}}
.num-card .tl.accent{{font-size:122px;line-height:1.05}}
.num-card .tag{{font-family:{SANS};font-size:24px;color:{t['muted']};margin-top:16px;letter-spacing:.10em}}
.foot-center{{position:absolute;left:96px;right:96px;bottom:34px;z-index:4;display:flex;
  justify-content:space-between;align-items:center}}
.foot-pill{{background:{t['accent']};color:{t['accent_on']};padding:8px 22px;font-family:{SANS};
  font-size:22px;font-weight:700;letter-spacing:.12em}}
"""
        body = f"""
  <div class="top-bar">
    <span class="side">{b['kicker']}</span>
    <span class="center-title">HUIXIN · {b['author']}</span>
    <span class="side">{b['ip_tag']}</span>
  </div>
  <div class="spot"></div>
  <img class="portrait" src="{portrait_uri}">
  <div class="left-col">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {main_html}
  </div>
  <div class="right-col">
    <div class="num-card">
      <div class="tl accent"><span style="font-weight:500">{accent_line}</span></div>
      <div class="tag">{b['sub']}</div>
    </div>
    <div class="ip-seal" style="background:rgba(11,11,13,.85)"><i class="dot"></i><span>{b['author']}</span></div>
  </div>
  <div class="foot-center">
    <span class="foot-pill">{b['author']}</span>
    <span class="sub" style="font-size:23px">{b['ip_tag']}</span>
  </div>"""

    # 5) card-black-split：左侧米白人物档案卡 + 右侧 62% 纯黑底超大白金字
    elif layout == "card-black-split":
        card_bg = t.get("card_bg", "#F3E7D3")
        card_ink = t.get("card_ink", "#261B11")
        p_h = 740
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 140, 174)
        css = _base_css(t, theme_key) + f"""
.frame{{position:absolute;left:88px;top:64px;width:720px;height:872px;background:{card_bg};
  border:2px solid rgba(255,255,255,.18);box-shadow:18px 18px 0 {t['accent']};overflow:hidden}}
.frame-top{{height:56px;border-bottom:1px solid rgba(38,27,17,.16);padding:0 28px;
  display:flex;justify-content:space-between;align-items:center;
  font-family:{LATIN};font-size:20px;font-weight:600;letter-spacing:.18em;color:rgba(38,27,17,.6)}}
.frame-body{{position:relative;height:706px;overflow:hidden}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);top:24px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.frame-foot{{height:110px;border-top:2px solid {card_ink};padding:0 28px;background:{card_bg};
  display:flex;justify-content:space-between;align-items:center}}
.frame-foot strong{{font-family:{SERIF};font-size:32px;color:{card_ink}}}
.frame-foot span{{font-family:{SANS};font-size:22px;color:{t['accent']};font-weight:700}}
.txt{{position:absolute;left:920px;top:0;right:96px;height:{H}px;padding-bottom:64px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:28px}}
.brand{{font-size:94px;margin-bottom:16px}}
.tl.accent span{{display:inline-block;background:{t['accent']};color:#FFFFFF;padding:6px 26px 10px;margin-top:8px}}
.rule{{width:360px;height:3px;background:{t['accent']};margin:34px 0 22px}}
.strip-r{{position:absolute;left:920px;right:96px;bottom:48px;border-top:1px solid {t['hair']};
  padding-top:16px;display:flex;justify-content:space-between;align-items:center;
  font-family:{SANS};font-size:23px;color:{t['muted']}}}
"""
        body = f"""
  <div class="frame">
    <div class="frame-top"><span>HUIXIN ARCHIVE</span><span>FOUNDER</span></div>
    <div class="frame-body"><img class="portrait" src="{portrait_uri}"></div>
    <div class="frame-foot"><strong>{b['author']}</strong><span>{b['ip_tag']}</span></div>
  </div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip-r"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 6) diagonal-cut：12° 斜切双色海报（左上浅底标题 + 右下深靛蓝斜切区人像）
    else:
        split_bg = t.get("split_bg", "#132A4A")
        p_h = 980
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 124, 156)
        css = _base_css(t, theme_key) + f"""
.diag-bg{{position:absolute;left:1260px;top:-160px;width:1500px;height:1400px;background:{split_bg};
  transform:rotate(11deg);transform-origin:top left;border-left:14px solid {t['accent']};z-index:1}}
.portrait{{position:absolute;right:76px;top:64px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:2}}
.diag-badge{{position:absolute;right:48px;top:48px;border:1.5px solid rgba(255,255,255,.45);
  padding:10px 22px;font-family:{SANS};font-size:23px;font-weight:600;letter-spacing:.12em;
  color:#FFFFFF;background:rgba(19,42,74,.92);z-index:3}}
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1120px;height:{H}px;padding-bottom:76px;
  display:flex;flex-direction:column;justify-content:center;z-index:3}}
.kicker{{margin-bottom:26px}}
.brand{{font-size:88px;margin-bottom:14px}}
.tl.accent span{{display:inline-block;background:{t['accent']};color:#FFFFFF;padding:8px 28px 12px;margin-top:8px}}
.rule{{width:340px;height:3px;background:{t['accent']};margin:32px 0 22px}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:46px;z-index:3;display:flex;align-items:center;gap:28px}}
.strip-tag{{font-family:{SANS};font-size:23px;color:{t['muted']};letter-spacing:.10em}}
"""
        body = f"""
  <div class="diag-bg"></div>
  <img class="portrait" src="{portrait_uri}">
  <div class="diag-badge">{b['author']}</div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip">
    <div class="ip-seal"><i class="dot"></i><span>{b['author']}</span></div>
    <span class="strip-tag">{b['ip_tag']}</span>
  </div>"""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="cv theme-{theme_key} layout-{layout}">
  <div class="paper2"></div>{grain}{body}
</div></body></html>"""


# ============================================================ 1:1 竖版分享卡
def build_square_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    t = THEMES[theme_key]
    b = _parse_brief(brief, theme_key)
    layout = b["layout"]
    pw = 500
    ph = round(pw * psize[1] / psize[0])
    pl = 440
    pt = SW - ph + 90
    titles = _titles_html(b["lines"], t["weight"], 88, 126)
    grain = '<div class="grain"></div>' if t["grain"] else ""

    extra_css = ""
    extra_dom = ""
    if layout == "diagonal-cut":
        split_bg = t.get("split_bg", "#132A4A")
        extra_css = f".sq-band{{position:absolute;left:-80px;right:-80px;bottom:-80px;height:480px;background:{split_bg};border-top:10px solid {t['accent']};transform:rotate(-5deg)}}"
        extra_dom = '<div class="sq-band"></div>'
    elif layout == "card-black-split":
        extra_css = f".sq-frame{{position:absolute;right:48px;bottom:48px;width:480px;height:460px;border:2px solid {t['ink']};background:{t.get('card_bg','#F3E7D3')};box-shadow:12px 12px 0 {t['accent']}}}"
        extra_dom = '<div class="sq-frame"></div>'
        pw, ph, pl, pt = 430, round(430 * psize[1] / psize[0]), 530, SW - round(430 * psize[1] / psize[0]) + 40
    elif layout == "bento-grid":
        extra_css = f".sq-top{{position:absolute;left:0;top:0;width:100%;height:16px;background:{t['accent']}}}"
        extra_dom = '<div class="sq-top"></div>'
    elif layout == "portrait-left":
        pl = 80

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{SW}px;height:{SW}px;overflow:hidden}}
.cv{{position:relative;width:{SW}px;height:{SW}px;background:{t['paper']};overflow:hidden}}
.paper2{{position:absolute;inset:0;background:radial-gradient(120% 80% at 26% 14%,{t['paper2']} 0%,transparent 60%)}}
.grain{{position:absolute;inset:0;opacity:.45;mix-blend-mode:{"screen" if theme_key=="midnight" else "multiply"};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px}}
{extra_css}
.portrait{{position:absolute;left:{pl}px;top:{pt}px;width:{pw}px;height:{ph}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,{t['paper']} 0%,{t['paper']} 45%,{_rgba(t['paper'],.90)} 51%,{_rgba(t['paper'],0)} 62%)}}
.inner{{position:absolute;left:74px;top:86px;width:930px}}
.kicker{{display:flex;align-items:center;gap:16px;font-family:{t['small_family']};
  font-weight:{t['small_weight']};font-size:25px;letter-spacing:{t['small_track']};
  color:{t['muted']};text-transform:uppercase;margin-bottom:24px}}
.kicker .sq{{width:10px;height:10px;background:{t['accent']}}}
.brand{{font-family:{t['brand_family']};font-weight:{t['brand_weight']};font-size:74px;
  letter-spacing:{t['brand_track']};color:{t['ink']};line-height:1;margin-bottom:14px}}
.tl{{font-family:{t['family']};font-weight:{t['weight']};line-height:1.16;
  letter-spacing:{t['track']};color:{t['ink']};white-space:nowrap}}
.tl.accent{{color:{t['accent']};line-height:1.10}}
.rule{{width:280px;height:2px;background:{t['accent']};margin:30px 0 20px}}
.sub{{font-family:{t['family']};font-size:30px;letter-spacing:.08em;color:{t['muted']};white-space:nowrap}}
.strip{{position:absolute;left:74px;bottom:48px;font-family:{SANS};font-weight:600;
  font-size:23px;letter-spacing:.12em;color:{t['ink']};background:{_rgba(t['paper'],.88)};padding:8px 16px;border-left:4px solid {t['accent']}}}
</style></head><body>
<div class="cv theme-{theme_key}-sq layout-{layout}">
  <div class="paper2"></div>{grain}{extra_dom}
  <img class="portrait" src="{portrait_uri}">
  {"<div class='tint'></div>" if layout not in ("diagonal-cut", "card-black-split") else ""}
  <div class="inner">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip">{b['author']}</div>
</div></body></html>"""


# ============================================================ 渲染与几何硬闸
def _chrome_bin() -> str:
    import os, shutil
    for c in [os.environ.get("CHROME_BIN"), "google-chrome", "chromium",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if c and (shutil.which(c) or Path(c).exists()):
            return shutil.which(c) or c
    raise SystemExit("找不到 Chrome 或 playwright，请安装 Chrome 或设置 CHROME_BIN")


def _chrome_shot(html_path: Path, out_png: Path, w: int, h: int):
    import subprocess
    cmd = [
        _chrome_bin(), "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--force-device-scale-factor=1",
        f"--window-size={w},{h}", "--virtual-time-budget=2500",
        f"--screenshot={out_png}", html_path.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)


def shot(html_path: Path, out_png: Path, clip_w: int, clip_h: int, offset_x: int = 0):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(800)
            pg.screenshot(path=str(out_png), clip={"x": offset_x, "y": 0, "width": clip_w, "height": clip_h})
            b.close()
    except ImportError:
        _chrome_shot(html_path, out_png, W, H)
        if offset_x or clip_w != W or clip_h != H:
            im = Image.open(out_png)
            im.crop((offset_x, 0, offset_x + clip_w, clip_h)).save(out_png)
    return out_png


def shot_square(html_path: Path, out_png: Path):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            pg = b.new_page(viewport={"width": SW, "height": SW}, device_scale_factor=1)
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(700)
            pg.screenshot(path=str(out_png))
            b.close()
    except ImportError:
        _chrome_shot(html_path, out_png, SW, SW)
    return out_png


def measure(html_path: Path) -> dict:
    js_eval = """() => {
      const g = s => { const e = document.querySelector(s); if(!e) return null;
        const r = e.getBoundingClientRect();
        return {x:r.x, y:r.y, w:r.width, h:r.height, r:r.x+r.width, b:r.y+r.height}; };
      const tls = [...document.querySelectorAll('.tl')].map(e=>{
        const s = e.querySelector('span') || e;
        const r = s.getBoundingClientRect();
        return {t:e.textContent.trim().slice(0,10), x:r.x, y:r.y, w:r.width, h:r.height, r:r.x+r.width, b:r.y+r.height};});
      return {brand:g('.brand'), kicker:g('.kicker'), sub:g('.sub'), rule:g('.rule'),
              portrait:g('.portrait'), titles:tls, vw:window.innerWidth, vh:window.innerHeight};
    }"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(600)
            data = pg.evaluate(js_eval)
            b.close()
        return data
    except ImportError:
        import re, subprocess, tempfile
        probe = html_path.read_text(encoding="utf-8")
        inject = f"<script>window.addEventListener('load',()=>{{const d=document.createElement('pre');d.id='__m';d.textContent=JSON.stringify(({js_eval})());document.body.appendChild(d);}});</script>"
        probe = probe.replace("</body>", inject + "</body>")
        with tempfile.NamedTemporaryFile("w", suffix=".html", dir=html_path.parent, delete=False, encoding="utf-8") as f:
            f.write(probe)
            tmp = Path(f.name)
        try:
            r = subprocess.run([
                _chrome_bin(), "--headless=new", "--no-sandbox", "--disable-gpu",
                "--force-device-scale-factor=1", f"--window-size={W},{H}",
                "--virtual-time-budget=2500", "--dump-dom", tmp.resolve().as_uri(),
            ], capture_output=True, text=True, timeout=60, check=True)
            m = re.search(r'<pre id="__m">(.*?)</pre>', r.stdout, re.S)
            return json.loads(html.unescape(m.group(1))) if m else {}
        finally:
            tmp.unlink(missing_ok=True)


def check(m: dict, errors: list, warns: list, psize=(817, 883), layout="editorial-right"):
    if not m.get("titles"):
        errors.append("没有标题行")
        return
    # 画布溢出检查
    for box in m["titles"] + ([m["brand"]] if m.get("brand") else []) + ([m["sub"]] if m.get("sub") else []):
        if box["x"] < 30 or box["r"] > W - 30:
            errors.append(f"文字越出画布边界 ({round(box['x'])}–{round(box['r'])})")
        if layout == "editorial-right" and box["r"] > SAFE_R:
            errors.append(f"文字右边界 {round(box['r'])} > 安全线 {SAFE_R}")
    # 标题不得压脸
    pr = m.get("portrait")
    if pr:
        sx, sy = psize[0] / 817.0, psize[1] / 883.0
        fx0 = pr["x"] + (FACE_BOX[0] * sx / psize[0]) * pr["w"]
        fx1 = pr["x"] + (FACE_BOX[2] * sx / psize[0]) * pr["w"]
        fy0 = pr["y"] + (FACE_BOX[1] * sy / psize[1]) * pr["h"]
        fy1 = pr["y"] + (FACE_BOX[3] * sy / psize[1]) * pr["h"]
        for box in m["titles"]:
            if box["r"] > fx0 and box["x"] < fx1 and box["b"] > fy0 and box["y"] < fy1:
                errors.append(f"标题「{box['t']}」压到人脸")
    for box in m["titles"]:
        if box["y"] < 30 or box["b"] > H - 30:
            warns.append(f"标题「{box['t']}」贴边（y={round(box['y'])}–{round(box['b'])}）")


DEMO = dict(
    kicker="知识星球 · 三个月复盘",
    brand="WorkBuddy",
    title_lines=["全自动运营星球", "3个月18万"],
    subtitle="附保姆级实操 · 5 讲全流程",
    author=DEFAULT_AUTHOR,
    ip_tag=DEFAULT_IP_TAG,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief")
    ap.add_argument("--out", default="out")
    ap.add_argument("--themes", nargs="*", default=list(THEMES))
    ap.add_argument("--layout", choices=LAYOUTS + tuple(LAYOUT_ALIAS.keys()), help="强制指定构图版式")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in THEMES.items():
            print(f"{k:<10} {v['name']:<7} [{v['layout']:<17}] {v['use']}")
        return

    brief = dict(DEMO) if (a.demo or not a.brief) else json.loads(Path(a.brief).read_text(encoding="utf-8"))
    if a.layout:
        brief["layout"] = LAYOUT_ALIAS.get(a.layout, a.layout)
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = {}
    for k in a.themes:
        t = THEMES[k]
        layout_used = LAYOUT_ALIAS.get(brief.get("layout") or t["layout"], brief.get("layout") or t["layout"])
        port, psize = treat_portrait(CUTOUT, out / f"_portrait-{k}.png", t["portrait"])
        page = out / f"cover-{k}.html"
        page.write_text(build_html(brief, k, port.as_uri(), psize), encoding="utf-8")

        errors, warns = [], []
        m = measure(page)
        check(m, errors, warns, psize, layout=layout_used)

        shot(page, out / f"cover-{k}-wide.png", W, H)
        sq_page = out / f"cover-{k}-square.html"
        sq_page.write_text(build_square_html(brief, k, port.as_uri(), psize), encoding="utf-8")
        shot_square(sq_page, out / f"cover-{k}-square.png")

        report[k] = dict(theme=k, name=t["name"], layout=layout_used, errors=errors, warns=warns,
                         title_r=[round(b["r"]) for b in m.get("titles", [])])
        flag = "OK " if not errors else "ERR"
        print(f"{flag} {k:<9} {t['name']:<5} ({layout_used:<17}) 右边界 {report[k]['title_r']}")
        for e in errors:
            print("     !", e)
        for w in warns:
            print("     ~", w)

    (out / "cover-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
