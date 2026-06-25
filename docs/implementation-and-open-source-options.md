# 长期美股量化盯盘系统：具体实现与开源项目选型

> 目标：围绕美股指数 ETF 与大型科技股，构建一个长期持有风格的个人量化盯盘系统。系统重点是数据更新、组合观察、风险提醒、财报跟踪和再平衡辅助，不以短线自动交易为核心。

## 1. 结论先行

对当前目标，最推荐的实现路线是：

```text
第一阶段：自研轻量系统
Python + DuckDB + yfinance + Streamlit + Plotly

第二阶段：加入财报和组合管理
SEC EDGAR API + 手动/CSV 持仓导入 + 告警规则

第三阶段：如需更完整账户管理
评估 Ghostfolio 二次开发，或与自研系统并行使用

第四阶段：如需实盘交易
接入 Alpaca 或 Interactive Brokers，只做人工确认下单
```

不建议一开始直接基于大型交易框架改造。你的目标是长期持有和盯盘，不是日内交易、高频交易或机器学习选股竞赛。

## 2. 两种实现路线

### 2.1 路线 A：自研轻量系统

适合程度：最高。

适合原因：

- 目标明确，只盯少量资产。
- 长期持有不需要复杂撮合引擎。
- Python 数据分析生态成熟。
- 后续可以逐步扩展财报、告警、组合和券商接口。
- 代码可控，适合个人长期维护。

推荐技术：

| 模块 | 技术 |
| --- | --- |
| 数据采集 | yfinance, SEC EDGAR API |
| 数据库 | DuckDB |
| 指标计算 | pandas / polars |
| 图表 | Plotly |
| 看板 | Streamlit |
| 定时任务 | cron / APScheduler |
| 配置 | YAML |
| 测试 | pytest |

第一版预期开发量：

```text
1-2 天：行情下载 + 指标计算 + 本地数据库
2-3 天：Streamlit Dashboard
1-2 天：持仓录入 + 权重分析
1-2 天：告警规则 + 周报
```

### 2.2 路线 B：基于 Ghostfolio 二次开发

适合程度：中高。

Ghostfolio 是一个开源财富管理系统，定位和你的长期持有目标比较接近。它支持股票、ETF、加密资产、多账户、交易导入、组合表现、风险分析和自托管。

优点：

- 已经有完整 Web UI。
- 已经有账户、交易、组合、收益统计。
- 支持 Docker 自部署。
- 更像一个长期资产管理系统，而不是交易机器人。

缺点：

- 技术栈是 TypeScript / Angular / NestJS / Prisma / PostgreSQL / Redis，二次开发门槛比 Python 高。
- 如果只是加几个量化指标，改它可能比自研还重。
- AGPL-3.0 许可证需要注意。如果只自用问题不大；如果要对外提供服务，需要认真处理开源义务。

适合二次开发的方向：

- 增加美股长期趋势指标。
- 增加 50/200 日均线状态。
- 增加科技股集中度风险提醒。
- 增加目标权重与再平衡提醒。
- 增加 SEC 财报摘要模块。
- 增加自定义投资 thesis 笔记。

不建议一开始就改 Ghostfolio 核心逻辑。更稳的做法是：

```text
先自部署 Ghostfolio 管持仓
再自研一个 Python 量化分析服务
最后通过 Ghostfolio API 或数据库同步数据
```

## 3. 不太推荐直接作为主项目的框架

### 3.1 Qlib

Qlib 是微软开源的 AI 量化研究平台，覆盖数据处理、模型训练、回测、组合优化和执行。

适合：

- 多因子研究。
- 机器学习选股。
- 大规模量化实验。
- 研究型项目。

不适合当前第一版的原因：

- 目标过重。
- 更偏 alpha 研究，不是个人长期持仓管理。
- 数据准备和框架学习成本较高。

可以后续用在：

- 科技股相对强弱模型。
- ETF 轮动研究。
- 多因子评分研究。

