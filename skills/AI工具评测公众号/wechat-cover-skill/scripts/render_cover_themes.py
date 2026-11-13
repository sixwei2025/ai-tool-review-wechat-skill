#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多主题极简编辑封面渲染器 V5 —— 6 套同级高逼格极简构图，绝无廉价色块与粗框。

设计原则（贵 = 克制）：
  · 留白主导（>45% 呼吸空间）+ 1px hairline 细线 + 「越大越细」字重对比
  · 6 套主题各有独特空间构图，但共享同一套顶级杂志极简美学：
    1. brand    (汇芯红 · editorial)  经典左文右人 + 极简底线 IP 署名
    2. paper    (纸本墨 · monocle)    左人右文反转 + 顶部 1px 通栏杂志刊头
    3. swiss    (瑞士蓝 · tdc-grid)   Tokyo TDC 若隐若现细线网格 + 左侧竖排边栏 + 右下留白人像
    4. midnight (午夜墨 · criterion)  暗夜中心暖光聚光 + 人物居中偏右 + 左右分列结论
    5. kraft    (牛皮纸 · kinfolk)    Kinfolk 画册大留白 + 左上极简标 + 右下克制人像 + 细线印章
    6. indigo   (靛蓝瓷 · interview)  近景专访半身特写 + 左文极简冷瓷留白

用法：
  python3 render_cover_themes.py --brief brief.json --out out/
  python3 render_cover_themes.py --demo
  python3 render_cover_themes.py --list
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
TEXT_X = 132
SAFE_R = SQUARE_X - 16

SERIF = '"Songti SC","STSong","Source Han Serif SC","Noto Serif CJK SC",serif'
SANS = '"PingFang SC","Noto Sans CJK SC","Helvetica Neue",sans-serif'
LATIN = '"Helvetica Neue","Inter","Arial",sans-serif'

DEFAULT_AUTHOR = "袁六伟 · 台州汇芯"
DEFAULT_IP_TAG = "一人 AI 公司实战派"

LAYOUTS = (
    "editorial",
    "monocle",
    "tdc-grid",
    "criterion",
    "kinfolk",
    "interview",
)

THEMES = {
    "brand": dict(
        name="汇芯红",
        layout="editorial",
        paper="#FAF7F4", paper2="#F2ECE7", ink="#1A1A1A",
        accent="#C7352D", accent_on="#FFFFFF",
        muted="rgba(26,26,26,.52)", hair="rgba(26,26,26,.16)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="normal", grain=False,
        use="经典杂志双栏 · 通用主力（与正文汇芯红一致）",
    ),
    "paper": dict(
        name="纸本墨",
        layout="monocle",
        paper="#F1EFEA", paper2="#E7E3DA", ink="#0A0A0B",
        accent="#0A0A0B", accent_on="#F1EFEA",
        muted="rgba(10,10,11,.52)", hair="rgba(10,10,11,.18)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="muted", grain=True,
        use="左人右文 + 1px 通栏刊头 · 方法论 / 观点 / 教程",
    ),
    "swiss": dict(
        name="瑞士蓝",
        layout="tdc-grid",
        paper="#FAFAF8", paper2="#EFF2F7", ink="#0A0A0A",
        accent="#002FA7", accent_on="#FFFFFF",
        muted="rgba(10,10,10,.48)", hair="rgba(10,10,10,.11)",
        family=SANS, weight=400, track="-0.01em",
        brand_family=LATIN, brand_weight=300, brand_track="0.11em",
        small_family=LATIN, small_weight=500, small_track="0.18em",
        portrait="muted", grain=False,
        use="TDC 细线网格 + 竖排边栏 · 发布 / 清单 / 数据",
    ),
    "midnight": dict(
        name="午夜墨",
        layout="criterion",
        paper="#0E0D0C", paper2="#171410", ink="#ECE2CF",
        accent="#D4A04A", accent_on="#0E0D0C",
        muted="rgba(236,226,207,.48)", hair="rgba(236,226,207,.18)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="warm_dark", grain=True,
        use="暗夜中心聚光 + 左右分列 · 复盘 / 搞钱 / 深夜长文",
    ),
    "kraft": dict(
        name="牛皮纸",
        layout="kinfolk",
        paper="#EEDFC7", paper2="#E2CFB2", ink="#2A1E13",
        accent="#9B5A2E", accent_on="#EEDFC7",
        muted="rgba(42,30,19,.54)", hair="rgba(42,30,19,.20)",
        family=SERIF, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.12em",
        small_family=LATIN, small_weight=500, small_track="0.20em",
        portrait="warm_muted", grain=True,
        use="Kinfolk 画册大留白 + 细线印章 · 经历 / 故事",
    ),
    "indigo": dict(
        name="靛蓝瓷",
        layout="interview",
        paper="#F2F4F7", paper2="#E3E9F0", ink="#0A1F3D",
        accent="#315D93", accent_on="#F2F4F7",
        muted="rgba(10,31,61,.52)", hair="rgba(10,31,61,.16)",
        family=SANS, weight=500, track="0em",
        brand_family=LATIN, brand_weight=300, brand_track="0.11em",
        small_family=LATIN, small_weight=500, small_track="0.20em",
        portrait="cool", grain=False,
        use="近景专访特写 · AI 工具 / 产品 / 技术拆解",
    ),
}

