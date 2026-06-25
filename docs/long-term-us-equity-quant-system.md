# 长期美股指数与科技股量化盯盘系统实现方案

> 目标：构建一个面向个人长期投资者的量化系统，用于长期跟踪美股指数与大型科技企业，辅助持仓观察、风险识别、再平衡和纪律化决策。本文仅用于系统设计与研究，不构成投资建议。

## 1. 项目定位

这个系统不应该被设计成高频交易机器人，也不应该以预测明天涨跌为核心。更合理的定位是：

- 长期跟踪核心资产。
- 自动更新价格、估值、财报、新闻和风险指标。
- 形成可解释的观察面板。
- 在风险、估值、趋势或基本面变化明显时提醒。
- 辅助定投、再平衡、减仓或继续持有决策。
- 保留完整的历史记录，便于复盘。

核心思想是：**长期持有为主，系统盯盘为辅；少交易，多观察；重风险，不追噪声。**

## 2. 目标资产池

### 2.1 指数与 ETF

系统优先跟踪可交易 ETF，而不是只跟踪指数点位。

| 类别 | 代表标的 | 用途 |
| --- | --- | --- |
| 标普 500 | SPY / VOO / IVV | 美国大盘核心仓位 |
| 纳斯达克 100 | QQQ / QQQM | 科技成长核心仓位 |
| 道琼斯工业指数 | DIA | 蓝筹风格观察 |
| 全市场 | VTI | 美国股票市场整体暴露 |
| 半导体 | SOXX / SMH | 科技硬件和 AI 产业链观察 |
| 科技行业 | XLK / VGT | 科技板块风格观察 |
| 短债或现金替代 | SGOV / BIL | 风险控制和现金管理观察 |

建议第一阶段只配置观察，不急于纳入所有标的。

推荐初始跟踪：

```text
SPY, QQQ, VTI, SMH, XLK, SGOV
```

### 2.2 科技龙头股票

重点关注大型科技企业：

```text
NVDA, AAPL, AMZN, MSFT, GOOGL, META, TSLA, AVGO, AMD, NFLX
```

用户当前明确提到：

```text
NVDA, AAPL, AMZN, MSFT
```