### 3.2 QuantConnect Lean

Lean 是 QuantConnect 的开源算法交易引擎，支持 Python / C#，可做回测和实盘交易。

适合：

- 系统化交易策略。
- 多市场回测。
- 后续接券商做实盘策略。

不适合第一版的原因：

- 对长期盯盘和组合观察来说偏重。
- 本地数据和环境配置成本较高。
- 你当前重点不是自动交易。

后续如果要做严格回测和券商交易，可以再接入。

### 3.3 Backtrader

Backtrader 是经典 Python 回测框架。

适合：

- 策略回测。
- 日线/分钟线交易策略验证。

问题：

- 项目维护活跃度相对有限。
- 更适合交易策略，不是组合看板。

可以作为回测模块备选，但不建议作为整个系统底座。

### 3.4 vectorbt

vectorbt 是高性能向量化回测框架，适合快速测试大量参数和策略。

适合：

- 快速回测均线、动量、轮动策略。
- 参数扫描。
- 研究信号有效性。

不适合：

- 持仓管理。
- 财报跟踪。
- 长期看板。
- 告警系统。

可作为研究子模块使用。

### 3.5 QuantStats

QuantStats 是组合绩效分析工具，可以生成收益、回撤、Sharpe 等分析报告。

适合：

- 给你的组合生成绩效报告。
- 比较组合与 SPY / QQQ。

不适合：

- 数据采集。
- 持仓管理。
- 告警。

建议纳入自研系统作为报告模块。

## 4. 推荐架构

### 4.1 第一版架构

```text
configs/watchlist.yaml
  -> price_collector.py
  -> DuckDB
  -> indicators.py
  -> alert_engine.py
  -> Streamlit Dashboard
```

### 4.2 第二版架构

```text
行情数据源
财报数据源
持仓配置
  -> 数据采集层
  -> 数据清洗层
  -> DuckDB / PostgreSQL
  -> 指标计算层
  -> 风险规则层
  -> 报告层
  -> Web Dashboard
  -> Email / Telegram 通知
```

### 4.3 与 Ghostfolio 结合的架构

```text
Ghostfolio
  -> 管理交易记录、账户、组合表现

QuantF 自研服务
  -> 拉行情
  -> 算趋势和风险
  -> 拉 SEC 财报
  -> 生成告警和研究报告

二者通过 API / CSV / 数据库导入导出同步
```

## 5. 项目目录建议

```text
QuantF/
  configs/
    watchlist.yaml
    portfolio.yaml
    alerts.yaml
  data/
    quantf.duckdb
  docs/
  src/
    quantf/
      data/
        prices.py
        sec.py
        calendar.py
      db/
        connection.py
        schema.py
      indicators/
        trend.py
        risk.py
        valuation.py
      portfolio/
        holdings.py
        allocation.py
        rebalance.py
      alerts/
        rules.py
        engine.py
      reports/
        weekly.py
        monthly.py
      app/
        streamlit_app.py
  tests/
    test_indicators.py
    test_alerts.py
  README.md
  pyproject.toml
```

## 6. 第一阶段具体实现

### 6.1 配置关注列表

`configs/watchlist.yaml`

```yaml
symbols:
  core_etf:
    - SPY
    - QQQ
    - VTI
  tech_stocks:
    - NVDA
    - AAPL
    - AMZN
    - MSFT
  sector_etf:
    - SMH
    - XLK
  cash_like:
    - SGOV
```

### 6.2 下载行情

第一阶段用 `yfinance`：

```python
import yfinance as yf

symbols = ["SPY", "QQQ", "VTI", "NVDA", "AAPL", "AMZN", "MSFT"]
data = yf.download(symbols, period="10y", auto_adjust=False, group_by="ticker")
```

下载后写入 DuckDB：

