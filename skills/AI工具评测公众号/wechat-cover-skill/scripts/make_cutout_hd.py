#!/usr/bin/env python3
"""HD portrait cutout with proper matting + edge decontamination.

1. 分割：rembg 生成软 mask（默认 isnet-general-use；birefnet-portrait 要约 5GB 内存，内存够时可用 --model 指定）
2. 已知背景：原图里残留的橙色描边和背景，强制视为背景
3. trimap：确定前景、确定背景，加一条未知带（头发顶部更宽）
4. 闭式 alpha matting（pymatting estimate_alpha_cf）
5. 前景色估计（pymatting estimate_foreground_ml）：去掉边缘混进的红色/橙色背景，也就是 decontamination
6. 轻微羽化（σ≈0.8px），不描边
输出：RGBA PNG，加一张三底色（黑/红/白）放大检查图
用法：make_cutout_hd.py --src cover.png --box x0 y0 x1 y1 --out owner_cutout_hd.png [--model birefnet-portrait]
"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

def hsv(rgb):
    im = Image.fromarray(rgb).convert("HSV"); a = np.asarray(im).astype(np.float32)
    return a[..., 0] * 360 / 255, a[..., 1] / 255, a[..., 2] / 255

def fill_ear_gap(alpha, fgc, r=16):
    """耳垂和下颌之间：原图这里是之前抠图留下的橙色缺口，抠掉后耳垂底部会出现一个“台阶”。
    用形态学闭运算把缺口补上，补的颜色是下颌内侧皮肤的阴影色（×0.5），看起来像耳后的脖子阴影。
    只作用在脸部中段的行（耳朵到下颌），不碰头发和肩膀。"""
    H, W = alpha.shape
    solid = alpha > 0.5
    rows = np.where(solid.any(1))[0]; top = rows.min(); h = rows.max() - top
    y0, y1 = top + int(0.30 * h), top + int(0.62 * h)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]; disk = (xx * xx + yy * yy) <= r * r
    closed = ndi.binary_closing(np.pad(solid, r), structure=disk)[r:-r, r:-r]
    gap = closed & ~solid; gap[:y0] = False; gap[y1:] = False
    if not gap.any():
        return alpha, fgc
    near = ndi.binary_dilation(gap, iterations=6) & solid
    shade = np.median(fgc[near], axis=0) * 0.5
    soft = ndi.gaussian_filter(gap.astype(np.float64), 1.2)
    new_alpha = np.maximum(alpha, soft)
    w = (soft > alpha)[..., None] * np.clip(soft - alpha, 0, 1)[..., None]
    fgc = fgc * (1 - w) + shade[None, None, :] * w
    return new_alpha, fgc

def tiled_cf(img, trimap, cf, tile=160, pad=24):
    """Closed-form matting tile by tile (only tiles containing unknown pixels) to keep memory low on a shared box."""
    alpha = (trimap >= 0.75).astype(np.float64)
    H, W = trimap.shape
    for y in range(0, H, tile):
        for x in range(0, W, tile):
            if not ((trimap[y:y+tile, x:x+tile] > 0.25) & (trimap[y:y+tile, x:x+tile] < 0.75)).any():
                continue
            y0, x0, y1, x1 = max(0, y-pad), max(0, x-pad), min(H, y+tile+pad), min(W, x+tile+pad)
            t = trimap[y0:y1, x0:x1]
            if not (t == 1).any() or not (t == 0).any():
                # 没有前景或背景约束时，用 mask 软值兜底
                sub = np.clip(t, 0, 1)
            else:
                sub = np.clip(cf(img[y0:y1, x0:x1], t), 0, 1)
            alpha[y:min(H, y+tile), x:min(W, x+tile)] = sub[y-y0:y-y0+min(tile, H-y), x-x0:x-x0+min(tile, W-x)]
    return alpha

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True); ap.add_argument("--box", type=int, nargs=4, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--model", default="isnet-general-use"); ap.add_argument("--mask", help="已有的 mask PNG（跳过分割）")
    ap.add_argument("--hair-band", type=int, default=18); ap.add_argument("--no-fill-ear-gap", dest="fill_ear_gap", action="store_false"); ap.add_argument("--band", type=int, default=6)
    a = ap.parse_args()
    from pymatting import estimate_alpha_cf, estimate_foreground_ml
    src = Image.open(a.src).convert("RGB").crop(tuple(a.box))
    rgb = np.asarray(src)
    if a.mask:
        m_img = Image.open(a.mask).convert("L"); model = "mask:" + a.mask
    else:
        from rembg import new_session, remove
        sess = new_session(a.model); model = a.model
        m_img = remove(src, session=sess, only_mask=True); del sess
    m = np.asarray(m_img).astype(np.float32) / 255
    h, s, v = hsv(rgb)
    orange = (h >= 4) & (h <= 40) & (s > 0.62) & (v > 0.45)            # 原图自带的橙色描边/填充
    orange = ndi.binary_dilation(orange, iterations=2)
    skin_guard = (m > 0.98) & ~ndi.binary_dilation(orange, iterations=4)
    fg = ndi.binary_erosion(m > 0.9, iterations=a.band) & ~orange
    bg = ndi.binary_dilation(m < 0.1, iterations=0) & ~ndi.binary_dilation(m > 0.5, iterations=a.band) | orange
    # 头发顶部（mask 上 25%）未知带更宽，让 matting 处理发丝
    ys = np.where(m.max(1) > 0.5)[0]; top = ys.min() if len(ys) else 0
    hair_zone = np.zeros_like(fg); hair_zone[: top + int(0.22 * (rgb.shape[0] - top)), :] = True
    fg_h = ndi.binary_erosion(m > 0.9, iterations=a.hair_band) & ~orange
    bg_h = (m < 0.1) & ~ndi.binary_dilation(m > 0.5, iterations=a.hair_band) | orange
    fg = np.where(hair_zone, fg_h, fg); bg = np.where(hair_zone, bg_h, bg)
    fg |= skin_guard & ~ndi.binary_dilation(~(m > 0.98), iterations=a.band)
    trimap = np.full(m.shape, 0.5); trimap[fg] = 1.0; trimap[bg & ~fg] = 0.0
    # 画布底边（衣服被画框切断处）保持不透明
    bottom = rgb.shape[0] - 3; trimap[bottom:, :][m[bottom:, :] > 0.5] = 1.0
    img = rgb.astype(np.float64) / 255
    alpha = tiled_cf(img, trimap, estimate_alpha_cf)
    alpha[orange] = 0
    # 去掉孤立噪点：只保留最大连通区域附近
    lab, n = ndi.label(alpha > 0.05)
    if n > 1:
        sizes = ndi.sum(np.ones_like(alpha), lab, range(1, n + 1)); keep = 1 + int(np.argmax(sizes))
        alpha[(lab != keep) & (lab > 0)] = 0
    # 头发区去雾：低 alpha 的雾状残留（原图发顶的红色辉光）压掉，发丝保留
    t = np.clip((alpha - 0.18) / (0.85 - 0.18), 0, 1); t = t * t * (3 - 2 * t)
    alpha = np.where(hair_zone, t, alpha)
    alpha = ndi.gaussian_filter(alpha, 0.8)
    alpha[bottom:, :][m[bottom:, :] > 0.5] = 1.0
    alpha[alpha < 0.02] = 0; alpha[alpha > 0.985] = 1
    fgc = estimate_foreground_ml(img, alpha, n_small_iterations=6, n_big_iterations=2)   # decontaminated colours
    fgc = np.clip(fgc, 0, 1)
    # 头发外沿残留红/橙色：在半透明带里把色相压向中性
    edge = (alpha > 0) & (alpha < 0.9)
    hh, ss, vv = hsv((fgc * 255).astype(np.uint8))
    warm = edge & (ss > 0.35) & ((hh < 40) | (hh > 330)) & (vv < 0.55)
    gray = fgc.mean(2, keepdims=True)
    fgc = np.where(warm[..., None], gray * 0.85 + fgc * 0.15, fgc)
    # 头发区：原图发梢自带红色轮廓光，在 alpha<1 的发梢和外沿 6px 内统一去饱和，回到黑发本色
    hair_edge = hair_zone & ((alpha < 0.999) | ~ndi.binary_erosion(alpha > 0.999, iterations=6)) & (vv < 0.32) & (ss < 0.75)
    fgc = np.where(hair_edge[..., None], gray * 0.9 + fgc * 0.1, fgc)
    if a.fill_ear_gap:
        alpha, fgc = fill_ear_gap(alpha, fgc)
    out = np.dstack([(fgc * 255).round(), (alpha * 255).round()]).astype(np.uint8)
    o = Image.fromarray(out, "RGBA"); bb = o.getchannel("A").getbbox(); o = o.crop(bb)
    o.save(a.out)
    meta = {"source": a.src, "box": a.box, "crop_bbox": bb, "model": model, "size": o.size}
    print(json.dumps(meta, ensure_ascii=False))
    # 检查图
    W, H = o.size; sheet = Image.new("RGB", (W * 3, H))
    for i, c in enumerate([(12, 6, 8), (170, 20, 30), (255, 255, 255)]):
        bgi = Image.new("RGB", (W, H), c); bgi.paste(o, (0, 0), o); sheet.paste(bgi, (i * W, 0))
    sheet.save(Path(a.out).with_name(Path(a.out).stem + "_check.png"))

if __name__ == "__main__":
    main()
