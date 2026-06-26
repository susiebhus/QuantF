# QuantF v1.2 Agent Research 需求说明

目标：在 QuantF v1.1 “稳定数据管道 + 事件驱动系统”的基础上，新增 LLM Agent 研究能力。Agent 只负责研究、解释、归纳、报告和人工复核辅助，不负责自动交易。

核心原则：

```text
数据系统负责事实
规则系统负责事件
LLM Agent 负责解释和研究
用户负责最终决策
交易动作全部手动
```

---

## 1. 背景

当前 QuantF 已具备：

- Watchlist 管理
- 增量行情抓取
- raw data 层
- 数据质量检查
- 信号计算
- 事件系统
- 组合权重偏离统计
- Streamlit Dashboard

下一阶段需要加入 Agent 能力，让系统能够基于本地 QuantF 数据生成：

- 每日市场研究摘要
- 事件解释
- 个股研究卡片
- 组合风险总结
- 人工复核清单
- 周报 / 月报草稿

---

## 2. 硬约束

### 2.1 禁止自动交易

Agent 不允许：

- 自动下单
- 自动生成实盘订单
- 调用券商交易 API
- 直接输出“必须买入 / 必须卖出”
- 代表用户做最终投资决策

Agent 可以：

- 输出观察结论
- 输出风险解释
- 输出需要人工复核的问题
- 输出“可选观察动作”
- 输出组合偏离和风险提示

推荐表达：

```text
建议人工复核 NVDA 权重偏离是否仍符合长期计划。
```

禁止表达：

```text
立即买入 NVDA。
立即卖出 AAPL。
```

### 2.2 禁止编造数据

Agent 只能基于 QuantF 提供的结构化上下文回答。

禁止：

- 编造实时价格
- 编造新闻
- 编造财报
- 编造估值数据
- 编造分析师预期

如果上下文缺失，必须输出：

```text
当前 QuantF 数据不足，无法判断。
```

### 2.3 研究与交易分离

Agent 输出只进入：

- `reports/`
- Streamlit Agent 页面
- 本地数据库记录

不进入：

- 券商 API
- 自动交易模块
- 订单管理系统

---

## 3. v1.2 核心目标

将 QuantF 升级为：

```text
Data Pipeline
  -> Signal Engine
  -> Event System
  -> Agent Context Builder
  -> LLM Research Agent
  -> Markdown Reports
  -> Human Review
```

v1.2 的重点不是让 Agent “预测股价”，而是让 Agent 解释 QuantF 已经计算出的事实和事件。

---

## 4. 新增模块

新增目录：

```text
src/quantf/agent/
  __init__.py
  client.py
  context.py
  prompts.py
  analyst.py
  reports.py
  schemas.py
```

### 4.1 `agent/client.py`

职责：

- 封装 LLM API 调用
- 读取 API Key
- 读取模型配置
- 处理超时、失败、重试
- 返回纯文本或结构化结果

第一版支持：

```text
OpenAI-compatible Chat Completions API
```

必须支持配置：

```yaml
provider: openai_compatible
base_url: https://api.openai.com/v1
model: gpt-4.1-mini
temperature: 0.2
timeout_seconds: 60
max_retries: 2
```

环境变量：

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
```

说明：

- `base_url` 必须可配置，方便以后切换 OpenAI、OpenRouter、DeepSeek、Moonshot、本地模型网关等兼容接口。
- 业务代码不得直接调用第三方 SDK，必须通过 `agent/client.py`。

### 4.2 `agent/context.py`

职责：

从 DuckDB 构建给 LLM 使用的结构化上下文。

输入表：

- `signals_daily`
- `events`
- `portfolio_stats`
- `ingestion_runs`
- `data_quality_report`
- `daily_prices`

输出结构：

```json
{
  "as_of_date": "2026-06-26",
  "market_regime": {
    "regime": "Risk On",
    "reason": "SPY and QQQ are in healthy uptrends"
  },
  "assets": [],
  "events": [],
  "portfolio": [],
  "data_health": {}
}
```

必须控制上下文大小：

- 默认最多 20 个 symbol
- 默认最多 30 条最近事件
- 默认最多 20 条数据质量问题
- 不把完整历史行情传给 LLM
- 不把 raw payload 传给 LLM

### 4.3 `agent/prompts.py`

职责：

- 管理系统提示词
- 管理不同报告类型的 prompt 模板
- 约束 Agent 输出风格和边界

必须包含系统约束：

```text
你是 QuantF 的长期投资研究 Agent。
你只能基于用户提供的 QuantF 结构化数据进行分析。
你不能编造实时价格、新闻、财报或估值数据。
你不能给出自动交易指令。
交易部分全部由用户手动完成。
你的输出应该帮助用户复核，而不是替用户决策。
```

### 4.4 `agent/analyst.py`

职责：

- 组织 context
- 选择 prompt
- 调用 LLM client
- 返回报告文本

第一版需要实现：

- `generate_daily_summary()`
- `generate_symbol_research(symbol)`
- `generate_event_explanation(event_id)`
- `generate_portfolio_review()`

### 4.5 `agent/reports.py`

职责：

- 将 Agent 输出保存为 Markdown
- 管理报告文件路径
- 提供读取最近报告的函数

输出目录：

```text
reports/
  daily/
  symbols/
  portfolio/
  events/
