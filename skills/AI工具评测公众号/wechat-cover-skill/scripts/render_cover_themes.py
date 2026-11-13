#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多主题多版式封面渲染器 V3 —— 6 套视觉体系 × 6 种构图版式，人像必留 + IP 强露出。

版式（layout）：
  1. editorial     经典杂志双栏（左文右人 + 渐隐遮罩 + 汇芯 IP 印章）
  2. masthead      大刊报头（顶通杂志刊头 + 人物头顶破框叠压分割线）
  3. archive-card  档案相框（左侧大留白排版 + 右侧 1px 细框人物档案卡 & IP 签名条）
  4. swiss-grid    瑞士网格（1px 细线几何分格 + 左上角标 + 右侧近景半身特写）
  5. duotone-split 硬切双色（60/40 干净色块硬切对撞 + 右侧纯色块托底人像）
  6. cinema        电影宽银幕（暗底聚光轮廓 + 极简高亮大字 + 底部主创铭牌）

用法：
  python3 render_cover_themes.py --brief brief.json --out out/
  python3 render_cover_themes.py --demo            # 六套不同版式全出，用内置样例文案
  python3 render_cover_themes.py --list            # 列主题与默认版式
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CUTOUT = ASSETS / "owner_cutout_hd.png"
FACE_BOX = json.loads((ASSETS / "owner_cutout_hd.json").read_text(encoding="utf-8"))["face_box"]

# 画布：公众号首图 2.35:1
W, H = 2350, 1000
SW = 1080
# 公众号 1:1 分享卡取横版右侧 1000px；标题不得越线
SQUARE_X = W - H
TEXT_X = 132
SAFE_R = SQUARE_X - 16

SERIF = '"Songti SC","STSong","Source Han Serif SC","Noto Serif CJK SC",serif'
SANS = '"PingFang SC","Noto Sans CJK SC","Helvetica Neue",sans-serif'
LATIN = '"Helvetica Neue","Inter","Arial",sans-serif'

DEFAULT_AUTHOR = "袁六伟 · 台州汇芯"
DEFAULT_IP_TAG = "一人 AI 公司实战派"

LAYOUTS = (
    "editorial",
    "masthead",
    "archive-card",
    "swiss-grid",
    "duotone-split",
    "cinema",
)

# ============================================================ 六套主题（各自绑定不同默认版式）
THEMES = {
    "brand": dict(
        name="汇芯红",
        layout="editorial",
        paper="#FAF7F4", paper2="#F2ECE7", ink="#1A1A1A",
        accent="#C8102E", accent_on="#FFFFFF",
        muted="rgba(26,26,26,.54)", hair="rgba(26,26,26,.16)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="normal", grain=False,
        use="经典杂志双栏 · 通用主力（与正文汇芯红一致）",
    ),
    "paper": dict(
        name="纸本墨",
        layout="masthead",
        paper="#F1EFEA", paper2="#E7E3DA", ink="#0A0A0B",
        accent="#C8102E", accent_on="#F1EFEA",
        muted="rgba(10,10,11,.54)", hair="rgba(10,10,11,.20)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="muted", grain=True,
        use="大刊报头破框 · 方法论 / 观点 / 教程",
    ),
    "kraft": dict(
        name="牛皮纸",
        layout="archive-card",
        paper="#EEDFC7", paper2="#E2CFB2", ink="#2A1E13",
        accent="#9B4322", accent_on="#EEDFC7",
        muted="rgba(42,30,19,.56)", hair="rgba(42,30,19,.24)",
        card_bg="#F6ECDC",
        family=SERIF, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.12em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="warm_muted", grain=True,
        use="档案相框卡片 · 个人经历 / 复盘 / 案例故事",
    ),
    "swiss": dict(
        name="瑞士蓝",
        layout="swiss-grid",
        paper="#FAFAF8", paper2="#EFF2F8", ink="#0A0A0A",
        accent="#002FA7", accent_on="#FFFFFF",
        muted="rgba(10,10,10,.52)", hair="rgba(10,10,10,.20)",
        family=SANS, weight=500, track="-0.01em",
        brand_family=LATIN, brand_weight=400, brand_track="0.10em",
        small_family=LATIN, small_weight=600, small_track="0.16em",
        portrait="muted", grain=False,
        use="瑞士细线网格 · 产品发布 / 清单 / 数据测评",
    ),
    "indigo": dict(
        name="靛蓝瓷",
        layout="duotone-split",
        paper="#F3F5F8", paper2="#E3E9EF", ink="#0A1F3D",
        accent="#C8102E", accent_on="#FFFFFF",
        split_bg="#132A4A", split_ink="#F3F5F8",
        muted="rgba(10,31,61,.54)", hair="rgba(10,31,61,.18)",
        family=SANS, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.11em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="cool", grain=False,
        use="硬切双色对撞 · AI 工具 / 重磅干货 / 技术拆解",
    ),
    "midnight": dict(
        name="午夜墨",
        layout="cinema",
        paper="#0B0B0D", paper2="#171410", ink="#ECE2CF",
        accent="#D4A04A", accent_on="#0B0B0D",
        muted="rgba(236,226,207,.50)", hair="rgba(236,226,207,.20)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="warm_dark", grain=True,
        use="电影宽银幕 · 数据复盘 / 搞钱 / 深夜长文",
    ),
}

