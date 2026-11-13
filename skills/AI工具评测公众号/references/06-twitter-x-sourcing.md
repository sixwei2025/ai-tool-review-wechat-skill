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

---

## 六、汇芯精选高信号信源库（X + 海外博客 + 公众号 + AIHOT）

> **采编铁律**：平时主要从 **X、海外博客与官方公告、中文公众号、AIHOT** 四路找选题；小红书**只补充用户发来的指定链接**，不做全站自动采集。现有清单登记了 **94 个 X 账号**，不每天全量扫，按当次选题定向拉取下面最相关的高信号子集。**所有账号只提供线索，绝不直接照搬——选中后必须回到原始官方发布、开源仓库或本机亲手实测，再转成自己的原创评测。**

### 1. X（Twitter）核心高信号矩阵

| 分类 | 核心账号清单（`@handle`） | 重点盯什么线索 |
| :--- | :--- | :--- |
| **中文 AI 实操与工具** | 宝玉 `@dotey`、歸藏 `@op7418`、向阳乔木 `@vista8`、花叔 `@AlchainHust`、Vincent `@Vincent_AINotes`、逸尘 `@gengdaJ`、meng shao `@shao__meng`、想风 `@xaiwind`、泊舟 `@bozhou_ai`、李继刚 `@lijigang` | 提示词模板、Claude Code / Codex / WorkBuddy / Skill / Agent 实操与工作流 |
| **一人公司、创业与变现** | **中文**：Orange AI `@oran_ge`、刘小排 `@bourneliu66`、亦仁 `@yiren_ai`、余温 `@gkxspace`、哥飞 `@gefei55`、AYi `@AYi_AInotes`、智昊 `@cnzhihao`<br>**英文**：Pieter Levels `@levelsio`、Marc Lou `@marc_louvion`、Dan Koe `@thedankoe`、Daniel Vassallo `@dvassallo`、Greg Isenberg（博客信源） | 一人公司产品打法、独立开发变现案例、真实收入与流量冷启动 |
| **海外一手方法与技术动向** | Ethan Mollick `@emollick`、Simon Willison `@simonw`、Andrej Karpathy `@karpathy`、Dan Shipper `@danshipper`、Swyx `@swyx`；产品与官方：`@AnthropicAI`、`@WorkBuddy_AI`、Sam Altman `@sama`、Tibo `@thsottiaux` | 一手工程评测方法论、新模型底层能力边界、官方产品路线与隐藏参数 |
| **AI 视频、视觉与开源发现** | Berryxia `@berryxia`、李岳 `@liyue_ai`、知识猫AI实验室 `@GeekCatX`、岚叔 `@LufzzLiz`、余一 `@ameliax111`、GitHubDaily `@GitHub_Daily` | AI 视频/视觉工作流、高星开源项目、本地工具实测 Demo |

### 2. 非 X 侧高频辅助信源

- **中文头部公众号（个人 IP 风格与方法对标）**：数字生命卡兹克、宝玉、歸藏、量子位、机器之心、Founder Park、特工宇宙、张小珺等（只看选题与叙事切口，绝不洗稿）。
- **海外一手博客与通讯**：各家 AI 实验室官方博客、Every、Lenny's Newsletter、One Useful Thing（Ethan Mollick）、Latent Space（Swyx）等。
- **中文 AI 热点快报**：AIHOT 每日高热工具与开源榜单。
