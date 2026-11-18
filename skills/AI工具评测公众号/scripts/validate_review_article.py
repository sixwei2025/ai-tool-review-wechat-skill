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

证据口径检查（E1–E7，字符串匹配，只提示「疑似」，不判断事实真伪）：
  默认只写入输出 JSON 的 `evidence` 字段，不进入 errors / warnings，不改变上面五道硬闸的结论；
  `--strict-evidence` 时升级为 errors；`--evidence-only --md 03-review.md` 只跑证据层（不代表排版与真跑回执已通过）。

退出码：
  0  通过（stdout 为 JSON，"status": "pass"）
  1  输入文件不存在或 JSON 无法解析（stderr 首行 `[IO]`）
  2  参数用错，未做任何校验（stderr 首行 `[USAGE]`）
  2  校验跑完但未通过（stderr 为 JSON，"status": "fail"）
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
BANNED_JARGON = (
    "赋能", "抓手", "闭环", "底层逻辑", "顶层设计", "颗粒度", "生态位", "降本增效", "组合拳", "全链路",
    "不得不说", "值得一提的是", "总而言之", "综上所述", "各有千秋", "见仁见智",
    "说白了", "意味着什么", "这意味着", "本质上", "换句话说", "不可否认",
    "硬闸", "门闸", "机械硬闸",
)


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

    # 3. 喊麦/绝对化违禁词 + 大厂黑话/AI口头禅/机械黑话
    hype_hits = [w for w in BANNED_HYPE if w in no_code]
    if hype_hits:
        errors.append(f"合规校验：命中夸张/绝对化禁用词：{', '.join(hype_hits)}")
    jargon_hits = [w for w in BANNED_JARGON if w in no_code]
    if jargon_hits:
        errors.append(f"说人话校验：命中大厂黑话/AI口头禅/内部机械词：{', '.join(jargon_hits)}")

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


# 证据口径规则：只匹配字面形态，命中即「疑似」，真伪与语境由人对照 00-real-run-proof.md 与原始材料判断。
# 合规提示（OK cues）只在命中所在的同一段（Markdown 一行）内生效；别处的交代不会抵消这一段的宣称。
# 同段带「反例 / 不要写成」等标签、且命中落在引号内的，记为示例（evidence.examples），不计入 counts。
_EVIDENCE_PATTERNS = {
    "E1_曝光标口径": re.compile(r"\d[\d,\.]*\s*(?:万|亿|k|K)?\s*次?\s*曝光"),
    "E2_曝光当阅读": re.compile(
        r"(?:\d[\d,\.]*)\s*(?:万|亿|k|K)?\s*(?:阅读量|阅读数|阅读|打开率|完读率)"
        r"|(?:阅读量|阅读数|打开率|完读率)[^。\n]{0,12}?\d"
    ),
    "E3_视频宣称": re.compile(r"(?:口型|运镜|字幕对齐|动作衔接|画面流畅|看完视频|逐个看完)"),
    "E4_未取得资产当已读": re.compile(
        r"(?:扫码包|资料包|课件|开箱库|网盘|评论区链接)[^。\n]{0,20}?(?:都看过了|已读|全部看完|照着填就行)"
        r"|(?:看过了|已读|看完)\s*(?:扫码包|资料包|课件|开箱库)"
    ),
    "E5_伪造I_O": re.compile(r"(?:终端返回|控制台返回|命令行返回|回显)[：:]\s*[`\"「]?[^\n`\"」]{2,}"),
    "E6_第三方交易推荐": re.compile(r"(?:邀请码|代注册|中转站|中转|白嫖|签到送|一元起|1\.88)"),
}

_EVIDENCE_OK_CUES = {
    "E1_曝光标口径": ("本节曝光", "本帖曝光", "API 曝光", "该帖曝光", "曝光不是阅读", "不是正文阅读"),
    "E3_视频宣称": ("视频效果未验证", "未看视频", "视频未看", "没看视频"),
    "E4_未取得资产当已读": ("未取得", "没有取得", "未拿到", "不能写成已读", "未读"),
    "E6_第三方交易推荐": ("风险", "不建议", "不构成推荐", "未核", "未验证", "对不上", "落差", "不作为实操范本"),
}