SHADOW = {
    "midnight": "drop-shadow(-38px 10px 80px rgba(0,0,0,.62))",
    "paper":    "drop-shadow(18px 6px 42px rgba(0,0,0,.09))",
    "kraft":    "drop-shadow(-20px 6px 46px rgba(60,40,20,.14))",
    "indigo":   "drop-shadow(-24px 6px 48px rgba(10,31,61,.12))",
    "swiss":    "drop-shadow(-16px 5px 38px rgba(0,0,0,.09))",
    "brand":    "drop-shadow(-22px 6px 46px rgba(0,0,0,.11))",
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
        out = (rgb * 0.54 + gray * 0.46) * np.array([0.94, 0.99, 1.07])
    elif mode == "normal":
        out = rgb * 0.93
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
    layout = brief.get("layout") or THEMES[theme_key]["layout"]
    return dict(
        kicker=html.escape(brief.get("kicker", "")),
        brand=html.escape(brief.get("brand", "")),
        lines=lines,
        sub=html.escape(brief.get("subtitle", "")),
        author=html.escape(brief.get("author", DEFAULT_AUTHOR)),
        ip_tag=html.escape(brief.get("ip_tag", DEFAULT_IP_TAG)),
        layout=layout,
    )


def _titles_html(lines: list[str], weight: int, fs_normal: int = 150, fs_accent: int = 184) -> str:
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
.grain{{position:absolute;inset:0;opacity:.48;mix-blend-mode:{mix};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px;pointer-events:none}}
.tl{{font-family:{t['family']};font-weight:{t['weight']};line-height:1.20;letter-spacing:{t['track']};
  color:{t['ink']};white-space:nowrap}}
.tl.accent{{line-height:1.10;color:{t['accent']}}}
.brand{{font-family:{t['brand_family']};font-weight:{t['brand_weight']};color:{t['ink']};
  letter-spacing:{t['brand_track']};line-height:1;white-space:nowrap}}
.kicker{{display:flex;align-items:center;gap:18px;font-family:{t['small_family']};font-weight:{t['small_weight']};
  font-size:28px;letter-spacing:{t['small_track']};color:{t['muted']};text-transform:uppercase}}
.kicker .sq{{width:10px;height:10px;background:{t['accent']};flex:0 0 auto}}
.sub{{font-family:{t['family']};font-weight:400;font-size:36px;letter-spacing:.09em;color:{t['muted']};white-space:nowrap}}
"""


# ============================================================ 6 套极简高逼格构图
def build_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    t = THEMES[theme_key]
    b = _parse_brief(brief, theme_key)
    layout = b["layout"]
    grain = '<div class="grain"></div>' if t["grain"] else ""
    pw_ratio = psize[0] / psize[1]

    # 1) editorial（汇芯红）：原汁原味经典左文右人 + 底部极简 IP 署名
    if layout == "editorial":
        p_h = 1016
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w + 16
        titles = _titles_html(b["lines"], t["weight"], 150, 184)
        css = _base_css(t, theme_key) + f"""
.portrait{{position:absolute;left:{p_left}px;top:68px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,{t['paper']} 0%,{t['paper']} 34%,{_rgba(t['paper'],.97)} 44%,
    {_rgba(t['paper'],.80)} 55%,{_rgba(t['paper'],.40)} 65%,{_rgba(t['paper'],0)} 78%)}}
