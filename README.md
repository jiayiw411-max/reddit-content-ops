# Reddit AI 内容运营助手

从本地图片素材生成 Reddit 帖子草稿,匹配最合适的社区,人工确认后手动发布
(工具本身不自动发帖),并持续追踪发布后的表现数据,用一套可校准的评测方法论
反哺下一轮选题——而不是单纯的"发帖机器人"。

方法论继承自 [`video-use`](../video-use) 项目里验证过的 rubric + 盲评 + bucket
校准模式(那边是给视频稿子用的 Claude skill),在这里用真代码重新实现,并针对
Reddit 场景做了两处关键调整:

- 风险/合规拆成独立指标,不进 6 维质量平均分——"被删帖"是断崖式风险,不该被
  文案质量的高分稀释掉
- 表现 bucket 用"相对该 subreddit 历史基准"而不是绝对 upvotes 数字——不同社区
  量级差好几个数量级,不可比

## 架构

```
素材库 ──▶ 生成草稿(LLM,按 standards/writing_standard.md)
               │
               ▼
        社区匹配(按 standards/community_standard.md,现查 Reddit 官方规则接口)
               │
               ▼
   盲评打分 + bucket 预测(按 standards/review_rubric.md,不接触任何历史表现数据)
               │
               ▼
         人工确认 ──▶ 你手动发布(工具不自动发帖)
               │
               ▼
      表现追踪(只读 Reddit 公开 .json 接口:score / num_comments / upvote_ratio / num_crossposts)
               │
               ▼
   校准(真实表现 vs 预测 bucket,连同 BanReport 一起反馈进下一轮生成与选社区)
```

## 三份标准文档

生成 / 选社区 / 打分的具体规则都在这三份文件里,不在代码里硬编码——改规则改文档,
不用改代码:

- [`standards/writing_standard.md`](standards/writing_standard.md) — 撰写标准
- [`standards/community_standard.md`](standards/community_standard.md) — 社区选取标准
- [`standards/review_rubric.md`](standards/review_rubric.md) — 复盘评分标准(blind sub-agent 白名单)

## 数据模型

`Image` → `Post`(草稿 + 状态 + 风险 gate 结果 + 预测 bucket)→ `RubricScore`(按
channel 区分 main/blind/cross)、`PerformanceSnapshot`(每次抓取的表现快照)、
`BanReport`(被封反馈,进复盘)。见 [`src/reddit_ops/db/models.py`](src/reddit_ops/db/models.py)。

## 设置

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # 填入 REDDIT_USER_AGENT + ANTHROPIC_API_KEY
reddit-ops init
```

**Reddit 这边不需要注册任何应用。** Reddit 在 2025-11-11 关闭了个人开发者自助
注册 OAuth 应用的入口(Responsible Builder Policy),reddit.com/prefs/apps 的
create app 现在会卡在 reCAPTCHA 循环走不通,这是平台层面的限制,不是配置问题。
我们读的都是公开数据(子版规则、帖子分数/评论数),所以直接走 Reddit 公开只读
`.json` 接口(见 [`reddit_client.py`](src/reddit_ops/reddit_client.py)),
只需要规范的 `REDDIT_USER_AGENT`,不需要 client_id/secret。代价是限速更紧
(未认证约 10 req/min,代码里已做节流),对我们这种小用量的追踪场景够用。
如果以后申请到官方 API 审批通过,可以把 `reddit_client.get_json` 换成 OAuth
客户端,其余模块不用动。

## 命令

```bash
reddit-ops init                                    # 初始化本地 SQLite
reddit-ops draft "<图片描述>" <subreddit>            # 生成一篇草稿
reddit-ops score "<标题>" "<正文>" <subreddit>       # 盲评打分 + bucket 预测
reddit-ops track                                    # 抓取所有已发布帖子的最新表现
```

## 测试

```bash
pytest
```

## 阶段

1. ✅ 数据模型 + 三份标准文档 + LLM 生成/打分 CLI 跑通
2. 社区匹配的"强制动作"抽取(选社区规则 → 结构化 required_actions)+ 校准循环(`review/calibration.py`,待建)
3. 表现追踪定时任务 + 校准反馈自动生成"下一轮实验假设"
4. 测试补全(mock Reddit/Anthropic 调用) + 部署
