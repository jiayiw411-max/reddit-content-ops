# Reddit AI 内容运营助手

一个本地网页,从图片生成 Reddit 帖子草稿、辅助选社区、发布后追踪表现数据,
用一套可校准的评测方法论反哺下一轮选题——而不是单纯的"发帖机器人"。工具不
自动发帖、不自动访问 Reddit(原因见下文),每一步都是"AI 辅助 + 人工确认"。

方法论继承自 [`video-use`](../video-use) 项目里验证过的 rubric + 盲评 + bucket
校准模式(那边是给视频稿子用的 Claude skill),在这里用真代码重新实现,并针对
Reddit 场景做了两处关键调整:

- 风险/合规拆成独立指标,不进 6 维质量平均分——"被删帖"是断崖式风险,不该被
  文案质量的高分稀释掉
- 表现 bucket 用"相对该 subreddit 历史基准"而不是绝对 upvotes 数字——不同社区
  量级差好几个数量级,不可比

## 流程

```
选图 → 撰写草稿(LLM,按 standards/writing_standard.md)
         │
         ▼
      选社区(LLM 按训练知识建议候选,标"未验证"——原因见下文)
         │
         ▼
      你去对应社区尝试发布 ──失败──▶ 在创作台标记失败原因,换一个候选重试
         │
       成功
         ▼
   盲评打分 + bucket 预测(此时才知道最终社区,按 standards/review_rubric.md,
   不接触任何真实表现数据)
         │
         ▼
      进复盘看板:表现追踪(人工录入 + 书签工具,见下文)
         │
         ▼
   校准(真实表现 vs 预测 bucket,反馈进下一轮生成与选社区)
```

选社区失败(被 AutoMod 拦、缺 flair 之类)和发布后被删,是两件不同的事,分别记在
`CommunityAttempt`(发布前的重试循环)和 `BanReport`(帖子活过、后来被删)两张表里,
不混在一起。

## 界面

`reddit-ops serve` 启动一个本地网页,两个区块:

- **创作台**:给一个本地文件夹路径,浏览缩略图选图——模型直接读图片内容生成
  文案(多模态,不是靠打字描述转述给模型),然后看候选社区建议、记录每次
  发布尝试的成败
- **复盘看板**:已发布帖子的表现数据历史,书签工具录入的数据自动显示在这里

## 三份标准文档

生成 / 选社区 / 打分的具体规则都在这三份文件里,不在代码里硬编码——改规则改文档,
不用改代码:

- [`standards/writing_standard.md`](standards/writing_standard.md) — 撰写标准
- [`standards/community_standard.md`](standards/community_standard.md) — 社区选取标准
- [`standards/review_rubric.md`](standards/review_rubric.md) — 复盘评分标准(blind sub-agent 白名单)

## 数据模型

`Image` → `Post`(草稿 + 状态 + 风险 gate 结果 + 预测 bucket)→
`CommunityAttempt`(发布前的选社区重试记录)、`RubricScore`(按 channel 区分
main/blind/cross)、`PerformanceSnapshot`(每次录入的表现快照)、`BanReport`
(发布后被删的反馈)。见 [`src/reddit_ops/db/models.py`](src/reddit_ops/db/models.py)。

## 设置

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 填入 REDDIT_USER_AGENT + ANTHROPIC_API_KEY
reddit-ops init
reddit-ops serve       # 打开 http://127.0.0.1:8765
```

### 读取 Reddit 数据这件事

Reddit 在 2025-11-11 关闭了个人开发者自助注册 OAuth 应用的入口(Responsible
Builder Policy),连公开只读的 `.json` 接口现在也会被指纹级反爬检测拦截
(403 Blocked,实测过,不是配置问题)。这不是靠换个 User-Agent 或者用浏览器
自动化能绕过的——那条路要求主动绕过平台的反自动化保护,这个项目不走那条路,
细节见 [`src/reddit_ops/reddit_client.py`](src/reddit_ops/reddit_client.py) 的注释。

这带来两个现实限制,现阶段的应对方式:

1. **没法自动发现/验证全网社区**:选社区那一步,LLM 只能凭训练知识给建议,
   每个候选都标"未验证"。发布前你自己打开对应页面看一眼规则,这一步不算
   额外负担,因为你反正要去那里手动发帖。
2. **没法自动追踪表现数据**:`reddit-ops record` 命令 + [`tools/`](tools/)
   里的浏览器书签——你自己发完帖子后打开帖子页面点一下书签,读一下页面上
   本来就显示给你的 score/评论数,自动发到本地看板存起来。好处是浏览量这种
   官方 API 永远拿不到、只有作者本人能看到的数据,这条路反而能录进去。

**官方 API 审批**(申请中,走 [Reddit 的 Data Access Request](https://support.reddithelp.com/hc/en-us/requests/new?ticket_form_id=14868593862164))
批下来之后,这两个限制都会解除:选社区能实时搜索验证,`tracker/fetcher.py`
能自动抓取表现数据,不用改其余模块。

## 命令

```bash
reddit-ops init      # 初始化本地 SQLite
reddit-ops serve      # 启动网页(创作台 + 复盘看板),默认 8765 端口
reddit-ops record --url <帖子链接> --score N --comments N [--views N]  # 人工录入一次表现快照
reddit-ops track      # 官方 API 批下来后:自动抓取所有已发布帖子的最新表现
```

## 测试

```bash
pytest
```

## 阶段

1. ✅ 数据模型 + 三份标准文档 + LLM 生成/打分跑通
2. ✅ 创作台网页(选图→撰写→选社区→失败重试循环)+ 复盘看板(人工录入 + 书签),官方 API 审批中
3. 社区规则的"强制动作"抽取(比如必须加的 flair)+ 校准循环(`review/calibration.py`,待建)
4. 官方 API 批下来后:选社区实时验证 + `track` 命令自动化 + 校准反馈自动生成"下一轮实验假设"
5. 测试补全(mock Anthropic 调用) + 部署
