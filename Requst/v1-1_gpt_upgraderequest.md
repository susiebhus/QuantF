QuantF v1.1 改进说明（给 Codex 用）

目标：在不改变现有功能的前提下，将系统从“可运行脚本”升级为“稳定数据管道 + 可扩展架构”。

⸻

🚨 当前问题总结（必须修）

1. 数据源耦合 yfinance

当前：

* 直接调用 yfinance

问题：

* 无法替换数据源
* 易被限流（429）
* 不可扩展

⸻

2. 全量拉取数据（严重低效）

当前：

* 每次 run-daily 重新拉历史数据

问题：

* 请求量大
* 慢
* 易失败
* 不可扩展

⸻

3. 没有数据质量控制

当前：

* 直接写入 DB

缺失：

* 数据校验
* 异常检测
* 失败记录

⸻

4. 没有 raw data 层

当前：

* 只有 clean 数据

问题：

* 无法 debug
* 无法回溯
* 无法修复历史错误

⸻

5. alert 是“重复计算型”

当前：

* 每天重新生成 alert

问题：

* 重复提醒
* 没有事件语义

⸻

🧱 v1.1 改进目标

🎯 核心目标

将系统升级为：

稳定数据管道（Data Pipeline） + 事件驱动系统（Event System）

⸻

🧩 必须新增模块

⸻

1️⃣ Data Provider 抽象层（必须做）

新建接口：

class MarketDataProvider:
    def fetch_prices(symbol, start, end):
        pass

⸻

实现：

* YahooFinanceProvider（当前 yfinance）
* （预留）PolygonProvider
* （预留）AlphaVantageProvider

⸻

修改点：

❌ 业务代码禁止直接 import yfinance
✔ 所有数据必须通过 Provider

⸻

2️⃣ 增量数据更新（核心优化）

当前逻辑（必须删除）：

每次：
  拉 10 年数据

⸻

v1.1 改为：

读取 last_successful_date
        ↓
只拉缺失区间
        ↓
追加写入 DB

⸻

必须新增字段：

ingestion_runs 表

* symbol
* start_date
* end_date
* status
* error_message
* fetched_at

⸻

3️⃣ Raw Data Layer（必须新增）

新表：

raw_prices

字段：

* symbol
* date_range
* raw_payload (json)
* provider
* fetched_at
* hash

⸻

作用：

* Debug 数据源问题
* 重建 clean data
* 对比不同 provider

⸻

4️⃣ 数据质量系统（必须新增）

新模块：

data_quality.py

⸻

检查规则：

Price Validity

* high >= low
* open/close != null
* volume >= 0

⸻

Spike Detection

* 单日涨跌 > 40% → warning

⸻

Missing Data

* 非交易日缺失 → ignore
* 交易日缺失 → error

⸻

输出：

data_quality_report

⸻

5️⃣ Signal Engine 解耦

当前问题：

* 指标计算和数据抓取混在一起

⸻

v1.1 修改：

data_layer → signal_layer → event_layer

⸻

signal_layer 输出：

* MA20 / 50 / 200
* return_20/60/252
* volatility
* drawdown
* rs_spy
* rs_qqq

⸻

6️⃣ Event System（重要升级）

当前：

* alert 每天重新生成

⸻

v1.1：

改为事件驱动

if state_changed:
    emit event

⸻

新事件类型：

* TrendChanged
* RiskEscalated
* New52WeekHigh
* New52WeekLow
* PriceCrossMA200
* PortfolioDrift

⸻

Event 特点：

* 不重复生成
* 可追溯
* 永久保存

⸻

7️⃣ Portfolio 模块（最小化加入）

新表：

portfolio

字段：

* symbol
* shares
* cost_basis
* target_weight

⸻

新功能：

* weight drift detection
* concentration risk
* beta estimation

⸻

8️⃣ Market Regime（新增轻量模块）

输入：

* SPY
* QQQ
* VIX

⸻

输出：

* Risk On
* Neutral
* Risk Off

⸻

🔧 修改 run-daily 流程

当前：

fetch → compute → alert → store

⸻

v1.1：

1. Read Watchlist
2. Incremental Fetch (Provider)
3. Store Raw Data
4. Clean & Validate
5. Update daily_prices
6. Compute Signals
7. Generate Events
8. Update Portfolio Stats
9. Write ingestion log

⸻

📊 Streamlit 改动（最小）

新增页面：

1. Data Health

* ingestion success rate
* failed symbols
* last update time

⸻

2. Event Timeline

* all events sorted by time

⸻

3. Portfolio Overview

* weight drift
* risk exposure

⸻

🧠 v1.1 核心思想（必须理解）

从：

“每天算指标”

变成：

“一个可靠的数据系统 + 事件驱动分析系统”

⸻

🚀 v1.1 完成标准

满足以下条件即成功：

✔ 可以切换数据源（不改业务逻辑）
✔ 支持增量更新
✔ 有 raw data 层
✔ 有数据质量检测
✔ alert 不再重复生成
✔ event 可追溯
✔ run-daily 可失败恢复

⸻

🧩 v2 预留接口（不要现在做）

* SEC 财报
* FRED 宏观
* Alpaca / IBKR
* AI Agent
* 自动日报

⸻

📌 一句话总结

v1.1 的核心不是“增加功能”，而是把 QuantF 从脚本升级成工程化数据系统。