.txt{{position:absolute;left:{TEXT_X}px;top:0;width:1150px;height:{H}px;padding-bottom:86px;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:34px}}
.brand{{font-size:104px;margin-bottom:18px}}
.rule{{width:430px;height:2px;background:{t['accent']};margin:40px 0 24px}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:52px;width:1190px;border-top:1px solid {t['hair']};
  padding-top:19px;display:flex;justify-content:space-between;align-items:baseline;
  font-family:{t['small_family']};font-weight:{t['small_weight']};font-size:23px;
  letter-spacing:.20em;color:{t['muted']};text-transform:uppercase}}
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
  <div class="strip"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 2) monocle（纸本墨）：左人右文反转 + 顶部 1px 通栏杂志刊头
    elif layout == "monocle":
        p_h = 940
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 144, 178)
        css = _base_css(t, theme_key) + f"""
.masthead{{position:absolute;left:110px;right:110px;top:48px;height:66px;
  border-bottom:1px solid {t['hair']};display:flex;justify-content:space-between;align-items:center;z-index:3}}
.masthead .l{{font-family:{LATIN};font-size:24px;font-weight:500;letter-spacing:.28em;color:{t['ink']}}}
.masthead .r{{font-family:{SERIF};font-size:24px;letter-spacing:.14em;color:{t['muted']}}}
.portrait{{position:absolute;left:64px;top:124px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:1}}
.tint{{position:absolute;inset:0;pointer-events:none;z-index:2;
  background:linear-gradient(270deg,{t['paper']} 0%,{t['paper']} 38%,{_rgba(t['paper'],.94)} 49%,
    {_rgba(t['paper'],.55)} 60%,{_rgba(t['paper'],0)} 74%)}}
.txt{{position:absolute;left:980px;top:116px;right:110px;height:760px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.kicker{{margin-bottom:32px}}
.brand{{font-size:96px;margin-bottom:18px}}
.rule{{width:360px;height:1.5px;background:{t['ink']};margin:38px 0 24px}}
.strip{{position:absolute;left:980px;right:110px;bottom:52px;border-top:1px solid {t['hair']};
  padding-top:18px;display:flex;justify-content:space-between;z-index:3;
  font-family:{t['small_family']};font-size:22px;letter-spacing:.18em;color:{t['muted']}}}
"""
        body = f"""
  <div class="masthead">
    <span class="l">HUIXIN  REVIEW</span>
    <span class="r">{b['author']}</span>
  </div>
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 3) tdc-grid（瑞士蓝）：Tokyo TDC 仅左侧文字区细线网格 + 左侧竖排边栏 + 右侧纯白留白人像
    elif layout == "tdc-grid":
        p_h = 920
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w - 40
        titles = _titles_html(b["lines"], t["weight"], 140, 174)
        css = _base_css(t, theme_key) + f"""
.paper2{{display:none}}
.top-hair{{position:absolute;left:0;top:0;width:100%;height:4px;background:{t['accent']}}}
.gv1{{position:absolute;left:110px;top:0;bottom:0;width:1px;background:{t['hair']}}}
.gh1{{position:absolute;left:0;width:1240px;top:140px;height:1px;background:{t['hair']}}}
.gh2{{position:absolute;left:0;width:1240px;bottom:118px;height:1px;background:{t['hair']}}}
.side-vert{{position:absolute;left:42px;top:180px;writing-mode:vertical-rl;transform:rotate(180deg);
  font-family:{LATIN};font-size:20px;font-weight:500;letter-spacing:.28em;color:{t['muted']}}}
