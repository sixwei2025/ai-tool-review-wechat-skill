#!/usr/bin/env python3
from __future__ import annotations
"""
AI 评测公众号草稿箱投递脚本（支持 2号 `hao2` 默认 / 主号 `main` 切换）

安全原则：
1. 只存草稿箱（`wechat_add_draft.py` / `wechat_update_draft.py`），绝不自动群发。
2. 所有主机 IP、SSH 密钥路径、远端环境变量路径均通过环境变量读取，仓库零硬编码密钥。
3. 投递前默认调用 `validate_review_article.py` 过硬闸；上传后回读微信 CDN URL JSON。

用法：
  # 投递到 2号（默认评测号）
  python3 publish_review_draft.py \
    --account hao2 --mode add \
    --article article.local-images.json --thumb assets/cover_900x383.jpg \
    --content-image assets/01-bench.png --content-image assets/02-speed.gif \
    --out article.wechat-cdn.json

  # 投递到主号
  python3 publish_review_draft.py --account main --mode add ...
"""
import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path

ACCOUNT_ENVS = {
    "hao2": os.environ.get("WECHAT_REMOTE_ENV_HAO2", "/root/wechat_publish_hao2/wechat.env"),
    "main": os.environ.get("WECHAT_REMOTE_ENV_MAIN", "/root/wechat_publish_workbuddy_ai_team/wechat.env"),
}


def run(cmd: list[str], capture: bool = False) -> str:
    r = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return r.stdout if capture else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="投递 AI 评测文章到微信公众号草稿箱（默认 2号 hao2，支持主号 main）")
    ap.add_argument("--account", choices=("hao2", "main"), default="hao2", help="hao2=2号（评测号默认），main=袁六伟主号")
    ap.add_argument("--mode", choices=("add", "update"), default="add")
    ap.add_argument("--media-id", default="", help="update 模式下必填原草稿 media_id")
    ap.add_argument("--article", required=True)
    ap.add_argument("--md", default="")
    ap.add_argument("--thumb", required=True)
    ap.add_argument("--content-image", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-paragraph", type=int, default=80)
    ap.add_argument("--key", default=os.environ.get("WECHAT_SSH_KEY", str(Path.home() / ".ssh" / "opencław_wechat_publish")))
    ap.add_argument("--target", default=os.environ.get("WECHAT_SERVER_TARGET", ""))
    ap.add_argument("--remote-env", default="")
    ap.add_argument("--remote-root", default=os.environ.get("WECHAT_REMOTE_ROOT", "/root"))
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    if args.mode == "update" and not args.media_id:
        raise SystemExit("update 模式必须传入 --media-id")
    if not args.target:
        env_file = Path.home() / ".config" / "wechat-autopilot" / "wechat.env"
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            args.target = os.environ.get("WECHAT_SERVER_TARGET", "")
            if args.key == str(Path.home() / ".ssh" / "opencław_wechat_publish") and os.environ.get("WECHAT_SSH_KEY"):
                args.key = os.environ["WECHAT_SSH_KEY"]
    if not args.target:
        raise SystemExit("未配置 WECHAT_SERVER_TARGET 环境变量（固定白名单 IP 服务器地址），请先在本地环境配置后再投递")

    remote_env = args.remote_env or ACCOUNT_ENVS[args.account]
    article = Path(args.article).resolve()
    thumb = Path(args.thumb).resolve()
    images = [Path(p).resolve() for p in args.content_image]

    for p in (article, thumb, *images):
        if not p.is_file() or p.stat().st_size == 0:
            raise SystemExit(f"输入文件缺失或为空: {p}")

    local_validator = Path(__file__).resolve().parent / "validate_review_article.py"
    if not args.skip_validate:
        vcmd = [sys.executable, str(local_validator), "--article", str(article), "--max-paragraph", str(args.max_paragraph)]
        if args.md:
            vcmd += ["--md", str(Path(args.md).resolve())]
        run(vcmd)

    # 查找本机已安装的远端上传辅助脚本
    autopilot_scripts = Path.home() / ".agents" / "skills" / "wechat-autopilot" / "skills" / "wechat-auto-publisher" / "scripts"
    remote_script = autopilot_scripts / ("wechat_update_draft.py" if args.mode == "update" else "wechat_add_draft.py")
    remote_validator = autopilot_scripts / "validate_wechat_article.py"
    if not remote_script.is_file():
        raise SystemExit(f"未找到底层微信草稿 API 脚本: {remote_script}")

    job = f"ai-review-{args.account}-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    remote_dir = f"{args.remote_root.rstrip('/')}/{job}"
    ssh = ["ssh", "-i", args.key, "-o", "BatchMode=yes", args.target]
    scp = ["scp", "-q", "-i", args.key, "-o", "BatchMode=yes"]

    run(ssh + [f"mkdir -p {shlex.quote(remote_dir)}/assets"])
    run(scp + [*(str(p) for p in (article, thumb, remote_script, remote_validator, *images)), f"{args.target}:{remote_dir}/"])
    img_names_str = " ".join(shlex.quote(img.name) for img in images)
    if images:
        run(ssh + [f"cd {shlex.quote(remote_dir)} && cp {img_names_str} assets/"])

    article_text = article.read_text(encoding="utf-8")
    cmd = ["python3", remote_script.name]
    if args.mode == "update":
        cmd += ["--media-id", args.media_id]
    cmd += ["--article", article.name, "--thumb", thumb.name, "--max-paragraph", str(args.max_paragraph), "--no-require-xiaohei"]
    for img in images:
        ref = f"assets/{img.name}" if f"assets/{img.name}" in article_text else img.name
        cmd += ["--content-image", ref]

    remote_cmd = (
        f"cd {shlex.quote(remote_dir)} && set -a && . {shlex.quote(remote_env)} && set +a && "
        + " ".join(shlex.quote(p) for p in cmd)
    )
    payload = json.loads(run(ssh + [remote_cmd], capture=True))
    if not payload.get("ok"):
        raise SystemExit(f"微信草稿箱投递失败: {payload}")

    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    run(scp + [f"{args.target}:{remote_dir}/{article.name}", str(out)])
    print(json.dumps({
        **payload,
        "account": args.account,
        "mode": args.mode,
        "article_with_wechat_urls": str(out),
        "remote_audit_dir": remote_dir,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
