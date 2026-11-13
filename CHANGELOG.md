# 更新日志

## v1.2.3 · 2026-11-13

- **新增汇芯精选高信号信源库**：在 `references/06-twitter-x-sourcing.md` 纳入 94 个登记 X 账号的核心高信号子集（中文 AI 实操与工具、一人公司创业与变现、海外一手方法与技术动向、AI 视频视觉与开源发现四大类），并补齐海外博客（Every / Lenny / One Useful Thing / Latent Space）、中文头部公众号与 AIHOT 辅助信源。
- **明确线索溯源与小红书边界**：确立「所有信源只提供线索、不直接照搬，选中后必须回原始发布/开源项目/本机亲手实测；小红书仅补充用户指定链接、不做全站自动采集」采编铁律。
- **兼容说明**：保持原有 CLI 调用参数与目录结构 100% 向后兼容。

## v1.2.2 · 2026-11-13

- **新增 X（Twitter）防风控四条红线**：在 `references/06-twitter-x-sourcing.md` 明确小号 Cookie 隔离、单次 `limit ≤ 15`、固定 IP 与手动截图兜底策略。
- **新增「快节奏 · 情绪张力 · 多图少字 · 信息增量」写作标尺**：在 `references/02-article-structures.md` 确立 1000–1600 字高密度短篇 + 8–12 张真图/GIF（每 120–150 字一图）的手机端快刷标准。

## v1.2.1 · 2026-11-13

- **新增 X（Twitter）一键抓取脚本**：新增 `scripts/fetch_x_evidence.py`（基于开源 `vladkens/twscrape`，MIT 许可），支持通过浏览器 Cookie 免官方 API Key 搜索 X 高赞推文、下载高清原图，并将推文中的 Demo 视频自动切片为 `≤3MB` 高清 GIF。
- **文档更新**：同步更新 `references/06-twitter-x-sourcing.md` 与 `SKILL.md`。

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