.top-meta{{position:absolute;left:168px;top:0;width:1072px;height:140px;
  display:flex;justify-content:space-between;align-items:center}}
.top-meta .ip{{font-family:{SANS};font-size:22px;font-weight:500;letter-spacing:.14em;color:{t['ink']}}}
.portrait{{position:absolute;left:{p_left}px;bottom:-24px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:2}}
.txt{{position:absolute;left:168px;top:140px;width:1120px;height:742px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.brand{{font-size:94px;margin-bottom:20px}}
.rule{{width:280px;height:2px;background:{t['accent']};margin:38px 0 24px}}
.foot{{position:absolute;left:168px;width:1072px;bottom:0;height:118px;z-index:3;
  display:flex;justify-content:space-between;align-items:center;
  font-family:{LATIN};font-size:22px;letter-spacing:.18em;color:{t['muted']}}}
"""
        body = f"""
  <div class="top-hair"></div>
  <div class="gv1"></div><div class="gh1"></div><div class="gh2"></div>
  <div class="side-vert">YUAN LIUWEI · HUIXIN</div>
  <div class="top-meta">
    <div class="kicker" style="margin:0"><i class="sq"></i><span>{b['kicker']}</span></div>
    <span class="ip">{b['author']}</span>
  </div>
  <img class="portrait" src="{portrait_uri}">
  <div class="txt">
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="foot"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 4) criterion（午夜墨）：暗夜中心暖光聚光 + 人物居中 + 左右分列信息
    elif layout == "criterion":
        main_lines = b["lines"][:-1] if len(b["lines"]) > 1 else b["lines"]
        accent_line = b["lines"][-1] if len(b["lines"]) > 1 else ""
        main_html = _titles_html(main_lines, t["weight"], 96, 96)
        p_h = 850
        p_w = round(p_h * pw_ratio)
        css = _base_css(t, theme_key) + f"""
.top-bar{{position:absolute;left:110px;right:110px;top:46px;height:62px;border-bottom:1px solid {t['hair']};
  display:flex;justify-content:space-between;align-items:center;z-index:3}}
.top-bar .c{{font-family:{SERIF};font-size:28px;letter-spacing:.28em;color:{t['ink']};font-weight:500}}
.top-bar .s{{font-family:{LATIN};font-size:20px;letter-spacing:.22em;color:{t['muted']}}}
.spot{{position:absolute;left:50%;transform:translateX(-50%);top:150px;width:820px;height:820px;border-radius:50%;
  background:radial-gradient(circle, rgba(212,160,74,.14) 0%, transparent 66%);pointer-events:none}}
.portrait{{position:absolute;left:50%;transform:translateX(-50%);bottom:-20px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:1}}
.left-col{{position:absolute;left:110px;top:190px;width:740px;height:640px;z-index:3;
  display:flex;flex-direction:column;justify-content:center}}
.left-col .kicker{{margin-bottom:28px}}
.left-col .brand{{font-size:84px;margin-bottom:20px}}
.left-col .tl{{white-space:normal;line-height:1.24}}
.right-col{{position:absolute;right:110px;top:210px;width:620px;height:600px;z-index:3;
  display:flex;flex-direction:column;justify-content:center;align-items:flex-end;text-align:right}}
.right-col .tl.accent{{font-size:138px;line-height:1.08}}
.right-col .rule{{width:260px;height:1.5px;background:{t['accent']};margin:34px 0 22px}}
.foot{{position:absolute;left:110px;right:110px;bottom:48px;
  display:flex;justify-content:space-between;z-index:3;
  font-family:{LATIN};font-size:21px;letter-spacing:.22em;color:{t['muted']}}}
"""
        body = f"""
  <div class="top-bar">
    <span class="s">{b['kicker']}</span>
    <span class="c">HUIXIN  ·  {b['author']}</span>
    <span class="s">{b['ip_tag']}</span>
  </div>
  <div class="spot"></div>
  <img class="portrait" src="{portrait_uri}">
  <div class="left-col">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {main_html}
  </div>
  <div class="right-col">
    <div class="tl accent"><span style="font-weight:400">{accent_line}</span></div>
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="foot"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 5) kinfolk（牛皮纸）：大留白画册风 + 人物克制缩置右下 + 右上 1px 细线印章
    elif layout == "kinfolk":
        p_h = 760
        p_w = round(p_h * pw_ratio)
        titles = _titles_html(b["lines"], t["weight"], 132, 162)
        css = _base_css(t, theme_key) + f"""
.seal-tr{{position:absolute;right:110px;top:64px;
  font-family:{SERIF};font-size:24px;letter-spacing:.18em;color:{t['muted']}}}
.portrait{{position:absolute;right:110px;bottom:-18px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]};z-index:1}}
.txt{{position:absolute;left:140px;top:110px;width:1180px;height:740px;z-index:2;
  display:flex;flex-direction:column;justify-content:flex-start;padding-top:40px}}
