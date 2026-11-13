#!/opt/homebrew/bin/python3.11
from __future__ import annotations
"""
X（Twitter）一手评测素材与 Demo 动图抓取脚本（基于开源 vladkens/twscrape, MIT）

功能：
1. 调用本地 twscrape（免官方高价 API Key）按关键词或大V列表搜索 X 推文。
2. 自动下载推文高清配图到本地目录；若推文含视频，直接拉取 MP4 最高清直链并用 ffmpeg 转为 3.5 秒高清 GIF（≤3MB 适配微信）。
3. 输出结构化 x_evidence.json 台账（含原帖 URL、作者 @handle、点赞数、正文与本地素材路径）。

首次绑定 X Cookie 示例（从已登录 x.com 的浏览器复制 auth_token 与 ct0）：
  /opt/homebrew/bin/python3.11 fetch_x_evidence.py --add-cookie "my_x_acc" "auth_token=xxx; ct0=yyy"

日常抓取示例：
  /opt/homebrew/bin/python3.11 fetch_x_evidence.py --query '"Gemini 4 Hydrogen" min_faves:20' --limit 15 --out ./assets/x
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
from twscrape import API, gather


DEFAULT_DB = str(Path.home() / ".config" / "wechat-autopilot" / "twscrape.db")


async def ensure_cookie_account(api: API, username: str, cookies: str) -> None:
    """Register or update an account using browser cookies (auth_token & ct0)."""
    await api.pool.add_account(
        username=username,
        password="cookie_login_unused",
        email=f"{username}@example.com",
        email_password="cookie_login_unused",
        cookies=cookies,
    )
    await api.pool.login_all()


def download_file(url: str, dest: Path) -> bool:
    """Download an image or video variant to dest."""
    try:
        with httpx.Client(follow_redirects=True, timeout=25.0) as client:
            r = client.get(url)
            r.raise_for_status()
            dest.write_bytes(r.content)
            return dest.stat().st_size > 0
    except Exception as exc:
        print(f"[warn] 下载失败 {url}: {exc}", file=sys.stderr)
        return False


def mp4_to_gif(mp4_path: Path, gif_path: Path, duration: float = 3.5) -> bool:
    """Convert a short MP4 clip into a WeChat-friendly <=3MB animated GIF."""
    vf = "fps=10,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer"
    cmd = [
        "ffmpeg", "-y", "-t", str(duration), "-i", str(mp4_path),
        "-vf", vf, str(gif_path),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return gif_path.is_file() and gif_path.stat().st_size > 0
    except Exception as exc:
        print(f"[warn] GIF 转换失败 {mp4_path.name}: {exc}", file=sys.stderr)
        return False


async def run_search(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    api = API(str(db_path))

    if args.add_cookie:
        username, cookies = args.add_cookie
        await ensure_cookie_account(api, username, cookies)
        print(json.dumps({"ok": True, "action": "add_cookie", "username": username, "db": str(db_path)}, ensure_ascii=False))
        if not args.query:
            return 0

    accounts = await api.pool.accounts_info()
    active = [a for a in accounts if a.get("active")]
    if not active:
        print(json.dumps({
            "ok": False,
            "error": "twscrape 账号池为空或未激活",
            "how_to_fix": '请从已登录 x.com 的 Chrome 开发者工具复制 auth_token 与 ct0，执行：/opt/homebrew/bin/python3.11 fetch_x_evidence.py --add-cookie "my_x" "auth_token=xxx; ct0=yyy"',
            "db": str(db_path),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    tweets = await gather(api.search(args.query, limit=args.limit))
    results: list[dict[str, Any]] = []

    for idx, tw in enumerate(tweets, 1):
        handle = tw.user.username if tw.user else "unknown"
        item: dict[str, Any] = {
            "index": idx,
            "id": str(tw.id),
            "url": tw.url,
            "author_handle": f"@{handle}",
            "author_name": tw.user.displayname if tw.user else "",
            "date": str(tw.date),
            "likes": tw.likeCount,
            "retweets": tw.retweetCount,
            "text": tw.rawContent,
            "local_images": [],
            "local_gifs": [],
        }

        if tw.media and getattr(tw.media, "photos", None):
            for p_idx, photo in enumerate(tw.media.photos, 1):
                img_path = out_dir / f"x_{idx:02d}_{handle}_{p_idx}.jpg"
                if download_file(photo.url, img_path):
                    item["local_images"].append(str(img_path))

        if args.gif and tw.media and getattr(tw.media, "videos", None):
            for v_idx, video in enumerate(tw.media.videos, 1):
                variants = [v for v in (video.variants or []) if getattr(v, "url", None)]
                if not variants:
                    continue
                best = sorted(variants, key=lambda v: getattr(v, "bitrate", 0) or 0, reverse=True)[0]
                mp4_path = out_dir / f"x_{idx:02d}_{handle}_{v_idx}.mp4"
                gif_path = out_dir / f"x_{idx:02d}_{handle}_{v_idx}.gif"
                if download_file(best.url, mp4_path):
                    if mp4_to_gif(mp4_path, gif_path, duration=args.gif_seconds):
                        item["local_gifs"].append(str(gif_path))
                    mp4_path.unlink(missing_ok=True)

        results.append(item)

    ledger_path = out_dir / "x_evidence.json"
    ledger_path.write_text(json.dumps({
        "query": args.query,
        "count": len(results),
        "tweets": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "query": args.query,
        "fetched_tweets": len(results),
        "ledger": str(ledger_path),
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取 X（Twitter）一手评测推文、配图与 Demo 动图")
    ap.add_argument("--query", default="", help="X 搜索语法，如 '\"Gemini 4 Hydrogen\" min_faves:20'")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--out", default="./assets/x")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--gif", action="store_true", help="自动把推文视频前几秒转为高清 GIF")
    ap.add_argument("--gif-seconds", type=float, default=3.5)
    ap.add_argument("--add-cookie", nargs=2, metavar=("USERNAME", "COOKIES"), help='绑定浏览器 Cookie："auth_token=...; ct0=..."')
    args = ap.parse_args()

    if not args.query and not args.add_cookie:
        ap.error("必须提供 --query 或 --add-cookie")

    return asyncio.run(run_search(args))


if __name__ == "__main__":
    raise SystemExit(main())
