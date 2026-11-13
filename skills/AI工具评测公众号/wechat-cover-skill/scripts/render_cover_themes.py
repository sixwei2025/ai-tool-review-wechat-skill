#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多主题封面渲染器 V2 —— 6 套视觉体系，人像必留。

设计依据（都是实测扒下来的，不是自己想的）：
  · op7418/guizang-social-card-skill (8.1k★) —— Editorial / Swiss 双体系 + 10 套配色 token
    「越大越细」：封面主标题 500 字重 + 宽字距；只有小字才加粗加宽字距
  · joeseesun/qiaomu-html-cover —— 0.5 秒停留测试：缩略图里只能有一个第一视觉所有者
  · ponyodong2026/ponyo-cover-anchor-system —— 点击率 = 信息密度 × 视觉锚点
  · 小红书实拍样本（高级感封面，2099/1254 赞）—— 纸感底 + 极小字标注 + 大留白

用法：
  python3 render_cover_themes.py --brief brief.json --out out/
  python3 render_cover_themes.py --demo            # 六套全出，用内置样例文案
  python3 render_cover_themes.py --list            # 列主题
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CUTOUT = ASSETS / "owner_cutout_hd.png"
FACE_BOX = json.loads((ASSETS / "owner_cutout_hd.json").read_text(encoding="utf-8"))["face_box"]

# 画布：公众号首图 2.35:1
W, H = 2350, 1000
# 公众号 1:1 分享卡取横版右侧 1000px；标题不得越线
SQUARE_X = W - H
TEXT_X = 132
SAFE_R = SQUARE_X - 16

SERIF = '"Songti SC","STSong","Source Han Serif SC","Noto Serif CJK SC",serif'
SANS = '"PingFang SC","Noto Sans CJK SC","Helvetica Neue",sans-serif'
LATIN = '"Helvetica Neue","Inter","Arial",sans-serif'


# ============================================================ 六套主题
THEMES = {
    "midnight": dict(
        name="午夜墨",
        paper="#0E0D0C", paper2="#171410", ink="#ECE2CF",
        accent="#D4A04A", accent_on="#0E0D0C",
        muted="rgba(236,226,207,.46)", hair="rgba(236,226,207,.18)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="warm_dark", grain=True,
        use="数据复盘 · 搞钱 · 深夜长文",
    ),
    "paper": dict(
        name="纸本墨",
        paper="#F1EFEA", paper2="#E7E3DA", ink="#0A0A0B",
        accent="#0A0A0B", accent_on="#F1EFEA",
        muted="rgba(10,10,11,.52)", hair="rgba(10,10,11,.20)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="muted", grain=True,
        use="方法论 · 观点 · 教程",
    ),
    "kraft": dict(
        name="牛皮纸",
        paper="#EEDFC7", paper2="#E2CFB2", ink="#2A1E13",
        accent="#9B5A2E", accent_on="#EEDFC7",
        muted="rgba(42,30,19,.55)", hair="rgba(42,30,19,.22)",
        family=SERIF, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.12em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="warm_muted", grain=True,
        use="个人经历 · 复盘 · 故事",
    ),
    "indigo": dict(
        name="靛蓝瓷",
        paper="#F1F3F5", paper2="#E3E9EF", ink="#0A1F3D",
        accent="#315D93", accent_on="#F1F3F5",
        muted="rgba(10,31,61,.52)", hair="rgba(10,31,61,.20)",
        family=SANS, weight=500, track="0em",
        brand_family=LATIN, brand_weight=400, brand_track="0.11em",
        small_family=LATIN, small_weight=600, small_track="0.20em",
        portrait="cool", grain=False,
        use="AI 工具 · 产品 · 技术",
    ),
    "swiss": dict(
        name="瑞士蓝",
        paper="#FAFAF8", paper2="#002FA7", ink="#0A0A0A",
        accent="#002FA7", accent_on="#FFFFFF",
        muted="rgba(10,10,10,.48)", hair="rgba(10,10,10,.16)",
        family=SANS, weight=400, track="-0.01em",
        brand_family=LATIN, brand_weight=400, brand_track="0.10em",
        small_family=LATIN, small_weight=650, small_track="0.16em",
        portrait="muted", grain=False,
        use="产品发布 · 清单 · 数据",
    ),
    "brand": dict(
        name="汇芯红",
        paper="#FAF7F4", paper2="#F2ECE7", ink="#1A1A1A",
        accent="#C7352D", accent_on="#FFFFFF",
        muted="rgba(26,26,26,.52)", hair="rgba(26,26,26,.16)",
        family=SERIF, weight=500, track="-0.005em",
        brand_family=LATIN, brand_weight=300, brand_track="0.13em",
        small_family=LATIN, small_weight=500, small_track="0.22em",
        portrait="normal", grain=False,
        use="跟正文排版一致 · 通用",
    ),
}


