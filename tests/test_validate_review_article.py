#!/usr/bin/env python3
"""Regression tests for skills/AI工具评测公众号/scripts/validate_review_article.py.

Run from the repo root:
    python3 -m unittest discover -s tests -v

Set VALIDATOR=/path/to/validate_review_article.py to run the same suite
against another copy (e.g. a baseline) for comparison.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "AI工具评测公众号"
VALIDATOR = Path(os.environ.get("VALIDATOR", SKILL / "scripts" / "validate_review_article.py"))
EXAMPLE = SKILL / "examples" / "sample-topic"
EXAMPLE_JSON = EXAMPLE / "article.ticket.example.json"
EXAMPLE_MD = EXAMPLE / "03-review-article.example.md"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "evidence"

BAD = {
    "bad-exposure-as-read": "E2",
    "bad-video-claimed-verified": "E3",
    "bad-package-as-read": "E4",
    "bad-fabricated-io": "E5",
    "bad-thirdparty-recommend": "E6",
    "bad-verbatim-repost": "E7",
}
GOOD = ("good-evidence-discipline", "good-thirdparty-critique")

PRE_BOX_ERROR = "原件排版臃肿硬闸：发现 1 个超长 pre-wrap 灰框（421 字 > 320 字上限），请精简为 ≤4 行纯命令"
PROOF_ERROR = "真跑验货拦截：工程目录缺少完整的 00-real-run-proof.md 真跑回执（禁止无实测纯整理稿推草稿箱）"

CLEAN_ARTICLE = {
    "title": "测试标题",
    "content": '<section><p style="text-align:justify">这是一段很普通的正文，用来确认最小合法草稿可以通过校验。</p></section>',
}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args], capture_output=True, text=True, encoding="utf-8"
    )


def body_section(path: Path) -> str:
    """Only the `## 正文` section of a fixture, so its explanatory footer is not scanned."""
    text = path.read_text(encoding="utf-8")
    body = text.split("## 正文", 1)[1]
    body = re.split(r"(?m)^## ", body, 1)[0]
    return "## 正文\n" + body


class _TmpDir(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        p = self.tmp / name
        p.write_text(text, encoding="utf-8")
        return p

    def clean_article(self) -> Path:
        return self.write("article.json", json.dumps(CLEAN_ARTICLE, ensure_ascii=False))


class ExistingBehaviour(_TmpDir):
    """Behaviour of v1.6.0 that must not change."""

    def test_help_exits_zero(self):
        r = run("--help")
        self.assertEqual(r.returncode, 0)
        for flag in ("--article", "--md", "--max-paragraph", "--min-images", "--strict-warnings", "--skip-proof"):
            self.assertIn(flag, r.stdout)

    def test_example_rejected_for_oversized_command_box(self):
        r = run("--article", str(EXAMPLE_JSON), "--md", str(EXAMPLE_MD), "--max-paragraph", "80", "--skip-proof")
        self.assertEqual(r.returncode, 2, r.stderr)
        out = json.loads(r.stderr)
        self.assertFalse(out["ok"])
        self.assertEqual(out["errors"], [PRE_BOX_ERROR])
        self.assertEqual(out["warnings"], [])

    def test_example_without_proof_adds_proof_error(self):
        r = run("--article", str(EXAMPLE_JSON), "--md", str(EXAMPLE_MD))
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stderr)["errors"], [PRE_BOX_ERROR, PROOF_ERROR])

    def test_proof_shorter_than_120_chars_is_rejected(self):
        md = self.write("03-review.md", "## 正文\n这是一段足够长的正常叙述，用来确认真跑回执检查仍然生效，而不是被别的规则干扰。\n")
        self.write("00-real-run-proof.md", "太短")
        r = run("--article", str(self.clean_article()), "--md", str(md))
        self.assertEqual(r.returncode, 2)
        self.assertIn(PROOF_ERROR, json.loads(r.stderr)["errors"])

    def test_proof_present_passes(self):
        md = self.write("03-review.md", "## 正文\n这是一段足够长的正常叙述，用来确认真跑回执齐全时不会被误拦，校验应当顺利通过。\n")
        self.write("00-real-run-proof.md", "真跑回执：" + "命令、截图、产物路径与耗时记录。" * 12)
        r = run("--article", str(self.clean_article()), "--md", str(md))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"])

    def test_clean_article_passes_and_keeps_old_keys(self):
        r = run("--article", str(self.clean_article()))
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        for key in ("ok", "errors", "warnings", "metrics"):
            self.assertIn(key, out)
        self.assertEqual(out["warnings"], ["未检测到汇芯红加粗锚点（建议每篇点睛 3–6 处）"])

    def test_strict_warnings_still_fails_on_warning(self):
        r = run("--article", str(self.clean_article()), "--strict-warnings")
        self.assertEqual(r.returncode, 2)

    def test_paragraph_limit_and_override(self):
        long_p = "长" * 90
        art = self.write(
            "a.json",
            json.dumps({"title": "t", "content": f'<p style="text-align:justify">{long_p}</p>'}, ensure_ascii=False),
        )
        r = run("--article", str(art))
        self.assertEqual(r.returncode, 2)
        self.assertIn("段落超过 80 字上限", json.loads(r.stderr)["errors"][0])
        self.assertEqual(run("--article", str(art), "--max-paragraph", "100").returncode, 0)

    def test_tone_gates_still_fire(self):
        md = self.write(
            "03-review.md",
            "## 正文\n这一段话里出现了判决两个字，也提到了赋能，属于说人话检查必须拦下来的典型表达。\n",
        )
        r = run("--article", str(self.clean_article()), "--md", str(md), "--skip-proof")
        self.assertEqual(r.returncode, 2)
        errs = json.loads(r.stderr)["errors"]
        self.assertTrue(any("法官腔" in e for e in errs))
        self.assertTrue(any("黑话" in e for e in errs))

    def test_staccato_gate_still_fires(self):
        md = self.write("03-review.md", "## 正文\n很快。\n很稳。\n很好。\n")
        r = run("--article", str(self.clean_article()), "--md", str(md), "--skip-proof")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(any("反电报碎句" in e for e in json.loads(r.stderr)["errors"]))

    def test_layout_gates_still_fire(self):
        art = self.write(
            "a.json",
            json.dumps({"title": "t", "content": '<div class="x" style="background:linear-gradient(red,blue)">x</div>'}),
        )
        errs = json.loads(run("--article", str(art)).stderr)["errors"]
        self.assertTrue(any("<div>" in e for e in errs))
        self.assertTrue(any("class" in e for e in errs))
        self.assertTrue(any("gradient" in e for e in errs))


class UsageAndIO(_TmpDir):
    """Usage errors, missing files and invalid JSON must be distinguishable from a failed article."""

    def assert_usage(self, r: subprocess.CompletedProcess):
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("[USAGE]"), r.stderr[:200])
        self.assertEqual(r.stdout, "")

    def test_no_arguments_is_usage_error(self):
        self.assert_usage(run())

    def test_md_only_is_usage_error_not_a_pass(self):
        md = self.write("03-review.md", "## 正文\n普通正文。\n")
        self.assert_usage(run("--md", str(md)))

    def test_unknown_flag_is_usage_error(self):
        self.assert_usage(run("--article", str(self.clean_article()), "--no-such-flag"))

    def test_missing_article_file(self):
        r = run("--article", str(self.tmp / "nope.json"))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("[IO]"), r.stderr[:200])
        self.assertNotIn("Traceback", r.stderr)

    def test_missing_md_file_is_not_silently_skipped(self):
        r = run("--article", str(self.clean_article()), "--md", str(self.tmp / "nope.md"))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("[IO]"), r.stderr[:200])

    def test_invalid_json(self):
        bad = self.write("bad.json", "{not json")
        r = run("--article", str(bad))
        self.assertEqual(r.returncode, 1)
        self.assertTrue(r.stderr.startswith("[IO]"), r.stderr[:200])
        self.assertNotIn("Traceback", r.stderr)

    def test_failed_article_stderr_is_pure_json_with_status(self):
        r = run("--article", str(EXAMPLE_JSON), "--skip-proof")
        self.assertEqual(r.returncode, 2)
        out = json.loads(r.stderr)
        self.assertEqual(out["status"], "fail")


class EvidenceDefaults(_TmpDir):
    """Evidence checks are advisory by default and must not change the old verdict."""

    def fixture_md(self, name: str) -> Path:
        return self.write("03-review.md", body_section(FIXTURES / f"{name}.md"))

    def evidence(self, name: str, *extra: str) -> tuple[subprocess.CompletedProcess, dict]:
        r = run("--article", str(self.clean_article()), "--md", str(self.fixture_md(name)), "--skip-proof", *extra)
        stream = r.stdout if r.returncode == 0 else r.stderr
        return r, json.loads(stream)

    def test_bad_fixtures_warn_but_do_not_fail_by_default(self):
        for name, rule in BAD.items():
            with self.subTest(name=name):
                r, out = self.evidence(name)
                self.assertEqual(r.returncode, 0, out.get("errors"))
                ids = [k.split("_")[0] for k in out["evidence"]["counts"]]
                self.assertIn(rule, ids)
                self.assertTrue(out["evidence"]["warnings"])
                self.assertFalse(any(w.startswith("证据口径") for w in out["warnings"]))

    def test_bad_fixtures_fail_with_strict_evidence(self):
        for name, rule in BAD.items():
            with self.subTest(name=name):
                r, out = self.evidence(name, "--strict-evidence")
                self.assertEqual(r.returncode, 2)
                self.assertEqual(out["status"], "fail")
                self.assertTrue(any(e.startswith(f"证据口径 {rule}") for e in out["errors"]), out["errors"])

    def test_good_fixtures_pass_strict_evidence(self):
        for name in GOOD:
            with self.subTest(name=name):
                r, out = self.evidence(name, "--strict-evidence")
                self.assertEqual(r.returncode, 0, out.get("errors"))
                self.assertEqual(out["evidence"]["counts"], {})

    def test_strict_warnings_not_triggered_by_evidence(self):
        art = self.write(
            "a.json",
            json.dumps(
                {"title": "t", "content": '<p style="text-align:justify">正文<strong style="color:#C8102E">锚点</strong></p>'},
                ensure_ascii=False,
            ),
        )
        md = self.fixture_md("bad-exposure-as-read")
        r = run("--article", str(art), "--md", str(md), "--skip-proof", "--strict-warnings")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_example_errors_unchanged_by_evidence_layer(self):
        r = run("--article", str(EXAMPLE_JSON), "--md", str(EXAMPLE_MD), "--skip-proof", "--strict-evidence")
        self.assertEqual(json.loads(r.stderr)["errors"], [PRE_BOX_ERROR])

    def test_evidence_only_mode_with_md(self):
        r = run("--md", str(self.fixture_md("bad-fabricated-io")), "--evidence-only")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["evidence"]["scope"], "evidence-only")
        self.assertIn("E5_伪造I_O", out["evidence"]["counts"])

    def test_evidence_only_does_not_claim_layout_or_proof_pass(self):
        r = run("--md", str(self.fixture_md("good-evidence-discipline")), "--evidence-only")
        out = json.loads(r.stdout)
        self.assertEqual(out["evidence"]["scope"], "evidence-only")
        self.assertEqual(out["metrics"], {})

    def test_evidence_scans_json_text_when_no_md(self):
        art = self.write(
            "a.json",
            json.dumps({"title": "t", "content": "<p>这条帖有 96 万阅读，打开率大概 1.7%。</p>"}, ensure_ascii=False),
        )
        out = json.loads(run("--article", str(art)).stdout)
        self.assertIn("E2_曝光当阅读", out["evidence"]["counts"])


class EvidenceFalsePositives(_TmpDir):
    """Known limits of string matching: these document behaviour, they do not certify truth."""

    def counts(self, body: str) -> dict:
        md = self.write("03-review.md", "## 正文\n" + body + "\n")
        r = run("--md", str(md), "--evidence-only")
        return json.loads(r.stdout)["evidence"]["counts"]

    def test_negated_video_claim_with_disclosure_is_clean(self):
        self.assertEqual(self.counts("口型和运镜我没法判断，本次没有视频，视频效果未验证。"), {})

    def test_risk_disclaimer_suppresses_e6(self):
        self.assertEqual(self.counts("有人在卖邀请码，价格与可用性本席未核，不构成推荐。"), {})

    def test_short_quote_with_url_is_clean(self):
        self.assertEqual(self.counts("> 先把工序拆开。https://x.com/example/status/1\n\n这句话的意思是先拆再配。"), {})

    def test_reading_time_is_not_exposure(self):
        self.assertEqual(self.counts("全文大约 8 分钟读完，建议收藏后慢慢看。"), {})

    def test_labeled_counterexample_still_warns(self):
        # Quoting a bad phrase as a labeled counter-example is still matched; this is advisory only.
        self.assertIn("E2_曝光当阅读", self.counts("反例：不要写「96 万阅读」，要写本帖曝光。"))

    def test_fake_io_pattern_only_flags_presence(self):
        # E5 cannot tell a real terminal line from an invented one; both are flagged for human comparison.
        self.assertIn("E5_伪造I_O", self.counts("终端返回：`ok`，与 00-real-run-proof.md 第 3 行一致。"))


if __name__ == "__main__":
    unittest.main()
