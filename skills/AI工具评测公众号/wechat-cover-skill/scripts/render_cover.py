#!/usr/bin/env python3
"""Render 袁六伟's WeChat cover (style v2b, see ../../cover-style-spec.md) via HTML + headless Chrome.

brief.json:
{
  "style": "classic",                 # classic = 金字细线眉标 + 白/金两行 + 细分割线 + ◆副标题（09-28 / 10-06 抹平 那一路）
                                      # punch   = 红色斜切标签 + 斜体粗标题 + 红框副标题，可加图标卡（10-05 / 10-06 活人感 那一路）
  "kicker": "一人公司 · 流程复盘",       # 眉标，≤16 字，可空
  "title_lines": ["AI做交付自动化", "最先卡在验收"],   # 正好 2 行；第 1 行白，第 2 行金（gold_line 可改）
  "gold_line": 2,
  "subtitle": "校验说通过，截图却是坏的",   # ≤14 字，可空
  "cards": [["文","写稿"],["版","排版"]],  # 仅 punch，可选，≤4 张：[图标字, ≤5 字标签]
  "prop": {"title": "验收清单", "items": [["排版", "ok"], ["验收", "x"]]},  # 可选：人像左下的半透明道具面板（≤3 行，ok/x）
  "background": null,                 # 可选：imagegen 生成的无字无人场景图，会以 55% 透明度垫底
  "portrait": null,                   # 默认 assets/owner_cutout_hd.png（同名 .json 里给出 face_box）；禁止 false（对外封面必须真人 IP）
  "layout": "classic",                # classic=左文右人；fullbleed=整图背景铺满+暗化/虚化衬字+右侧仍保留抠像
  "bg_brightness": 0.62,              # fullbleed 建议 0.55–0.7
  "text_shade": 0.72,                 # fullbleed 左侧文字区暗化强度 0–1（右侧少暗化，勿糊脸）
  "bg_blur": 8                        # fullbleed 背景高斯模糊半径（px，0=关；模糊只在背景层）
}
Outputs in --out: cover_master.png 2350x1000, cover_900x383.jpg, cover_1x1.png, cover_1x1_300.png,
cover_200.png, cover_360.png, cover_sheet.png, cover.meta.json (pic_crop_235_1 / pic_crop_1_1 + QA).
Exit 2 on QA failure.
"""
from __future__ import annotations
import argparse, hashlib, html, json, os, random, re, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))  # chrome_shot + rules vendored here
from rules import load_rules  # noqa: E402
from chrome_shot import dump_dom, screenshot  # noqa: E402

W, H = 2350, 1000
SQUARE_X = W - H            # 1350：右侧 1:1 裁切区
FACE_CX = 1880              # 参考封面里脸的中心约在横向 78–82%
FACE_W = 385              # 参考封面脸宽（发际到耳）约 330–390px（按 2350 宽换算），取偏大值让人更“满”
TEXT_X = 110

def vis_len(s: str) -> float:
    return sum(0.58 if (c.isascii() and c not in " ") else (0.3 if c == " " else 1.0) for c in s)

FONT_CANDIDATES = [
    Path.home() / ".fonts/NotoSansCJKsc-Black.otf",
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"),
    ROOT / "assets/fonts/NotoSansCJKsc-Black.otf",
    ROOT / "assets/fonts/NotoSansSC-Black.otf",
    # 本机回退：没装思源黑体时用系统自带的中文粗黑（macOS）
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/PingFang.ttc"),
]

def font_path() -> Path | None:
    """返回可用的粗黑中文字体文件；COVER_FONT 环境变量优先。"""
    env = os.environ.get("COVER_FONT")
    if env and Path(env).expanduser().exists():
        return Path(env).expanduser().resolve()
    for p in FONT_CANDIDATES:
        if p.exists():
            return p.resolve()
    return None

def font_url() -> str:
    p = font_path()
    return p.as_uri() if p else ""