# 人像阴影：深底给重影（托出主体），浅底给轻影（重影会在人像左缘留一道脏边）
SHADOW = {
    "midnight": "drop-shadow(-58px 10px 90px rgba(0,0,0,.55))",
    "paper":    "drop-shadow(-22px 6px 46px rgba(0,0,0,.10))",
    "kraft":    "drop-shadow(-26px 7px 50px rgba(60,40,20,.16))",
    "indigo":   "drop-shadow(-22px 6px 46px rgba(10,31,61,.12))",
    "swiss":    "drop-shadow(-18px 5px 40px rgba(0,0,0,.10))",
    "brand":    "drop-shadow(-22px 6px 46px rgba(0,0,0,.12))",
}


# ============================================================ 人像处理
def _curve(a: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """把 [lo, hi] 拉到 [0,1]，超出裁掉。"""
    return np.clip((a - lo) / max(1e-6, hi - lo), 0.0, 1.0)


def trim_alpha(im: Image.Image, pad: int = 2) -> Image.Image:
    """裁掉抠像四周的透明边。不裁的话人像右侧会留一条空隙，看起来像没贴边。"""
    bb = im.split()[-1].getbbox()
    if not bb:
        return im
    x0, y0, x1, y1 = bb
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))


def treat_portrait(src: Path, dst: Path, mode: str) -> Path:
    im = trim_alpha(Image.open(src).convert("RGBA"))
    arr = np.asarray(im).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3:4]
    g = (rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114) / 255.0

    if mode == "warm_dark":
        # 暖调压暗：按亮度选择性压暗 —— 白 T 这种高光压狠一点，脸的中间调保住
        f = (1.04 - 0.40 * g).clip(0.58, 1.04)[..., None]
        out = rgb * f
        out[..., 0] *= 1.10
        out[..., 1] *= 1.00
        out[..., 2] *= 0.86
        out = np.clip(out, 0, 255)
    elif mode == "muted":
        # 低饱和彩照：保留肤色和血色，只把艳度压下来。
        # 纯黑白会像遗像，袁总原话「像我人已经去往西天了」，这条永久删掉。
        gray = np.stack([g * 255.0] * 3, axis=-1)
        out = np.clip(rgb * 0.72 + gray * 0.28, 0, 255)
        out = np.clip(out * 1.01, 0, 255)
    elif mode == "warm_muted":
        # 暖调低饱和：给牛皮纸主题，复古感靠底色，不靠去色
        gray = np.stack([g * 255.0] * 3, axis=-1)
        base = np.clip(rgb * 0.70 + gray * 0.30, 0, 255)
        out = np.clip(base * np.array([1.06, 1.00, 0.92]), 0, 255)
    elif mode == "bw":
        # 黑白高对比：Editorial 的经典处理
        t = _curve(g, 0.06, 0.92) ** 0.92
        t = t * 255.0
        out = np.stack([t, t, t], axis=-1)
    elif mode == "duotone":
        # 双色印刷：暗部进墨褐，亮部进牛皮纸色
        t = _curve(g, 0.05, 0.95)[..., None]
        dark = np.array([42, 30, 19], dtype=np.float32)
        light = np.array([238, 223, 199], dtype=np.float32)
        out = dark + (light - dark) * t
    elif mode == "cool":
        # 冷调去饱和：靛蓝瓷
        gray = np.stack([g * 255.0] * 3, axis=-1)
        mixed = rgb * 0.50 + gray * 0.50
        out = mixed * np.array([0.94, 0.99, 1.08])
        out = np.clip(out, 0, 255)
    elif mode == "normal":
        out = np.clip(rgb * 0.92, 0, 255)
    else:
        out = rgb

    merged = np.concatenate([out, alpha], axis=-1).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(merged, "RGBA")
    img = ImageEnhance.Sharpness(img).enhance(1.12)
    img.save(dst)
    return dst, im.size