.kicker{{margin-bottom:36px}}
.brand{{font-size:88px;margin-bottom:22px}}
.rule{{width:180px;height:1.5px;background:{t['accent']};margin:44px 0 24px}}
.strip{{position:absolute;left:140px;bottom:56px;width:1080px;border-top:1px solid {t['hair']};
  padding-top:18px;display:flex;justify-content:space-between;
  font-family:{LATIN};font-size:22px;letter-spacing:.20em;color:{t['muted']}}}
"""
        body = f"""
  <div class="seal-tr">{b['author']}</div>
  <img class="portrait" src="{portrait_uri}">
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    # 6) interview（靛蓝瓷）：阶梯错落排版（左上标题 + 右下结论副标 + 右侧近景专访半身特写）
    else:
        main_lines = b["lines"][:-1] if len(b["lines"]) > 1 else b["lines"]
        accent_line = b["lines"][-1] if len(b["lines"]) > 1 else ""
        main_html = _titles_html(main_lines, t["weight"], 136, 136)
        p_h = 1040
        p_w = round(p_h * pw_ratio)
        p_left = W - p_w + 36
        css = _base_css(t, theme_key) + f"""
.portrait{{position:absolute;left:{p_left}px;top:52px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,{t['paper']} 0%,{t['paper']} 38%,{_rgba(t['paper'],.95)} 48%,
    {_rgba(t['paper'],.68)} 58%,{_rgba(t['paper'],0)} 74%)}}
.txt-top{{position:absolute;left:{TEXT_X}px;top:110px;width:1120px;z-index:3}}
.kicker{{margin-bottom:28px}}
.brand{{font-size:96px;margin-bottom:16px}}
.txt-step{{position:absolute;left:360px;bottom:170px;width:920px;z-index:3}}
.txt-step .tl.accent{{font-size:168px;line-height:1.05;margin-bottom:20px}}
.txt-step .rule{{width:280px;height:2px;background:{t['accent']};margin:24px 0 18px}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:52px;width:1160px;border-top:1px solid {t['hair']};
  padding-top:18px;display:flex;justify-content:space-between;
  font-family:{LATIN};font-size:22px;letter-spacing:.20em;color:{t['muted']}}}
"""
        body = f"""
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="txt-top">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {main_html}
  </div>
  <div class="txt-step">
    <div class="tl accent"><span style="font-weight:400">{accent_line}</span></div>
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip"><span>{b['author']}</span><span>{b['ip_tag']}</span></div>"""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="cv theme-{theme_key} layout-{layout}">
  <div class="paper2"></div>{grain}{body}
