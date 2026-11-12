#!/usr/bin/env python3
"""Side-by-side sheet: user's reference covers vs. new covers (all scaled to 900x383), with 200px thumbs.
Usage: compare_refs.py --refs a.png b.png c.png --new x.jpg [y.jpg] --out sheet.png"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT = next((p for p in ["/home/box/.fonts/NotoSansCJKsc-Black.otf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"] if Path(p).exists()), None)
def font(sz): return ImageFont.truetype(FONT, sz) if FONT else ImageFont.load_default()

def tile(path, label, color):
    im = Image.open(path).convert("RGB").resize((900, 383), Image.LANCZOS)
    t = Image.new("RGB", (900 + 20 + 200, 383 + 50), "white")
    d = ImageDraw.Draw(t); d.text((0, 6), label, fill=color, font=font(28))
    t.paste(im, (0, 50)); t.paste(im.resize((200, 85), Image.LANCZOS), (920, 50))
    d.text((920, 145), "200px 缩略图", fill="#888", font=font(18))
    return t

ap = argparse.ArgumentParser(); ap.add_argument("--refs", nargs="+", required=True); ap.add_argument("--new", nargs="+", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
left = [tile(p, "参考 · " + Path(p).stem[:30], "#555") for p in a.refs]
right = [tile(p, "新封面 · " + lab, "#C8102E") for p, lab in zip(a.new, ["v2b classic（定稿）", "v2b punch（备选）", "备选 2"])]
rows = max(len(left), len(right)); tw, th = left[0].size
sheet = Image.new("RGB", (tw * 2 + 90, th * rows + 80), "white")
d = ImageDraw.Draw(sheet)
d.text((30, 18), "用户参考封面（左）  vs  新模板渲染（右）", fill="#111", font=font(34))
for i, t in enumerate(left): sheet.paste(t, (30, 70 + i * th))
for i, t in enumerate(right): sheet.paste(t, (tw + 60, 70 + i * th))
sheet.save(a.out); print(a.out, sheet.size)