第一阶段可以只做：

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT
```

后续再扩展到更多科技股和行业 ETF。

## 3. 系统目标

### 3.1 必须解决的问题

这个系统应该回答以下问题：

- 当前资产价格相对长期趋势处于什么位置？
- 当前估值处于历史高位、中位还是低位？
- 公司基本面是否继续增长？
- 盈利能力和现金流是否恶化？
- 当前组合是否过度集中在单一股票或单一行业？
- 科技股整体是否进入高波动或高回撤状态？
- 是否触发长期持有者需要关注的风险事件？
- 是否到了定投、暂停定投、再平衡或减仓观察区？

### 3.2 不追求的问题

第一版不追求：

- 高频交易。
- 秒级或分钟级信号。
- 自动预测明日涨跌。
- 自动满仓或清仓。
- 复杂期权策略。
- 高杠杆。
- 完全无人值守实盘交易。

## 4. 核心设计原则

### 4.1 长期系统优先级

长期持有系统的优先级应该是：

```text
数据可靠性 > 风险控制 > 可解释性 > 自动化 > 收益优化
```

### 4.2 信号设计原则

信号应该少而稳：

- 价格趋势信号：判断资产是否处于长期上升、震荡或下跌趋势。
- 估值信号：判断资产是否过热或低估。
- 基本面信号：判断公司收入、利润、现金流和利润率是否变差。
- 风险信号：判断波动、回撤、相关性和集中度是否过高。
- 事件信号：财报、重大公告、监管、评级变化。

### 4.3 决策方式

系统不直接输出“买入/卖出”，而是输出状态：

| 状态 | 含义 | 人的动作 |
| --- | --- | --- |
| 正常 | 趋势、基本面、风险均正常 | 继续观察或按计划定投 |
| 关注 | 某些指标转弱或过热 | 暂停加仓、等待确认 |
| 警戒 | 回撤、估值或基本面风险明显 | 检查仓位和风险敞口 |
| 行动建议 | 触发明确再平衡规则 | 人工确认后执行 |

## 5. 数据源方案

### 5.1 行情数据

第一阶段可以用免费或低成本数据做研究：

- `yfinance`：适合原型开发和历史日线数据研究。
- Stooq / Nasdaq Data Link / Alpha Vantage：可作为备选或校验源。
- Alpaca Market Data：适合接入正式 API，支持历史和实时行情。
- Interactive Brokers：如果用户后续使用 IBKR 交易，可接入 TWS / Gateway API。

需要注意：免费数据适合研究，不适合作为唯一实盘依据。正式交易前至少要有一个稳定 API 数据源，并保留数据校验机制。

### 5.2 财报与基本面数据

美国上市公司财报可以从 SEC EDGAR 获取。SEC 的 `data.sec.gov` 提供公司提交历史和 XBRL 财务数据 API，不需要 API Key。

建议使用：

- SEC Submissions API：获取公司文件提交历史。
- SEC Company Facts API：获取 XBRL 财务指标。
- 财报日历 API：获取未来财报发布时间。

重点基本面指标：

- Revenue。
- Gross Profit。
- Operating Income。
- Net Income。
- Diluted EPS。
- Free Cash Flow。
- Operating Cash Flow。
- Gross Margin。
- Operating Margin。
- Net Margin。
- Revenue YoY。
- EPS YoY。
- FCF YoY。

### 5.3 宏观与利率数据

长期科技股估值对利率和流动性敏感。可以纳入：

- 美国 10 年期国债收益率。
- 美国 2 年期国债收益率。
- Fed Funds Rate。
- CPI。
- 美元指数。
- VIX。

第一阶段只纳入：

```text
10Y Treasury Yield, Fed Funds Rate, VIX
```

### 5.4 新闻与事件数据

新闻不应该直接驱动交易，但可以驱动提醒。

事件类型：

- 财报发布。
- 业绩指引上调或下调。
- 重大并购。
- 监管调查。
- 反垄断诉讼。
- 产品发布。
- 管理层变动。
- 大额回购或增发。

第一版可以先记录财报日期和 SEC 8-K / 10-Q / 10-K，新闻摘要留到第二阶段。

## 6. 数据表设计

推荐使用 DuckDB 或 SQLite 起步，后续再迁移到 PostgreSQL。

### 6.1 `assets`

记录资产元信息。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | text | 股票或 ETF 代码 |
| name | text | 名称 |
| asset_type | text | stock / etf / index / macro |
| sector | text | 行业 |
| currency | text | 币种 |
| active | boolean | 是否启用 |

### 6.2 `daily_prices`

记录日线行情。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | text | 代码 |
| date | date | 交易日 |
| open | double | 开盘价 |
| high | double | 最高价 |
| low | double | 最低价 |
| close | double | 收盘价 |
| adj_close | double | 复权收盘价 |
| volume | double | 成交量 |
| source | text | 数据源 |

### 6.3 `fundamentals_quarterly`

记录季度财务数据。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | text | 代码 |
| fiscal_period | text | 财报期 |
| report_date | date | 披露日期 |
| revenue | double | 收入 |
| gross_profit | double | 毛利 |
| operating_income | double | 经营利润 |
| net_income | double | 净利润 |
| eps_diluted | double | 稀释 EPS |
| operating_cash_flow | double | 经营现金流 |
| free_cash_flow | double | 自由现金流 |

### 6.4 `signals_daily`

记录每日指标和信号。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| symbol | text | 代码 |
| date | date | 日期 |
| ma_50 | double | 50 日均线 |
| ma_200 | double | 200 日均线 |
| rsi_14 | double | RSI |
| volatility_20 | double | 20 日波动率 |
| drawdown_from_high | double | 距离历史高点回撤 |
| trend_state | text | up / neutral / down |
| risk_state | text | normal / watch / warning |

### 6.5 `portfolio_snapshots`

记录个人持仓快照。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| date | date | 日期 |
| symbol | text | 代码 |
| shares | double | 持有数量 |
| market_value | double | 市值 |
| cost_basis | double | 成本 |
| weight | double | 组合权重 |

### 6.6 `alerts`

记录提醒。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | text | 提醒 ID |
| created_at | timestamp | 创建时间 |
| symbol | text | 代码 |
| alert_type | text | trend / risk / valuation / event / portfolio |
| severity | text | info / watch / warning / critical |
| title | text | 标题 |
| message | text | 详情 |
| resolved | boolean | 是否处理 |

## 7. 核心指标体系

### 7.1 趋势指标

长期持有不需要太多技术指标，建议保留少数稳定指标：

- 50 日均线。
- 200 日均线。
- 52 周高点和低点。
- 距离历史高点回撤。
- 20 日、60 日、252 日收益率。
- 20 日和60 日波动率。

趋势状态示例：

```text
长期上行：价格 > 200 日均线，且 50 日均线 > 200 日均线
中性震荡：价格接近 200 日均线，上下偏离不明显
长期转弱：价格 < 200 日均线，且 50 日均线 < 200 日均线
```

### 7.2 风险指标

长期系统最重要的是避免单一资产和单一风格风险过高。

重点监控：

- 单资产最大权重。
- 科技股总权重。
- 前三大持仓权重。
- 组合相对 SPY 的 Beta。
- 组合最大回撤。
- 个股从高点回撤。
- 个股与 QQQ 的相关性。
- 组合年化波动率。

风险规则示例：

```text
单只股票权重 > 25%：警戒
科技股总权重 > 70%：警戒
组合最大回撤 > 20%：警戒
NVDA / AAPL / MSFT / AMZN 任一从高点回撤 > 30%：重点关注
QQQ 跌破 200 日均线且 VIX > 30：市场风险警戒
```

### 7.3 估值指标

ETF 和个股的估值处理不同。

个股估值：

- PE。
- Forward PE。
- PS。
- EV / EBITDA。
- Free Cash Flow Yield。
- PEG。

ETF 估值：

- 指数整体 PE。
- 指数盈利收益率。
- 与 10 年期国债收益率比较。
- 当前估值处于过去 5 年或 10 年分位数。

第一版如果估值数据难以稳定获取，可以先手动维护或接入第三方 API，行情和风险系统先跑起来。

### 7.4 基本面指标

对大型科技股，重点不只是利润，而是增长质量。

核心指标：

- 收入同比增长。
- 净利润同比增长。
- EPS 同比增长。
- 毛利率。
- 经营利润率。
- 自由现金流。
- 回购规模。
- 现金和债务。

警戒规则示例：

```text
收入同比连续 2 个季度放缓：关注
营业利润率连续 2 个季度下降：关注
自由现金流转负：警戒
EPS 同比大幅下降且管理层指引下修：警戒
```

### 7.5 事件指标

系统应该维护事件日历：

- 财报日期。
- 除权除息日。
- 股东大会。
- CPI / FOMC 等宏观日期。
- 大型产品发布会。

长期投资者不一定要交易事件，但应该知道事件窗口。

## 8. 系统架构

### 8.1 总体架构

```text
数据源
  -> 数据采集任务
  -> 数据清洗与校验
  -> 本地数据库
  -> 指标计算引擎
  -> 风险与告警引擎
  -> Web Dashboard / 报告
  -> 人工确认
  -> 可选交易执行