def rim_lit(cut: Image.Image, out_png: Path, strength: float = 0.14, width: int = 4, color=(255, 110, 90)) -> Path:
    """自然轮廓光：只在人像 alpha 边缘向内约 4px 的带状区域，用 screen 方式提亮成暖红色。
    越靠右、越靠上越强；强度低（默认 0.14），只是一层若有若无的暖光（光源是人像身后偏右的红色辉光）。不在外面加描边或发光，所以不会出现红晕。"""
    import numpy as np
    from scipy import ndimage as ndi
    a = np.asarray(cut, dtype=np.float32) / 255.0
    al = a[..., 3]
    inner = ndi.grey_erosion(al, size=(2 * width + 1, 2 * width + 1))
    band = np.clip(al - inner, 0, 1)
    band = ndi.gaussian_filter(band, width / 2.5) * al
    h, w = al.shape
    yy, xx = np.mgrid[0:h, 0:w]
    weight = (0.45 + 0.55 * xx / w) * (1.0 - 0.6 * yy / h)
    rgb = a[..., :3]
    luma = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    # 黑发上的均匀暖光会变成一圈棕色“头盔”边，所以按亮度调制：皮肤和 T 恤边缘有轮廓光，黑发只在高光发丝上有
    k = np.clip(band * weight * strength * 2.2, 0, strength) * np.clip((luma - 0.12) * 2.5, 0, 1)
    k = k[..., None]
    c = np.array(color, dtype=np.float32)[None, None, :] / 255.0
    screen = 1 - (1 - rgb) * (1 - c)
    a[..., :3] = rgb * (1 - k) + screen * k
    Image.fromarray((a * 255).clip(0, 255).astype("uint8"), "RGBA").save(out_png)
    return out_png

def fade_bottom(png: Path, p_top: int, scale: float, y0: float, y1: float, power: float = 1.15) -> Path:
    """按【画布坐标】给人像 alpha 做底部渐隐。
    CSS mask 的百分比相对 <img> 自身高度，而人像通常比画布高（底部出血），
    直接用百分比会把渐隐线落到画布外面，底部变成一条硬切线。这里用像素坐标算，不会错。
    y0 = 开始变透明的画布 y；y1 = 完全消失的画布 y。"""
    import numpy as np
    im = Image.open(png).convert("RGBA")
    a = np.asarray(im).astype(np.float32)
    h = a.shape[0]
    canvas_y = p_top + np.arange(h, dtype=np.float32) * scale
    k = np.clip(1.0 - (canvas_y - y0) / max(1.0, y1 - y0), 0.0, 1.0) ** power
    a[..., 3] *= k[:, None]
    Image.fromarray(a.clip(0, 255).astype("uint8"), "RGBA").save(png)
    return png

