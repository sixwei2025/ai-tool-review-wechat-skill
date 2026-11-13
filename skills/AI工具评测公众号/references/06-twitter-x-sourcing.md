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

## 四、一键自动化抓取脚本（`scripts/fetch_x_evidence.py`，基于 `vladkens/twscrape`）

本 Skill 已内置 `scripts/fetch_x_evidence.py`（依赖本机已预装的 `/opt/homebrew/bin/twscrape` 与 `ffmpeg`），免买官方高价 API Key，可直接拉取 X 推文正文、配图并把 Demo 视频自动切为 `≤3MB` 微信高清 GIF：

```bash
# 首次使用：从已登录 x.com 的 Chrome 复制 auth_token 与 ct0 绑定
/opt/homebrew/bin/python3.11 skills/AI工具评测公众号/scripts/fetch_x_evidence.py \
  --add-cookie "my_x" "auth_token=xxx; ct0=yyy"

# 日常抓图 + Demo 视频自动转 GIF
/opt/homebrew/bin/python3.11 skills/AI工具评测公众号/scripts/fetch_x_evidence.py \
  --query '"Gemini 4 Hydrogen" min_faves:20' --limit 15 --gif --out ./assets/x
```

---

## 五、X（Twitter）风控评估与防封四条红线

按每天写 1–2 篇的频率，单次拉 10–15 条属于极低频的个人阅读级请求，正常不容易触发批量爬虫封号；但为了绝对稳妥，必须守住以下四条红线：
1. **绝对不用主号 Cookie，专配 1–2 个小号**：`twscrape` 走非官方 GraphQL 接口，只用小号 Cookie 跑抓取，保证主号与日常刷推零风险。
2. **单次 `--limit` 压在 `10–15` 条以内**：严禁跑 `--limit 100` 或高频定时轮询，按需“写一篇拉一次”。
3. **代理 IP 保持固定，不频繁切国家节点**：同一 Cookie 短时间跨区跳 IP 最容易触发异常登录风控弹窗。
4. **手动刷推截图随时兜底**：平时手动刷 X 顺手截的图或录的 3 秒屏直接丢进 `assets/`，脚本无缝接管排版推箱。