```

示例：

```text
reports/daily/daily_2026-06-26.md
reports/symbols/NVDA_2026-06-26.md
reports/portfolio/portfolio_2026-06-26.md
reports/events/event_TrendChanged_NVDA_2026-06-26.md
```

### 4.6 `agent/schemas.py`

职责：

- 定义 Agent context 的数据结构
- 定义报告元数据结构
- 为后续结构化输出预留接口

第一版可以使用 `dataclass`，不强制引入 Pydantic。

---

## 5. 配置文件

新增：

```text
configs/agent.yaml
```

示例：

```yaml
enabled: true
provider: openai_compatible
base_url_env: OPENAI_BASE_URL
api_key_env: OPENAI_API_KEY
model_env: OPENAI_MODEL
default_base_url: https://api.openai.com/v1
default_model: gpt-4.1-mini
temperature: 0.2
timeout_seconds: 60
max_retries: 2
output_language: zh-CN
max_context_symbols: 20
max_context_events: 30
max_context_quality_issues: 20
```

---

## 6. 新增数据库表

### 6.1 `agent_runs`

记录每次 Agent 调用。

字段：

- `run_id`
- `run_type`
- `symbol`
- `event_id`
- `model`
- `status`
- `error_message`
- `prompt_hash`
- `context_hash`
- `output_path`
- `created_at`

用途：

- 追踪 Agent 调用历史
- 排查失败
- 确认某份报告使用了什么上下文

### 6.2 `agent_reports`

记录报告元数据。

字段：

- `report_id`
- `run_id`
- `report_type`
- `symbol`
- `event_id`
- `title`
- `path`
- `summary`
- `created_at`

用途：

- Streamlit 展示最近报告
- 后续搜索报告
- 与事件、标的关联

---

## 7. CLI 需求

新增命令：

```bash
quantf agent-daily
quantf agent-symbol NVDA
quantf agent-event <event_id>
quantf agent-portfolio
```

### 7.1 `quantf agent-daily`

输出：

- 市场状态
- 今日/最近事件
- 需要关注的标的
- 组合风险
- 人工复核清单

保存：

```text
reports/daily/daily_YYYY-MM-DD.md
```

### 7.2 `quantf agent-symbol NVDA`

输出：

- 当前趋势状态
- 风险状态
- 回撤
- 相对 SPY/QQQ 强弱
- 最近事件解释
- 长期 thesis 复核问题

保存：

```text
reports/symbols/NVDA_YYYY-MM-DD.md
```

### 7.3 `quantf agent-event <event_id>`

输出：

- 事件含义
- 为什么触发
- 对长期持有的影响
- 需要人工检查的问题

保存：

```text
reports/events/event_<event_id>.md
```

### 7.4 `quantf agent-portfolio`

输出：

- 当前组合权重
- 目标权重偏离
- 集中度风险
- 科技股暴露风险
- 再平衡复核问题

保存：

```text
reports/portfolio/portfolio_YYYY-MM-DD.md
```

---

## 8. Streamlit 需求

新增页面：

```text
Agent Research
```

页面功能：

- 展示最近日报
- 展示最近个股研究报告
- 展示最近组合复核报告
- 展示 Agent run 状态
- 支持选择 symbol 并生成个股研究
- 支持选择 event 并生成事件解释

第一版可以使用按钮触发同步生成，不要求异步队列。

如果没有 API Key，需要提示：

```text
未检测到 OPENAI_API_KEY，无法生成 Agent 报告。
```

---

## 9. 报告输出格式

### 9.1 每日研究摘要

Markdown 结构：

```text
# QuantF 每日研究摘要

## 1. 数据日期

## 2. 市场状态

## 3. 关键事件

## 4. 需要关注的标的

## 5. 组合风险

## 6. 人工复核清单

## 7. 说明与限制
```

### 9.2 个股研究卡片

Markdown 结构：

```text
# QuantF 个股研究卡片：NVDA

## 1. 当前状态

## 2. 趋势与风险

## 3. 相对强弱

## 4. 最近事件

## 5. 长期 thesis 复核