# ============================================================ HTML
def build_html(brief: dict, theme_key: str, portrait_uri: str) -> str:
    t = THEMES[theme_key]

    def rgba(hexv: str, a: float) -> str:
        h = hexv.lstrip("#")
        return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

    kicker = html.escape(brief.get("kicker", ""))
    brand = html.escape(brief.get("brand", ""))
    lines = [html.escape(x) for x in brief.get("title_lines", []) if x.strip()]
    sub = html.escape(brief.get("subtitle", ""))
    meta = html.escape(brief.get("meta", ""))

    # 标题组：最后一行为锚点色，并且「越大越细」——字号更大、字重更轻
    title_html = ""
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1
        cls = "accent" if last else ""
        w = 400 if last else t["weight"]
        title_html += (
            f'<div class="tl {cls}"><span style="font-weight:{w}">{ln}</span></div>'
        )

    # 人像几何：整个头必须完整（袁总要求），只让身体底部出血
    # 抠像 PNG 顶部约 13px 就是发顶，所以 p_top 要给到 20 以上
    p_h = 1016
    p_top = 68
    p_w = round(p_h * 817 / 883)
    p_left = W - p_w + 16

    grain = '<div class="grain"></div>' if t["grain"] else ""
    # swiss 用整块蓝色压左侧，别的不加块
    block = '<div class="block"></div>' if theme_key == "swiss" else ""
    stamp = f'<div class="stamp">{html.escape(brief.get("stamp", ""))}</div>' if brief.get("stamp") else ""
    strip_left = html.escape(brief.get("strip_left", brief.get("author", "")))
    # 期号 / 编号属于实现细节，默认不上面；要就显式给 strip_right
    strip_right = html.escape(brief.get("strip_right", ""))
    strip_right_html = f"<span>{strip_right}</span>" if strip_right else ""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
.cv{{position:relative;width:{W}px;height:{H}px;background:{t['paper']};overflow:hidden;
  font-kerning:normal;-webkit-font-smoothing:antialiased}}
.paper2{{position:absolute;inset:0;
  background:radial-gradient(120% 90% at 22% 18%, {t['paper2']} 0%, transparent 62%)}}
.grain{{position:absolute;inset:0;opacity:.5;mix-blend-mode:{"screen" if theme_key=="midnight" else "multiply"};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px}}
.block{{position:absolute;left:0;top:0;width:100%;height:26px;background:{t['accent']}}}

.portrait{{position:absolute;left:{p_left}px;top:{p_top}px;width:{p_w}px;height:{p_h}px;
  object-fit:contain;object-position:bottom;
  filter:{SHADOW[theme_key]}}}
/* 局部 tint：人像满铺，但左侧压一层纸色，让标题压得上去又不糊字 */
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(90deg,{t['paper']} 0%,{t['paper']} 34%,
    {rgba(t['paper'],.97)} 44%,{rgba(t['paper'],.80)} 55%,
    {rgba(t['paper'],.40)} 65%,{rgba(t['paper'],0)} 78%)}}

.txt{{position:absolute;left:{TEXT_X}px;top:0;
  width:1150px;height:{H}px;padding-bottom:86px;
  display:flex;flex-direction:column;justify-content:center}}

.kicker{{display:flex;align-items:center;gap:20px;
  font-family:{t['small_family']};font-weight:{t['small_weight']};
  font-size:29px;letter-spacing:{t['small_track']};color:{t['muted']};
  text-transform:uppercase;margin-bottom:{34 if theme_key!="swiss" else 26}px}}
.kicker .sq{{width:11px;height:11px;background:{t['accent']};flex:0 0 auto}}
.kicker .bar{{width:64px;height:2px;background:{t['accent']};flex:0 0 auto}}

.brand{{font-family:{t['brand_family']};font-weight:{t['brand_weight']};
  font-size:104px;letter-spacing:{t['brand_track']};color:{t['ink']};
  line-height:1;margin-bottom:18px;white-space:nowrap}}

.tl{{font-family:{t['family']};font-weight:{t['weight']};
  font-size:150px;line-height:1.20;letter-spacing:{t['track']};
  color:{t['ink']};white-space:nowrap}}
.tl.accent{{font-size:184px;line-height:1.10;color:{t['accent']}}}

.rule{{width:430px;height:2px;background:{t['accent']};margin:40px 0 24px}}
.sub{{font-family:{t['family']};font-weight:400;font-size:37px;
  letter-spacing:.09em;color:{t['muted']};white-space:nowrap}}