def fx(seed: str) -> str:
    rnd = random.Random(int(hashlib.md5(seed.encode()).hexdigest()[:8], 16))
    parts = [
        f'<div class="arc" style="left:{FACE_CX-560}px;top:-180px;width:1120px;height:1120px;opacity:.55"></div>',
        f'<div class="arc" style="left:{FACE_CX-760}px;top:-380px;width:1520px;height:1520px;opacity:.22;border-width:3px"></div>',
    ]
    for _ in range(5):  # 斜向红色光线（右上→左下），集中在人像两侧
        x = rnd.randint(1250, 2300); y = rnd.randint(40, 900); ln = rnd.randint(260, 620); ang = rnd.choice([-28, -30, -33, 150, 152])
        parts.append(f'<div class="streak" style="left:{x}px;top:{y}px;width:{ln}px;transform:rotate({ang}deg);opacity:{rnd.uniform(.45,.9):.2f}"></div>')
    for _ in range(26):  # 火星粒子
        s = rnd.randint(6, 18)
        parts.append(f'<div class="dot" style="left:{rnd.randint(900, 2340)}px;top:{rnd.randint(20, 980)}px;width:{s}px;height:{s}px;opacity:{rnd.uniform(.35,.95):.2f}"></div>')
    return "\n".join(parts)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("brief"); ap.add_argument("--out", required=True); ap.add_argument("--rules")
    a = ap.parse_args()
    r = load_rules(a.rules)["cover"]
    b = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    brief_dir = Path(a.brief).resolve().parent
    for k in ("background", "portrait"):   # brief 自己的相对路径按 brief 所在目录解析
        if isinstance(b.get(k), str) and b.get(k) and not Path(b[k]).is_absolute() and not Path(b[k]).exists(): b[k] = str(brief_dir / b[k])
    dp = ROOT / "templates/default-brief.json"   # 2026-10-17：默认模板只提供风格参数；内容字段必须每篇自己写
    if b.get("use_default", True) and dp.exists():
        layout0 = b.get("layout", "classic")
        req = ["kicker", "title_lines", "subtitle", "square_badge", "background"]
        if b.get("bg_optional"):          # 纯色底封面（瑞士风）：不铺插画背景，只用模板自带暗底
            req.remove("background")
        if layout0 != "fullbleed":
            req.append("bg_subject_x")
        missing = [k for k in req if b.get(k) in (None, "", [])]
        if missing:
            print(json.dumps({"ok": False, "errors": ["brief 缺少必填内容字段：" + "、".join(missing) + "（参考 templates/example-brief-xiaowangzi.json）"]}, ensure_ascii=False)); sys.exit(2)
        d = json.loads(dp.read_text(encoding="utf-8")); d.pop("_doc", None)
        pal = {**d.get("palette", {}), **b.get("palette", {})}
        bst = {**d.get("badge_style", {}), **b.get("badge_style", {})}
        b = {**d, **b, "palette": pal, "badge_style": bst}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    errs, warns = [], []
    pal = b.get("palette", {})
    style = b.get("style", "classic")
    if style not in ("classic", "punch"): errs.append("style 只能是 classic / punch")
    lines = [l.strip() for l in b.get("title_lines", []) if l.strip()]
    if not (2 <= len(lines) <= 3): errs.append("标题 2–3 行（默认两行：白色陈述 + 金色结论；三行用于「品牌名 / 主标题 / 数字结论」这种层级）")
    if any(vis_len(l) > r["title_max_vis_per_line"] for l in lines): errs.append(f"单行视觉长度 > {r['title_max_vis_per_line']}（汉字=1，数字/字母≈0.6）")
    if sum(len(l.replace(' ', '')) for l in lines) > r["title_max_chars_total"]: errs.append(f"标题总字数 > {r['title_max_chars_total']}")
    kicker = (b.get("kicker") or "").strip(); sub = (b.get("subtitle") or "").strip()
    if len(kicker) > r["kicker_max_chars"]: errs.append(f"眉标 > {r['kicker_max_chars']} 字")
    if len(sub) > r["subtitle_max_chars"]: errs.append(f"副标题 > {r['subtitle_max_chars']} 字")
    cards = b.get("cards") or []
    if cards and style != "punch": errs.append("图标卡只用于 punch 风格")
    if len(cards) > 4 or any(len(c) != 2 or len(c[1]) > 5 for c in cards): errs.append("cards 最多 4 张，每张 [图标字, ≤5 字]")
    gold = int(b.get("gold_line", 2))
    if gold not in (1, 2, 3): errs.append("gold_line 只能是 1–3（三行封面用 3）")
    if errs: print(json.dumps({"ok": False, "errors": errs}, ensure_ascii=False)); sys.exit(2)

    # 硬规则（六伟 2026-10-28）：对外封面必须真人 IP 露出；禁止 portrait:false 藏人像
    if "portrait" in b and b.get("portrait") is False:
        print(json.dumps({"ok": False, "errors": [
            "对外封面必须真人 IP 露出，禁止 portrait:false（默认用 assets/owner_cutout_hd.png；"
            "layout=fullbleed 是整图背景+暗化虚化+右侧抠像，不是去人像）"
        ]}, ensure_ascii=False)); sys.exit(2)
    if "portrait" in b and b.get("portrait") is None:
        print(json.dumps({"ok": False, "errors": [
            "对外封面必须真人 IP 露出：brief 里不要写 \"portrait\": null 来藏人像；"
            "删掉 portrait 字段即走默认抠像，或显式给抠像路径"
        ]}, ensure_ascii=False)); sys.exit(2)

    layout = b.get("layout", "classic")
    if layout not in ("classic", "fullbleed"):
        errs.append("layout 只能是 classic / fullbleed"); print(json.dumps({"ok": False, "errors": errs}, ensure_ascii=False)); sys.exit(2)
    fullbleed = layout == "fullbleed"

    # 人像：classic / fullbleed 都必须渲染（默认 owner_cutout_hd）；按 face_box 缩放
    portrait = Path(b.get("portrait") or ROOT / "assets/owner_cutout_hd.png")
    side = portrait.with_suffix(".json")
    cut = Image.open(portrait).convert("RGBA")
    if side.exists():
        fb = json.loads(side.read_text(encoding="utf-8"))["face_box"]
    else:
        bb = cut.getchannel("A").getbbox(); fb = [bb[0] + (bb[2]-bb[0]) * .28, bb[1], bb[0] + (bb[2]-bb[0]) * .72, bb[1] + (bb[3]-bb[1]) * .55]
        warns.append("人像没有 face_box 文件，按比例估算脸部位置；请目检")
    s = FACE_W / (fb[2] - fb[0])
    p_h = round(cut.height * s); p_w = round(cut.width * s)
    p_left = round(FACE_CX - (fb[0] + fb[2]) / 2 * s)
    p_top = max(H + 12 - p_h, round(H * 0.10 - fb[1] * s))   # 底部出血；头顶约在 11% 高度
    if p_top + p_h < H: errs.append("人像底边没有出血到画布底部（源图太短）")
    face = (p_left + fb[0] * s, p_top + fb[1] * s, p_left + fb[2] * s, p_top + fb[3] * s)
    if s > 1.6: warns.append(f"人像放大 {s:.2f} 倍，可能发糊；建议换更高清原片")
    if fullbleed:
        warns.append("layout=fullbleed：整图背景铺满 + 文字区暗化/虚化 + 右侧保留抠像")

    tw = 1000 if cards else 1240
    lens = [vis_len(l) for l in lines]
    ls = 6
    cap_px = int(b.get("title_max_px", 240 if b.get("flat") else 205))
    base_px = int(min(cap_px, min((tw - ls * len(l)) / vl for l, vl in zip(lines, lens))))
    if style == "punch": base_px = int(base_px * 0.97)
    want = b.get("title_px_lines") or []          # 可选：逐行字号，如 [150, 195, 235]
    title_pxs = []
    for i, (l, vl) in enumerate(zip(lines, lens)):
        w_ = int(want[i]) if i < len(want) and want[i] else base_px
        title_pxs.append(int(min(w_, (tw - ls * len(l)) / vl)))   # 逐行再按可用宽度收一次，防溢出
    title_px = max(title_pxs)
    if sum(px * 1.12 for px in title_pxs) > H * 0.62:
        warns.append(f"标题 {len(lines)} 行总高超过画布 62%（约 {int(sum(px * 1.12 for px in title_pxs))}px），可能挤压副标题")
    if min(title_pxs) < r["title_min_height_ratio"] * H: errs.append(f"标题最小字号 {min(title_pxs)}px < {int(r['title_min_height_ratio']*H)}px，请缩短")

    tcls = b.get("title_classes") or []      # 逐行附加 class：lat=拉丁细体、dim=灰色、留空=默认
    flat = bool(b.get("flat"))
    def tl(i, l):
        cls = "g" if i + 1 == gold else "w"
        extra = (" " + tcls[i]) if i < len(tcls) and tcls[i] else ""
        return f'<div class="t {cls}{extra}" style="font-size:{title_pxs[i]}px"><span>{html.escape(l)}</span></div>'
    title_html = "".join(tl(i, l) for i, l in enumerate(lines))
    if not kicker: kicker_html = ""
    elif style == "classic" and b.get("kicker_tag"): kicker_html = f'<div class="ktag" id="kick" style="background:linear-gradient(180deg,{pal.get("tag_top", "#E3262F")},{pal.get("tag_bottom", "#A30B16")})"><span>{html.escape(kicker)}</span></div>'  # 2026-10-17 红底标签条
    elif style == "classic":
        kcls = "kicker" if b.get("kicker_rule", True) else "kicker kr-off"
        lead = '<i class="sq"></i>' if b.get("flat") else "<i></i>"
        tail = "" if b.get("flat") else "<i></i>"
        kicker_html = f'<div class="{kcls}" id="kick" style="margin-left:{int(b.get("kicker_offset", title_px*0.9))}px">{lead}<span>{html.escape(kicker)}</span>{tail}</div>'
    else: kicker_html = f'<div class="ktag" id="kick"><span>{html.escape(kicker)}</span></div>'
    if not sub: sub_html = ""
    elif style == "classic":
        scls = "sub" if b.get("sub_mark", True) else "sub plain"
        sub_html = f'<div class="rule"></div><div class="{scls}" id="sub"><b></b><span>{html.escape(sub)}</span></div>'
    else: sub_html = f'<div class="stag" id="sub"><span>{html.escape(sub)}</span></div>'
    cards_html = "".join(f'<div class="card" style="left:1130px;top:{200 + i*150 + (0 if len(cards) > 3 else 60)}px"><div class="ic">{html.escape(c[0])}</div><div class="lb">{html.escape(c[1])}</div></div>' for i, c in enumerate(cards))
    prop = b.get("prop")
    prop_html = ""
    if prop:
        items = prop.get("items", [])
        if len(items) > 3 or any(len(i) != 2 or i[1] not in ("ok", "x") or len(i[0]) > 5 for i in items):
            errs.append("prop.items 最多 3 行，每行 [≤5 字, ok|x]")
        rows = "".join(f'<div class="row"><span>{html.escape(n)}</span>' + ('<span class="ok">✔</span>' if st == "ok" else '<span class="x">✕</span>') + '</div>' for n, st in items)
        prop_html = f'<div class="prop" id="prop"><h4>{html.escape(prop.get("title", ""))}</h4>{rows}</div>'
    bg = b.get("background")
    if bg and not Path(bg).is_absolute() and not Path(bg).exists():   # 2026-10-17：相对路径按 brief 所在目录解析（gzh.py build 在 v2 根目录调用）
        bg = str(Path(a.brief).resolve().parent / bg)
    if bg and not Path(bg).exists():   # 背景是必填内容，找不到就停止渲染
        print(json.dumps({"ok": False, "errors": [f"background 文件不存在: {bg}"]}, ensure_ascii=False)); sys.exit(2)
    if bg and Path(bg).exists() and (fullbleed or float(b.get("bg_brightness", 1.0)) < 1.0 or b.get("bg_subject_x") is not None):
        from PIL import ImageEnhance, ImageFilter
        br = float(b.get("bg_brightness", 0.62 if fullbleed else 1.0))
        fr0 = Image.open(bg).convert("RGB")
        if fullbleed:
            # cover 铺满整画布 2350×1000（不做左侧渐隐成黑底 + 右侧留人像位）
            scale = max(W / fr0.width, H / fr0.height)
            nw, nh = round(fr0.width * scale), round(fr0.height * scale)
            fr = fr0.resize((nw, nh), Image.LANCZOS)
            fx_ = float(b.get("bg_focus_x", 0.55)); fy_ = float(b.get("bg_focus_y", 0.45))
            left = max(0, min(nw - W, round(fx_ * nw - W / 2)))
            top = max(0, min(nh - H, round(fy_ * nh - H / 2)))
            fr = fr.crop((left, top, left + W, top + H))
            blur_r = float(b.get("bg_blur", 8))
            if blur_r > 0:
                fr = fr.filter(ImageFilter.GaussianBlur(radius=blur_r))
            fr = ImageEnhance.Brightness(fr).enhance(br)
            if br < 0.5: warns.append(f"bg_brightness={br} 过暗，标题区可能发闷")
            cv = fr
        else:
            fr = ImageEnhance.Brightness(fr0).enhance(br)
            if br < 0.85: warns.append("bg_brightness < 0.85，压暗超过 15%")
            cv = Image.new("RGB", (W, H), pal.get("canvas_bg", "#080405"))
            if b.get("bg_subject_x") is not None:
                fr = fr.resize((round(fr.width * H / fr.height), H), Image.LANCZOS)
                x0 = int(b.get("bg_subject_target_x", 1470)) - round(float(b["bg_subject_x"]) * fr.width)
                fade = int(b.get("bg_fade_px", 360)); mk = Image.new("L", fr.size, 255)
                for x in range(min(fade, fr.width)): mk.paste(int(255 * x / fade), (x, 0, x + 1, H))
                cv.paste(fr, (x0, 0), mk)
            else:
                cv = fr
        bg = str(out / "bg_composed.jpg"); cv.save(bg, quality=92)

    text_shade = float(b.get("text_shade", 0.72 if fullbleed else 0.82))
    text_shade = max(0.0, min(0.95, text_shade))
    text_shade_mid = round(text_shade * 0.55, 3)
    css_blur = float(b.get("bg_blur_css", 0 if not fullbleed else max(0.0, float(b.get("bg_blur", 8)) * 0.4)))
    bg_op = float(b.get("bg_opacity", 1.0 if fullbleed else 0.55))
    # 人像底部渐隐：mask 的百分比是相对 <img> 自身高度，而人像通常比画布高，
    # 直接用 % 会把渐隐线落到画布外面 → 底部变成硬切。这里统一换算成 img 内像素坐标。
    fa = float(b.get("fade_start", 0.56)) * H      # 画布坐标：从这里开始渐隐
    fb_ = float(b.get("fade_mid", 0.80)) * H       # 到 90% 不透明
    fc = float(b.get("fade_end", 1.0)) * H         # 到这里完全消失
    def _iy(y): return max(0, round(y - p_top))
    do_fade = bool(b.get("fade_start")) and (b.get("flat") or b.get("portrait_fade"))
    mask_css = "none" if do_fade else (f"linear-gradient(180deg,#000 0px,#000 {_iy(fa)}px,rgba(0,0,0,.90) {_iy(fb_)}px,"
                f"rgba(0,0,0,.45) {_iy((fb_+fc)/2)}px,rgba(0,0,0,0) {_iy(fc)}px)")
    lit = rim_lit(cut, out / "portrait_lit.png", strength=float(b.get("rim_strength", 0.14)))
    if do_fade:
        lit = fade_bottom(lit, p_top, s, fa, fc, float(b.get("fade_power", 1.15)))
    portrait_html = f'<img class="portrait" id="portrait" src="{lit.resolve().as_uri()}">'
    glow_x = str(FACE_CX - 20)
    if fullbleed or b.get("fx") is False:
        # 瑞士风：去 arc/斜光线/火星粒子/地面网格，画面只留标题、人像、一条发丝线
        fx_html = ""
        floor_html = ""
    else:
        fx_html = fx("".join(lines))
        floor_html = '<div class="floor"></div>'
    def g_(k, d): return b.get(k, d)
    rep = {"{{flat_cls}}": "flat" if b.get("flat") else "",
           "{{flat_bg}}": g_("flat_bg", "#0B0B0C"),
           "{{gold_solid}}": g_("gold_solid", "#F0A63C"),
           "{{mid_color}}": g_("mid_color", "#B9B9B9"),
           "{{ls_set}}": str(g_("title_ls_set", 0)),
           "{{lat_weight}}": str(g_("lat_weight", 300)),
           "{{lat_ls}}": str(g_("lat_ls", 8)),
           "{{port_sat}}": str(g_("port_saturate", 0.82)),
           "{{port_bright}}": str(g_("port_brightness", 0.94)),
           "{{port_contrast}}": str(g_("port_contrast", 1.02)),
           "{{mask_css}}": mask_css,
           "{{rule_color}}": g_("rule_color", "rgba(255,255,255,.14)"),
           "{{accent_fade}}": g_("accent_fade", "rgba(200,16,46,.28)"),
           "{{rule_mt}}": str(g_("rule_mt", 44)),
           "{{rule_mb}}": str(g_("rule_mb", 26)),
           "{{sub_color}}": g_("sub_color", "#7E7E7E"),
           "{{sub_ls}}": str(g_("sub_ls", 3)),
           "{{kicker_color}}": g_("kicker_color", "#7E7E7E"),
           "{{kick_ls}}": str(g_("kick_ls", 6)),
           "{{kick_sq}}": str(g_("kick_sq", 14)),
           "{{kick_sq_gap}}": str(g_("kick_sq_gap", 20)),
           "{{accent}}": g_("accent", "#C8102E"),
           "{{prop_html}}": prop_html, "{{prop_left}}": "1165", "{{prop_top}}": "560", "{{style}}": style, "{{layout}}": layout,
           "{{glow_x}}": glow_x, "{{p_left}}": str(p_left), "{{p_top}}": str(p_top), "{{p_height}}": str(p_h),
           "{{portrait_html}}": portrait_html, "{{floor_html}}": floor_html,
           "{{font_black}}": font_url(), "{{tx}}": str(int(b.get("text_x", TEXT_X))), "{{tw}}": str(tw + 120),
           "{{title_ls}}": str(ls), "{{title_lh}}": str(b.get("title_lh", 1.12)), "{{kicker_px}}": str(b.get("kicker_px", 50 if style == "classic" else 60)), "{{sub_px}}": str(b.get("sub_px", 52 if style == "classic" else 56)),
           "{{rule_w}}": "860", "{{title_html}}": title_html, "{{kicker_html}}": kicker_html, "{{sub_html}}": sub_html,
           "{{cards_html}}": cards_html, "{{fx_html}}": fx_html,
           "{{text_shade}}": f"{text_shade:.3f}", "{{text_shade_mid}}": f"{text_shade_mid:.3f}",
           "{{bg_blur_css}}": f"{css_blur:.1f}",
           "{{bg_layer}}": f'<div class="bgimg" style="background-image:url(\'{Path(bg).resolve().as_uri()}\');opacity:{bg_op:.2f};background-position:{b.get("bg_position", "center")}"></div>' if bg else ""}
    tpl = (ROOT / "templates/cover.html").read_text(encoding="utf-8")
    for k, v in rep.items(): tpl = tpl.replace(k, v)
    page = out / "cover.html"; page.write_text(tpl, encoding="utf-8")

    dom = dump_dom(page, W, H)
    m = re.search(r"QA=(\{.*?\})</pre>", dom, re.S)
    qa = json.loads(html.unescape(m.group(1))) if m else {}
    if not qa: errs.append("QA 脚本未返回结果")
    if qa.get("fonts") != "black": warns.append(f"未加载超粗黑体（当前字体 {font_path() or '无'}），字重可能不够；装思源黑体 Heavy 或设 COVER_FONT 指向字体文件")
    def inter(a1, b1, tol=4): return not (a1[2] <= b1[0] + tol or b1[2] <= a1[0] + tol or a1[3] <= b1[1] + tol or b1[3] <= a1[1] + tol)   # tol：相邻行矩形边界相接 1px 不算压
    boxes = [("title", (t["x"], t["y"], t["x"] + t["w"], t["y"] + t["h"])) for t in qa.get("titles", [])]
    for k in ("kicker", "sub"):
        if qa.get(k): v = qa[k]; boxes.append((k, (v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"])))
    # classic / fullbleed 同级：压脸、出血、文字不进肩线、1:1 含完整脸
    shoulder_x = p_left + 0.10 * p_w
    for name, bx in boxes:
        if bx[2] > SQUARE_X - 14: errs.append(f"{name} 伸进 1:1 裁切区（右边界 {bx[2]} > {SQUARE_X - 14}），手机小图会被切字")
        if bx[2] > shoulder_x: errs.append(f"{name} 伸进人像（右边界 {bx[2]} > {round(shoulder_x)}）")
        if bx[0] < 70 or bx[1] < 40 or bx[3] > H - 40: errs.append(f"{name} 超出安全边距 {bx}")
        if inter(bx, face): errs.append(f"{name} 压到人脸")
    if qa.get("prop"):
        pb = qa["prop"]; pbox = (pb["x"], pb["y"], pb["x"] + pb["w"], pb["y"] + pb["h"])
        if inter(pbox, face): errs.append("道具面板压到人脸")
        if pbox[3] > H - 20: errs.append("道具面板超出底边")
        for name, bx in boxes:
            if inter(pbox, bx): errs.append(f"道具面板与 {name} 重叠")
    for c in qa.get("cards", []):
        cb = (c["x"], c["y"], c["x"] + c["w"], c["y"] + c["h"])
        if inter(cb, face): errs.append("图标卡压到人脸")
        for name, bx in boxes:
            if inter(cb, bx): errs.append(f"图标卡与 {name} 重叠")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if inter(boxes[i][1], boxes[j][1]): errs.append(f"{boxes[i][0]} 与 {boxes[j][0]} 重叠")
    if face[0] < SQUARE_X or face[2] > W: errs.append(f"人脸不完整落在右侧 1:1 区: {tuple(round(v) for v in face)}")

    master = out / "cover_master.png"
    screenshot(page, master, W, H)
    im = Image.open(master).convert("RGB")
    if im.size != (W, H): errs.append(f"母版尺寸异常 {im.size}")
    badge = (b.get("square_badge") or "").strip()   # 2026-10-17：1:1 区左上角红底角标（画进母版，公众号按 pic_crop_1_1 裁切时也带上），≤8 字
    if badge:
        if len(badge) > 8: errs.append("square_badge > 8 字")
        from PIL import ImageDraw, ImageFont
        _fpath = font_path()
        bs = b.get("badge_style", {})
        try:
            fnt = ImageFont.truetype(str(_fpath), int(bs.get("font_px", 64))) if _fpath else ImageFont.load_default()
        except OSError:
            errs.append(f"角标字体无法加载（{_fpath}），中文角标会变成方块")
            fnt = ImageFont.load_default()
        d = ImageDraw.Draw(im); bx = d.textbbox((0, 0), badge, font=fnt)
        # 1:1 区固定右侧带脸裁切；角标画在 SQUARE_X 左上
        badge_base_x = SQUARE_X
        px_, py_ = int(bs.get("pad_x", 32)), int(bs.get("pad_y", 22)); x0, y0 = badge_base_x + int(bs.get("pos", [40, 40])[0]), int(bs.get("pos", [40, 40])[1]); x1, y1 = x0 + (bx[2] - bx[0]) + 2 * px_, y0 + (bx[3] - bx[1]) + 2 * py_
        d.rounded_rectangle((x0, y0, x1, y1), radius=int(bs.get("radius", 14)), fill=pal.get("badge_fill", "#C8102E"), outline=pal.get("badge_outline", "#FFD68C"), width=int(bs.get("outline_width", 3)))
        d.text((x0 + px_ - bx[0], y0 + py_ - bx[1]), badge, font=fnt, fill=pal.get("badge_text", "#FFFFFF"))
        im.save(master)
    ex_w, ex_h = r["export"]
    jpg = out / "cover_900x383.jpg"
    im.resize((ex_w, ex_h), Image.LANCZOS).save(jpg, "JPEG", quality=92, optimize=True, progressive=True)
    if jpg.stat().st_size >= r["export_max_bytes"]: errs.append("导出 JPG ≥ 1MB")
    # 无论 classic / fullbleed：1:1 都取右侧带完整脸的裁切
    pic_crop_1_1 = f"{SQUARE_X / W:.6f}_0_1_1"
    sq = im.crop((SQUARE_X, 0, W, H))
    sq.save(out / "cover_1x1.png"); sq.resize((300, 300), Image.LANCZOS).save(out / "cover_1x1_300.png")
    for twd in r["thumb_check_widths"]:
        im.resize((twd, round(twd * H / W)), Image.LANCZOS).save(out / f"cover_{twd}.png")
    sheet = Image.new("RGB", (900 + 30 + 383, 383 + 30 + 160), "white")
    sheet.paste(Image.open(jpg), (0, 0)); sheet.paste(sq.resize((383, 383), Image.LANCZOS), (930, 0))
    sheet.paste(Image.open(out / "cover_200.png"), (0, 413)); sheet.paste(Image.open(out / "cover_360.png"), (230, 413))
    sheet.paste(sq.resize((120, 120), Image.LANCZOS), (620, 413)); sheet.save(out / "cover_sheet.png")
    meta = {"pic_crop_235_1": "0_0_1_1", "pic_crop_1_1": pic_crop_1_1, "style": style, "layout": layout,
            "title_lines": lines, "title_px": title_px,
            "face_box": [round(v) for v in face],
            "portrait": str(portrait),
            "portrait_scale": round(s, 3),
            "bg_brightness": float(b.get("bg_brightness", 0.62 if fullbleed else 1.0)),
            "text_shade": text_shade, "bg_blur": float(b.get("bg_blur", 8 if fullbleed else 0)),
            "jpg_kb": jpg.stat().st_size // 1024, "qa": qa, "errors": errs, "warnings": warns}
    (out / "cover.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": not errs, "errors": errs, "warnings": warns, "jpg": str(jpg), "jpg_kb": meta["jpg_kb"], "sheet": str(out / "cover_sheet.png"), "layout": layout}, ensure_ascii=False, indent=2))
    sys.exit(2 if errs else 0)

if __name__ == "__main__":
    main()
