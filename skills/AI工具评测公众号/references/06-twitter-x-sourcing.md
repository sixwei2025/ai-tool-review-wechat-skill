# 06 · X（Twitter）一手评测素材与 Demo 动图抓取规范

> 核心洞察：头部评测号（如数字生命卡兹克、歸藏、宝玉）之所以能做到“首发几小时出深度稿且配图极丰富”，核心原因之一就是把 **X（Twitter）** 作为第一上游水源，专门抓海外官方 Thread、真实开发者实测视频（转 GIF）和第三方榜单对比图。

---

## 一、X（Twitter）四类必盯信源清单

每次评测新模型、新 Skill 或 AI 编程工具时，优先检索以下四类账号：

| 信源类型 | 代表账号（`@handle`） | 主要拿什么素材 |
| :--- | :--- | :--- |
| **1. 官方发布与核心团队** | `@GoogleDeepMind`、`@AnthropicAI`、`@OpenAI`、`@xai`、`@deepseek_ai`、`@Alibaba_Qwen` | 官方公告 Thread、首发对比柱状图、官方 Demo 视频 |
| **2. 独立第三方客观榜单** | `@ArtificialAnlys`、`@lmarena_ai`、`@vals_ai` | 价格 vs 智能度散点图、盲测胜率排行、响应速度实测表 |
| **3. 海外一线开发者与 CEO** | `@simonw`、`@levie`、`@karpathy`、`@swyx`、`@emollick` | 真实工程踩边界案例、工具调用自愈率数据、Token 真实账单 |
| **4. 中文 AI 圈一手实测大V** | `@op7418`（归藏）、`@dotey`（宝玉）、`@xiaohu`（小互） | 中文提示词实测对比图、开源 Skill 玩法、国内可用性反馈 |

---

## 二、X 高效检索语法（直接复制进 X 搜索框）

1. **找高赞对比与 Demo 视频**：
   ```text
   "Gemini 4 Hydrogen" (demo OR benchmark OR vs OR pricing) min_faves:50
   ```
2. **只看独立榜单与核心大V的评价**：
   ```text
   "Gemini 4 Hydrogen" (from:ArtificialAnlys OR from:simonw OR from:levie OR from:op7418 OR from:dotey)
   ```
3. **找真实吐槽与边界案例**：
   ```text
   "Gemini 4 Hydrogen" (failed OR bug OR better than OR replaced Claude) min_faves:20
   ```

---

## 三、X 素材进正文的四条操作规范

1. **优先复用本机已登录 Chrome 会话**：普通无头浏览器访问 `x.com` 会撞登录墙；直接用本机已登录 X 账号的浏览器打开目标推文，才能完整加载原帖、高清配图与评论区实测图。
2. **遇到 Demo 视频直接切 GIF**：看到大V发的一手生成视频或操作录屏，保存或录屏 3–5 秒高光片段，用 `ffmpeg` 压成 `≤3MB` 的高清 GIF 插进正文，说服力远超静态图。
3. **裁掉浏览器噪音、保留作者 `@handle`**：截取推文卡片时，裁掉左侧边栏和右侧热搜推荐，保留发帖人头像、`@handle`、时间戳和核心文字/图表。
4. **严格区分「自己测的」和「X 平台引用」**：自己没跑过的测试不能冒充亲测；引用 X 素材时必须写明来源（例如「海外 X 平台上 Box CEO Aaron Levie 晒出的实测数据显示……」），真诚第一。