_EVIDENCE_MESSAGES = {
    "E1_曝光标口径": "证据口径 E1：出现曝光数字（命中：{sample}），请标明它是本帖 API 曝光，不是正文阅读量。",
    "E2_曝光当阅读": "证据口径 E2：疑似把曝光当阅读 / 反推打开率；命中：{sample}",
    "E3_视频宣称": "证据口径 E3：出现「{sample}」类视频效果描述，同段未见「视频效果未验证」。未看视频不得写成已验证。",
    "E4_未取得资产当已读": "证据口径 E4：疑似把未取得的包 / 课件写成已读；命中：{sample}",
    "E5_伪造I_O": "证据口径 E5：正文出现「终端返回 / 回显」式输出行（{count} 处），须与 00-real-run-proof.md 的回执逐行对得上；这只是提示信号，不能证明真跑。",
    "E6_第三方交易推荐": "证据口径 E6：正文提到「{sample}」等第三方获取路径，同段未见风险提示。请补一句价格与可用性未核、不构成推荐；提到中转本身不算违规。",
}

_EXAMPLE_LABELS = ("反例", "错误写法", "错误示范", "不要写", "别写", "不得写", "禁止写", "不能写")
_QUOTE_SPAN = re.compile(r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|\"[^\"\n]*\"")

QUOTE_MIN_CHARS = 120
QUOTE_HARD_CHARS = 300


def evidence_corpus(text: str) -> str:
    if "## 正文" in text:
        text = text.split("## 正文", 1)[1]
    return text


def _rule_hits(rule: str, paragraphs: list[str]) -> tuple[list[str], list[str]]:
    """返回（计数命中, 标注示例命中）；合规提示与反例标签都只看命中所在段。"""
    hits: list[str] = []
    examples: list[str] = []
    for para in paragraphs:
        matches = list(_EVIDENCE_PATTERNS[rule].finditer(para))
        if not matches or any(c in para for c in _EVIDENCE_OK_CUES.get(rule, ())):
            continue
        labeled = any(label in para for label in _EXAMPLE_LABELS)
        spans = [q.span() for q in _QUOTE_SPAN.finditer(para)] if labeled else []
        for m in matches:
            in_quote = any(s <= m.start() < e for s, e in spans)
            (examples if in_quote else hits).append(m.group(0))
    return hits, examples


def check_quotes(body: str) -> list[str]:
    """E7：连续引用块超过 120 字且块内无来源 url。"""
    out: list[str] = []
    for block in re.findall(r"(?m)^(?:>.*(?:\n|$))+", body):
        quoted = re.sub(r"(?m)^>\s?", "", block).strip()
        if len(quoted) < QUOTE_MIN_CHARS or re.search(r"https?://", quoted):
            continue
        level = f"超过 {QUOTE_HARD_CHARS} 字，公开稿不应出现" if len(quoted) > QUOTE_HARD_CHARS else f"超过 {QUOTE_MIN_CHARS} 字"
        out.append(f"证据口径 E7：连续引用块 {len(quoted)} 字且未见来源 url（{level}）；公开稿只允许必要一句 + 来源 + 自己的解读。")
    return out


def check_evidence(text: str) -> tuple[dict[str, int], list[str], dict[str, int]]:
    body = evidence_corpus(text)
    paragraphs = [re.sub(r"\s+", " ", line).strip() for line in body.splitlines() if line.strip()]
    counts: dict[str, int] = {}
    messages: list[str] = []
    examples: dict[str, int] = {}
    for rule in _EVIDENCE_PATTERNS:
        hits, labeled = _rule_hits(rule, paragraphs)
        if labeled:
            examples[rule] = len(labeled)
        if not hits:
            continue
        counts[rule] = len(hits)
        sample = "、".join(list(dict.fromkeys(hits))[:3])
        messages.append(_EVIDENCE_MESSAGES[rule].format(sample=sample, count=len(hits)))
    quote_msgs = check_quotes(body)
    if quote_msgs:
        counts["E7_他人全文搬运"] = len(quote_msgs)
        messages.extend(quote_msgs)
    return counts, messages, examples