```

### 8.2 推荐技术栈

个人开发优先选择简单、稳定、可维护的技术。

| 模块 | 推荐 |
| --- | --- |
| 语言 | Python |
| 数据处理 | pandas / polars |
| 本地数据库 | DuckDB / SQLite |
| 后端 API | FastAPI |
| 前端 | Streamlit 起步，后续可换 React |
| 定时任务 | cron / APScheduler / Prefect |
| 可视化 | Plotly |
| 配置管理 | YAML / TOML |
| 日志 | loguru / Python logging |
| 测试 | pytest |
| 部署 | 本地 Mac / VPS / Docker |

### 8.3 为什么第一版建议 Streamlit

Streamlit 适合个人量化系统第一版：

- 上手快。
- 数据表、图表、筛选器实现简单。
- 不需要前后端分离。
- 适合研究面板和内部工具。

等系统稳定后，再拆成 FastAPI + React。

## 9. 功能模块设计

### 9.1 Watchlist 模块

功能：

- 维护关注资产列表。
- 标记核心仓位、观察仓位、宏观指标。
- 设置资产分类和目标权重。

示例配置：

```yaml
watchlist:
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

### 9.2 Data Collector 模块

功能：

- 每日收盘后拉取价格数据。
- 每周补齐缺失数据。
- 财报发布后拉取 SEC 数据。
- 保存数据源和更新时间。
- 失败重试并记录错误。