SHADOW = {
    "midnight": "drop-shadow(-50px 10px 80px rgba(0,0,0,.65))",
    "paper":    "drop-shadow(-20px 6px 42px rgba(0,0,0,.10))",
    "kraft":    "drop-shadow(-20px 6px 40px rgba(60,40,20,.14))",
    "indigo":   "drop-shadow(-24px 8px 46px rgba(0,0,0,.28))",
    "swiss":    "drop-shadow(-16px 4px 34px rgba(0,0,0,.10))",
    "brand":    "drop-shadow(-22px 6px 46px rgba(0,0,0,.12))",
}


# ============================================================ 人像处理
def _curve(a: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip((a - lo) / max(1e-6, hi - lo), 0.0, 1.0)


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
        out = rgb * 0.72 + gray * 0.28
        out = out * 1.01
    elif mode == "warm_muted":
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = (rgb * 0.70 + gray * 0.30) * np.array([1.06, 1.00, 0.92])
    elif mode == "cool":
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = (rgb * 0.55 + gray * 0.45) * np.array([0.94, 0.99, 1.07])
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
    return dict(
        kicker=html.escape(brief.get("kicker", "")),
        brand=html.escape(brief.get("brand", "")),
        lines=lines,
        sub=html.escape(brief.get("subtitle", "")),
        author=html.escape(brief.get("author", DEFAULT_AUTHOR)),
        ip_tag=html.escape(brief.get("ip_tag", DEFAULT_IP_TAG)),
        stamp=html.escape(brief.get("stamp", "")),
        layout=brief.get("layout") or THEMES[theme_key]["layout"],
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


# ============================================================ 6 套不同横版构图
def build_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    t = THEMES[theme_key]
    b = _parse_brief(brief, theme_key)
    layout = b["layout"]
    grain = '<div class="grain"></div>' if t["grain"] else ""
    pw_ratio = psize[0] / psize[1]

    # 1) editorial：经典杂志双栏 + 底部汇芯 IP 铭牌
    if layout == "editorial":
        p_h = 1016
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w + 16
        p_top = 68
        titles = _titles_html(b["lines"], t["weight"], 146, 178)
        css = _base_css(t, theme_key) + f"""
.portrait{{position:absolute;left:{p_left}px;top:{p_top}px;width:{p_w}px;height:{p_h}px;
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

    # 2) masthead：大刊报头 + 人物头顶破框叠压刊头细线
    elif layout == "masthead":
        p_h = 980
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w - 40
        p_top = 86  # 刻意低于顶部 136px 报头线以下一点，使头部轻微破框叠压报头线
        titles = _titles_html(b["lines"], t["weight"], 136, 168)
        css = _base_css(t, theme_key) + f"""
.masthead{{position:absolute;left:{TEXT_X}px;right:{TEXT_X}px;top:52px;height:86px;
  border-bottom:2px solid {t['ink']};display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:16px;z-index:1}}
.mast-title{{font-family:{SERIF};font-size:44px;font-weight:700;letter-spacing:.18em;color:{t['ink']}}}
.mast-title em{{font-style:normal;color:{t['accent']}}}
.mast-meta{{font-family:{t['small_family']};font-size:23px;letter-spacing:.20em;color:{t['muted']};text-transform:uppercase}}
.portrait{{position:absolute;left:{p_left}px;top:{p_top}px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:2}}
.txt{{position:absolute;left:{TEXT_X}px;top:210px;width:1160px;height:690px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:26px}}
.brand{{font-size:88px;margin-bottom:16px}}
.rule{{width:160px;height:4px;background:{t['accent']};margin:34px 0 24px}}
.bottom-bar{{position:absolute;left:{TEXT_X}px;bottom:46px;width:1120px;border-top:1px solid {t['hair']};
  padding-top:16px;display:flex;justify-content:space-between;align-items:center;z-index:3;
  font-family:{SANS};font-size:23px;letter-spacing:.12em;color:{t['muted']}}}
.bottom-bar strong{{color:{t['ink']};font-weight:600}}
"""
        body = f"""
  <div class="masthead">
    <div class="mast-title">HUIXIN <em>·</em> {b['author']}</div>
    <div class="mast-meta">{b['ip_tag']}</div>
  </div>
  <img class="portrait" src="{portrait_uri}">
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="bottom-bar"><span><strong>COLUMN</strong> · {b['kicker']}</span><span>{b['author']}</span></div>"""

    # 3) archive-card：左侧大留白 + 右侧 1px 细框人物档案卡片 + IP 签名底栏
    elif layout == "archive-card":
        card_bg = t.get("card_bg", "#FFFFFF")
        p_h = 770
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 138, 170)
        css = _base_css(t, theme_key) + f"""
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1140px;height:{H}px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:32px}}
.brand{{font-size:92px;margin-bottom:16px}}
.rule{{width:340px;height:2px;background:{t['accent']};margin:34px 0 24px}}
.sub{{margin-bottom:44px}}
.frame{{position:absolute;right:96px;top:62px;width:780px;height:876px;background:{card_bg};
  border:2px solid {t['ink']};box-shadow:18px 18px 0 {t['accent']};overflow:hidden}}
