# QuantF

[English README](README.md)

QuantF 是一个轻量级的长期美股量化盯盘系统，面向指数 ETF 和大型科技股。它服务于个人长期持有场景：持续观察核心资产，识别长期趋势和风险变化，跟踪组合集中度，并在需要人工复核时输出提醒。

本项目仅用于研究和个人监控，不构成任何投资建议。

## 项目能做什么

当前 MVP 重点包括：

- 每日价格数据采集
- 长期趋势指标计算
- 回撤和波动率监控
- 基于规则的提醒
- Streamlit 可视化看板

默认关注列表：

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT, SMH, XLK, SGOV
```

## 实现原理

QuantF 使用一条简单的数据流水线：

```text
configs/watchlist.yaml
  -> yfinance 历史日线行情
  -> DuckDB 本地数据库
  -> 趋势/风险指标计算
  -> 规则提醒引擎
  -> Streamlit 看板
```

这个系统不是高频交易机器人。第一版定位是长期投资监控和决策辅助工具。

## 调用的 API 和数据源

### 当前 MVP

| 数据 | 来源 | 代码位置 | 说明 |
| --- | --- | --- | --- |
| 日线 OHLCV 行情 | `yfinance` | `src/quantf/data/prices.py` | 默认下载 10 年日线数据 |
| 关注列表 | 本地 YAML | `configs/watchlist.yaml` | 定义要监控的 ETF 和股票 |
| 持仓配置 | 本地 YAML | `configs/portfolio.example.yaml` | 手动录入本地持仓 |
| 本地存储 | DuckDB | `src/quantf/db/schema.py` | 存储行情、指标和提醒 |

`yfinance` 适合研究和 MVP 开发。如果后续用于生产环境或实盘交易，需要替换或交叉校验更稳定的数据源，例如 Alpaca、Polygon、Nasdaq Data Link 或 Interactive Brokers。

### 后续计划

| 数据 | 可能来源 | 用途 |
| --- | --- | --- |
| SEC 财报和基本面 | SEC EDGAR API | 收入、EPS、现金流、利润率、基本面恶化提醒 |
| 真实券商持仓 | Alpaca / Interactive Brokers | 只读同步账户，后续生成订单草稿 |
| 宏观指标 | FRED / 行情 API | VIX、利率、通胀、流动性背景 |
| 新闻和事件 | SEC 8-K / 财报日历 API | 财报和重大事件提醒 |

## 数据怎么获取

`quantf run-daily` 命令会执行完整的 MVP 流程：

```text
1. 从 configs/watchlist.yaml 读取股票/ETF 代码
2. 调用 yfinance.download(...)
3. 标准化为 symbol/date/open/high/low/close/adj_close/volume
4. 写入 data/quantf.duckdb -> daily_prices
5. 基于所有已存行情重新计算指标
6. 将指标写入 signals_daily
7. 读取每个 symbol 的最新信号并生成提醒
8. 将提醒写入 alerts
```

默认下载参数：

```python
yf.download(
    symbols,
    period="10y",
    auto_adjust=False,
    group_by="ticker",
    progress=False,
    threads=True,
)
```

## 分析与“预测”

当前系统不预测明天的股价。它做的是长期状态分类。

对于长期持有系统，第一阶段真正有用的“预测”不是目标价，而是结构化回答这些问题：

- 这个资产是否仍处于长期上升趋势？
- 这个资产是否已经进入显著回撤？
- 波动率是否正在升高？
- 组合是否过度集中？
- 哪些标的需要人工复核？

### 当前算法

MVP 在 `src/quantf/indicators/trend.py` 中计算以下指标：

| 指标 | 公式 / 含义 |
| --- | --- |
| `ma_50` | 50 个交易日移动平均线 |
| `ma_200` | 200 个交易日移动平均线 |
| `return_20d` | 20 个交易日收益率 |
| `return_60d` | 60 个交易日收益率 |
| `return_252d` | 252 个交易日收益率 |
| `volatility_20d` | 基于 20 日收益率的年化波动率 |
| `volatility_60d` | 基于 60 日收益率的年化波动率 |
| `drawdown_from_52w_high` | 当前价格 / 252 日高点 - 1 |
| `drawdown_from_all_time_high` | 当前价格 / 历史高点 - 1 |

### 趋势状态

```text
uptrend:
  close > ma_200 且 ma_50 > ma_200