任务频率：

| 任务 | 频率 |
| --- | --- |
| 日线行情更新 | 每个美股交易日收盘后 |
| 指标计算 | 行情更新后 |
| 财报数据更新 | 每日检查一次 |
| 持仓快照 | 每日或每周 |
| 周报生成 | 每周一次 |
| 月度再平衡检查 | 每月一次 |

### 9.3 Signal Engine 模块

功能：

- 计算趋势指标。
- 计算风险指标。
- 计算组合权重。
- 生成资产状态。

资产状态示例：

```text
SPY: normal
QQQ: watch
NVDA: extended
AAPL: normal
AMZN: improving
MSFT: normal
```

### 9.4 Alert Engine 模块

提醒不宜太多。过多提醒会导致用户忽略系统。

提醒类型：

- `trend_break`：跌破长期均线。
- `drawdown_warning`：从高点回撤超过阈值。
- `valuation_high`：估值进入高分位。
- `earnings_event`：财报临近。
- `fundamental_deterioration`：基本面恶化。
- `portfolio_concentration`：组合过度集中。
- `rebalance_due`：再平衡窗口到来。

提醒渠道：

- 本地 Dashboard。
- Email。
- Telegram / Discord / Slack。
- 手机推送可后续加入。

### 9.5 Portfolio 模块

功能：

- 手动录入或导入持仓。
- 计算当前市值、收益、权重。
- 计算资产类别暴露。
- 计算目标权重偏离。
- 输出再平衡建议。

长期持有推荐用目标权重，而不是频繁择时。

示例：

```yaml
target_allocation:
  SPY: 35
  QQQ: 25
  NVDA: 10
  AAPL: 10
  AMZN: 7.5
  MSFT: 7.5
  SGOV: 5
```

再平衡规则：

```text
任一资产偏离目标权重超过 5 个百分点：提醒
单一个股超过 20%：提醒
现金类资产低于 3%：提醒
每月只检查一次再平衡，避免过度交易
```

### 9.6 Report 模块

系统应该自动生成报告，而不是只展示图表。

日报：

- 昨日涨跌。
- 是否触发提醒。
- 组合回撤。

周报：

- 本周资产表现。
- 趋势状态变化。
- 风险状态变化。
- 下周财报和宏观事件。

月报：

- 组合收益。
- 与 SPY / QQQ 对比。
- 最大回撤。
- 目标权重偏离。
- 是否需要再平衡。

## 10. 页面设计

### 10.1 首页 Dashboard

首页只展示最重要的信息：

- 组合总市值。
- 今日 / 本周 / 本月收益。
- 当前风险状态。
- 触发的提醒。
- 核心资产趋势状态。
- 组合权重饼图。
- 与 SPY / QQQ 的相对表现。

### 10.2 资产详情页