.stamp{{position:absolute;left:{TEXT_X}px;bottom:150px;border:2px solid {t['accent']};
  padding:12px 20px;font-family:{t['small_family']};font-weight:600;font-size:25px;
  letter-spacing:.16em;color:{t['accent']};text-transform:uppercase}}
.strip{{position:absolute;left:{TEXT_X}px;bottom:52px;width:1190px;
  border-top:1px solid {t['hair']};padding-top:19px;
  display:flex;justify-content:space-between;align-items:baseline;
  font-family:{t['small_family']};font-weight:{t['small_weight']};
  font-size:23px;letter-spacing:.20em;color:{t['muted']};text-transform:uppercase}}
</style></head><body>
<div class="cv theme-{theme_key}">
  <div class="paper2"></div>{grain}{block}
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="txt">
    <div class="kicker"><i class="sq"></i><span>{kicker}</span></div>
    <div class="brand">{brand}</div>
    {title_html}
    <div class="rule"></div>
    <div class="sub">{sub}</div>{stamp}
  </div>
  <div class="strip"><span>{strip_left}</span>{strip_right_html}</div>
</div></body></html>"""


# ============================================================ 1:1 竖版分享卡
SW = 1080


def build_square_html(brief: dict, theme_key: str, portrait_uri: str, psize=(817, 883)) -> str:
    """1:1 分享卡单独排版，不是从横版裁切。

    横版裁右侧只会得到一张大头照（文字右边界 937 < 裁切线 1350）。
    微信分享卡的显示尺寸只有 200-300px，所以这里字要大、信息要少。
    """
    t = THEMES[theme_key]

    def rgba(hexv, a):
        h = hexv.lstrip("#")
        return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

    kicker = html.escape(brief.get("kicker", ""))
    brand = html.escape(brief.get("brand", ""))
    lines = [html.escape(x) for x in brief.get("title_lines", []) if x.strip()]
    sub = html.escape(brief.get("subtitle", ""))
    author = html.escape(brief.get("author", ""))

    title_html = ""
    for i, ln in enumerate(lines):
        last = i == len(lines) - 1
        cls = "accent" if last else ""
        w = 400 if last else t["weight"]
        fs = 132 if last else 92
        title_html += f'<div class="tl {cls}" style="font-size:{fs}px"><span style="font-weight:{w}">{ln}</span></div>'

    # 人像：底部出血，居中偏右
    pw = 520
    ph = round(pw * psize[1] / psize[0])
    pl = 400
    pt = SW - ph + 96

    grain = '<div class="grain"></div>' if t["grain"] else ""
    block = '<div class="block"></div>' if theme_key == "swiss" else ""

    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{SW}px;height:{SW}px;overflow:hidden}}
.cv{{position:relative;width:{SW}px;height:{SW}px;background:{t['paper']};overflow:hidden}}
.paper2{{position:absolute;inset:0;background:radial-gradient(120% 80% at 26% 14%,{t['paper2']} 0%,transparent 60%)}}
.grain{{position:absolute;inset:0;opacity:.5;mix-blend-mode:{"screen" if theme_key=="midnight" else "multiply"};
  background-image:radial-gradient(rgba(0,0,0,.055) 1px,transparent 1px);background-size:3px 3px}}
.block{{position:absolute;left:0;top:0;width:100%;height:20px;background:{t['accent']}}}
.portrait{{position:absolute;left:{pl}px;top:{pt}px;width:{pw}px;height:{ph}px;
  object-fit:contain;object-position:bottom;filter:{SHADOW[theme_key]}}}
.tint{{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,{t['paper']} 0%,{t['paper']} 46%,
    {rgba(t['paper'],.92)} 51%,{rgba(t['paper'],.42)} 56%,{rgba(t['paper'],0)} 62%)}}
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
.strip{{position:absolute;left:78px;bottom:52px;width:924px;
  display:flex;justify-content:space-between;
  font-family:{t['small_family']};font-weight:{t['small_weight']};font-size:22px;
  letter-spacing:.18em;color:{t['muted']};text-transform:uppercase}}
</style></head><body>
<div class="cv theme-{theme_key}-sq">
  <div class="paper2"></div>{grain}{block}
  <img class="portrait" src="{portrait_uri}">
  <div class="tint"></div>
  <div class="inner">
    <div class="kicker"><i class="sq"></i><span>{kicker}</span></div>
    <div class="brand">{brand}</div>
    {title_html}
    <div class="rule"></div>
    <div class="sub">{sub}</div>
  </div>
  <div class="strip"><span>{author}</span>{('<span>' + html.escape(brief["strip_right"]) + '</span>') if brief.get("strip_right") else ''}</div>
</div></body></html>"""