```sql
CREATE TABLE IF NOT EXISTS daily_prices (
  symbol TEXT,
  date DATE,
  open DOUBLE,
  high DOUBLE,
  low DOUBLE,
  close DOUBLE,
  adj_close DOUBLE,
  volume DOUBLE,
  source TEXT,
  updated_at TIMESTAMP,
  PRIMARY KEY (symbol, date)
);
```

### 6.3 计算指标

每个 symbol 每天计算：

```text
ma_50
ma_200
return_20d
return_60d
return_252d
volatility_20d
volatility_60d
drawdown_from_52w_high
drawdown_from_all_time_high
trend_state
risk_state
```

趋势规则：

```text
price > ma_200 且 ma_50 > ma_200 => uptrend
price < ma_200 且 ma_50 < ma_200 => downtrend
其他 => neutral
```

风险规则：

```text
从 52 周高点回撤超过 20% => watch
从 52 周高点回撤超过 30% => warning
价格跌破 200 日均线 => watch
QQQ 跌破 200 日均线且 VIX > 30 => market_warning
```

### 6.4 录入持仓

`configs/portfolio.yaml`

```yaml
base_currency: USD
positions:
  - symbol: SPY
    shares: 10
    cost_basis: 450
  - symbol: QQQ
    shares: 8
    cost_basis: 390
  - symbol: NVDA
    shares: 20
    cost_basis: 120

target_allocation:
  SPY: 35
  QQQ: 25
  VTI: 10
  NVDA: 10
  AAPL: 7.5
  AMZN: 7.5
  MSFT: 5
```

组合规则：

```text
单只股票 > 20% => warning
科技股合计 > 70% => warning
实际权重偏离目标权重超过 5 个百分点 => rebalance_watch
现金类资产低于 3% => cash_watch
```

### 6.5 做 Dashboard

Streamlit 页面：

```text
首页：
  - 市场状态
  - 组合总市值
  - 当日 / 本周 / 本月收益
  - 触发提醒
  - 核心资产趋势表

资产页：
  - 价格 + 50/200 日均线
  - 回撤图
  - 波动率
  - 最近提醒

组合页：
  - 当前权重
  - 目标权重
  - 偏离程度
  - 再平衡提醒
```

## 7. 第二阶段具体实现

### 7.1 接入 SEC 财报

通过 SEC 的 Company Facts API 获取公司 XBRL 数据：

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
```

需要维护 ticker 到 CIK 的映射：

```yaml
NVDA: 0001045810
AAPL: 0000320193
AMZN: 0001018724
MSFT: 0000789019
```

重点提取：

```text
RevenueFromContractWithCustomerExcludingAssessedTax
NetIncomeLoss
OperatingIncomeLoss
EarningsPerShareDiluted
NetCashProvidedByUsedInOperatingActivities
PaymentsToAcquirePropertyPlantAndEquipment
```

自由现金流：

```text
free_cash_flow = operating_cash_flow - capex
```

### 7.2 财报告警

规则示例：

```text
收入同比连续两个季度下降 => watch
经营利润率连续两个季度下降 => watch
自由现金流转负 => warning
EPS 同比大幅下降且股价跌破 200 日均线 => warning
```

### 7.3 投资 thesis

每个个股维护一份 thesis：

```text
NVDA:
  thesis: AI 算力需求长期增长，数据中心收入是核心观察变量
  must_hold:
    - 数据中心收入继续增长
    - 毛利率保持健康
    - CUDA 生态优势没有明显削弱
  review_if:
    - 数据中心收入增长明显放缓
    - 大客户自研芯片替代加速
    - 估值极端且增长放缓
```

这个模块很重要，因为长期持有真正要判断的是“买入逻辑是否仍然成立”。

## 8. 第三阶段：券商接口

### 8.1 Alpaca

适合：

- API 友好。
- Paper trading 方便。
- 股票和 ETF 自动交易较容易。

适合后续：

- 同步账户。
- 读取持仓。
- 生成订单草稿。
- Paper trading 测试。

### 8.2 Interactive Brokers

适合：

- 覆盖市场更广。
- 更接近专业券商。
- 适合长期实际账户管理。

缺点：

- TWS / Gateway 配置复杂。
- API 上手成本高。

### 8.3 建议原则

第三阶段之前不要做全自动交易。

推荐顺序：

```text
只读同步持仓
  -> 生成再平衡建议
  -> 生成订单草稿
  -> 人工确认
  -> 小资金 paper trading
  -> 小资金实盘