每个资产展示：

- 价格走势图。
- 50 / 200 日均线。
- 回撤曲线。
- 波动率。
- 估值指标。
- 财报指标。
- 历史提醒。
- 备注和投资 thesis。

### 10.3 组合页

展示：

- 当前持仓。
- 目标权重。
- 权重偏离。
- 行业暴露。
- 科技股总暴露。
- 个股集中度。
- 再平衡建议。

### 10.4 事件页

展示：

- 即将到来的财报。
- FOMC / CPI 等宏观日期。
- 已发生的重要公告。
- 人工记录的投资笔记。

## 11. 策略逻辑：长期持有版

### 11.1 核心规则

长期持有系统建议以规则辅助纪律，不以规则替代判断。

基本规则：

```text
只在固定周期检查组合，例如每月一次。
只有风险状态进入 warning 才考虑减少加仓或减仓。
估值过热不等于立刻卖出，只代表降低未来加仓强度。
趋势转弱不等于立刻清仓，只代表进入观察状态。
基本面恶化比短期价格下跌更重要。
```

### 11.2 定投规则

示例定投策略：

```text
每月固定投入。
SPY / VTI 作为基础仓位。
QQQ 作为成长仓位。
科技个股只在目标权重内补充。
当 QQQ 跌破 200 日均线且 VIX 高于阈值时，降低个股加仓比例。
当个股估值进入历史高分位时，只补 ETF，不补个股。
```

### 11.3 再平衡规则

示例：

```text
每月最后一个交易日检查。
资产权重偏离目标超过 5 个百分点才提醒。
单只科技股超过组合 20% 时提醒。
科技股总权重超过 70% 时提醒。
再平衡建议只输出，不自动交易。
```

### 11.4 风险退出规则

长期持有不建议频繁止损，但要有风险退出机制。

可以考虑：

```text
公司基本面连续 2-3 个季度恶化：进入 thesis review
重大财务造假或监管风险：critical
商业模式发生根本变化：critical
个股权重过高且回撤扩大：减仓提醒
```

## 12. 第一阶段 MVP

第一阶段目标：做出一个每天自动更新的本地盯盘系统。

### 12.1 MVP 功能

- 维护关注列表。
- 拉取日线价格。
- 保存到本地数据库。
- 计算均线、收益率、波动率、回撤。
- 展示 Dashboard。
- 生成提醒。
- 手动录入持仓。
- 输出组合权重和风险状态。

### 12.2 MVP 标的

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT
```

### 12.3 MVP 技术选择

```text
Python
pandas
yfinance
DuckDB
Streamlit
Plotly
APScheduler
pytest
```

### 12.4 MVP 项目结构

```text
QuantF/
  docs/
  configs/
    watchlist.yaml
    portfolio.yaml
    alerts.yaml
  data/
    quantf.duckdb
  src/
    quantf/
      data/
        price_loader.py
        sec_loader.py
      indicators/
        trend.py
        risk.py
      portfolio/
        holdings.py
        rebalance.py
      alerts/
        rules.py
        notifier.py
      reports/
        weekly.py
      app/
        streamlit_app.py
  tests/
  README.md
