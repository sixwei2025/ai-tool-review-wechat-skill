<div align="center">

<img src="assets/showcase/hero-banner.jpg" alt="AI 工具评测公众号 Skill 2.0 — 真跑压测 + 高价值原件 + 汇芯红六套骨架全自动推草稿箱" width="100%" />

# AI 工具评测公众号全自动 Skill（2.0 重构版）
### `ai-tool-review-wechat-skill` · 双水源评测雷达 → 本机沙盒真跑 → 五幕高密度成稿 → 反电报碎句硬闸 → 汇芯红六套骨架直推 2号/主号草稿箱

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-v2.0%20Autopilot-C8102E?style=flat-square)](https://agentskills.io)
[![Workflow](https://img.shields.io/badge/Workflow-6%20Auto%20Stages%20·%204%20Core%20Scripts-18181B?style=flat-square)](#二20-六步全自动评测流水线)
[![Quality](https://img.shields.io/badge/Hard%20Gates-反电报碎句%20+%20原件块≥2%20+%20零法官腔-B45309?style=flat-square)](#三20-四大重构升级砍掉繁琐填表全面脚本硬闸化)
[![License](https://img.shields.io/badge/License-MIT-059669?style=flat-square)](LICENSE)

> 🔴 **作者：袁六伟 · 台州汇芯**｜一人 AI 公司创始人，学员 6000+，服务企业客户 100+，得到 / 华为分享老师  
> 📮 更多 AI 模型、Skill 实测与一人公司实战，关注 **公众号 / 视频号：袁六伟**

**「替老板、创作者和开发者花真金白银踩坑，算清 ROI，直接给能抄走的结论和配置原件。」**  
这不是把厂商通稿洗一遍的提示词模板，而是一套**本机真跑压测 + 代码级硬闸拦截 + 汇芯红 `#C8102E` 六套手机排版骨架**的一体化评测工程体系。默认投递 **2号（`hao2`）**，支持一键切换 **主号（`main`）**，只进草稿箱预览，绝不自动群发。

```bash
# 一键安装 Skill
npx skills add sixwei2025/ai-tool-review-wechat-skill
```

[为什么重做 2.0](#一为什么重做-20旧版评测号的-4-大病根与彻底纠偏) · [六步全自动流水线](#二20-六步全自动评测流水线) · [四大评测赛道与模板](#三四大评测赛道与五幕高密度模板) · [汇芯红六套排版骨架](#四视觉交付汇芯红六套排版骨架按题材直选) · [脚本用法与目录](#五自动化脚本与仓库全景目录)

</div>

---

## 一、为什么重做 2.0？（旧版评测号的 4 大病根与彻底纠偏）

| 旧版痛点（1.0 已废弃） | 2.0 全自动硬核方案（现行标准） |
| :--- | :--- |
| ❌ **四道人工拍板闸 + 手填一页纸/自评表**，把 Agent 变成填表文员 | ✅ **一句话跑通全链路**：用 `validate_review_article.py` 代码级硬闸替代虚假的大模型打分 |
| ❌ **强制「一句一段」**，导致满篇 5–10 字电报碎句，阅读廉价感极重 | ✅ **2–3 行自然呼吸短段（35–60 字，上限 ≤80 字）**，连续 3 段 ≤15 字碎句直接报错拦截 |
| ❌ **依赖「洗稿三步」**，必须等别人先写出爆款才能跟风改写 | ✅ **内置四大评测赛道沙盒压测题库（Benchmark）**，本机终端/浏览器真跑拿一手截图与 GIF |
| ❌ **转换脚本只支持单一骨架**，其它五套骨架需手工拼 HTML | ✅ **`apply_theme_shell.py` 全量支持六套汇芯红骨架自动注入**（含原生 Markdown 斑马纹表格渲染） |

---

## 二、2.0 六步全自动评测流水线

<p align="center">
  <img src="assets/showcase/pipeline-architecture.jpg" alt="AI 工具评测公众号全自动工作流架构图" width="100%" />
</p>

| 步骤 | 环节 | 执行动作与关联模块 | 交付物与代码级硬闸 |
| :---: | :--- | :--- | :--- |
| **01** | **双水源评测雷达** | 扫 `zsxq-cli` 社群真实痛点 + `aihot` 24h 首发模型/高星 Skill | 产出 3 个实测方向 + 6 个高张力标题候选 |
| **02** | **沙盒真跑与核价** | 按 `01-benchmark-and-matrix.md` 跑 3–4 道真题；查官网价格并标日期 | 产出 8–12 张红框实操截图卡 + 1–3 张 `ffmpeg` 对比 GIF |
| **03** | **五幕高密度写稿** | 按 `02-article-structures.md` 四大模板写正文（段均 40–60 字） | **硬闸**：≥2 个可复制原件块（Prompt/配置/算账表）+ 至少 1 处真实翻车 |
| **04** | **汇芯红骨架装配** | `markdown_to_wechat_article.py` + `apply_theme_shell.py` | 按题材自动装配 `ticket` / `magazine-card` / `classic-edit` 等六套外壳 |
| **05** | **一体化硬闸校验** | 运行 `validate_review_article.py` + 375px 手机实屏预览 | **硬闸**：零 `<div>`/`class`/`gradient`、零电报碎句、零法官腔、翻案句 ≤2 |
| **06** | **双账号推草稿箱** | 运行 `publish_review_draft.py --account hao2\|main` | 自动上传图片换微信 CDN URL、返回 `media_id`（只存草稿不群发） |

---

## 三、四大评测赛道与五幕高密度模板

### 3.1 测什么？（四大核心赛道压测标尺）
1. **基座与推理/编程大模型（Claude / GPT / Gemini / DeepSeek / Qwen）**：测去 AI 味中文商业改写、400+ 行单页应用一次点亮率、长文档大海捞针幻觉率、首字延迟与百次调用真实 API 账单。
2. **Agent Skills、MCP 与工作流插件（核心护城河）**：测从零安装与鉴权摩擦耗时、端到端业务闭环交付度、连跑 10 次抗崩率、对比人工手搓省下的时间。
3. **多模态生成（图像 / 视频 / 语音克隆）**：测中文海报排版准确率、多图角色一致性、大动态运镜废片率、中英混读机械感。
4. **AI IDE 与智能体宿主（Claude Code / Antigravity / Cursor / WorkBuddy）**：测跨文件重构成功率与浏览器接管边界。

### 3.2 怎么写？（五幕结构 + 至少 2 个可带走原件）
- **专属开篇卡**：划掉一句市场盲目吹捧的旧认知，用红黑大字亮出反差结论（严守开篇卡、目录、首章标题、首段去重硬闸）。
- **第 1 幕 · 现场立靶与结论先行**：前 2 段必见真实痛点或首屏《胜负总表》+ 第一张实拍 GIF/大图。
- **第 2 幕 · 亮出公共考卷（原件块 ①）**：直接贴出测试用的 **完整 Prompt 原文 / 终端命令代码块**，读者复制即可复现。
- **第 3 幕 · 惊艳高光 vs 翻车抓包**：并排展示真实输出截图，红框标出它哪里封神、哪里偷偷删代码或死循环报错。
- **第 4 幕 · 真金白银算账与选型路由（原件块 ②）**：给出官网价格（标查询日期）与带 `✓ 闭眼入` / `✗ 劝退` 的分级配置单。
- **第 5 幕 · 尾件分流**：**2号（`hao2`）** 走纯净公域破万尾件（END + 三连引导）；**主号（`main`）** 加挂无二维码红金产品海报。

---

## 四、视觉交付：汇芯红六套排版骨架（按题材直选）

废除旧版“按星期一到星期六轮换”，改为**按评测内容结构直接匹配最合适的汇芯红 `#C8102E` 骨架**：

<p align="center">
  <img src="assets/showcase/00-themes-six.jpg" alt="汇芯红六套排版骨架总览" width="100%" />
</p>

| 骨架 ID (`--theme`) | 中文名 | 最佳评测场景 | 开篇标志性组件 |
| :--- | :--- | :--- | :--- |
| **`ticket`** | 汇芯红·票据 | **单品深度实测 / 首发快刀斩 / 避坑打假** | 米黄纸感门票凭证（星级 + 编号 + S/A/B/C 等级 + 撕票线） |
| **`magazine-card`** | 汇芯红·杂志卡 | **多模型/多工具同题横评 / 榜单盘点** | 杂志快讯封面（划掉旧认知 + 红黑大字）+ 横向滑动目录 |
| **`classic-edit`** | 汇芯红·经典编辑 | **Agent Skill / MCP 深扒 / 重度实操教程** | 白底红光晕引言卡 + 三列看点短标（3–6字）+ 红底编号章节 |
| **`journal`** | 汇芯红·内刊手记 | **工作流复盘 / 团队长周期落地算账** | 内刊头图卡 + PART 竖线章节 + 精简对照表 |
| **`minimal-line`** | 汇芯红·极简细线 | **极客短评 / 技术边界犀利剖析** | 上下细线金句 + 48px 超大水印数字章节（红点睛 ≤3 处） |
| **`zen-space`** | 汇芯红·禅意留白 | **AI 行业深度随笔** | 衬线大字居中金句 + 极简目录 |

---

## 五、自动化脚本与仓库全景目录

### 5.1 三条命令跑通「转换 → 装配外壳 → 硬闸校验 → 推箱」

```bash
# 1. Markdown 转微信内联 HTML 草稿 JSON（自动渲染斑马纹表格与代码块）
python3 skills/AI工具评测公众号/scripts/markdown_to_wechat_article.py \
  --md skills/AI工具评测公众号/examples/sample-topic/03-review-article.example.md \
  --title "花 260 元连测 3 款主流编程 AI，我把呼声最高的那个退订了" \
  --theme ticket --out /tmp/article.base.json

# 2. 注入主题专属开篇封面、目录短标、编号章节头与 END 尾件
python3 skills/AI工具评测公众号/scripts/apply_theme_shell.py \
  --article /tmp/article.base.json --theme ticket \
  --eyebrow "AI CODING BENCHMARK" --strike "跑分第一就等于写代码最强" \
  --cover-black "连测3款编程AI" --cover-red1 "最火的那个" --cover-red2 "被我当场退订了" \
  --cover-meta "3轮真实工程压测 · 4张实拍对比 · 2份可抄配置单" \
  --grade "A" --issue-no "042" --parts-short "省流总表|压测考卷|翻车抓包|终极站队" \
  --out /tmp/article.final.json

# 3. 跑一体化硬闸校验（排版兼容 + 反电报碎句 + 原件块≥2 + 说人话禁词）
python3 skills/AI工具评测公众号/scripts/validate_review_article.py \
  --article /tmp/article.final.json \
  --md skills/AI工具评测公众号/examples/sample-topic/03-review-article.example.md
```

### 5.2 仓库目录结构

```text
ai-tool-review-wechat-skill/
├── README.md                                        # 仓库总览与 2.0 架构说明
├── LICENSE                                          # MIT 开源许可
├── assets/showcase/                                 # 汇芯红六套骨架预览与成稿切片
└── skills/AI工具评测公众号/
    ├── SKILL.md                                     # 【总控入口】六步全自动流水线与四个唤醒口令
    ├── references/                                  # 【4 份高密度规范】
    │   ├── 01-benchmark-and-matrix.md               # 对标账号矩阵、双水源雷达与四大评测赛道压测题库
    │   ├── 02-article-structures.md                 # 五个一票否决、四大实战模板、标题公式与 2号/主号尾件分流
    │   ├── 03-visual-and-media-policy.md            # 实操截图卡七要素、ffmpeg 高清 GIF 与黑红金封面规范
    │   └── 04-tone-and-safety-gates.md              # 反电报碎句、说人话禁词表、内外表达分界与技术类比库
    ├── scripts/                                     # 【全自动可执行工程脚本】
    │   ├── markdown_to_wechat_article.py            # Markdown → 汇芯红六套骨架 JSON 转换器
    │   ├── apply_theme_shell.py                     # 全六套主题专属开篇卡/目录/章节头/END 装配器
    │   ├── validate_review_article.py               # 排版 + 反碎句 + 原件块 + 说人话一体化硬闸校验器
    │   └── publish_review_draft.py                  # 默认 2号(hao2) / 支持主号(main) 草稿箱 SSH 投递器
    ├── templates/                                   # 选题与压测方案卡 / 实测取证核价台账模板
    ├── examples/sample-topic/                       # 2.0 完整评测样稿与通过硬闸的 ticket JSON 成品
    └── themes/                                      # 汇芯红 #C8102E 六套手机排版骨架组件库
```