</div></body></html>"""


# ============================================================ 1:1 竖版分享卡
def build_square_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    t = THEMES[theme_key]
    b = _parse_brief(brief, theme_key)
    pw = 520
    ph = round(pw * psize[1] / psize[0])
    pl = 400 if b["layout"] != "monocle" else 120
    pt = SW - ph + 96
    titles = _titles_html(b["lines"], t["weight"], 92, 132)
    grain = '<div class="grain"></div>' if t["grain"] else ""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{SW}px;height:{SW}px;overflow:hidden}}
.cv{{position:relative;width:{SW}px;height:{SW}px;background:{t['paper']};overflow:hidden}}
.paper2{{position:absolute;inset:0;background:radial-gradient(120% 80% at 26% 14%,{t['paper2']} 0%,transparent 60%)}}
.grain{{position:absolute;inset:0;opacity:.48;mix-blend-mode:{"screen" if theme_key=="midnight" else "multiply"};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px}}
.portrait{{position:absolute;left:{pl}px;top:{pt}px;width:{pw}px;height:{ph}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,{t['paper']} 0%,{t['paper']} 46%,{_rgba(t['paper'],.92)} 51%,{_rgba(t['paper'],.42)} 56%,{_rgba(t['paper'],0)} 62%)}}
.inner{{position:absolute;left:78px;top:92px;width:930px}}
.kicker{{display:flex;align-items:center;gap:16px;font-family:{t['small_family']};
  font-weight:{t['small_weight']};font-size:26px;letter-spacing:{t['small_track']};
  color:{t['muted']};text-transform:uppercase;margin-bottom:26px}}
.kicker .sq{{width:10px;height:10px;background:{t['accent']}}}
.brand{{font-family:{t['brand_family']};font-weight:{t['brand_weight']};font-size:76px;
  letter-spacing:{t['brand_track']};color:{t['ink']};line-height:1;margin-bottom:14px}}
.tl{{font-family:{t['family']};font-weight:{t['weight']};line-height:1.16;
  letter-spacing:{t['track']};color:{t['ink']};white-space:nowrap}}
.tl.accent{{color:{t['accent']};line-height:1.10}}
.rule{{width:300px;height:2px;background:{t['accent']};margin:34px 0 22px}}
.sub{{font-family:{t['family']};font-size:31px;letter-spacing:.08em;color:{t['muted']};white-space:nowrap}}
.strip{{position:absolute;left:78px;bottom:52px;width:924px;display:flex;justify-content:space-between;
  font-family:{t['small_family']};font-weight:{t['small_weight']};font-size:22px;
  letter-spacing:.18em;color:{t['muted']};text-transform:uppercase}}
</style></head><body>
<div class="cv theme-{theme_key}-sq">
  <div class="paper2"></div>{grain}
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="inner">
    <div class="kicker"><i class="sq"></i><span>{b['kicker']}</span></div>
    <div class="brand">{b['brand']}</div>
    {titles}
    <div class="rule"></div>
    <div class="sub">{b['sub']}</div>
  </div>
  <div class="strip"><span>{b['author']}</span></div>
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


def check(m: dict, errors: list, warns: list, psize=(817, 883), layout="editorial"):
    if not m.get("titles"):
        errors.append("没有标题行")
        return
    for box in m["titles"] + ([m["brand"]] if m.get("brand") else []) + ([m["sub"]] if m.get("sub") else []):
        if box["x"] < 30 or box["r"] > W - 30:
            errors.append(f"文字越出画布边界 ({round(box['x'])}–{round(box['r'])})")
        if layout == "editorial" and box["r"] > SAFE_R:
            errors.append(f"文字右边界 {round(box['r'])} > 安全线 {SAFE_R}")
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
    ap.add_argument("--layout", choices=LAYOUTS)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in THEMES.items():
            print(f"{k:<10} {v['name']:<7} [{v['layout']:<11}] {v['use']}")
        return

    brief = dict(DEMO) if (a.demo or not a.brief) else json.loads(Path(a.brief).read_text(encoding="utf-8"))
    if a.layout:
        brief["layout"] = a.layout
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = {}
    for k in a.themes:
        t = THEMES[k]
        layout_used = brief.get("layout") or t["layout"]
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
        print(f"{flag} {k:<9} {t['name']:<5} ({layout_used:<10}) 右边界 {report[k]['title_r']}")
        for e in errors:
            print("     !", e)
        for w in warns:
            print("     ~", w)

    (out / "cover-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
