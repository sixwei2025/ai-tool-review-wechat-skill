# 更新日志

## v1.2.0 · 2026-11-13

- **X（Twitter）一手评测水源正式接入工作流**：新增 `references/06-twitter-x-sourcing.md`，内置四类必盯海外与中文 AI 大V信源清单、X 高效检索语法与原帖截图 / Demo 视频转 GIF 规范。
- **三水源评测雷达升级**：`SKILL.md` 第 1 步升级为「社群痛点 + 24h 资讯 + X/Twitter 一手热帖」，第 2 步新增 X 原帖与 Demo 动图取证要求，`03-visual-and-media-policy.md` 同步纳入 X 素材标准。
- **兼容说明**：保持原有 CLI 调用参数与目录结构 100% 向后兼容。

## v1.1.0 · 2026-11-13

- **头部 20 家 AI 评测公众号拆解矩阵**：扩充 `01-benchmark-and-matrix.md` 为四大流派 20 家头部账号对标体系。
- **评测写作七大原则**：确立「一手心得细节 / 必须带对比 / 具体言之有物 / 动图与海外截图强可视化 / 结论先行 / 10 秒听懂人话类比 / 必留可抄原件」。
- **吸收 `khazix-writer` 活人感写作技法**：新增 `references/05-human-writing-craft.md`（保留原作者 `KKKKhazix/khazix-skills` 致谢），融入 HKR 质检、人机边界、升番逻辑与契诃夫之枪。
- **全量黑话与 AI 暴露词自动拦截**：升级 `validate_review_article.py`，自动拦截大厂黑话、AI 口头禅、`khazix-writer` 高危 AI 暴露词及内部机械词。
- **尾件防重与业务海报自动挂载**：修复 `apply_theme_shell.py` 重复三连问题，2 号（`hao2`）与主号（`main`）统一挂载无二维码《袁六伟 · 一人AI公司》业务海报；修复 `publish_review_draft.py` 自动加载环境变量与 `assets/` 路径兼容。
- **兼容说明**：保持原有 CLI 调用参数与目录结构 100% 向后兼容。

## v1.0.0 · 2026-11-13

- 建立可追踪的版本记录，README、Skill 文件和 Git 标签保持一致。
- 后续功能变化、修复和兼容性调整会持续记录在本文件。