```

## 9. 开源项目对比

| 项目 | 用途 | 是否适合二开 | 适合放在系统哪里 |
| --- | --- | --- | --- |
| Ghostfolio | 财富管理、组合跟踪 | 高 | 持仓和组合管理底座 |
| Qlib | AI 量化研究 | 中 | 后续研究模块 |
| QuantConnect Lean | 回测和实盘交易引擎 | 中 | 后续交易模块 |
| Backtrader | Python 回测 | 中 | 策略回测子模块 |
| vectorbt | 向量化回测 | 中高 | 快速研究子模块 |
| QuantStats | 组合绩效分析 | 高 | 报告模块 |
| yfinance | 行情下载 | 高 | 第一版数据源 |
| bt | 组合回测 | 中 | 资产配置回测 |

## 10. 最推荐组合

### 10.1 最快落地

```text
自研 Python 项目
+ yfinance
+ DuckDB
+ Streamlit
+ Plotly
+ QuantStats
```

这是最适合当前仓库从零开始的方案。

### 10.2 最像完整产品

```text
Ghostfolio 自部署
+ QuantF Python 分析服务
+ SEC 财报模块
+ 自定义风险告警
```

适合你后续想把它做成长期资产管理工具。

### 10.3 最偏专业量化

```text
Qlib
+ vectorbt
+ Lean
```

适合以后做策略研究和交易执行，不适合作为第一版主线。

## 11. 建议的实际开发顺序

### Step 1：先自研 MVP

做出可运行版本：

```text
下载行情
保存数据
计算指标
展示页面
生成提醒
```

### Step 2：加入持仓和权重

让系统知道你持有什么：

```text
手动录入持仓
计算组合市值
计算权重
检查集中度
检查再平衡偏离
```

### Step 3：加入财报

让系统知道公司有没有变差：

```text
SEC 数据
收入增长
利润增长
现金流
利润率
财报提醒
```

### Step 4：加入报告

让系统每周/月自动告诉你重点：

```text
本周表现
风险变化
提醒列表
再平衡建议
财报事件
```

### Step 5：再考虑 Ghostfolio 或券商接口

不要太早接交易。先把“看得清楚”做好，再做“动得起来”。

## 12. 我建议现在怎么开工

当前仓库还很轻，建议直接开始自研 MVP，而不是 fork 大项目。

下一步可以创建：

```text
pyproject.toml
configs/watchlist.yaml
configs/portfolio.example.yaml
src/quantf/data/prices.py
src/quantf/db/schema.py
src/quantf/indicators/trend.py
src/quantf/alerts/rules.py
src/quantf/app/streamlit_app.py
```

第一版目标只做四件事：

```text
1. 拉 SPY / QQQ / VTI / NVDA / AAPL / AMZN / MSFT 日线
2. 计算 MA50 / MA200 / 回撤 / 波动率
3. 展示趋势和风险状态
4. 对跌破长期均线、回撤、集中度发出提醒
```

做完这个，系统就有真实使用价值。

## 13. 参考链接

- Ghostfolio: <https://github.com/ghostfolio/ghostfolio>
- Qlib: <https://github.com/microsoft/qlib>
- QuantConnect Lean: <https://github.com/QuantConnect/Lean>
- Backtrader: <https://github.com/mementum/backtrader>
- vectorbt: <https://github.com/polakowo/vectorbt>
- QuantStats: <https://github.com/ranaroussi/quantstats>
- yfinance: <https://github.com/ranaroussi/yfinance>
- SEC EDGAR APIs: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>

