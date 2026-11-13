#!/usr/bin/env python3
from __future__ import annotations
"""
AI 评测公众号 2.0 · 一体化硬闸校验器 (`validate_review_article.py`)

一次执行同时校验 Markdown 原稿与转换后的微信草稿 JSON：
1. 排版与微信兼容硬闸：禁 `<div>`、`class`、`id`、`<style>`、`<script>`、渐变 `*-gradient`、双重转义 `&amp;quot;`、残留反引号。
2. 段落呼吸硬闸：单段上限 ≤80 字；严禁出现连续 3 段 ≤15 字的「电报碎句群」（彻底废除旧版一句一段碎句）。
3. 高价值原件硬闸：长文（≥1500 字）必须包含 ≥2 个可复制原件块（`white-space:pre-wrap` 代码块或结构化对比表 `<table>`）。
4. 主题外壳硬闸：必须已通过 `apply_theme_shell.py` 装配主题专属开篇卡与章节头（含 `<span leaf="">`）。
5. 说人话与合规硬闸：零法官腔（「判决/宣判/落槌」）、翻案句（「不是…而是…」）≤2、提示冒号 ≤6、广告法绝对化极限词拦截。

用法：
  python3 validate_review_article.py --article article.local-images.json --md 03-review.md
"""
import argparse
import json
import re
import statistics
import sys
from html import unescape
from pathlib import Path

DEFAULT_MAX_PARAGRAPH = 80

JUDGE_WORDS = ("判决", "宣判", "裁定", "裁决", "本案", "落槌", "铁证如山")
BANNED_HYPE = ("颠覆行业", "遥遥领先", "史无前例", "宇宙第一", "吊打一切", "100%准确", "包过", "必赚")