## 6. 人工检查清单
```

### 9.3 组合复核报告

Markdown 结构：

```text
# QuantF 组合复核报告

## 1. 组合概览

## 2. 权重偏离

## 3. 集中度风险

## 4. 市场环境

## 5. 人工复核清单
```

---

## 10. Agent 输出约束

所有 Agent 输出必须包含：

- 数据来源说明
- 基于 QuantF 本地数据的限制说明
- 不构成投资建议说明
- 人工复核清单

所有 Agent 输出不允许包含：

- 自动交易命令
- 确定性收益承诺
- 未提供数据的新闻或财报结论
- 无依据目标价
- 夸张语言

推荐输出用词：

```text
观察
关注
复核
风险提示
可能
需要进一步确认
```

避免输出用词：

```text
必涨
必跌
稳赚
立刻买入
立刻卖出
无风险
```

---

## 11. Multi-Agent 设计

v1.2 不需要真正启动多个独立进程。第一版使用“逻辑多 Agent”即可。

建议角色：

### 11.1 Market Analyst

输入：

- SPY / QQQ 信号
- market_regime
- 最近市场事件

输出：

- Risk On / Neutral / Risk Off 解释
- 科技股环境判断

### 11.2 Event Analyst

输入：

- `events`

输出：

- 事件解释
- 影响范围
- 人工复核问题

### 11.3 Portfolio Analyst

输入：

- `portfolio_stats`

输出：

- 权重偏离
- 集中度风险
- 再平衡复核问题

### 11.4 Symbol Analyst

输入：

- 单个 symbol 的 signals
- 相关 events

输出：

- 个股研究卡片
- 长期持有 thesis 复核问题

第一版可以由一个 LLM call 完成综合报告；后续再拆成多个 Agent call。

---

## 12. 安全与隐私

### 12.1 API Key

要求：

- 不允许把 API Key 写入代码
- 不允许把 API Key 写入报告
- 不允许把 API Key 写入数据库
- 只从环境变量读取

### 12.2 上下文最小化

发送给 LLM 的内容只包含必要摘要：

- latest signals
- recent events
- portfolio stats
- market regime
- data health summary

不发送：

- 完整历史行情
- raw provider payload
- 本地文件路径之外的敏感信息
- 用户券商账号信息

### 12.3 可审计性

每次 Agent 调用必须记录：

- 使用模型
- 报告类型
- context hash
- prompt hash
- 输出文件路径
- 成功/失败状态

---

## 13. 错误处理

必须处理：

- API Key 缺失
- 网络超时
- LLM API 返回错误
- 模型输出为空
- 数据库无数据
- 事件不存在
- symbol 不在 watchlist

错误信息应清晰，例如：

```text
Agent report generation failed: OPENAI_API_KEY is not configured.
```

---

## 14. 测试要求

必须新增测试：

- `test_agent_context.py`
- `test_agent_prompts.py`
- `test_agent_reports.py`

测试重点：

- Context 不包含 raw payload
- Context 限制最近事件数量
- 无 API Key 时给出明确错误
- 报告能正确写入 `reports/`
- Prompt 包含禁止自动交易约束

LLM API 调用必须 mock，不允许测试依赖真实网络。

---

## 15. v1.2 完成标准

满足以下条件即认为 v1.2 成功：

- 可以通过环境变量接入 LLM API
- 可以生成中文每日研究摘要
- 可以生成个股研究卡片
- 可以生成事件解释
- 可以生成组合复核报告
- 报告保存到 `reports/`
- Streamlit 可以查看最近 Agent 报告
- Agent 不会输出自动交易指令
- Agent 不会编造 QuantF 上下文之外的数据
- 所有 LLM 调用可追溯
- 无 API Key 时系统仍可正常运行，只是禁用 Agent 生成

---

## 16. v1.2 不做的事

明确不做：

- 自动交易
- 券商 API 下单
- 实时新闻抓取
- SEC 财报抓取
- FRED 宏观数据抓取
- AI Agent 自主循环
- 多模型投票
- 自动日报定时推送

这些留给 v1.3 或 v2。

---

## 17. 推荐实现顺序

1. 新增 `configs/agent.yaml`
2. 新增 `agent/context.py`
3. 新增 `agent/prompts.py`
4. 新增 `agent/client.py`
5. 新增 `agent/reports.py`
6. 新增 `agent/analyst.py`
7. 新增数据库表 `agent_runs` 和 `agent_reports`
8. 新增 CLI 命令
9. 新增 Streamlit Agent Research 页面
10. 新增测试
11. 更新 README / README.zh-CN

---

## 18. 一句话总结

v1.2 的核心不是让 QuantF 自动交易，而是让 QuantF 拥有一个可审计、可约束、只基于本地数据工作的 LLM 研究员。