.frame-top{{height:58px;border-bottom:1px solid {t['hair']};padding:0 28px;
  display:flex;justify-content:space-between;align-items:center;
  font-family:{t['small_family']};font-size:20px;font-weight:600;letter-spacing:.18em;color:{t['muted']}}}
.frame-body{{position:relative;height:706px;overflow:hidden;background:{t['paper2']}}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);top:24px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.frame-foot{{height:110px;border-top:1.5px solid {t['ink']};padding:0 28px;background:{card_bg};
  display:flex;justify-content:space-between;align-items:center}}
.frame-name{{font-family:{SERIF};font-size:32px;font-weight:700;color:{t['ink']};letter-spacing:.06em}}
.frame-role{{font-family:{SANS};font-size:22px;color:{t['accent']};font-weight:600;letter-spacing:.08em}}
"""
        body = f"""
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
    <div><span class="ip-seal"><i class="dot"></i><span>{b['author']} · {b['ip_tag']}</span></span></div>
  </div>
  <div class="frame">
    <div class="frame-top"><span>HUIXIN ARCHIVE</span><span>FOUNDER</span></div>
    <div class="frame-body"><img class="portrait" src="{portrait_uri}"></div>
    <div class="frame-foot">
      <span class="frame-name">{b['author']}</span>
      <span class="frame-role">{b['ip_tag']}</span>
    </div>
  </div>"""

    # 4) swiss-grid：瑞士包豪斯 1px 细线网格分割 + 右侧近景半身特写
    elif layout == "swiss-grid":
        p_h = 960
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 136, 168)
        css = _base_css(t, theme_key) + f"""
.top-band{{position:absolute;left:0;top:0;width:100%;height:18px;background:{t['accent']}}}
.grid-v{{position:absolute;left:1350px;top:18px;bottom:0;width:1.5px;background:{t['hair']}}}
.grid-h1{{position:absolute;left:0;right:0;top:172px;height:1.5px;background:{t['hair']}}}
.grid-h2{{position:absolute;left:0;width:1350px;bottom:148px;height:1.5px;background:{t['hair']}}}
.cell-tl{{position:absolute;left:{TEXT_X}px;top:18px;width:1160px;height:154px;
  display:flex;align-items:center;justify-content:space-between}}