class _UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        sys.stderr.write(f"[USAGE] {message}\n")
        self.print_usage(sys.stderr)
        raise SystemExit(2)


def _io_fail(message: str) -> int:
    print(f"[IO] {message}", file=sys.stderr)
    return 1


def main() -> int:
    ap = _UsageParser(description="Validate AI Tool Review WeChat article JSON and Markdown.")
    ap.add_argument("--article", default="", help="转换并装配外壳后的草稿 JSON（除 --evidence-only 外必填）")
    ap.add_argument("--md", default="", help="可选：原始 Markdown 稿，用于跑反电报碎句与说人话校验")
    ap.add_argument("--max-paragraph", type=int, default=DEFAULT_MAX_PARAGRAPH)
    ap.add_argument("--min-images", type=int, default=None)
    ap.add_argument("--strict-warnings", action="store_true")
    ap.add_argument("--skip-proof", action="store_true", help="跳过 00-real-run-proof.md 真跑回执检查")
    ap.add_argument(
        "--strict-evidence", action="store_true", help="证据口径 E1–E7 命中时计入 errors（默认只写入 evidence 字段）"
    )
    ap.add_argument(
        "--evidence-only",
        action="store_true",
        help="只跑证据口径检查（需 --md 或 --article）；不跑排版、说人话与真跑回执检查，结果不代表这些已通过",
    )
    args = ap.parse_args()

    if not args.article and not (args.evidence_only and args.md):
        ap.error("--article is required (only --evidence-only may run on --md alone)")
    if args.article and not Path(args.article).is_file():
        return _io_fail(f"--article 文件不存在：{args.article}")
    if args.md and not Path(args.md).is_file():
        return _io_fail(f"--md 文件不存在：{args.md}")
    article_text = ""
    if args.article:
        try:
            content = json.loads(Path(args.article).read_text(encoding="utf-8")).get("content", "")
            article_text = strip_tags(re.sub(r"</p>|</section>|<br\s*/?>", "\n", content, flags=re.I))
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as exc:
            return _io_fail(f"--article 不是有效的草稿 JSON：{exc}")

    errors: list[str] = []
    warnings: list[str] = []
    metrics = {}
    if not args.evidence_only:
        errors, warnings = validate_json(Path(args.article), args.max_paragraph, args.min_images)
        if args.md:
            md_path = Path(args.md)
            md_err, md_warn, metrics = check_markdown_tone(md_path)
            errors.extend(md_err)
            warnings.extend(md_warn)
            if not args.skip_proof:
                proof_path = md_path.parent / "00-real-run-proof.md"
                if not proof_path.is_file() or len(proof_path.read_text(encoding="utf-8").strip()) < 120:
                    errors.append(
                        "真跑验货拦截：工程目录缺少完整的 00-real-run-proof.md 真跑回执（禁止无实测纯整理稿推草稿箱）"
                    )

    corpus = Path(args.md).read_text(encoding="utf-8") if args.md else article_text
    ev_counts, ev_messages, ev_examples = check_evidence(corpus)
    if args.strict_evidence:
        errors.extend(ev_messages)

    ok = len(errors) == 0 and not (args.strict_warnings and warnings)
    payload = {
        "ok": ok,
        "status": "pass" if ok else "fail",
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
        "evidence": {
            "scope": "evidence-only" if args.evidence_only else "full",
            "source": "md" if args.md else "article",
            "strict": bool(args.strict_evidence),
            "counts": ev_counts,
            "warnings": ev_messages,
            "examples": ev_examples,
        },
    }
    if not payload["ok"]:
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
