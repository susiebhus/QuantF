# QuantF

[中文说明](README.zh-CN.md)

QuantF is a lightweight long-term US equity monitoring system for index ETFs and large technology stocks. It is designed for a personal buy-and-hold workflow: keep watching core assets, detect long-term trend/risk changes, track portfolio concentration, and surface alerts that deserve manual review.

This project is for research and personal monitoring only. It is not investment advice.

## What This Project Does

The current MVP focuses on:

- Daily price collection
- Long-term trend indicators
- Drawdown and volatility monitoring
- Event-driven alerts
- Data ingestion health tracking
- Raw data retention
- A Streamlit dashboard

The default watchlist tracks:

```text
SPY, QQQ, VTI, NVDA, AAPL, AMZN, MSFT, SMH, XLK, SGOV
```

## Implementation Principle

QuantF follows a simple data pipeline:

```text
configs/watchlist.yaml
  -> MarketDataProvider
  -> incremental historical daily prices
  -> raw_prices
  -> DuckDB local database
  -> data quality checks
  -> trend/risk indicator calculation
  -> event engine
  -> Streamlit dashboard
```

The system is intentionally not built as a high-frequency trading bot. The first version is a long-term monitoring and decision-support tool.

## APIs And Data Sources

### Current MVP

| Data | Source | Code | Notes |
| --- | --- | --- | --- |
| Daily OHLCV prices | `yfinance` | `src/quantf/data/prices.py` | Downloads 10 years of daily market data by default |
| Provider abstraction | `MarketDataProvider` | `src/quantf/data/providers/` | Keeps business logic independent from data vendors |
| Watchlist symbols | Local YAML | `configs/watchlist.yaml` | Defines ETFs and stocks to monitor |
| Portfolio positions | Local YAML | `configs/portfolio.example.yaml` | Manual position input for local tracking |
| Local storage | DuckDB | `src/quantf/db/schema.py` | Stores prices, raw payloads, signals, events, quality reports, and portfolio stats |

`yfinance` is convenient for research and MVP development. For production or trading use, replace or cross-check it with a more robust data provider such as Alpaca, Polygon, Nasdaq Data Link, or Interactive Brokers.

### Planned Later

| Data | Possible Source | Purpose |
| --- | --- | --- |
| SEC filings and fundamentals | SEC EDGAR API | Revenue, EPS, cash flow, margin, financial deterioration alerts |
| Real brokerage positions | Alpaca / Interactive Brokers | Read-only account sync, then order drafts |
| Macro indicators | FRED / market data APIs | VIX, rates, inflation, liquidity context |
| News/events | SEC 8-K / earnings calendar APIs | Earnings and major event reminders |

## How Data Is Collected

The `quantf run-daily` command performs the full MVP workflow:

```text
1. Read symbols from configs/watchlist.yaml
2. Select a MarketDataProvider
3. Read the last successful price date for each symbol
4. Fetch only the missing date range
5. Store provider payloads into raw_prices
6. Validate and clean data
7. Save clean rows into daily_prices
8. Recompute signals into signals_daily
9. Emit non-duplicated events into events
10. Update portfolio stats
11. Write ingestion_runs for recovery/debugging
```

The default download settings are:

```python
provider.fetch_prices(
    symbol,
    start=last_price_date + 1 day,
    end=today,
)
```

The current Yahoo provider uses:

```python
yf.download(
    symbol,
    start=start.isoformat(),
    end=(end + 1 day).isoformat(),
    auto_adjust=False,
    group_by="ticker",
    progress=False,
    threads=False,
)
```

## Analysis And "Prediction"

The current system does not predict tomorrow's stock price. It performs long-term state classification.

For a long-term holding system, the first useful "prediction" is not a price target. It is a structured answer to questions like:

- Is this asset still in a long-term uptrend?
- Has this asset entered a meaningful drawdown?
- Is volatility rising?
- Is the portfolio too concentrated?
- Which symbols need manual review?

### Current Algorithms

The MVP computes these indicators in `src/quantf/indicators/trend.py`:

| Indicator | Formula / Meaning |
| --- | --- |
| `ma_50` | 50-trading-day moving average |
| `ma_200` | 200-trading-day moving average |
| `return_20d` | 20-trading-day percentage return |
| `return_60d` | 60-trading-day percentage return |
| `return_252d` | 252-trading-day percentage return |
| `volatility_20d` | Annualized volatility from 20-day daily returns |
| `volatility_60d` | Annualized volatility from 60-day daily returns |
| `drawdown_from_52w_high` | Current price divided by 252-day high minus 1 |
| `drawdown_from_all_time_high` | Current price divided by historical high minus 1 |
| `rs_spy` | 60-day return minus SPY 60-day return |
| `rs_qqq` | 60-day return minus QQQ 60-day return |