.pill{{background:{t['accent']};color:{t['accent_on']};padding:12px 24px;
  font-family:{SANS};font-size:26px;font-weight:700;letter-spacing:.12em}}
.cell-tr{{position:absolute;left:1390px;top:18px;right:72px;height:154px;
  display:flex;align-items:center;justify-content:space-between;
  font-family:{SANS};font-size:24px;font-weight:600;letter-spacing:.10em;color:{t['ink']}}}
.txt{{position:absolute;left:{TEXT_X}px;top:174px;width:1170px;height:676px;
  display:flex;flex-direction:column;justify-content:center}}
.brand{{font-size:88px;margin-bottom:16px}}
.cell-bl{{position:absolute;left:{TEXT_X}px;bottom:0;width:1160px;height:148px;
  display:flex;align-items:center;justify-content:space-between}}
.cell-right{{position:absolute;left:1352px;top:174px;right:0;bottom:0;overflow:hidden}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);top:22px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
"""
        body = f"""
  <div class="top-band"></div>
  <div class="grid-v"></div><div class="grid-h1"></div><div class="grid-h2"></div>
  <div class="cell-tl">
    <span class="pill">{b['kicker']}</span>
    <span class="kicker" style="margin:0">{b['ip_tag']}</span>
  </div>
  <div class="cell-tr"><span>{b['author']}</span><span style="color:{t['accent']}">● LIVE</span></div>
  <div class="txt">
    <div class="brand">{b['brand']}</div>
    {titles}
  </div>
  <div class="cell-bl">
    <div class="sub">{b['sub']}</div>
    <div class="ip-seal"><i class="dot"></i><span>{b['author']}</span></div>
  </div>
  <div class="cell-right"><img class="portrait" src="{portrait_uri}"></div>"""

    # 5) duotone-split：60/40 硬切双色对撞 + 右侧深色纯色底托底人像
    elif layout == "duotone-split":
        split_bg = t.get("split_bg", "#132A4A")
        split_ink = t.get("split_ink", "#FFFFFF")
        p_h = 980
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 136, 170)
        css = _base_css(t, theme_key) + f"""
.split-right{{position:absolute;left:1360px;top:0;right:0;bottom:0;background:{split_bg};overflow:hidden}}
.split-accent{{position:absolute;left:1360px;top:0;width:12px;height:100%;background:{t['accent']}}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);top:66px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.split-badge{{position:absolute;right:52px;top:48px;border:1.5px solid rgba(255,255,255,.35);
  padding:10px 20px;font-family:{SANS};font-size:22px;font-weight:600;letter-spacing:.12em;
  color:{split_ink};background:rgba(0,0,0,.18)}}
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1160px;height:{H}px;padding-bottom:84px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:28px}}
.brand{{font-size:90px;margin-bottom:16px}}
.rule{{width:380px;height:3px;background:{t['accent']};margin:34px 0 24px}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:48px;width:1160px;display:flex;justify-content:space-between;align-items:center}}
.strip-note{{font-family:{SANS};font-size:23px;color:{t['muted']};letter-spacing:.10em}}
"""
        body = f"""
  <div class="split-right">
    <img class="portrait" src="{portrait_uri}">
    <div class="split-badge">{b['author']}</div>
  </div>
  <div class="split-accent"></div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip">
    <div class="ip-seal"><i class="dot"></i><span>{b['author']}</span></div>
    <span class="strip-note">{b['ip_tag']}</span>
  </div>"""

    # 6) cinema：电影宽银幕 + 暗底聚光 + 底部主创铭牌
    else:
        p_h = 1010
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w - 20
        titles = _titles_html(b["lines"], t["weight"], 144, 178)
        css = _base_css(t, theme_key) + f"""
.spot{{position:absolute;right:140px;top:120px;width:820px;height:820px;border-radius:50%;
  background:radial-gradient(circle, rgba(212,160,74,.20) 0%, transparent 66%);pointer-events:none}}