```

## 13. 第二阶段增强

第二阶段目标：增强长期投资分析能力。

功能：

- 接入 SEC 财报数据。
- 计算收入、利润、现金流增长。
- 加入估值数据。
- 加入财报日历。
- 生成周报和月报。
- 增加投资 thesis 笔记。
- 增加数据源校验。
- 支持导入券商持仓 CSV。

## 14. 第三阶段实盘辅助

第三阶段目标：接入券商接口，但仍以人工确认为主。

功能：

- 接入 Interactive Brokers 或 Alpaca。
- 同步真实持仓。
- 同步账户现金。
- 获取真实成交记录。
- 生成再平衡订单草稿。
- 人工确认后下单。
- 记录每次交易原因。

建议不要在第三阶段之前做全自动下单。

## 15. 告警规则样例

### 15.1 市场风险

```text
QQQ close < QQQ ma_200 AND VIX > 30
=> warning: 科技成长资产进入高风险状态
```

### 15.2 个股回撤

```text
NVDA drawdown_from_52w_high < -30%
=> watch: NVDA 从 52 周高点回撤超过 30%
```

### 15.3 集中度

```text
NVDA portfolio_weight > 20%
=> warning: 单只股票权重过高
```

### 15.4 再平衡

```text
abs(actual_weight - target_weight) > 5%
=> watch: 目标权重偏离，需要检查再平衡
```

### 15.5 基本面

```text
revenue_yoy < 0 for 2 consecutive quarters
=> warning: 收入连续两个季度同比下降
```

## 16. 回测方案

长期持有系统的回测重点不是高频买卖，而是验证规则是否改善风险收益。

需要回测：

- 固定定投。
- 固定权重再平衡。
- 估值高分位降低加仓。
- 跌破长期均线降低个股加仓。
- 高 VIX 环境增加现金或短债权重。

比较基准：

- 100% SPY。
- 100% QQQ。
- 60% SPY + 40% QQQ。
- 用户目标组合。

回测指标：

- 年化收益。
- 最大回撤。
- 年化波动。
- Sharpe Ratio。
- Calmar Ratio。
- 月度胜率。
- 最长回撤恢复时间。
- 换手率。

## 17. 风险与限制

### 17.1 投资风险

- 大型科技股也可能长期跑输。
- 估值高不代表马上下跌。
- 跌破均线不代表趋势一定结束。
- 长期持有会经历明显回撤。
- 个股集中度是主要风险来源。

### 17.2 系统风险

- 免费行情数据可能延迟或修正。
- 财报字段映射可能不一致。
- 不同数据源的复权价格可能不同。
- 自动提醒可能误报或漏报。
- 全自动交易可能放大错误。

### 17.3 行为风险

- 系统提醒太多导致焦虑。
- 过度优化规则导致频繁交易。
- 把回测结果误认为未来收益。
- 在市场大跌时临时改变长期计划。

## 18. 实施里程碑

### Milestone 1：数据与指标

- 建立 watchlist。
- 拉取日线数据。
- 保存数据库。
- 计算均线、收益率、波动、回撤。
- 写单元测试。

### Milestone 2：Dashboard

- 首页资产状态表。
- 价格和均线图。
- 回撤图。
- 风险状态标签。
- 提醒列表。

### Milestone 3：组合管理

- 手动录入持仓。
- 计算权重。
- 目标权重配置。
- 输出偏离和再平衡提醒。

### Milestone 4：财报与基本面

- 接入 SEC API。
- 拉取季度财务数据。
- 计算同比和利润率。
- 财报风险提醒。

### Milestone 5：报告与通知

- 每周报告。
- 每月再平衡报告。
- Email 或 Telegram 提醒。

### Milestone 6：券商接口

- 接入真实持仓同步。
- 只读模式运行。
- 再生成订单草稿。
- 人工确认交易。

## 19. 推荐先做的最小版本

建议先完成一个极简闭环：

```text
watchlist.yaml
  -> 下载日线行情
  -> 写入 DuckDB
  -> 计算趋势和风险指标
  -> Streamlit 展示
  -> 生成 alerts 表
```

第一版只要能每天回答：

```text
今天我的核心资产有没有异常？
我的组合有没有过度集中？
有没有跌破长期趋势？
有没有接近再平衡阈值？
```

就已经有实际价值。

## 20. 参考资料

- SEC EDGAR APIs: <https://www.sec.gov/search-filings/edgar-application-programming-interfaces>
- Alpaca Market Data FAQ: <https://docs.alpaca.markets/us/docs/market-data-faq>
- Interactive Brokers TWS Historical Bar Data: <https://interactivebrokers.github.io/tws-api/historical_bars.html>
- yfinance download API: <https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html>