# ============================================================ 渲染
def shot(html_path: Path, out_png: Path, clip_w: int, clip_h: int, offset_x: int = 0):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(out_png), clip={"x": offset_x, "y": 0, "width": clip_w, "height": clip_h})
        b.close()
    return out_png


def shot_square(html_path: Path, out_png: Path):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": SW, "height": SW}, device_scale_factor=1)
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(out_png))
        b.close()
    return out_png


def measure(html_path: Path) -> dict:
    """量出文字盒子，跑两条硬闸：不越 1:1 裁切线、不压脸。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(html_path.resolve().as_uri())
        pg.wait_for_timeout(700)
        data = pg.evaluate(
            """() => {
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
        )
        b.close()
    return data


def check(m: dict, errors: list, warns: list, psize=(817, 883)):
    if not m.get("titles"):
        errors.append("没有标题行")
        return
    # 标题与品牌行右边界不得越过 1:1 裁切线
    for box in m["titles"] + ([m["brand"]] if m.get("brand") else []) + ([m["sub"]] if m.get("sub") else []):
        if box["r"] > SAFE_R:
            errors.append(f"文字右边界 {round(box['r'])} > 安全线 {SAFE_R}，1:1 小图会切字")
    # 标题不得压脸
    pr = m.get("portrait")
    if pr:
        # 抠像已按 alpha 裁边，face_box 要按【裁后尺寸】重新映射
        sx, sy = psize[0] / 817.0, psize[1] / 883.0
        fx0 = pr["x"] + (FACE_BOX[0] * sx / psize[0]) * pr["w"]
        fx1 = pr["x"] + (FACE_BOX[2] * sx / psize[0]) * pr["w"]
        fy0 = pr["y"] + (FACE_BOX[1] * sy / psize[1]) * pr["h"]
        fy1 = pr["y"] + (FACE_BOX[3] * sy / psize[1]) * pr["h"]
        for box in m["titles"]:
            if box["r"] > fx0 and box["x"] < fx1 and box["b"] > fy0 and box["y"] < fy1:
                errors.append(f"标题「{box['t']}」压到人脸")
    # 上下出血检查
    for box in m["titles"]:
        if box["y"] < 40 or box["b"] > H - 40:
            warns.append(f"标题「{box['t']}」贴边（y={round(box['y'])}–{round(box['b'])}）")


DEMO = dict(
    kicker="知识星球 · 三个月复盘",
    brand="WorkBuddy",
    title_lines=["全自动运营星球", "3个月18万"],
    subtitle="附保姆级实操 · 5 讲全流程",
    meta="NO.03 / 2026.11",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief")
    ap.add_argument("--out", default="out")
    ap.add_argument("--themes", nargs="*", default=list(THEMES))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for k, v in THEMES.items():
            print(f"{k:<10} {v['name']:<7} {v['use']}")
        return

    brief = DEMO if a.demo or not a.brief else json.loads(Path(a.brief).read_text(encoding="utf-8"))
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    report = {}
    for k in a.themes:
        t = THEMES[k]
        port, psize = treat_portrait(CUTOUT, out / f"_portrait-{k}.png", t["portrait"])
        page = out / f"cover-{k}.html"
        page.write_text(build_html(brief, k, port.as_uri()), encoding="utf-8")

        errors, warns = [], []
        m = measure(page)
        check(m, errors, warns, psize)

        shot(page, out / f"cover-{k}-wide.png", W, H)

        # 1:1 单独排版，不从横版裁
        sq_page = out / f"cover-{k}-square.html"
        sq_page.write_text(build_square_html(brief, k, port.as_uri(), psize), encoding="utf-8")
        shot_square(sq_page, out / f"cover-{k}-square.png")
        report[k] = dict(theme=k, name=t["name"], errors=errors, warns=warns,
                         title_r=[round(b["r"]) for b in m.get("titles", [])])
        flag = "OK " if not errors else "ERR"
        print(f"{flag} {k:<9} {t['name']:<5} 右边界 {report[k]['title_r']}  安全线 {SAFE_R}")
        for e in errors:
            print("     !", e)
        for w in warns:
            print("     ~", w)

    (out / "cover-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
