#!/usr/bin/env python3
"""Make a transparent portrait PNG from a plain-background photo WITHOUT eating a light shirt.

v1 bug: edge flood-fill with color distance <= 48 from every edge (incl. bottom) removed the
white T-shirt, because shirt (~228,235,243) and light-gray background (~200,214,220) differ by ~42.
v2 protection:
  1. seeds only from top edge and left/right edges above `--seed-bottom` (default 70% height),
     never from the bottom edge where the body touches the frame;
  2. a pixel is background only if close to bg color (<= --tol, default 26) AND not brighter
     than bg by more than --bright-guard (default 8 luma) -> white clothing is protected;
  3. small holes filled, edge feathered 1.2px.
Preferred path: if `rembg` is importable (pip install "rembg[cpu]"), the isnet-general-use model is
used instead of the heuristic (this is how the bundled assets/owner_cutout.png was made, 2026-10-09).
Prefer a professionally cut PNG: if assets/owner_cutout.png exists and you did not pass --force,
this script does nothing. Always eyeball the *_check.png it writes (portrait on black and red).
"""
import argparse, math
from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter

def luma(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

def cutout(src: Image.Image, tol: float, bright_guard: float, seed_bottom: float) -> Image.Image:
    rgb = src.convert("RGB"); w, h = rgb.size; px = rgb.load()
    border = [px[x, 0] for x in range(0, w, 4)] + [px[0, y] for y in range(0, int(h * seed_bottom), 4)] + [px[w - 1, y] for y in range(0, int(h * seed_bottom), 4)]
    bg = tuple(sorted(c[i] for c in border)[len(border) // 2] for i in range(3))
    bl = luma(bg)
    def is_bg(x, y):
        c = px[x, y]
        return math.dist(c, bg) <= tol and luma(c) <= bl + bright_guard
    seen = bytearray(w * h); qd = deque()
    def push(x, y):
        i = y * w + x
        if not seen[i] and is_bg(x, y):
            seen[i] = 1; qd.append((x, y))
    for x in range(w): push(x, 0)
    for y in range(int(h * seed_bottom)): push(0, y); push(w - 1, y)
    while qd:
        x, y = qd.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h: push(nx, ny)
    m = Image.new("L", (w, h), 255); mp = m.load()
    for y in range(h):
        row = y * w
        for x in range(w):
            if seen[row + x]: mp[x, y] = 0
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))  # close tiny holes
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    out = src.convert("RGBA"); out.putalpha(m)
    return out

def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--src", default=str(root / "assets/owner_portrait.jpg"))
    ap.add_argument("--out", default=str(root / "assets/owner_cutout.png"))
    ap.add_argument("--tol", type=float, default=26); ap.add_argument("--bright-guard", type=float, default=8)
    ap.add_argument("--seed-bottom", type=float, default=0.70); ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and not a.force:
        print(f"已有 {out}，跳过（--force 重新生成）"); return
    src = Image.open(a.src)
    if min(src.size) < 1000:
        print(f"警告：人像源图只有 {src.size}，封面上会被放大发糊；请换 ≥1500px 高的原片")
    try:
        from rembg import remove, new_session
        cut = remove(src, session=new_session("isnet-general-use"), post_process_mask=True)
        print("使用 rembg isnet-general-use 抠图")
    except ImportError:
        print("未安装 rembg，使用保护主体的启发式抠图（阴影处可能缺损，务必目检）")
        cut = cutout(src, a.tol, a.bright_guard, a.seed_bottom)
    cut.save(out)
    chk = Image.new("RGB", (cut.width * 2, cut.height), (17, 17, 17))
    chk.paste(cut, (0, 0), cut)
    red = Image.new("RGB", cut.size, (179, 0, 44)); red.paste(cut, (0, 0), cut); chk.paste(red, (cut.width, 0))
    chk.save(out.with_name(out.stem + "_check.png"))
    print(f"写入 {out} 和 {out.stem}_check.png，请目检 T 恤/发丝边缘")

if __name__ == "__main__":
    main()