.portrait{{position:absolute;left:{p_left}px;top:64px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,{t['paper']} 0%,{t['paper']} 36%,{_rgba(t['paper'],.92)} 48%,
    {_rgba(t['paper'],.45)} 62%,{_rgba(t['paper'],0)} 76%)}}
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1160px;height:{H}px;padding-bottom:104px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:28px}}
.brand{{font-size:96px;margin-bottom:16px}}
.rule{{width:420px;height:2px;background:{t['accent']};margin:34px 0 22px}}
.credits{{position:absolute;left:{TEXT_X}px;right:{TEXT_X}px;bottom:42px;border-top:1px solid {t['hair']};
  padding-top:16px;display:flex;justify-content:space-between;align-items:center;
  font-family:{t['small_family']};font-size:22px;letter-spacing:.22em;color:{t['muted']};text-transform:uppercase}}
.credits strong{{color:{t['accent']};font-weight:600}}
"""
        body = f"""
  <div class="spot"></div>
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="credits">
    <span>PRESENTED BY <strong>{b['author']}</strong></span>
    <span>{b['ip_tag']}</span>
  </div>"""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="cv theme-{theme_key} layout-{layout}">
  <div class="paper2"></div>{grain}{body}
</div></body></html>"""


# ============================================================ 1:1 竖版分享卡（随 layout 差异化）
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
    if layout == "duotone-split":
        split_bg = t.get("split_bg", "#132A4A")
        extra_css = f".sq-band{{position:absolute;left:0;right:0;bottom:0;height:430px;background:{split_bg};border-top:8px solid {t['accent']}}}"
        extra_dom = '<div class="sq-band"></div>'
    elif layout == "archive-card":
        extra_css = f".sq-frame{{position:absolute;right:48px;bottom:48px;width:480px;height:460px;border:2px solid {t['ink']};background:{t.get('card_bg','#FFF')};box-shadow:12px 12px 0 {t['accent']}}}"
        extra_dom = '<div class="sq-frame"></div>'
        pw, ph, pl, pt = 430, round(430 * psize[1] / psize[0]), 530, SW - round(430 * psize[1] / psize[0]) + 40
    elif layout == "swiss-grid":
        extra_css = f".sq-top{{position:absolute;left:0;top:0;width:100%;height:16px;background:{t['accent']}}}"
        extra_dom = '<div class="sq-top"></div>'

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
  {"<div class='tint'></div>" if layout not in ("duotone-split", "archive-card") else ""}
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


def check(m: dict, errors: list, warns: list, psize=(817, 883)):
    if not m.get("titles"):
        errors.append("没有标题行")
        return
    for box in m["titles"] + ([m["brand"]] if m.get("brand") else []) + ([m["sub"]] if m.get("sub") else []):
        if box["r"] > SAFE_R:
            errors.append(f"文字右边界 {round(box['r'])} > 安全线 {SAFE_R}，1:1 小图会切字")
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
        if box["y"] < 40 or box["b"] > H - 40:
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
    ap.add_argument("--layout", choices=LAYOUTS, help="强制指定构图版式（覆盖主题默认版式）")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in THEMES.items():
            print(f"{k:<10} {v['name']:<7} [{v['layout']:<13}] {v['use']}")
        return

    brief = dict(DEMO) if (a.demo or not a.brief) else json.loads(Path(a.brief).read_text(encoding="utf-8"))
    if a.layout:
        brief["layout"] = a.layout
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = {}
    for k in a.themes:
        t = THEMES[k]
        port, psize = treat_portrait(CUTOUT, out / f"_portrait-{k}.png", t["portrait"])
        page = out / f"cover-{k}.html"
        page.write_text(build_html(brief, k, port.as_uri(), psize), encoding="utf-8")

        errors, warns = [], []
        m = measure(page)
        check(m, errors, warns, psize)

        shot(page, out / f"cover-{k}-wide.png", W, H)
        sq_page = out / f"cover-{k}-square.html"
        sq_page.write_text(build_square_html(brief, k, port.as_uri(), psize), encoding="utf-8")
        shot_square(sq_page, out / f"cover-{k}-square.png")

        layout_used = brief.get("layout") or t["layout"]
        report[k] = dict(theme=k, name=t["name"], layout=layout_used, errors=errors, warns=warns,
                         title_r=[round(b["r"]) for b in m.get("titles", [])])
        flag = "OK " if not errors else "ERR"
        print(f"{flag} {k:<9} {t['name']:<5} ({layout_used:<13}) 右边界 {report[k]['title_r']}  安全线 {SAFE_R}")
        for e in errors:
            print("     !", e)
        for w in warns:
            print("     ~", w)

    (out / "cover-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