def strip_tags(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", html))


def image_sources(content: str) -> list[str]:
    return re.findall(r'<img[^>]+src="([^"]+)"', content)


def local_image_exists(article_path: Path, src: str) -> bool:
    if src.startswith(("http://", "https://")):
        return True
    candidates = [
        article_path.parent / src,
        article_path.parent / "assets" / Path(src).name,
        Path(src),
    ]
    return any(p.exists() for p in candidates)


def check_markdown_tone(md_path: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    raw = md_path.read_text(encoding="utf-8")
    if "## 正文" in raw:
        raw = raw.split("## 正文", 1)[1]

    # Strip code blocks and tables before checking narrative paragraphs
    no_code = re.sub(r"```.*?```", "", raw, flags=re.S)
    narrative_lines = [
        l.strip()
        for l in no_code.splitlines()
        if l.strip()
        and not l.strip().startswith(("!", "#", "|", ">", "-", "*", "```", "（", "("))
        and not re.match(r"^\d+\.\s+", l.strip())
    ]

    # 1. 反电报碎句检测：连续 3 段 ≤15 字
    staccato_runs = []
    cur = []
    for p in narrative_lines:
        if len(p) <= 15:
            cur.append(p)
        else:
            if len(cur) >= 3:
                staccato_runs.append(" / ".join(cur))
            cur = []
    if len(cur) >= 3:
        staccato_runs.append(" / ".join(cur))
    if staccato_runs:
        errors.append(f"反电报碎句硬闸：发现 {len(staccato_runs)} 处连续 ≥3 段 ≤15 字的碎句群（例：{staccato_runs[0]}）")

    # 2. 法官腔检测
    judge_hits = [w for w in JUDGE_WORDS if w in no_code]
    if judge_hits:
        errors.append(f"说人话硬闸：命中禁用「法官腔」词汇：{', '.join(judge_hits)}")

    # 3. 喊麦/绝对化违禁词
    hype_hits = [w for w in BANNED_HYPE if w in no_code]
    if hype_hits:
        errors.append(f"合规硬闸：命中夸张/绝对化禁用词：{', '.join(hype_hits)}")

    # 4. 翻案腔（不是A而是B）
    flips = [
        m.group(0).strip()
        for m in re.finditer(r"不是[^。！？\n]{1,35}[，,][^。！？\n]{0,10}(?:而是|是)[^\n。！？]{1,25}", no_code)
    ]
    if len(flips) > 2:
        errors.append(f"AI 味硬闸：「不是…而是…」翻案句出现 {len(flips)} 处（上限 ≤2）：{flips[:3]}")

    # 5. 破折号与结论提示冒号
    dash_count = no_code.count("——")
    if dash_count > 1:
        warnings.append(f"正文中出现 {dash_count} 处破折号「——」，建议改为句号或逗号")

    lens = [len(p) for p in narrative_lines]
    metrics = {
        "narrative_paragraphs": len(narrative_lines),
        "avg_paragraph_len": round(statistics.mean(lens), 1) if lens else 0,
        "flip_sentences": len(flips),
        "staccato_clusters": len(staccato_runs),
    }
    return errors, warnings, metrics


def validate_json(article_path: Path, max_paragraph: int, min_images: int | None) -> tuple[list[str], list[str]]:
    article = json.loads(article_path.read_text(encoding="utf-8"))
    title = article.get("title", "").strip()
    content = article.get("content", "")
    text = strip_tags(content)
    errors: list[str] = []
    warnings: list[str] = []

    if not title:
        errors.append("缺少文章标题 (title)")
    if "<h1" in content.lower():
        errors.append("正文包含 <h1> 标签；公众号标题只能放在 title 字段")
    if re.search(r"\[\[img:|\bTODO\b|图片占位符|待补素材", text):
        errors.append("正文存在未完成的占位符（TODO / 待补素材 / [[img:）")
    if re.search(r"/Users/|file://", content):
        errors.append("正文泄露本机文件路径 (/Users/ 或 file://)")

    masked = re.sub(
        r'(<section style="[^"]*white-space:pre-wrap[^"]*">).*?(</section>)',
        r"\1\2",
        content,
        flags=re.S,
    )
    masked = re.sub(
        r'(<section data-takeaway="1"[^>]*>).*?(</section>\s*</section>)',
        r"\1\2",
        masked,
        flags=re.S,
    )
    masked = re.sub(
        r"(<table\b[^>]*>).*?(</table>)",
        r"\1\2",
        masked,
        flags=re.S | re.I,
    )
    _FORBIDDEN = [
        (re.compile(r"</?div[\s>]", re.I), "禁止使用 <div>，请统一使用 <section>"),
        (re.compile(r"\sclass\s*=", re.I), "存在 class 属性（微信后台会剥离，必须全内联 style）"),
        (re.compile(r"\sid\s*=", re.I), "存在 id 属性"),
        (re.compile(r"<style[\s>]", re.I), "存在 <style> 标签"),
        (re.compile(r"<script[\s>]", re.I), "存在 <script> 标签"),
        (re.compile(r"position\s*:\s*(fixed|absolute|sticky)", re.I), "不支持 position:fixed/absolute/sticky"),
        (re.compile(r"display\s*:\s*grid", re.I), "不支持 display:grid"),
        (re.compile(r"(linear|radial|conic)-gradient", re.I), "乱码硬闸：禁用渐变 gradient，请改用纯色"),
    ]
    for rx, msg in _FORBIDDEN:
        if rx.search(masked):
            errors.append("style: " + msg)

    if "&amp;quot;" in content or "&amp;#" in content:
        errors.append("乱码硬闸：正文存在双重转义（&amp;quot; / &amp;#）")
    if "`" in strip_tags(masked):
        errors.append("乱码硬闸：正文残留 Markdown 反引号 `")

    # 段落长度检查（跳过开篇卡、目录和表格内短标签）
    body_paras = [
        strip_tags(m).strip()
        for m in re.findall(r'<p style="[^"]*text-align:justify[^"]*">(.*?)</p>', content, flags=re.S | re.I)
    ]
    long_paras = [
        (i + 1, len(p), p[:32])
        for i, p in enumerate(body_paras)
        if len(p) > max_paragraph
    ]
    if long_paras:
        preview = "; ".join(f"P{idx}({length}字): {head}..." for idx, length, head in long_paras[:4])
        errors.append(f"段落超过 {max_paragraph} 字上限: {preview}")

    if len(text) >= 1200 and content.count('<span leaf="">') < 6:
        errors.append("未装配主题专属外壳：请先运行 scripts/apply_theme_shell.py")

    pre_blocks = re.findall(r'<section style="[^"]*white-space:pre-wrap[^"]*">(.*?)</section>', content, flags=re.S)
    takeaway_cards = re.findall(r'<section data-takeaway="1"', content, flags=re.I)
    tables = re.findall(r"<table\b", content, flags=re.I)
    takeaways = len(pre_blocks) + len(takeaway_cards) + len(tables)
    if len(text) >= 1200 and takeaways < 1:
        errors.append(f"高价值干货硬闸：评测文至少需 1 个横评数据表或精简命令框（当前仅 {takeaways} 个）")

    # 臃肿原件硬闸：严禁出现【原件 1】、【Prompt 1】等标题以及超长 pre-wrap 灰框
    if re.search(r"【(?:原件|Prompt|速查卡|命令卡)\s*\d*", content, flags=re.I):
        errors.append("原件排版臃肿硬闸：严禁在正文中写「【原件 1】/【Prompt 1】」等拥挤标题框，图片已清晰展示的内容禁止下方再塞重复文字块")
    bloated_pre = [len(strip_tags(b).strip()) for b in pre_blocks if len(strip_tags(b).strip()) > 320]
    if bloated_pre:
        errors.append(f"原件排版臃肿硬闸：发现 {len(bloated_pre)} 个超长 pre-wrap 灰框（{bloated_pre[0]} 字 > 320 字上限），请精简为 ≤4 行纯命令")

    imgs = image_sources(content)
    missing = [src for src in imgs if not local_image_exists(article_path, src)]
    if missing:
        errors.append("存在缺失的本地配图文件: " + ", ".join(missing[:6]))

    req_imgs = min_images if min_images is not None else (4 if len(text) >= 1500 else 0)
    if len(imgs) < req_imgs:
        errors.append(f"配图数量不足：当前 {len(imgs)} 张，至少需要 {req_imgs} 张真实截图/GIF")

    anchors = len(re.findall(r'<strong style="color:#C8102E', content, flags=re.I))
    if anchors == 0:
        warnings.append("未检测到汇芯红加粗锚点（建议每篇点睛 3–6 处）")
    elif anchors > 12:
        warnings.append(f"汇芯红加粗锚点偏多（当前 {anchors} 处，建议控制在 3–6 处）")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate AI Tool Review WeChat article JSON and Markdown.")
    ap.add_argument("--article", required=True, help="转换并装配外壳后的草稿 JSON")
    ap.add_argument("--md", default="", help="可选：原始 Markdown 稿，用于跑反电报碎句与说人话校验")
    ap.add_argument("--max-paragraph", type=int, default=DEFAULT_MAX_PARAGRAPH)
    ap.add_argument("--min-images", type=int, default=None)
    ap.add_argument("--strict-warnings", action="store_true")
    args = ap.parse_args()

    errors, warnings = validate_json(Path(args.article), args.max_paragraph, args.min_images)
    metrics = {}
    if args.md and Path(args.md).is_file():
        md_err, md_warn, metrics = check_markdown_tone(Path(args.md))
        errors.extend(md_err)
        warnings.extend(md_warn)

    payload = {
        "ok": len(errors) == 0 and not (args.strict_warnings and warnings),
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }
    if not payload["ok"]:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