downtrend:
  close < ma_200 且 ma_50 < ma_200

neutral:
  其他有效状态

insufficient_data:
  历史数据不足，无法计算 MA50/MA200
```

### 风险状态

```text
warning:
  drawdown_from_52w_high <= -30%

watch:
  drawdown_from_52w_high <= -20%
  或 close < ma_200

normal:
  没有触发风险规则
```

### 提醒规则

MVP 的提醒引擎位于 `src/quantf/alerts/rules.py`。

它会在以下情况生成提醒：

- `trend_state == "downtrend"`：长期趋势走弱
- `risk_state == "watch"`：资产需要关注
- `risk_state == "warning"`：回撤进入警戒

提醒会存入本地 `alerts` 表：

```text
id, created_at, symbol, alert_type, severity, title, message, resolved
```

## 输出结果

### 命令行输出

运行：

```bash
quantf run-daily
```

会输出类似：

```text
Daily run complete: 2510 prices, 2510 signals, 3 alerts.
```

### 数据库输出

本地 DuckDB 文件会保存：

| 表 | 说明 |
| --- | --- |
| `daily_prices` | 标准化后的日线 OHLCV 数据 |
| `signals_daily` | 计算后的指标、趋势状态和风险状态 |
| `alerts` | 当前和历史提醒 |

### 看板输出

运行 Streamlit 看板后可以看到：

- 最新资产状态表
- 单个标的收盘价走势图
- 趋势状态和风险状态
- 52 周回撤
- 20 日波动率
- 60 日和 252 日收益率
- 来自本地配置的组合持仓
- 目标权重偏离
- 当前未处理提醒

## 当前限制

MVP 暂未包含：

- SEC 基本面数据
- 财报日历
- 新闻分析
- 机器学习预测
- 回测引擎
- 券商账户同步
- 自动交易

这些功能是有意后置的。第一阶段目标是先建立可靠的长期监控闭环。

## 后续预测能力升级

后续可以分层加入预测和决策模块：

| 层级 | 方法 | 输出 |
| --- | --- | --- |
| 基本面趋势 | SEC 收入/EPS/现金流增长 | `fundamental_state` |
| 估值状态 | PE/PS/FCF Yield 历史分位 | `valuation_state` |
| 市场环境 | SPY/QQQ 趋势 + VIX + 利率 | `market_regime` |
| 组合风险 | 集中度、Beta、回撤 | `portfolio_risk_state` |
| 机器学习评分 | Logistic Regression / Gradient Boosting | 跑赢基准的概率 |

推荐下一步不是直接上深度学习，而是先加入基本面和组合级风险规则。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

如果你的终端只有 `python3`：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

## 常用命令

```bash
quantf init-db
quantf update-prices
quantf compute-signals
quantf generate-alerts
quantf run-daily
```

## 项目结构

```text
configs/
  watchlist.yaml              # 要监控的标的
  portfolio.example.yaml      # 手动持仓输入
  alerts.yaml                 # 后续扩展用的提醒阈值
src/quantf/
  data/prices.py              # yfinance 行情下载和标准化
  db/schema.py                # DuckDB 表结构
  indicators/trend.py         # 趋势、收益、波动率、回撤指标
  alerts/rules.py             # 基于规则生成提醒
  portfolio/                  # 持仓和目标权重辅助函数
  app/streamlit_app.py        # 看板
  cli.py                      # 命令行流程
tests/
  test_indicators.py
  test_alerts.py
```