### Trend State

```text
uptrend:
  close > ma_200 and ma_50 > ma_200

downtrend:
  close < ma_200 and ma_50 < ma_200

neutral:
  all other valid states

insufficient_data:
  not enough history to calculate MA50/MA200
```

### Risk State

```text
warning:
  drawdown_from_52w_high <= -30%

watch:
  drawdown_from_52w_high <= -20%
  or close < ma_200

normal:
  no risk rule triggered
```

### Event Rules

The v1.1 event engine lives in `src/quantf/events/engine.py`.

It creates durable events when:

- `TrendChanged`: trend state changes
- `RiskEscalated`: risk state moves to a higher severity
- `New52WeekHigh`: asset reaches a new 52-week high
- `New52WeekLow`: asset reaches a new 52-week low
- `PriceCrossMA200`: price crosses the 200-day moving average
- `PortfolioDrift`: actual weight drifts away from target weight

Events are deterministic and non-duplicated. They are stored in the local `events` table with:

```text
event_id, event_time, symbol, event_type, severity, title, message, payload, source_date
```

## Output Results

### Command Line Output

Running:

```bash
quantf run-daily
```

prints a summary like:

```text
Daily run complete: 2510 prices, 2510 signals, 3 alerts.
```

### Database Output

The local DuckDB file stores:

| Table | Description |
| --- | --- |
| `daily_prices` | Raw normalized daily OHLCV data |
| `signals_daily` | Calculated indicators and trend/risk states |
| `raw_prices` | Original provider payloads for debugging/rebuilds |
| `ingestion_runs` | Fetch status, failures, and recovery metadata |
| `data_quality_report` | Data validity, spike, and missing-data reports |
| `events` | Durable event timeline |
| `portfolio` | Current portfolio config loaded into the database |
| `portfolio_stats` | Weight, target weight, and drift snapshots |

### Dashboard Output

Running the Streamlit app shows:

- Latest asset state table
- Close price chart by symbol
- Trend state and risk state
- 52-week drawdown
- 20-day volatility
- 60-day and 252-day returns
- Portfolio holdings from local config
- Target allocation drift
- Data health and ingestion runs
- Event timeline

## Current Limitations

The MVP does not yet include:

- SEC fundamental data
- Earnings calendar
- News analysis
- Machine learning forecasts
- Backtesting engine
- Broker account sync
- Automatic trading

These are intentionally deferred. The first milestone is to build a reliable long-term monitoring loop.

## Planned Prediction Upgrades

Future prediction/decision modules can be added in layers:

| Layer | Method | Output |
| --- | --- | --- |
| Fundamental trend | SEC revenue/EPS/cash-flow growth | `fundamental_state` |
| Valuation regime | PE/PS/FCF yield percentile | `valuation_state` |
| Market regime | SPY/QQQ trend + VIX + rates | `market_regime` |
| Portfolio risk | concentration, beta, drawdown | `portfolio_risk_state` |
| ML scoring | logistic regression / gradient boosting | probability of outperforming benchmark |

The recommended next algorithmic step is not deep learning. It is adding fundamentals and portfolio-level risk rules.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

If your shell only has `python3`, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
quantf run-daily
streamlit run src/quantf/app/streamlit_app.py
```

## Useful Commands

```bash
quantf init-db
quantf update-prices
quantf compute-signals
quantf generate-alerts
quantf generate-events
quantf run-daily
```

## Project Structure

```text
configs/
  watchlist.yaml              # Symbols to monitor
  portfolio.example.yaml      # Manual portfolio input
  alerts.yaml                 # Alert thresholds for later expansion
src/quantf/
  data/providers/             # MarketDataProvider implementations
  data/pipeline.py            # Incremental ingestion pipeline
  data/prices.py              # Price persistence helpers
  data/quality.py             # Data quality checks
  data/raw.py                 # Raw provider payload storage
  db/schema.py                # DuckDB tables
  indicators/trend.py         # Trend, return, volatility, drawdown indicators
  events/engine.py            # Durable event generation
  portfolio/                  # Holdings and target allocation helpers
  market/regime.py            # Lightweight market regime classification
  app/streamlit_app.py        # Dashboard
  cli.py                      # Command-line workflow
tests/
  test_indicators.py
  test_alerts.py
  test_data_quality.py
  test_events.py
```
